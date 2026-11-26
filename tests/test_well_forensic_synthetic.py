"""Phase D synthetic corrupted-LAS forensic tests (100% synthetic public data, zero corporate IDs)."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from geox.forensics.well_pda import geox_well_pda
from geox_mcp.apps_well_forensic import APP_HTML_PATH, APP_MIME, APP_URI


def _make_clean_synthetic() -> dict:
    depths = [1000.0 + i * 1.0 for i in range(60)]
    gr = [45.0 + 30.0 * math.sin(i / 6.0) for i in range(60)]
    return {
        "depth_m": depths,
        "run_a": gr,
        "run_b": list(gr),  # 0.0 m shift
        "curves": {
            "GR": gr,
            "NPHI": [0.22] * 60,
            "VPVS": [1.85] * 60,
            "DTC": [85.0] * 60,
        },
        "matrix": {
            "rhob": [2.42] * 60,
            "nphi": [0.22] * 60,
            "nmr": [0.20] * 60,  # excess OH = 0.02 (clean)
            "vpvs": [1.85] * 60,
        },
        "biostrat_picks": [
            {"depth_m": 1200.0, "zone": "NN11", "age_ma": 7.5, "sample_type": "swc", "event_type": "top"},
            {"depth_m": 1800.0, "zone": "NN7", "age_ma": 11.9, "sample_type": "swc", "event_type": "top"},
        ],
        "checkshot_flag": 1,
    }


def _make_corrupted_synthetic() -> dict:
    depths = [1000.0 + i * 1.0 for i in range(60)]
    # 1. Inject +10 m datum shift between run_a and run_b
    run_a = [40.0 + 40.0 * math.exp(-((i - 20) ** 2) / 12.0) for i in range(60)]
    run_b = [40.0 + 40.0 * math.exp(-((i - 30) ** 2) / 12.0) for i in range(60)]
    # 2. Inject x3.28084 Vp/Vs unit corruption + x100 % porosity + us/m sonic
    # 3. Inject 1e37 sentinel + sparse (<25% valid) curve
    sparse_gr = [-999.25] * 55 + [60.0] * 5
    return {
        "depth_m": depths,
        "run_a": run_a,
        "run_b": run_b,
        "curves": {
            "GR_SPARSE": sparse_gr,
            "HORIZON_TWT": [1e37] * 10 + [2200.0] * 50,
            "VPVS": [1.85 * 3.28084] * 60,
            "NPHI": [24.0] * 60,
            "DTC": [280.0] * 60,
        },
        # 4. Inject matrix paradox: excess OH (+0.22 v/v) + low RHOB (1.98 g/cm3)
        "matrix": {
            "rhob": [1.98] * 60,
            "nphi": [0.42] * 60,
            "nmr": [0.20] * 60,
            "vpvs": [2.04] * 60,
        },
        # 5. Inject age inversion + cuttings base + checkshot_flag=0
        "biostrat_picks": [
            {"depth_m": 1200.0, "zone": "NN5", "age_ma": 14.0, "sample_type": "cuttings", "event_type": "base"},
            {"depth_m": 1500.0, "zone": "NN9", "age_ma": 10.6, "sample_type": "cuttings", "event_type": "top"},
        ],
        "checkshot_flag": 0,
    }


def test_empty_args_returns_default_dashboard_under_400_tokens() -> None:
    res = geox_well_pda()
    assert res["verdict"] == "READY"
    assert res["structuredContent"]["artifact_uri"] == APP_URI
    assert (len(json.dumps(res)) // 4) < 400


def test_clean_synthetic_las_has_zero_false_positives() -> None:
    res = geox_well_pda(mode="all", payload=_make_clean_synthetic())
    assert res["verdict"] == "PASS"
    assert res["structuredContent"]["data"]["defects"] == []


def test_corrupted_synthetic_las_catches_all_five_injected_faults() -> None:
    res = geox_well_pda(mode="all", payload=_make_corrupted_synthetic())
    assert res["verdict"] == "DEFECTS_FOUND"
    defects = set(res["structuredContent"]["data"]["defects"])
    expected = {"datum_shift", "unit_trap", "sentinel", "matrix_paradox", "age_inversion"}
    assert defects == expected, f"Missed defects: {expected - defects}"
    hyps = res["structuredContent"]["data"]["checks"]["matrix_paradox"]["hypotheses"]
    assert len(hyps) >= 3
    assert all("falsifier" in h for h in hyps)


def test_sep1865_mcp_app_html_is_csp_safe_and_offline() -> None:
    assert APP_MIME == "text/html;profile=mcp-app"
    html = Path(APP_HTML_PATH).read_text(encoding="utf-8")
    assert "default-src 'none'" in html
    assert not re.search(r"https?://", html), "External CDN/URL found in offline SEP-1865 MCP App!"
