"""
A-* amplitude physics gates — contract tests for the SCAFFOLD ONLY.

These tests assert the SHAPE of the A-* module, not the physics.
Every gate currently returns UNMEASURED with reason="gate not implemented".
Physics comes after spec ratification.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────────────────────────


ALL_GATE_IDS: tuple[str, ...] = (
    "A-POL",
    "A-PHASE",
    "A-SCALE",
    "A-PROV",
    "A-IMP",
    "A-AVO",
    "A-OFFSET",
    "A-TUNING",
    "A-PROP",
    "A-SNR",
    "A-ARTIFACT",
    "A-CONFORM",
    "A-4D",
)


def _import_module():
    from geox_mcp.tools import amplitude_gates

    return amplitude_gates


def test_module_imports_and_exposes_all_13_gates():
    mod = _import_module()
    for gid in ALL_GATE_IDS:
        func_name = "gate_" + gid.replace("-", "_").lower()
        assert hasattr(mod, func_name), f"missing {func_name}"
        fn = getattr(mod, func_name)
        assert callable(fn), f"{func_name} not callable"


# ─────────────────────────────────────────────────────────────────────────────
# Per-gate contract: verdict enum is valid, default = UNMEASURED, no SEALED
# ─────────────────────────────────────────────────────────────────────────────


VALID_STATUSES: frozenset[str] = frozenset(
    {
        "PASS",
        "WARN",
        "KILL",
        "UNMEASURED",
        "NOT_APPLICABLE",
        "PARTIALLY_MEASURED",
        "COMPUTABLE",
    }
)


def _gate_ids_to_func_names() -> list[tuple[str, str]]:
    return [(gid, "gate_" + gid.replace("-", "_").lower()) for gid in ALL_GATE_IDS]


@pytest.mark.parametrize("gate_id,func_name", _gate_ids_to_func_names())
def test_each_gate_returns_valid_verdict_enum(gate_id: str, func_name: str):
    mod = _import_module()
    fn = getattr(mod, func_name)
    r = fn({})
    assert r.get("gate_id") == gate_id
    assert r.get("gate") == gate_id
    assert r.get("status") in VALID_STATUSES, f"{gate_id} status={r.get('status')!r}"
    assert r.get("verdict") == r.get("status"), "verdict must mirror status"
    assert "receipt_hash" in r, f"{gate_id} missing receipt_hash"
    assert len(r["receipt_hash"]) == 64, f"{gate_id} receipt_hash not sha256 hex"
    # Constitutionally barred
    assert r.get("status") != "SEALED", f"{gate_id} returned SEALED — GEOX never self-seals"


@pytest.mark.parametrize("gate_id,func_name", _gate_ids_to_func_names())
def test_each_gate_default_is_unmeasured_with_stub_reason(gate_id: str, func_name: str):
    mod = _import_module()
    fn = getattr(mod, func_name)
    r = fn({})
    assert r.get("status") == "UNMEASURED", (
        f"{gate_id} must default to UNMEASURED (scaffold); got {r.get('status')!r}"
    )
    assert r.get("reason") == "gate not implemented", (
        f"{gate_id} must carry stub reason; got {r.get('reason')!r}"
    )


@pytest.mark.parametrize("gate_id,func_name", _gate_ids_to_func_names())
def test_each_gate_receipt_is_deterministic(gate_id: str, func_name: str):
    mod = _import_module()
    fn = getattr(mod, func_name)
    framework = {"framework_keys": sorted(list(ALL_GATE_IDS))}
    h1 = fn(framework)["receipt_hash"]
    h2 = fn(framework)["receipt_hash"]
    assert h1 == h2, f"{gate_id} receipt not deterministic"


# ─────────────────────────────────────────────────────────────────────────────
# Aggregator: run_all_amplitude_gates — 13 gates, all UNMEASURED by default
# ─────────────────────────────────────────────────────────────────────────────


def test_run_all_amplitude_gates_returns_13_receipts():
    mod = _import_module()
    out = mod.run_all_amplitude_gates({})
    assert "gates" in out
    assert set(out["gates"].keys()) == set(ALL_GATE_IDS)


def test_run_all_amplitude_gates_default_combined_verdict_is_unmeasured():
    mod = _import_module()
    out = mod.run_all_amplitude_gates({})
    assert out["combined_verdict"] == "UNMEASURED"
    assert out["hypothesis_status"] == "UNTESTED"


def test_run_all_amplitude_gates_class_buckets_match_spec():
    mod = _import_module()
    out = mod.run_all_amplitude_gates({})
    assert set(out["class_i_gates"]) == {"A-POL", "A-PHASE", "A-SCALE", "A-PROV"}
    assert set(out["class_ii_gates"]) == {"A-IMP", "A-AVO", "A-OFFSET", "A-TUNING", "A-PROP"}
    assert set(out["class_iii_gates"]) == {"A-SNR", "A-ARTIFACT", "A-CONFORM", "A-4D"}


def test_run_all_amplitude_gates_never_self_seals():
    mod = _import_module()
    out = mod.run_all_amplitude_gates({})
    assert out["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert out["seal_authority"] == "arifOS_only"
    assert out["preferred_hypothesis"] is None


def test_run_all_amplitude_gates_can_skip_class_iii():
    mod = _import_module()
    out = mod.run_all_amplitude_gates({}, include_class_iii=False)
    assert "A-SNR" not in out["gates"]
    assert "A-4D" not in out["gates"]
    assert set(out["gates"].keys()) == set(ALL_GATE_IDS) - set(out["class_iii_gates"])


def test_amplitude_hypothesis_status_map_is_present():
    mod = _import_module()
    m = mod.AMPLITUDE_HYPOTHESIS_STATUS_MAP
    assert m["KILL"] == "REJECTED"
    assert m["PASS"] == "SURVIVES_CURRENT_TESTS"
    assert m["UNMEASURED"] == "UNTESTED"


def test_aggregate_amplitude_hypothesis_status_empty_is_untested():
    mod = _import_module()
    s = mod.aggregate_amplitude_hypothesis_status({}, [], [], [], [])
    assert s == "UNTESTED"


def test_aggregate_amplitude_hypothesis_status_kill_is_rejected():
    mod = _import_module()
    s = mod.aggregate_amplitude_hypothesis_status({}, ["A-POL"], [], [], [])
    assert s == "REJECTED"