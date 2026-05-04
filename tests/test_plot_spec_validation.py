"""
test_plot_spec_validation.py — Artifact Contract Test #1
═══════════════════════════════════════════════════════════════════════

PlotSpec MUST reject executable/code fields and invalid schemas.
DITEMPA BUKAN DIBERI
"""

import pytest
from geox.plot_specs import PlotSpec, from_dict


def test_rejects_exec_in_annotations():
    payload = {
        "renderer": "matplotlib",
        "plot_type": "line",
        "annotations": [{"exec": "import os; os.system('rm -rf /')"}],
    }
    spec = from_dict(payload)
    result = spec.validate()
    assert result["ok"] is False
    assert any("exec" in f for f in result["blocked_fields"])


def test_rejects_eval_in_annotations():
    payload = {
        "renderer": "matplotlib",
        "annotations": [{"eval": "__import__('os').system('id')"}],
    }
    spec = from_dict(payload)
    result = spec.validate()
    assert result["ok"] is False
    assert any("eval" in f for f in result["blocked_fields"])


def test_rejects_code_string():
    payload = {
        "renderer": "matplotlib",
        "annotations": [{"text": "eval(123)"}],
    }
    spec = from_dict(payload)
    result = spec.validate()
    assert result["ok"] is False


def test_rejects_unapproved_renderer():
    spec = PlotSpec(renderer="matplotlib")
    assert spec.validate()["ok"] is True

    spec = PlotSpec(renderer="malicious_renderer")
    result = spec.validate()
    assert result["ok"] is False
    assert "malicious_renderer" in result["error"]


def test_rejects_unapproved_format():
    spec = PlotSpec(output_format="exe")
    result = spec.validate()
    assert result["ok"] is False
    assert "exe" in result["error"]


def test_accepts_approved_depth_basis():
    for basis in ("MD", "TVD", "TVDSS", "KB", "DF", "WS"):
        spec = PlotSpec(depth_basis=basis)
        assert spec.validate()["ok"] is True


def test_rejects_bad_depth_basis():
    spec = PlotSpec(depth_basis="arbitrary")
    result = spec.validate()
    assert result["ok"] is False
