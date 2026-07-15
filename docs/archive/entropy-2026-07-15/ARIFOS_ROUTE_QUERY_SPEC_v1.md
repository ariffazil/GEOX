# arifos_route_query Spec v1

Status: Draft
Date: 2026-06-09
Scope: Tenant-safe deterministic routing for enterprise retrieval

## 1. Purpose

`arifos_route_query` is a mandatory pre-router MCP tool.
It classifies intent and returns a policy-bound retrieval mode before any search tool is called.

Primary objective:
- Prevent planner-only, non-deterministic tool selection.
- Enforce discovery behavior when user intent implies exploration.
- Preserve entitlement boundaries and auditability.

## 2. Invocation Contract

Call order (hard requirement):
1. Agent receives user query.
2. Agent MUST call `arifos_route_query`.
3. Agent MUST follow returned mode and policy flags when selecting retrieval tools.

If router call fails:
- Default to `mode=exploit` for safety.
- Return status `PARTIAL` with explicit note: "routing unavailable".

## 3. Input Schema

```json
{
  "query": "string, required",
  "user_id": "string, required",
  "user_groups": ["string"],
  "domain_hint": "geology|finance|hse|general|optional",
  "current_hypothesis": "string|optional",
  "task_type": "lookup|analysis|decision|optional",
  "risk_context": "low|medium|high|optional",
  "request_id": "string, required"
}
```

## 4. Output Schema

```json
{
  "mode": "exploit|explore|hybrid",
  "domain": "geology|finance|hse|general",
  "risk_level": "low|medium|high",
  "policy_flags": {
    "explore_required": true,
    "disconfirmation_required": true,
    "conservative_language_required": false,
    "citation_required": true,
    "hold_if_low_confidence": false
  },
  "retrieval_budget": {
    "exploit_ratio": 0.7,
    "explore_ratio": 0.3,
    "min_explore_docs": 3,
    "min_contradicting_docs": 1
  },
  "allowed_tools": [
    "enterprise_graph_search",
    "geox_contrast_search",
    "geox_disconfirm_evidence_scan"
  ],
  "reason_code": "intent_exploration_mandatory",
  "reason_text": "Query asks for unknowns/alternatives, exploration enforced.",
  "route_version": "v1.0.0"
}
```

## 5. Deterministic Policy Rules (v1)

Rule group A: intent to mode
- If query contains intent patterns:
  - "what am I missing"
  - "alternatives"
  - "limitations"
  - "contradict"
  - "what could be wrong"
  then `mode=explore` and `explore_required=true`.

- If query intent is known-item retrieval:
  - "find file"
  - "open latest"
  - exact doc lookup
  then `mode=exploit`.

- If query is decision-support, scenario assessment, or risk review:
  then `mode=hybrid`, `disconfirmation_required=true`.

Rule group B: domain constraints
- If domain is `hse` or compliance-critical:
  - `conservative_language_required=true`
  - `citation_required=true`
  - if evidence conflict is high, `hold_if_low_confidence=true`.

Rule group C: budget floors
- For `mode=explore|hybrid`:
  - `explore_ratio >= 0.2`
  - `min_contradicting_docs >= 1`.

Rule group D: entitlement guard
- Returned `allowed_tools` MUST be filtered by user entitlement policy.
- Router must not return tools outside authorized perimeter.

## 6. Entitlement Model

The router must carry forward identity context for downstream filters.

Minimum fields passed to retrieval tools:
- `user_id`
- `user_groups`
- `entitlement_scope`
- `request_id`

If service-principal search is used behind the tool:
- retrieval layer MUST apply per-user ACL filter before ranking.
- result payload MUST include `acl_filter_applied=true`.

## 7. Downstream Tool Selection Mapping

Selection matrix:
- `mode=exploit`
  - Primary: `enterprise_graph_search`
  - Optional: `geox_contrast_search` disabled unless user escalates.

- `mode=explore`
  - Primary: `geox_contrast_search`
  - Required companion: `geox_disconfirm_evidence_scan`
  - Graph can be auxiliary only.

- `mode=hybrid`
  - Use both exploit and explore lanes with budget floors.

## 8. Response Contract Requirements

For `mode=explore|hybrid`, final answer must include:
- supporting evidence
- contradicting evidence
- unknowns
- confidence band
- citation list

If contradiction floor not met:
- return status `PARTIAL`
- include remediation: query expansion attempted, why still unmet.

## 9. Observability / Audit Fields

Log per request:
- `timestamp`
- `request_id`
- `user_id_hash`
- `router_mode`
- `domain`
- `risk_level`
- `policy_flags`
- `allowed_tools`
- `selected_tools`
- `reason_code`
- `exploit_docs_used`
- `explore_docs_used`
- `contradicting_docs_used`
- `status` (COMPLETE|PARTIAL|HOLD)

Security note:
- Log IDs should be pseudonymized where required by policy.

## 10. Failure Semantics

Failure classes:
- `ROUTER_TIMEOUT`
- `ROUTER_POLICY_INVALID`
- `ROUTER_UNAUTHORIZED`
- `ROUTER_DEPENDENCY_DOWN`

Fallback behavior:
- fallback mode = exploit
- enforce citation-required
- emit `status=PARTIAL`
- include `failure_class` and safe next action.

## 11. Example Calls

### Example A: Exploration intent

Input:
```json
{
  "query": "What am I missing about Kinabalu basement porosity?",
  "user_id": "arif.fazil",
  "user_groups": ["geox-core", "subsurface"],
  "domain_hint": "geology",
  "task_type": "analysis",
  "request_id": "req-20260609-001"
}
```

Output:
```json
{
  "mode": "explore",
  "domain": "geology",
  "risk_level": "medium",
  "policy_flags": {
    "explore_required": true,
    "disconfirmation_required": true,
    "conservative_language_required": false,
    "citation_required": true,
    "hold_if_low_confidence": false
  },
  "retrieval_budget": {
    "exploit_ratio": 0.3,
    "explore_ratio": 0.7,
    "min_explore_docs": 5,
    "min_contradicting_docs": 2
  },
  "allowed_tools": [
    "geox_contrast_search",
    "geox_disconfirm_evidence_scan",
    "enterprise_graph_search"
  ],
  "reason_code": "intent_exploration_mandatory",
  "reason_text": "Unknowns/contrast intent detected.",
  "route_version": "v1.0.0"
}
```

### Example B: Known file lookup

Input:
```json
{
  "query": "Find KL2_TDR_Finalized.xlsx I edited last week",
  "user_id": "arif.fazil",
  "user_groups": ["geox-core"],
  "domain_hint": "general",
  "task_type": "lookup",
  "request_id": "req-20260609-002"
}
```

Output:
```json
{
  "mode": "exploit",
  "domain": "general",
  "risk_level": "low",
  "policy_flags": {
    "explore_required": false,
    "disconfirmation_required": false,
    "conservative_language_required": false,
    "citation_required": true,
    "hold_if_low_confidence": false
  },
  "retrieval_budget": {
    "exploit_ratio": 1.0,
    "explore_ratio": 0.0,
    "min_explore_docs": 0,
    "min_contradicting_docs": 0
  },
  "allowed_tools": ["enterprise_graph_search"],
  "reason_code": "intent_known_item_lookup",
  "reason_text": "Direct known item retrieval.",
  "route_version": "v1.0.0"
}
```

## 12. Implementation Notes

- Start as a lightweight rules engine (keyword + intent templates).
- Add classifier model later if needed, but keep policy rules explicit and overrideable.
- Version route policy (`route_version`) and include it in logs for audit traceability.
- Keep policy config externalized in YAML/JSON for governance review.

## 13. Acceptance Criteria

- 100% of knowledge queries call `arifos_route_query` before retrieval.
- 0 policy-bypassed tool calls in audit logs.
- For explore/hybrid intents, contradiction floor is met or answer marked PARTIAL.
- Routing decision reproducible from logged inputs and policy version.
