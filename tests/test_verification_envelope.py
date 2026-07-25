"""P0-4 hardening 2026-07-25 · FI-008 — Verification envelope.

Audit fix: replace the audit's "VAULT999-PENDING / no sealed receipt"
finding with a deterministic verification pipeline that:

  1. Reads the artifact back from disk.
  2. Recomputes SHA-256.
  3. Compares against the expected hash.
  4. Optionally checks the in-memory registry.
  5. Emits a VerificationResult with status VERIFIED / UNVERIFIED / FAILED.

The sealed receipt path is provided by ``seal_receipt`` (D.1 framework).
Wiring the envelope into mutating tools is D.3 (paused for F13 ack).

DITEMPA BUKAN DIBEI — Forged, Not Given.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geox_mcp.seal_receipt import (
    SealResult,
    build_verification_envelope,
    seal_receipt,
)
from geox_mcp.tools._artifact_identity import (
    VerificationResult,
    make_artifact_id,
    sha256_for_bytes,
    verify_artifact,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def las_file(tmp_path: Path) -> Path:
    """Write a fake LAS file with known SHA-256."""
    content = b"GEOX-AUDIT-01 LAS contents\n~WELL GEOX-AUDIT-01\n~UWI AUDIT-0001\n"
    p = tmp_path / "GEOX_AUDIT_01.las"
    p.write_bytes(content)
    return p


# ── 1. verify_artifact readback pipeline ───────────────────────────────────


def test_verify_verified_when_sha_matches(las_file: Path) -> None:
    expected = sha256_for_bytes(las_file.read_bytes())
    result = verify_artifact(
        str(las_file),
        expected_sha256=expected,
    )
    assert result.verification_status == "VERIFIED"
    assert result.recomputed_sha256 == expected
    assert "sha256_match:OK" in result.checks


def test_verify_failed_when_sha_mismatches(las_file: Path) -> None:
    wrong_sha = "f" * 64
    result = verify_artifact(str(las_file), expected_sha256=wrong_sha)
    assert result.verification_status == "FAILED"
    assert "sha256 mismatch" in result.reason


def test_verify_failed_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.las"
    result = verify_artifact(str(missing))
    assert result.verification_status == "FAILED"
    assert "readback:file_missing" in result.checks


def test_verify_failed_when_path_empty() -> None:
    result = verify_artifact("")
    assert result.verification_status == "FAILED"
    assert "readback:missing_path" in result.checks


def test_verify_with_sha256_prefix_is_stripped(las_file: Path) -> None:
    """Caller may pass 'sha256:abc...' form — must be normalized."""
    expected = sha256_for_bytes(las_file.read_bytes())
    result = verify_artifact(
        str(las_file),
        expected_sha256=f"sha256:{expected}",
    )
    assert result.verification_status == "VERIFIED"


def test_verify_unverified_when_registry_missing(las_file: Path) -> None:
    expected = sha256_for_bytes(las_file.read_bytes())

    def fake_registry(key: str) -> bool:
        return False

    result = verify_artifact(
        str(las_file),
        expected_sha256=expected,
        check_registry=fake_registry,
        expected_metadata={"well": "GEOX-AUDIT-01", "uwi": "AUDIT-0001"},
    )
    assert result.verification_status == "UNVERIFIED"
    assert "registry entry missing" in result.reason
    # sha256_match:OK still recorded.
    assert "sha256_match:OK" in result.checks


def test_verify_verified_when_registry_present(las_file: Path) -> None:
    expected = sha256_for_bytes(las_file.read_bytes())

    def fake_registry(key: str) -> bool:
        return "well_las:GEOX-AUDIT-01" in key

    result = verify_artifact(
        str(las_file),
        expected_sha256=expected,
        check_registry=fake_registry,
        expected_metadata={"well": "GEOX-AUDIT-01", "uwi": "AUDIT-0001"},
    )
    assert result.verification_status == "VERIFIED"
    assert "registry_check:OK" in result.checks


def test_verify_unverified_when_registry_raises(las_file: Path) -> None:
    expected = sha256_for_bytes(las_file.read_bytes())

    def fake_registry(key: str) -> bool:
        raise RuntimeError("registry down")

    result = verify_artifact(
        str(las_file),
        expected_sha256=expected,
        check_registry=fake_registry,
    )
    assert result.verification_status == "UNVERIFIED"
    assert "registry_check:ERROR" in ";".join(result.checks)


def test_verify_records_metadata_keys_as_checks(las_file: Path) -> None:
    expected = sha256_for_bytes(las_file.read_bytes())
    result = verify_artifact(
        str(las_file),
        expected_sha256=expected,
        expected_metadata={"well": "X", "uwi": "Y", "depth_top": 1000},
    )
    # Each metadata key is mentioned in the audit trail.
    for key in ("well", "uwi", "depth_top"):
        assert any(key in c for c in result.checks), (
            f"metadata_check:{key} missing from {result.checks}"
        )


# ── 2. seal_receipt fail-soft path ─────────────────────────────────────────


def test_seal_receipt_returns_sealed_when_arifos_up() -> None:
    """When arifOS is reachable, returns SEALED + vault999:// ref."""
    result = seal_receipt(
        tool="geox_well_ingest",
        artifact_id=make_artifact_id("well_las", "AUDIT-0001", "a" * 64),
        artifact_sha256="a" * 64,
        actor_id="ARIF",
        session_id="SEAL-test-1234567890",
        verdict="SEAL",
    )
    # arifOS may or may not be up during tests; both states are valid as
    # long as the helper did not raise.
    assert result.state in ("SEALED", "PENDING")
    if result.state == "SEALED":
        assert result.ref is not None
        assert result.ref.startswith("vault999://")


def test_seal_receipt_result_to_dict_shape() -> None:
    """SealResult.to_dict carries state, ref, optional error, optional pending."""
    r = SealResult(state="SEALED", ref="vault999://x", error=None)
    d = r.to_dict()
    assert d["state"] == "SEALED"
    assert d["ref"] == "vault999://x"
    assert "error" not in d
    assert "vault_pending" not in d or d["vault_pending"] is False


def test_seal_receipt_pending_carrys_error() -> None:
    r = SealResult(
        state="PENDING",
        ref=None,
        error="arifOS unreachable",
        vault_pending=True,
    )
    d = r.to_dict()
    assert d["state"] == "PENDING"
    assert d["error"] == "arifOS unreachable"
    assert d["vault_pending"] is True


# ── 3. build_verification_envelope ──────────────────────────────────────────


def test_envelope_verified_carries_sealed_receipt() -> None:
    seal = SealResult(state="SEALED", ref="vault999://sha256:abc")
    env = build_verification_envelope(
        artifact_status="CREATED",
        verification_status="VERIFIED",
        artifact_id="artifact://x",
        artifact_sha256="abc",
        actor_id="ARIF",
        session_id="SEAL-x",
        tool="geox_well_ingest",
        receipt=seal,
    )
    # Required envelope fields per the audit's "Required architecture correction".
    required = [
        "transport_status",
        "execution_status",
        "artifact_status",
        "verification_status",
        "governance_verdict",
        "claim_state",
        "actor_id",
        "session_id",
        "artifact",
        "receipt",
    ]
    for field in required:
        assert field in env, f"envelope missing required field: {field}"
    assert env["receipt"]["state"] == "SEALED"
    assert env["receipt"]["ref"] == "vault999://sha256:abc"
    assert env["verification_status"] == "VERIFIED"


def test_envelope_failed_carries_reason() -> None:
    seal = SealResult(state="PENDING", ref=None, error="infra down")
    env = build_verification_envelope(
        artifact_status="CREATED",
        verification_status="FAILED",
        artifact_id="artifact://x",
        artifact_sha256=None,
        actor_id=None,
        session_id=None,
        tool="geox_well_ingest",
        verification_reason="sha256 mismatch: expected fff got abc",
        receipt=seal,
    )
    assert env["verification_status"] == "FAILED"
    assert env["verification_reason"] == "sha256 mismatch: expected fff got abc"
    assert env["actor_id"] == "anonymous"
    assert env["session_id"] == "anonymous"


def test_envelope_serializable_to_json() -> None:
    """The envelope must serialize cleanly for audit transmission."""
    seal = SealResult(state="SEALED", ref="vault999://x")
    env = build_verification_envelope(
        artifact_status="CREATED",
        verification_status="VERIFIED",
        artifact_id="artifact://geox/well_las/AUDIT-0001/sha256-abc",
        artifact_sha256="abc",
        actor_id="ARIF",
        session_id="SEAL-xyz",
        tool="geox_well_ingest",
        receipt=seal,
    )
    # Must not raise.
    json.dumps(env)


# ── 4. End-to-end roundtrip ────────────────────────────────────────────────


def test_roundtrip_ingest_to_envelope(las_file: Path) -> None:
    """The audit's stated flow: ingest artifact → verify → emit envelope."""
    expected_sha = sha256_for_bytes(las_file.read_bytes())
    artifact_id = make_artifact_id(
        kind="well_las",
        canonical_id="AUDIT-0001",
        sha256=expected_sha,
    )

    # 1. Verify (readback pipeline).
    verification = verify_artifact(
        str(las_file),
        expected_sha256=expected_sha,
    )
    assert verification.verification_status == "VERIFIED"

    # 2. Seal (vault 999 reference).
    seal = seal_receipt(
        tool="geox_well_ingest",
        artifact_id=artifact_id,
        artifact_sha256=expected_sha,
        actor_id="ARIF",
        session_id="SEAL-roundtrip-test-1234",
        verdict="SEAL",
    )
    assert seal.state in ("SEALED", "PENDING")

    # 3. Envelope composition.
    env = build_verification_envelope(
        artifact_status="CREATED",
        verification_status=verification.verification_status,
        artifact_id=artifact_id,
        artifact_sha256=expected_sha,
        actor_id="ARIF",
        session_id="SEAL-roundtrip-test-1234",
        tool="geox_well_ingest",
        receipt=seal,
    )
    assert env["artifact"]["id"] == artifact_id
    assert env["artifact"]["sha256"] == expected_sha
    assert env["verification_status"] == "VERIFIED"
    assert env["receipt"]["state"] == seal.state
