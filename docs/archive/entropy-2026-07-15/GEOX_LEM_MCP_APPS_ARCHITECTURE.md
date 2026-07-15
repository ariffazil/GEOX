# GEOX Large Earth Model — MCP Apps & UI Architecture

> **DITEMPA BUKAN DIBERI** — Forged, Not Given
>
> Extends the existing LEM Blueprint (v1, 2026-06-14) with MCP Apps, MCP UI, 
> product primitives, and the agentic earth loop.
>
> **Doctrine:** The winning GEOX product is not a geology chatbot. It is a 
> **constitutional cockpit for the Earth** where MCP Apps become the governing 
> interface, and every earth claim is a visual, reviewable, reversible object.

**Author:** Muhammad Arif bin Fazil (F13 SOVEREIGN) + FORGE (000Ω)  
**Canonical location:** `docs/GEOX_LEM_MCP_APPS_ARCHITECTURE.md`  
**Status:** SEALED (2026-06-15)  
**Supersedes:** The "Agent Surfaces" section of the existing LEM blueprint  
**Next review:** 2026-07-15

---

## 0. Dimensional Axes

Before the architecture, the axes that govern all design decisions:

| Axis | Pole A | Pole B | GEOX bias |
|------|--------|--------|-----------|
| **Epistemic** | Text | Visual-spatial | **Visual-spatial first.** Text is legal/explanatory wrapper. |
| **Temporal** | Snapshot | Diff | **Diff first.** Not "current state" but "what changed." |
| **Certainty** | Single truth | Alternatives | **Alternatives first.** No claim without contradiction scan. |
| **Authority** | Agent decides | Human approves | **Human veto always final.** Agent proposes, human seals. |
| **Identity** | Anonymous | Attributed | **Identity always visible.** No anonymous geology. |
| **Spatial** | Free text | CRS-guaranteed | **CRS always explicit.** No free-text coordinates. |
| **Governance** | Implicit | Explicit | **Approval first for irreversible.** No silent promotion. |

---

## 1. Architecture: LEM + MCP Apps Stack

The full stack, from Earth to human:

```
                          ┌──────────────────────────┐
                          │     MCP HOST (Claude,     │
                          │    ChatGPT, Cursor...)    │
                          │    Conversation entry     │
                          └───────────┬──────────────┘
                                      │ MCP Apps protocol
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GEOX MCP APP SHELL                                 │
│  ┌─────────────┬──────────────┬──────────────┬──────────────────┐  │
│  │ GEOX QC App │Interp. App   │Prospect App  │Governance App    │  │
│  │ Ingest      │ClaimCards    │ScenarioDelta │Approvals         │  │
│  │ Evidence    │Seismic       │Volumetrics   │Challenge Queue   │  │
│  │ QC State    │Overlays      │Risk          │Seal Audit        │  │
│  └─────────────┴──────────────┴──────────────┴──────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              GEOX REVIEW WORKBENCH (4-panel)                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │ Evidence │  │  Earth   │  │ ClaimCard│  │ Scenario │   │   │
│  │  │ Panel    │  │  Scene   │  │ + Action │  │ Delta    │   │   │
│  │  │ QC state │  │ Seismic  │  │ Rail     │  │ Low/Base │   │   │
│  │  │ Lineage  │  │ Logs     │  │ Review   │  │ /High    │   │   │
│  │  │ Proven.  │  │ Overlays │  │ Approve  │  │ Sensitiv │   │   │
│  │  │          │  │ CRS      │  │ Reject   │  │ Movement │   │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ arifOS Constitutional Gate
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GEOX LEM RUNTIME (5 existing layers)               │
│                                                                     │
│  Layer E: GOVERNED DECISION SURFACE                                 │
│  Layer D: EARTH KNOWLEDGE GRAPH                                     │
│  Layer C: LEARNED REPRESENTATIONS                                   │
│  Layer B: DETERMINISTIC PHYSICS ENGINES                             │
│  Layer A: RAW WITNESS                                               │
│                                                                     │
│  Claim Engine ─── Visual Engine ─── Agent Surfaces (MCP tools)      │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA INFRASTRUCTURE                                │
│  Postgres │ Qdrant │ FalkorDB │ VAULT999 │ Object Store              │
└─────────────────────────────────────────────────────────────────────┘
```

### Architecture Law

```
Chat proposes.
     ↓
ClaimCard structures.
     ↓
ScenePacket locates.
     ↓
EvidencePack grounds.
     ↓
ScenarioDelta tests.
     ↓
Human reviews.
     ↓
SealAction authorizes.
     ↓
AuthorityReceipt records.
```

This is the **Agentic Earth Loop** — the constitutional cycle for every earth intelligence decision.

---

## 2. The Eight Product Primitives

### 2.0 ClaimCard State Machine

Every ClaimCard follows a governed state machine with 9 states and 8 transitions.

Canonical definition: `contracts/claim_state_machine.yaml`

```
     ┌─────────┐
     │  DRAFT  │
     └────┬────┘
          │ EvidencePack linked or NO_VALID_EVIDENCE declared
          ▼
   ┌──────────────┐
   │ AI_INFERRED  │
   └──────┬───────┘
          │ Human opens review session
          ▼
    ┌───────────────┐
    │ REVIEW_PENDING │◄──────────────────┐
    └───┬───┬───┬───┘                    │
        │   │   │                        │
   QC   │   │   │ Approve                │
   fail │   │   ▼                        │
        │   │  ┌──────────────────────┐  │
        │   │  │ APPROVED_INTERPRET.  │  │
        │   │  └──────────┬───────────┘  │
        │   │             │ ack_irrev.   │
        │   │             ▼              │
        │   │       ┌──────────┐         │
        │   │       │  SEALED  │         │
        │   │       └────┬─────┘         │
        │   │            │ F13 override  │
        │   │            ▼               │
        │   │       ┌──────────┐         │
        │   │       │ REVOKED  │         │
        │   │       └──────────┘         │
        │   │                            │
        │   ▼                            │
   ┌────┴──────────┐                     │
   │ NEEDS_EVIDENCE│─────────────────────┘
   └───────┬───────┘
           │
           ▼
   ┌──────────────┐
   │  CHALLENGED  │──────────────────────┘
   └──────┬───────┘
          │
          ▼
    ┌──────────┐
    │ REJECTED │  ← Terminal state (can return to DRAFT)
    └──────────┘
```

**Transition rules (from `contracts/claim_state_machine.yaml`):**

| From | To | Condition | Error on fail |
|------|----|-----------|---------------|
| DRAFT | AI_INFERRED | EvidencePack linked or NO_VALID_EVIDENCE declared | HOLD_EVIDENCE_REQUIRED |
| AI_INFERRED | REVIEW_PENDING | Human opens review session | HOLD_IDENTITY_REQUIRED |
| REVIEW_PENDING | NEEDS_EVIDENCE | Evidence QC failed or contradictions found | HOLD_EVIDENCE_REQUIRED |
| REVIEW_PENDING | CHALLENGED | Alternatives exist, reviewer flags dispute | — |
| REVIEW_PENDING | APPROVED_INTERPRETATION | Reviewer approves, all gates pass | HOLD_HUMAN_REVIEW_REQUIRED |
| APPROVED_INTERPRETATION | SEALED | ack_irreversible=true AND policy permits | HOLD_SEAL_NOT_PERMITTED |
| SEALED | REVOKED | F13 SOVEREIGN override with justification | HOLD_REVOKE_NOT_PERMITTED |
| ANY | REJECTED | Claim invalidated or withdrawn | — |

**Blocking rule:** A claim SHALL NOT advance beyond DRAFT or AI_INFERRED if EvidencePack is in `NO_VALID_EVIDENCE` or `QC_FAILED` state.

**Structured error codes:**

| Code | Severity | Meaning |
|------|----------|---------|
| HOLD_IDENTITY_REQUIRED | critical | Missing actor/session identity |
| HOLD_SCOPE_REQUIRED | critical | Missing asset/basin/lease scope |
| HOLD_EVIDENCE_REQUIRED | critical | Claim lacks valid EvidencePack |
| HOLD_QC_FAILED | high | Evidence exists but failed QC |
| HOLD_CRS_PROOF_REQUIRED | high | Spatial claim lacks verifiable CRS |
| HOLD_HUMAN_REVIEW_REQUIRED | critical | Action exceeds autonomous boundary |
| HOLD_SEAL_NOT_PERMITTED | critical | Seal policy denied |

### 2.1 ClaimCard
**Purpose:** The atomic unit of governed geological truth. Every assertion about Earth is a ClaimCard.

```yaml
spec_version: geox-claimcard/v1
card_id: uuid
claim_text: "Channel sand at 2.5s TWT, Malay Basin"
claim_type: horizon          # horizon | fault | reservoir | seal | ...
truth_class: INTERPRETATION  # FACT | INTERPRETATION | SPECULATION
evidence_refs: ["artifact-001", "artifact-002"]
qc_status: QC_VERIFIED
location:
  crs: "EPSG:4326"
  bbox: [101.5, 2.5, 102.0, 3.0]
  depth_m: 2500
  depth_datum: MSL
uncertainty:
  p10: 2450
  p50: 2500
  p90: 2580
  epistemic_tag: INTERPRETATION
contradictions: ["artifact-003 conflicts with this pick"]
alternatives:
  - claim_text: "Incised valley fill, not channel"
    evidence_refs: ["artifact-004"]
actor_id: "arifbfazil"
session_id: "SEAL-057f7da656314775"
asset_id: "asset-malay-basin-alpha"
basin_id: "basin-malay"
discipline_role: geophysicist
ai_inferred: true
saliency_available: false
review_status: DRAFT          # DRAFT | IN_REVIEW | APPROVED | REJECTED | SEALED | VOID
seal_status: UNSEALED        # UNSEALED | SEALED | REVERTED
reversible: true
```

**Rendering on MCP Apps:**
- `claim_text` → bold header
- `truth_class` → badge (FACT=green, INTERPRETATION=amber, SPECULATION=red)
- `qc_status` → icon (✅ QC_VERIFIED, ❌ QC_FAILED, ⚠️ NO_VALID_EVIDENCE)
- `ai_inferred` → `[AI_INFERRED]` tag if true
- `saliency_available` → saliency overlay link OR "NO_SALIENCY_AVAILABLE" badge
- `review_status` → coloured border (DRAFT=grey, IN_REVIEW=blue, APPROVED=green, REJECTED=red, SEALED=gold)
- `uncertainty` → uncertainty bar P10–P50–P90
- `alternatives` → collapsible list

### 2.2 EvidencePack
**Purpose:** The complete grounded support bundle for a ClaimCard. Every claim in REVIEW_PENDING or above MUST reference an EvidencePack.

Canonical schema: `contracts/schemas/evidence_pack.json`
**Design law:** No claim without evidence. No evidence without provenance. No provenance without artifact hash.

```yaml
spec_version: geox-evidencepack/v1
evidence_pack_id: "550e8400-e29b-41d4-a716-446655440002"
claim_card_id: "550e8400-e29b-41d4-a716-446655440001"
evidence_refs: ["artifact-001", "artifact-002"]
qc_state: QC_VERIFIED
provenance:
  source_systems:
    - "GEOX:geox_data_ingest_bundle"
    - "GEOX:geox_data_qc_bundle"
  tool_versions:
    geox_data_ingest_bundle: "v2026.06.05"
    geox_data_qc_bundle: "v2026.06.05"
  processing_lineage:
    - "1. LAS ingested from file:///data/geox_las/A-1.las"
    - "2. Header QC: score 5/5 (UWI, location, datum, depth unit all valid)"
    - "3. Depth QC: monotonicity PASS, step consistency PASS"
    - "4. Curve QC: GR, RHOB, NPHI, RT all within canonical ranges"
  extraction_steps:
    - "LAS curves extracted at 0.5m sample rate"
    - "Depth converted from MD to TVDSS using deviation survey"
artifact_manifest:
  - artifact_ref: "artifact-001"
    artifact_type: LAS
    source_type: well_log
    well_id: "A-1"
    curves: ["GR", "RHOB", "NPHI", "RT"]
    qc_status: QC_VERIFIED
    depth_range_m: [2000.0, 3000.0]
    depth_datum: MSL
  - artifact_ref: "artifact-002"
    artifact_type: SEG-Y
    source_type: seismic
    survey_id: "MAL_3D"
    qc_status: QC_VERIFIED
spatial_context:
  asset_id: "asset-malay-basin-alpha"
  basin_id: "basin-malay"
  crs: "EPSG:4326"
  depth_datum: MSL
quality_notes:
  - severity: INFO
    message: "All curves within canonical ranges"
    source: "geox_data_qc_bundle:curves"
confidence_notes:
  - "DT log gap below 2500m — sonic porosity is interpolated below this depth"
limitations:
  - "No checkshot available — time-depth conversion uses regional proxy"
  - "DT log gap below 2500m — porosity uncertainty increases below this depth"
generated_by:
  tool_name: "geox_data_qc_bundle"
  workflow_path: "ingest → header QC → depth QC → curve QC → completeness check"
generated_at: "2026-06-15T01:53:00+08:00"
```

**Rendering:**
- Collapsible tree: artifact → well/survey → curves → QC state
- Each node links to the original artifact in the Evidence Panel
- Key: green = QC_VERIFIED, amber = QC_PENDING, red = QC_FAILED

### 2.3 ScenePacket
**Purpose:** Spatial/visual context for a claim. Every location-based claim has a ScenePacket.

```yaml
spec_version: geox-scenepacket/v1
scene_id: uuid
claim_card_id: uuid
bbox: [101.5, 2.5, 102.0, 3.0]
crs: "EPSG:4326"
crs_proof:
  source_crs: "EPSG:3168"
  target_crs: "EPSG:4326"
  roundtrip_passed: true
  roundtrip_max_error_m: 0.000168
  depth_datum: KB
seismic_section:
  - survey: "MAL_3D"
    inline: 1200
    twt_range_ms: [1500, 3000]
    attribute: amplitude
log_tracks:
  - well_id: "A-1"
    curves: ["GR", "RHOB", "NPHI"]
    depth_range_m: [2000, 3000]
overlays:
  - type: horizon_pick
    label: "Top Reservoir"
    depth_m: 2450
    confidence: 0.85
    ai_inferred: true
viewport_state:
  zoom: 1.0
  center: [101.75, 2.75]
  orientation: inline
```

**Rendering:**
- Seismic section with well log overlay
- AI picks as dashed lines with confidence bands
- CRS_PROOF_PACKET as footer tag (green if passed, red if failed)

### 2.4 InterpretationDiff
**Purpose:** Every state change is a diff, not a snapshot.

```yaml
spec_version: geox-interpretation-diff/v1
diff_id: uuid
claim_card_id: uuid
before:
  pick_depth_m: 2460
  confidence: 0.70
  author: "ai_agent"
after:
  pick_depth_m: 2450
  confidence: 0.85
  author: "arifbfazil"
deltas:
  - parameter: "Top Reservoir depth"
    change_m: -10
    impact: "Gross sand +8m, OWC unchanged"
  - parameter: "Net pay"
    change_m: +5
    impact: "STOIIP +5%"
sensitivity:
  - parameter: "OWC ±10m"
    stoiip_impact_pct: [-15, +18]
status: superseded
superseded_by: "diff-002"
```

**Rendering:**
- Side-by-side: before (grey) / after (coloured)
- Delta arrows: up green, down red
- Sensitivity tornado mini-chart

### 2.5 ScenarioDelta
**Purpose:** Maps consequence of accepting a claim. From interpretation to business impact.

```yaml
spec_version: geox-scenario-delta/v1
scenario_id: uuid
claim_card_id: uuid
base_case:
  stoiip_mmbo: 120
  giip_bcf: 850
  pos: 0.45
  npv_musd: 340
low_case:
  stoiip_mmbo: 85
  giip_bcf: 600
  pos: 0.30
  npv_musd: 180
high_case:
  stoiip_mmbo: 170
  giip_bcf: 1100
  pos: 0.60
  npv_musd: 520
sensitivity_ranking:
  - parameter: "Net pay"
    impact: HIGH
    range_m: [12, 34]
  - parameter: "Porosity"
    impact: MEDIUM
    range: [0.18, 0.26]
  - parameter: "OWC depth"
    impact: HIGH
    range_m: [2510, 2530]
decision_impact:
  - "If scenario accepted: well location moves 200m east"
  - "If scenario accepted: casing program changes from 7\" to 9-5/8\""
  - "If rejected: maintain current model, defer well by 6 months"
```

**Rendering:**
- Table: Base | Low | High with % movement arrows
- Sensitivity tornado bar chart
- Decision impact list (bullet points)

### 2.6 ReviewAction
**Purpose:** Human sovereignty over every claim. The act of review is a first-class object.

```yaml
spec_version: geox-review-action/v1
action_id: uuid
claim_card_id: uuid
action: approve_as_interpretation  # reject | request_evidence | approve | seal | export
actor_id: "arifbfazil"
session_id: "SEAL-057f7da656314775"
lease_id: "lease-malay-basin-2026"
notes: "Pick consistent with offset well A-2. QC verified. Approve as interpretation."
evidence_checked: ["artifact-001", "artifact-002"]
alternatives_reviewed: ["Incised valley fill hypothesis rejected — no amplitude support"]
irreversible_ack: false  # must be true for seal
timestamp: "2026-06-15T01:53:00+08:00"
```

**Rendering:**
- Action buttons: [Reject] [Request Evidence] [Approve as Interpretation] [Seal] [Export]
- Seal button requires irreversible acknowledgement checkbox + confirmation dialog
- All actions emit an AuthorityReceipt

### 2.7 AuthorityReceipt
**Purpose:** Immutable record of who authorized what, when, under which policy.

```yaml
spec_version: geox-authority-receipt/v1
receipt_id: uuid
claim_card_id: uuid
review_action_id: uuid
actor_id: "arifbfazil"
session_id: "SEAL-057f7da656314775"
lease_id: "lease-malay-basin-2026"
asset_id: "asset-malay-basin-alpha"
basin_id: "basin-malay"
policy_result: APPROVED  # APPROVED | REJECTED | HELD | SEALED
policy_reason: "All gates passed: evidence QC_VERIFIED, no contradictions, 
                uncertainty within threshold, human approved."
irreversible: false
vault999_ref: "VAULT999-SEAL-9823"
timestamp: "2026-06-15T01:53:00+08:00"
```

**Rendering:**
- Seal icon with vault reference
- Expandable to show full policy trace
- Links back to the original ClaimCard

---

## 3. GEOX MCP Apps Portfolio

Do not build one giant app. Build a constellation of focused MCP Apps, each mapping to a natural subsurface workflow:

| App | Primitives | Review Workbench Panel | Production readiness |
|-----|-----------|----------------------|:-------------------:|
| **GEOX QC App** | EvidencePack | Evidence Panel | Internal alpha (70) |
| **GEOX Interpretation App** | ClaimCard, ScenePacket, InterpretationDiff | Earth Scene + ClaimCard | Prototype (45) |
| **GEOX Prospect Review App** | ScenarioDelta, ClaimCard, ReviewAction | Scenario Delta + ClaimCard | Prototype (35) |
| **GEOX CRS & Scene App** | ScenePacket, CRS_PROOF_PACKET | Earth Scene | Internal alpha (55) |
| **GEOX Governance App** | ReviewAction, AuthorityReceipt | Action Rail | Not ready (30) |
| **GEOX Basin Console** | All | Dashboard | Not ready (25) |

### App Architecture (each app)

```
MCP App Manifest
  ├── app_id, version, asset scope
  ├── required primitives (ClaimCard, ScenePacket, etc.)
  ├── required evidence types
  ├── safety tier
  ├── human_review_required
  └── reversible flag

MCP App Transition Handlers
  ├── on_claim_create    → ClaimCard
  ├── on_evidence_attach → EvidencePack
  ├── on_scene_load      → ScenePacket
  ├── on_diff            → InterpretationDiff
  ├── on_scenario_run    → ScenarioDelta
  ├── on_review          → ReviewAction
  └── on_seal            → AuthorityReceipt + VAULT999 write
```

---

## 4. GEOX Review Workbench — The 4-Panel Layout

### Panel 1: Evidence (Left, 25% width)

```
┌─────────────────────────┐
│  EVIDENCE               │
│                         │
│  ┌─ Artifact: A-1 LAS ─┐│
│  │ ✅ QC_VERIFIED      ││
│  │ GR, RHOB, NPHI, RT  ││
│  │ 2000-3000m MD       ││
│  └─────────────────────┘│
│  ┌─ Artifact: MAL_3D ──┐│
│  │ ✅ QC_VERIFIED      ││
│  │ Amplitude attribute ││
│  │ Inline 1200         ││
│  └─────────────────────┘│
│  ┌─ Limitations ───────┐│
│  │ ⚠️ DT gap <2500m   ││
│  │ ⚠️ No checkshot    ││
│  └─────────────────────┘│
│                         │
│  [Add Evidence]         │
└─────────────────────────┘
```

**Properties:**
- Scrollable artifact list
- Colour-coded QC state
- Click-to-expand provenance chain
- "Missing Evidence" section with warnings

### Panel 2: Earth Scene (Center, 50% width)

```
┌────────────────────────────────────────┐
│  EARTH SCENE                            │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │                                  │  │
│  │   SEISMIC SECTION + LOG OVERLAY  │  │
│  │   ────────────────               │  │
│  │   AI pick (dashed) ─ ─ ─ ─ ─    │  │
│  │   Human pick (solid) ─────────   │  │
│  │   Confidence band ░░░░░░░░░      │  │
│  │                                  │  │
│  └──────────────────────────────────┘  │
│                                         │
│  CRS: EPSG:4326 │ DZ: MSL │ ✅ Stable │
│  [Zoom] [Pan] [Inline/Xline/Depth]     │
└────────────────────────────────────────┘
```

**Properties:**
- Multi-modal (seismic + logs + map + section)
- Overlay toggle: AI picks, human picks, confidence bands
- CRS_PROOF_PACKET as footer
- Viewport state preserved across transitions

### Panel 3: ClaimCard + Action Rail (Right, 25% width)

```
┌─────────────────────────┐
│  CLAIM CARD             │
│                         │
│  "Channel sand at       │
│   2.5s TWT, Malay B."   │
│                         │
│  [INTERPRETATION] [AI]  │
│  Uncertainty: ███░░░    │
│  P10: 2450  P50: 2500   │
│  P90: 2580              │
│                         │
│  Contradictions (1):    │
│  ┌─ Artifact-003 ─────┐│
│  │ Conflicts at 2.48s ││
│  └────────────────────┘│
│                         │
│  Alternatives (1):      │
│  ▼ Incised valley fill  │
│                         │
│  [Reject] [Req Evid]    │
│  [Approve] [Seal]       │
│  [Export Pack]          │
└─────────────────────────┘
```

**Properties:**
- ClaimCard rendered per schema
- Action buttons with appropriate gates:
  - Seal requires irreversible acknowledgement
  - Reject requires reason
  - Request Evidence opens Evidence Panel
- "Seal" button only active when all mandatory gates pass

### Panel 4: Scenario Delta (Bottom, collapsible)

```
┌────────────────────────────────────────────────────────┐
│  SCENARIO DELTA                  ▲ Collapse            │
│                                                         │
│  ┌──────────┬─────────┬─────────┬──────────────────┐  │
│  │ Parameter│  Base   │  Low    │  High            │  │
│  ├──────────┼─────────┼─────────┼──────────────────┤  │
│  │ STOIIP   │ 120 MMbbl│ 85     │ 170 ▲42%        │  │
│  │ GIIP     │ 850 Bcf │ 600     │ 1100 ▲29%       │  │
│  │ POS      │ 0.45    │ 0.30    │ 0.60 ▲33%       │  │
│  │ NPV      │ $340M   │ $180M   │ $520M ▲53%      │  │
│  └──────────┴─────────┴─────────┴──────────────────┘  │
│                                                         │
│  Sensitivity: Net pay ████████░░ (HIGH)                │
│               Porosity ████░░░░░░ (MEDIUM)             │
│               OWC      ████████░░ (HIGH)               │
│                                                         │
│  Decision impact:                                        │
│  • Well location moves 200m east if accepted            │
│  • Casing program changes from 7\" to 9-5/8\"          │
│  • Defer 6 months if rejected                           │
└────────────────────────────────────────────────────────┘
```

**Properties:**
- Collapsible by default
- Color-coded movement arrows
- Sensitivity tornado bar chart
- Decision impact as bullet list
- Links to full ScenarioDelta engine

---

## 5. The Agentic Earth Loop

The constitutional cycle for every earth intelligence decision:

```
STEP 1: CHAT PROPOSES
  Agent (or human) forms intent:
  "Interpret the top reservoir in Malay Basin well A-1"
  → Routes to GEOX Interpretation App

STEP 2: CLAIMCARD STRUCTURES
  GEOX produces a ClaimCard:
  claim_text, claim_type, truth_class, uncertainty
  → Renders in ClaimCard Panel

STEP 3: SCENEPACKET LOCATES
  GEOX loads seismic section + well logs:
  bbox, CRS_PROOF_PACKET, overlays, viewport
  → Renders in Earth Scene Panel

STEP 4: EVIDENCEPACK GROUNDS
  GEOX assembles evidence chain:
  artifact refs, QC state, provenance, limitations
  → Renders in Evidence Panel

STEP 5: SCENARIODELTA TESTS
  GEOX runs consequence analysis:
  low/base/high, sensitivity, decision impact
  → Renders in Scenario Delta Panel

STEP 6: HUMAN REVIEWS
  Geoscientist inspects all four panels:
  checks evidence, evaluates alternatives, reviews deltas
  → Clicks [Approve] or [Reject] or [Request Evidence]

STEP 7: SEALACTION AUTHORIZES
  If approved, ReviewAction + irreversible acknowledgement:
  → ClaimCard review_status = APPROVED or SEALED

STEP 8: AUTHORITYRECEIPT RECORDS
  VAULT999 seal:
  actor_id, session_id, lease_id, asset_id, timestamp, policy_result
  → Immutable record in VAULT999
```

### Loop Invariants

- **No step can be skipped.** Chat → Card → Scene → Evidence → Scenario → Review → Seal → Receipt.
- **Each step produces a first-class object.** The chain is traversable backwards.
- **Human can exit at any step.** Reject at Step 6 produces a receipt. Request evidence loops back to Step 4.
- **Every loop emits an AuthorityReceipt.** Even rejection.

---

## 6. Design Doctrine for GEOX MCP UI

| Law | Meaning | Fiqh |
|-----|---------|:----:|
| **Spatial first, not chat first** | The Earth Scene panel is the primary interface. Chat is supportive. | Wajib |
| **Evidence first, not answer first** | Evidence Panel loads before ClaimCard is trusted. | Wajib |
| **Diffs first, not snapshots** | InterpretationDiff before absolute values. | Wajib |
| **Alternatives first, not single truth** | Contradictions and alternatives always visible. | Wajib |
| **Approval first for irreversible** | Seal requires explicit human action. | Wajib |
| **Identity always visible** | Actor name/badge in every panel header. | Wajib |
| **CRS always explicit** | CRS_PROOF_PACKET in Scene footer. | Wajib |
| **Confidence always bounded** | No bare confidence number. Always P10/P50/P90 + epistemic tag. | Wajib |
| **Human veto always final** | Reject/Approve/Seal buttons are real gates. | **Haram to bypass** |

---

## 7. GEOX MCP Apps Manifest Schema

Every GEOX MCP App MUST declare:

```yaml
app_id: geox-interpretation-app
app_version: v0.1
scope:
  asset_id: "asset-malay-basin-alpha"
  basin_id: "basin-malay"
  disciplines: [geophysics, geology]
primitives:
  - ClaimCard
  - ScenePacket
  - InterpretationDiff
  - EvidencePack
  - ReviewAction
evidence_required: [LAS, SEG-Y, tops, checkshot]
safety_tier: Tier 1 (design-only)
human_review_required: true
mutation_allowed: false
ops_touch_allowed: false
reversible: true
panels:
  - evidence
  - earth_scene
  - claim_card
  - scenario_delta
transition_handlers:
  on_claim_create: return ClaimCard
  on_evidence_attach: update EvidencePack
  on_scene_load: return ScenePacket
  on_review: return ReviewAction → AuthorityReceipt
```

---

## 8. Build Priorities (extends Readiness Spec v0.2 §6)

| Priority | What | Primitives | Panels | Fiqh |
|:--------:|------|-----------|--------|:----:|
| **P0** | Identity propagation + Invocation Envelope | AuthorityReceipt (partial) | — | **Wajib** |
| **P1** | ClaimCard schema + state machine + renderer | ClaimCard | ClaimCard Panel | **Wajib** |
| **P2** | EvidencePack schema + assembly workflow | EvidencePack | Evidence Panel | **Wajib** |
| **P3** | ScenePacket with CRS_PROOF_PACKET | ScenePacket | Earth Scene Panel | **Wajib** |
| **P4** | ReviewAction + seal flow | ReviewAction, AuthorityReceipt | Action Rail | **Wajib** |
| **P5** | ScenarioDelta engine | ScenarioDelta | Scenario Delta Panel | Sunat |
| **P6** | InterpretationDiff | InterpretationDiff | Diff overlay on Scene | Sunat |
| **P7** | Full 4-panel Workbench v0 | All primitives integrated | All panels integrated | **Wajib** |

---

## 9. Dimensional Alignment with Existing LEM

| LEM Layer | Existing | MCP Apps Extension |
|-----------|----------|-------------------|
| **Layer A: Raw Witness** | Artifact store, QC, ingest | EvidencePack primitives. Evidence Panel in Workbench |
| **Layer B: Physics Engines** | Petrophysics, seismic, volumetrics | ScenarioDelta primitives. Parameter perturbation via App UI |
| **Layer C: Learned Reps** | VQ tokens, embeddings | ClaimCard `ai_inferred` flag. Saliency attribution in Scene Panel |
| **Layer D: Knowledge Graph** | Entities, relations, contradictions | ClaimCard `contradictions` list. Graph traversal in Evidence Panel |
| **Layer E: Decision Surface** | ACRisk, HOLD/SEAL/VOID | ReviewAction + AuthorityReceipt. Seal Panel integrates with VAULT999 |
| **Claim Engine** | Create, validate, challenge, seal | ClaimCard is the MCP Apps surface for the entire Claim Engine |
| **Visual Engine** | Map, section, cube, overlay | ScenePacket is the MCP Apps surface for the Visual Engine |
| **Agent Surfaces** | MCP 40 tools, OpenAPI, OGC, A2A | **NEW:** GEOX MCP App Shell + Review Workbench on top |

---

## 10. Final Doctrine

```
GEOX is not an AI assistant for geologists.
GEOX is a truth-forging system for the subsurface.

MCP Apps are not decoration.
MCP Apps are the vessel for human-earth-agent alignment.

The Large Earth Model is not just model weights.
It is evidence, ontology, simulation, governance, and interface
fused into one constitutional stack.

The winning interface is not "ask Earth anything."
The winning interface is:
  "Show me the claim, the evidence, the alternatives,
   the consequence, and the seal."
```

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
