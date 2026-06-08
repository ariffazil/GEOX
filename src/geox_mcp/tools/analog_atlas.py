"""
GEOX Analog Atlas — ToAC-Integrated Global Analog Search
══════════════════════════════════════════════════════════
Eureka: the analog that kills you is the one that looks 90% similar but
has a fundamentally different charge history or seal mechanism. So this
tool returns BOTH (a) similarity scoring AND (b) dangerous-similarity
flagging via the Theory of Anomalous Contrast (ToAC).

Architecture:
  INPUT: prospect/feature description (structured + free-text)
  EMBEDDING: per-dimension categorical + numeric similarity (no LLM)
  CONSTITUTIONAL WRAPPER:
    F2 TRUTH    — every analog carries epistemic_rung + confidence_band
    F7 HUMILITY — similarity is a HINT, not a SEAL; output is HYPOTHESIS
    F9 ANTIHANTU — no "this is an analog" — only "this MAY share features"
    F1 AMANAH  — read-only advisory; never authorizes a drill decision
    Doctrine 8  — primary hypothesis + alternatives + missing evidence
  OUTPUT: ranked analogs with similarity, CONTRAST signals, and
          dangerous_similarity_flag (the audit-driven eureka)

MVP scope (2026-06-08): 5 Malaysian basins, 2 seed analogs. Extensible.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from geox_core.enums.statuses import (
    ArtifactStatus,
    ExecutionStatus,
    GovernanceStatus,
    get_standard_envelope,
)

logger = logging.getLogger("geox.canonical.analog_atlas")

# Repo-root resolution. Default = path-relative; override via GEOX_RESOURCES_DIR.
# Fix: prior hardcode `/root/geox/...` broke CI (runner uses /home/runner/work/...).
import os as _os

_REPO_ROOT = Path(__file__).resolve().parents[3]
ANALOGS_DIR = Path(_os.environ.get("GEOX_RESOURCES_DIR", str(_REPO_ROOT / "resources" / "analogs")))

# ═══════════════════════════════════════════════════════════════════════════════
# Scoring dimensions (7 axes for similarity + contrast)
# ═══════════════════════════════════════════════════════════════════════════════
# Each dimension contributes to BOTH similarity (1 - distance) and contrast
# (the distance itself). The dangerous-similarity flag fires when similarity
# is high (>= 0.7) but contrast_diversity (count of dimensions with delta>0.5)
# is also >= 2.

DIMENSION_WEIGHTS: dict[str, float] = {
    "tectonic_setting": 0.20,  # structural heritage is hard to overcome
    "basin_age": 0.10,  # less critical — many plays span ages
    "lithology_primary": 0.15,  # reservoir rock matters
    "depth_range_m": 0.15,  # burial → porosity + phase
    "trap_style": 0.20,  # critical for seal integrity
    "source_rock": 0.10,  # charge matters but not deal-breaker
    "reservoir_rock": 0.10,  # closely correlated with lithology_primary
}

DANGEROUS_SIMILARITY_THRESHOLD = 0.70  # similarity score above this
DANGEROUS_CONTRAST_THRESHOLD = 0.5  # per-dimension contrast above this
DANGEROUS_CONTRAST_COUNT_MIN = 2  # at least N dimensions with high contrast

# Confidence band width depends on analog data quality
QUALITY_BAND_WIDTH: dict[str, float] = {
    "HIGH": 0.08,
    "MEDIUM": 0.15,
    "LOW": 0.25,
    "VERY_LOW": 0.40,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Per-dimension similarity computation
# ═══════════════════════════════════════════════════════════════════════════════


def _norm(s: Any) -> str:
    """Normalize a categorical value for comparison."""
    if s is None:
        return ""
    return str(s).strip().lower().replace(" ", "_").replace("-", "_")


def _categorical_similarity(a: Any, b: Any) -> float:
    """Categorical similarity: 1.0 if exact match (normalized), 0.0 otherwise.

    Could be enhanced with semantic embedding — for MVP, exact match suffices.
    The audit (2026-06-08) flagged that naive string matching on geological
    categories is dangerous; hence the dangerous_similarity flag downstream
    compensates by surfacing *any* dimension where exact match fails.
    """
    a_n = _norm(a)
    b_n = _norm(b)
    if not a_n or not b_n:
        return 0.5  # neutral on missing
    return 1.0 if a_n == b_n else 0.0


def _numeric_range_overlap(a_range: list[float] | None, b_range: list[float] | None) -> float:
    """Numeric range overlap as 0.0-1.0. Returns 1.0 if both fully overlap,
    0.0 if disjoint, partial otherwise.

    a_range, b_range: [min, max]. None values return 0.5 (neutral).
    """
    if a_range is None or b_range is None:
        return 0.5
    try:
        a_min, a_max = float(a_range[0]), float(a_range[1])
        b_min, b_max = float(b_range[0]), float(b_range[1])
    except (TypeError, IndexError, ValueError):
        return 0.5
    # Compute overlap / union (Jaccard)
    if a_max < a_min or b_max < b_min:
        return 0.0
    inter_lo = max(a_min, b_min)
    inter_hi = min(a_max, b_max)
    if inter_hi < inter_lo:
        return 0.0
    inter = inter_hi - inter_lo
    union = max(a_max, b_max) - min(a_min, b_min)
    if union <= 0:
        return 1.0 if inter > 0 else 0.5
    return float(inter / union)


# ═══════════════════════════════════════════════════════════════════════════════
# Analog loading (corpus)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class AnalogFactsheet:
    """In-memory representation of one analog."""

    analog_id: str
    basin_id: str
    play_name: str
    play_type: str
    tectonic_setting: str
    basin_age: str
    lithology_primary: str
    depth_range_m: list[float] | None
    trap_style: str
    source_rock: str
    reservoir_rock: str
    epistemic_rung: str
    data_quality: str
    evidence_refs: list[str]
    contrast_dimensions: list[dict[str, Any]]
    notes: list[str]

    @property
    def depth_range(self) -> list[float] | None:
        return self.depth_range_m


def _load_analog(path: Path) -> AnalogFactsheet:
    """Load one analog from YAML. Fail-loud: returns a partial factsheet
    with errors noted (the loader never crashes the tool)."""
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return AnalogFactsheet(
        analog_id=data.get("analog_id", path.stem),
        basin_id=data.get("basin_id", "UNKNOWN"),
        play_name=data.get("play_name", "unnamed play"),
        play_type=data.get("play_type", "unknown"),
        tectonic_setting=data.get("tectonic_setting", ""),
        basin_age=data.get("basin_age", ""),
        lithology_primary=data.get("lithology_primary", ""),
        depth_range_m=data.get("depth_range_m"),
        trap_style=data.get("trap_style", ""),
        source_rock=data.get("source_rock", ""),
        reservoir_rock=data.get("reservoir_rock", ""),
        epistemic_rung=data.get("epistemic_rung", "INTERPRETATION"),
        data_quality=data.get("data_quality", "MEDIUM"),
        evidence_refs=data.get("evidence_refs", []),
        contrast_dimensions=data.get("contrast_dimensions", []),
        notes=data.get("notes", []),
    )


def _load_corpus(filter_basin_ids: list[str] | None = None) -> list[AnalogFactsheet]:
    """Load all analogs from the corpus, optionally filtered by basin."""
    if not ANALOGS_DIR.exists():
        return []
    corpus: list[AnalogFactsheet] = []
    for p in sorted(ANALOGS_DIR.glob("*.yaml")):
        try:
            analog = _load_analog(p)
        except Exception as exc:
            logger.warning(f"Failed to load analog {p}: {exc}")
            continue
        if filter_basin_ids and analog.basin_id not in filter_basin_ids:
            continue
        corpus.append(analog)
    return corpus


# ═══════════════════════════════════════════════════════════════════════════════
# Similarity + contrast scoring
# ═══════════════════════════════════════════════════════════════════════════════


def _score_analog(query: dict[str, Any], analog: AnalogFactsheet) -> dict[str, Any]:
    """Score one analog against the query. Returns per-dimension similarity
    and per-dimension contrast (delta). The dangerous-similarity flag is
    derived from these."""
    per_dim_sim: dict[str, float] = {}
    per_dim_contrast: dict[str, float] = {}
    contrast_signals: list[dict[str, Any]] = []

    # Per-dimension similarity + contrast
    sim_axes = [
        ("tectonic_setting", _categorical_similarity(query.get("tectonic_setting"), analog.tectonic_setting)),
        ("basin_age", _categorical_similarity(query.get("basin_age"), analog.basin_age)),
        ("lithology_primary", _categorical_similarity(query.get("lithology_primary"), analog.lithology_primary)),
        ("depth_range_m", _numeric_range_overlap(query.get("depth_range_m"), analog.depth_range_m)),
        ("trap_style", _categorical_similarity(query.get("trap_style"), analog.trap_style)),
        ("source_rock", _categorical_similarity(query.get("source_rock"), analog.source_rock)),
        ("reservoir_rock", _categorical_similarity(query.get("reservoir_rock"), analog.reservoir_rock)),
    ]
    for dim, sim in sim_axes:
        per_dim_sim[dim] = round(sim, 4)
        # Contrast = distance from perfect match (1.0 - sim)
        contrast = round(1.0 - sim, 4)
        per_dim_contrast[dim] = contrast
        # Surface high-contrast dimensions as a ToAC signal
        if contrast >= DANGEROUS_CONTRAST_THRESHOLD and query.get(_axis_key(dim)) is not None:
            # Find the analog's contrast_dimensions entry for richer context
            for cd in analog.contrast_dimensions:
                if _norm(cd.get("dimension")) == dim:
                    contrast_signals.append(
                        {
                            "dimension": dim,
                            "observation_in_analog": cd.get("observation", ""),
                            "implication": cd.get("implication", ""),
                            "delta": contrast,
                        }
                    )
                    break
            else:
                contrast_signals.append(
                    {
                        "dimension": dim,
                        "observation_in_analog": getattr(analog, _axis_key(dim), ""),
                        "implication": "This dimension does not match your query — verify with primary data before substituting analog.",
                        "delta": contrast,
                    }
                )

    # Weighted similarity score
    score = sum(per_dim_sim[d] * DIMENSION_WEIGHTS.get(d, 0.0) for d in per_dim_sim)
    score = round(score, 4)

    # Confidence band
    band_w = QUALITY_BAND_WIDTH.get(analog.data_quality, 0.20)
    confidence_band = [
        round(max(0.0, score - band_w), 4),
        round(min(1.0, score + band_w), 4),
    ]

    # Dangerous similarity: high score AND multiple high-contrast dimensions
    high_contrast_count = sum(
        1 for d, c in per_dim_contrast.items() if c >= DANGEROUS_CONTRAST_THRESHOLD and query.get(_axis_key(d)) is not None
    )
    dangerous = score >= DANGEROUS_SIMILARITY_THRESHOLD and high_contrast_count >= DANGEROUS_CONTRAST_COUNT_MIN

    return {
        "analog_id": analog.analog_id,
        "basin_id": analog.basin_id,
        "play_name": analog.play_name,
        "play_type": analog.play_type,
        "similarity_score": score,
        "similarity_confidence_band": confidence_band,
        "data_quality": analog.data_quality,
        "epistemic_rung": analog.epistemic_rung,
        "evidence_refs": list(analog.evidence_refs),
        "per_dimension_similarity": per_dim_sim,
        "per_dimension_contrast": per_dim_contrast,
        "high_contrast_dimensions_count": high_contrast_count,
        "contrast_signals": contrast_signals,
        "dangerous_similarity_flag": dangerous,
        "warning": (
            "HIGH similarity but multiple high-contrast dimensions. "
            "Verify charge history, seal integrity, and structural style "
            "with PRIMARY DATA before substituting this analog for your prospect."
        )
        if dangerous
        else None,
    }


def _axis_key(dim: str) -> str:
    """Map dimension name to the query key used to look it up."""
    return dim  # identical in this implementation


# ═══════════════════════════════════════════════════════════════════════════════
# Main tool
# ═══════════════════════════════════════════════════════════════════════════════


async def geox_analog_atlas(
    query: dict[str, Any],
    corpus_filter: dict[str, Any] | None = None,
    contrast_mode: Literal["similarity_only", "contrast_only", "full"] = "full",
    top_k: int = 5,
    min_similarity: float = 0.0,
) -> dict:
    """Find analog prospects/plays, with explicit dangerous-similarity flagging.

    Use this tool to:
      1. Find global or basin-specific analogs for a prospect description
      2. Quantify the CONTRAST between your prospect and each candidate analog
      3. Receive an explicit warning when an analog looks similar on aggregate
         but has fundamentally different structural / charge / seal features

    Parameters
    ----------
    query : dict
        Prospect/feature description. Recognized fields (all optional, but
        the more you supply the better the score):
          - basin_id, play_type, tectonic_setting, basin_age
          - lithology_primary, lithology_secondary
          - depth_range_m: [min, max] in meters
          - trap_style, source_rock, reservoir_rock, seal
          - geological_narrative: free-text description (currently unused
            in scoring; reserved for future embedding)
    corpus_filter : dict, optional
        Restrict the corpus. Recognized fields:
          - basin_ids: list of basin_id strings (e.g. ["MALAY_BASIN"])
          - tectonic_settings: list of allowed tectonic settings
          - min_data_quality: "LOW" | "MEDIUM" | "HIGH"
    contrast_mode : str
        "similarity_only" — return only similarity scores
        "contrast_only"  — return only contrast signals
        "full"           — return both (default; recommended)
    top_k : int
        Maximum analogs to return (1-20, default 5).
    min_similarity : float
        Drop analogs below this similarity threshold (0.0-1.0, default 0.0).

    Returns
    -------
    dict
        Standard GEOX envelope with:
          - result.results: ranked list of analog matches
          - result.summary: aggregate counts, verdict, caveats
          - result.dangerous_count: how many analogs hit the dangerous flag
          - epistemic_tag: PLAUSIBLE (analog match is a hint, not a SEAL)
    """
    # ── Input validation ─────────────────────────────────────────────────────
    if not isinstance(query, dict) or not query:
        return get_standard_envelope(
            {
                "tool": "geox_analog_atlas",
                "error_code": "EMPTY_QUERY",
                "message": "query must be a non-empty dict. Supply at least one of: "
                "basin_id, play_type, tectonic_setting, basin_age, "
                "lithology_primary, depth_range_m, trap_style, source_rock, "
                "reservoir_rock.",
                "downgrade_available": False,
            },
            tool_class="reason",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )
    if not (1 <= int(top_k) <= 20):
        return get_standard_envelope(
            {
                "tool": "geox_analog_atlas",
                "error_code": "INVALID_TOP_K",
                "message": f"top_k must be in [1, 20]; got {top_k}",
            },
            tool_class="reason",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )
    if contrast_mode not in ("similarity_only", "contrast_only", "full"):
        return get_standard_envelope(
            {
                "tool": "geox_analog_atlas",
                "error_code": "INVALID_CONTRAST_MODE",
                "message": f"contrast_mode must be similarity_only|contrast_only|full; got {contrast_mode}",
            },
            tool_class="reason",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )

    # ── Load corpus ─────────────────────────────────────────────────────────
    cf = corpus_filter or {}
    corpus = _load_corpus(filter_basin_ids=cf.get("basin_ids"))
    if not corpus:
        return get_standard_envelope(
            {
                "tool": "geox_analog_atlas",
                "error_code": "EMPTY_CORPUS",
                "message": "Analog corpus is empty. Add YAML factsheets under /root/geox/resources/analogs/ to seed the corpus.",
                "corpus_filter_applied": cf,
                "downgrade_available": False,
            },
            tool_class="reason",
            execution_status=ExecutionStatus.ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )

    # ── Optional: filter by data quality ───────────────────────────────────
    min_q = cf.get("min_data_quality", "LOW")
    quality_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "VERY_LOW": -1}
    min_q_rank = quality_order.get(str(min_q).upper(), 0)
    corpus = [a for a in corpus if quality_order.get(a.data_quality, 0) >= min_q_rank]
    if not corpus:
        return get_standard_envelope(
            {
                "tool": "geox_analog_atlas",
                "error_code": "NO_CORPUS_MATCH_QUALITY",
                "message": f"No analogs meet min_data_quality={min_q}",
                "downgrade_available": True,
                "downgrade_param": "min_data_quality=LOW",
            },
            tool_class="reason",
            execution_status=ExecutionStatus.RECOVERABLE_ERROR,
            governance_status=GovernanceStatus.HOLD,
            claim_state="NO_VALID_EVIDENCE",
        )

    # ── Optional: filter by tectonic setting ───────────────────────────────
    if cf.get("tectonic_settings"):
        allowed = {_norm(t) for t in cf["tectonic_settings"]}
        corpus = [a for a in corpus if _norm(a.tectonic_setting) in allowed]
        if not corpus:
            return get_standard_envelope(
                {
                    "tool": "geox_analog_atlas",
                    "error_code": "NO_CORPUS_MATCH_TECTONIC",
                    "message": "No analogs in specified tectonic settings",
                    "tectonic_settings": cf.get("tectonic_settings"),
                },
                tool_class="reason",
                execution_status=ExecutionStatus.RECOVERABLE_ERROR,
                governance_status=GovernanceStatus.HOLD,
                claim_state="NO_VALID_EVIDENCE",
            )

    # ── Score all analogs ──────────────────────────────────────────────────
    scored = [_score_analog(query, a) for a in corpus]
    scored = [s for s in scored if s["similarity_score"] >= float(min_similarity)]
    # Rank: highest similarity first; ties broken by dangerous_similarity_flag
    # descending (so the most-contrasting high-similarity analogs surface)
    scored.sort(
        key=lambda s: (s["similarity_score"], s["dangerous_similarity_flag"]),
        reverse=True,
    )
    scored = scored[: int(top_k)]

    # ── Apply contrast_mode filter ─────────────────────────────────────────
    if contrast_mode == "similarity_only":
        for s in scored:
            s.pop("per_dimension_contrast", None)
            s.pop("contrast_signals", None)
            s.pop("high_contrast_dimensions_count", None)
            s.pop("warning", None)
    elif contrast_mode == "contrast_only":
        # Keep only the contrast-bearing fields
        for s in scored:
            for k in [
                "similarity_score",
                "similarity_confidence_band",
                "per_dimension_similarity",
                "data_quality",
                "epistemic_rung",
                "evidence_refs",
            ]:
                s.pop(k, None)

    # ── Aggregate summary + verdict ────────────────────────────────────────
    dangerous_count = sum(1 for s in scored if s["dangerous_similarity_flag"])
    best = scored[0] if scored else None
    if not scored:
        verdict = "HOLD"
        verdict_reason = "No analogs met min_similarity threshold"
        claim_state = "NO_VALID_EVIDENCE"
    elif dangerous_count > 0:
        # Dangerous similarity: HOLD the verdict. The audit was correct —
        # this is the case where the AI should NOT give a SEAL even if the
        # top score is high. Geologist must verify charge/seal with primary data.
        verdict = "HOLD"
        verdict_reason = (
            f"{dangerous_count}/{len(scored)} analog(s) hit dangerous-similarity flag. "
            "Score is high but multiple high-contrast dimensions exist. "
            "Verify with PRIMARY DATA (well logs, seismic, PVT) before using."
        )
        claim_state = "HYPOTHESIS"
    else:
        verdict = "QUALIFY"
        verdict_reason = "Top analogs have high similarity without dangerous-similarity flags."
        claim_state = "PLAUSIBLE"

    # ── Doctrine 8: primary hypothesis + alternatives + missing evidence ───
    missing_evidence: list[str] = []
    if not query.get("geological_narrative"):
        missing_evidence.append("geological_narrative: free-text context would improve score confidence")
    if not query.get("depth_range_m"):
        missing_evidence.append("depth_range_m: depth context discriminates analog suitability")
    if not query.get("tectonic_setting"):
        missing_evidence.append("tectonic_setting: most weight-bearing dimension; supplying it surfaces the right analogs")

    primary_hypothesis = (
        (
            f"Top analog: {best['analog_id']} (score={best['similarity_score']}) in {best['basin_id']} "
            f"may share structural / charge / reservoir features with the query."
        )
        if best
        else "No analogs scored above threshold."
    )

    alternative_explanations: list[str] = [
        f"Other {len(scored) - 1} analogs available with lower similarity but possibly different contrast profile.",
        "Score is computed from categorical and numeric overlap only; it does not capture spatial, temporal, or facies variability within a play.",
    ]
    if dangerous_count > 0:
        alternative_explanations.append(
            f"{dangerous_count} analog(s) flagged dangerous: similar at aggregate level but "
            "with multiple high-contrast dimensions. These are the highest-risk "
            "false-positive analogs in the corpus. Treat with extra skepticism."
        )

    result = {
        "tool": "geox_analog_atlas",
        "atlas_version": "v2026.06.08",
        "atlas_doctrine": "ToAC-integrated analog search (F2 + F7 + F9 + GEOX Doctrine 8)",
        "query_summary": {k: v for k, v in query.items() if k != "geological_narrative"},
        "corpus_filter_applied": cf,
        "n_corpus_evaluated": len(corpus),
        "results": scored,
        "summary": {
            "n_results_returned": len(scored),
            "n_dangerous_similarities": dangerous_count,
            "best_score": best["similarity_score"] if best else None,
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "primary_hypothesis": primary_hypothesis,
            "alternative_explanations": alternative_explanations,
            "missing_evidence": missing_evidence,
            "caveat": (
                "This is a HYPOTHESIS-grade tool. Analog match does not authorize "
                "any drill or commercial decision. The dangerous_similarity_flag is "
                "an explicit warning that aggregate similarity can mask dimensional "
                "divergence. Always verify with primary subsurface data (wells, "
                "seismic, PVT) before committing capital. arifOS judges; GEOX advises."
            ),
        },
    }

    return get_standard_envelope(
        result,
        tool_class="reason",
        execution_status=ExecutionStatus.SUCCESS,
        governance_status=GovernanceStatus[verdict]
        if verdict in ("HOLD", "QUALIFY", "VOID", "APPROVED", "SEAL")
        else GovernanceStatus.QUALIFY,
        claim_tag=("HYPOTHESIS" if verdict == "HOLD" else "PLAUSIBLE"),
        claim_state=claim_state,
        evidence_refs=[],
    )
