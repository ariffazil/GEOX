# GEOX Deprecation Calendar — 2026-07-30 Enforcement

> **DITEMPA BUKAN DIBERI** — Forged, Not Given.
> **Created:** 2026-07-02 | **Enforcement date:** 2026-07-30

## Items Scheduled for Deletion (2026-07-30)

| Item | Type | Location | Action | Risk |
|------|------|----------|--------|------|
| 49 backward-compat aliases | Code | `src/geox_mcp/registry.py:CANONICAL_COMPAT_TOOLS` | Delete entire dict + middleware compat path | LOW — already scheduled, no live dependency |
| `entrypoint_unified.sh` | Script | `/root/geox/entrypoint_unified.sh` | Delete file | LOW — already deprecated, forwards to entrypoint.sh |

## Items Pending Merge (no hard deadline)

| Item | Type | Location | Action | Risk |
|------|------|----------|--------|------|
| `geox/core/` duplicate | Package | `/root/geox/geox/core/` | Merge imports to root `core/`, update tests | MEDIUM — 20+ test files import from `geox.core.*` |

## Enforcement Process

1. **2026-07-28**: Pre-flight check — verify no live imports from compat aliases
2. **2026-07-30**: Delete compat aliases from `registry.py` + middleware
3. **2026-07-30**: Delete `entrypoint_unified.sh`
4. **2026-07-30**: Update `_EXPECTED_CANONICAL` if alias removal changes count
5. **2026-07-30**: Run full test suite, verify 0 regressions
6. **2026-07-30**: Commit with message: `chore(geox): enforce compat alias deletion per deprecation calendar`

## Guardrail

Do NOT extend the 2026-07-30 deadline. The 49 aliases are a maintenance tax and certification noise. Every day they exist, they increase the gap between "what GEOX reports" and "what GEOX actually is."

---

*DITEMPA BUKAN DIBERI*
