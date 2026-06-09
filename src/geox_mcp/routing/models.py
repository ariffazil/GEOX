from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RouteMode(StrEnum):
    EXPLOIT = "exploit"
    EXPLORE = "explore"
    HYBRID = "hybrid"


class DomainHint(StrEnum):
    GEOLOGY = "geology"
    FINANCE = "finance"
    HSE = "hse"
    GENERAL = "general"


class TaskType(StrEnum):
    LOOKUP = "lookup"
    ANALYSIS = "analysis"
    DECISION = "decision"


class RiskContext(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PolicyFlags(BaseModel):
    explore_required: bool
    disconfirmation_required: bool
    conservative_language_required: bool
    citation_required: bool
    hold_if_low_confidence: bool


class RetrievalBudget(BaseModel):
    exploit_ratio: float = Field(ge=0.0, le=1.0)
    explore_ratio: float = Field(ge=0.0, le=1.0)
    min_explore_docs: int = Field(ge=0)
    min_contradicting_docs: int = Field(ge=0)

    @field_validator("explore_ratio")
    @classmethod
    def ratios_sum_to_one(cls, explore_ratio: float, info: Any) -> float:
        exploit_ratio = info.data.get("exploit_ratio")
        if exploit_ratio is not None and round(exploit_ratio + explore_ratio, 6) != 1.0:
            raise ValueError("exploit_ratio + explore_ratio must equal 1.0")
        return explore_ratio


class RouteQueryInput(BaseModel):
    query: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    user_groups: list[str] = Field(default_factory=list)
    domain_hint: DomainHint = DomainHint.GENERAL
    current_hypothesis: str | None = None
    task_type: TaskType | None = None
    risk_context: RiskContext | None = None
    request_id: str = Field(min_length=1)


class RouteQueryResult(BaseModel):
    mode: RouteMode
    domain: DomainHint
    risk_level: RiskContext
    policy_flags: PolicyFlags
    retrieval_budget: RetrievalBudget
    allowed_tools: list[str]
    reason_code: str
    reason_text: str
    route_version: str
    status: str = "COMPLETE"
    failure_class: str | None = None
    safe_next_action: str | None = None
    entitlement_scope: list[str] = Field(default_factory=list)


class RouteQueryAuditRecord(BaseModel):
    timestamp: str
    request_id: str
    user_id_hash: str
    router_mode: RouteMode
    domain: DomainHint
    risk_level: RiskContext
    policy_flags: PolicyFlags
    allowed_tools: list[str]
    selected_tools: list[str] = Field(default_factory=list)
    reason_code: str
    exploit_docs_used: int = 0
    explore_docs_used: int = 0
    contradicting_docs_used: int = 0
    status: str
    route_version: str
    failure_class: str | None = None
