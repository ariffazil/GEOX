# PHYSICAL REALITY GRAPH — semantic contract v0.2

v0.2 (2026-11-12) adds the SPINE DECISION (§4a), the two missing edge fields
valid_time + geometry_context (§4), and the FALSIFIER soft requirement (§4b).

Arif's correction applied (2026-11-12, ENTERPRISE PARTIAL→SEAL architecture):
*xDD KG, H3, claims, topology and plate rotation are NOT five competitors for
"GEOX Knowledge Graph" — they are five layers of different reality.*

Supersedes the build-path framing in EARTH-REALITY-GRAPH.md §5 where it differs.

---

## 0. THE ORDERING (the eureka, stated as law)

```
REALITY  ──observed by──▶  OBSERVATION  ──supports──▶  CLAIM  ──interpreted into──▶  MODEL
                                                                              MODEL ≠ REALITY
```

Literature ≠ reality. Map ≠ reality. Seismic interpretation ≠ reality. LLM extraction ≠ reality.
Macrostrat polygon ≠ reality. GPlates reconstruction ≠ reality.
They are all witnesses, measurements, models, or transformations of reality.

**Earth first. Knowledge second.** That is what makes GEOX different from another geoscience RAG.

---

## 1. THE FIVE LAYERS (never collapsed into one monster KG)

| Layer | Answers | Lives in GEOX today |
|---|---|---|
| **Reality graph** | What Earth contains, where, when, relative to what | `src/geox/egs/models/entities.py::EarthGraph` — **dormant skeleton** (see §2) |
| **Observation graph** | What humans and instruments measured | ingest paths exist (`geox_well_ingest`, `geox_seismic_ingest`); **0 registered sources live** |
| **Claim graph** | What we believe the measurements mean | `geox_claim` + 87 authored claims in `resources/basins/*/claims.json` — live |
| **Evidence graph** | Why the claim exists | `evidence_refs`, `prior_art`, Macrostrat lexicon/xDD as future witness provider |
| **Reconstruction** | Physical state transformed through time | DEREGISTERED GPlates path (`tools_wiring.py:2172`) — infrastructure worth keeping |

Each layer is a graph with its own edges. Cross-layer edges are the only edges that cross:
`observation → supports → claim → about → reality-node`.

---

## 2. THE PROOF THAT DECIDED THE PATH (measured, not assumed)

Arif asked: *prove whether the existing EarthGraph is actually instantiated and mutated anywhere
in live GEOX.* Measured 2026-11-12:

| Check | Result | Instrument |
|---|---|---|
| Is it instantiated at startup? | **YES** — `EarthGraph()` at import, `init_egs_state()` called at server.py:396 | source + live journal |
| Is it ever mutated? | **NO** — journal at every start: `EGS state initialized: graph v1, claims=0, provenance_chains=0` (incl. the running PID 1421087, started 2026-11-11T16:06:09Z) | `journalctl -u geox-mcp` |
| Is it exposed on the MCP surface? | **NO** — `register_egs_tools(mcp)` is COMMENTED OUT at server.py:399; none of the 27 public tools is an egs_* tool | live tools/list + source |
| Is it reachable via `geox_basin` "mode expansion" as its docstring claims? | **NO** — `basin.py` has zero EGS references; the docstring overclaims | source |
| Does the one live EGS-resident tool touch it? | **NO** — `geox_temporal` (decline/rrr/basin_lifecycle/cadence) imports only fastmcp/logging/math | source |

**Verdict: the EarthGraph skeleton exists, is empty, and nothing can ever fill it.**
Therefore: do not build another graph. **Promote this dormant skeleton into the canonical
Physical Reality Graph.** (Arif's instruction, now measured and confirmed.)

Semantic renames (conceptual contract first; code renames only when the layer is wired):
```
state/knowledge_graph.py            →  BasinRelationGraph   (it holds basin/well name relations)
egs/models/entities.py::EarthGraph  →  PhysicalRealityGraph (the canonical physical layer)
```

---

## 3. NODE TAXONOMY (extends `EarthEntity`; geometry is a FUNCTION OF TIME)

```
EarthEntity (id, name, description, tags, version, active)   ← existing
 ├─ Lithosphere
 ├─ Plate
 ├─ CrustalBlock
 ├─ Fault
 ├─ Fold
 ├─ Basin
 ├─ StructuralHigh
 ├─ StratigraphicBody
 │   ├─ Formation
 │   ├─ Member
 │   └─ ReservoirBody
 ├─ IgneousBody
 ├─ Unconformity
 ├─ WellIntersection
 └─ Observation            ← NEW: the reality graph's only source of truth
```

**`geometry(t)`, not `geometry`.** Geological geometry has history. Every body carries
`geometry_at(t) -> Geometry | None` and a `plate_id` so reconstruction is a lookup, not a model.

---

## 3a. THE SPINE DECISION (settled — no second graph)

**Nodes come from the EarthGraph entity types. Edges come from the claim machinery.**
One spine, one owner.

```
NODE IDENTITY   ← EarthGraph entity types (basin, play, strat_unit, horizon, fault,
                   volume, well, survey + the taxonomy in §3)
                   key = (entity_type, external_ref)

EDGE            ← ClaimEnvelope machinery, now with subject/predicate/object
                   (+ valid_time, geometry_context, falsifier_state)

STORAGE         ← EarthGraph, lifted out of its in-memory global and persisted.
                   The claim schema gains OPTIONAL fields; no new store.
```

The alternative — binding claims to their own ad-hoc node types — was measured and
rejected: it produces two graphs with two owners, which is the failure class the
census already exists to prevent. The census measures entity-binding edges, not
claim-binding edges; under this decision the census number goes UP as real bindings
land, which is the only thing a census should do.

**EarthGraph is the canonical physical layer.** `src/geox/egs/models/entities.py` is
promoted, not replaced. Its `ConnectivityGraph` (3-tuples of source/target/relation)
is the seed shape for the edge vocabulary in §4.

## 4. RELATION SEMANTICS (the missing jump: physical, not `related_to`)

```
Unit A        OVERLIES     Unit B
Fault X       CUTS         Formation Y
Unconformity U TRUNCATES   Sequence S
IgneousBody I INTRUDES     Unit U
Well W        PENETRATES   Formation F
Plate P       CONTAINS     CrustalBlock C
Body A        ADJACENT_TO  Body B
```

Every edge carries — no edge without these. **valid_time and geometry_context are
OPTIONAL on day one, not retrofitted later** (a geology edge without time cannot be
tested against the rock record, and one without geometry cannot be tested against space):

```
subject_ref:       (entity_type, external_ref)     ← EarthGraph node
predicate:         OVERLIES | CUTS | TRUNCATES | INTRUDES | PENETRATES |
                   CONTAINS | ADJACENT_TO | ...
object_ref:        (entity_type, external_ref)     ← EarthGraph node
valid_time:        {start_ma, end_ma}               OPTIONAL — required before the
                   edge may claim a temporal relation (CUTS/OVERLIES/etc.)
geometry_context:  {bbox | h3_cells | section_ref} OPTIONAL — required before the
                   edge may claim a spatial relation
observation_refs:  [Observation ids]                — what measured it
claim_refs:        [ClaimEnvelope ids]              — what we believe it means
provenance:        [file | receipt | upstream id]
confidence:        (existing)
epistemic_label:   OBS | DER | INT | HYPOTHESIS | UNKNOWN   (existing machinery)
status:            observed | derived | interpreted | disputed
falsifier:         (existing) — see §4b
forbidden_uses:    (existing)
```

**Rule for the optional pair:** an edge that asserts a spatial or temporal relation
WITHOUT the matching field is not permitted to claim `observed`. It is `interpreted`
at best, and it must say so. That is cheaper than retrofitting time and space into
every edge later, and it keeps an honest gap visible instead of hiding it.

`status` is the fundamental one: an edge that is `interpreted` must never render as
`observed`. That single distinction is what stops a seismic pick from becoming a fact.

---

## 4b. THE FALSIFIER SOFT REQUIREMENT (the number that matters more than the bindings)

The census measured **9 of 87 claims carry a falsifier**. A claim without a
falsifier cannot be tested, so binding it into a graph only puts an untestable
statement into the structure — and makes the structure look rigorous because the
edges exist.

**Rule (Slice 2, from day one):** every edge carries `falsifier_state`, one of

| state | meaning |
|---|---|
| `FALSIFIABLE` | a falsifier exists (or one can be derived from the edge's own fields) |
| `UNFALSIFIABLE_AS_STATED` | no falsifier — the edge is flagged, not hidden, and cannot be cited as tested |
| `UNVERIFIED` | a falsifier exists but has not been run |

An edge in `UNFALSIFIABLE_AS_STATED` is still allowed in the graph — removing it
would be the same silent-gap error the census exists to prevent — but it carries the
label, and any query that returns it must return the label too. A graph query that
answers "what is known about X" and silently returns 78 untestable statements among
9 testable ones is lying by omission.

**Target:** Slice 2 ships the `falsifier_state` field and the label propagation.
Raising 9/87 is content work (Arif's judgement, not an agent's) and is tracked
separately — the instrument comes first.

## 5. IDENTITY (one node, many sources)

Node key = `(entity_type, external_ref)`.
- Upstream half: `macrostrat:col:<id>`, `macrostrat:unit:<id>`, `macrostrat:int:<id>`,
  `macrostrat:strat_name:<id>`, `macrostrat:source:<id>` — the canonical lexicon keys.
- Local half: `local:well:<well_id>`, `local:survey:<id>`, `local:obs:<sha256-prefix>`.

One `Formation X` node receives the Macrostrat unit polygon, Arif's basin-profile stratigraphy,
and the log interval from a LAS — as three edges, not three nodes.

---

## 6. ACCEPTANCE TEST (v0 — the gate the slice must pass)

**Given: Sabah, 15 Ma.** GEOX returns:
1. physical entities present at that place and time,
2. spatial relationships between them (typed, time-valid),
3. temporal validity of each relation,
4. present geometry, and reconstructed geometry where a provider exists,
5. supporting observations (or an explicit "none"),
6. competing geological claims (the interpretation set),
7. provenance for every edge,
8. **UNKNOWN wherever evidence is absent** — absent evidence is a returned value, not a gap.

If the answer contains no UNKNOWN, it is lying (F7). The test fails if GEOX returns an
invented unit where coverage says none exists.

---

## 7. BUILD PATH (Arif's phases; revised by the census + proof)

| Phase | Content | Prereq | Size |
|---|---|---|---|
| 0 | **Census** — measured: 111 nodes, 92 edges, 0 entity-binding edges | — | ✅ done (`4259d9ac`) |
| 1 | **Promote the dormant skeleton**: persist `EarthGraph` (SQLite first), register ONE read surface, adopt the semantic contract above | this contract | small |
| 2 | **Binding**: claim→entity edges (`subject_ref/predicate/object_ref/epistemic_label/coverage_score` as optional fields on the existing claim schema); the unbound count is reported honestly | Phase 1 | small |
| 3 | **Observation**: `geox_well_ingest`/`geox_seismic_ingest` write Observation nodes + `observation→unit` edges with the coverage class they already compute | Phase 2 | medium |
| 4 | **ReconstructionProvider**: `reconstruct(entity, time_ma) -> Geometry`; implementations `StaticProvider` (present-day), `CorelleProvider`, `GPlatesProvider` (revive the deregistered path *behind the interface*) | Phase 1 | small |
| 5 | **Literature witness**: xDD/KG as an *evidence provider* — `passage → asserts → Claim → about → node`. It supports claims; it never writes reality edges | Phase 2 | medium |
| 6 | **Topology** (face/edge/node adjacency) only if geological use-cases prove it necessary | use-case | large |

**Do not** build xDD, topology-manager, Corelle and map ingestion simultaneously (Arif).
**Do not** start Phase 3 before Phase 2 has bindings (census logic: observations with nothing to
bind to are a dashboard with a database behind it).

---

## 8. SUBSTRATE (deliberately NOT Macrostrat's)

H3 (spatial index) · Shapely (geometry) · the existing typed entity objects · LanceDB (retrieval) ·
the existing claim engine · VAULT999 (provenance). SQLite for persistence first — the graph is
small (hundreds of nodes today); a database decision made before there is a graph is LAW 3.

**PostGIS only when** GEOX demonstrably needs polygon topology at scale, spatial joins over large
datasets, persistent face/edge/node topology, or server-side reconstruction workloads. Don't
import infrastructure because the upstream project happens to use it.

---

## 9. RECEIPTS

- Census: `/root/GEOX` commit `4259d9ac`, `scripts/earth_graph_census.py` (runnable)
- Runtime proof: `journalctl -u geox-mcp` — `EGS state initialized: graph v1, claims=0, provenance_chains=0` at every start incl. PID 1421087 (2026-11-11T16:06:09Z, still running)
- Dead-surface proof: `server.py:399` `# register_egs_tools(mcp)` (commented out) · `basin.py` zero EGS references · live tools/list = 27, no egs_*
- Deploy-gate invariant (Arif's finding, built): `/root/arif-fazil.com` commit `96d1025` — `scripts/verify-served-state.py` + self-test 7/7 + `make verify-served`
- Macrostrat architecture: macrostrat.org/docs/platform/system-architecture · UW-Macrostrat/corelle · Mapboard/topology-manager · UW-Macrostrat/macrostrat-xdd
- Supersedes: EARTH-REALITY-GRAPH.md §5 build path (kept for the census numbers and gap table)
