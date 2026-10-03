"""EarthBench pytest surface — run with the repo's normal pytest invocation."""

from __future__ import annotations

import pytest

from tests.earth_bench.earthbench import CASES, run_case


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_earthbench_case(case):
    result = run_case(case)
    failed = [c for c in result["checks"] if not c["ok"]]
    assert result["ok"], f"{case['id']} failed: {failed}"
