from geox_core.schemas.velocity_mapping import VelocityFailureMode, VelocityQCGate, VelocityRenderPayload, VelocityStructuralClaim
from geox_core.schemas.velocity_policy import VelocityACRiskPolicy


class VelocityStructuralEngine:
    """
    Evaluates a Velocity Model against the GEOX Constitutional QC Gates and Failure Modes.
    Computes Anomalous Contrast (AC) Risk using a configurable policy.
    """

    def __init__(self, policy: VelocityACRiskPolicy | None = None):
        self.policy = policy or VelocityACRiskPolicy()

    def evaluate_velocity_cube(
        self,
        cube_id: str,
        source_model_version: str,
        cleared_gates: list[VelocityQCGate],
        identified_failures: list[VelocityFailureMode],
        evidence_for: str,
        evidence_against: str,
        uncertainty_band: str = "P10-P90 Not Calculated",
        proxy_id: str | None = None,
        lineage: list[dict] | None = None,
        evidence_handles: list[str] | None = None,
    ) -> VelocityRenderPayload:
        """
        Runs the doctrine logic. Calculate AC Risk.
        Returns the RenderPayload compliant with Binary Transport Doctrine.
        """

        # 1. Determine failed and missing gates
        all_gates = set(VelocityQCGate)
        cleared_set = set(cleared_gates)
        failed_gates = list(all_gates - cleared_set)

        # 2. Compute AC Risk
        ac_risk = self.policy.base_irreducible_risk

        for gate in failed_gates:
            ac_risk += self.policy.qc_penalty_map.get(gate, 0.0)

        for failure in identified_failures:
            ac_risk += self.policy.failure_mode_penalty_map.get(failure, 0.0)

        # Cap AC Risk at 1.0
        ac_risk = min(1.0, ac_risk)

        # 3. Determine if structural proxy is valid (Threshold from policy)
        is_valid = ac_risk < self.policy.max_acceptable_ac_risk

        # 4. Construct Claim Grammar
        missing_tests = [gate.value for gate in failed_gates]

        claim = VelocityStructuralClaim(
            proxy_id=proxy_id or f"proxy_{cube_id}",
            cube_id=cube_id,
            source_model_version=source_model_version,
            epistemic_rung="EARTHMODEL",
            lineage=lineage or [],
            evidence_handles=evidence_handles or [],
            cleared_qc_gates=cleared_gates,
            failed_qc_gates=failed_gates,
            identified_failure_modes=identified_failures,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            missing_tests=missing_tests,
            uncertainty_band=uncertainty_band,
            ac_risk=round(ac_risk, 3),
            is_structural_proxy_valid=is_valid,
        )

        # 5. Construct Binary Transport Envelope
        manifest_uri = f"geox://render/cubes/{cube_id}/manifest"

        payload = VelocityRenderPayload(renderable=True, cube_manifest_uri=manifest_uri, claim=claim)

        return payload
