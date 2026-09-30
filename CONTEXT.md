# CONTEXT — GEOX (Earth Intelligence)

> What an agent (human or machine) needs to know to onboard GEOX without
> re-reading the whole repo.

## What GEOX is

GEOX is the Earth Intelligence organ of the arifOS federation. It computes
geological evidence from subsurface data (seismic, wells, basins, GLOF
cascades). It does **not** adjudicate, **not** allocate capital, **not** actuate
field equipment. Every output carries an epistemic label (`OBS` / `DER` /
`INT` / `SPEC`) and provenance.

## Role in the federation

```
arifOS  ── judges / seals (L0/L1)
   │
   ├── AAA        ── attention / routing (L1)
   │
   ├── GEOX ──── ► A-FORGE  ── executes (L2 EXECUTIVE)
   │             WEALTH     ── capital compute (L3 DOMAIN)
   │             WELL       ── vitality mirror (L3 DOMAIN)
   │             HERMES     ── inbound gateway (L3 DOMAIN)
   │
   └── arifFlow  ── receipt metabolism (L3)
```

GEOX outputs go **into** `arif_judge` (L0) for verdict; into `A-FORGE`
(L2) for execution; into `WEALTH` (L3) for capital math. GEOX never directly
writes to a sovereign DB.

## Authority ceiling

`555_COMPUTE_ONLY`. Action classes accepted:
- `OBSERVE` (read-only evidence)
- `MUTATE` (writes — but only to local GEOX cache, never to federation)
- `EXECUTE` (calls other tools)

GEOX has no `SEAL` class. Only `arif_judge` may SEAL.

## Public surface

31 canonical tools, all carrying the four required MCP annotations
(`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).
See `FEDERATION.md` for the role/layer markers and `registry.py` for the
gate-enforced list. The surface regeneration script is
`scripts/generate_all_surfaces.py`.

## Living doc rules

This file is a pointer, not a constitution. When in doubt, prefer:

1. `:8081/health` and `:8081/drift` (runtime truth)
2. `registry.py::CANONICAL_PUBLIC_TOOLS` (gate-enforced SOT)
3. `CANONICAL_PUBLIC_SURFACE.json` (generated)
4. `FEDERATION_CONTRACT.md`
5. `arifOS/docs/FEDERATION.md` (canonical)
6. This file (human explainer; the gates above still beat it)

## How to read GEOX outputs

Every tool returns:

```json
{
  "ok": true|false,
  "mode": "overview",
  "basin_name": "...",
  "observed":   { ... },   // OBS — direct measurement
  "derived":    { ... },   // DER — from physical law
  "interpreted":{ ... },   // INT — geologist's read
  "process_hypotheses": [...],
  "forbidden_claims": [...],   // machine-readable policy keys
  "missing_evidence": [...],   // for appraise/decision strictness
  "next_best_actions": [...],
}
```

Empty `observed: {}` is **FAIL** — not "no data," not "ok." Empty SUCCESS is a lie.

## What GEOX refuses

- **No publish to sovereign DBs.** GEOX writes to its own cache only.
- **No field control.** No actuator surfaces.
- **No capital allocation.** Money decisions go through WEALTH + arifOS.
- **No verdict.** Signals only; arifOS seals.
- **No ghost capabilities.** Surfaces are gated; `SURFACE_DRIFT` middleware
  rejects raw_live > canonical. If you see drift, redeploy.

## Onboarding (engineer)

```
1. uv sync
2. uv run python -m geox_mcp.server --host 127.0.0.1 --port 8081
3. curl http://127.0.0.1:8081/health
4. uv run python scripts/generate_all_surfaces.py
5. bash scripts/governance-gate.sh
6. PYTHONPATH=src pytest tests/ -q --tb=short
```

## Onboarding (agent / A2A)

```
1. Read /root/AGENTS.md (canonical federation guide)
2. Read /root/AAA/AGENTS-AUTONOMY.md (autonomy tiers)
3. Read this file
4. Read FEDERATION.md (pointer)
5. Read FEDERATION_CONTRACT.md (the actual contract)
6. Look at registry.py::CANONICAL_PUBLIC_TOOLS (the surface)
7. Don't read the source until you need to (tools are self-describing)
```

## Common mistakes

- Treating `interpreted` as ground truth. It's an interpretation; arifOS judges.
- Trusting the live count over the SOT. If they disagree, redeploy.
- Reading `events` from the inner JSON without checking `interpreted_compacted`.
  The MCP middleware compacts dicts over 4 KB. Always look for the
  top-level `event_registry` key for the full event list.
- Treating GEOX as authoritative on capital or judgment. It is not.
