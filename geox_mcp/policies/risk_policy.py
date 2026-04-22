# GEOX MCP Server Policies
# Phase-gated access control for GEOX skills

from enum import Enum
from typing import Set


class DeploymentPhase(Enum):
    PHASE_1_STATIC_SITE = 1
    PHASE_2_MCP_RESOURCES = 2
    PHASE_3_MCP_PROMPTS = 3
    PHASE_4_MCP_TOOLS_TRANSFORMS = 4
    PHASE_5_MCP_TOOLS_OPERATIONAL_888HOLD = 5
    PHASE_6_MULTI_AGENT_LOOPS = 6


class RiskPolicy:
    LOW_RISK_TOOLS = {"low"}
    MEDIUM_RISK_TOOLS = {"low", "medium"}
    HIGH_RISK_TOOLS = {"low", "medium", "high"}
    CRITICAL_RISK_TOOLS = {"low", "medium", "high", "critical"}

    @staticmethod
    def requires_human_confirmation(risk_class: str) -> bool:
        return risk_class in {"high", "critical"}

    @staticmethod
    def get_allowed_tools(phase: DeploymentPhase, risk_class: str) -> Set[str]:
        if phase.value <= 1:
            return set()
        elif phase.value == 2:
            return set()
        elif phase.value == 3:
            return RiskPolicy.LOW_RISK_TOOLS
        elif phase.value == 4:
            return RiskPolicy.MEDIUM_RISK_TOOLS
        elif phase.value == 5:
            return RiskPolicy.HIGH_RISK_TOOLS
        else:
            return RiskPolicy.CRITICAL_RISK_TOOLS


PHASE_1_TOOLS = []
PHASE_2_RESOURCES_ONLY = [
    "list_skills",
    "get_skill_metadata",
    "get_dependencies",
]
PHASE_3_PROMPTS = [
    "geox_mission_template",
    "geox_human_approval_request",
]
PHASE_4_TOOLS_TRANSFORMS = [
    "list_skills",
    "get_skill_metadata",
    "get_dependencies",
    "check_888_hold",
]
PHASE_5_TOOLS_888HOLD = PHASE_4_TOOLS_TRANSFORMS + []
PHASE_6_MULTI_AGENT = PHASE_5_TOOLS_888HOLD + []


TOOL_ALLOWLIST = {
    DeploymentPhase.PHASE_1_STATIC_SITE: PHASE_1_TOOLS,
    DeploymentPhase.PHASE_2_MCP_RESOURCES: PHASE_2_RESOURCES_ONLY,
    DeploymentPhase.PHASE_3_MCP_PROMPTS: PHASE_3_PROMPTS,
    DeploymentPhase.PHASE_4_MCP_TOOLS_TRANSFORMS: PHASE_4_TOOLS_TRANSFORMS,
    DeploymentPhase.PHASE_5_MCP_TOOLS_OPERATIONAL_888HOLD: PHASE_5_TOOLS_888HOLD,
    DeploymentPhase.PHASE_6_MULTI_AGENT_LOOPS: PHASE_6_MULTI_AGENT,
}


INVOCATION_LOG_SCHEMA = {
    "invocation_id": "string",
    "timestamp": "ISO8601",
    "tool_name": "string",
    "agent_id": "string",
    "input_hash": "SHA256",
    "output_hash": "SHA256",
    "approval_status": "PENDING|CONFIRMED|REJECTED",
    "phase": "1-6",
}


def is_tool_allowed(tool_name: str, current_phase: DeploymentPhase) -> bool:
    allowed = TOOL_ALLOWLIST.get(current_phase, [])
    return tool_name in allowed


def requires_approval(tool_name: str, risk_class: str) -> bool:
    return RiskPolicy.requires_human_confirmation(risk_class)
