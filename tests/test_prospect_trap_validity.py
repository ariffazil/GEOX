import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Prospect Trap Validity Challenge (Synthetic)
# ═══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger("geox.prospect_trap")

class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    metadata: Dict[str, Any]
    provenance: str

class Hypothesis(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    is_primary: bool = False
    evidence_for: List[str] = []
    evidence_against: List[str] = []

class Uncertainty(BaseModel):
    uncertainty_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    impact: str
    missing_evidence: List[str] = []
    recommended_verification: List[str] = []

class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    evidence_attached: List[Evidence] = []
    hypotheses: List[Hypothesis] = []
    uncertainties: List[Uncertainty] = []
    confidence: float = 0.0
    status: str = "DRAFT"
    decision_impact: str = ""

# Tool State Mock
_STORE: Dict[str, Claim] = {}

def geox_claim_create(title: str, description: str) -> str:
    """Creates a new geological claim workflow."""
    claim = Claim(title=title, description=description)
    _STORE[claim.claim_id] = claim
    return claim.claim_id

def geox_evidence_attach(claim_id: str, evidence_type: str, metadata: Dict[str, Any], provenance: str) -> str:
    """Attaches piece of geological evidence to a claim."""
    if claim_id not in _STORE:
        raise ValueError(f"Claim {claim_id} not found.")
    claim = _STORE[claim_id]
    ev = Evidence(type=evidence_type, metadata=metadata, provenance=provenance)
    claim.evidence_attached.append(ev)
    return ev.evidence_id

def geox_claim_challenge(claim_id: str, hypothesis_description: str, evidence_for: List[str], evidence_against: List[str]) -> str:
    """Registers the primary hypothesis for the challenge."""
    if claim_id not in _STORE:
        raise ValueError(f"Claim {claim_id} not found.")
    claim = _STORE[claim_id]
    hyp = Hypothesis(
        description=hypothesis_description, 
        is_primary=True,
        evidence_for=evidence_for,
        evidence_against=evidence_against
    )
    claim.hypotheses.append(hyp)
    return hyp.hypothesis_id

def geox_alternative_model_register(claim_id: str, alternative_description: str, evidence_for: List[str], evidence_against: List[str]) -> str:
    """Registers a competing geological hypothesis."""
    if claim_id not in _STORE:
        raise ValueError(f"Claim {claim_id} not found.")
    claim = _STORE[claim_id]
    hyp = Hypothesis(
        description=alternative_description, 
        is_primary=False, 
        evidence_for=evidence_for, 
        evidence_against=evidence_against
    )
    claim.hypotheses.append(hyp)
    return hyp.hypothesis_id

def geox_uncertainty_register(claim_id: str, description: str, impact: str, missing_evidence: List[str], recommended_verification: List[str]) -> str:
    """Registers uncertainties and missing critical evidence."""
    if claim_id not in _STORE:
        raise ValueError(f"Claim {claim_id} not found.")
    claim = _STORE[claim_id]
    unc = Uncertainty(
        description=description, 
        impact=impact, 
        missing_evidence=missing_evidence, 
        recommended_verification=recommended_verification
    )
    claim.uncertainties.append(unc)
    return unc.uncertainty_id

def geox_claim_seal(claim_id: str, confidence: float, decision_impact: str) -> Dict[str, Any]:
    """Seals the claim with a confidence score and generates the Vault payload."""
    if claim_id not in _STORE:
        raise ValueError(f"Claim {claim_id} not found.")
    claim = _STORE[claim_id]
    claim.confidence = confidence
    claim.decision_impact = decision_impact
    claim.status = "SEALED"
    
    primary_hyp = next((h for h in claim.hypotheses if h.is_primary), None)
    
    seal_payload = {
        "claim_id": claim.claim_id,
        "title": claim.title,
        "primary_geological_hypothesis": primary_hyp.description if primary_hyp else None,
        "alternative_hypotheses": [h.description for h in claim.hypotheses if not h.is_primary],
        "evidence_for": [e for h in claim.hypotheses for e in h.evidence_for],
        "evidence_against": [e for h in claim.hypotheses for e in h.evidence_against],
        "uncertainty": [u.description for u in claim.uncertainties],
        "missing_evidence": [m for u in claim.uncertainties for m in u.missing_evidence],
        "confidence": claim.confidence,
        "recommended_verification": [v for u in claim.uncertainties for v in u.recommended_verification],
        "decision_impact": claim.decision_impact,
        "Vault_seal_payload": {
            "epoch": datetime.now(timezone.utc).isoformat(),
            "seal_hash": f"SEAL-{claim.claim_id[:8]}",
            "verdict": "SEALED | VALID" if claim.confidence > 0.7 else "SEALED | HOLD",
            "ds": 1.2
        }
    }
    return seal_payload

# ═══════════════════════════════════════════════════════════════════════════════
# Pytest Test Case
# ═══════════════════════════════════════════════════════════════════════════════

def test_prospect_trap_validity_synthetic():
    # 1. Initialize Challenge
    claim_id = geox_claim_create(
        title="SYN-01 Alpha Prospect Trap Validity",
        description="Abductive reasoning challenge for synthetic 3-way dip closure"
    )

    # 2. Attach Evidence
    ev_crs = geox_evidence_attach(
        claim_id,
        "crs_metadata",
        {"epsg": 32631, "datum": "WGS84", "depth_unit": "meters"},
        "synthetic_project_db"
    )
    ev_seis = geox_evidence_attach(
        claim_id,
        "seismic_volume",
        {"type": "psdm", "vintage": "2024", "polarity": "SEG normal"},
        "synthetic_seismic_server"
    )
    ev_horz = geox_evidence_attach(
        claim_id,
        "horizon_object",
        {"name": "Top_Sand_A", "interpreter": "bot_01", "amplitude_extraction": "RMS high"},
        "synthetic_interpretation_db"
    )
    ev_fault = geox_evidence_attach(
        claim_id,
        "fault_object",
        {"name": "F1_Main_Bounding", "throw_m": 120, "dip_deg": 60},
        "synthetic_interpretation_db"
    )
    ev_well = geox_evidence_attach(
        claim_id,
        "well_tie",
        {"well": "SYN-1", "cc": 0.85, "synthetic_to_seismic_shift_ms": -4},
        "synthetic_well_db"
    )

    # 3. Create Primary Hypothesis
    hyp_primary = geox_claim_challenge(
        claim_id,
        hypothesis_description="Valid 3-way dip closure bounded by F1 sealing fault, sand A present.",
        evidence_for=[ev_horz, ev_fault, ev_well],
        evidence_against=[]
    )

    # 4. Register Alternative Models
    hyp_alt1 = geox_alternative_model_register(
        claim_id,
        alternative_description="Fault F1 is leaking due to sand-on-sand juxtaposition across the fault plane.",
        evidence_for=[],
        evidence_against=[ev_fault]
    )

    hyp_alt2 = geox_alternative_model_register(
        claim_id,
        alternative_description="Amplitude anomaly on horizon A is a tuning artifact, not related to fluid.",
        evidence_for=[],
        evidence_against=[ev_horz]
    )

    # 5. Register Uncertainties
    unc_1 = geox_uncertainty_register(
        claim_id,
        description="Fault seal capacity is poorly constrained; unknown shale gouge ratio (SGR).",
        impact="High risk of trap failure (leakage).",
        missing_evidence=["SGR calculation along F1", "Pressure data across fault"],
        recommended_verification=["Conduct fault seal analysis on F1", "Extract fault throw profile"]
    )
    
    unc_2 = geox_uncertainty_register(
        claim_id,
        description="Depth conversion velocity model uncertainty.",
        impact="Spill point depth may shift up to 15m, affecting volume.",
        missing_evidence=["Velocity checkshot at SYN-2 location"],
        recommended_verification=["Update velocity model with VSP data"]
    )

    # 6. Seal Claim
    seal_payload = geox_claim_seal(
        claim_id,
        confidence=0.65,
        decision_impact="HOLD drill decision until fault seal analysis is completed."
    )

    # Assertions
    assert seal_payload["claim_id"] == claim_id
    assert seal_payload["primary_geological_hypothesis"] == "Valid 3-way dip closure bounded by F1 sealing fault, sand A present."
    assert len(seal_payload["alternative_hypotheses"]) == 2
    assert "Fault F1 is leaking due to sand-on-sand juxtaposition across the fault plane." in seal_payload["alternative_hypotheses"]
    assert len(seal_payload["missing_evidence"]) == 3
    assert seal_payload["confidence"] == 0.65
    assert seal_payload["decision_impact"] == "HOLD drill decision until fault seal analysis is completed."
    assert "Vault_seal_payload" in seal_payload
    assert seal_payload["Vault_seal_payload"]["verdict"] == "SEALED | HOLD"

    # Optional: Print payload for visibility when run directly or with -s
    print(json.dumps(seal_payload, indent=2))

if __name__ == "__main__":
    test_prospect_trap_validity_synthetic()
