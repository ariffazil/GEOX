"""generate_pytest_receipt.py — Machine-generated pytest audit receipt for GEOX.

Phase 888: Generates machine-verifiable pytest-receipt.json with full commit SHA,
environment metadata, exact counts, verbatim summary, and gate-categorized failure nodeids.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def get_git_commit_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception as e:
        return f"UNKNOWN ({e})"


def categorize_nodeid(nodeid: str, error_msg: str = "") -> str:
    """Categorize failure/error nodeid into GATE A, GATE B, or GATE C."""
    node_lower = nodeid.lower()
    err_lower = error_msg.lower()

    if "browser" in node_lower or "playwright" in err_lower or "e2e_mcp_apps" in node_lower:
        return "GATE_B_UI_BROWSER"

    if (
        "wealth_bridge" in node_lower
        or "gplates" in node_lower
        or "macrostrat" in node_lower
        or "live" in node_lower
        or "socket" in err_lower
        or "connection" in err_lower
    ):
        return "GATE_C_FEDERATION_EXTERNAL"

    if "charmap" in err_lower or "unicode" in err_lower or "cp1252" in err_lower:
        return "GATE_A_CORE_ENCODING"

    if "expected_count" in err_lower or "public_32" in err_lower or "truth_32" in err_lower:
        return "GATE_A_CORE_COUNT_ASSERTION"

    return "GATE_A_CORE_PHYSICS"


def run_and_generate_receipt(args: list[str] | None = None) -> dict:
    commit_sha = get_git_commit_sha()
    start_time = time.time()

    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"]
    if args:
        cmd.extend(args)

    raw_output_lines = []
    print(f"Running command: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if proc.stdout is not None:
        for line in proc.stdout:
            raw_output_lines.append(line)

    proc.wait()
    duration = time.time() - start_time
    full_output = "".join(raw_output_lines)

    # Parse short summary line
    summary_line = ""
    for line in reversed(raw_output_lines):
        if "passed" in line or "failed" in line or "error" in line:
            summary_line = line.strip()
            break

    # Parse counts via regex
    def _parse_count(pattern: str, text: str) -> int:
        m = re.search(pattern, text)
        return int(m.group(1)) if m else 0

    failed_count = _parse_count(r"(\d+)\s+failed", full_output)
    passed_count = _parse_count(r"(\d+)\s+passed", full_output)
    skipped_count = _parse_count(r"(\d+)\s+skipped", full_output)
    errors_count = _parse_count(r"(\d+)\s+error", full_output)
    deselected_count = _parse_count(r"(\d+)\s+deselected", full_output)
    collected_count = _parse_count(r"collected\s+(\d+)\s+items", full_output)

    # Parse FAILED / ERROR nodeids
    failures = []
    current_nodeid = None
    current_err = []

    for line in raw_output_lines:
        if line.startswith("FAILED ") or line.startswith("ERROR "):
            if current_nodeid:
                err_str = "\n".join(current_err)
                cat = categorize_nodeid(current_nodeid, err_str)
                failures.append(
                    {
                        "nodeid": current_nodeid,
                        "category": cat,
                        "root_cause_snippet": current_err[0] if current_err else "",
                        "environmental": cat in ("GATE_B_UI_BROWSER", "GATE_C_FEDERATION_EXTERNAL"),
                    }
                )
            current_nodeid = line.split()[1] if len(line.split()) > 1 else line.strip()
            current_err = []
        elif current_nodeid and (line.startswith("E ") or line.startswith("  ")):
            current_err.append(line.strip())

    if current_nodeid:
        err_str = "\n".join(current_err)
        cat = categorize_nodeid(current_nodeid, err_str)
        failures.append(
            {
                "nodeid": current_nodeid,
                "category": cat,
                "root_cause_snippet": current_err[0] if current_err else "",
                "environmental": cat in ("GATE_B_UI_BROWSER", "GATE_C_FEDERATION_EXTERNAL"),
            }
        )

    receipt = {
        "spec_version": "1.0",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "commit": commit_sha,
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "cwd": str(ROOT_DIR),
        },
        "pytest_counts": {
            "collected": collected_count,
            "passed": passed_count,
            "failed": failed_count,
            "errors": errors_count,
            "skipped": skipped_count,
            "deselected": deselected_count,
            "total_outcomes": passed_count + failed_count + errors_count + skipped_count,
        },
        "verbatim_summary_line": summary_line,
        "duration_seconds": round(duration, 2),
        "gate_breakdown": {
            "gate_a_core_physics_failures": len([f for f in failures if f["category"] == "GATE_A_CORE_PHYSICS"]),
            "gate_a_encoding_failures": len([f for f in failures if f["category"] == "GATE_A_CORE_ENCODING"]),
            "gate_a_count_assertion_failures": len([f for f in failures if f["category"] == "GATE_A_CORE_COUNT_ASSERTION"]),
            "gate_b_ui_browser_failures": len([f for f in failures if f["category"] == "GATE_B_UI_BROWSER"]),
            "gate_c_federation_external_failures": len([f for f in failures if f["category"] == "GATE_C_FEDERATION_EXTERNAL"]),
        },
        "failures": failures,
    }

    out_path = ROOT_DIR / "pytest-receipt.json"
    out_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Machine receipt written to {out_path}")
    return receipt


if __name__ == "__main__":
    extra = sys.argv[1:] if len(sys.argv) > 1 else []
    run_and_generate_receipt(extra)
