# GEOX App Manifest Schema — The Sovereign Entry Point

from pydantic import BaseModel, Field

class UIEntry(BaseModel):
    """Entry point configuration for the App UI."""
    resource_uri: str = Field(..., description="The canonical URI for the app bundle.")
    version: str = Field(..., description="Semantic version of the UI bundle.")
    mode: str = Field("inline-or-external", description="Preferred rendering mode: inline, external, or both.")
    csp_allow_list: list[str] = Field(default_factory=list, description="CSP origins required by the app.")

class AppManifest(BaseModel):
    """
    Canonical GEOX App Manifest.
    Defines the identity, capabilities, and transport for a microfrontend.
    """
    app_id: str = Field(..., description="Unique identifier: geox.[domain].[name]")
    version: str = Field(..., description="Version of the application.")
    domain: str = Field(..., description="Geoscientific domain: seismic, wells, maps, etc.")
    title: str = Field(..., description="Human-readable title.")
    description: str = Field(..., description="Deep description of the app's purpose.")

    ui_entry: UIEntry = Field(..., description="UI entry point configuration.")

    tools_required: list[str] = Field(
        default_factory=list,
        description="List of MCP tool names this app needs to function."
    )

    events_published: list[str] = Field(
        default_factory=list,
        description="Event names this app emits (e.g., ui.action)."
    )

    events_subscribed: list[str] = Field(
        default_factory=list,
        description="Event names this app listens for (e.g., app.context.patch)."
    )

    metadata: dict[str, any] = Field(
        default_factory=dict,
        description="Extended metadata for host-specific hints (OpenAI, Copilot)."
    )

    class Config:
        schema_extra = {
            "example": {
                "app_id": "geox.seismic.viewer",
                "version": "1.0.0",
                "domain": "seismic",
                "title": "Seismic Section Viewer",
                "ui_entry": {
                    "resource_uri": "https://geox.apps/seismic-viewer",
                    "version": "1.2.0"
                },
                "tools_required": ["geox_load_seismic_line", "geox_build_structural_candidates"]
            }
        }
