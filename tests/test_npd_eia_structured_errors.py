"""
tests/test_npd_eia_structured_errors.py

Unit tests for M5 (structured errors) + L3 (data_origin tagging) on the
five NPD/EIA open-energy tools.

Coverage per tool:
  - Success path: data payload present, data_origin == "OBSERVED"
  - Network/timeout failure: error="upstream_unavailable", source correct, retry_hint
  - Missing API key (EIA only): error="config_missing"
  - Upstream 4xx: error="bad_request", http_status present
  - Upstream 5xx: error="upstream_unavailable"

Invariant: a downstream helper can branch on data_origin to distinguish
synthetic vs real data.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from geox.geox_mcp.tools.open_energy_tool import (
    geox_field_observe_npd,
    geox_price_observe_eia,
    geox_production_observe_eia,
    geox_production_observe_npd,
    geox_well_load_npd,
)


# ─── shared error response factories ─────────────────────────────────────────


def _eia_timeout_result() -> dict:
    return {"_eia_error": True, "_eia_status": 0, "_eia_detail": "Connection timed out"}


def _eia_missing_key_result() -> dict:
    return {
        "_eia_error": True,
        "_eia_status": 401,
        "_eia_detail": "EIA price_spot lookup voided: missing_api_key.",
    }


def _eia_4xx_result() -> dict:
    return {
        "_eia_error": True,
        "_eia_status": 400,
        "_eia_detail": "Invalid frequency parameter",
    }


def _eia_5xx_result() -> dict:
    return {"_eia_error": True, "_eia_status": 503, "_eia_detail": "Service Unavailable"}


def _eia_success_result() -> dict:
    return {
        "_eia_provenance": {
            "source": "eia_gov_api",
            "endpoint": "petroleum/pri/spt/data",
            "requested_at": "2026-05-02T00:00:00+00:00",
            "response_status": 200,
            "row_count": 2,
            "latency_ms": 150.0,
        },
        "prices": [
            {"period": "2026-04-30", "value": "82.31", "unit": "Dollars per Barrel"},
        ],
    }


def _npd_timeout_result() -> dict:
    return {"_npd_error": True, "_npd_status": 0, "_npd_detail": "Connect timeout"}


def _npd_4xx_result() -> dict:
    return {"_npd_error": True, "_npd_status": 404, "_npd_detail": "Resource not found"}


def _npd_5xx_result() -> dict:
    return {"_npd_error": True, "_npd_status": 500, "_npd_detail": "Internal Server Error"}


def _npd_fields_success() -> dict:
    return {
        "_npd_data": [
            {"fldName": "STATFJORD", "fldStatus": "PRODUCING"},
            {"fldName": "GULLFAKS", "fldStatus": "PRODUCING"},
        ],
        "_npd_provenance": {
            "source": "npd_norway",
            "endpoint": "field",
            "requested_at": "2026-05-02T00:00:00+00:00",
            "response_status": 200,
            "row_count": 2,
        },
    }


def _npd_wellbore_success() -> dict:
    return {
        "query": "6406/2-1",
        "count": 1,
        "wellbores": [{"wlbWellboreName": "6406/2-1"}],
        "_npd_provenance": {
            "source": "npd_norway",
            "endpoint": "wellbore_search",
            "requested_at": "2026-05-02T00:00:00+00:00",
            "response_status": 200,
            "row_count": 1,
        },
    }


def _npd_production_success() -> dict:
    return {
        "field_name": "STATFJORD",
        "count": 2,
        "production": [
            {"prfInformationCarrier": "STATFJORD", "prfYear": "2026", "prfMonth": "3"}
        ],
        "_npd_provenance": {
            "source": "npd_norway",
            "endpoint": "field_production_filtered",
            "requested_at": "2026-05-02T00:00:00+00:00",
            "response_status": 200,
            "row_count": 2,
        },
    }


# ─── helpers ──────────────────────────────────────────────────────────────────


def _assert_structured_error(result: dict, expected_error: str, expected_source: str):
    """Assert canonical error shape is present."""
    assert result.get("error") == expected_error, (
        f"expected error={expected_error!r}, got {result.get('error')!r}\nresult={result}"
    )
    assert result.get("source") == expected_source, (
        f"expected source={expected_source!r}, got {result.get('source')!r}"
    )
    assert result.get("claim_tag") == "UNKNOWN", f"error must have claim_tag=VOID; got {result.get('claim_tag')!r}"
    assert result.get("status") == "error", f"error must have status=error; got {result.get('status')!r}"
    assert result.get("data_origin") is None, f"error path must have data_origin=None; got {result.get('data_origin')!r}"
    assert "vault_receipt" in result, "vault_receipt missing from error response"
    assert "limitations" in result, "limitations missing from error response"


def _assert_success(result: dict):
    """Assert canonical success shape."""
    assert result.get("status") == "loaded", f"expected status=loaded; got {result.get('status')!r}\nresult={result}"
    assert result.get("claim_tag") == "OBSERVED", f"expected claim_tag=OBSERVED"
    assert result.get("data_origin") == "OBSERVED", (
        f"success must have data_origin='OBSERVED'; got {result.get('data_origin')!r}"
    )
    assert "vault_receipt" in result, "vault_receipt missing from success response"
    assert "limitations" in result, "limitations missing from success response"


# ══════════════════════════════════════════════════════════════════════════════
# geox_price_observe_eia
# ══════════════════════════════════════════════════════════════════════════════


class TestGeoxPriceObserveEIA:
    def _patch_client(self, return_value):
        mock_client = MagicMock()
        mock_client.fetch_price_spot = AsyncMock(return_value=return_value)
        return patch(
            "geox.geox_mcp.tools.open_energy_tool.EIAClient",
            return_value=mock_client,
        )

    def test_success_data_origin_observed(self):
        with self._patch_client(_eia_success_result()):
            result = geox_price_observe_eia(commodity="wti")
        _assert_success(result)
        assert result["prices"] == _eia_success_result()["prices"]

    def test_timeout_upstream_unavailable(self):
        with self._patch_client(_eia_timeout_result()):
            result = geox_price_observe_eia(commodity="wti")
        _assert_structured_error(result, "upstream_unavailable", "eia.gov")
        assert result.get("retry_hint") == "later"

    def test_missing_api_key_config_missing(self):
        with self._patch_client(_eia_missing_key_result()):
            result = geox_price_observe_eia(commodity="brent")
        _assert_structured_error(result, "config_missing", "eia.gov")

    def test_upstream_4xx_bad_request(self):
        with self._patch_client(_eia_4xx_result()):
            result = geox_price_observe_eia(commodity="wti", frequency="bad")
        _assert_structured_error(result, "bad_request", "eia.gov")
        assert result.get("http_status") == 400

    def test_upstream_5xx_upstream_unavailable(self):
        with self._patch_client(_eia_5xx_result()):
            result = geox_price_observe_eia(commodity="wti")
        _assert_structured_error(result, "upstream_unavailable", "eia.gov")
        assert result.get("http_status") == 503

    def test_exception_upstream_unavailable(self):
        mock_client = MagicMock()
        mock_client.fetch_price_spot = AsyncMock(side_effect=ConnectionError("network gone"))
        with patch("geox.geox_mcp.tools.open_energy_tool.EIAClient", return_value=mock_client):
            result = geox_price_observe_eia(commodity="wti")
        _assert_structured_error(result, "upstream_unavailable", "eia.gov")
        assert "network gone" in result.get("details", "")


# ══════════════════════════════════════════════════════════════════════════════
# geox_production_observe_eia
# ══════════════════════════════════════════════════════════════════════════════


def _eia_prod_success() -> dict:
    return {
        "_eia_provenance": {
            "source": "eia_gov_api",
            "endpoint": "petroleum/crd/crpdn/data",
            "requested_at": "2026-05-02T00:00:00+00:00",
            "response_status": 200,
            "row_count": 3,
            "latency_ms": 210.0,
        },
        "production": [{"period": "2026-03", "value": "12900"}],
    }


class TestGeoxProductionObserveEIA:
    def _patch_client(self, return_value, data_type="crude_oil"):
        mock_client = MagicMock()
        if data_type == "crude_oil":
            mock_client.fetch_crude_production = AsyncMock(return_value=return_value)
        else:
            mock_client.fetch_natural_gas_production = AsyncMock(return_value=return_value)
        return patch(
            "geox.geox_mcp.tools.open_energy_tool.EIAClient",
            return_value=mock_client,
        )

    def test_success_data_origin_observed(self):
        with self._patch_client(_eia_prod_success()):
            result = geox_production_observe_eia(data_type="crude_oil")
        _assert_success(result)
        assert result["production"] == _eia_prod_success()["production"]

    def test_timeout_upstream_unavailable(self):
        with self._patch_client(_eia_timeout_result()):
            result = geox_production_observe_eia(data_type="crude_oil")
        _assert_structured_error(result, "upstream_unavailable", "eia.gov")
        assert result.get("retry_hint") == "later"

    def test_missing_api_key_config_missing(self):
        with patch("geox.geox_mcp.tools.open_energy_tool.EIAClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.fetch_natural_gas_production = AsyncMock(
                return_value=_eia_missing_key_result()
            )
            mock_cls.return_value = mock_client
            result = geox_production_observe_eia(data_type="natural_gas")
        _assert_structured_error(result, "config_missing", "eia.gov")

    def test_upstream_5xx_upstream_unavailable(self):
        with self._patch_client(_eia_5xx_result(), data_type="natural_gas"):
            mock_client = MagicMock()
            mock_client.fetch_natural_gas_production = AsyncMock(
                return_value=_eia_5xx_result()
            )
            with patch(
                "geox.geox_mcp.tools.open_energy_tool.EIAClient",
                return_value=mock_client,
            ):
                result = geox_production_observe_eia(data_type="natural_gas")
        _assert_structured_error(result, "upstream_unavailable", "eia.gov")


# ══════════════════════════════════════════════════════════════════════════════
# geox_well_load_npd
# ══════════════════════════════════════════════════════════════════════════════


class TestGeoxWellLoadNPD:
    def _patch_client_search(self, return_value):
        mock_client = MagicMock()
        mock_client.search_wellbore_by_name = AsyncMock(return_value=return_value)
        return patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient",
            return_value=mock_client,
        )

    def test_success_data_origin_observed(self):
        with self._patch_client_search(_npd_wellbore_success()):
            result = geox_well_load_npd(well_name="6406/2-1")
        _assert_success(result)
        assert result.get("count") == 1

    def test_timeout_upstream_unavailable(self):
        with self._patch_client_search(_npd_timeout_result()):
            result = geox_well_load_npd(well_name="TEST")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")
        assert result.get("retry_hint") == "later"

    def test_upstream_4xx_bad_request(self):
        with self._patch_client_search(_npd_4xx_result()):
            result = geox_well_load_npd(well_name="TEST")
        _assert_structured_error(result, "bad_request", "npd.no")
        assert result.get("http_status") == 404

    def test_exception_upstream_unavailable(self):
        mock_client = MagicMock()
        mock_client.search_wellbore_by_name = AsyncMock(
            side_effect=OSError("DNS failure")
        )
        with patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient", return_value=mock_client
        ):
            result = geox_well_load_npd(well_name="ANYTHING")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")


# ══════════════════════════════════════════════════════════════════════════════
# geox_field_observe_npd
# ══════════════════════════════════════════════════════════════════════════════


class TestGeoxFieldObserveNPD:
    def _patch_client_fields(self, return_value):
        mock_client = MagicMock()
        mock_client.fetch_fields = AsyncMock(return_value=return_value)
        mock_client.get_field_production = AsyncMock(return_value={"_npd_error": True})
        return patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient",
            return_value=mock_client,
        )

    def test_success_data_origin_observed(self):
        with self._patch_client_fields(_npd_fields_success()):
            result = geox_field_observe_npd(field_name="STATFJORD")
        _assert_success(result)
        assert result.get("count") >= 1

    def test_no_filter_returns_capped_list(self):
        data = _npd_fields_success()
        with self._patch_client_fields(data):
            result = geox_field_observe_npd()
        _assert_success(result)
        assert result.get("data_origin") == "OBSERVED"

    def test_timeout_on_fields_fetch(self):
        with self._patch_client_fields(_npd_timeout_result()):
            result = geox_field_observe_npd(field_name="STATFJORD")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")

    def test_upstream_5xx_upstream_unavailable(self):
        with self._patch_client_fields(_npd_5xx_result()):
            result = geox_field_observe_npd()
        _assert_structured_error(result, "upstream_unavailable", "npd.no")

    def test_exception_upstream_unavailable(self):
        mock_client = MagicMock()
        mock_client.fetch_fields = AsyncMock(side_effect=RuntimeError("boom"))
        with patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient", return_value=mock_client
        ):
            result = geox_field_observe_npd(field_name="STATFJORD")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")
        assert "boom" in result.get("details", "")


# ══════════════════════════════════════════════════════════════════════════════
# geox_production_observe_npd
# ══════════════════════════════════════════════════════════════════════════════


class TestGeoxProductionObserveNPD:
    def _patch_client_prod(self, return_value):
        mock_client = MagicMock()
        mock_client.get_field_production = AsyncMock(return_value=return_value)
        return patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient",
            return_value=mock_client,
        )

    def test_success_data_origin_observed(self):
        with self._patch_client_prod(_npd_production_success()):
            result = geox_production_observe_npd(field_name="STATFJORD")
        _assert_success(result)
        assert result.get("count") >= 1
        assert len(result.get("production", [])) >= 1

    def test_timeout_upstream_unavailable(self):
        with self._patch_client_prod(_npd_timeout_result()):
            result = geox_production_observe_npd(field_name="STATFJORD")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")
        assert result.get("retry_hint") == "later"

    def test_upstream_4xx_bad_request(self):
        with self._patch_client_prod(_npd_4xx_result()):
            result = geox_production_observe_npd(field_name="STATFJORD")
        _assert_structured_error(result, "bad_request", "npd.no")
        assert result.get("http_status") == 404

    def test_upstream_5xx_upstream_unavailable(self):
        with self._patch_client_prod(_npd_5xx_result()):
            result = geox_production_observe_npd(field_name="STATFJORD")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")

    def test_exception_upstream_unavailable(self):
        mock_client = MagicMock()
        mock_client.get_field_production = AsyncMock(side_effect=TimeoutError("NPD slow"))
        with patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient", return_value=mock_client
        ):
            result = geox_production_observe_npd(field_name="GULLFAKS")
        _assert_structured_error(result, "upstream_unavailable", "npd.no")


# ══════════════════════════════════════════════════════════════════════════════
# L3 data_origin — downstream branching invariant
# ══════════════════════════════════════════════════════════════════════════════


class TestDataOriginBranching:
    """
    Downstream helpers must be able to branch on data_origin to distinguish
    real from synthetic data without reading claim_tag.
    """

    def _decide(self, result: dict) -> str:
        origin = result.get("data_origin")
        if origin == "OBSERVED":
            return "real"
        if origin == "SYNTHETIC_FIXTURE":
            return "synthetic"
        return "unknown_or_error"

    def test_success_routes_to_real(self):
        mock_client = MagicMock()
        mock_client.get_field_production = AsyncMock(return_value=_npd_production_success())
        with patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient", return_value=mock_client
        ):
            result = geox_production_observe_npd(field_name="STATFJORD")
        assert self._decide(result) == "real"

    def test_error_routes_to_unknown_or_error(self):
        mock_client = MagicMock()
        mock_client.get_field_production = AsyncMock(return_value=_npd_timeout_result())
        with patch(
            "geox.geox_mcp.tools.open_energy_tool.NPDClient", return_value=mock_client
        ):
            result = geox_production_observe_npd(field_name="STATFJORD")
        assert self._decide(result) == "unknown_or_error"

    def test_synthetic_fixture_marker(self):
        """
        If a scaffold/mock response is ever added to these tools, it must
        carry data_origin='SYNTHETIC_FIXTURE'. This test documents the contract
        without requiring a scaffold to exist today.
        """
        synthetic_result = {
            "status": "loaded",
            "claim_tag": "HYPOTHESIS",
            "data_origin": "SYNTHETIC_FIXTURE",
            "production": [{"period": "2026-01", "value": "999"}],
        }
        assert self._decide(synthetic_result) == "synthetic"
