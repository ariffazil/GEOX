"""deep_time/age_resolver.py — Fuzzy query → canonical [start_Ma, end_Ma].

F2 TRUTH: All resolutions are derived from the embedded ICS Chart v2024/12.
No external API calls in the resolution path; deterministic and offline-safe.

Resolution priority:
  1. Explicit numeric (age_ma or age_top_ma/age_bot_ma)
  2. Named period/epoch/era (case-insensitive, fuzzy match)
  3. Fuzzy phrase (e.g. "age of dinosaurs", "K-Pg boundary")
  4. Free-text query (substring match against fuzzy_phrases)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .ics_chart import ChronostratUnit, ICSChart, ics_chart_v2024_12


@dataclass(frozen=True)
class AgeResolution:
    """Result of resolving a user age query.

    Attributes:
        top_ma:        younger boundary of resolved interval (closer to 0)
        base_ma:       older boundary of resolved interval
        named_unit:    canonical name of matched unit (if any)
        named_rank:    'period' | 'epoch' | 'era' | 'event' | 'point'
        matched_input: the input string that was resolved
        resolution_method: how the resolution was achieved
        ics_chart_version: which ICS chart was used
        confidence:    confidence in the resolution (0.0-1.0)
        midpoint_ma:   midpoint of the resolved interval
        duration_myr:  duration of the resolved interval
    """

    top_ma: float
    base_ma: float
    named_unit: str
    named_rank: str
    matched_input: str
    resolution_method: str
    ics_chart_version: str
    confidence: float
    midpoint_ma: float
    duration_myr: float


# ─── Helper: build AgeResolution from a ChronostratUnit ──────────────────────


def _from_unit(
    unit: ChronostratUnit,
    matched_input: str,
    method: str,
    chart_version: str,
    confidence: float = 0.95,
) -> AgeResolution:
    return AgeResolution(
        top_ma=unit.top_ma,
        base_ma=unit.base_ma,
        named_unit=unit.name,
        named_rank=unit.rank,
        matched_input=matched_input,
        resolution_method=method,
        ics_chart_version=chart_version,
        confidence=confidence,
        midpoint_ma=unit.midpoint_ma,
        duration_myr=unit.duration_myr,
    )


def _from_point(
    age_ma: float,
    matched_input: str,
    method: str,
    chart: ICSChart,
    window_myr: float = 1.0,
    confidence: float = 0.90,
) -> AgeResolution:
    """Resolve a single age (in Ma) to a small symmetric window.

    Returns a ±window_myr/2 interval around the queried point. Also annotates
    which named chronostratigraphic units the point falls inside.
    """
    half_window = window_myr / 2.0
    top_ma = max(0.0, age_ma - half_window)
    base_ma = age_ma + half_window
    epoch, period, era = chart.unit_containing(age_ma)
    named = epoch.name if epoch else (period.name if period else (era.name if era else "unresolved"))
    rank = epoch.rank if epoch else (period.rank if period else (era.rank if era else "point"))
    return AgeResolution(
        top_ma=top_ma,
        base_ma=base_ma,
        named_unit=named,
        named_rank=rank,
        matched_input=matched_input,
        resolution_method=method,
        ics_chart_version=chart.version,
        confidence=confidence,
        midpoint_ma=age_ma,
        duration_myr=window_myr,
    )


# ─── Main resolver ────────────────────────────────────────────────────────────


def resolve_age_query(
    age_ma: float | None = None,
    age_top_ma: float | None = None,
    age_bot_ma: float | None = None,
    period: str | None = None,
    query: str | None = None,
    chart: ICSChart | None = None,
) -> AgeResolution:
    """Resolve a user age query to a canonical [start_Ma, end_Ma] interval.

    Resolution priority:
      1. Explicit numeric (age_ma or age_top_ma + age_bot_ma)
      2. Named period/epoch/era via `period` arg or `query` arg
      3. Fuzzy phrase (e.g. "age of dinosaurs", "K-Pg boundary")
      4. Free-text substring match against fuzzy_phrases

    The returned AgeResolution always carries the matched interval bounds
    and provenance (chart version, resolution method, confidence).
    """
    chart = chart or ics_chart_v2024_12

    # Priority 1: explicit numeric
    if age_top_ma is not None and age_bot_ma is not None:
        top, base = sorted((float(age_top_ma), float(age_bot_ma)))
        epoch, period_unit, era = chart.unit_containing((top + base) / 2.0)
        named = epoch.name if epoch else (period_unit.name if period_unit else (era.name if era else "explicit range"))
        rank = epoch.rank if epoch else (period_unit.rank if period_unit else (era.rank if era else "range"))
        return AgeResolution(
            top_ma=top,
            base_ma=base,
            named_unit=named,
            named_rank=rank,
            matched_input=f"age_top_ma={top}, age_bot_ma={base}",
            resolution_method="explicit_numeric_range",
            ics_chart_version=chart.version,
            confidence=0.95,
            midpoint_ma=(top + base) / 2.0,
            duration_myr=base - top,
        )

    if age_ma is not None:
        return _from_point(
            age_ma=float(age_ma),
            matched_input=f"age_ma={age_ma}",
            method="explicit_numeric_point",
            chart=chart,
            window_myr=2.0,  # ±1 Myr around the point
            confidence=0.90,
        )

    # Combine period + query for fuzzy matching
    search_text = (period or "") + " " + (query or "")
    search_text = search_text.strip()
    if not search_text:
        # Default: present day
        return _from_point(
            age_ma=0.0,
            matched_input="(default: present)",
            method="default_present",
            chart=chart,
            window_myr=0.1,
            confidence=0.50,
        )

    norm = search_text.lower().strip()

    # Priority 2: direct match against fuzzy_phrases
    if norm in chart.fuzzy_phrases:
        age_mid, label = chart.fuzzy_phrases[norm]
        # Look up the canonical unit by name
        unit = _lookup_unit_by_name(label, chart)
        if unit is not None:
            return _from_unit(
                unit=unit,
                matched_input=norm,
                method="fuzzy_phrase_exact",
                chart_version=chart.version,
                confidence=0.90,
            )
        # Fallback: treat as point query
        return _from_point(
            age_ma=age_mid,
            matched_input=norm,
            method="fuzzy_phrase_point",
            chart=chart,
            window_myr=5.0,
            confidence=0.85,
        )

    # Priority 3: match against named periods / epochs / eras
    unit = _lookup_unit_by_name(norm, chart)
    if unit is not None:
        return _from_unit(
            unit=unit,
            matched_input=norm,
            method="named_unit_direct",
            chart_version=chart.version,
            confidence=0.95,
        )

    # Priority 4: substring match against fuzzy_phrases
    for phrase, (_age_mid, label) in chart.fuzzy_phrases.items():
        if phrase in norm or norm in phrase:
            unit = _lookup_unit_by_name(label, chart)
            if unit is not None:
                return _from_unit(
                    unit=unit,
                    matched_input=f"{norm} (via substring '{phrase}')",
                    method="fuzzy_phrase_substring",
                    chart_version=chart.version,
                    confidence=0.80,
                )

    # Priority 5: numeric extraction from query (e.g. "85 Ma", "Late Cretaceous 85")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ma|mya|m\.y\.)?", norm)
    if m:
        extracted = float(m.group(1))
        return _from_point(
            age_ma=extracted,
            matched_input=f"{norm} (extracted numeric)",
            method="regex_numeric_extraction",
            chart=chart,
            window_myr=2.0,
            confidence=0.75,
        )

    # Unresolvable
    return AgeResolution(
        top_ma=0.0,
        base_ma=0.0,
        named_unit="UNRESOLVED",
        named_rank="unresolved",
        matched_input=norm,
        resolution_method="unresolved",
        ics_chart_version=chart.version,
        confidence=0.0,
        midpoint_ma=0.0,
        duration_myr=0.0,
    )


def _lookup_unit_by_name(name: str, chart: ICSChart) -> ChronostratUnit | None:
    """Find a chronostratigraphic unit by (case-insensitive) name."""
    norm = name.lower().strip()
    for unit in chart.periods:
        if unit.name.lower() == norm:
            return unit
    for unit in chart.epochs:
        if unit.name.lower() == norm:
            return unit
    for unit in chart.eras:
        if unit.name.lower() == norm:
            return unit
    return None
