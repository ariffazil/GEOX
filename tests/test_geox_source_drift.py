"""geox_source_drift certifies GEOX. It does not reuse the arifOS field."""

from __future__ import annotations

from pathlib import Path

from geox_mcp.source_drift import probe_geox_source_drift

_SERVER = Path(__file__).resolve().parents[1] / "src" / "geox_mcp" / "server.py"


def test_health_field_names_are_organ_scoped() -> None:
    text = _SERVER.read_text(encoding="utf-8")
    assert '"arifos_deployment_drift"' in text
    assert '"geox_source_drift"' in text
    assert '"deployment_drift"' not in text


def test_probe_reports_drift_from_the_runner() -> None:
    calls: list[list[str]] = []

    def runner(args: list[str]) -> tuple[int, str]:
        calls.append(args)
        if args[-2:] == ["rev-parse", "HEAD"]:
            return 0, "a" * 40
        if args[-2:] == ["get-url", "origin"]:
            return 0, "https://github.com/ariffazil/GEOX.git"
        if args[:2] == ["git", "ls-remote"]:
            return 0, "b" * 40 + "\trefs/heads/main"
        return 1, ""

    out = probe_geox_source_drift(runner=runner, ttl_s=0)
    assert out["drift"] is True
    assert out["status"] == "drift"
    assert out["compared_via"] == "git ls-remote"
    assert out["local_head"] == "a" * 40
    assert out["origin_main"] == "b" * 40
    assert "source_commit" not in out
    assert any(c[:2] == ["git", "ls-remote"] for c in calls)


def test_probe_falls_back_to_the_tracking_ref_and_says_so() -> None:
    def runner(args: list[str]) -> tuple[int, str]:
        if args[-2:] == ["rev-parse", "HEAD"]:
            return 0, "c" * 40
        if args[-2:] == ["get-url", "origin"]:
            return 1, ""
        if args[-2:] == ["rev-parse", "origin/main"]:
            return 0, "c" * 40
        return 1, ""

    out = probe_geox_source_drift(runner=runner, ttl_s=0)
    assert out["drift"] is False
    assert out["status"] == "aligned"
    assert out["compared_via"] == "origin/main tracking ref"


def test_live_opt_geox_probe_has_a_head() -> None:
    if not Path("/opt/geox/.git").exists():
        return
    out = probe_geox_source_drift(ttl_s=0)
    assert out["repo"] == "/opt/geox"
    assert out["local_head"] not in ("", "unknown")
    assert len(out["local_head"]) == 40
    assert out["drift"] in (True, False, None)
