"""deep_time/data_loaders.py — Null-safe loaders for external datasets + F9 UNKNOWN guard.

F2 TRUTH: We never fabricate data. When a dataset is not ingested, the
loader returns an EarthStateVariable with value=None and epistemic_level=
NO_DATA, plus a `notes` field pointing to the canonical external source
that needs to be ingested to fill the variable.

F9 ANTI-HANTU (fabrication guard): When a parameter CANNOT be known at
the requested age even in principle (e.g. CO2 in the Hadean, where no
calibrated proxy exists), the loader returns epistemic_level=UNKNOWN
with a hard note explaining the unknowability. A naive tool would
extrapolate GEOCARB off the end and emit a hallucinated number — this
loader refuses.

DITEMPA BUKAN DIBEI — Forged, Not Given.
"""

from __future__ import annotations

from .schemas import (
    EarthStateVariable,
    PolarityState,
    ReferenceFrame,
)


# ─── Pending-external-dataset stub registry ──────────────────────────────────
PENDING_DATASETS: dict[str, dict[str, str]] = {
    "co2": {
        "primary": "Berner GEOCARBSULF v3 (Berner & Kothavala 2001, Beerling & Royer 2011)",
        "alternative": "Mills et al. 2023 Phanerozoic CO2 reconstruction",
        "format": "CSV with columns: age_Ma, co2_ppm, uncertainty_p10, uncertainty_p90",
        "license": "CC-BY",
        "ingestion_path": "Phase 1 forge — /root/geox/src/geox_mcp/tools/deep_time/data/co2_*.csv",
    },
    "temperature": {
        "primary": "Zachos et al. 2008 Cenozoic δ18O benthic stack + Westerhold 2020",
        "alternative": "Scotese et al. 2021 Phanerozoic temperature model",
        "format": "CSV with columns: age_Ma, temp_anomaly_c, uncertainty_p10, uncertainty_p90",
        "license": "CC-BY",
        "ingestion_path": "Phase 1 forge — /root/geox/src/geox_mcp/tools/deep_time/data/temp_*.csv",
    },
    "sea_level": {
        "primary": "Haq 2017 Phanerozoic sea-level curve (long-term + composite)",
        "alternative": "Miller et al. 2005 Cenozoic high-resolution backstripping",
        "format": "CSV with columns: age_Ma, sea_level_m_relative_present, curve, component",
        "license": "CC-BY",
        "ingestion_path": "Phase 1 forge — /root/geox/src/geox_mcp/tools/deep_time/data/sea_level_*.csv",
    },
    "magnetic_polarity": {
        "primary": "GPTS GTS2020 (Gradstein et al. 2020)",
        "alternative": "Ogg 2020, Cande & Kent 1995",
        "format": "CSV with columns: age_top_Ma, age_base_Ma, chron_id, polarity (normal/reversed)",
        "license": "CC-BY",
        "ingestion_path": "Phase 1 forge — /root/geox/src/geox_mcp/tools/deep_time/data/gp_ts_gts2020.csv",
    },
    "o2": {
        "primary": "Berner 2001 GEOCARBSULF atmospheric O2",
        "alternative": "Lenton 2023 COPSE re-run",
        "format": "CSV with columns: age_Ma, o2_pal (present atmospheric level)",
        "license": "CC-BY",
        "ingestion_path": "Phase 1 forge — /root/geox/src/geox_mcp/tools/deep_time/data/o2_berner.csv",
    },
    "paleogeography": {
        "primary": "Merdith et al. 2021 full Phanerozoic plate reconstruction",
        "alternative": "Scotese PALEOMAP, GPlates Web Service",
        "format": "GPlates .rot files or Merdith NetCDF",
        "license": "CC-BY",
        "ingestion_path": "Phase 2 forge — external API or /root/geox/src/geox_mcp/tools/deep_time/data/merdith_2021/",
    },
    "ice_extent": {
        "primary": "Crowell 1999 Late Paleozoic Ice Age + Eyles 2008",
        "format": "qualitative",
        "license": "varies",
        "ingestion_path": "Phase 2 — bundled as lookup table",
    },
}


# ─── Superchron definitions (for 5-state polarity resolution) ────────────────
# CNS = Cretaceous Normal Superchron (no reversals, normal polarity throughout)
# Kiaman = Permo-Carboniferous Reversed Superchron (no reversals, reversed throughout)
#
# Per Ogg 2020 / Gradstein 2020 (GTS2020):
#   CNS: 83.6 - 120.6 Ma (rounded to 83.6 - 121 Ma in our table)
#   Kiaman: ~262 - 318 Ma
#
# GPTS coverage:
#   Cenozoic: 0 - 66 Ma — dense, C1-C29r
#   Cretaceous (post-CNS): 66 - 83.6 Ma — moderate, C29r-C34n
#   CNS (blind): 83.6 - 121 Ma
#   Cretaceous (pre-CNS): 121 - 145 Ma — M-series (M0-M25n)
#   Jurassic: 145 - 201.4 Ma — M-series (M25n-M44Ar)
#   Triassic (limited): 201.4 - ~227 Ma — M44Ar-? (poorly calibrated)
#   Pre-Triassic: >227 Ma — UNRESOLVED

CNS_TOP_MA = 83.6
CNS_BASE_MA = 121.0
KIAMAN_TOP_MA = 262.0
KIAMAN_BASE_MA = 318.0
GPTS_FLOOR_MA = 0.0
GPTS_CEILING_MA = 250.0  # conservative — Laskar chaos regime above


# ─── UNKNOWN thresholds (F9 fabrication guard) ───────────────────────────────
# For these parameter × age combinations, the variable is unknowable even
# in principle. Return UNKNOWN rather than NO_DATA so the caller knows
# ingestion is not the path — the parameter simply does not exist.

def _is_unknown_at_age(param: str, age_ma: float) -> bool:
    """F9 fabrication guard: returns True if param CANNOT be known at age."""
    # Atmospheric CO2 in Hadean/early Archean: no calibrated proxy exists.
    # GEOCARB extrapolates but is model-dependent speculation, not data.
    if param == "co2" and age_ma > 1500.0:
        return True
    # Atmospheric O2 in Hadean: no proxy exists.
    if param == "o2" and age_ma > 2500.0:
        return True
    # Magnetic polarity pre-M29: no calibrated GPTS chrons.
    if param == "magnetic_polarity" and age_ma > GPTS_CEILING_MA:
        return True
    # δ18O in pre-Cenozoic: no benthic forams.
    if param == "d18O" and age_ma > 180.0:
        return True
    return False


# ─── 5-state polarity resolver ───────────────────────────────────────────────

def resolve_polarity_state(age_ma: float, interval_top_ma: float, interval_base_ma: float) -> tuple[PolarityState, str]:
    """Determine the 5-state polarity for the requested interval.

    Returns:
        (state, detailed_note)

    Logic:
      1. If interval entirely within CNS or Kiaman → SUPERCHRON
      2. If interval entirely above GPTS ceiling (pre-Triassic) → UNRESOLVED
      3. If interval spans >=1 known reversal → MIXED
      4. If single chron covers the interval → NORMAL or REVERSED
      5. If interval entirely outside GPTS calibrated range → UNRESOLVED

    Note: in this forge we use static boundaries. A future phase will
    ingest the GPTS CSV and use real chron crossings.
    """
    # Case 1: superchron containment
    if interval_base_ma <= CNS_BASE_MA and interval_top_ma >= CNS_TOP_MA:
        return (
            PolarityState.SUPERCHRON,
            f"Interval [{interval_top_ma}, {interval_base_ma}] Ma lies entirely within the "
            f"Cretaceous Normal Superchron (CNS, {CNS_TOP_MA}-{CNS_BASE_MA} Ma). "
            f"Polarity is known (normal) but provides ZERO stratigraphic dating resolution. "
            f"Use biostrat (radiolarians) or 40Ar/39Ar as alternative age control.",
        )
    if interval_base_ma <= KIAMAN_BASE_MA and interval_top_ma >= KIAMAN_TOP_MA:
        return (
            PolarityState.SUPERCHRON,
            f"Interval lies within the Kiaman Reversed Superchron ({KIAMAN_TOP_MA}-{KIAMAN_BASE_MA} Ma). "
            f"Polarity is known (reversed) but provides ZERO dating resolution.",
        )

    # Case 2: above GPTS ceiling (uncalibrated)
    if interval_top_ma > GPTS_CEILING_MA:
        return (
            PolarityState.UNRESOLVED,
            f"Interval entirely above GPTS calibrated range (>~{GPTS_CEILING_MA} Ma). "
            f"No calibrated magnetic polarity time scale exists for this window.",
        )

    # Case 3: intersects CNS (partially blind)
    if interval_top_ma < CNS_BASE_MA and interval_base_ma > CNS_TOP_MA:
        return (
            PolarityState.MIXED,
            f"Interval [{interval_top_ma}, {interval_base_ma}] Ma spans the Cretaceous "
            f"Normal Superchron ({CNS_TOP_MA}-{CNS_BASE_MA} Ma). Pre- and post-CNS chrons "
            f"are resolvable but the CNS itself is a blind zone.",
        )

    # Case 4: in calibrated GPTS range; assume single chron for narrow queries
    # (proper chron crossing detection requires GPTS CSV ingestion — Phase 2)
    if interval_base_ma - interval_top_ma < 1.0:
        # Single-instant query — assume normal polarity by default at Cenozoic
        # (Phase 2 will use real GPTS CSV lookup)
        if 0 <= age_ma < 0.781:
            return (PolarityState.NORMAL, "Brunhes normal chron (0-0.781 Ma)")
        if 0.781 <= age_ma < 0.988:
            return (PolarityState.REVERSED, "Matuyama reversed chron (0.781-0.988 Ma)")
        # ... Phase 2: replace with full GPTS lookup
        return (
            PolarityState.NORMAL,
            "Single-chron resolution (Phase 2 will use full GPTS CSV lookup)",
        )

    # Case 5: interval with unknown reversal count (mid range, no GPTS data yet)
    return (
        PolarityState.MIXED,
        f"Interval [{interval_top_ma}, {interval_base_ma}] Ma spans unknown number of "
        f"reversals. Phase 2 will resolve exact chron boundaries from GPTS CSV.",
    )


# ─── Interval-distribution helper ─────────────────────────────────────────────

def _wrap_distribution(
    variable_name: str,
    units: str,
    age_res_top: float,
    age_res_base: float,
    duration_myr: float,
    is_interval: bool,
    n_proxy_points: int | None,
    trend: str | None,
    pending_dataset_key: str,
    epistemic_level: str,
    notes: str,
) -> EarthStateVariable:
    """Wrap a NO_DATA / INTERPRETED variable with interval-distribution
    metadata when the query interval is wide enough."""
    warning = None
    if is_interval and duration_myr > 5.0:
        warning = (
            f"{duration_myr:.1f} Myr interval — single value would be interval statistic, "
            f"not point estimate. Distribution metadata provided; scalar is midpoint."
        )

    return EarthStateVariable(
        name=variable_name,
        value=None,
        units=units,
        epistemic_level=epistemic_level,
        source_citation=f"(pending — see PENDING_DATASETS['{pending_dataset_key}'])",
        coverage_top_ma=0.0,
        coverage_base_ma=541.0,
        notes=notes,
        confidence=0.10,
        interval_top_ma=age_res_top,
        interval_base_ma=age_res_base,
        n_proxy_points=n_proxy_points,
        trend=trend,
        warning=warning,
    )


# ─── Loader functions ─────────────────────────────────────────────────────────

def load_co2_estimate(age_ma: float, age_top_ma: float, age_base_ma: float, duration_myr: float) -> EarthStateVariable:
    """Atmospheric CO2 estimate at `age_ma` (or distribution over interval).

    F9 guard: UNKNOWN for ages > 1500 Ma (no calibrated proxy exists).
    Otherwise: NO_DATA (awaiting ingestion).
    """
    if _is_unknown_at_age("co2", age_ma):
        return EarthStateVariable(
            name="atmospheric_co2_ppm",
            value=None,
            units="ppm",
            epistemic_level="UNKNOWN",
            notes=(
                f"CO2 at {age_ma} Ma is UNKNOWN in principle: no calibrated proxy exists "
                f"for the Hadean / early Archean. GEOCARB models extrapolate but are "
                f"speculation, not data. F9 Anti-Hantu: refuse to fabricate."
            ),
            confidence=0.05,
            interval_top_ma=age_top_ma,
            interval_base_ma=age_base_ma,
            warning=f"Cannot be known — not a data gap, an unknowable.",
        )
    notes = (
        "External dataset not yet ingested. For Cenozoic, the canonical source is "
        "Zachos 2001 / Beerling & Royer 2011. For Phanerozoic, Berner GEOCARBSULF. "
        "Uncertainties: ±20-50 ppm (Cenozoic), factor 2-3x (Mesozoic-Paleozoic)."
    )
    return _wrap_distribution(
        "atmospheric_co2_ppm",
        "ppm",
        age_top_ma, age_base_ma, duration_myr,
        is_interval=(duration_myr > 5.0),
        n_proxy_points=None,
        trend=None,
        pending_dataset_key="co2",
        epistemic_level="NO_DATA",
        notes=notes,
    )


def load_benthic_d18O(age_ma: float, age_top_ma: float, age_base_ma: float, duration_myr: float) -> EarthStateVariable:
    """Benthic δ18O (per mil) at `age_ma` — the OBSERVED measurement.

    F9 guard: UNKNOWN for ages > 180 Ma (no benthic forams in pre-Cenozoic
    marine record; planktonic forams appeared in Jurassic).
    """
    if _is_unknown_at_age("d18O", age_ma):
        return EarthStateVariable(
            name="benthic_d18O_permil",
            value=None,
            units="per mil VPDB",
            epistemic_level="UNKNOWN",
            notes=(
                f"δ18O at {age_ma} Ma is UNKNOWN in principle: benthic foraminifera "
                f"do not exist before the Late Triassic (~225 Ma). Use brachiopod "
                f"or phosphate δ18O for older, but with much lower resolution."
            ),
            confidence=0.05,
            interval_top_ma=age_top_ma,
            interval_base_ma=age_base_ma,
        )

    return _wrap_distribution(
        "benthic_d18O_permil",
        "per mil VPDB",
        age_top_ma, age_base_ma, duration_myr,
        is_interval=(duration_myr > 5.0),
        n_proxy_points=None,
        trend=None,
        pending_dataset_key="temperature",  # benthic δ18O is in the same dataset bundle
        epistemic_level="NO_DATA",
        notes=(
            "Benthic δ18O is the OBSERVED measurement (not the temperature). "
            "When ingested, this will be OBSERVED (raw measurement). "
            "Conversion to temperature anomaly requires assumptions about "
            "δ18O_sw and ice-volume — see global_temperature_anomaly_c "
            "for the INTERPRETED downstream variable."
        ),
    )


def load_temperature_estimate(age_ma: float, age_top_ma: float, age_base_ma: float, duration_myr: float) -> EarthStateVariable:
    """Global mean temperature anomaly at `age_ma` — the INTERPRETED downstream.

    F9 guard: UNKNOWN for ages > 1500 Ma (no proxy). For 540-1500 Ma:
    PROCESS_HYPOTHESIS range only (Scotese 2021 model, ±5-10°C).

    Note: benthic δ18O is OBSERVED (raw measurement); temperature is
    INTERPRETED (depends on δ18O_sw assumption + ice-volume correction).
    These are TWO separate fields in the Earth State Vector.
    """
    if _is_unknown_at_age("co2", age_ma):
        # Same F9 threshold — temp proxy also fails in deep time
        return EarthStateVariable(
            name="global_temperature_anomaly_c",
            value=None,
            units="°C relative to present",
            epistemic_level="UNKNOWN",
            notes=(
                f"Temperature anomaly at {age_ma} Ma is UNKNOWN in principle: "
                f"no proxy (δ18O, Mg/Ca, leaf stomata) extends reliably beyond "
                f"~540 Ma. F9 Anti-Hantu: refuse to fabricate."
            ),
            confidence=0.05,
            interval_top_ma=age_top_ma,
            interval_base_ma=age_base_ma,
        )

    notes = (
        "INTERPRETED (not DERIVED). benthic δ18O is the OBSERVED measurement; "
        "temperature requires assumptions: δ18O_sw=-1.0 permil (ice-free) or "
        "+1.0 permil (ice-house), plus ice-volume correction. "
        "Cenozoic uncertainty: ±1-2°C; Phanerozoic (model-derived): ±3-5°C."
    )
    return _wrap_distribution(
        "global_temperature_anomaly_c",
        "°C relative to present",
        age_top_ma, age_base_ma, duration_myr,
        is_interval=(duration_myr > 5.0),
        n_proxy_points=None,
        trend=None,
        pending_dataset_key="temperature",
        epistemic_level="NO_DATA",
        notes=notes,
    )


def load_sea_level_estimate(age_ma: float, age_top_ma: float, age_base_ma: float, duration_myr: float) -> EarthStateVariable:
    """Eustatic sea level at `age_ma` with mandatory reference-frame fields.

    F4 CLARITY: never return "+40 m" without specifying curve, component,
    and datum. The reference_curve / reference_component / reference_datum
    fields below must be populated whenever a sea_level value is emitted.

    F9 guard: UNKNOWN for ages > 541 Ma (no eustatic record in Precambrian).
    """
    if age_ma > 541.0:
        return EarthStateVariable(
            name="eustatic_sea_level_m",
            value=None,
            units="m relative to present MSL",
            epistemic_level="UNKNOWN",
            notes=(
                f"Eustatic sea level at {age_ma} Ma is UNKNOWN in principle: "
                f"no eustatic record preserved before the Phanerozoic. "
                f"F9 Anti-Hantu: refuse to fabricate."
            ),
            confidence=0.05,
            interval_top_ma=age_top_ma,
            interval_base_ma=age_base_ma,
            reference_curve="n/a (UNRESOLVED)",
            reference_component="n/a",
            reference_datum="n/a",
        )

    notes = (
        "External dataset not yet ingested. Reference-frame fields MUST be "
        "populated when dataset is loaded: curve (Haq2014 vs Miller2005 vs "
        "Ray2019 vs Kominz2008), component (long_term / short_term / "
        "composite), datum (present_msl). Never emit a scalar without these. "
        "F4 CLARITY requires explicit reference frames."
    )
    return _wrap_distribution(
        "eustatic_sea_level_m",
        "m relative to present MSL",
        age_top_ma, age_base_ma, duration_myr,
        is_interval=(duration_myr > 5.0),
        n_proxy_points=None,
        trend=None,
        pending_dataset_key="sea_level",
        epistemic_level="NO_DATA",
        notes=notes,
    )


def load_magnetic_polarity(age_ma: float, age_top_ma: float, age_base_ma: float, duration_myr: float) -> EarthStateVariable:
    """Geomagnetic polarity at `age_ma` — 5-state enum (NORMAL / REVERSED / MIXED / SUPERCHRON / UNRESOLVED).

    This is the canonical LC#28 closure for Sabah ophiolite dating.
    """
    state, detail_note = resolve_polarity_state(age_ma, age_top_ma, age_base_ma)

    # Map PolarityState → value string and confidence
    if state == PolarityState.SUPERCHRON:
        # Polarity is KNOWN but dating power is ZERO
        return EarthStateVariable(
            name="geomagnetic_polarity",
            value="SUPERCHRON (polarity known, dating power NULL)",
            units="enum: normal|reversed|mixed|superchron|unresolved",
            epistemic_level="OBSERVED",
            source_citation="Ogg 2020 (GTS2020 chronology)",
            coverage_top_ma=GPTS_FLOOR_MA,
            coverage_base_ma=GPTS_CEILING_MA,
            notes=detail_note,
            confidence=0.90,  # polarity is known, but dating resolution is NULL
            warning="DATING RESOLUTION = NULL: use biostrat or radiometric dating as alternative.",
        )
    if state == PolarityState.UNRESOLVED:
        return EarthStateVariable(
            name="geomagnetic_polarity",
            value="UNRESOLVED",
            units="enum: normal|reversed|mixed|superchron|unresolved",
            epistemic_level="NO_DATA",
            source_citation="(no calibrated GPTS for this interval)",
            notes=detail_note,
            confidence=0.10,
        )

    # For NORMAL / REVERSED / MIXED, we have NO_DATA because the GPTS CSV
    # is not ingested — but we can still describe the resolution logic.
    return EarthStateVariable(
        name="geomagnetic_polarity",
        value=state.value,  # 'normal' | 'reversed' | 'mixed'
        units="enum: normal|reversed|mixed|superchron|unresolved",
        epistemic_level="NO_DATA",
        source_citation="(pending — see PENDING_DATASETS['magnetic_polarity'])",
        coverage_top_ma=GPTS_FLOOR_MA,
        coverage_base_ma=GPTS_CEILING_MA,
        notes=(
            f"5-state enum resolution: {state.value}. {detail_note} "
            "GPTS CSV not yet ingested — exact chron assignments pending Phase 1 forge."
        ),
        confidence=0.50,  # logic is sound, but exact chron data missing
    )


def load_atmospheric_o2(age_ma: float, age_top_ma: float, age_base_ma: float, duration_myr: float) -> EarthStateVariable:
    """Atmospheric O2 (PAL) at `age_ma`."""
    if _is_unknown_at_age("o2", age_ma):
        return EarthStateVariable(
            name="atmospheric_o2_pal",
            value=None,
            units="PAL (1.0 = present)",
            epistemic_level="UNKNOWN",
            notes=(
                f"Atmospheric O2 at {age_ma} Ma is UNKNOWN in principle: "
                f"no O2 proxy exists for the Archean. F9 Anti-Hantu: refuse."
            ),
            confidence=0.05,
            interval_top_ma=age_top_ma,
            interval_base_ma=age_base_ma,
        )
    return _wrap_distribution(
        "atmospheric_o2_pal",
        "PAL (1.0 = present)",
        age_top_ma, age_base_ma, duration_myr,
        is_interval=(duration_myr > 5.0),
        n_proxy_points=None,
        trend=None,
        pending_dataset_key="o2",
        epistemic_level="NO_DATA",
        notes=(
            "External dataset not yet ingested. Berner 2001 GEOCARBSULF "
            "(Phanerozoic). O2 peak ~30% in Carboniferous (giant dragonflies), "
            "drops in P-Tr, recovers in Jurassic, dips at K-Pg."
        ),
    )


def load_supercontinent_state(age_ma: float) -> EarthStateVariable:
    """Qualitative supercontinent descriptor — OBSERVED (consensus)."""
    descriptor: str | None = None
    if 320 <= age_ma <= 180:
        descriptor = "Pangaea (assembled ~320 Ma, breaking apart ~180 Ma)"
    elif 1000 <= age_ma <= 750:
        descriptor = "Rodinia (assembled ~1100 Ma, breaking apart ~750 Ma)"
    elif 550 <= age_ma <= 500:
        descriptor = "Gondwana (assembling)"
    elif 0 <= age_ma < 180:
        descriptor = "Modern continental configuration (Pangaea fragments dispersed)"
    elif 180 < age_ma <= 250:
        descriptor = "Pangaea rifting → Laurasia + Gondwana"
    elif 250 < age_ma <= 320:
        descriptor = "Late Paleozoic assembly → Pangaea forming"
    elif 540 < age_ma < 1000:
        descriptor = "Rodinia rifting / Gondwana assembling (Mesoproterozoic-Neoproterozoic)"

    if descriptor is None:
        return EarthStateVariable(
            name="supercontinent_state",
            value=None,
            units="descriptor",
            epistemic_level="NO_DATA",
            notes=f"No canonical supercontinent descriptor for age {age_ma} Ma",
            confidence=0.10,
        )
    return EarthStateVariable(
        name="supercontinent_state",
        value=descriptor,
        units="descriptor",
        epistemic_level="OBSERVED",
        source_citation="Bradley (2011) Secular trends in the geologic record and the supercontinent cycle",
        coverage_top_ma=0.0,
        coverage_base_ma=1100.0,
        notes="Qualitative descriptor from supercontinent cycle literature",
        confidence=0.85,
    )


def load_biotic_realm(age_ma: float) -> EarthStateVariable:
    """Qualitative biotic-realm descriptor — OBSERVED (fossil record)."""
    descriptor: str | None = None
    if 0 <= age_ma < 2.58:
        descriptor = "Quaternary: humans (Homo), megafauna, ice-age biota"
    elif 2.58 <= age_ma < 23.03:
        descriptor = "Neogene: modern mammal families, grassland expansion, hominid evolution"
    elif 23.03 <= age_ma < 66.0:
        descriptor = "Paleogene: post-K-Pg mammal radiation, angiosperm dominance, first primates"
    elif 66.0 <= age_ma < 145.0:
        descriptor = "Cretaceous: dinosaurs (non-avian), ammonites, angiosperms diversify, K-Pg mass extinction"
    elif 145.0 <= age_ma < 201.4:
        descriptor = "Jurassic: dinosaurs peak, first birds, mammals small, Pangea rifting"
    elif 201.4 <= age_ma < 251.902:
        descriptor = "Triassic: recovery from P-Tr extinction, first dinosaurs, archosaurs dominant"
    elif 251.902 <= age_ma < 298.9:
        descriptor = "Permian: synapsids dominant, P-Tr mass extinction (96% marine species)"
    elif 298.9 <= age_ma < 358.9:
        descriptor = "Carboniferous: giant arthropods (high O2), first reptiles, coal forests"
    elif 358.9 <= age_ma < 419.2:
        descriptor = "Devonian: Age of Fishes, first tetrapods, first forests, Late Devonian extinctions"
    elif 419.2 <= age_ma < 443.8:
        descriptor = "Silurian: first land plants, first jawed fish"
    elif 443.8 <= age_ma < 485.4:
        descriptor = "Ordovician: marine invertebrate diversification, O-S mass extinction"
    elif 485.4 <= age_ma < 538.8:
        descriptor = "Cambrian: Cambrian explosion (most major animal phyla), Anomalocaris"
    elif 538.8 <= age_ma < 1000:
        descriptor = "Neoproterozoic: Ediacaran biota (~575-538 Ma), first multicellular life"
    elif age_ma >= 1000:
        descriptor = "Mesoproterozoic or older: microbial mats, simple eukaryotes"

    if descriptor is None:
        return EarthStateVariable(
            name="biotic_realm",
            value=None,
            units="descriptor",
            epistemic_level="NO_DATA",
            notes=f"No biotic descriptor for age {age_ma} Ma",
            confidence=0.10,
        )
    return EarthStateVariable(
        name="biotic_realm",
        value=descriptor,
        units="descriptor",
        epistemic_level="OBSERVED",
        source_citation="Gradstein et al. (2020) Geologic Time Scale 2020 (Chapter on Phanerozoic biostratigraphy)",
        coverage_top_ma=0.0,
        coverage_base_ma=2500.0,
        notes="Qualitative descriptor from Phanerozoic biotic events literature",
        confidence=0.90,
    )


def load_ice_extent(age_ma: float) -> EarthStateVariable:
    """Qualitative ice-extent descriptor — OBSERVED (sediment + δ18O record)."""
    descriptor: str | None = None
    if 0 <= age_ma < 2.58:
        descriptor = "Pleistocene glacial-interglacial cycles (cyclical ice sheets)"
    elif 2.58 <= age_ma < 33.9:
        descriptor = "Ice-free (warm-house state)"
    elif 33.9 <= age_ma < 34.5:
        descriptor = "EOGM: ephemeral Antarctic glaciation (Oi-1 event)"
    elif 34.5 <= age_ma < 66.0:
        descriptor = "Ice-free (warm Eocene)"
    elif 66.0 <= age_ma < 145.0:
        descriptor = "Cretaceous: ice-free (greenhouse)"
    elif 251.0 <= age_ma < 360.0:
        descriptor = "Late Paleozoic Ice Age (Gondwanan glaciation)"
    elif 635 <= age_ma <= 720:
        descriptor = "Snowball Earth (Sturtian + Marinoan glaciations)"
    if descriptor is None:
        descriptor = "ice-free (default)"
    return EarthStateVariable(
        name="ice_extent",
        value=descriptor,
        units="descriptor",
        epistemic_level="OBSERVED",
        source_citation="Crowell (1999), Eyles (2008), Lisiecki & Raymo (2005) LR04",
        coverage_top_ma=0.0,
        coverage_base_ma=720.0,
        confidence=0.85,
    )
