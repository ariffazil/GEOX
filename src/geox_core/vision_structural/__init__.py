"""GEOX deterministic structural-vision layer.

An LLM must never read a spatial metric off a picture. This package runs deterministic CV
(scikit-image + numpy, no OpenCV, no torch) and returns **numbers with coverage**, never a
probability and never a verdict (CONTRACT §0, §3).

Axes
----
* **A — Shape** (:mod:`~geox_core.vision_structural.structure_tensor`): structure-tensor dip,
  in-section apparent dip azimuth, curvature, and a *declared-rule* geometry class.
* **B — Differential** (:mod:`~geox_core.vision_structural.isopach`): DTW trace warp, isopach
  thickness, expansion index, and the isopach differential ratio that tests the null.
* **Calibration** (:mod:`~geox_core.vision_structural.calibration`): vertical-exaggeration and
  time-to-depth corrections, plus the calibration-state declaration.

Axes C (orientation) and D (superposition) live in sibling modules owned by other agents and
are deliberately not imported here, so that this package imports cleanly on its own.

Every extractor returns :class:`~geox_core.vision_structural.types.Measurement`, whose
``UNMEASURED`` state means *not tested* — never PASS, never KILL.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from .calibration import (
    MIGRATION_STATES,
    apply_ve_correction,
    declare_calibration_state,
    time_to_depth,
)
from .isopach import (
    DTW_WARP_ONLY_WARNING,
    compute_isopach,
    dtw_align_traces,
    expansion_index,
    isopach_differential,
    trace_thickness_profile,
)
from .structure_tensor import (
    GEOMETRY_RULES,
    RULE_KINKED,
    RULE_LISTRIC,
    RULE_PLANAR,
    compute_dip_field,
    extract_axis_a,
)
from .types import ExtractionStatus, Measurement, measured, unmeasured

__all__ = [
    "DTW_WARP_ONLY_WARNING",
    "ExtractionStatus",
    "GEOMETRY_RULES",
    "MIGRATION_STATES",
    "Measurement",
    "RULE_KINKED",
    "RULE_LISTRIC",
    "RULE_PLANAR",
    "apply_ve_correction",
    "compute_dip_field",
    "compute_isopach",
    "declare_calibration_state",
    "dtw_align_traces",
    "expansion_index",
    "extract_axis_a",
    "isopach_differential",
    "measured",
    "time_to_depth",
    "trace_thickness_profile",
    "unmeasured",
]
