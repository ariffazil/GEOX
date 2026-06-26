import pytest

from geox_mcp.tools.paleoscan_forge import geox_coord_transform_tool


@pytest.mark.asyncio
async def test_coord_transform_accepts_epsg_reprojection_shape():
    result = await geox_coord_transform_tool(
        x=500000,
        y=350000,
        from_crs="EPSG:32647",
        to_crs="EPSG:4326",
    )

    assert result["execution_status"] == "SUCCESS"
    artifact = result["primary_artifact"]
    assert artifact["mode"] == "crs_reprojection"
    assert artifact["from_crs"] == "EPSG:32647"
    assert artifact["to_crs"] == "EPSG:4326"

    lon, lat = artifact["transformed_points"][0]
    assert lon == pytest.approx(99.0, abs=1e-9)
    assert lat == pytest.approx(3.1665274397, rel=1e-9)


@pytest.mark.asyncio
async def test_coord_transform_names_local_affine_mode():
    result = await geox_coord_transform_tool(
        points=[[0, 0, 0]],
        from_space="block",
        to_space="survey",
    )

    assert result["execution_status"] == "SUCCESS"
    assert result["primary_artifact"]["mode"] == "local_affine_space_transform"


@pytest.mark.asyncio
async def test_coord_transform_missing_mode_returns_structured_hold():
    result = await geox_coord_transform_tool()

    assert result["execution_status"] == "ERROR"
    assert result["governance_status"] == "HOLD"
    assert result["primary_artifact"]["mode"] == "local_affine_space_transform"
    assert "crs_mode_hint" in result["primary_artifact"]
