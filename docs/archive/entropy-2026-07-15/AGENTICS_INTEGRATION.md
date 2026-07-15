# Agentics Integration — WELL · WEALTH · arifOS · GEOX

> **Last verified:** 2026-06-21 (W2-W13+ FORGE, commit `657b9eb0`)
> **Audience:** Agent builders integrating GEOX with the arifOS federation
> **Status:** Tools live; full federation call paths proven in mock mode

---

## Architecture: GEOX in the Agentic Mesh

```
┌────────────────────────────────────────────────────────────────────┐
│                     AGENT (Claude Code, OpenCode, …)                │
│  Calls MCP tools, reasons about evidence, proposes actions          │
└────────────┬───────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│                      arifOS KERNEL :8088                            │
│  Session init · 888 JUDGE · VAULT999 · 999 SEAL · F1-F13 floors    │
│  Routes calls; gates irreversible actions; seals outcomes          │
└────────────┬───────────────────────────────────────────────────────┘
             │ (kernel-mediated, federated)
             ▼
┌────────────────────────────────────────────────────────────────────┐
│                          GEOX :8081                                │
│  56 canonical MCP tools · Evidence-only · Witness to kernel         │
│  DOES NOT DECIDE — computes, models, testifies, hands to kernel    │
└────────────┬───────────────────────────────────────────────────────┘
             │ (subscribes via federation calls)
             ▼
┌────────────┴───────────────────────────────────────────────────────┐
│                                                                     │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│   │   WELL :18083    │  │  WEALTH :18082   │  │  A-FORGE :7071   │  │
│   │ Human Readiness  │  │ Capital Intel    │  │ Execution Shell  │  │
│   │ REFLECT-ONLY     │  │ ADVISORY-ONLY    │  │ (deployment)     │  │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. GEOX → arifOS KERNEL (the canonical witness path)

Every GEOX output is **evidence-only**. It hands the envelope to arifOS, which adjudicates.

```python
# Agent calls geox_prospect_evaluate(...)
result = await geox_prospect_evaluate({
    "mode": "screen",
    "evidence_refs": ["well-A-las", "seismic-B-il-5400"],
})

# Agent routes to arifOS for seal
verdict = await arifos_judge_deliberate({
    "candidate": result["primary_artifact"]["claim_text"],
    "evidence_receipt": result,
    "action_class": "DRAFT",  # not SEAL — GEOX never seals
})
# arifOS returns SEAL/SABAR/HOLD/VOID
# If SEAL: vault_entry_id is written; agent can commit
```

**Mandatory rules:**
- GEOX **never** issues drill decisions (F13 territory).
- GEOX **never** allocates capital (WEALTH territory).
- GEOX **never** adjudicates constitutional verdicts (arifOS territory).
- Every irreversible action routes through `geox_claim_seal` → arifOS 888 JUDGE.

---

## 2. GEOX ↔ WELL (Operator Readiness Gate) — NEW W13+

`geox_well_decision_class` reads operator fatigue from WELL and returns a C1-C5 decision class that gates joint inversion aggressiveness.

```python
# Before launching joint_inversion on a critical cell:
gate = await geox_well_decision_class({
    "operator_id": "arif",
    "task_description": "joint inversion of Malay Basin prospect",
})

if gate.decision_class == "C5":
    # Chronic fatigue or session_fatigue >= 0.85
    # DO NOT proceed — surface 888_HOLD
    raise SystemHold(rationale=gate.rationale)

if gate.decision_class in ("C3", "C4"):
    # Proceed but flag uncertainty
    result = await geox_joint_inversion({...with decision_class=gate.decision_class})

# C1 / C2 — proceed strict with full evidence envelope
```

**Implementation:**
- Lazy-imports WELL organ via arifOS kernel (`arifosmcp.tools.organ_health`).
- Falls back to a conservative stub (`_stub_well_assess` returns `fatigue=0.5` → C3) when WELL is unreachable.
- Decision matrix:

| Fatigue | Decision | Operator | Godel |
|---------|----------|----------|-------|
| < 0.40 | C1 | OPTIMAL | KNOWN |
| 0.40-0.65 | C3 | STABLE | KNOWN |
| 0.65-0.85 | C4 | AMBER | UNDECIDABLE_YET |
| ≥ 0.85 OR chronic | C5 | RED | **VOID (HOLD)** |

---

## 3. GEOX → WEALTH (Capital Feed) — NEW W13+

`geox_wealth_feed` consumes cell-level Physics9State from joint inversion and produces a WEALTH-ready feed.

```python
# After joint_inversion produces cell states
feed = await geox_wealth_feed({
    "cell_states": [
        joint_result.cells[0].state.to_dict(),
        joint_result.cells[1].state.to_dict(),
        ...
    ],
    "areal_extent_m2": 1e6,
    "pay_zone_thickness_m": 50,
    "water_saturation": 0.20,
})

# feed is the WEALTH-ready input. Feed it to wealth_compute_npv:
npv_result = await wealth_compute_npv({
    "scenario_inputs": feed,
    "discount_rate": 0.10,
    "capex_musd": 250,
})

# Or to wealth_omni_wisdom for full portfolio synthesis:
wisdom = await wealth_omni_wisdom({
    "mode": "synthesize",
    "decision_context": {
        "feed": feed,
        "operator_gate": gate.decision_class,
    },
})
```

**Verdict thresholds (lithology-aware):**
- Only Sandstone / Limestone / Dolomite count as producible (shale & basement = 0).
- `producible_phi = max(0, min(avg_phi, 0.28) - 0.05)` — defensible cap (shales typically > 0.28).
- `producible_score = producible_phi × (1 - Sw) × RF × grade_fraction × producible_fraction`.

| Score | Verdict | Action |
|-------|---------|--------|
| < 0.005 OR grade_fraction < 0.5 OR lithology_fraction < 0.3 | REJECT | Acquire more data; do not proceed |
| 0.005 – 0.015 | DEFER | Marginal; revisit with new wells |
| ≥ 0.015 | ADVANCE | Ready for `wealth_compute_npv` |

---

## 4. GEOX → A-FORGE (Deployment Hook)

A-FORGE owns build + deploy + orchestration. GEOX exposes build/test/deploy via Makefile:

```bash
# In A-FORGE pipeline
cd /root/geox
make install      # uv sync --frozen
make test         # 89 passed, 3 skipped
make smoke        # PYTHONPATH=src python scripts/smoke_test.py
make forge        # Trivy + Semgrep + Gitleaks + Ruff (non-blocking, 888_HOLD on critical)

# Deploy (requires 888_HOLD per AGENTS.md §Authority)
make build
systemctl restart geox-mcp
curl -s http://127.0.0.1:8081/health | python3 -m json.tool
```

A-FORGE monitors the service health and surfaces drift to the cockpit (AAA :3001).

---

## 5. GEOX → Foundation Model Agents (Prithvi, TerraMind, Clay, Aurora) — NEW W5-W8

For agents that need multimodal Earth observation inference, GEOX wraps pretrained foundation models with a constitutional envelope:

```python
# Prithvi-EO-2.0 inference (mock mode default; live requires GPU + 888)
result = await geox_prithvi_eo_inference({
    "tile_id": "T30TXN",
    "task": "flood_mapping",
    "bands": ["B02", "B03", "B04", "B8A", "B11", "B12"],
})

# result.ml_provenance carries:
#   - model_name: "Prithvi-EO-2.0"
#   - model_version: "2.0"
#   - input_hash: sha256 of the input payload
#   - confidence_source: "mock" or "softmax"
#   - mode: "live" or "mock"
# result.godel_wall: KNOWN (Rung 2 observation backed by HLS tile + model weights)
```

**Other FMs planned (scaffolded, awaiting 888):**
- `geox_terramind_scene_reason` — TerraMind (IBM + ESA Φ-lab, ICCV 2025, any-to-any generative)
- `geox_clay_mineral_inference` — Clay v1.5 (multi-sensor FM)
- `geox_aurora_atmosphere` — Aurora (Microsoft, atmospheric)
- `geox_tgs_seismic_inference` — TGS SFM (660M 3D ViT-H)
- `geox_hyperspectral_mineral` — SpectralEarth / HyperSIGMA

---

## 6. GEOX Tool Discovery from Agent Code

```python
# List all tools (run once at agent startup)
async def discover_geox_tools(session):
    tools = await session.list_tools()
    return tools

# Filter by lane for agent role:
discovery_tools = [t for t in tools if t["name"].startswith("geox_") and any(
    k in t["name"] for k in ("registry", "attribute_registry", "basin_resolve", "query", "icgem")
)]
# → 6 tools, all OBSERVE-only

reasoning_tools = [t for t in tools if any(
    k in t["name"] for k in ("seismic", "subsurface", "sequence", "evidence_reason",
                              "prospect", "horizon_contrast", "prithvi", "gravity_mag",
                              "mt_", "biostrat", "seismic_inversion", "geomechanics")
)]
# → 21 tools, all ANALYZE with lease+session
```

---

## 7. Federation Call Patterns

### Pattern A — Pure observation (no lease)
```python
# Agent discovers basin; gets back canonical ID; queries profile
basin = await geox_basin_resolve({"name": "Malay Basin"})
profile = await geox_basin_profile({"basin_id": basin.id})
# These tools are OBSERVE-only; no session needed.
```

### Pattern B — Lease + session for reasoning
```python
# Reasoning tools require lease + session (acquired via arifOS)
async with arifos_session() as sess:
    lease = await sess.lease_acquire(tool="geox_joint_inversion")

    result = await geox_joint_inversion({
        "observations": [...],
    }, lease=lease, session_id=sess.id)

    if result.godel_wall["state"] == "VOID":
        await sess.hold(reason=result.godel_wall["reason"])
```

### Pattern C — Judgment with full federation call
```python
async with arifos_session() as sess:
    # Step 1: well gate
    gate = await geox_well_decision_class({"operator_id": sess.actor_id})
    if gate.decision_class == "C5":
        await sess.hold("operator_fatigue_hold")
        return

    # Step 2: joint inversion
    joint = await geox_joint_inversion({...}, session_id=sess.id)

    # Step 3: WEALTH feed
    feed = await geox_wealth_feed({
        "cell_states": [c.to_dict() for c in joint.cells],
    })

    # Step 4: doctrine wrap (assume + audit)
    asm = await geox_doctrine_assumption_register({
        "introduced_by": "geox_joint_inversion",
        "rung_origin": 5,
        "description": "Multi-physics fusion under Physics9 bounds",
    })

    # Step 5: godel review (seal verdict)
    claim = await geox_doctrine_godel_register_claim({
        "rung": 5,
        "description": "Joint inversion cell passes AAA grade",
        "depends_on_assumption_ids": [asm.assumption_id],
    })
    seal = await geox_doctrine_godel_review({
        "claim_id": claim.claim_id,
        "action": "seal",
    })

    if seal.state == "SEALED":
        await sess.vault_seal(seal.vault_entry_id)
```

---

## 8. Anti-Patterns (forbidden)

❌ **Calling GEOX for drilling decisions** — GEOX returns evidence, not verdicts.
❌ **Bypassing arifOS for irreversible actions** — every SEAL routes through 888 JUDGE.
❌ **Ignoring `godel_wall.state == "VOID"`** — this is a constitutional HOLD; do not retry.
❌ **Treating mock FM output as live inference** — check `ml_provenance.mode` before reasoning.
❌ **Routing WEALTH without `geox_wealth_feed`** — the feed carries the constitutional envelope; raw cell arrays bypass it.
❌ **Skipping `geox_well_decision_class` for heavy inversions** — operator fatigue gates the work.

---

## References

- **WELL organ:** `https://github.com/ariffazil/well` (port 18083)
- **WEALTH organ:** `https://github.com/ariffazil/wealth` (port 18082)
- **A-FORGE organ:** `https://github.com/ariffazil/A-FORGE` (port 7071)
- **arifOS kernel:** `https://github.com/ariffazil/arifos` (port 8088)
- **AAA cockpit:** `https://github.com/ariffazil/AAA` (port 3001)
- **Forge receipt:** `/root/forge_work/2026-06-21_geox-w2-w13-multiphysics-earth-witness.md`

---

**DITEMPA BUKAN DIBEI — the agentic mesh is forged. The sovereign decides.**
