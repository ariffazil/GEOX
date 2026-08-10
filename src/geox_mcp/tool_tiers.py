"""Tool tier classification — by what the call TOUCHES, not by organ name."""

TOOL_TIERS = {
    # Anon: pure functions, caller-supplied inputs only
    "anon": {
        "geox_temporal", "geox_source", "geox_seismic_compute",
        "geox_geomechanics", "geox_basin", "geox_deep_time",
        "geox_map", "geox_spatial", "geox_model", "geox_prospect",
    },
    # Session: server-held artifacts, workspace state
    "session": {
        "geox_workspace", "geox_well", "geox_well_qc",
        "geox_petrophysics",  # stateless modes are anon, but tool is session
        "geox_seismic_interpret",  # reads existing interpretations
    },
    # Verified: ingest, mutations, seal, vault writes
    "verified": {
        "geox_well_ingest",  # write mode
        "geox_claim",  # seal mode
        "geox_seismic_ingest",  # write mode
    },
}


def get_tool_tier(tool_name: str) -> str:
    """Returns 'anon', 'session', or 'verified' for a given tool."""
    if tool_name in TOOL_TIERS["verified"]:
        return "verified"
    if tool_name in TOOL_TIERS["session"]:
        return "session"
    return "anon"  # default to anon for unknown tools
