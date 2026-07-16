# GEOX Post-Merge Drift Audit

Audit date (UTC): 2026-07-13 12:05:01  
Scope: Post-merge truth alignment for institutional release evidence  
Reference release: v2026.07.13-institution-1

## 1. Evidence inputs

- Local git HEAD: e670c39d2ed9266ae75f3046ec98e37091a09e25
- Public health endpoint: https://geox.arif-fazil.com/health
- Public discovery endpoint: https://geox.arif-fazil.com/.well-known/mcp/server.json
- Public apps endpoint: https://geox.arif-fazil.com/apps.json
- Public GUI endpoint: https://geox.arif-fazil.com/gui/
- README baseline: repository README claims collected in session evidence

## 2. Claim parity table

| Claim area | README / static claim | Live observation | Verdict | Notes |
|---|---|---|---|---|
| Live status | healthy / GREEN path expected | status=healthy and owner_summary.color=GREEN | PASS | Runtime matches health claim |
| Live version | v2026.07.06-phase3.1-rsi-pipeline | version=v2026.07.06-phase3.1-rsi-pipeline | PASS | Version alignment holds |
| Live commit identity | live_commit_short=5bc66284 and git identity geox-5bc66284 (SOT block) | git_version=geox-5bc66284 while local main is e670c39d | DRIFT | Public runtime appears behind repository head |
| Public tool count (SOT header) | mcp_tools_live=32 | health reasons include public_tools=32 | PASS | Indirect parity from health evidence |
| Public tool count (README body section) | Public MCP tools shown as 26 | health reasons include public_tools=32 | DRIFT | Body prose stale vs live SOT signal |
| tools/list direct verification | tools/list is canonical truth rule | Public /mcp requires session handshake; unauthenticated direct call blocked | DRIFT | Verification path requires protocol session context |
| Public health endpoint reachability | should be reachable | HTTP 200 | PASS | Reachable |
| Public MCP endpoint reachability | should be reachable | Endpoint reachable; protocol returns controlled errors without required headers/session | PASS | Reachable with governance guard |
| Public server.json reachability | should be reachable | HTTP 200 | PASS | Reachable |
| Public apps.json reachability | should be reachable | HTTP 200 | PASS | Reachable |
| Public GUI reachability | should be reachable | HTTP 200 | PASS | Reachable |

## 3. Detailed observations

- Public service health reports healthy state and GREEN owner summary.
- Public runtime identity hash is geox-5bc66284, while repository main head for release cut is e670c39d.
- This indicates a deployment lag or staged rollout split between repository and live surface.
- README contains mixed tool-count claims (32 in SOT header context, 26 in body capability section), causing static ambiguity.
- Canonical verification method (tools/list) could not be completed anonymously due to required session contract at /mcp.

## 4. Risk assessment

- Operational risk: medium.
- Primary risk driver: repository-to-runtime commit drift.
- Secondary risk driver: static documentation inconsistency (26 vs 32 public tools).
- Control already present: live /health remains honest and exposes identity and tool-count reason.

## 5. Recommended corrective actions

1. Align production deployment to release commit e670c39d, or explicitly document staged hold reason.
2. Normalize README public tool-count language to one canonical source path.
3. Add CI guard that compares README count against authenticated tools/list result under valid MCP session.
4. Publish a short operator note with current runtime commit and release commit delta until converged.

## 6. Audit verdict

- Overall: CONDITIONAL PASS.
- Service is live and healthy, but truth alignment has document/runtime drift that must be closed for strict institutional readiness.
