"""
Test registry status tools — machine-checkable validation surface.
DITEMPA BUKAN DIBERI
"""

import pytest
from geox_mcp.tools.registry import (
    geox_contradiction_registry_status,
    geox_test_receipt_status,
    geox_bundle_security_audit,
    geox_resource_registry_status,
)


class TestContradictionRegistryStatus:
    async def test_returns_detectors_list(self):
        result = await geox_contradiction_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["detectors_count"] == 11
        assert len(payload["detectors"]) == 11

    async def test_auto_hold_triggers_exactly_four(self):
        result = await geox_contradiction_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["auto_hold_count"] == 4
        assert set(payload["auto_hold_triggers"]) == {"C2", "C5", "C6", "C8"}

    async def test_all_detectors_have_required_fields(self):
        result = await geox_contradiction_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        for d in payload["detectors"]:
            assert "id" in d
            assert "name" in d
            assert "penalty" in d
            assert "auto_hold" in d
            assert "description" in d

    async def test_registry_truth_pass(self):
        result = await geox_contradiction_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["registry_truth"] == "PASS"


class TestTestReceiptStatus:
    async def test_returns_commit_hash(self):
        result = await geox_test_receipt_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert "commit_hash" in payload
        assert len(payload["commit_hash"]) == 40 or payload["commit_hash"] == "unknown"

    async def test_test_counts_present(self):
        result = await geox_test_receipt_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert "tests_passing" in payload
        assert "tests_skipped" in payload
        assert "tests_xfailed" in payload
        assert "tests_failed" in payload
        assert "total_tests" in payload

    async def test_total_equals_sum(self):
        result = await geox_test_receipt_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        total = (
            payload["tests_passing"]
            + payload["tests_skipped"]
            + payload["tests_xfailed"]
            + payload["tests_failed"]
        )
        assert payload["total_tests"] == total
        assert payload["tests_passing"] > 0  # dynamic: real count, not hardcoded
        assert payload["tests_passing"] < 2000  # sanity ceiling

    async def test_verified_at_isoformat(self):
        result = await geox_test_receipt_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert "verified_at" in payload
        assert payload["verified_at"].endswith("+00:00") or "Z" in payload["verified_at"]


class TestResourceRegistryStatus:
    async def test_returns_resource_surface(self):
        result = await geox_resource_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert "resource_surface" in payload
        rs = payload["resource_surface"]
        assert rs["playbooks"] >= 1
        assert rs["prompts"] >= 1
        assert rs["ontology"] >= 1
        assert rs["schemas"] >= 1

    async def test_total_resources_positive(self):
        result = await geox_resource_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["total_resources"] > 0

    async def test_registry_truth_pass(self):
        result = await geox_resource_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["registry_truth"] == "PASS"

    async def test_categories_present(self):
        result = await geox_resource_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert "categories" in payload
        cats = payload["categories"]
        assert "playbooks" in cats
        assert "prompts" in cats
        assert "ontology" in cats


class TestBundleSecurityAudit:
    async def test_mcpignore_present(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["mcpignore_present"] is True

    async def test_required_categories_covered(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["all_required_covered"] is True
        cats = payload["required_categories_covered"]
        assert cats["secrets"] is True
        assert cats["vaults"] is True
        assert cats["raw_data"] is True
        assert cats["build_artifacts"] is True
        assert cats["git"] is True

    async def test_no_blocked_exposed_in_resources(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["exposed_count"] == 0
        assert payload["exposed_blocked_in_resources"] == []

    async def test_registry_truth_pass(self):
        result = await geox_bundle_security_audit()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload["registry_truth"] == "PASS"
