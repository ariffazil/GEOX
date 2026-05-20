"""
GEOX Test Conftest
DITEMPA BUKAN DIBERI

Shared fixtures for the GEOX test suite:
  - geo_request   — standard GeoRequest pointing at Blok Selatan, Malay Basin
  - mock_agent    — GeoXAgent with MockEarthNetTool + MockSeismicVLMTool,
                    in-memory GeoMemoryStore, no external APIs
"""

from __future__ import annotations

import os
# Bypass the root-owned .env file so FastMCP settings load without PermissionError in CI.
os.environ.setdefault("FASTMCP_ENV_FILE", "")

import sys
from pathlib import Path

import pytest
import pytest_asyncio

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# New spine compatibility
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Legacy test compatibility: arifos/ and geox/ are archived
ARCHIVE_ROOT = REPO_ROOT / "archive"
if str(ARCHIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_ROOT))

# Handle arifos legacy structure
ARIFOS_LEGACY = ARCHIVE_ROOT / "arifos"
if str(ARIFOS_LEGACY) not in sys.path and ARIFOS_LEGACY.exists():
    sys.path.insert(0, str(ARIFOS_LEGACY))

# Handle geox legacy structure
GEOX_LEGACY = ARCHIVE_ROOT / "geox_legacy"
if str(GEOX_LEGACY) not in sys.path and GEOX_LEGACY.exists():
    sys.path.append(str(GEOX_LEGACY))

# Strip arifOS paths that shadow GEOX packages with empty namespace dirs
sys.path = [p for p in sys.path if "arifOS" not in p]

# ---------------------------------------------------------------------------
# Legacy test exclusion — these test files import archived module paths
# that no longer exist in the live src/ spine. They are preserved for
# historical reference but excluded from the default test run.
# ---------------------------------------------------------------------------
collect_ignore = [
    "test_asset_memory_wave2.py",
    "test_basin_charge_wave2.py",
    "test_canonical_public_surface.py",
    "test_claim_laundering_guard.py",
    "test_depth_basis_footer_contract.py",
    "test_ensemble_residual_contracts.py",
    "test_fail_closed_auth.py",
    "test_geox_truth_state_golden.py",
    "test_gr_cognitive.py",
    "test_las_ingestor_wave2.py",
    "test_legacy_alias_resolution.py",
    "test_manifest_llms_parity.py",
    "test_mcp_runtime_regressions.py",
    "test_metabolic_contract.py",
    "test_missing_curve_warning_contract.py",
    "test_npd_eia_structured_errors.py",
    "test_petro_ensemble_wave2.py",
    "test_petrophysics_wave1_hardening.py",
    "test_physics_guard.py",
    "test_plot_spec_validation.py",
    "test_sensitivity_wave2.py",
    "test_visualization_wave2.py",
    "test_volumetrics_wave2.py",
    "test_well_desk_physics.py",
    "test_well_mcp_hardening.py",
    "test_welltie.py",
    "test_wave2_capabilities.py",
    "unit/test_registry_status.py",
    # Additional legacy tests that import arifos.geox.* (A-FORGE co-located code)
    "physics/test_porosity_solvers.py",
    "physics/test_saturation_models.py",
    "test_attributes.py",
    "test_cigvis_adapter.py",
    "test_cigvis_adapter_runtime.py",
    "test_contrast_canon.py",
    "test_contrast_metadata.py",
    "test_core_tools.py",
    "test_earth_realtime_tool.py",
    "test_end_to_end_mock.py",
    "test_hardened_agent.py",
    "test_memory_and_public_surfaces.py",
    "test_schemas.py",
    "test_seismic_visual_filter.py",
    "test_single_line_interpreter.py",
    "test_validator.py",
    "unit/test_petrophysics.py",
]

# ---------------------------------------------------------------------------
# Import current canonical modules; fall back to legacy A-FORGE if available.
# All legacy imports are wrapped so conftest loads even when A-FORGE is
# unreachable or has broken case-sensitive imports.
# ---------------------------------------------------------------------------
GeoXAgent = GeoXConfig = GeoXValidator = GeoMemoryStore = ToolRegistry = None
MockEarthNetTool = MockSeismicVLMTool = None
CoordinatePoint = GeoRequest = None
ACRisk = None

try:
    from geox_core.schemas.well import CoordinatePoint, GeoRequest
    from geox_core.core.ac_risk import ACRisk
except ImportError:
    pass

try:
    from arifos.geox.geox_agent import GeoXAgent, GeoXConfig
    from arifos.geox.geox_validator import GeoXValidator
    from arifos.geox.geox_memory import GeoMemoryStore
    from arifos.geox.geox_tools import ToolRegistry
    from arifos.geox.examples.mock_tools.mock_earthnet import MockEarthNetTool
    from arifos.geox.examples.mock_tools.mock_vlm import MockSeismicVLMTool
except ImportError:
    pass


# ---------------------------------------------------------------------------
# geo_request — standard Blok Selatan fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def geo_request():
    """
    A standard GeoRequest for the fictional 'Blok Selatan' prospect
    in the Malay Basin at lat=4.5, lon=104.2.
    """
    if GeoRequest is None or CoordinatePoint is None:
        pytest.skip("Legacy GeoRequest / CoordinatePoint not available")
    return GeoRequest(
        query=(
            "Evaluate hydrocarbon potential of Blok Selatan anticline "
            "in the Malay Basin. Assess reservoir quality, structural closure, "
            "and seal integrity."
        ),
        prospect_name="Blok Selatan",
        location=CoordinatePoint(latitude=4.5, longitude=104.2, depth_m=2500.0),
        basin="Malay Basin",
        play_type="structural",
        available_data=["seismic_3d", "well_logs"],
        risk_tolerance="medium",
        requester_id="USER-geo-test-001",
    )


# ---------------------------------------------------------------------------
# mock_agent — GeoXAgent with mock tools only
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_agent():
    """
    GeoXAgent wired with:
      - MockEarthNetTool   (registered as 'EarthModelTool')
      - MockSeismicVLMTool (registered as 'SeismicVLMTool')
      - GeoXValidator
      - In-memory GeoMemoryStore
      - No LLM planner (falls back to heuristic plan)
      - No audit sink
    """
    if any(cls is None for cls in (GeoXAgent, GeoXConfig, ToolRegistry, GeoXValidator,
                                   GeoMemoryStore, MockEarthNetTool, MockSeismicVLMTool)):
        pytest.skip("Legacy mock_agent fixtures not available (arifos.geox unreachable)")

    # Build registry with mock tools registered under production tool names
    registry = ToolRegistry()
    registry.register(_EarthModelToolProxy())
    registry.register(_SeismicVLMToolProxy())

    validator = GeoXValidator()
    memory = GeoMemoryStore()  # in-memory backend

    config = GeoXConfig(
        lem_confidence_threshold=0.70,
        max_tool_retries=1,
        allowed_tools=["EarthModelTool", "SeismicVLMTool"],
        provenance_required=True,
        pipeline_id="geox-test-v0.1",
    )

    return GeoXAgent(
        config=config,
        tool_registry=registry,
        validator=validator,
        llm_planner=None,
        audit_sink=None,
        memory_store=memory,
    )


# ---------------------------------------------------------------------------
# Internal proxy classes — register mock tools under production names
# ---------------------------------------------------------------------------

class _EarthModelToolProxy(MockEarthNetTool if MockEarthNetTool else object):
    """MockEarthNetTool registered under the production name 'EarthModelTool'."""

    @property
    def name(self) -> str:
        return "EarthModelTool"


class _SeismicVLMToolProxy(MockSeismicVLMTool if MockSeismicVLMTool else object):
    """MockSeismicVLMTool registered under the production name 'SeismicVLMTool'."""

    @property
    def name(self) -> str:
        return "SeismicVLMTool"
