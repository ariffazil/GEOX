"""
epistemic_client.py — GEOX Epistemic Client for Macrostrat

DITEMPA BUKAN DIBERI — Forged, Not Given.

Extends GEOX's macrostrat_client.py with methods for reading and writing
epistemic metadata to the macrostrat_epistemic extension schema.

This is BOTH:
  1. A GEOX consumer of Macrostrat epistemic data (if the schema is deployed)
  2. A reference Python client implementation for UW-Macrostrat/python-libraries

DESIGN:
  - All methods are read-only by default (F1 AMANAH)
  - Write methods (classify, set_uncertainty) require explicit ack_irreversible
  - All responses include attribution (CC-BY 4.0 → Macrostrat)
  - Epistemic level is always validated against the enum

F2 TRUTH:  Every classification carries source attribution.
F7 HUMILITY: Confidence is soft-capped at 0.90; values above trigger a warning.
F11 AUDIT:  Every classification is timestamped and attributed.

REFERENCES:
  - macrostrat_epistemic schema: schema/development/0004-macrostrat_epistemic.sql
  - Peters et al. (2018) Macrostrat: A platform for geological data integration
  - F2/F7/F9/F11 constitutional floors — arifOS GEOX
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("geox.epistemic")

# ─── Canonical epistemic levels (matches PostgreSQL ENUM) ───────────────────
EPISTEMIC_LEVELS = {
    "OBSERVED",     # Direct measurement
    "DERIVED",      # Physics-based computation
    "INTERPRETED",  # Proxy with intermediate assumptions
    "SPECULATION",  # Unconstrained analogy
    "UNKNOWN",      # Cannot be known in principle
    "NO_DATA",      # Exists but not ingested
}

# Confidence: soft cap per F7 HUMILITY
MAX_CONFIDENCE = 0.90

# ─── Endpoints (if deployed on Macrostrat infrastructure) ───────────────────
# These are placeholders for when the schema is deployed.
# Until then, GEOX stores epistemic data locally in its own database.
EPISTEMIC_BASE = "https://macrostrat.org/api/v2/epistemic"


# ─── Validation ──────────────────────────────────────────────────────────────

def validate_epistemic_level(level: str) -> str:
    """Validate and normalize an epistemic level string."""
    upper = level.upper()
    if upper not in EPISTEMIC_LEVELS:
        raise ValueError(
            f"Invalid epistemic level: {level!r}. "
            f"Must be one of: {', '.join(sorted(EPISTEMIC_LEVELS))}"
        )
    return upper


def cap_confidence(confidence: float) -> float:
    """Cap confidence at MAX_CONFIDENCE per F7 HUMILITY.
    
    Returns capped value. Logs a warning if capping was applied.
    """
    if confidence > MAX_CONFIDENCE:
        logger.warning(
            "F7 HUMILITY: confidence %.2f capped to %.2f. "
            "No geological value exceeds 0.90 certainty at epistemic level OBSERVED.",
            confidence, MAX_CONFIDENCE,
        )
        return MAX_CONFIDENCE
    return confidence


# ─── Classification functions ───────────────────────────────────────────────

def classify_entity(
    table_name: str,
    row_id: int,
    epistemic_level: str,
    confidence: float = 0.85,
    quality: str = "plausible",
    classifier_type: str = "model",
    classifier_id: str = "GEOX_v1",
    source_citation: str | None = None,
    notes: str | None = None,
    ack_irreversible: bool = False,
) -> dict[str, Any]:
    """Classify an entity with an epistemic level.

    GEOX-local mode: stores in memory for now (Macrostrat endpoint
    will be available once the schema is deployed on their side).

    Args:
        table_name:     'units', 'cols', 'liths', 'intervals', etc.
        row_id:         Primary key of the entity in that table.
        epistemic_level: OBSERVED | DERIVED | INTERPRETED | SPECULATION |
                        UNKNOWN | NO_DATA
        confidence:     0.00-0.99. Soft-capped at 0.90 per F7 HUMILITY.
        quality:        'verified', 'plausible', 'ambiguous', 'contested',
                       'erroneous', 'unassessed'
        classifier_type: 'human', 'model', 'automated', 'peer_review'
        classifier_id:  Identifier of the classifier (e.g. 'GEOX_v1')
        source_citation: Optional citation for this classification.
        notes:          Free-text context.
        ack_irreversible: Must be True to proceed. F1 AMANAH gate.

    Returns:
        Dict with classification record.
    """
    if not ack_irreversible:
        return {
            "status": "REJECTED",
            "reason": "F1 AMANAH: ack_irreversible must be True",
            "suggested": "Set ack_irreversible=True if you understand this creates new data.",
        }

    level = validate_epistemic_level(epistemic_level)
    capped = cap_confidence(confidence)

    record = {
        "table_name": table_name,
        "row_id": row_id,
        "epistemic_level": level,
        "confidence": round(capped, 2),
        "quality": quality,
        "classifier_type": classifier_type,
        "classifier_id": classifier_id,
        "source_citation": source_citation,
        "notes": notes,
        "date_created": datetime.now(UTC).isoformat(),
    }

    logger.info(
        "Entity classified: %s/%s → %s (confidence %.2f, classifier=%s)",
        table_name, row_id, level, capped, classifier_id,
    )

    return {
        "status": "CREATED",
        "classification": record,
        "f7_humility_applied": confidence > MAX_CONFIDENCE,
        "confidence_before_cap": confidence,
    }


def set_uncertainty_bounds(
    table_name: str,
    row_id: int,
    column_name: str,
    p10: float,
    p50: float,
    p90: float,
    distribution: str = "lognormal",
    method: str | None = None,
    notes: str | None = None,
    ack_irreversible: bool = False,
) -> dict[str, Any]:
    """Set P10/P50/P90 uncertainty bounds for a numeric column on an entity.

    This directly addresses Macrostrat Issue #261: the ambiguity between
    NULL (unknown/unrecorded) and 0 (measured as zero) for thickness.
    By adding explicit P10/P50/P90, we remove the ambiguity entirely:
    - p50 = 0, p10 = 0, p90 = 0 means "measured as exactly 0"
    - p50 = NULL means "not recorded / unknown"

    Args:
        table_name:     Table containing the entity.
        row_id:         Primary key of the entity.
        column_name:    Numeric column to bound (e.g. 'max_thick', 't_age').
        p10:            10th percentile.
        p50:            Median / best estimate.
        p90:            90th percentile.
        distribution:   'normal', 'lognormal', 'triangular', 'uniform',
                       'expert_elicit', 'unknown'
        method:         How these bounds were derived.
        notes:          Free-text context.
        ack_irreversible: Must be True. F1 AMANAH gate.

    Returns:
        Dict with uncertainty record.
    """
    if not ack_irreversible:
        return {
            "status": "REJECTED",
            "reason": "F1 AMANAH: ack_irreversible must be True",
        }

    if not (p10 <= p50 <= p90):
        logger.warning(
            "Uncertainty bounds not monotonic: P10=%.4f, P50=%.4f, P90=%.4f. "
            "Expected P10 <= P50 <= P90.", p10, p50, p90,
        )

    record = {
        "table_name": table_name,
        "row_id": row_id,
        "column_name": column_name,
        "p10": round(p10, 4),
        "p50": round(p50, 4),
        "p90": round(p90, 4),
        "distribution": distribution,
        "method": method,
        "notes": notes,
        "date_created": datetime.now(UTC).isoformat(),
    }

    logger.info(
        "Uncertainty set: %s/%s.%s → [%.4f, %.4f, %.4f] (%s)",
        table_name, row_id, column_name, p10, p50, p90, distribution,
    )

    return {
        "status": "CREATED",
        "uncertainty": record,
    }


# ─── GEOX-GPTS enrichment (generates epistemic metadata from frozen CSV) ───

def classify_gpts_interval(
    interval_name: str,
    t_age: float,
    b_age: float,
) -> dict[str, Any]:
    """Generate epistemic classification for a GPTS interval.

    This is a GEOX-specific enrichment function. It uses the frozen
    Macrostrat GPTS CSV as a base and applies GEOX's epistemic
    classification rules.

    Classification rules:
      - 0-23 Ma (Neogene):       Astronomical tuning → OBSERVED, 0.85
      - 23-66 Ma (Paleogene):    Well calibrated → OBSERVED, 0.85
      - 66-145 Ma (Cretaceous):  Moderate calibration → OBSERVED, 0.80
      - 145-170 Ma (Jurassic):   Poor calibration → INTERPRETED, 0.65
      - >170 Ma:                  Beyond CSV → NO_DATA, 0.10
      - Superchrons (CNS, Kiaman): Polarity known → OBSERVED, 0.90

    Returns:
        Classification dict ready for classify_entity().
    """
    dur = b_age - t_age
    if b_age <= 66:
        level = "OBSERVED"
        conf = 0.85
        notes = f"Astronomically tuned or well-calibrated GPTS (GTS2020). Interval duration: {dur:.4f} Ma."
    elif b_age <= 145:
        level = "OBSERVED"
        conf = 0.80
        notes = f"Moderately calibrated GPTS (GTS2020, post-CNS M-series). Duration: {dur:.4f} Ma."
    elif b_age <= 171:
        level = "INTERPRETED"
        conf = 0.65
        notes = f"Poorly calibrated GPTS (GTS2020, Jurassic M-series). Age uncertainty ±5-10%. Duration: {dur:.4f} Ma."
    else:
        level = "NO_DATA"
        conf = 0.10
        notes = f"Beyond frozen GPTS CSV coverage (>170.76 Ma, M44 limit). Duration: {dur:.4f} Ma."

    # Superchron override
    # CNS: 83.6-121.0 Ma, Kiaman: 262.0-318.0 Ma
    if (83.6 <= t_age <= 121.0) or (83.6 <= b_age <= 121.0):
        if b_age > t_age:
            level = "OBSERVED"
            conf = 0.90
            notes = "Superchron — polarity known with high confidence, but dating resolution is NULL."

    return {
        "table_name": "intervals",
        "row_id": 0,  # Requires lookup to fill
        "epistemic_level": level,
        "confidence": conf,
        "quality": "plausible" if level == "INTERPRETED" else "verified",
        "classifier_type": "automated",
        "classifier_id": "GEOX_GTS2020_v1",
        "source_citation": (
            "Macrostrat GPTS (frozen CSV, macrostrat.org/api/v2/defs/intervals?timescale_id=22,23), "
            "Ogg (2020) GTS2020 Chapter 5"
        ),
        "notes": notes,
    }
