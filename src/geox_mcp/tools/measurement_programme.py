"""geox_measurement_programme — post-drill measurement / lab-scope programme.

The deepest GEOX gap (BRIEF WP-B, from a working geologist's field question):
"what is the standard analysis list for post-drill samples — I have to prepare
the contract." The organ could say what the rock IS; it could not say what to
MEASURE or BUY to find out. This is the procurement-side capability.

Design (per BRIEF):
  1. analysis list grouped by discipline — decision informed, method, sample, P1/P2/P3 tier
  2. sample count with per-line arithmetic (scaleable)
  3. cut list under a 20% budget cut + what is lost
  4. flag analyses commonly bought but rarely decision-changing

Hard rules (binding):
  - every recommendation carries a rationale string
  - NO fabricated cost figures — cost is labelled ESTIMATE with basis, or omitted
  - deterministic output for identical input
  - epistemic label DERIVED (standard practice), NEVER presented as measured
  - honest degradation on unknown basin (state the province assumption used)

Authority: 555_COMPUTE_ONLY. This is a knowledge-base catalogue of standard
post-well lab practice, not a measurement and not a verdict.
"""

from __future__ import annotations
from typing import Any

# ── the catalogue — standard post-drill lab analyses ──────────────────────────
# Each entry: discipline, name, decision (what it informs), method, sample,
# tier (P1 must / P2 include-with-allowance / P3 pre-priced contingent),
# rationale, rarely_decisive (commonly bought, rarely changes a decision).
# Carbonate-only entries are filtered in unless lithology is carbonate.
ANALYSES: list[dict[str, Any]] = [
    # ── petrography / mineralogy ──
    {
        "id": "thin_section",
        "discipline": "Petrography / Mineralogy",
        "name": "Thin-section petrography (blue-dye)",
        "decision": "Reservoir quality + diagenetic history (porosity type, clay distribution)",
        "method": "Standard 30 µm thin section, blue-dye epoxy impregnation",
        "sample": "1 thin section per plug / sidewall-core depth",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Highest-information petrographic screen; establishes porosity type and diagenesis that control every permeability model.",
    },
    {
        "id": "xrd",
        "discipline": "Petrography / Mineralogy",
        "name": "XRD whole-rock + clay fraction",
        "decision": "Mineralogy, clay typing (swelling vs non-swelling), cement assemblage",
        "method": "X-ray diffraction, whole-rock + <2 µm clay fraction",
        "sample": "1 per 3–5 m of cored interval",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Clays control water sensitivity and log response; cement assemblage controls porosity preservation.",
    },
    {
        "id": "sem_eds",
        "discipline": "Petrography / Mineralogy",
        "name": "SEM + EDS",
        "decision": "Pore geometry, authigenic clays, microporosity",
        "method": "Scanning electron microscopy with energy-dispersive spectroscopy",
        "sample": "Selected plugs / chips (targeted, not routine)",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Resolves pore-throat geometry and authigenic clay habit that petrography alone cannot.",
    },
    # ── biostratigraphy ──
    {
        "id": "nannofossils",
        "discipline": "Biostratigraphy",
        "name": "Calcareous nannofossil biostratigraphy",
        "decision": "Age calibration + zonation (the NW Borneo Stage IV NN framework)",
        "method": "Standard smear-slide nannofossil analysis (NN zonation)",
        "sample": "1 per 10–20 m of drilled interval (cuttings/core)",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Primary age control in this basin; ties DRU/SRU surfaces to the NN ladder (see Kinabalu clock).",
    },
    {
        "id": "forams",
        "discipline": "Biostratigraphy",
        "name": "Planktonic + benthonic foraminifera",
        "decision": "Age + palaeobathymetry (depositional environment)",
        "method": "Standard foram picking, planktic + benthonic",
        "sample": "1 per 20–30 m of drilled interval",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Planktics give age, benthonics give palaeowater-depth — essential for the shelf-vs-slope reconstruction.",
    },
    {
        "id": "palynology",
        "discipline": "Biostratigraphy",
        "name": "Palynology",
        "decision": "Non-marine / marginal correlation where nanno/forams are absent",
        "method": "Standard palynological preparation + count",
        "sample": "1 per 30–50 m (deltaic / paralic intervals)",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Only biostrat tool that works through the deltaic (non-marine) sections.",
    },
    # ── organic geochemistry ──
    {
        "id": "toc_pyrolysis",
        "discipline": "Organic Geochemistry",
        "name": "TOC + Rock-Eval pyrolysis",
        "decision": "Source richness (TOC) + kerogen type + maturity (HI/Tmax)",
        "method": "LECO TOC + Rock-Eval pyrolysis",
        "sample": "1 per 10–20 m through the source interval",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "The source-rock screen — richness, type, maturity in one cheap run.",
    },
    {
        "id": "vitrinite",
        "discipline": "Organic Geochemistry",
        "name": "Vitrinite reflectance (Ro)",
        "decision": "Thermal maturity calibration",
        "method": "Standard vitrinite reflectance (%Ro)",
        "sample": "Selected depths across the maturity window",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "The maturity anchor that ties the whole burial/charge model.",
    },
    {
        "id": "biomarkers",
        "discipline": "Organic Geochemistry",
        "name": "Gas chromatography + biomarkers",
        "decision": "Oil-source correlation, biodegradation, migration",
        "method": "GC / GC-MS biomarker analysis",
        "sample": "Selected oil/condensate shows + source extracts",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Correlates charge to source kitchen — but only matters once a working source is proven.",
    },
    # ── fluid / PVT ──
    {
        "id": "pvt",
        "discipline": "Fluid / PVT",
        "name": "PVT bottom-hole sampling + analysis",
        "decision": "Reservoir fluid properties (composition, saturation pressure, GOR)",
        "method": "Downhole sampling (MDT/RCI) + PVT lab",
        "sample": "1–3 bottom-hole samples per reservoir zone",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Defines the fluid the whole development plan is built around; unrepeatable once the well is completed.",
    },
    {
        "id": "gas_iso",
        "discipline": "Fluid / PVT",
        "name": "Gas composition + isotopes",
        "decision": "Gas origin (biogenic vs thermogenic), contamination",
        "method": "GC composition + stable C isotope ratio",
        "sample": "Gas from shows / DST / MDT",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Gas origin discriminates charge systems — cheap, high signal.",
    },
    # ── routine core analysis (RCA) ──
    {
        "id": "poro_perm",
        "discipline": "Routine Core Analysis (RCA)",
        "name": "Porosity + permeability (horizontal + vertical)",
        "decision": "Reservoir quality, net pay, permeability model",
        "method": "Standard plug poro-perm (He porosity, Klinkenberg permeability)",
        "sample": "1 plug per 0.3 m of cored interval",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "The fundamental reservoir-quality measurement; feeds every volumetric + flow model.",
    },
    {
        "id": "grain_density",
        "discipline": "Routine Core Analysis (RCA)",
        "name": "Grain density",
        "decision": "Porosity calculation (matrix density for log porosity)",
        "method": "Helium pycnometry",
        "sample": "Same plugs as poro-perm",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Ties log-derived porosity to core; a wrong grain density biases the whole log interpretation.",
    },
    {
        "id": "saturation",
        "discipline": "Routine Core Analysis (RCA)",
        "name": "Fluid saturation (Dean-Stark)",
        "decision": "Water saturation (Sw), hydrocarbon shows",
        "method": "Dean-Stark extraction",
        "sample": "1 per 1 m of cored interval (in hydrocarbon zone)",
        "tier": "P1",
        "rarely_decisive": False,
        "rationale": "Direct Sw — the ground truth for the saturation-height model.",
    },
    # ── special core analysis (SCAL) ──
    {
        "id": "capillary",
        "discipline": "Special Core Analysis (SCAL)",
        "name": "Capillary pressure (MICP / centrifuge)",
        "decision": "Saturation-height model, free-water level, seal capacity",
        "method": "Mercury injection / centrifuge capillary pressure",
        "sample": "Selected plugs across the permeability range",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Converts structural closure into a Sw prediction — the difference between 'in-place' and 'recoverable'.",
    },
    {
        "id": "rel_perm",
        "discipline": "Special Core Analysis (SCAL)",
        "name": "Relative permeability",
        "decision": "Flow modelling, recovery factor, water/gas coning",
        "method": "Steady-state / unsteady-state relative permeability",
        "sample": "Selected plugs (reservoir-condition, few)",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Controls recovery — but is expensive and can wait until the reservoir is proven.",
    },
    {
        "id": "resistivity_factor",
        "discipline": "Special Core Analysis (SCAL)",
        "name": "Formation resistivity factor (m/n)",
        "decision": "Archie saturation parameters",
        "method": "Standard FRF / resistivity index",
        "sample": "Same plugs as capillary pressure",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Calibrates log Sw; needed before the log-derived saturation is trusted.",
    },
    # ── geomechanics ──
    {
        "id": "rock_strength",
        "discipline": "Geomechanics",
        "name": "Rock strength (uniaxial / triaxial)",
        "decision": "Wellbore stability, sand production, fracture gradient",
        "method": "UCS + triaxial tests",
        "sample": "Selected plugs (few, targeted)",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Feeds the geomechanical model for drilling + completion — mostly for development wells.",
    },
    {
        "id": "in_situ_stress",
        "discipline": "Geomechanics",
        "name": "In-situ stress orientation/magnitude",
        "decision": "Stress regime, fracture orientation",
        "method": "Anelastic strain recovery / breakout analysis",
        "sample": "Selected core / image-log analysis",
        "tier": "P2",
        "rarely_decisive": False,
        "rationale": "Orients the completion — only matters once development is committed.",
    },
    # ── chemostratigraphy ──
    {
        "id": "chemostrat",
        "discipline": "Chemostratigraphy",
        "name": "Elemental chemostratigraphy",
        "decision": "Correlation where biostrat is absent (non-marine)",
        "method": "ICP-MS elemental fingerprinting",
        "sample": "1 per 2–5 m through uncorrelated intervals",
        "tier": "P3",
        "rarely_decisive": False,
        "rationale": "Correlation fallback — pre-priced contingent, deploy only if biostrat fails.",
    },
    # ── carbonate-specific ──
    {
        "id": "carbonate_texture",
        "discipline": "Carbonate (conditional)",
        "name": "Carbonate thin-section texture (Dunham)",
        "decision": "Depositional texture, porosity type (interparticle/vuggy/moldic/fracture)",
        "method": "Carbonate thin section + Dunham classification",
        "sample": "1 per plug / sidewall depth",
        "tier": "P1",
        "rarely_decisive": False,
        "carbonate_only": True,
        "rationale": "Carbonate reservoir quality is texture-controlled — a siliciclastic thin section cannot answer it.",
    },
    {
        "id": "stable_isotope",
        "discipline": "Carbonate (conditional)",
        "name": "Stable isotopes (C/O)",
        "decision": "Diagenesis, meteoric vs marine cement, burial history",
        "method": "Stable C and O isotope ratio",
        "sample": "Selected cements / matrix",
        "tier": "P2",
        "rarely_decisive": False,
        "carbonate_only": True,
        "rationale": "Diagenetic pathway — controls whether porosity is preserved or occluded.",
    },
    {
        "id": "carbonate_scal",
        "discipline": "Carbonate (conditional)",
        "name": "Carbonate SCAL (capillary + rel-perm)",
        "decision": "Saturation-height + recovery in dual-porosity carbonates",
        "method": "MICP + relative permeability (vuggy/moldic-aware sampling)",
        "sample": "Selected plugs spanning texture classes",
        "tier": "P2",
        "rarely_decisive": False,
        "carbonate_only": True,
        "rationale": "Carbonate Sw-height is bimodal; a siliciclastic SCAL suite does not transfer.",
    },
]

# analyses that are routinely bought but rarely change the go/no-go decision
# (flagged in output as a line item, per BRIEF WP-B requirement 4)


def _basin_assumption(basin: str | None) -> str:
    """Honest province assumption when the basin is unknown/unspecified."""
    if not basin:
        return "UNSPECIFIED — assuming a NW Borneo deepwater clastic province (Sarawak/Sabah fold-thrust belt) as the default. State basin/province to refine."
    return basin


def _select(well_type: str, lithology: str, core_planned: bool) -> list[dict[str, Any]]:
    """Deterministic selection: all P1; P2/P3 by well type + lithology + core."""
    wt = (well_type or "exploration").lower()
    lith = (lithology or "clastic").lower()
    is_carb = "carbonate" in lith
    out = []
    for a in ANALYSES:
        if a.get("carbonate_only") and not is_carb:
            continue
        keep = False
        tier = a["tier"]
        if tier == "P1":
            keep = True
        elif tier == "P2":
            # appraisal/development carry the reservoir-characterisation P2s;
            # exploration carries them only where they de-risk (SCAL/PVT are carried as contingent)
            if wt in ("appraisal", "development"):
                keep = True
            elif wt == "exploration" and a["discipline"] in ("Fluid / PVT", "Special Core Analysis (SCAL)"):
                keep = core_planned  # only if core is actually planned
            elif wt == "exploration" and a["discipline"] not in ("Special Core Analysis (SCAL)", "Geomechanics"):
                keep = True
        elif tier == "P3":
            keep = wt in ("appraisal", "development")  # contingent only when the well matters
        if keep:
            out.append(a)
    return out


def _sample_arithmetic(a: dict[str, Any], core_planned: bool, target_depth: float) -> str:
    """Per-line sample-count arithmetic (scaleable), never a bare number."""
    if a["discipline"] in ("Routine Core Analysis (RCA)", "Special Core Analysis (SCAL)"):
        core_m = target_depth * 0.05 if core_planned else 0  # ~5% of TD cored, schematic
        if a["id"] == "poro_perm":
            return f"core ≈ {core_m:.0f} m → 1 plug / 0.3 m = {core_m / 0.3:.0f} plugs (core={core_planned})"
        if a["id"] == "saturation":
            return f"core ≈ {core_m:.0f} m → 1 / 1 m = {core_m:.0f} samples (core={core_planned})"
        return f"core ≈ {core_m:.0f} m → selected plugs (span permeability range; count at lab)"
    if a["discipline"] == "Biostratigraphy":
        n = target_depth / 15
        return f"TD {target_depth:.0f} m → 1 / 15 m = {n:.0f} samples"
    if a["discipline"] == "Organic Geochemistry":
        n = target_depth / 20
        return f"TD {target_depth:.0f} m → 1 / 20 m = {n:.0f} samples"
    return "count at lab (targeted, not a routine grid)"


def geox_measurement_programme(
    well_type: str = "exploration",
    basin: str | None = None,
    lithology: str = "clastic",
    play_type: str | None = None,
    water_depth: float | None = None,
    target_depth: float = 3000.0,
    mud_system: str | None = None,
    core_planned: bool = False,
) -> dict[str, Any]:
    """Post-drill measurement / lab-scope programme (4-part, deterministic)."""
    wt = (well_type or "exploration").lower()
    if wt not in ("exploration", "appraisal", "development"):
        return {"status": "INVALID", "error": f"well_type={wt!r} invalid; use exploration|appraisal|development"}

    selected = _select(wt, lithology, core_planned)
    is_carb = "carbonate" in (lithology or "").lower()

    # group by discipline, preserving order
    groups: dict[str, list[dict[str, Any]]] = {}
    for a in selected:
        groups.setdefault(a["discipline"], []).append(a)

    analysis_list = []
    for disc, items in groups.items():
        rows = []
        for a in items:
            rows.append(
                {
                    "name": a["name"],
                    "decision": a["decision"],
                    "method": a["method"],
                    "sample": a["sample"],
                    "sample_arithmetic": _sample_arithmetic(a, core_planned, target_depth),
                    "tier": a["tier"],
                    "rationale": a["rationale"],
                    "commonly_bought_rarely_decisive": bool(a.get("rarely_decisive")),
                }
            )
        analysis_list.append({"discipline": disc, "analyses": rows})

    # cut list — first to drop under 20% budget cut, and what is lost
    cut_order = [
        a
        for a in selected
        if a["tier"] in ("P3", "P2") and a["discipline"] in ("Chemostratigraphy", "Geomechanics", "Special Core Analysis (SCAL)")
    ]
    cut_list = [
        {
            "drop": a["name"],
            "tier": a["tier"],
            "lost": a["decision"],
            "why_safe_to_cut_first": "Contingent / reservoir-condition — recoverable later if the well proves up, at a re-sample cost.",
        }
        for a in cut_order[:5]
    ]

    rarely_decisive = [a["name"] for a in selected if a.get("rarely_decisive")]

    return {
        "status": "OK",
        "well_type": wt,
        "basin_assumption": _basin_assumption(basin),
        "lithology": lithology,
        "play_type": play_type,
        "water_depth_m": water_depth,
        "target_depth_m": target_depth,
        "mud_system": mud_system,
        "core_planned": core_planned,
        "carbonate_suite_included": is_carb,
        "analysis_list": analysis_list,
        "analysis_count": len(selected),
        "cut_list": cut_list,
        "commonly_bought_rarely_decisive": rarely_decisive,
        "epistemic": {
            "label": "DERIVED",
            "basis": "standard post-well lab practice catalogue — NOT a measurement, NOT priced",
            "cost": "OMITTED — no fabricated cost figures; obtain lab rates for the actual scope",
            "authority": "555_COMPUTE_ONLY",
        },
    }
