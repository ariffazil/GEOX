"""
Bias Detector — Cognitive Bias Heuristics for ToAC
DITEMPA BUKAN DIBERI

Automatically detects B_cog modifiers based on session telemetry,
interpretation diversity, and timeline pressure.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

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
    }

    @classmethod
    def detect(
        cls,
        claimed_scenario: str,
        session_history: List[Dict[str, Any]],
        hypotheses_count: int = 1,
        deadline: Optional[datetime] = None,
        complexity_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Detect the actual bias scenario and return the corrected B_cog.
        """
        detected_scenario = claimed_scenario
        modifiers = []

        # 1. Detect Missing Physics (Anti-Gaming)
        # If they claim physics_validated, check if a verify tool was actually run
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
        # High complexity with only 1 hypothesis triggers collapse
        if hypotheses_count <= 1 and complexity_score > 0.6:
            detected_scenario = "single_model_collapse"
            modifiers.append("MODEL_COLLAPSE_DETECTED")

        # 3. Detect Executive Pressure (Timeline)
        if deadline:
            time_left = deadline - datetime.now()
            # If less than 2 hours left for a complex task, trigger pressure
            if time_left < timedelta(hours=2) and complexity_score > 0.4:
                detected_scenario = "executive_pressure"
                modifiers.append("TIMELINE_PRESSURE_DETECTED")

        # 4. Final B_cog Determination
        actual_b_cog = cls.SCENARIOS.get(detected_scenario, cls.SCENARIOS["ai_vision_only"])
        
        # Ceiling: if both collapse and pressure, floor is 0.70
        if "MODEL_COLLAPSE_DETECTED" in modifiers and "TIMELINE_PRESSURE_DETECTED" in modifiers:
            actual_b_cog = 0.70
            detected_scenario = "pressure_collapse_conflation"

        return {
            "detected_scenario": detected_scenario,
            "b_cog": actual_b_cog,
            "modifiers": modifiers,
            "audit": {
                "claimed": claimed_scenario,
                "hypotheses": hypotheses_count,
                "timestamp": datetime.now().isoformat()
            }
        }
