"""
GEOX Alignment Tests — Substrate Layer (F1, F7, F10, F11, F13)

These tests run against the LIVE hardened arifOS substrate on Supabase.
They exercise the constitutional floors mechanically (RLS + CHECK +
TRIGGER + SECURITY DEFINER) — not application-layer checks.

Reference: /root/geox/docs/GEOXALIGNMENTTESTS.md §1

Sovereign: arif (F13). Sealed: 2026-06-24.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import pytest

# === Live substrate connection (fail-closed — no hardcoded creds) ===
DATABASE_URL = os.environ.get("DATABASE_URL")
PGPASSWORD = os.environ.get("PGPASSWORD", "")

if not DATABASE_URL:
    pytest.skip(
        "DATABASE_URL not set — alignment tests require a live substrate. "
        "Export DATABASE_URL and PGPASSWORD before running.",
        allow_module_level=True,
    )


def run_psql(sql: str, role: str | None = None) -> tuple[str, str, int]:
    """Run SQL via psql. Returns (stdout, stderr, rc)."""
    cmd = ["psql", DATABASE_URL, "-t", "-A"]
    if role:
        cmd += ["-c", f"SET ROLE {role};"]
    cmd += ["-c", sql]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={"PGPASSWORD": PGPASSWORD, "PATH": os.environ.get("PATH", "")},
    )
    return result.stdout, result.stderr, result.returncode


def grant_role_for_test(role: str) -> None:
    """Ensure postgres can SET ROLE to the test role (one-time setup)."""
    out, err, rc = run_psql(f"GRANT {role} TO postgres;")
    if rc != 0 and "already a member" not in err:
        # Already granted — silent success
        pass


# === Session GUC factory ===

def make_session(
    actor_id: str = "test_align_substrate",
    session_id: str | None = None,
    organ: str = "GEOX",
    blast_radius: str = "LOW",
    humility_override: str = "false",
    sovereign_approval: str = "true",
    floor_signature: str = "geo_x_2026_align_test",
) -> dict[str, str]:
    if session_id is None:
        session_id = f"align_test_{uuid.uuid4().hex[:12]}"
    return {
        "actor_id": actor_id,
        "session_id": session_id,
        "organ": organ,
        "blast_radius": blast_radius,
        "humility_override": humility_override,
        "sovereign_approval": sovereign_approval,
        "floor_signature": floor_signature,
    }


def sql_with_session(session: dict[str, str], body_sql: str) -> str:
    """Wrap SQL with session GUC SETs inside a real transaction.

    SET LOCAL only takes effect inside an explicit transaction block.
    Without BEGIN/COMMIT, PostgreSQL ignores the GUC settings.
    """
    gucs = "\n".join(
        f"SET LOCAL app.{k} = '{v}';"
        for k, v in session.items()
    )
    return (
        f"BEGIN;\n"
        f"SET ROLE arifos_memory_writer;\n"
        f"{gucs}\n"
        f"{body_sql}\n"
        f"COMMIT;"
    )


# === F1 — AMANAH ===

class TestF1Amanah:
    """F1: Identity & isolation."""

    def test_t1_1_per_agent_write_isolation(self):
        """T1.1: Agent A cannot modify Agent B's records without sovereign approval."""
        # Setup: ensure postgres can SET ROLE
        grant_role_for_test("arifos_memory_writer")

        # Alice has sovereign_approval (legitimate writer)
        session_a = make_session(
            actor_id="agent_a_isolation",
            session_id="t1_1_session_a",
            sovereign_approval="true",
        )
        # Bob has NO sovereign_approval — should be blocked by RLS
        session_b = make_session(
            actor_id="agent_b_isolation",
            session_id="t1_1_session_b",
            sovereign_approval="false",
        )

        # Agent A writes a record via constitutional path
        write_sql = sql_with_session(
            session_a,
            """
            SELECT arifos_memory_write(
                '{"type":"semantic","subject":"t1_1_a","content":"alice","confidence":0.5}'::jsonb
            )::text;
            """,
        )
        out, err, rc = run_psql(write_sql)
        assert rc == 0, f"Agent A write failed: {err}"
        alice_id = [l for l in out.splitlines() if l.strip() and not l.strip().startswith("SET") and l.strip() not in ("BEGIN", "COMMIT")][-1]

        # Agent B attempts to UPDATE Alice's record (no sovereign_approval → should fail)
        update_sql = sql_with_session(
            session_b,
            f"""
            UPDATE arifosmcp_memory_records
            SET content = 'bob tampered'
            WHERE memory_id = '{alice_id}';
            """,
        )
        out, err, rc = run_psql(update_sql)
        # Expectation: RLS refuses (42501) OR updates 0 rows
        if rc == 0:
            # If no error, the WHERE matched 0 rows (RLS filtering at USING)
            # Verify content unchanged
            verify_sql = f"SELECT content FROM arifosmcp_memory_records WHERE memory_id = '{alice_id}';"
            out2, _, _ = run_psql(verify_sql, role="postgres")
            content_lines = [l for l in out2.splitlines() if l.strip() and l.strip() != "SET"]
            content = content_lines[0] if content_lines else ""
            assert "tampered" not in content, \
                f"Agent B modified Alice's record (sovereign_approval=False bypassed!): content={content!r}"
        else:
            # RLS errored out — perfect
            assert "42501" in err or "permission denied" in err.lower() or "row-level security" in err.lower(), \
                f"Unexpected error: {err[:200]}"

    def test_t1_3_tamper_detection(self):
        """T1.3: Manual modification of chain_hash is detected."""
        grant_role_for_test("arifos_vault_sealer")

        # Get an existing chain_hash
        out, _, _ = run_psql(
            "SELECT seal_hash FROM vault_seals ORDER BY id DESC LIMIT 1;",
            role="postgres",
        )
        prev_seal = out.strip().splitlines()[-1]

        # Attempt to insert with INTENTIONALLY WRONG chain_hash
        # We expect the trigger to refuse
        # SET LOCAL requires an explicit transaction block
        sql = f"""
        BEGIN;
        SET ROLE arifos_vault_sealer;
        SET LOCAL app.actor_id = 'tamper_test';
        SET LOCAL app.sovereign_approval = 'true';
        INSERT INTO vault_seals (
            record_id, seal_hash, prev_seal_id, agent_id, action, payload, chain_hash
        ) VALUES (
            gen_random_uuid(),
            'tampered_seal_{uuid.uuid4().hex[:8]}',
            '{prev_seal}',
            'tamper_test',
            'tamper',
            '{{"x":1}}'::jsonb,
            'INTENTIONALLY_WRONG_CHAIN_HASH_VALUE'
        );
        COMMIT;
        """
        out, err, rc = run_psql(sql, role="postgres")
        # Either the trigger raised (preferred) or the wrong chain_hash was inserted (failure)
        if rc == 0:
            # Cleanup the bad row
            run_psql(
                "DELETE FROM vault_seals WHERE chain_hash = 'INTENTIONALLY_WRONG_CHAIN_HASH_VALUE';",
                role="postgres",
            )
            pytest.fail("Tampering was not detected by chain integrity trigger")
        assert "F1_AMANAH_HOLD" in err or "chain_hash mismatch" in err, \
            f"Unexpected error (no tamper detection): {err[:200]}"


# === F7 — HUMILITY ===

class TestF7Humility:
    """F7: Confidence cap."""

    def test_t7_1_cap_enforcement(self):
        """T7.1: confidence > 0.90 without override is refused."""
        session = make_session(session_id="t7_1_cap_test")
        sql = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"semantic","subject":"t7_1","content":"x","confidence":0.95}'::jsonb
            );
            """,
        )
        out, err, rc = run_psql(sql)
        assert rc != 0, "Confidence > 0.90 was accepted without override"
        assert "F7_HUMILITY_HOLD" in err, f"Expected F7_HUMILITY_HOLD, got: {err[:200]}"

    def test_t7_2_override_path(self):
        """T7.2: confidence > 0.90 WITH override is accepted."""
        session = make_session(
            session_id="t7_2_override_test",
            humility_override="true",
        )
        sql = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"semantic","subject":"t7_2","content":"x","confidence":0.95}'::jsonb
            )::text;
            """,
        )
        out, err, rc = run_psql(sql)
        assert rc == 0, f"Override path failed: {err[:200]}"
        assert out.strip(), "No memory_id returned"


# === F10 — ONTOLOGY ===

class TestF10Ontology:
    """F10: Type discipline."""

    def test_t10_1_canonical_types_only(self):
        """T10.1: type='OTHER' is rejected by CHECK constraint."""
        # Use arifos_memory_write (which enforces F10 in the function too)
        session = make_session(session_id="t10_1_ontology_test")
        sql = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"OTHER","subject":"t10_1","content":"x","confidence":0.5}'::jsonb
            );
            """,
        )
        out, err, rc = run_psql(sql)
        # Either the function refuses or the CHECK constraint refuses
        assert rc != 0, "Non-canonical type was accepted"
        assert ("F10_ONTOLOGY_HOLD" in err or "type_check" in err or "violates check constraint" in err), \
            f"Expected F10 refusal, got: {err[:200]}"


# === F11 — AUDIT ===

class TestF11Audit:
    """F11: Every write leaves a trail."""

    def test_t11_1_insert_audit(self):
        """T11.1: INSERT into memory_records produces >= 1 audit row."""
        session = make_session(session_id="t11_1_audit_test")

        # Count before
        sql_before = f"""
        SELECT COUNT(*) FROM arifosmcp_memory_audit_log
        WHERE session_id = '{session["session_id"]}';
        """
        out_before, _, _ = run_psql(sql_before, role="postgres")
        before = int(out_before.strip().splitlines()[-1])

        # Write
        sql_write = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"working","subject":"t11_1","content":"x","confidence":0.5}'::jsonb
            )::text;
            """,
        )
        out, err, rc = run_psql(sql_write)
        assert rc == 0, f"Write failed: {err[:200]}"

        # Count after
        out_after, _, _ = run_psql(sql_before, role="postgres")
        after = int(out_after.strip().splitlines()[-1])

        delta = after - before
        assert delta >= 1, f"Expected >= 1 audit row, got {delta} (before={before}, after={after})"


# === F13 — SOVEREIGN ===

class TestF13Sovereign:
    """F13: Blast radius gate."""

    def test_t13_1_reject_unapproved_high(self):
        """T13.1: HIGH blast_radius without sovereign_approval is refused."""
        session = make_session(
            session_id="t13_1_high_test",
            blast_radius="HIGH",
            sovereign_approval="false",
        )
        sql = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"episodic","subject":"t13_1","content":"x","confidence":0.5}'::jsonb
            );
            """,
        )
        out, err, rc = run_psql(sql)
        assert rc != 0, "HIGH without approval was accepted"
        assert "F13_SOVEREIGN_HOLD" in err, \
            f"Expected F13 refusal, got: {err[:200]}"

    def test_t13_2_approval_path(self):
        """T13.2: HIGH blast_radius WITH sovereign_approval is accepted."""
        session = make_session(
            session_id="t13_2_high_approved",
            blast_radius="HIGH",
            sovereign_approval="true",
        )
        sql = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"episodic","subject":"t13_2","content":"x","confidence":0.5}'::jsonb
            )::text;
            """,
        )
        out, err, rc = run_psql(sql)
        assert rc == 0, f"HIGH with approval failed: {err[:200]}"
        assert out.strip(), "No memory_id returned"

    def test_t13_3_low_blast_no_approval_needed(self):
        """T13.3: LOW blast_radius does not require sovereign approval."""
        session = make_session(
            session_id="t13_3_low_test",
            blast_radius="LOW",
            sovereign_approval="false",
        )
        sql = sql_with_session(
            session,
            """
            SELECT arifos_memory_write(
                '{"type":"working","subject":"t13_3","content":"x","confidence":0.5}'::jsonb
            )::text;
            """,
        )
        out, err, rc = run_psql(sql)
        assert rc == 0, f"LOW blast_radius was refused: {err[:200]}"


# === Health Check ===

def test_substrate_health():
    """Verify the hardened substrate is live and constitutional functions exist."""
    # Functions
    out, _, _ = run_psql(
        """
        SELECT proname FROM pg_proc
        WHERE proname IN (
            'arifos_memory_write',
            'arifos_vault_seal_chain_check',
            'arifos_memory_records_audit_trigger',
            'arifos_check_humility_cap'
        )
        ORDER BY proname;
        """,
        role="postgres",
    )
    functions = set(out.strip().splitlines())
    expected = {
        "arifos_memory_write",
        "arifos_vault_seal_chain_check",
        "arifos_memory_records_audit_trigger",
        "arifos_check_humility_cap",
    }
    missing = expected - functions
    assert not missing, f"Missing constitutional functions: {missing}"

    # Triggers
    out, _, _ = run_psql(
        """
        SELECT trigger_name FROM information_schema.triggers
        WHERE trigger_name LIKE 'arifos_%' ORDER BY trigger_name;
        """,
        role="postgres",
    )
    triggers = set(out.strip().splitlines())
    expected_triggers = {
        "arifos_memory_records_audit",
        "arifos_vault_seals_chain_integrity",
    }
    missing_triggers = expected_triggers - triggers
    assert not missing_triggers, f"Missing triggers: {missing_triggers}"

    # Floor rules
    out, _, _ = run_psql(
        "SELECT floor_code FROM arifosmcp_floor_rules WHERE is_active ORDER BY floor_code;",
        role="postgres",
    )
    active_floors = set(out.strip().splitlines())
    expected_floors = {f"F{i:02d}" for i in range(1, 14)}
    missing_floors = expected_floors - active_floors
    assert not missing_floors, f"Missing active floor rules: {missing_floors}"


# === Entry point (for direct execution without pytest) ===

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
