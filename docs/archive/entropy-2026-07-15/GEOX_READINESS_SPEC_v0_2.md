# GEOX Readiness Specification v0.2 — ClaimCard + CRS Proof Packet + Invocation Envelope

> **DITEMPA BUKAN DIBERI** — Forged, Not Given
>
> Extends v0.1 with three new primitives: ClaimCard, CRS_PROOF_PACKET, and GEOX Invocation Envelope.

**Author:** Muhammad Arif bin Fazil (F13 SOVEREIGN) + FORGE (000Ω)  
**Canonical location:** `geox/docs/GEOX_READINESS_SPEC_v0_2.md`  
**Status:** SEALED (2026-06-15)  
**Supersedes:** v0.1 (§7.2 decision rules updated; §8, §9, §10 added)  
**Next review:** 2026-07-15

---

## 1. Purpose

v0.1 established the five-layer readiness model, mandatory gates, and Review Workbench specification. v0.2 adds:

1. **ClaimCard** — the atomic UI object for governed geology on MCP.
2. **CRS_PROOF_PACKET** — the verifiable geospatial safety record.
3. **GEOX Invocation Envelope** — the universal identity + context wrapper for all tool calls.

These three primitives complete the architecture that v0.1 started: every geological claim becomes a visual, reviewable, reversible object; every coordinate carries proof; every action is attributable.

---

## 2. ClaimCard — The Atomic GEOX UI Object

### 2.1 Definition

A **ClaimCard** is the minimum displayable unit of governed geological truth on MCP Apps. It is the GEOX equivalent of a "card" in a social feed — but for subsurface authority.

**Design law:** The unit of product is NOT "chat answer." The unit of product is `ClaimCard`.

### 2.2 Schema

```yaml
ClaimCard:
  spec_version: geox-claimcard/v1

  # Identity
  card_id: uuid                          # Unique card identifier
  claim_text: string                     # Natural language claim (e.g. "Channel sand at 2.5s TWT")
  claim_type: horizon | fault | trap | reservoir | seal | charge | source | 
               temperature | pressure | fluid_contact | net_pay | permeability |
               porosity | saturation | thickness | depth | structure | stratigraphy |
               lithology | facies | environment | sequence | other
  truth_class: FACT | INTERPRETATION | SPECULATION

  # Evidence
  evidence_refs: string[]                # Artifact IDs supporting this claim
  qc_status: RAW | INGESTED | QC_PENDING | QC_VERIFIED | QC_FAILED | 
             NO_VALID_EVIDENCE | ARTIFACT_MISSING

  # Spatial
  location:
    crs: string                          # e.g. "EPSG:4326"
    bbox: [float, float, float, float]   # [min_lon, min_lat, max_lon, max_lat]
    depth_m: float | null
    depth_datum: KB | MSL | DF | unknown

  # Uncertainty
  uncertainty:
    p10: float | null
    p50: float | null
    p90: float | null
    distribution: lognormal | normal | triangular | null
    epistemic_tag: CLAIM | PLAUSIBLE | HYPOTHESIS | ESTIMATE | UNKNOWN

  # Contradictions & alternatives
  contradictions: string[]               # Contradicting evidence refs
  alternatives:                          # Alternative interpretations
    - claim_text: string
      evidence_refs: string[]
      uncertainty: ...
  
  # Provenance
  actor_id: string
  session_id: string
  lease_id: string | null
  asset_id: string | null
  basin_id: string | null
  discipline_role: geophysicist | petrophysicist | reservoir_engineer | 
                   drilling_engineer | geologist | reviewer | ai_agent
  
  # AI metadata
  ai_inferred: boolean                   # True if any AI system produced this claim
  saliency_available: boolean            # True if attention/saliency map exists
  saliency_uri: string | null            # Resource URI for saliency overlay

  # Governance
  review_status: DRAFT | IN_REVIEW | APPROVED | REJECTED | SEALED | VOID
  seal_status: UNSEALED | SEALED | REVERTED
  reversible: boolean
  
  # Timestamps
  created_at: datetime
  reviewed_at: datetime | null
  sealed_at: datetime | null
```

### 2.3 Required vs Optional Fields

| Class | Fields | Rule |
|-------|--------|------|
| **Always required** | `card_id`, `claim_text`, `claim_type`, `truth_class`, `evidence_refs` (or empty with flag), `actor_id`, `session_id`, `review_status`, `created_at` | Wajib |
| **Spatial required** | `location.crs`, `location.depth_datum` | Wajib when spatial context applies |
| **AI required** | `ai_inferred`, `saliency_available` | Wajib when AI involved |
| **Optional** | `uncertainty.*`, `contradictions`, `alternatives`, `saliency_uri`, `lease_id` | Sunat |

### 2.4 Rendering Rules on MCP Apps

| Field | Render as | If missing |
|-------|-----------|------------|
| `claim_text` | Bold header | Block card |
| `truth_class` | Badge: FACT (green), INTERPRETATION (amber), SPECULATION (red) | Default SPECULATION |
| `qc_status` | Icon + label: ✅ QC_VERIFIED, ❌ QC_FAILED, ⚠️ NO_VALID_EVIDENCE | Show "QC unknown" |
| `ai_inferred` | `[AI_INFERRED]` tag if true | Hide if false |
| `saliency_available` | "Saliency available" link or "NO_SALIENCY_AVAILABLE" badge | Show NO_SALIENCY_AVAILABLE |
| `review_status` | Colored border: DRAFT (grey), IN_REVIEW (blue), APPROVED (green), REJECTED (red), SEALED (gold) | Default DRAFT |
| `evidence_refs` | Clickable list — each opens evidence panel | Show "No evidence references" |
| `uncertainty` | Uncertainty bar: P10–P50–P90 range | Hide section |
| `alternatives` | Collapsible "Alternative interpretations" | Hide section |

---

## 3. CRS_PROOF_PACKET

### 3.1 Definition

A **CRS_PROOF_PACKET** is a verifiable record that a coordinate transformation happened correctly. It must accompany every CRS-bearing operation in production mode.

**Design law:** No CRS without proof. No free-text coordinates. No mixing depth datum with horizontal CRS.

### 3.2 Schema

```yaml
CRSProofPacket:
  spec_version: geox-crs-proof/v1

  # Source
  source_crs: string                     # e.g. "EPSG:3168"
  source_crs_name: string                # e.g. "Kertau (Malay Peninsula)"
  source_crs_type: geographic | projected
  source_crs_unit: string                # e.g. "metre", "Clark's foot", "degree"

  # Target (canonical)
  target_crs: string                     # "EPSG:4326"
  target_crs_name: string                # "WGS84"
  target_crs_type: geographic

  # Depth datum (separate from horizontal CRS)
  depth_datum: KB | MSL | DF | unknown | null

  # Axis order
  axis_order: (x,y) | (y,x) | (easting,northing) | (latitude,longitude)

  # Transform
  transform_method: string               # e.g. "pyproj.Transformer.from_crs"
  pyproj_version: string
  proj_version: string | null

  # Validation
  roundtrip_samples: int                 # Number of test points
  roundtrip_max_error_m: float           # Maximum deviation in metres
  roundtrip_avg_error_m: float           # Average deviation
  roundtrip_passed: boolean              # true if max_error <= tolerance

  # Provenance
  transformed_by: string                 # tool_name or actor_id
  timestamp: datetime
  confidence: CONTROLLED | APPROXIMATE | UNKNOWN
```

### 3.3 Hard gates

| Condition | Action |
|-----------|--------|
| `source_crs` is "unknown" or null | Flag WARNING, do not block in sandbox |
| `source_crs` is "unknown" in production mode | **BLOCK** — HOLD_IDENTITY_REQUIRED-style gate |
| `roundtrip_passed` is false | **BLOCK** — transformation may be corrupt |
| `depth_datum` is null and data is subsurface | Flag WARNING — depth reference ambiguous |

---

## 4. GEOX Invocation Envelope

### 4.1 Definition

Every GEOX tool call in production mode **MUST** carry a standardized invocation envelope that propagates identity, context, and authority scope through the entire call chain: MCP Host → App Shell → Tool Surface → Artifact Store → Vault Seal.

**Design law:** No anonymous geology. No unknown tool_name. No state change without attribution.

### 4.2 Schema

```yaml
GEOXInvocationEnvelope:
  spec_version: geox-invocation/v1

  # Identity (from arifOS session_init)
  session_id: string                      # SEAL-xxxxxxxxxxx
  actor_id: string                        # e.g. "arifbfazil"
  actor_role: geophysicist | petrophysicist | reservoir_engineer |
              drilling_engineer | geologist | reviewer | ai_agent

  # Context
  lease_id: string | null                 # e.g. "lease-malay-basin-2026"
  asset_id: string | null                 # e.g. "asset-malay-basin-a"
  basin_id: string | null                 # e.g. "basin-malay"
  discipline: geology | geophysics | petrophysics | reservoir | drilling | completion

  # Tool
  tool_name: string                       # MUST match registered canonical name
  tool_version: string                    # e.g. "v2026.06.05"

  # Trace
  trace_id: string                        # uuid for end-to-end tracing
  parent_trace_id: string | null
  invocation_timestamp: datetime

  # Authority
  authority_scope: READONLY | C1_ADVISORY | C2_EXECUTE | IRREVERSIBLE
  mutation_allowed: boolean
  ops_touch_allowed: boolean
  human_review_required: boolean
```

### 4.3 Propagation Rules

| Layer | Must propagate | Gate if missing |
|-------|---------------|-----------------|
| MCP Host → App Shell | `session_id`, `actor_id`, `trace_id` | Not applicable — host responsibility |
| App Shell → Tool | Full envelope | **BLOCK** — missing identity |
| Tool → Artifact Store | `session_id`, `actor_id`, `trace_id`, `tool_name` | Flag WARNING — attribution gap |
| Tool → Vault Seal | Full envelope + evidence_refs | **BLOCK** — G5 mandatory gate |
| App Shell → Review Workbench | Full envelope + ClaimCard | **BLOCK** — cannot render unattributed card |

### 4.4 Combined Example

```json
{
  "invocation": {
    "spec_version": "geox-invocation/v1",
    "session_id": "SEAL-057f7da656314775",
    "actor_id": "arifbfazil",
    "actor_role": "geophysicist",
    "lease_id": "lease-malay-basin-2026",
    "asset_id": "asset-malay-basin-alpha",
    "basin_id": "basin-malay",
    "discipline": "geophysics",
    "tool_name": "geox_horizon_contrast_surface",
    "tool_version": "v2026.06.05",
    "trace_id": "trace-a1b2c3d4e5f6",
    "parent_trace_id": null,
    "invocation_timestamp": "2026-06-15T01:53:00+08:00",
    "authority_scope": "C1_ADVISORY",
    "mutation_allowed": false,
    "ops_touch_allowed": false,
    "human_review_required": true
  },
  "crsp_proof": {
    "spec_version": "geox-crs-proof/v1",
    "source_crs": "EPSG:3168",
    "target_crs": "EPSG:4326",
    "roundtrip_passed": true,
    "roundtrip_max_error_m": 0.000168,
    "depth_datum": "KB"
  },
  "claim_card": {
    "spec_version": "geox-claimcard/v1",
    "claim_text": "Channel sand at 2.5s TWT",
    "claim_type": "horizon",
    "truth_class": "INTERPRETATION",
    "evidence_refs": ["artifact-001", "artifact-002"],
    "review_status": "DRAFT",
    "ai_inferred": true,
    "saliency_available": false
  }
}
```

---

## 5. Updated Decision Rules (supersedes v0.1 §9)

The following promotion rules now incorporate the three new primitives:

| Condition | Result |
|-----------|--------|
| All previous v0.1 rules apply | — |
| **ClaimCard not implemented for any AI-derived output** | **Production authority BLOCKED** |
| **CRS_PROOF_PACKET absent for any CRS-bearing operation in production mode** | **Production authority BLOCKED** |
| **Invocation Envelope absent or partial for any state-changing action** | **Production authority BLOCKED** |
| ClaimCard implemented but missing required fields (`actor_id`, `session_id`, `evidence_refs`) | Feature-level BLOCK for that claim type |
| CRS_PROOF_PACKET implemented with `roundtrip_passed: false` | Coordinate-level HOLD — manual review required |

---

## 6. Build-Priority Mappings (extends v0.1 §10)

| Priority | Spec reference | Action | Fiqh |
|:--------:|---------------|--------|:----:|
| **P0** | §4 GEOX Invocation Envelope + v0.1 P1 | End-to-end identity and session propagation across all layers. Envelope must survive host → shell → tool → store → vault. | **Wajib** |
| **P1** | §2 ClaimCard + §7 Review Workbench | Build ClaimCard schema + Review Workbench v0. Every tool that emits a geological claim returns a ClaimCard. | **Wajib** |
| **P1.5** | §3 CRS_PROOF_PACKET | Every CRS-bearing tool emits proof packet. Reject free-text coordinates in production. | **Wajib** |
| **P2** | v0.1 A1 + A3 | App manifest enforcement for asset, basin, discipline, safety tier. | **Wajib** |
| **P3** | v0.1 C6 | Before/after diff on all reviewable model mutations. | Sunat |
| **P4** | v0.1 §8 | CI/CD readiness report emission. | Sunat |

---

## 7. Fiqh of the Three Primitives

| Primitive | Fiqh | Why |
|-----------|:----:|-----|
| ClaimCard | **Wajib** for any AI-derived claim surfaced through MCP Apps | Without it, geoscientists cannot audit, challenge, or approve claims. Governance failure. |
| CRS_PROOF_PACKET | **Wajib** for any CRS-bearing operation in production mode | Wrong CRS can shift a prospect by kilometres. Physical safety requirement. |
| GEOX Invocation Envelope | **Wajib** for every state-changing tool call in production mode | Identity is the prerequisite for all other governance. No identity = no audit. |
| ClaimCard with null `actor_id` | **Haram** | Anonymous geology is not geology. |
| Free-text coordinates without CRS | **Haram** in production mode | "100000, 200000" is meaningless without CRS context. |

---

## 8. Amendment Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-06-15 | v0.1 | Initial specification (5-layer model, gates, workbench, priorities) | Arif (F13) + FORGE (000Ω) |
| 2026-06-15 | v0.2 | Added ClaimCard (§2), CRS_PROOF_PACKET (§3), Invocation Envelope (§4). Updated decision rules, priorities, fiqh. | Arif (F13) + FORGE (000Ω) |

---

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
