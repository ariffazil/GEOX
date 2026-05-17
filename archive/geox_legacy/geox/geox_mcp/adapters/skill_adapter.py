"""
GEOX MCP Adapters
Bridge between GEOX skills and MCP protocol surface
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class SkillAdapter:
    """Adapter for converting GEOX skill markdown to MCP resources."""

    FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

    @staticmethod
    def parse_frontmatter(content: str) -> Dict[str, Any]:
        match = SkillAdapter.FRONTMATTER_RE.search(content)
        if not match:
            return {}
        fm = {}
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm[key.strip()] = value.strip()
        return fm

    @staticmethod
    def skill_to_resource(skill_path: Path) -> Dict[str, Any]:
        with open(skill_path) as f:
            content = f.read()
        fm = SkillAdapter.parse_frontmatter(content)
        return {
            "uri": f"geox://skills/{skill_path.stem}",
            "name": fm.get("title", skill_path.stem),
            "description": content[:500],
            "mimeType": "text/markdown",
            "metadata": fm,
        }


class RegistryAdapter:
    """Adapter for GEOX registry operations."""

    @staticmethod
    def get_skills_by_domain(registry: Dict, domain: str) -> List[Dict]:
        return [s for s in registry.get("skills", []) if s.get("domain") == domain]

    @staticmethod
    def get_skills_by_substrate(registry: Dict, substrate: str) -> List[Dict]:
        return [
            s
            for s in registry.get("skills", [])
            if substrate in s.get("substrates", [])
        ]

    @staticmethod
    def get_dependencies(registry: Dict, skill_id: str) -> List[Dict]:
        for skill in registry.get("skills", []):
            if skill.get("id") == skill_id:
                dep_ids = skill.get("depends_on", [])
                return [s for s in registry.get("skills", []) if s.get("id") in dep_ids]
        return []


class PromptAdapter:
    """Adapter for converting GEOX skills to MCP prompts."""

    @staticmethod
    def skill_to_prompt(
        skill_id: str, skill_title: str, inputs: List[str], outputs: List[str]
    ) -> str:
        return f"""GEOX Skill: {skill_title} ({skill_id})

Purpose: Execute {skill_title} skill for earth intelligence operations.

Inputs Required: {", ".join(inputs)}
Outputs Expected: {", ".join(outputs)}

Follow the 888 HOLD protocol for high-risk actions.
Maintain audit trail for all invocations.
"""


class ToolAnnotationAdapter:
    """Adapter for MCP tool annotations (2026 spec safety guardrails)."""

    @staticmethod
    def annotate_tool(skill_metadata: Dict) -> Dict[str, Any]:
        risk_class = skill_metadata.get("risk_class", "low")
        human_conf = skill_metadata.get("human_confirmation", False)

        annotations = {
            "readOnlyHint": risk_class == "low" and not human_conf,
            "destructiveHint": risk_class in ["high", "critical"],
            "humanConfirmationIf": "888_HOLD" if human_conf else None,
            "allowedDomains": [skill_metadata.get("legal_domain", "public")],
        }
        return {k: v for k, v in annotations.items() if v is not None}
