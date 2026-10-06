"""
model_physics.py — Physics-grounded geological modeling modes for geox_model.
Forged 2026-10-06 by 333-AGI under F13 directive: "upgrade GEOX MCP tools to enable
proper cross section and geological model based on physics and geomechanics of dynamic earth".

Three modes:
  flexure         — elastic plate flexure: Te → forebulge distance (known-answer tested)
  physics_section — spine-driven cross-section renderer (asas_malam_xs.py) with confidentiality gate
  critical_taper  — REFERENCE-GATED: Davis-Supe-Dahlen 1983 eq(22)+(28) not yet implemented
                    from verified source text (F2 discipline — no hand-written formulas from memory)

Governance: COMPUTE_ONLY. No PETRONAS/partner confidential data in any path, ever.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

# ── Physics constants (assumed; stated in every output) ──
E_YOUNG = 70e9  # Pa (assumed)
NU_POISSON = 0.25  # (assumed)
RHO_MANTLE = 3300.0  # kg/m³ (assumed)
G_GRAVITY = 9.81  # m/s²
RHO_SEDIMENT_INFILL = 2400.0  # kg/m³ (assumed)
RHO_WATER_INFILL = 1030.0  # kg/m³ (assumed)

_SECTION_SCRIPT = Path("/root/GEOX/geox/skills/subsurface/section/asas_malam_xs.py")
_SPINE_YAML = Path("/root/GEOX/okf/sabah-basin/kinabalu_event_spine.yaml")
_FORBIDDEN_STRINGS = ["Pekaka", "LL-1", "Megah", "Zoisit", "Nuri", "Rotan"]
# 2026-10-06 (auditor fix #3): pattern-level gate — reserve figures + well-name shapes
_FORBIDDEN_PATTERNS = [
    r"\b\d+(\.\d+)?\s*(?:MMbbl|MMstb|Tcf|Bcf|bboe)\b",   # volume/reserve figures
    r"\bOOIP\b|\bGIIP\b|\bSTOIIP\b",                        # reserve-class terms
    r"\b[A-Z][a-zA-Z]{2,}(?:\s?Deep)?\s?-?\s?\d\b",         # well-name shape ("Xxx-1", "Xxx Deep-1")
]
_FORBIDDEN_ALLOWLIST = ["Tepat"]  # published well (Banerjee & Salim 2020, JNGSE 83)


def compute_flexure(
    te_km: float | list[float] | None = None,
    infill: str = "sediment",
    plate: str = "continuous",
    rho_mantle: float = RHO_MANTLE,
    rho_infill: float | None = None,
) -> dict:
    """Elastic plate flexure: Te → flexural parameter a, forebulge distance.

    Physics: D = E·Te³ / (12·(1-ν²));  a = (4D / ((ρm-ρi)·g))^(1/4)
    Forebulge: continuous plate ≈ π·a; broken plate ≈ 0.75·π·a
    (Watts 2001, Isostasy and Flexure of the Lithosphere, ch. 3–5.)

    Known-answer anchors (sediment infill ρ=2400, ρm=3300):
      Te=10 km → a≈41.0 km, forebulge_cont≈129 km, forebulge_broken≈97 km
    """
    if rho_infill is None:
        rho_infill = RHO_SEDIMENT_INFILL if inffill_valid(infill) else RHO_WATER_INFILL
    if te_km is None:
        te_km = [5, 10, 15, 20, 30]
    te_list = [te_km] if isinstance(te_km, (int, float)) else list(te_km)
    results = []
    for te in te_list:
        te_m = te * 1e3
        D = E_YOUNG * te_m**3 / (12 * (1 - NU_POISSON**2))  # N·m
        rho_diff = rho_mantle - rho_infill
        if rho_diff <= 0:
            raise ValueError(f"ρ_mantle ({rho_mantle}) must exceed ρ_infill ({rho_infill})")
        a = (4 * D / (rho_diff * G_GRAVITY)) ** 0.25  # m
        a_km = a / 1e3
        if plate == "continuous":
            forebulge_km = 3.14159265358979 * a_km
        elif plate == "broken":
            forebulge_km = 0.75 * 3.14159265358979 * a_km
        else:
            raise ValueError(f"plate must be 'continuous' or 'broken', got '{plate}'")
        results.append(
            {
                "te_km": te,
                "flexural_rigidity_D_Nm": round(D, 2),
                "flexural_parameter_a_km": round(a_km, 2),
                "forebulge_distance_km": round(forebulge_km, 1),
            }
        )
    return {
        "mode": "flexure",
        "tool": "geox_model",
        "plate_model": plate,
        "infill_density_kgm3": rho_infill,
        "assumptions": {
            "E_Pa": E_YOUNG,
            "nu": NU_POISSON,
            "rho_mantle_kgm3": rho_mantle,
            "E_source": "assumed",
            "nu_source": "assumed",
        },
        "formula": "D = E·Te³/(12(1-ν²));  a = (4D/((ρm-ρi)g))^(1/4);  forebulge = π·a (continuous) | 0.75π·a (broken)",
        "results": results,
        "note": "Assumed E, ν, ρ. A measured forebulge on 3D fixes Te; if no realistic Te fits, the trough is not a simple flexural moat.",
        "compute_output_partner_free": True,
        "fail_closed": True,
        "residual_interpretation": "Computation = forebulge distance under stated assumptions. Interpretation = whether this mechanism explains Sabah Trough (requires measured forebulge on MC3D). Observation = whether the predicted feature exists on the actual transect (L2 until measured).",
        "source": "Watts (2001) Isostasy and Flexure; validated against ASAS-MALAM figure computation 2026-10-06.",
    }


def inffill_valid(infill: str) -> bool:
    if infill == "sediment":
        return True
    if infill == "water":
        return False
    raise ValueError(f"infill must be 'sediment' or 'water', got '{infill}'")


def render_physics_section(
    transect: str = "sabah_nw_se",
    theme: str = "dark",
    out_dir: str | None = None,
) -> dict:
    """Render a spine-driven, physics-annotated cross-section via asas_malam_xs.py.

    The renderer reads age labels from kinabalu_event_spine.yaml, ensuring figure
    and framework cannot drift. Includes a confidentiality gate: the rendered
    SVG is scanned for forbidden partner-data strings before returning.

    Returns: artifact paths + provenance + physics annotations + L0/L1/L2 manifest.
    """
    if transect != "sabah_nw_se":
        return {
            "mode": "physics_section",
            "tool": "geox_model",
            "status": "ERROR",
            "error": f"Unknown transect '{transect}'. Currently supported: 'sabah_nw_se'.",
        }
    if theme not in ("dark", "light"):
        return {
            "mode": "physics_section",
            "tool": "geox_model",
            "status": "ERROR",
            "error": f"theme must be 'dark' or 'light', got '{theme}'.",
        }
    if not _SECTION_SCRIPT.exists():
        return {
            "mode": "physics_section",
            "tool": "geox_model",
            "status": "ERROR",
            "error": f"Renderer script not found: {_SECTION_SCRIPT}",
        }
    default_out = str(_SECTION_SCRIPT.parent / "output")
    out = out_dir or default_out
    os.makedirs(out, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(_SECTION_SCRIPT), theme],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(_SECTION_SCRIPT.parent),
    )
    if proc.returncode != 0:
        return {
            "mode": "physics_section",
            "tool": "geox_model",
            "status": "ERROR",
            "error": f"Renderer exited {proc.returncode}: {proc.stderr[-500:]}",
        }
    png = Path(out) / f"asas_malam_xs_{theme}.png"
    svg = Path(out) / "asas_malam_xs.svg"
    pdf = Path(out) / "asas_malam_xs_print.pdf"
    artifacts = [str(p) for p in (png, svg, pdf) if p.exists()]
    # confidentiality gate
    scan_clean = True
    scan_hits = []
    if svg.exists():
        svg_text = svg.read_text(errors="ignore")
        for forbidden in _FORBIDDEN_STRINGS:
            if forbidden.lower() in svg_text.lower():
                scan_clean = False
                scan_hits.append(forbidden)
        import re as _re
        for pat in _FORBIDDEN_PATTERNS:
            for m in _re.finditer(pat, svg_text):
                token = m.group(0)
                if not any(al.lower() in token.lower() for al in _FORBIDDEN_ALLOWLIST):
                    scan_clean = False
                    scan_hits.append(token)
    spine_hash = "UNKNOWN"
    if _SPINE_YAML.exists():
        spine_hash = hashlib.sha256(_SPINE_YAML.read_bytes()).hexdigest()[:16]
    if not scan_clean:
        # HARDENED: withhold artifacts entirely — clean=False means the render
        # leaked; returning the artifacts alongside the flag would be a theatre gate
        return {
            "mode": "physics_section",
            "tool": "geox_model",
            "status": "BLOCKED_CONFIDENTIALITY_GATE",
            "artifacts": [],  # WITHHELD — do not serve leaked renders
            "transect": transect,
            "theme": theme,
            "confidentiality_gate": {
                "clean": False,
                "forbidden_strings_scanned": _FORBIDDEN_STRINGS,
                "hits": scan_hits,
                "action": "ARTIFACTS_WITHHELD",
                "rule": "Public-only figure. Partner-data hits = render is quarantined, not served.",
            },
            "error": f"Confidentiality gate BLOCKED: {scan_hits} found in SVG output. Artifacts withheld.",
        }
    return {
        "mode": "physics_section",
        "tool": "geox_model",
        "status": "OK",
        "artifacts": artifacts,
        "transect": transect,
        "theme": theme,
        "spine_file": str(_SPINE_YAML),
        "spine_sha256_first16": spine_hash,
        "confidentiality_gate": {
            "clean": True,
            "forbidden_strings_scanned": _FORBIDDEN_STRINGS,
            "hits": [],
            "action": "PASSED",
            "rule": "Public-only figure. Internal/partner well data is excluded by design.",
            "scope": f"SVG forbidden-string scan ({len(_FORBIDDEN_STRINGS)} strings + {len(_FORBIDDEN_PATTERNS)} patterns, allowlist {_FORBIDDEN_ALLOWLIST}). NOT a guarantee of full-output safety — HTML, PDF metadata, manifests not covered.",
        },
        "physics_annotations": [
            "Three blocks · two margins · one suture",
            "Flexure: Te 8–17 km fits 110–150 km load-to-high distance",
            "Moat relief needs sediment load + underthrust downdrag (not sag alone)",
            "Bending extension at Trough = outer-rise analog (no spreading; 5-vector falsification 2026-09-30)",
            "Wedge taper ~4° on shale detachment (within critical-taper bounds for shale-detached wedges)",
        ],
        "evidence_tiers": {
            "L0": "Topography/bathymetry (green line), Tepat-1 public result",
            "L1": "Granite U-Pb 7.85–7.22 Ma, Moho 26–33 km (non-unique), flexure curves",
            "L2": "Every subsurface surface, body, fault, closure — schematic, not seismic picks",
        },
        "renderer_stdout_tail": proc.stdout[-200:] if proc.stdout else "",
        "compute_output_partner_free": True,
        "fail_closed": True,
        "residual": {"velocity_model": "ABSENT — all depths are L2", "forebulge_measured": "ABSENT — Te range is L2", "restoration_balance": "NOT_RUN", "geomech": "NOT_RUN", "note": "A section that passes these gates earns PARTIAL, not SEAL. SEAL requires: velocity model at one well + measured forebulge + balanced restoration."},
    }


def critical_taper_reference(
    phi_deg: float | None = None,
    phi_basal_deg: float | None = None,
    lambda_pore: float | None = None,
    lambda_basal: float | None = None,
    beta_deg: float | None = None,
) -> dict:
    """REFERENCE-GATED: critical Coulomb wedge taper (Davis-Supe-Dahlen 1983).

    The closed-form solution — DSD 1983 eq(22) + eq(28), with Dahlen 1984 exactness
    correction and Wang & Hu 2006 λ≠λb reconciliation — is NOT yet implemented
    from a verified source text. This mode returns the parameter set, the reference
    chain, and the implementation plan. F2: no hand-written formulas from memory
    in a tested public tool.

    To activate: fetch DSD 1983 PDF (tectonicsweb.eu link in session evidence),
    extract eq(22) and eq(28) verbatim, implement, add known-answer test vs
    Taiwan wedge (α=2.9°, β=6°, λ≈0.7, μ=1.03, μb=0.85).
    """
    return {
        "mode": "critical_taper",
        "tool": "geox_model",
        "status": "REFERENCE_GATED",
        "reason": "F2 discipline: closed-form DSD 1983 eq(22)+(28) not yet transcribed from a verified source PDF. No formula-from-memory in tested tools.",
        "parameters_echoed": {
            "phi_internal_deg": phi_deg,
            "phi_basal_deg": phi_basal_deg,
            "lambda_pore": lambda_pore,
            "lambda_basal": lambda_basal,
            "beta_decollement_dip_deg": beta_deg,
        },
        "references": [
            "Davis, D., Suppe, J. & Dahlen, F.A. (1983) JGR 88, 1153–1172 — Mechanics of fold-and-thrust belts and accretionary wedges",
            "Dahlen, F.A. (1984) JGR 89, 10,125–10,133 — Noncohesive critical Coulomb wedges: exact solution",
            "Dahlen, F.A. (2007) GRL 34, L09307 — pore fluid pressure ratios in Coulomb wedge theory (λ≠λb correction)",
            "Wang, K. & Hu, Y. (2006) JGR 111, B06410 — Accretionary prisms in subduction earthquake cycles",
        ],
        "pdf_source_for_implementation": "http://www.tectonicsweb.eu/Classes/MAT/DavisSuppeDahlen_JGR_83.pdf",
        "known_answer_for_test": {
            "case": "western Taiwan wedge",
            "alpha_deg": 2.9,
            "beta_deg": 6.0,
            "lambda": 0.7,
            "mu_internal": 1.03,
            "mu_basal": 0.85,
            "note": "from DSD 1983 fig.14 — use as the pytest known-answer when implemented",
        },
        "implementation_task": "Extract eq(22) K-factor + eq(28) from DSD 1983 PDF → implement in this module → add pytest with Taiwan known-answer → activate this mode.",
        "compute_output_partner_free": True,
        "fail_closed": True,
        "note": "In the meantime, wedge taper is annotated as '~4° on shale detachment, within critical-taper bounds' on the physics_section figure (qualitative, from Morley et al. 2023 + GSA 2009 DWFTB).",
    }
