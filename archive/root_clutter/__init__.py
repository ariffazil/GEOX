"""
GEOX — Earth Intelligence Core
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given
Version: v2026.04.10-EIC (Earth Intelligence Core)

Simplified, focused, essential.

The 7 Tools:
1. geox_compute_ac_risk — ToAC calculation (THE CORE)
2. geox_load_seismic_line — Seismic with F4 Clarity
3. geox_build_structural_candidates — Multi-model interpretation
4. geox_verify_geospatial — Coordinate grounding
5. geox_feasibility_check — Constitutional firewall
6. geox_evaluate_prospect — Prospect verdict with 888_HOLD
7. geox_earth_signals — Live Earth observations

Constitutional Floors: F1, F2, F4, F7, F9, F11, F13
"""

__version__ = "v2026.04.10-EIC"
__seal__ = "DITEMPA BUKAN DIBERI"

from pathlib import Path

_NESTED_PACKAGE = Path(__file__).with_name("geox")
if _NESTED_PACKAGE.is_dir() and str(_NESTED_PACKAGE) not in __path__:
    __path__.insert(0, str(_NESTED_PACKAGE))

from geox.core.ac_risk import (
    compute_ac_risk,
    compute_ac_risk_governed,
    AC_RiskResult,
    GovernedACRiskResult,
    ClaimTag,
    TEARFRAME,
    AntiHantuScreen,
)
from geox.core.basin_charge import BasinChargeSimulator
from geox.core.petro_ensemble import PetroEnsemble
from geox.core.sensitivity import SensitivitySweep
from geox.core.volumetrics import ProbabilisticVolumetrics
from geox.core.tool_registry import ToolRegistry, ToolStatus, ErrorCode
from geox.services.asset_memory import AssetMemoryStore
from geox.services.las_ingestor import LASIngestor

__all__ = [
    "__version__",
    "__seal__",
    "compute_ac_risk",
    "compute_ac_risk_governed",
    "AC_RiskResult",
    "GovernedACRiskResult",
    "ClaimTag",
    "TEARFRAME",
    "AntiHantuScreen",
    "PetroEnsemble",
    "LASIngestor",
    "ProbabilisticVolumetrics",
    "BasinChargeSimulator",
    "AssetMemoryStore",
    "SensitivitySweep",
    "ToolRegistry",
    "ToolStatus",
    "ErrorCode",
]
