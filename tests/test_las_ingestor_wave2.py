from pathlib import Path

from geox.services.las_ingestor import LASIngestor
from geox.geox_mcp.server import geox_well_load_bundle


LAS_SAMPLE = """~Version Information
 VERS.                  2.0 : CWLS LOG ASCII STANDARD - VERSION 2.0
 WRAP.                  NO  : ONE LINE PER DEPTH STEP
~Well Information
 STRT.M              1000.0 :
 STOP.M              1002.0 :
 STEP.M                 0.5 :
 NULL.               -999.25 :
 COMP.                  GEOX :
 WELL.               TEST-1  :
 UWI.                TEST-UWI:
~Curve Information
 DEPT.M : Depth
 GR  .API : Gamma Ray
 RT  .OHMM: Resistivity
 NPHI.V/V: Neutron Porosity
~ASCII
1000.0 45.0 20.0 0.22
1000.5 50.0 18.0 0.24
1001.0 48.0 17.0 0.23
1001.5 47.0 16.0 0.21
1002.0 46.0 15.5 0.20
"""


def test_las_ingestor_parses_manifest(tmp_path: Path):
    las_path = tmp_path / "test.las"
    las_path.write_text(LAS_SAMPLE)
    manifest = LASIngestor().ingest(str(las_path), asset_id="asset-1").to_dict()
    assert manifest["asset_id"] == "asset-1"
    assert manifest["curve_count"] if "curve_count" in manifest else len(manifest["curves"]) >= 3
    assert manifest["depth_range"][0] == 1000.0


def test_existing_bundle_tool_handles_las(tmp_path: Path):
    las_path = tmp_path / "test.las"
    las_path.write_text(LAS_SAMPLE)
    result = geox_well_load_bundle("TEST-1", str(las_path))
    assert result["status"] == "loaded"
    assert "las_manifest" in result
    assert result["curve_manifest"]
