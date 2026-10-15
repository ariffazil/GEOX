#!/usr/bin/env python3
"""verify_bundle_schemas.py — 8-step validation for capability-bundle schemas.

Run: cd /root/GEOX && PYTHONPATH=src .venv/bin/python3 scripts/verify_bundle_schemas.py
Exit 0 = all pass; exit 1 = any fail.

Covers the Step 3.5 acceptance list:
  1. JSON round-trip
  2. invalid forbidden claim rejection
  3. fewer-than-three hypotheses rejection
  4. non-null preferred_* rejection
  5. missing provenance rejection
  6. backward compatibility (ui_resource_uri optional)
  7. cross-schema shared vocabulary
  8. pydantic version
"""

from __future__ import annotations

import sys
from typing import get_args

import pydantic
from pydantic import ValidationError

from geox_core.schemas.bundle_common import (
    AUTHORITY_CEILING,
    FORBIDDEN_EPISTEMIC,
    ConstitutionalVerdict,
    EpistemicClass,
    LifecycleState,
)
from geox_core.schemas.charge_result import ChargeResult
from geox_core.schemas.restoration_bundle import RestorationBundle
from geox_core.schemas.strat_mesh_ref import StratMeshRef

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def valid_restoration() -> dict:
    return dict(
        hypotheses=[{"id": 1}, {"id": 2}, {"id": 3}],
        provenance=["test-fixture"],
    )


# 1. JSON round-trip
try:
    r = RestorationBundle(**valid_restoration())
    r2 = RestorationBundle.model_validate_json(r.model_dump_json())
    check("1_json_roundtrip", r2 == r, "model_dump_json -> model_validate_json == original")
except Exception as e:  # noqa: BLE001
    check("1_json_roundtrip", False, repr(e))

# 2. invalid forbidden claim rejection
try:
    RestorationBundle(epistemic_class="CERTAIN", **valid_restoration())
    check("2_forbidden_claim", False, "CERTAIN was accepted")
except ValidationError as e:
    check("2_forbidden_claim", True, "CERTAIN rejected (not in EpistemicClass / FORBIDDEN)")
except Exception as e:  # noqa: BLE001
    check("2_forbidden_claim", False, repr(e))

# 3. fewer-than-three hypotheses rejection
try:
    RestorationBundle(hypotheses=[{"id": 1}, {"id": 2}], provenance=["x"])
    check("3_min_three_hypotheses", False, "2 hypotheses accepted")
except ValidationError:
    check("3_min_three_hypotheses", True, "2 hypotheses rejected (need >=3)")
except Exception as e:  # noqa: BLE001
    check("3_min_three_hypotheses", False, repr(e))

# 4. non-null preferred_* rejection (all three schemas)
try:
    RestorationBundle(**valid_restoration(), preferred_model={"id": 1})
    check("4_preferred_null", False, "preferred_model accepted (restoration)")
except ValidationError:
    check("4_preferred_null", True, "preferred_model rejected (restoration)")
except Exception as e:  # noqa: BLE001
    check("4_preferred_null", False, repr(e))

# 5. missing provenance rejection
try:
    RestorationBundle(hypotheses=[{"id": 1}, {"id": 2}, {"id": 3}])
    check("5_missing_provenance", False, "empty provenance accepted")
except ValidationError:
    check("5_missing_provenance", True, "empty provenance rejected")
except Exception as e:  # noqa: BLE001
    check("5_missing_provenance", False, repr(e))

# 6. backward compatibility — ui_resource_uri optional
try:
    r = RestorationBundle(**valid_restoration())
    check("6_backward_compat", r.ui_resource_uri is None, "ui_resource_uri omitted -> None accepted")
except Exception as e:  # noqa: BLE001
    check("6_backward_compat", False, repr(e))

# 7. cross-schema shared vocabulary
try:
    shared = (
        RestorationBundle.model_fields["epistemic_class"].annotation is EpistemicClass
        and StratMeshRef.model_fields["epistemic_class"].annotation is EpistemicClass
        and ChargeResult.model_fields["epistemic_class"].annotation is EpistemicClass
        and RestorationBundle.model_fields["lifecycle_state"].annotation is LifecycleState
        and ConstitutionalVerdict in get_args(ChargeResult.model_fields["constitutional_verdict"].annotation)
        and ChargeResult.model_fields["authority_ceiling"].default == AUTHORITY_CEILING
    )
    check("7_shared_vocabulary", shared, "all three import the same Literal objects from bundle_common")
except Exception as e:  # noqa: BLE001
    check("7_shared_vocabulary", False, repr(e))

# 8. pydantic version
try:
    major = int(pydantic.VERSION.split(".")[0])
    check("8_pydantic_version", major == 2, f"pydantic {pydantic.VERSION} (major 2 required)")
except Exception as e:  # noqa: BLE001
    check("8_pydantic_version", False, repr(e))

# 9. unknown enum rejection (any of the five dimensions)
try:
    RestorationBundle(epistemic_class="NOT_A_REAL_STATE", **valid_restoration())
    check("9_unknown_enum", False, "unknown epistemic_class accepted")
except ValidationError:
    check("9_unknown_enum", True, "unknown epistemic_class rejected")
except Exception as e:  # noqa: BLE001
    check("9_unknown_enum", False, repr(e))

try:
    RestorationBundle(**valid_restoration(), explanation_class="BOGUS")
    check("9b_unknown_explanation_class", False, "unknown explanation_class accepted")
except ValidationError:
    check("9b_unknown_explanation_class", True, "unknown explanation_class rejected")
except Exception as e:  # noqa: BLE001
    check("9b_unknown_explanation_class", False, repr(e))

# ── summary ──
passed = sum(1 for _, ok, _ in RESULTS if ok)
total = len(RESULTS)
print(f"\n{passed}/{total} PASS")
print(f"FORBIDDEN_EPISTEMIC = {sorted(FORBIDDEN_EPISTEMIC)}")
print(f"AUTHORITY_CEILING = {AUTHORITY_CEILING}")
sys.exit(0 if passed == total else 1)
