"""
Bias Detector — Cognitive Bias Heuristics for ToAC
DITEMPA BUKAN DIBERI

Automatically detects B_cog modifiers based on session telemetry,
interpretation diversity, timeline pressure, and pattern repetition.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter

logger = logging.getLogger("geox.core.bias_detector")


class BiasDetector:
    """
    Heuristic engine to detect cognitive bias exposure (B_cog).
    Prevents manual gaming of bias scenarios.
    """

    # Canonical B_cog values from TOAC_AC_RISK_SPEC
    SCENARIOS = {
        "physics_validated": 0.20,
        "multi_interpreter": 0.28,
        "ai_with_physics": 0.30,
        "unaided_expert": 0.35,
        "ai_vision_only": 0.42,
        "executive_pressure": 0.55,
        "single_model_collapse": 0.65,
        "confirmation_bias": 0.50,
        "authority_bias": 0.48,
        "anchoring_bias": 0.45,
        "pressure_collapse_conflation": 0.70,
    }

    @classmethod
    def detect(
        cls,
        claimed_scenario: str,
        session_history: List[Dict[str, Any]],
        hypotheses_count: int = 1,
        deadline: Optional[datetime] = None,
        complexity_score: float = 0.5,
        initial_estimate: Optional[float] = None,
        final_estimate: Optional[float] = None,
        external_sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Detect the actual bias scenario and return the corrected B_cog.
        """
        detected_scenario = claimed_scenario
        modifiers = []

        # 1. Detect Missing Physics (Anti-Gaming)
        if claimed_scenario == "physics_validated":
            physics_verified = any(
                "verify" in str(event.get("tool_class", "")) or
                "physics_verify" in str(event.get("tool", ""))
                for event in session_history
            )
            if not physics_verified:
                detected_scenario = "unaided_expert"
                modifiers.append("MISSING_PHYSICS_VERIFICATION")
                logger.warning("Bias Override: Claimed physics_validated but no verify tool found in history.")

        # 2. Detect Model Collapse (F7 Humility)
        if hypotheses_count <= 1 and complexity_score > 0.6:
            detected_scenario = "single_model_collapse"
            modifiers.append("MODEL_COLLAPSE_DETECTED")

        # 3. Detect Executive Pressure (Timeline)
        if deadline:
            time_left = deadline - datetime.now()
            if time_left < timedelta(hours=2) and complexity_score > 0.4:
                detected_scenario = "executive_pressure"
                modifiers.append("TIMELINE_PRESSURE_DETECTED")

        # 4. Detect Confirmation Bias
        # If >70% of session events use the same tool/interpretation path
        tool_classes = [str(event.get("tool_class", "unknown")) for event in session_history if event]
        if tool_classes:
            most_common_ratio = Counter(tool_classes).most_common(1)[0][1] / len(tool_classes)
            if most_common_ratio > 0.7 and len(set(tool_classes)) <= 2:
                detected_scenario = "confirmation_bias"
                modifiers.append("CONFIRMATION_BIAS_DETECTED")

        # 5. Detect Authority Bias
        # If all sources are the same provider or <2 distinct sources
        sources = external_sources or []
        distinct_sources = len(set(sources))
        if distinct_sources == 1 and len(sources) >= 3:
            detected_scenario = "authority_bias"
            modifiers.append("AUTHORITY_BIAS_DETECTED")
        elif distinct_sources == 0 and len(session_history) > 5:
            detected_scenario = "authority_bias"
            modifiers.append("NO_EXTERNAL_SOURCES")

        # 6. Detect Anchoring Bias
        # If final estimate is within 5% of initial estimate despite new evidence
        if initial_estimate is not None and final_estimate is not None:
            if abs(initial_estimate) > 1e-9:
                deviation = abs(final_estimate - initial_estimate) / abs(initial_estimate)
                evidence_events = len([e for e in session_history if "load" in str(e.get("action", "")) or "ingest" in str(e.get("action", ""))])
                if deviation < 0.05 and evidence_events >= 2:
                    detected_scenario = "anchoring_bias"
                    modifiers.append("ANCHORING_BIAS_DETECTED")

        # 7. Final B_cog Determination
        actual_b_cog = cls.SCENARIOS.get(detected_scenario, cls.SCENARIOS["ai_vision_only"])

        # Ceiling: if both collapse and pressure, floor is 0.70
        if "MODEL_COLLAPSE_DETECTED" in modifiers and "TIMELINE_PRESSURE_DETECTED" in modifiers:
            actual_b_cog = 0.70
            detected_scenario = "pressure_collapse_conflation"

        # Secondary ceiling: confirmation + authority conflation
        if "CONFIRMATION_BIAS_DETECTED" in modifiers and "AUTHORITY_BIAS_DETECTED" in modifiers:
            actual_b_cog = max(actual_b_cog, 0.60)
            detected_scenario = "confirmation_authority_conflation"

        return {
            "detected_scenario": detected_scenario,
            "b_cog": actual_b_cog,
            "modifiers": modifiers,
            "audit": {
                "claimed": claimed_scenario,
                "hypotheses": hypotheses_count,
                "timestamp": datetime.now().isoformat(),
                "session_event_count": len(session_history),
                "distinct_sources": len(set(external_sources or [])),
            }
        }
