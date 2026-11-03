"""
tests/test_geox_deep_time_ontology_mapping.py
Test Task 3:
1. Parameter mapping: age/ontology terms (e.g. "Middle Miocene") map to interval_name/age fields, NEVER lith=.
2. When Macrostrat is offline/fails: return UNKNOWN with source_status="OFFLINE", no cached/invented units as live.
3. Offshore Borneo coverage: queries report 0 units honestly without inventing units.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests
from geox_mcp.tools.dde_reason import geox_dde_reason


@pytest.mark.asyncio
async def test_geox_deep_time_ontology_term_age_mapping():
    """Chronostratigraphic terms like 'Middle Miocene' must map to interval_name, NOT lith."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": {
                "data": [
                    {
                        "strat_name": "Cycle IV Carbonate",
                        "b_age": 15.0,
                        "t_age": 11.6,
                        "lith": ["limestone", "dolomite"],
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp

        res = await geox_dde_reason(
            mode="query_stratigraphy",
            ontology_term="Middle Miocene",
            lat=4.65,
            lng=112.50,
        )

        assert mock_get.called
        call_params = mock_get.call_args[1].get("params", {})
        assert "lith" not in call_params or call_params.get("lith") != "Middle Miocene", (
            f"Middle Miocene must NOT be sent as lith=, params were: {call_params}"
        )
        assert call_params.get("interval_name") == "Middle Miocene", (
            f"Middle Miocene should be sent as interval_name, params were: {call_params}"
        )


@pytest.mark.asyncio
async def test_geox_deep_time_offline_returns_unknown():
    """When Macrostrat is offline (e.g. 500 error or connection error), return UNKNOWN with source_status=OFFLINE."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("500 Server Error: Macrostrat cluster unreachable")

        res = await geox_dde_reason(
            mode="query_stratigraphy",
            ontology_term="Middle Miocene",
            lat=4.65,
            lng=112.50,
        )

        assert res.get("ok") is False or res.get("epistemic_label") == "UNKNOWN"
        assert res.get("source_status") == "OFFLINE"
        assert res.get("epistemic_label") == "UNKNOWN" or res.get("claim_tag") == "UNKNOWN"
        assert len(res.get("units", [])) == 0, "No cached or invented units should be returned as live when offline"
