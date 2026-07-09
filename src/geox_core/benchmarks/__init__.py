"""GEOX benchmarks — proof wedges that decide whether models deserve to live.

GEOX-001: Well-Seismic Truth Test ("Model Deserves To Live")
"""

from geox_core.benchmarks.geox_001_well_seismic_truth import (
    SCENARIO_GOOD,
    SCENARIO_HOLD,
    SCENARIO_KILL,
    run_geox_001,
    run_geox_001_real_las,
)

__all__ = [
    "run_geox_001",
    "run_geox_001_real_las",
    "SCENARIO_GOOD",
    "SCENARIO_HOLD",
    "SCENARIO_KILL",
]
