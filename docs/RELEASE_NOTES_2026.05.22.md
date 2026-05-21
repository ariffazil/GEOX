# RELEASE NOTES - GEOX v2026.05.22-pre

> **Pre-release date:** 2026-05-22  
> **Evidence date:** 2026-05-21  
> **Status:** PRE-RELEASE / PR REVIEW  
> **Authority:** arifOS governance, Arif final judgment

## Purpose

This pre-release lowers repo entropy while keeping GEOX focused as the Earth evidence engine: geoscience computation, governed subsurface evidence, and compatibility-safe tool behavior.

## Changed

- Shared federation layout contract repaired and normalized in `docs/AGENT_LAYOUT_CONTRACT.md`.
- Repo hygiene audit ledger added at `docs/REPO_HYGIENE_AUDIT_2026-05-21.md`.
- Existing dirty documentation drift cleaned without moving runtime code.
- Seismic/physics guard issues fixed:
  - `PhysicsGuard` imports NumPy explicitly.
  - attested Dix interval velocities are bounded to Sabah Basin limits.
  - well-tie computation no longer depends on random trace data for deterministic success.

## Verification

```txt
git diff --check: PASS
pytest tests/test_geox_mcp_benchmark.py tests/test_geox_sovereign_e2e.py -q: PASS (6/6)
pytest tests/ -q: PASS (51 passed, 1 skipped)
```

## Boundary

GEOX owns Earth evidence. It does not own constitutional judgment, final capital allocation, the agent cockpit, or general execution runtime.

## Release Note

This is a pre-release branch, not a direct push to `main`.

Ditempa Bukan Diberi.
