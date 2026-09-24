#!/usr/bin/env python3
"""
GEOX Voice Reality — hook Telegram.

EVENT-DRIVEN (bukan cron — F13 solution-architecture preference):
  dipanggil SELEPAS STT voice note berjaya. Satu panggilan, satu kad ringkas.

Pautan (anchor sedia ada, lihat voice-state-membrane.yaml):
  gateway/run_inbound.py
    after: event._gateway_pending_stt_transcripts = list(successful_transcripts)
    ->  from hooks.telegram_voice_hook import on_voice_note
        for t in event._gateway_pending_stt_transcripts:
            on_voice_note(t.get("audio_path") or t.get("path"), t.get("text"))

Penggunaan terus:
  python3 telegram_voice_hook.py /path/ke/voice.ogg
  python3 telegram_voice_hook.py --watch /root/.hermes/workspace   # inotify, bukan poll
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reality_ingest import ingest_file, guard  # noqa: E402

AUDIO = {".ogg", ".mp3", ".wav", ".m4a", ".opus", ".flac"}


def render_card(result: dict) -> str:
    """Satu kad ringkas. Mesin lapor, manusia putuskan."""
    st = result.get("status")
    if st == "QUARANTINED":
        return f"⛔ Dikuarentin ({result.get('category')}). Bukan untuk GEOX. Sebab: {', '.join(result.get('reasons', [])[:2])}"

    if st == "INGESTED":
        proj = result.get("projections") or {}
        bits = [f"✅ Direkod: {result.get('project') or 'tanpa projek'}"]
        if result.get("event_type"):
            bits.append(f"jenis {result['event_type']}")
        dom = " · ".join(f"{k.upper()} {v}" for k, v in proj.items() if v) or "tiada unjuran"
        bits.append(f"→ {dom}")
        if result.get("n_scar"):
            dims = result.get("scar_dimensions") or {}
            dtxt = "+".join(k for k, v in dims.items() if v) or "?"
            bits.append(f"**1 SCAR** [{dtxt}]")
        if result.get("named_persons"):
            names = ", ".join(p2.get("name", "?") for p2 in result["named_persons"])
            bits.append(f"nama: {names} (pernyataan)")
        if result.get("proprietary_flag"):
            bits.append("⚠️ proprietary")
        bits.append(f"trace {result.get('trace_id', '-')[:14]}")
        return " · ".join(bits)

    return f"⚠️ {st}: {result.get('reason', result.get('error', '-'))}"


def on_voice_note(audio_path: str | None, transcript: str | None = None) -> str:
    """Titik masuk event-driven. Pulangkan kad ringkas untuk bot."""
    if not audio_path:
        return "⚠️ tiada fail audio"
    p = Path(audio_path)
    if not p.exists():
        return f"⚠️ fail tidak wujud: {p.name}"

    try:
        result = ingest_file(p, kind="voice_note")
    except Exception as e:  # jangan sekali-kali jatuhkan giliran bot
        return f"⚠️ ingest gagal: {str(e)[:120]}"
    return render_card(result)


def watch(directory: str, settle_s: float = 2.0) -> None:
    """inotify (event-driven). Poll hanya sebagai fallback terakhir."""
    d = Path(directory)
    seen = {f.name for f in d.iterdir() if f.suffix.lower() in AUDIO}
    print(f"# watch {d} — {len(seen)} fail sedia ada diabaikan", file=sys.stderr)
    try:
        import inotify.adapters  # type: ignore

        i = inotify.adapters.InotifyTree(str(d))
        for event in i.event_gen(yield_nones=False, timeout_s=30):
            (_, types, _, fname) = event
            if "IN_CLOSE_WRITE" not in types:
                continue
            f = d / fname
            if f.suffix.lower() not in AUDIO or f.name in seen:
                continue
            time.sleep(settle_s)  # biarkan selesai ditulis
            seen.add(f.name)
            print(json.dumps({"file": str(f), "card": on_voice_note(str(f))}, ensure_ascii=False))
    except ImportError:
        print("# inotify tiada — fallback poll 5s", file=sys.stderr)
        while True:
            for f in d.iterdir():
                if f.suffix.lower() in AUDIO and f.name not in seen:
                    seen.add(f.name)
                    print(json.dumps({"file": str(f), "card": on_voice_note(str(f))}, ensure_ascii=False))
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--watch":
        watch(sys.argv[2])
    elif len(sys.argv) >= 2:
        print(on_voice_note(sys.argv[1]))
    else:
        print(__doc__)
        sys.exit(1)
