# 888_HOLD Packet — Promote `geox_crustal_domain_classify` to canonical registry

**Date:** 2026-06-22
**Stage:** 777_FORGE / Stage 6 (EXECUTION) → handoff to 888_HOLD
**Forge agent:** FORGE (000Ω)
**Subject:** Authority required to register a new GEOX canonical tool.

---

## 1. What is being requested

Promote `geox_crustal_domain_classify` from **forge_work preview** (importable but not in canonical registry) to **canonical tool** (registered in `CANONICAL_PUBLIC_TOOLS`).

## 2. Why this is sovereign territory

Per GEOX `AGENTS.md §Authority`:

> ### Requires 888_HOLD
> - **Changes to the tool registry** (54 canonical tools in `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS`)

Adding a new tool to the registry changes the public MCP surface. This is an irreversible declaration of contract — every agent, every dashboard, every production deployment that calls `geox_*` will see this new tool appear.

The forge work has been done. The governance decision is yours.

## 3. What is ready for ratification

| Artifact | Status | Evidence |
|----------|--------|----------|
| `src/geox_mcp/tools/crustal_domain_classify.py` | ✅ Forged | 268 lines, Pydantic-strict |
| `tests/test_crustal_domain_classify.py` | ✅ 16/16 tests pass | Multi-cell scenarios, F4/F7/F13 |
| `src/geox_core/schemas/crust_vp_grammar.py` | ✅ Forged (Stage 6 prior) | 32 tests pass |
| `src/geox_core/physics/joint_inversion_zone_hook.py` | ✅ Forged (Stage 6 prior) | 15 tests pass |
| `forge_work/2026-06-22-huang2021-eureka-receipt.md` | ✅ Forged | 8 eurekas documented |

## 4. Tool specification (for registry entry)

| Field | Value |
|-------|-------|
| Tool name | `geox_crustal_domain_classify` |
| Axis | `reason` |
| Lane | `reasoning` |
| Expose | `True` |
| Risk tier | `C1_ADVISORY` (read-mostly, evidence-only, no SEAL) |
| Module | `src/geox_mcp/tools/crustal_domain_classify.py` |
| Function | `geox_crustal_domain_classify(request: CrustDomainRequest) -> CrustDomainMap` |
| Schema strict | Yes (Pydantic v2, `extra="forbid"`) |
| Confidence cap | F7 = 0.90 (enforced) |
| Source paper | Huang et al. (2021) — Tectonics |

## 5. Required registry edits (one-liner each)

```python
# src/geox_mcp/registry.py
CANONICAL_PUBLIC_TOOLS: list[str] = [
    ...
    "geox_crustal_domain_classify",  # ← INSERT
    ...
]

# In GEOX_TOOL_MANIFEST
{"name": "geox_crustal_domain_classify", "axis": "reason", "lane": "reasoning", "expose": True},

# In GEOX_RISK_MAP (organ_governance.py)
"geox_crustal_domain_classify": RiskTier.C1_ADVISORY,
```

## 6. Rollback plan

If ratification is denied or revoked:
- Remove the three lines above
- Tool becomes unimportable from canonical surface
- Existing imports still work (Python module path unchanged)

Risk: LOW. Reversible in one commit.

## 7. Risk assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Schema drift in future | LOW | Pydantic `extra="forbid"` + 16 tests |
| Conflict with existing tools | NONE | `geox_joint_inversion` (auto) and `geox_crustal_domain_classify` (manual) are complementary |
| Misuse for boundary inference | LOW | `sovereignty_note` explicitly states F13 requirement |
| Production deploy without 888 | LOW | This packet IS the 888 — promotion is conditional on approval |

## 8. What I need from you (888_HOLD required for)

**ONE-LINE RULING needed:**
> "Ratify geox_crustal_domain_classify as canonical tool" — **OR** —
> "Hold: changes required" — **OR** —
> "Reject: do not register"

If **ratify**, I will:
1. Apply the three registry edits
2. Run the full test suite
3. Commit + push to `origin/main`
4. Restart `geox-mcp.service`
5. Verify new tool visible at `http://127.0.0.1:8081/mcp`

If **hold**, I will await your specific changes (e.g. risk tier adjustment, schema additions).

If **reject**, the tool remains importable but not in canonical registry. No further action.

---

## 9. Cross-references

- Huang 2021 eureka receipt: `forge_work/2026-06-22-huang2021-eureka-receipt.md`
- Joint inversion hook (auto, no 888 needed): `src/geox_core/physics/joint_inversion_zone_hook.py`
- Phase I Kinabalu D1 deliverable scope (Phase I scope doc, see project workspace)
- Existing tool surface: `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS`

---

DITEMPA BUKAN DIBERI — The forge has built the substrate. The sovereign ratifies.

**HANDOFF to 888_HOLD:** Awaiting Arif's ruling.
