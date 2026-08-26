from __future__ import annotations

from dataclasses import dataclass, field

from geox_mcp.surface_manifest import manifest_tools, public_tools


@dataclass(frozen=True)
class CanonicalTool:
    mcp_tool_name: str
    domain_verb: str
    domain: str
    description: str
    use_when: str
    internal_backing: list[str] = field(default_factory=list)
    acrisk: str = "QUALIFY"
    is_888_hold: bool = False
    modes: list[str] | None = None


def _domain_verb(tool_name: str, domain: str) -> str:
    tail = tool_name.removeprefix("geox_")
    domain_tail = domain.split(".", 1)[-1].replace(".", "_")
    return f"{domain_tail}.{tail}"


def _acrisk(tool_name: str, lane: str) -> str:
    if tool_name in {"geox_subsurface_model"}:
        return "HOLD"
    if lane == "judgment":
        return "ADVISORY"
    return "QUALIFY"


CANONICAL_TOOLS: dict[str, CanonicalTool] = {
    tool.name: CanonicalTool(
        mcp_tool_name=tool.name,
        domain_verb=_domain_verb(tool.name, tool.domain),
        domain=tool.domain,
        description=tool.description or f"{tool.name} — GEOX canonical surface tool.",
        # Zen §6: one trigger phrase, not two. If the upstream description already
        # embeds a "Use when" phrase, suppress the synthesized fallback to avoid
        # the duplicated "Use when: Use when you need ..." pattern that surfaced
        # in tools/list for 10 tools during the 2026-08-26 zen audit.
        use_when=(
            ""
            if (tool.description or "").lstrip().lower().startswith("use when")
            else f"Use when you need {tool.name.replace('geox_', '').replace('_', ' ')} evidence."
        ),
        acrisk=_acrisk(tool.name, tool.lane),
        is_888_hold=tool.lane == "judgment",
    )
    for tool in public_tools()
}

DOMAIN_VERB_TOOLS: dict[str, str] = {canonical.domain_verb: canonical.mcp_tool_name for canonical in CANONICAL_TOOLS.values()}


def get_canonical_tool(name: str) -> CanonicalTool | None:
    return CANONICAL_TOOLS.get(name)


MANIFEST_TOOL_COUNT = len(tuple(manifest_tools()))
