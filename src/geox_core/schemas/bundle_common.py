"""
bundle_common.py — capability-bundle output contract vocabulary (DRAFT_CANDIDATE).

FIVE ORTHOGONAL dimensions (Arif reconciliation directive — no conflation):
  1. epistemic_class        — WHAT KIND of knowledge (mission RULE-04)
  2. lifecycle_state        — WHERE in the processing pipeline (live GEOX lifecycle)
  3. explanation_class      — WHAT KIND of explanation (claim_kernel/v1, LIVE)
  4. authority_ceiling      — CONSTANT: QUALIFIED_CANDIDATE (GEOX never exceeds)
  5. constitutional_verdict — null unless arifOS issues one (owner: arifOS)

NOT a registry. Import only from the three bundle schemas:
  restoration_bundle / strat_mesh_ref / charge_result.

Reconciliation vs the live/legacy vocabularies:
  see reconciliation_vocabulary_0.1.0-draft.yaml (same directory).

Status: DRAFT_CANDIDATE — not frozen. Pending human acceptance of
  exact version, field semantics, and vocabulary mapping.
"""

from __future__ import annotations

from typing import Literal

# (1) epistemic class — mission RULE-04 (what kind of knowledge)
EpistemicClass = Literal["OBSERVED", "COMPUTED", "INTERPRETED_LOCAL", "HYPOTHESIS"]

# (2) lifecycle state — pure pipeline stage (verdict states moved to dimension 5)
LifecycleState = Literal["NO_VALID_EVIDENCE", "INGESTED", "QC_VERIFIED", "INTERPRETED", "DERIVED_CANDIDATE"]

# (3) explanation class — claim_kernel/v1 (LIVE, active consumer claim_explanation_guard.py)
ExplanationClass = Literal["MEASURED", "MECHANISM", "PATTERN", "NARRATIVE", "UNCLASSIFIED"]

# (4) authority ceiling — GEOX never exceeds QUALIFIED_CANDIDATE.
AUTHORITY_CEILING: str = "QUALIFIED_CANDIDATE"

# (5) constitutional verdict — owner arifOS ONLY. GEOX never sets it.
ConstitutionalVerdict = Literal["SEALED", "SABAR", "VOID", "HOLD"]

# Forbidden epistemic states (RULE-04).
# NOTE: "FACT" collides with live claims.py truth_class="FACT" — see reconciliation artifact.
FORBIDDEN_EPISTEMIC: frozenset[str] = frozenset({"CERTAIN", "PROVEN", "FINAL", "FACT"})

# Explanation classes that are action-eligible (claim_kernel/v1). NARRATIVE and
# UNCLASSIFIED may be published but cannot be approved/sealed.
ACTION_ELIGIBLE_EXPLANATION: frozenset[str] = frozenset({"MEASURED", "MECHANISM", "PATTERN"})
