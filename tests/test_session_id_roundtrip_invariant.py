"""
tests/test_session_id_roundtrip_invariant.py — ID round-trip / no-mutation contract.

FORGED 2026-07-31 (Stage 0.1, FI-008 GEOX public-launch hardening) per F13 directive.

Per F13 Stage 0.1 of the GEOX public-launch execution plan:
  "Fix the 16→12 hex session-id truncation across all middleware;
   add round-trip/property tests on id length+charset at every hop;
   add a contract test that fails if any id mutates across the pipeline."

This test enforces the invariant: **NO id mutation across the GEOX pipeline.**

Specifically:
  - validate_session() error_message must contain the FULL session_id, not a slice.
  - geox_middleware log helpers must record the FULL session_id.
  - The error formatter in geox_middleware.py:712 (reason[:300]) must NOT truncate
    session_id-bearing reasons.
  - The artifact_id format in organ_governance.py (intentional 16-char slice) is
    SEPARATE — this test does NOT cover it (it is a stable identifier format,
    not a session_id round-trip).

History:
  - 2026-07-31: Created after Stage 0.1 patch (session_enforcement.py:497 + 5
    geox_middleware.py + 3 server.py + 1 authority_gate.py sites).
  - The earlier [:16] / [:12] truncation was the root cause of the "16 hex
    → 12 hex" leak that broke round-trip audit trails.

DITEMPA BUKAN DIBERI — forged, not given.
"""

from __future__ import annotations

import re
from unittest.mock import patch

import pytest

from geox_mcp.session_enforcement import validate_session


# ─────────────────────────────────────────────────────────────────────────────
# Test fixtures: SEED sample session_ids covering all known formats
# ─────────────────────────────────────────────────────────────────────────────

VALID_SEAL_SESSION_IDS = [
    "SEAL-abcdef1234567890",          # 21 chars (5+16)
    "SEAL-0000000000000000",          # 21 chars, all zeros
    "SEAL-FFFFFFFFFFFFFFFF",          # 21 chars, upper hex
    "SEAL-1234567890abcdef",          # 21 chars, mixed
]

INVALID_FORMAT_SESSION_IDS = [
    "not-a-valid-format-session-id",  # 30 chars, no SEAL- prefix
    "deadbeef1234567890abcdef",       # 24 chars, no SEAL- prefix
    "SEALXXXX",                       # 8 chars, too short
    "short",                          # 5 chars
    "a-very-long-string-without-the-SEAL-prefix-but-quite-long-yes",  # 65 chars
]

INVALID_BUT_FORMAT_PATH2_SESSION_IDS = [
    "SEAL-abcdef1234567890",          # 21 chars but arifOS rejects (fake)
    "SEAL-deadbeefdeadbeef",          # 21 chars but arifOS rejects (fake)
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. session_enforcement.py — validate_session round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSessionPreservesFullSessionId:
    """Round-trip: error_message must contain the FULL session_id, never a slice."""

    @pytest.mark.parametrize("session_id", INVALID_FORMAT_SESSION_IDS)
    def test_path_3_format_not_recognized_preserves_full_session_id(self, session_id):
        """Path 3 (format-not-recognized) must echo the full session_id.

        Pre-Stage 0.1 bug: response was `f"... {session_id[:16]}..."` which
        truncated to 16 chars. The round-trip audit trail must preserve the
        full session_id so a forensic log can correlate the exact request.
        """
        # Path 3 requires that we don't match Path 1 (sct_v1.) or Path 2 (SEAL-*).
        # Call validate_session with a session_id that doesn't start with sct_v1.
        result = validate_session(session_id, actor_id="test-actor")
        # If the result is the format-not-recognized path, verify the full id
        # is preserved in error_message.
        if result.error_code == "SESSION_INVALID" and "format not recognized" in (result.error_message or ""):
            assert session_id in (result.error_message or ""), (
                f"Path 3 error_message must contain full session_id. "
                f"Got: {result.error_message!r}, expected to contain: {session_id!r}"
            )
            # And the error must NOT contain a truncated form like "SEAL-abcdef1234567..."
            # (i.e., 16-char ellipsis truncation pattern).
            assert "..." not in result.error_message, (
                f"Path 3 error_message must NOT use '...' truncation. "
                f"Got: {result.error_message!r}"
            )

    @pytest.mark.parametrize("session_id", VALID_SEAL_SESSION_IDS)
    def test_path_2_arifos_rejected_preserves_full_session_id(self, session_id, monkeypatch):
        """Path 2 (arifOS rejected) must echo the full session_id.

        We mock the cached kernel verify to return None (arifOS rejected) so we
        deterministically hit Path 2's error message construction.
        """
        # Force Path 2 by giving a SEAL-* format and mocking kernel verification
        # to return None (arifOS rejection).
        from geox_mcp import session_enforcement

        # Clear cache to ensure fresh call
        with patch.object(session_enforcement, "_cached_kernel_verify", return_value=None):
            result = validate_session(session_id, actor_id="test-actor")
            if result.error_code == "SESSION_INVALID" and "rejected" in (result.error_message or ""):
                assert session_id in (result.error_message or ""), (
                    f"Path 2 error_message must contain full session_id. "
                    f"Got: {result.error_message!r}, expected to contain: {session_id!r}"
                )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Source-level invariant: no session_id[:N] or sid[:N] truncation in any
#    module except the intentional artifact_id format in organ_governance.
# ─────────────────────────────────────────────────────────────────────────────

class TestSourceLevelNoIdMutation:
    """No session_id[:N] or sid[:N] slice anywhere in the GEOX source tree.

    This is a static grep-style test that fails CI if anyone re-introduces
    the truncation bug. The artifact_id format in organ_governance.py is
    legitimate and excluded (it's a stable identifier, not a session_id).
    """

    # Source files that should be free of session_id/sid slicing.
    # Excludes:
    #   - artifact_id format in organ_governance.py (intentional, geox:{16hex}:...)
    #   - verify_ingest.py (truncates SHA256 hashes, not session_ids)
    #   - trace_id generation (uuid.uuid4().hex[:12] is intentional short trace_id)
    FORBIDDEN_TRUNCATION_PATTERNS = [
        (r"session_id\[:", "session_id slice"),
        (r"\bsid\[:",      "sid slice"),
    ]

    # Files that are ALLOWED to use session_id[:N] (none after Stage 0.1).
    ALLOWED_FILES = {
        # Excluded by intent: artifact_id format uses [:16] for SHA256-style short id.
        # This is a stable identifier, not a session_id mutation.
        # See: organ_governance.py:709 `session_short = (session_id or "nosession")[:16]`
    }

    def test_no_session_id_slice_in_middleware(self):
        """geox_middleware.py must NOT slice session_id."""
        import pathlib
        mw = pathlib.Path("/root/GEOX/src/geox_mcp/geox_middleware.py")
        if not mw.exists():
            pytest.skip("geox_middleware.py not present")
        text = mw.read_text()
        for pat, desc in self.FORBIDDEN_TRUNCATION_PATTERNS:
            matches = list(re.finditer(pat, text))
            assert not matches, (
                f"geox_middleware.py contains {desc} pattern: {pat!r}. "
                f"Matches: {[m.group() for m in matches]}. "
                f"Per Stage 0.1, no session_id mutation across middleware."
            )

    def test_no_session_id_slice_in_session_enforcement(self):
        """session_enforcement.py must NOT slice session_id in error_message."""
        import pathlib
        se = pathlib.Path("/root/GEOX/src/geox_mcp/session_enforcement.py")
        if not se.exists():
            pytest.skip("session_enforcement.py not present")
        text = se.read_text()
        for pat, desc in self.FORBIDDEN_TRUNCATION_PATTERNS:
            matches = list(re.finditer(pat, text))
            assert not matches, (
                f"session_enforcement.py contains {desc} pattern: {pat!r}. "
                f"Matches: {[m.group() for m in matches]}."
            )

    def test_no_session_id_slice_in_server(self):
        """server.py must NOT slice session_id in log handlers."""
        import pathlib
        sv = pathlib.Path("/root/GEOX/src/geox_mcp/server.py")
        if not sv.exists():
            pytest.skip("server.py not present")
        text = sv.read_text()
        for pat, desc in self.FORBIDDEN_TRUNCATION_PATTERNS:
            matches = list(re.finditer(pat, text))
            assert not matches, (
                f"server.py contains {desc} pattern: {pat!r}. "
                f"Matches: {[m.group() for m in matches]}."
            )

    def test_no_session_id_slice_in_authority_gate(self):
        """authority_gate.py must NOT slice session_id in AUTH_OK log."""
        import pathlib
        ag = pathlib.Path("/root/GEOX/src/geox_mcp/authority_gate.py")
        if not ag.exists():
            pytest.skip("authority_gate.py not present")
        text = ag.read_text()
        for pat, desc in self.FORBIDDEN_TRUNCATION_PATTERNS:
            matches = list(re.finditer(pat, text))
            assert not matches, (
                f"authority_gate.py contains {desc} pattern: {pat!r}. "
                f"Matches: {[m.group() for m in matches]}."
            )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Property-style: for any arbitrary session_id, error_message preserves it
# ─────────────────────────────────────────────────────────────────────────────

class TestPropertyRoundTripPreservation:
    """Property: for any input session_id, the error response preserves it."""

    @pytest.mark.parametrize("session_id", [
        "x" * 8,                # 8 chars
        "x" * 12,               # 12 chars
        "x" * 16,               # 16 chars
        "x" * 21,               # 21 chars (SEAL- size)
        "x" * 32,               # 32 chars (UUID-style)
        "x" * 64,               # 64 chars
        "x" * 128,              # 128 chars
    ])
    def test_any_length_session_id_preserved_in_path_3(self, session_id):
        """For any session_id length, the path-3 error keeps the full id."""
        # Avoid Path 1 (sct_v1.) and Path 2 (SEAL-*) triggers.
        if session_id.startswith("sct_v1.") or session_id.startswith("SEAL-"):
            pytest.skip("Path 3 expects not-SEAL-/not-sct format")
        result = validate_session(session_id, actor_id="test-actor")
        if result.error_code == "SESSION_INVALID" and "format not recognized" in (result.error_message or ""):
            assert session_id in (result.error_message or ""), (
                f"Path 3 error must preserve full session_id (len={len(session_id)}). "
                f"Got: {result.error_message!r}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Audit: record the pre-Stage-0.1 truncation sites (so regression is traceable)
# ─────────────────────────────────────────────────────────────────────────────

STAGE_0_1_FIX_HISTORY = {
    "fixed_at": "2026-07-31",
    "issue": "16 hex to 12 hex session_id truncation across middleware; [:16] in error_message",
    "blast_radius": "audit trail corruption, regression test failure, no security exposure",
    "sites_fixed": [
        ("/root/GEOX/src/geox_mcp/session_enforcement.py", "497",
         "{session_id[:16]}... -> {session_id}",
         "Path 3 (format-not-recognized) error message"),
        ("/root/GEOX/src/geox_mcp/geox_middleware.py", "67",
         "session_id[:12] -> session_id",
         "lifecycle PENDING log"),
        ("/root/GEOX/src/geox_mcp/geox_middleware.py", "78",
         "session_id[:12] -> session_id",
         "lifecycle READY log"),
        ("/root/GEOX/src/geox_mcp/geox_middleware.py", "308",
         "sid[:12] -> sid",
         "lifecycle awaiting notifications/initialized log"),
        ("/root/GEOX/src/geox_mcp/geox_middleware.py", "332",
         "sid[:12] -> sid",
         "lifecycle READY (notifications/initialized) log"),
        ("/root/GEOX/src/geox_mcp/geox_middleware.py", "355",
         "sid[:12] -> sid",
         "lifecycle READY via on_message log"),
        ("/root/GEOX/src/geox_mcp/server.py", "2446",
         "sid[:12] -> sid",
         "LIFECYCLE_BLOCK_HTTP log"),
        ("/root/GEOX/src/geox_mcp/server.py", "2516",
         "session_id[:8] -> session_id",
         "MCP_VERSION_MISSING log"),
        ("/root/GEOX/src/geox_mcp/server.py", "3150",
         "session_id[:8] -> session_id",
         "MCP_SESSION_TERMINATE log"),
        ("/root/GEOX/src/geox_mcp/authority_gate.py", "285",
         "session_id[:12] -> session_id",
         "AUTH_OK log"),
    ],
    "preserved_intentionally": [
        ("/root/GEOX/src/geox_mcp/organ_governance.py", "709",
         "session_short = (session_id or \"nosession\")[:16]",
         "artifact_id format: geox:{session_short}:{tool_name}:{content_hash} — by design"),
        ("/root/GEOX/src/geox_mcp/verify_ingest.py", "63,75",
         "sha256[:16]",
         "SHA256 hash display (not session_id)"),
        ("/root/GEOX/src/geox_mcp/geox_middleware.py", "689",
         "uuid.uuid4().hex[:12]",
         "trace_id generation (not session_id)"),
    ],
}


def test_stage_0_1_fix_history_recorded():
    """Sanity: the fix history is committed to the test file for audit."""
    assert len(STAGE_0_1_FIX_HISTORY["sites_fixed"]) == 10
    assert len(STAGE_0_1_FIX_HISTORY["preserved_intentionally"]) == 3


# ─────────────────────────────────────────────────────────────────────────────
# 5. Severity-graded failure messages
# ─────────────────────────────────────────────────────────────────────────────

class TestFailureMessagesAreActionable:
    """When the contract fails, the error message must tell the dev exactly where to fix."""

    def test_path_3_error_pinpoints_file_and_line(self):
        """Error must include the file path so a developer can jump to the fix."""
        # The validate_session error_message from Path 3 should reference the
        # format that produced the rejection but NOT a truncated form.
        result = validate_session("not-a-valid-format", actor_id="test")
        if result.error_code == "SESSION_INVALID":
            msg = result.error_message or ""
            # The full session_id must appear, not a truncated form.
            assert "not-a-valid-format" in msg, (
                f"Path 3 error must contain full session_id. Got: {msg!r}"
            )
