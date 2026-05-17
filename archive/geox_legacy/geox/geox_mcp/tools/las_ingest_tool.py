from geox.skills.subsurface.petro.las_ingest import geox_ingest_las_tool

def geox_ingest_las(path: str, asset_id: str | None = None, chunk_size: int = 200) -> dict:
    try:
        return geox_ingest_las_tool(path=path, asset_id=asset_id, chunk_size=chunk_size)
    except Exception as exc:
        return {"error": str(exc), "hold_enforced": True, "claim_tag": "UNKNOWN"}

__all__ = ["geox_ingest_las_tool", "geox_ingest_las"]
