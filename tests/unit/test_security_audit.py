"""
GEOX Security Audit Tests — P3 / P4 Priority
Validates: .mcpignore present, all required categories blocked, no raw data exposed.
DITEMPA BUKAN DIBERI
"""
import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from geox_mcp.tools.registry import geox_bundle_security_audit


class TestSecurityAudit:
    """GEOX must never expose raw geoscience data, secrets, or vaults."""

    @pytest.mark.asyncio
    async def test_mcpignore_present(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["mcpignore_present"] is True, (
            ".mcpignore must be present at app root — mount /root/geox/.mcpignore:/app/.mcpignore:ro"
        )

    @pytest.mark.asyncio
    async def test_secrets_category_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        cats = payload.get("required_categories_covered", {})
        assert cats.get("secrets") is True, "secrets category must be covered in .mcpignore"

    @pytest.mark.asyncio
    async def test_vaults_category_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        cats = payload.get("required_categories_covered", {})
        assert cats.get("vaults") is True, "vaults/ledger category must be covered in .mcpignore"

    @pytest.mark.asyncio
    async def test_raw_data_category_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        cats = payload.get("required_categories_covered", {})
        assert cats.get("raw_data") is True, "raw_data (*.LAS, *.segy, *.csv) must be covered in .mcpignore"

    @pytest.mark.asyncio
    async def test_build_artifacts_category_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        cats = payload.get("required_categories_covered", {})
        assert cats.get("build_artifacts") is True, "build_artifacts (dist/, node_modules/) must be covered"

    @pytest.mark.asyncio
    async def test_git_category_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        cats = payload.get("required_categories_covered", {})
        assert cats.get("git") is True, ".git/ must be covered in .mcpignore"

    @pytest.mark.asyncio
    async def test_all_required_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload.get("all_required_covered") is True, (
            "all_required_covered must be True — some categories still unblocked"
        )

    @pytest.mark.asyncio
    async def test_no_blocked_files_exposed(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        exposed = payload.get("exposed_blocked_in_resources", [])
        assert len(exposed) == 0, (
            f"Blocked files exposed in resources/: {exposed}"
        )

    @pytest.mark.asyncio
    async def test_registry_truth_pass(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        rt = payload.get("registry_truth", "")
        assert rt == "PASS", f"Security audit registry_truth must be PASS, got: {rt}"

    @pytest.mark.asyncio
    async def test_blocked_patterns_count_positive(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        count = payload.get("blocked_patterns_count", 0)
        assert count > 10, (
            f"Expected >10 blocked patterns, got {count} — .mcpignore may be empty or missing"
        )
