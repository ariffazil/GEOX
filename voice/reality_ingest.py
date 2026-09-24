#!/usr/bin/env python3
"""
GEOX Voice Reality Ingestion — EMD Decode -> Metabolize -> GEOX sink.

  Bukan chatbot. Organ tangkapan realiti.

  Audio -> ASR -> transkrip -> KATEGORI GUARD -> entiti/claim -> GEOX + SCAR + VAULT999

KENAPA INI, BUKAN TTS:
  Kuota TTS = ~10K aksara/model (perhiasan).
  Kuota ASR = ~36K saat/model x ~14 model = ~140 jam (lombong).
  Aset kekal = realiti subsurface yang hanya wujud dalam kepala & bilik review.

FLOORS: F1 reversible · F2 truth_class wajib · F4 ΔS<=0 · F6 maruah pihak ketiga
        F9 tiada tuntutan kesedaran · F11 receipt · F13 sempadan berdaulat

DOCTRINE (state-transition-discipline):
  Suara = Claimed, BUKAN Measured.
  truth_class ingatan suara = REPORTED (max), tidak pernah OBSERVED.
  Stored != Retrieved != Relevant != Current.

DOCTRINE (hermes BIOS #8 + claim-receipt-discipline):
  Claim tentang ORANG = tentang PERKATAAN dia ("X luah risiko Y"),
  BUKAN tentang SIFAT dia ("X cuai"). Trait-claim = REJECT.

SEMPADAN F13 (kategori guard, gagal-tertutup):
  GEOSCIENCE  -> sink GEOX
  OPS         -> sink GEOX (ops brief)
  PERSONAL    -> QUARANTINE (F5-private, relationship-memory-isolation)
  THIRD_PARTY -> QUARANTINE (perlukan consent + klasifikasi sebelum ingest)
  UNKNOWN     -> QUARANTINE (jangan teka)

Usage:
  python3 reality_ingest.py ingest <audio_or_transcript> [--kind voice_note|meeting|field]
  python3 reality_ingest.py batch  <dir> [--dry-run]
  python3 reality_ingest.py guard  <text>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
QUAR = ROOT / "quarantine"
OUT.mkdir(exist_ok=True)
QUAR.mkdir(exist_ok=True)

# ── Route least power ────────────────────────────────────────────────────────
# ASR: BAILIAN_PAYG_API_KEY (sk-ws-) = SATU-SATUNYA key yang bakar free quota.
#      QWEN_API_KEY (sk-sp-) Token Plan = TIDAK PERNAH sentuh free quota (dokumen Alibaba).
# METABOLIZE: FED flash lane :4000 = percuma.
PAYG_BASE = os.environ.get(
    "BAILIAN_PAYG_BASE",
    "https://ws-wlab8klalfojzq7i.ap-southeast-1.maas.aliyuncs.com",
)
DASHSCOPE_INTL = "https://dashscope-intl.aliyuncs.com"
FED_FLASH = os.environ.get("FED_FLASH_BASE", "http://127.0.0.1:4000")

ASR_MODEL_PRIMARY = "qwen3-asr-flash"  # 36K saat free quota
ASR_MODEL_FALLBACK = "fun-asr"  # 36K saat free quota (berasingan!)
LLM_MODEL = os.environ.get("GEOX_VOICE_LLM", "deepseek-v4-flash")

# ── PENGANTIAN MODEL = PENGALI KUOTA ─────────────────────────────────────────
# Dokumen Alibaba: "Snapshot versions with date suffixes and latest versions
# without suffixes are treated as two independent models with separate quotas."
# Setiap ID di bawah = kolam 36K saat PERSENDIRIAN. Putar untuk bakar semuanya.
#
# DIKESAN HIDUP 2026-09-24 (6/9 lulus ujian langsung):
#   fun-asr · fun-asr-2025-11-07 · fun-asr-mtl · fun-asr-mtl-2025-08-25
#   fun-asr-2025-08-25 · qwen-audio-3.0-asr-flash-filetrans
# Gagal: fun-asr-flash-2026-06-15 (url error),
#        qwen3-asr-flash-filetrans[-2025-11-17] (task FAILED),
#        qwen3-asr-flash chat (mahukan URL sebenar, bukan data-URL)
#
# STRATEGI MASA (F4: jangan bazir yang belum luput):
#   Burn dahulu yang luput 2026-09-29. Tahan qwen-audio-3.0-* (luput 2026-10-27)
#   untuk kegunaan SELEPAS tebing.
ASR_ROTA = [
    # --- LUPUT 2026-09-29 : bakar SEKARANG ---
    ("fun-asr", "2026-09-29"),
    ("fun-asr-2025-11-07", "2026-09-29"),
    ("fun-asr-mtl", "2026-09-29"),
    ("fun-asr-mtl-2025-08-25", "2026-09-29"),
    ("fun-asr-2025-08-25", "2026-09-29"),
    # --- LUPUT 2026-10-27 : simpan utk selepas tebing ---
    ("qwen-audio-3.0-asr-flash-filetrans", "2026-10-27"),
    ("qwen-audio-3.0-asr-flash", "2026-10-27"),
]

# Nisbah kuota yang dibakar (jejak audit — 36K saat = 36000)
HOLD_LATE_EXPIRY = os.environ.get("GEOX_VOICE_HOLD_LATE", "1") == "1"  # tahan kuota luput lambat

ASR_QUOTA_S = {
    "fun-asr": 36000,
    "fun-asr-2025-11-07": 36000,
    "fun-asr-mtl": 36000,
    "fun-asr-mtl-2025-08-25": 36000,
    "fun-asr-2025-08-25": 36000,
    "qwen-audio-3.0-asr-flash-filetrans": 36000,
    "qwen-audio-3.0-asr-flash": 36000,
}

MAX_CHUNK_S = 25  # had keras skill AAA-asr-glm-ingest: <=30s, <=25MB
MAX_CHUNK_BYTES = 20 * 1024 * 1024


# ═══════════════════════════════════════════════════════════════════════════
# 1. KATEGORI GUARD — gagal-tertutup. Ini lantai F6/F13.
# ═══════════════════════════════════════════════════════════════════════════

GEO_LEXICON = {
    "basin",
    "formation",
    "source rock",
    "reservoir",
    "seal",
    "trap",
    "migration",
    "charge",
    "prospect",
    "lead",
    "play",
    "well",
    "telaga",
    "basement",
    "carbonate",
    "clastic",
    "sandstone",
    "shale",
    "limestone",
    "dolomite",
    "porosity",
    "permeability",
    "saturation",
    "hydrocarbon",
    "kerogen",
    "vitrinite",
    "maturation",
    "burial",
    "subsidence",
    "rift",
    "sag",
    "inversion",
    "halokinesis",
    "salt",
    "diapir",
    "fault",
    "horizon",
    "reflection",
    "seismic",
    "amplitude",
    "avo",
    "impedance",
    "velocity",
    "checkshot",
    "synthetic",
    "tops",
    "core",
    "dst",
    "rft",
    "mdt",
    "petrophys",
    "vsh",
    "gr",
    "rhob",
    "nphi",
    "dt",
    "sigma",
    "basin model",
    "charge model",
    "psource",
    "psource",
    "play fairway",
    "segment",
    "closure",
    "spill point",
    "column",
    "goc",
    "owc",
    "gwc",
    "stoip",
    "giip",
    "recoverable",
    "kinabalu",
    "sabah",
    "sarawak",
    "malay basin",
    "luconia",
    "baram",
    "tigapuluh",
    "balingian",
    "bongawan",
    "tambak",
    "siwa",
    "gumusut",
    "malikai",
    "kepong",
    "wakid",
    "bekantan",
    "lebah emas",
    "bunga tasbih",
    "kl-2",
    "kl2",
    "cp review",
    "peer review",
    "prospect maturation",
    "volumetric",
    "pos",
    "chance of success",
    "emv",
    "evoi",
    "dry hole",
    "junked",
    "sidetrack",
    "td",
    "tvd",
    "md",
    "correlation",
    "sequence stratigraphy",
    "parasequence",
    "system tract",
    "depositional",
    "deltaic",
    "fluvial",
    "shoreface",
    "turbidite",
    "reef",
    "karst",
    "unconformity",
    "condensed section",
    "flooding surface",
}

PERSONAL_LEXICON = {
    "syed",
    "sado",
    "magnesium",
    "ronaldo",
    "anxiety",
    "wallet",
    "perasaan",
    "marah",
    "sedih",
    "rindu",
    "cinta",
    "kahwin",
    "cerai",
    "keluarga",
    "ayah",
    "abang",
    "adik",
    "kakak",
    "isteri",
    "suami",
    "teman",
    "kawan baik",
    "shadow",
    "trauma",
    "luka",
    "hati",
    "jiwa",
    "rindu",
    "kisah peribadi",
    "sedihnya",
    "emosi",
    "mimpi",
    "perasaan saya",
}

# Petunjuk pihak ketiga — OVERRIDE ke QUARANTINE walau berapa pun skor geo.
# Perlu consent F13 + pengesanan hak IP majikan sebelum sebarang ingest.
THIRD_PARTY_LEXICON = {
    "laletha",
    "hakim",
    "kak su",
    "encik",
    "puan",
    "datuk",
    "tan sri",
    "petronas carigali",
    "petronas",
    "petros",
    "shell sarawak",
    "gentari",
    "tengku taufik",
    "retired",
    "pencen",
    "bekas staf",
    "bekas pekerja",
    "ex-staff",
    "bekas",
    "oral history",
    "temu bual",
    "interview",
    "wawancara",
    "arwah",
    "allahyarham",
}

# Nama orang satu-token yang kerap muncul dalam nota kita.
PERSON_NAMES = {
    "syazwan",
    "syed",
    "sado",
    "laletha",
    "hakim",
    "ronaldo",
    "arif",
    "azril",
    "nazri",
    "farid",
    "izzat",
}

# Kata sifat negatif tentang manusia — trait-claim HARAM (hermes BIOS #8, F6).
TRAIT_WORDS = {
    "cuai",
    "lembab",
    "malas",
    "bodoh",
    "degil",
    "sombong",
    "tipu",
    "penipu",
    "tak cekap",
    "tidak kompeten",
    "jahat",
}


@dataclass
class GuardVerdict:
    category: str  # GEOSCIENCE | OPS | PERSONAL | THIRD_PARTY | UNKNOWN
    sink: str  # GEOX | QUARANTINE
    confidence: float
    reasons: list = field(default_factory=list)
    named_persons: list = field(default_factory=list)
    proprietary_flag: bool = False

    def to_dict(self):
        return asdict(self)


def _hit(text_lower: str, lexicon) -> list:
    """Padanan bersempadan perkataan (F10). 'mak' TIDAK match 'lemak'."""
    out = []
    for w in lexicon:
        if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", text_lower):
            out.append(w)
    return sorted(out)


def guard(text: str) -> GuardVerdict:
    """F13 kategori guard. Gagal-tertutup: apa-apa keraguan -> QUARANTINE.

    SUSUNAN KEPUTUSAN (jangan terbalik — ini yang pernah bocor):
      1. OVERRIDE third-party -> QUARANTINE walau geo tinggi   [consent F13 + IP]
      2. OVERRIDE personal    -> QUARANTINE walau geo tinggi   [F5 private]
      3. trait-claim atas orang -> QUARANTINE                  [F6 maruah]
      4. barulah geo / ops / unknown
    Arah gagal-tertutup = mengkuarantin, bukan mengutamakan ingest.
    """
    t = text.lower()

    geo = _hit(t, GEO_LEXICON)
    per = _hit(t, PERSONAL_LEXICON)
    tp = _hit(t, THIRD_PARTY_LEXICON)
    trait = _hit(t, TRAIT_WORDS)

    # Nama: dua-token berhuruf besar + satu-token dari leksikon orang
    named = sorted(set(re.findall(r"\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b", text)))
    named = [n for n in named if n.lower() not in GEO_LEXICON]
    named += [w for w in PERSON_NAMES if re.search(r"\b" + re.escape(w) + r"\b", t)]
    named = sorted(set(named))

    proprietary = bool(
        re.search(
            r"petronas|carigali|petros|shell\s+sarawak|confidential|sulit|proprietary|internal\s+only",
            t,
        )
    )

    trait_on_person = bool(trait) and bool(named)

    # ── 1. OVERRIDE third-party (paling bahaya: sejarah lisan + IP majikan) ──
    if tp:
        return GuardVerdict(
            "THIRD_PARTY",
            "QUARANTINE",
            0.80,
            [
                f"OVERRIDE_third_party={tp}",
                "perlukan_consent_F13_sebelum_ingest",
                "kenal_pasti_hak_IP_PETRONAS",
            ],
            named,
            proprietary,
        )

    # ── 2. OVERRIDE personal (F5-private, relationship-memory-isolation) ──
    if per:
        return GuardVerdict(
            "PERSONAL",
            "QUARANTINE",
            0.85,
            [f"OVERRIDE_personal={per}", "F5_private_bukan_geox"],
            named,
            proprietary,
        )

    # ── 3. trait-claim tentang orang: bendera keras, jangan senyap ──
    if trait_on_person:
        return GuardVerdict(
            "PERSONAL",
            "QUARANTINE",
            0.75,
            [
                f"TRAIT_CLAIM_on_person={trait}",
                f"named={named}",
                "F6_MARUAH_trait_claim_ditolak",
            ],
            named,
            proprietary,
        )

    # ── 4. geosains ──
    if len(geo) >= 2:
        conf = min(0.70 + 0.05 * len(geo), 0.90)  # F7: cap 0.90
        reasons = [f"lexicon_geo={geo}"]
        if named:
            reasons.append(f"named_persons={named} -> framing PERKATAAN, bukan SIFAT")
        if proprietary:
            reasons.append("proprietary_flag -> klasifikasi sebelum sebar")
        return GuardVerdict("GEOSCIENCE", "GEOX", conf, reasons, named, proprietary)

    ops_cue = _hit(
        t,
        {"reminder", "action item", "tindakan", "deadline", "esok", "meeting", "emel", "email"},
    )
    if ops_cue or "kena " in t or "perlu " in t:
        return GuardVerdict("OPS", "GEOX", 0.65, [f"ops_cue={ops_cue}"], named, proprietary)

    return GuardVerdict("UNKNOWN", "QUARANTINE", 0.40, ["tiada_isyarat_mencukupi", "jangan_teka"], named, proprietary)


# ═══════════════════════════════════════════════════════════════════════════
# 2. DECODE — ASR. Bakar kuota PAYG, bukan Token Plan.
# ═══════════════════════════════════════════════════════════════════════════


def _b64_audio(path: Path) -> tuple[str, str]:
    import base64
    import mimetypes

    mime = mimetypes.guess_type(str(path))[0] or "audio/ogg"
    return base64.b64encode(path.read_bytes()).decode(), mime


def _http_json(url: str, payload: dict, headers: dict, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:600]
        raise RuntimeError(f"HTTP {e.code} {url}: {body}") from None


def asr_qwen_chat(path: Path, api_key: str, model: str = ASR_MODEL_PRIMARY) -> dict:
    """qwen3-asr-flash via compatible-mode chat completions (audio input).
    Ini laluan yang BAKAR free quota 36K saat."""
    b64, mime = _b64_audio(path)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "input_audio", "input_audio": {"data": b64, "format": mime.split("/")[-1]}},
                    {
                        "type": "text",
                        "text": (
                            "Transkrip audio ini SAHAJA. Kekalkan bahasa asal (BM/EN/saik-switch). "
                            "Jangan ringkas, jangan terjemah, jangan tambah. Keluaran = transkrip mentah."
                        ),
                    },
                ],
            }
        ],
        "temperature": 0.0,
    }
    r = _http_json(f"{PAYG_BASE}/compatible-mode/v1/chat/completions", payload, {"Authorization": f"Bearer {api_key}"})
    text = (r.get("choices") or [{}])[0].get("message", {}).get("content", "")
    usage = r.get("usage", {})
    return {"text": text, "model": model, "usage": usage, "lane": "qwen_chat"}


def asr_fun_asr(path: Path, api_key: str, model: str = ASR_MODEL_FALLBACK) -> dict:
    """Transkripsi fail via DashScope (async). Setiap `model` = kolam kuota PERSENDIRIAN."""
    b64, mime = _b64_audio(path)
    payload = {
        "model": model,
        "input": {"file_urls": [f"data:{mime};base64,{b64}"]},
        "parameters": {"language_hints": ["zh", "en", "ms"]},
    }
    r = _http_json(
        f"{DASHSCOPE_INTL}/api/v1/services/audio/asr/transcription",
        payload,
        {"Authorization": f"Bearer {api_key}", "X-DashScope-Async": "enable"},
    )
    task = (r.get("output") or {}).get("task_id")
    if not task:
        return {"text": "", "model": model, "lane": "asr_transcribe", "error": str(r)[:300]}
    for _ in range(60):
        time.sleep(3)
        q = urllib.request.Request(f"{DASHSCOPE_INTL}/api/v1/tasks/{task}", headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(q, timeout=60) as rr:
            st = json.loads(rr.read().decode())
        out = st.get("output") or {}
        if out.get("task_status") in ("SUCCEEDED", "FAILED", "CANCELED"):
            if out.get("task_status") != "SUCCEEDED":
                return {
                    "text": "",
                    "model": model,
                    "lane": "asr_transcribe",
                    "error": f"task_{out.get('task_status')}: {str(out)[:200]}",
                }
            text = ""
            for res in out.get("results") or []:
                u = res.get("transcription_url")
                if u:
                    with urllib.request.urlopen(u, timeout=60) as tr:
                        tj = json.loads(tr.read().decode())
                    text += _flatten_fun(tj) + "\n"
            return {"text": text.strip(), "model": model, "usage": st.get("usage", {}), "lane": "asr_transcribe"}
    return {"text": "", "model": model, "lane": "asr_transcribe", "error": "poll_timeout"}


def _flatten_fun(tj: dict) -> str:
    try:
        return " ".join(x.get("text", "") for x in tj["transcripts"][0]["sentences"])
    except Exception:
        return json.dumps(tj, ensure_ascii=False)[:4000]


def _load_payg_key() -> str:
    key = os.environ.get("BAILIAN_PAYG_API_KEY", "")
    if key:
        return key
    for f in (Path("/root/.secrets/bailian-payg.env"), Path("/root/.secrets/kunci-mas.env")):
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if line.startswith("BAILIAN_PAYG_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
                os.environ["BAILIAN_PAYG_API_KEY"] = key
                return key
    return ""


def log_burn(model: str, seconds: float, trace_id: str) -> None:
    """Jejak pembakaran kuota — berapa saat dari kolam mana (F11 audit)."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "model": model,
        "seconds_burned": seconds,
        "pool_total_s": ASR_QUOTA_S.get(model),
        "lane": "PAYG_free_quota",
    }
    with (OUT / "quota_burn.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")


def decode(path: Path, trace_id: str = "-", hold_late_expiry: bool = False) -> dict:
    """DECODE. Putar model ASR — setiap satu kolam kuota PERSENDIRIAN.

    hold_late_expiry=True -> hanya bakar yang luput 2026-09-29;
    tahan qwen-audio-3.0-* (luput 2026-10-27) utk selepas tebing. (F4)
    """
    key = _load_payg_key()
    if not key:
        return {"text": "", "error": "BAILIAN_PAYG_API_KEY tiada — free quota tak boleh dibakar", "lane": "none"}

    rota = [m for m, exp in ASR_ROTA if (not hold_late_expiry) or exp <= "2026-09-29"]
    try:
        sys.path.insert(0, "/root/scripts")
        from alibaba_quota_sentinel import is_model_available

        rota = [m for m in rota if is_model_available(m)[0]]
    except Exception:
        pass
    errors = []
    for model in rota:
        try:
            r = asr_fun_asr(path, key, model)
        except Exception as e:
            errors.append(f"{model}={str(e)[:120]}")
            continue
        if r.get("text"):
            log_burn(model, float((r.get("usage") or {}).get("duration") or 0), trace_id)
            r["rota_tried"] = errors
            return r
        errors.append(f"{model}={r.get('error', 'kosong')[:120]}")
    return {"text": "", "error": "semua rota ASR gagal: " + " | ".join(errors), "lane": "rota_exhausted"}


# ═══════════════════════════════════════════════════════════════════════════
# 3. METABOLIZE — FED flash lane (percuma). Strukturkan, jangan reka.
# ═══════════════════════════════════════════════════════════════════════════

EXTRACT_PROMPT = """Kau penukar realiti berbilang domain, bukan chatbot. Tukar transkrip suara
ini menjadi TIGA UNJURAN peristiwa yang sama. Satu peristiwa, beberapa dimensi realiti.

1. truth_class SEMUA item = "REPORTED". Suara = Claimed, bukan Measured. Jangan sekali-kali
   guna OBSERVED/MEASURED untuk ingatan suara.
2. Claim tentang ORANG mesti tentang PERKATAAN/AKUAN dia, BUKAN sifat diri.
   Betul: {"actor":"Syazwan","claim":"Syazwan luah risiko kesinambungan seismik","type":"attributed_statement"}
   Salah: {"actor":"Syazwan","claim":"Syazwan cuai","type":"trait"}  <- HARAM, buang.
3. Setiap claim WAJIB ada falsification_path: apa bukti akan batal dia.
4. Jika transkrip meragu / kosong / bukan geosains, pulangkan {"reject":"<sebab>"}.

TIGA UNJURAN (biarkan kosong [] jika transkrip tak sebut — JANGAN reka):
  geox  = realiti batu: stratigrafi, seismik, petrofizik, struktur, telaga, fisik bumi
  wealth= realiti modal: KOS, duit, EMV, belanjawan, kerugian telaga kering, capital_at_risk,
          peluang kos, ranking prospek ikut nilai dolar. Dry hole = rock failed + capital consumed.
  well  = realiti manusia: keadaan pembuat keputusan (letih, stres, beban, maruah).
          REFLEKSI sahaja, bukan diagnosis. Jangan katakan apa-apa tentang kesihatan/penyakit.

Keluaran JSON SAHAJA (tiada prose):
{
 "summary": "<1 ayat>",
 "event_type": "CP_REVIEW|FIELD_NOTE|ORAL_HISTORY|OPS|SCAR|OTHER",
 "project": "<kod projek atau null>",
 "basin": "<nama basin atau null>",
 "projections": {
   "geox":  [{"id":"G1","text":"...","truth_class":"REPORTED","type":"technical_assertion|attributed_statement|uncertainty",
              "actor":null,"falsification_path":"..."}],
   "wealth":[{"id":"W1","text":"...","truth_class":"REPORTED","type":"capital_cost|capital_loss|emv|opportunity_cost|capital_at_risk",
              "amount":null,"currency":null,"falsification_path":"..."}],
   "well":  [{"id":"H1","text":"...","truth_class":"REPORTED","type":"operator_state|workload|dignity_signal",
              "falsification_path":"..."}]
 },
 "actions": [{"owner":null,"action":"...","deadline":null,"domain":"geox|wealth|well"}],
 "named_persons": [{"name":"...","role":"...","mentioned_for":"statement|context"}],
 "proprietary_flag": false,
 "scar": {"failure_mode":"...",
          "constraint_imposed":"...",
          "severity":"LOW|MEDIUM|HIGH",
          "dimensions":{"geological":"...","capital":"..."}}
      | null
}

TRANSCRIPT:
"""


def metabolize(text: str, category: str) -> dict:
    if not text.strip():
        return {"reject": "transkrip kosong"}

    prompt = EXTRACT_PROMPT + text[:12000]
    body = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Kau enjin ekstraksi deterministik. JSON sahaja. Jangan reka butiran tiada dalam transkrip.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
    }
    try:
        r = _http_json(f"{FED_FLASH}/v1/chat/completions", body, {}, timeout=90)
        raw = (r.get("choices") or [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return {"reject": f"FED flash gagal: {e}"}

    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"reject": "tiada JSON", "raw": raw[:400]}
    try:
        out = json.loads(m.group(0))
    except Exception as e:
        return {"reject": f"JSON rosak: {e}", "raw": raw[:400]}

    # Enforce F2: tiada claim naik taraf melebihi REPORTED dari ingatan suara.
    # F2: tiada claim naik taraf melebihi REPORTED dari ingatan suara (semua unjuran)
    for dom in ("geox", "wealth", "well"):
        for c in (out.get("projections") or {}).get(dom, []) or []:
            c["truth_class"] = "REPORTED"
            c.setdefault("falsification_path", "mesti disokong bukti bebas sebelum jadi DER/OBS")
            if c.get("type") == "trait" and c.get("actor"):
                c["type"] = "REJECTED_TRAIT_CLAIM"
                c["text"] = f"[DITOLAK F6] {c.get('text')}"
    out["category"] = category
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 4. SINK — GEOX claim ledger + scar + receipt. Semua bertrace.
# ═══════════════════════════════════════════════════════════════════════════


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


DOMAIN_DIRS = {d: (OUT / ("staged_" + d)) for d in ("geox", "wealth", "well")}
# LANDING TRUTH: fail ini STAGING TEMPATAN, bukan organ itu sendiri.
# /root/WEALTH (organ :18082) TIDAK membaca folder ini. Integrasi sebenar =
# handoff_package -> WEALTH. Jangan tuntut "WEALTH" semata-mata sebab nama folder.
LANDING_STATE = "STAGED_LOCAL_NOT_ORGAN"
for _d in DOMAIN_DIRS.values():
    _d.mkdir(exist_ok=True)


def sink(payload: dict, guard_v: GuardVerdict, source: Path, trace_id: str) -> dict:
    """Satu peristiwa -> TIGA paip keluar domain + SATU parut berganda dimensi.

    Ini pembetulan seni bina: membrane ada, corong yang bocor.
    Dry hole = rock failed (GEOX) + capital consumed (WEALTH) + decision made
    by a tired operator (WELL). Semua tiga adalah peristiwa yang SAMA.
    """
    now = datetime.now(timezone.utc).isoformat()
    proj = (payload.get("projections") or {}) if payload else {}
    counts = {d: len(proj.get(d, []) or []) for d in ("geox", "wealth", "well")}

    rec = {
        "ts": now,
        "trace_id": trace_id,
        "source_file": str(source),
        "source_sha256": _sha(str(source) + str(source.stat().st_size)),
        "category": guard_v.category,
        "guard": guard_v.to_dict(),
        "projections": proj,
        "projection_counts": counts,
        "truth_ceiling": "REPORTED",
        "state": "INGESTED_UNSUPERSEDED",
        "expected_next": "CROSS_VALIDATE dgn bukti bebas utk naik DER/OBS",
    }

    if guard_v.sink == "QUARANTINE":
        qf = QUAR / f"{now[:10]}_{trace_id}.json"
        qf.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
        return {"sink": "QUARANTINE", "path": str(qf), "record": rec, "projection_counts": counts}

    # ── fan-out: satu klaim masuk domain dia sendiri ──
    landed = {}
    for dom, ddir in DOMAIN_DIRS.items():
        items = proj.get(dom, []) or []
        if not items:
            continue
        lf = ddir / "claims.jsonl"
        with lf.open("a") as f:
            for it in items:
                f.write(
                    json.dumps(
                        {
                            "ts": now,
                            "trace_id": trace_id,
                            "domain": dom,
                            "source_file": str(source),
                            "event_type": payload.get("event_type"),
                            "project": payload.get("project"),
                            "basin": payload.get("basin"),
                            "claim": it,
                            "truth_ceiling": "REPORTED",
                            "state": "INGESTED_UNSUPERSEDED",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        landed[dom] = str(lf)

    # ── SCAR: satu entri, DUA dimensi -> calon VAULT999 ──
    scar = payload.get("scar") if payload else None
    if scar:
        sf = OUT / "scar_candidates.jsonl"
        with sf.open("a") as f:
            f.write(
                json.dumps(
                    {
                        "ts": now,
                        "trace_id": trace_id,
                        "failure_mode": scar.get("failure_mode"),
                        "constraint_imposed": scar.get("constraint_imposed"),
                        "severity": scar.get("severity"),
                        "dimensions": scar.get("dimensions") or {},
                        "status": "CANDIDATE",  # 888/F13 yang SEAL, bukan mesin
                        "source": str(source),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    # ── resit (Lane B) ──
    rf = OUT / "receipts.jsonl"
    receipt = {
        "ts": now,
        "trace_id": trace_id,
        "actor": "333-AGI",
        "action": "geox_voice_reality_ingest",
        "state": "PRODUCED->INGESTED",
        "prev_state": "AUDIO_RAW",
        "expected_next": "CROSS_VALIDATED|RETRACTED|SUPERSEDED",
        "owner": "MULTI_DOMAIN",
        "landing": LANDING_STATE,
        "organ_integration_note": "STAGED sahaja. Handoff sebenar ke organ melalui hermes_handoff_package / arif_route; bukan folder ini.",
        "domains_landed": sorted(landed),
        "projection_counts": counts,
        "evidence_required": "bukti bebas utk naik truth_class",
        "category": guard_v.category,
        "n_scar": 1 if scar else 0,
        "proprietary_flag": (payload or {}).get("proprietary_flag") or guard_v.proprietary_flag,
    }
    with rf.open("a") as f:
        f.write(json.dumps(receipt, ensure_ascii=False) + "\n")

    return {"sink": "MULTI_DOMAIN", "landed": landed, "receipts": str(rf), "projection_counts": counts, "record": rec}


# ═══════════════════════════════════════════════════════════════════════════
# 5. ORCHESTRA — satu fail masuk, satu rekod keluar.
# ═══════════════════════════════════════════════════════════════════════════


# Nama fail yang sudah dikenal pasti sebagai content peribadi/relationship.
# Ditapis SEBELUM ASR — jimat kuota, jangan transkrip apa yang bukan milik GEOX.
PERSONAL_FILENAME_PREFIX = ("syed", "sado", "magnesium", "ronaldo", "arif-wake", "arif-syed", "arif-meeting", "shadow")


def filename_pre_guard(path: Path):
    """Tapisan pra-ASR (F4/F5). Pulangkan GuardVerdict jika nama fail sudah jelas."""
    stem = path.stem.lower()
    if any(stem.startswith(pref) or pref in stem for pref in PERSONAL_FILENAME_PREFIX):
        return GuardVerdict(
            "PERSONAL",
            "QUARANTINE",
            0.80,
            ["PRA_ASR_filename_personal", "F5_private_bukan_geox", "kuota_tidak_dibakar"],
            [],
            False,
        )
    return None


def ingest_transcript(text: str, audio_path: Path | None = None, kind: str = "voice_note") -> dict:
    """Ingest TRANKRIP YANG SUDAH ADA — tanpa ASR.

    Titik masuk untuk gateway yang sudah buat STT sendiri.
    Disiplin kuota (INIT-MULTIMODAL-QUOTA §2): JANGAN bakar ASR dua kali
    untuk audio yang sama. Gateway STT -> transkrip -> sini terus.

    F1: tiada mutasi audio · F2: truth_ceiling kekal REPORTED · F4: ΔS<=0
    """
    if not (text or "").strip():
        return {"status": "REJECTED", "reason": "transkrip kosong", "asr_lane": "gateway_stt", "trace_id": "-"}

    if audio_path:
        src = Path(audio_path)
        trace_id = f"VR-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{_sha(str(src) + text[:64])}"
        pre = filename_pre_guard(src)
        if pre is not None:
            r = sink({}, pre, src, trace_id)
            return {
                "trace_id": trace_id,
                "status": "QUARANTINED",
                "category": pre.category,
                "reasons": pre.reasons,
                "path": r["path"],
                "asr_lane": "skipped_pre_guard",
            }
    else:
        # Tiada fail audio (transkrip terus dari gateway STT). Tulis sebagai artifak
        # sebenar — sink() perlukan saiz fail, dan realiti patut kekal di disk.
        trace_id = f"VR-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{_sha(text[:64])}"
        src = OUT / f"{trace_id}.txt"
        src.write_text(text, encoding="utf-8")

    if not (text or "").strip():
        return {"trace_id": trace_id, "status": "REJECTED", "reason": "transkrip kosong", "asr_lane": "gateway_stt"}

    gv = guard(text)

    if gv.sink == "QUARANTINE":
        r = sink({}, gv, src, trace_id)
        return {
            "trace_id": trace_id,
            "status": "QUARANTINED",
            "category": gv.category,
            "reasons": gv.reasons,
            "path": r["path"],
            "asr_lane": "gateway_stt",
        }

    ext = metabolize(text, gv.category)
    if "reject" in ext:
        gv.sink = "QUARANTINE"
        gv.category = "UNKNOWN"
        gv.reasons.append(f"metabolize_reject={ext['reject']}")
        r = sink({}, gv, src, trace_id)
        return {"trace_id": trace_id, "status": "QUARANTINED", "reason": ext["reject"], "path": r["path"]}

    r = sink(ext, gv, src, trace_id)
    return {
        "trace_id": trace_id,
        "status": "INGESTED",
        "category": gv.category,
        "project": ext.get("project"),
        "basin": ext.get("basin"),
        "event_type": ext.get("event_type"),
        "projections": r.get("projection_counts", {}),
        "n_actions": len(ext.get("actions", [])),
        "n_scar": 1 if ext.get("scar") else 0,
        "scar_dimensions": (ext.get("scar") or {}).get("dimensions", {}) if ext.get("scar") else {},
        "proprietary_flag": ext.get("proprietary_flag") or gv.proprietary_flag,
        "named_persons": ext.get("named_persons", []),
        "asr_lane": "gateway_stt",
        "asr_usage": {},
        "receipts": r.get("receipts"),
        "ledger": r.get("ledger"),
    }


def ingest_file(path: Path, kind: str = "voice_note", dry_run: bool = False) -> dict:
    trace_id = f"VR-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{_sha(str(path))}"

    pre = filename_pre_guard(path)
    if pre is not None:
        r = sink({}, pre, path, trace_id)
        return {
            "trace_id": trace_id,
            "status": "QUARANTINED",
            "category": pre.category,
            "reasons": pre.reasons,
            "path": r["path"],
            "asr_lane": "skipped_pre_guard",
        }

    if path.suffix.lower() in (".txt", ".md", ".json"):
        text = path.read_text(errors="replace")
        asr_meta = {"lane": "transcript_direct", "usage": {}}
    else:
        asr_meta = decode(path, trace_id=trace_id, hold_late_expiry=HOLD_LATE_EXPIRY)
        text = asr_meta.get("text", "")

    if not text.strip():
        return {"trace_id": trace_id, "status": "REJECTED", "reason": asr_meta.get("error", "transkrip kosong"), "asr": asr_meta}

    gv = guard(text)
    if dry_run:
        return {
            "trace_id": trace_id,
            "status": "DRY_RUN",
            "guard": gv.to_dict(),
            "chars": len(text),
            "preview": text[:400],
            "asr_lane": asr_meta.get("lane"),
        }

    if gv.sink == "QUARANTINE":
        r = sink({}, gv, path, trace_id)
        return {
            "trace_id": trace_id,
            "status": "QUARANTINED",
            "category": gv.category,
            "reasons": gv.reasons,
            "path": r["path"],
            "asr_lane": asr_meta.get("lane"),
        }

    ext = metabolize(text, gv.category)
    if "reject" in ext:
        gv.sink = "QUARANTINE"
        gv.category = "UNKNOWN"
        gv.reasons.append(f"metabolize_reject={ext['reject']}")
        r = sink({}, gv, path, trace_id)
        return {"trace_id": trace_id, "status": "QUARANTINED", "reason": ext["reject"], "path": r["path"]}

    r = sink(ext, gv, path, trace_id)
    return {
        "trace_id": trace_id,
        "status": "INGESTED",
        "category": gv.category,
        "project": ext.get("project"),
        "basin": ext.get("basin"),
        "event_type": ext.get("event_type"),
        "projections": r.get("projection_counts", {}),
        "n_actions": len(ext.get("actions", [])),
        "n_scar": 1 if ext.get("scar") else 0,
        "scar_dimensions": (ext.get("scar") or {}).get("dimensions", {}) if ext.get("scar") else {},
        "proprietary_flag": ext.get("proprietary_flag") or gv.proprietary_flag,
        "named_persons": ext.get("named_persons", []),
        "asr_lane": asr_meta.get("lane"),
        "asr_usage": asr_meta.get("usage", {}),
        "receipts": r.get("receipts"),
        "ledger": r.get("ledger"),
    }


def main():
    ap = argparse.ArgumentParser(description="GEOX Voice Reality Ingestion")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("guard")
    g.add_argument("text")
    i = sub.add_parser("ingest")
    i.add_argument("path")
    i.add_argument("--kind", default="voice_note")
    i.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("batch")
    b.add_argument("dir")
    b.add_argument("--dry-run", action="store_true")
    b.add_argument("--glob", default="*")

    a = ap.parse_args()

    if a.cmd == "guard":
        print(json.dumps(guard(a.text).to_dict(), ensure_ascii=False, indent=2))
    elif a.cmd == "ingest":
        print(json.dumps(ingest_file(Path(a.path), a.kind, a.dry_run), ensure_ascii=False, indent=2))
    elif a.cmd == "batch":
        files = sorted(Path(a.dir).glob(a.glob))
        files = [f for f in files if f.suffix.lower() in (".ogg", ".mp3", ".wav", ".m4a", ".opus", ".flac", ".txt", ".md")]
        print(f"# {len(files)} fail ditemui", file=sys.stderr)
        for f in files:
            try:
                r = ingest_file(f, dry_run=a.dry_run)
            except Exception as e:
                r = {"trace_id": "-", "status": "ERROR", "file": str(f), "error": str(e)[:300]}
            print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
