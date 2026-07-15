<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-11
valid_from: 2026-07-09
valid_until: 2026-08-10
confidence: high
scope: /root/geox/GENESIS
-->

# GENESIS/017 — EARTHOS CONSTITUTION

> **Authority:** F13 SOVEREIGN (Arif)  
> **Status:** CANON draft — enforceable as GEOX law; VAULT999 seal only after F13 ceremony  
> **SoT:** `/root/geox/GENESIS/017_EARTHOS_CONSTITUTION.md`  
> **Canonical floors:** arifOS `GENESIS/000_KERNEL_CANON.md` + GEOX `003_CONSTITUTIONAL_ALIGNMENT.md`  
> **Pairs:** 007 Charter · 009 Organ Contract · 010 AEI · 011 Competitive Layer · 012 GEOX-001 · 013 Metabolic · 015 Agentic Geology · 016 Prompt Standard  
> **One line:** Earth physics first; geology second; arifOS seals; Arif vetoes.

---

## 0. What EarthOS Is / Is Not

**EarthOS** is the constitutional nickname for **GEOX NATURAL_LAW** — the governed earth-intelligence substrate of the arifOS federation.

### EarthOS IS

- Physics custody for wells, seismic, and basin claims  
- Falsification gates (SEAL / HOLD / VOID) with absolute numbers  
- Epistemic rank (OBS / DER / INT / SPEC) on material claims  
- Receipt custody (`geox://…`) with `vault999_status: DRAFT_ONLY` until arifOS  
- Layer-3 **earth reasoning** (GENESIS/011) — “whether the model deserves to live”

### EarthOS IS NOT

- A Petrel / DS365 / DecisionSpace clone  
- A capital allocator (WEALTH computes; never allocates here)  
- A medical or human-state adjudicator (WELL is REFLECT_ONLY)  
- A self-sealing vault writer (only arifOS + F13 seal VAULT999)  
- A planetary “operating system” product claim — see demotion of overclaim in `vision/earth_substrate_v1.md`  
- A replacement for human depositional, tectonic, or play intuition (GENESIS/015)

**Attack line (locked, GENESIS/011):**

```text
DS365 tells you where your model lives.
GEOX tells you whether your model deserves to live.
```

---

## 1. Hierarchy of Authority

```text
Arif (F13 SOVEREIGN) — final veto
        │
        ▼
arifOS (CONSTITUTIONAL_LAW) — F1–F13, 888 JUDGE, VAULT999
        │
        ▼
GEOX (NATURAL_LAW / EarthOS) — physics, evidence, DRAFT_ONLY receipts
        │
        ├──► WEALTH (CAPITAL_LAW) — NPV/EMV/STOIIP compute only; DER/INT inputs
        ├──► WELL (SUBSTRATE_LAW) — human readiness reflect; never earth verdict
        ├──► AAA — cockpit / A2A surface; never invents geology
        └──► A-FORGE — mutation only after arifOS SEAL
```

| Domain law | Owner | GEOX may |
|------------|-------|----------|
| NATURAL_LAW | GEOX | Emit physics gates, evidence, DRAFT receipts |
| CONSTITUTIONAL_LAW | arifOS | Judge floors, seal vault |
| CAPITAL_LAW | WEALTH | Receive tagged volumes; GEOX must not allocate |
| SUBSTRATE_LAW | WELL | GEOX must not diagnose humans |

Full organ ownership: `BOUNDARY.md`, GENESIS/009, GENESIS/010.

---

## 2. Articles of Earth Law

Each article: **Axiom · Geological meaning · Enforcement · Verdict grammar · STATUS**.  
STATUS uses only **LIVE / PARTIAL / ABSENT** with paths that exist in this repo at last verification.

Floors F1–F13 are **not re-numbered here** — geological mapping stays in GENESIS/003.

---

### Article I — Physics Precedes Interpretation

**Axiom:** No earth claim may outrank a falsifiable physical number.

**Geological meaning:** Velocity, mistie, porosity bounds, and wavelet stability constrain narrative. Geology supplies priors; physics adjudicates custody of the number plane.

**Enforcement:**

| Component | Path |
|-----------|------|
| PhysicsGuard (canonical) | `src/geox_core/physics/guards.py` |
| Physics parameters / CANON bounds | `src/geox_core/physics/parameters.py` |
| T-D methods | `src/geox_core/physics/td_methods/` |
| 1D T-D MCP | `geox_well_time_depth_calibrate` → `src/geox_mcp/tools/well_1d_surface.py` |

**Verdict grammar:** Bounds/gradient/curvature fail → HOLD or VOID on the physics plane (advisory).

**STATUS:** ✅ **LIVE** (core guard + 1D path). ⚠️ **PARTIAL** — dual/stub guard history may exist under `src/geox_core/laws/`; Phase B must single-path to `physics/guards.py`.

---

### Article II — Orthogonal Base First

**Axiom:** Cognitive, dimensional, and 3D tools may not speak as truth before Orthogonal Base custody.

**Geological meaning:** A beautiful 3D model without a well-tie is theatre. Ingest and 1D truth before interpretation volume.

**Enforcement:**

| Step | Tool / doctrine |
|------|-----------------|
| Metabolic law | GENESIS/013 |
| Ingest / QC | `geox_well_ingest`, `geox_well_qc`, seismic ingest/audit |
| Preflight | `geox_tie_preflight` |
| T-D → mistie → wavelet | 1D surface tools |
| Receipt | `geox_tie_receipt` |
| Truth wedge | `geox_benchmark_001` (GENESIS/012) |

**Order (non-negotiable):**

```text
ingest → QC → preflight → T-D → mistie → wavelet → tie_receipt
  → (only then) claim / contrast / vision / 3D / simulate
```

**STATUS:** ✅ **LIVE** doctrine + tools. ⚠️ **PARTIAL** enforcement — not every high-level tool hard-blocks if Base skipped (orthogonal route tests exist; global gate incomplete).

---

### Article III — Binary Gate, Constitutional Verdict

**Axiom:** Soft “quality looks OK” is HARAM. Gates emit SEAL / HOLD / VOID with absolute thresholds.

**Geological meaning:** Mistie in milliseconds is evidence. Phase class and condition number are evidence. Human eye-balling is not a SEAL.

**Enforcement:**

| Gate | Tool / engine | Threshold / rule |
|------|---------------|------------------|
| Mistie RMS | `geox_well_seismic_mistie_rms` · `engines/seismic/mistie_engine.py` | Default **25 ms** → SEAL / HOLD / VOID |
| Wavelet LS | `geox_wavelet_extract_least_squares` · `engines/seismic/wavelet_extract.py` | Real wavelet; not assumed Ricker as truth |
| GEOX-001 | `geox_benchmark_001` · `benchmarks/geox_001_well_seismic_truth.py` | PROCEED / HOLD / KILL scenarios |
| Preflight | `geox_tie_preflight` | GO / HOLD / VOID intake |

**Verdict grammar (physics plane):**

| Verdict | Meaning |
|---------|---------|
| **SEAL** | Physics agrees (advisory; not VAULT999) |
| **HOLD** | Uncertain / fixable |
| **VOID** | Physics rejects / catastrophic input |

**STATUS:** ✅ **LIVE** for 1D mistie + wavelet + GEOX-001. ⚠️ Assumed Ricker still appears on some synthetic paths — must be tagged **SPEC**, never OBS truth (Phase B).

---

### Article IV — Epistemic Rank

**Axiom:** Every material claim carries OBS / DER / INT / SPEC (or HYPOTHESIS where declared). Confidence ≤ 0.90 (F7).

**Geological meaning:** Tops and horizons are INT. Checkshots and logs are OBS. Velocity models without control are SPEC. Mixing ranks is a lie.

**Enforcement:**

| Surface | Path |
|---------|------|
| GEOX-001 evidence graph | `benchmarks/geox_001_well_seismic_truth.py` + tests |
| Claim / evidence envelopes | claim schemas + `geox_claim` / `geox_evidence` |
| Prompt block | `prompts/GEOX_CONSTITUTIONAL_PROMPT_BLOCK.yaml` · GENESIS/016 |

**STATUS:** ✅ **LIVE** on GEOX-001 and claim plane. ⚠️ **PARTIAL** — not every MCP tool forces labels on all outputs.

---

### Article V — Contradiction Metabolism

**Axiom:** An earth claim without an alternative is incomplete. Pre-seal requires challenge. Contradictions resolve to VOID / HOLD / DEMOTE — not silence.

**Geological meaning:** Multi-hypothesis discipline is geology. GEOX stores and scores contradictions; humans still invent play concepts.

**Enforcement:**

| Component | Path |
|-----------|------|
| Contradiction ontology | `src/geox_mcp/epistemic/contradiction_ontology.py` |
| Evidence contradict mode | `geox_evidence(mode=contradict)` |
| Claim challenge / pre-seal | `geox_claim` lifecycle · `tools/claims.py` |
| Biostrat falsify | `geox_biostrat_falsify`, `geox_biostrat_ruling_check` |
| Forbidden grammar | `geox_forbidden_claims_scan` |
| Unit tests | `tests/unit/test_contradiction_scan.py` |

**STATUS:** ⚠️ **PARTIAL** — live pieces, fragmented entry points. **ABSENT as product:** multi-well T-D/mistie/wavelet coherence matrix (Phase C — GEOX-002 wedge). Do **not** invent a parallel `geox_contradiction_engine` MCP; compose ontology + existing modes.

---

### Article VI — Uncertainty Cascade

**Axiom:** Naked certainty is VOID-grade epistemology. Joint confidence propagates; F7 caps confidence.

**Geological meaning:** Single-stage confidence ignores serial failure. Cascade serial ×, parallel noisy-or, and stage confidence must flow into claim envelopes.

**Enforcement:**

| Component | Path |
|-----------|------|
| Uncertainty cascade | `src/geox_core/orchestration/uncertainty_cascade.py` |
| EGS uncertainty models | `src/geox/egs/models/uncertainty.py` (+ egs tests) |
| Basin synthesis (uses cascade) | `src/geox_core/orchestration/basin_synthesis_pipeline.py` |

**STATUS:** ⚠️ **PARTIAL** — math LIVE; end-to-end 1D → claim → prospect auto-propagation incomplete.

---

### Article VII — Incomplete Earth / Gödel Wall

**Axiom:** Circular grounding and self-certifying earth stories are UNSEALABLE.

**Geological meaning:** The earth is not fully known. A model that only cites itself cannot become vault truth.

**Enforcement:**

| Component | Path |
|-----------|------|
| Gödel wall | `src/geox_core/godel_wall.py` |
| Anti–Beautiful One | `src/geox_core/anti_beautiful_one.py` · MCP epistemic twin |
| Anti-hantu / forbidden claims | `geox_forbidden_claims_scan` |

**STATUS:** ✅ **LIVE** modules. ⚠️ **PARTIAL** — not every narrative path hits the wall.

---

### Article VIII — Receipt Custody

**Axiom:** Computation without custody is ephemeral theatre. Every gate produces `geox://…` **or** explicit `MISSING_RECEIPT`.

**Geological meaning:** Future interpreters (human or agent) must re-open the number, not the screenshot.

**Enforcement:**

| Component | Path / pattern |
|-----------|----------------|
| 1D EGS lite | `data/egs/receipts/` · URI `geox://well/{id}/{tdfit\|mistie\|wavelet}/{rid}` |
| 1D writer | `well_1d_surface.py` |
| Vault field | `vault999_status: DRAFT_ONLY` always from GEOX physics plane |
| Tie receipt | `geox_tie_receipt` · schemas under `geox_core/schemas/` |

**STATUS:** ✅ **LIVE** (lite EGS) for 1D tools. ⚠️ **PARTIAL** — not all tools emit URIs; full graph EGS not universal.

---

### Article IX — Domain Separation

**Axiom:** GEOX witnesses the earth. It does not judge constitution, allocate capital, or diagnose humans.

**Enforcement:**

| Boundary | Document / code |
|----------|-----------------|
| Organ contract | GENESIS/009 · `BOUNDARY.md` |
| Risk tiers | `src/geox_mcp/organ_governance.py` |
| WEALTH bridge | `src/geox_core/adapters/wealth_bridge.py` (DER/INT volumes) |
| Federation floors | GENESIS/003 → arifOS 000 |

**STATUS:** ✅ **LIVE** doctrine. Continuous vigilance required against tool sprawl that crosses law domains.

---

### Article X — Sovereign Seal

**Axiom:** GEOX drafts. arifOS judges. Arif seals. No organ self-authorizes vault finality.

**Enforcement:**

| Step | Owner |
|------|-------|
| Physics receipt DRAFT_ONLY | GEOX |
| Claim create / evidence / challenge | GEOX |
| `geox_claim_seal` + `ack_irreversible` | GEOX proxy → arifOS |
| 888 JUDGE / VAULT999 append | arifOS |
| Final veto | F13 Arif |

**STATUS:** ✅ **LIVE** boundary. Any path that self-seals from GEOX is a constitutional defect — VOID the path, do not paper it.

---

## 3. Six Bands of Operation (from GENESIS/009)

| Band | Role | Example surfaces |
|------|------|------------------|
| **observe** | Ingest logs, seismic, markers | `geox_well_ingest`, seismic ingest |
| **correlate** | Well-tie, strat, biostrat | 1D tools, tie preflight/receipt |
| **infer** | Structure, facies, contacts | interpret / contrast / claim |
| **simulate** | Rock physics, scenarios, charge | petrophysics, basin_charge |
| **audit** | Uncertainty, QC, contradictions | evidence contradict, forbidden scan, PhysicsGuard |
| **render** | Thin payloads + manifests | map/render tools; never invent geology |

**GEOX never returns naked certainty.** Every claim carries physics basis, uncertainty, conflict register, and allowed-use contract when on the claim plane.

---

## 4. Claim Lifecycle (code-backed)

```text
create → attach evidence → validate → challenge
  → (optional contrast / contradiction scan)
  → seal proxy (ack_irreversible)
  → arifOS 888 → F13 → VAULT999
```

Pre-seal without challenge is incomplete (Article V). Physics gates without Orthogonal Base are incomplete (Article II).

---

## 5. Multi-Organ Handoff

| Packet | From GEOX | To | Must carry |
|--------|-----------|-----|------------|
| Earth claim | Claim envelope + physics gates | arifOS | evidence, challenges, uncertainty, DRAFT receipts |
| Volume / EMV inputs | STOIIP MC / POS-style DER | WEALTH | DER/INT tags — never fake OBS |
| Human readiness | — | WELL | GEOX does not adjudicate |
| Mutation / deploy | — | A-FORGE | Only after arifOS SEAL |

---

## 6. Strategic moats ↔ Articles (gap matrix)

Strategic language maps onto articles — **no second organ zoo**.

| Strategic moat | Article(s) | Status 2026-07-09 |
|----------------|------------|-------------------|
| Physics invariants / PhysicsGuard | I | LIVE / PARTIAL (stub risk) |
| Seismic honesty (mistie, wavelet, QC) | III | LIVE |
| Falsification + GEOX-001 | II, III | LIVE |
| Epistemic OBS/DER/INT/SPEC | IV | LIVE on 001 / PARTIAL global |
| Contradiction metabolism | V | PARTIAL |
| Uncertainty propagation | VI | PARTIAL |
| Basin / petroleum matrix | (resources + `geox_basin`) | PARTIAL; product matrix **ABSENT** |
| EGS + DRAFT_ONLY | VIII, X | LIVE lite |
| Multi-well field coherence | V + future GEOX-002 | **ABSENT as product** |

**Four operational moats of GENESIS/016** (physics · EGS · falsification · prompts) are a **subset** of this constitution, not a competing list. Prompt block remains mandatory for agents.

---

## 7. 777_FORGE — Build table (ordered)

| Priority | Work | Article | Action | Status |
|----------|------|---------|--------|--------|
| **P0** | This constitution | all | Seal law with honest STATUS | **THIS DOC** |
| **P0** | Keep 1D + GEOX-001 green | I–IV, VIII | Regression only; no forks | LIVE |
| **P1** | Single PhysicsGuard import path | I | Quarantine always-True stubs | OPEN (Phase B) |
| **P1** | Ricker = SPEC when extract available | III | Prefer LS wavelet | OPEN (Phase B) |
| **P1** | `resource_uri` or `MISSING_RECEIPT` tests | VIII | Harden 1D + tie_receipt | OPEN (Phase B) |
| **P1** | Multi-well physics coherence (GEOX-002) | V, VI | Compose ontology + cascade + N receipts | OPEN (Phase C) |
| **P2** | Spatial ToAC / prospect-local contrast | — | GENESIS/014–015 build order | DEFERRED |
| **P3** | Full basin consistency matrix | — | After multi-well + multi-seismic receipts | DEFERRED |
| **P3** | 3D corner-point / Darcy receipts | — | GENESIS/014 | DEFERRED |

**Iron rule:** Do not ship P3 basin product before P1 multi-well coherence.

---

## 8. 999_SEAL — Required receipt fields

Every governed physics/claim packet SHOULD include:

| Field | Rule |
|-------|------|
| `tool` | Canonical MCP or engine name |
| `actor` / actor_signature | Attributable (F11) |
| `threshold` | e.g. mistie_ms = 25 |
| `verdict` | SEAL \| HOLD \| VOID (physics) or claim state |
| `resource_uri` | `geox://…` **or** `MISSING_RECEIPT` |
| `epistemic` | OBS / DER / INT / SPEC on material numbers |
| `physics_validated` | bool / guard summary |
| `vault999_status` | **`DRAFT_ONLY`** until arifOS + F13 path |
| `timestamp` | UTC |

GEOX may never set vault finality unilaterally (Article X).

---

## 9. Anti-patterns (constitution-level HARAM)

1. Soft quality scores instead of absolute RMS ms.  
2. Assumed Ricker presented as earth wavelet truth.  
3. 3D / vision / simulate before Orthogonal Base.  
4. New MCP tool when a mode on `geox_evidence` / `geox_claim` / `geox_basin` exists.  
5. Second PhysicsGuard or always-True guard stubs left on the wire.  
6. GEOX self-seal to VAULT999.  
7. WEALTH-style capital allocation or WELL diagnosis from GEOX.  
8. Unlabeled confidence > 0.90.  
9. Amplitude → hydrocarbon leap without physics ladder.  
10. “EarthOS” as marketing for planetary AGI without falsification receipts.  
11. Shadow schemas / second tool registry.  
12. Building GEOXBASINMATRIX product before multi-well coherence.

---

## 10. Skill ↔ Code rule

Skills under `~/.agents/skills/geox-*` are **agent loading surfaces**.  
**Live registry and source paths win** on name or count drift.  
Skills must be updated after code — never invent tools from skill text.

Relevant skills: `geox-constitution`, `geox-well-tie-pipeline`, `geox-contradiction-engine`, `prospect-maturation-workflow`.

---

## 11. Supersession

| Document | Relation to 017 |
|----------|-----------------|
| GENESIS/003 | **Still SoT** for F1–F13 geological mapping |
| GENESIS/009 | **Still SoT** for six bands + ontology layers |
| GENESIS/011 | **Still SoT** for competitive Layer-3 stance |
| GENESIS/012 | **Still SoT** for GEOX-001 wedge |
| GENESIS/015 | **Still SoT** for human–agent split; pairs 017 |
| GENESIS/016 | **Still SoT** for prompt block + four operational moats; subset of 017 |
| **017** | **Compressed EarthOS charter** — articles, gap matrix, build order, seal fields |

017 does **not** replace arifOS floors. It is NATURAL_LAW for earth custody.

---

## 12. Verification anchors (at last check)

| Probe | Expectation |
|-------|-------------|
| `curl :8081/health` | healthy / GREEN |
| 1D tests | `tests/benchmarks/test_geox_1d_mcp_surface.py` |
| GEOX-001 | `tests/benchmarks/test_geox_001_*.py` |
| PhysicsGuard | `tests/test_physics_guard.py` |
| Contradiction unit | `tests/unit/test_contradiction_scan.py` |

Re-probe at T₁ before any irreversible deploy (Dynamic-State Principle).

---

*GENESIS 017 · 2026-07-09 · EarthOS Constitution (CANON draft)*  
*Pairs: 003 · 009 · 011 · 012 · 015 · 016 · BOUNDARY.md*  
*DITEMPA BUKAN DIBERI — The gate is physics. The verdict is constitutional. The seal is sovereign.*
