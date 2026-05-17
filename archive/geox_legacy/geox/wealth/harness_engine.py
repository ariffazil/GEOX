"""
GEOX Harness Engine: 9-Harness Constraint Architecture
Ported from arifOS WEALTH v2.0
DITEMPA BUKAN DIBERI
"""
import os
import hashlib
import inspect
from typing import Any, Dict, List, Optional

class HarnessEngine:
    """9-Harness Constraint Architecture for GEOX Decision Kernel."""

    _LINEAGE_HASH = None
    _DOCTRINE_HASH = None

    @classmethod
    def get_doctrine_hash(cls) -> str:
        """Compute hash of the local GEOX WEALTH_HARNESS.md file."""
        if cls._DOCTRINE_HASH is None:
            try:
                base_dir = os.path.dirname(__file__)
                path = os.path.join(base_dir, "canon", "WEALTH_HARNESS.md")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        cls._DOCTRINE_HASH = hashlib.sha256(f.read().encode()).hexdigest()
                else:
                    cls._DOCTRINE_HASH = "MISSING_DOCTRINE_FILE"
            except Exception:
                cls._DOCTRINE_HASH = "UNKNOWN_DOCTRINE"
        return cls._DOCTRINE_HASH

    @classmethod
    def get_lineage_hash(cls) -> str:
        """Compute the lineage hash of the HarnessEngine source code."""
        if cls._LINEAGE_HASH is None:
            try:
                source = inspect.getsource(cls)
                cls._LINEAGE_HASH = hashlib.sha256(source.encode()).hexdigest()
            except Exception:
                cls._LINEAGE_HASH = "UNKNOWN_LINEAGE"
        return cls._LINEAGE_HASH

    HARNESS_NAMES = [
        "Identity", "Reality", "Epistemic", "Entropy", "Survival",
        "Constitutional", "Efficiency", "Coordination", "Civilization"
    ]

    def audit(self, tool_name: str, primary: Dict[str, Any], flags: List[str], parent_hash: str = "") -> Dict[str, Any]:
        """Audit geoscientific evidence against the 9-harness constraints."""
        harness_status = {name: {"stress": 0.0, "status": "SECURE"} for name in self.HARNESS_NAMES}
        violations = []
        
        # 1. Identity Check (Parent chaining)
        if parent_hash and len(parent_hash) != 64:
            harness_status["Identity"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("IDENTITY_CHAIN_VIOLATION")

        # 2. Reality Check (Data Integrity)
        if any(f in flags for f in ["INVALID_DATA_SOURCE", "STALE_DATA", "PHYSICS_INVARIANT_VIOLATION"]):
            harness_status["Reality"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("REALITY_HARNESS_FAILURE")

        # 3. Epistemic Check (Ambiguity)
        if "LOW_INTEGRITY" in flags or "AC_RISK_VOID" in flags:
            harness_status["Epistemic"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("EPISTEMIC_HARNESS_FAILURE")

        # 4. Entropy Check (Thermodynamics)
        if "HIGH_ENTROPY_SIGNAL" in flags:
            harness_status["Entropy"].update({"stress": 0.8, "status": "STRESSED"})

        # 6. Constitutional Check (Floors)
        if any(f.startswith("FLOOR_") for f in flags):
            harness_status["Constitutional"].update({"stress": 1.0, "status": "SNAPPED"})
            violations.append("CONSTITUTIONAL_HARNESS_FAILURE")

        # 9. Civilization Check (Quantified Triggers)
        # Dynamic EROEI derivation: Volume / (Stress/Flow Penalty)
        hcpv = primary.get("hcpv", 1.0)
        stress_resistance = primary.get("stress_resistance", 0.5)
        flow_mobility = primary.get("flow_mobility", 0.5)
        
        # Energy In = Stress Resistance / Flow Mobility
        energy_invested = (stress_resistance / max(0.01, flow_mobility)) * 1000
        eroei = hcpv / max(1.0, energy_invested)
        
        carbon = primary.get("carbon_intensity", 0.0)
        collapse = primary.get("collapse_risk", 0.0)
        
        if carbon > 0.04 or collapse > 0.3 or eroei < 3.0:
            harness_status["Civilization"].update({
                "stress": 1.0, 
                "status": "SNAPPED",
                "detail": f"C:{carbon:.3f} | R:{collapse:.3f} | EROEI:{eroei:.2f}"
            })
            violations.append("CIVILIZATION_HARNESS_FAILURE")
            if eroei < 3.0:
                violations.append("ENERGY_OVERSHOOT_FAILURE")

        # Systemic Accumulator Rule (Cumulative Stress)
        systemic_stress = sum(h["stress"] for h in harness_status.values())
        if systemic_stress > 2.0:
            violations.append("SYSTEMIC_INSTABILITY_FAILURE")

        overall_verdict = "PASS"
        if any(h["status"] == "SNAPPED" for h in harness_status.values()) or systemic_stress > 2.0:
            overall_verdict = "FAIL"

        return {
            "verdict": overall_verdict,
            "harness_status": harness_status,
            "violations": violations,
            "systemic_stress": round(systemic_stress, 4),
            "harness_lineage_hash": self.get_lineage_hash(),
            "doctrine_hash": self.get_doctrine_hash(),
        }
