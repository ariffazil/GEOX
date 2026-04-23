"""
GEOX Canonical Substrate Ontology v2.1
Shared SES Evidence Envelope Factory
"""
import uuid
import hashlib
from datetime import datetime

class SESEvidenceObject:
    def __init__(self, tool_name, parent_ids=None):
        self.evidence_id = str(uuid.uuid4())
        self.tool = tool_name
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.parent_ids = parent_ids or []
        self.physics_hash = self._generate_physics_hash()

    def _generate_physics_hash(self):
        # Hash of the fundamental Physics9 substrate constants
        return hashlib.sha256(b"mass_phi_sw_time_u_v_T_P_k_v1").hexdigest()

    def wrap(self, substrate_data, claim_tag="ESTIMATE", uncertainty=None):
        return {
            "evidence_id": self.evidence_id,
            "tool": self.tool,
            "timestamp": self.timestamp,
            "parent_ids": self.parent_ids,
            "physics_hash": self.physics_hash,
            "claim_tag": claim_tag,
            "uncertainty": uncertainty or {"method": "unspecified", "sigma": 0.0},
            "data": substrate_data,
            "eligible_for_verdict": self.tool in ["geox_kinetic_tool", "geox_stress_tool", "geox_flow_tool"]
        }
