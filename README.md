# GEOX — Governed Earth Intelligence

```
Physics > Narrative.
Maruah > Convenience.
DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
```

---

## What GEOX Is

**GEOX is the Earth-domain reasoning instrument of the [arifOS](https://github.com/ariffazil/arifOS) constitutional federation** — a governed geoscience coprocessor that reads subsurface evidence, maps spatial trajectories, and issues physics-verified verdicts under hard constitutional law.

It is **not** a viewer. It is **not** a feelings engine. It is a **reasoning instrument** built on the doctrine that every interpretation must be grounded in physical evidence before it can be sealed.

> *"In geology, the earth remembers everything — every sediment layer, every pressure event, every fracture. But memory without interpretation is just noise."*
> — Arif Fazil, Sovereign Architect

---

## Position in arifOS Trinity

```
ΔΩΨ — Trinity Model
├── ARIF-Δ   Human Sovereign      → F13 veto authority
├── ADAM-Ω   Constitutional Kernel → F1–F13 floors enforced
└── GEOX-Ψ   Earth Coprocessor    → This repository
```

GEOX operates as the **Ψ (Psi/Earth) node** — sensing physical reality, computing trajectory options, and routing every verdict through the arifOS constitutional layer before sealing to VAULT999.

---

## Architecture

```
ariffazil/GEOX
│
├── geox/                          # Core Python package
│   ├── __init__.py
│   ├── core/
│   │   ├── ac_risk.py            # ToAC AC_Risk calculation engine
│   │   ├── bias_detector.py      # Bond et al. (2007) cognitive bias audit
│   │   ├── epistemic_integrity.py # Posterior integrity scoring (AlphaFold pLDDT equiv)
│   │   ├── portfolio_audit.py    # Portfolio risk tracking + PoS coupling detection
│   │   ├── physics_guard.py      # Hard physics constraint enforcement
│   │   ├── governed_output.py    # ClaimTag + VAULT999 receipt builder
│   │   └── tool_registry.py      # Unified tool registry with metadata
│   ├── geox_mcp/
│   │   ├── server.py             # FastMCP server entry
│   │   ├── fastmcp_server.py    # FastMCP transport layer (15 public tools)
│   │   ├── tools/                # Tool implementations
│   │   │   ├── las_ingest_tool.py
│   │   │   ├── petro_ensemble_tool.py
│   │   │   ├── basin_charge_tool.py
│   │   │   ├── sensitivity_tool.py
│   │   │   ├── volumetrics_tool.py
│   │   │   ├── visualization.py
│   │   │   └── asset_memory_tool.py
│   │   └── adapters/
│   ├── skills/
│   │   ├── earth_science/        # Earth science skill pack
│   │   │   ├── __init__.py
│   │   │   └── seismic_wrappers.py  # segyio + bruges wrappers, ClaimTag, VAULT999
│   │   └── [12 domain skill dirs]   # atmosphere, geodesy, hazards, etc.
│   ├── telemetry/
│   │   └── geox_telemetry.py     # GEOX → arifOS metabolic heartbeat emitter
│   └── core/doctrine/
│       └── geox_core_prompt.py  # Sovereign system identity (F1–F13 compliant)
│
├── WELL/                         # Biological substrate — operator sovereignty
│   ├── server.py                # WELL cognitive pressure monitor
│   ├── vault_bridge.py           # WELL ↔ arifOS ↔ A-FORGE bridge
│   ├── gate/well_gate.py         # Constitutional gate before forge
│   └── CHARTER.md               # Operator sovereignty charter
│
├── sealkit/                      # Constitutional SEAL ritual
│   ├── seal.sh                  # Shell script SEAL ceremony
│   ├── SEAL.md                  # SEAL protocol documentation
│   └── manifest.json/.sig        # SEAL manifest + signature
│
├── services/
│   └── a2a-gateway/             # Agent-to-Agent mesh protocol
│
├── skills/                       # 12 domain skill definitions
│   ├── atmosphere/
│   ├── geodesy/
│   ├── governance/
│   ├── hazards/
│   ├── infrastructure/
│   ├── mobility/
│   ├── orchestration/
│   ├── sensing/
│   ├── subsurface/              # 6 subsurface skill domains
│   ├── terrain/
│   ├── time/
│   └── water/
│
├── geox-gui/                    # React + Cesium GUI
│   ├── dist/                   # Pre-built Cesium viewer + apps
│   └── src/
│
├── apps/                        # MCP App manifests + HTML UIs
│   ├── geox-seismic-viewer/   # First living MCP App organ
│   │   ├── manifest.json      # arifOS F1–F13 compliant app manifest
│   │   ├── mcp-app.config.json
│   │   └── public/index.html  # Interactive seismic viewer (WebGL canvas)
│   ├── well-desk/             # AAA-grade well context desk
│   ├── seismic-vision-review/  # AI fault pick scaffold
│   ├── judge-console/         # AC_Risk Console
│   └── [other MCP apps]
│
├── contracts/
│   └── mcp/                   # Canonical MCP tool contracts
│       ├── geox_ui_tool_contract.json           # Master schema for GEOX UI tools
│       └── geox_seismic_load_volume_contract.json
│
├── infra/
│   └── geox-static.yml       # Traefik config (MCP Apps plane routes)
│
├── registry/
│   └── registry.json          # 47 skills across 12 domains
│
├── docs/
│   ├── deploy.md             # Docker, Railway, Fly.io deployment
│   └── [other docs]
│
├── geox_mcp_server.py         # CLI entry point
├── fastmcp.json               # FastMCP deployment config
└── pyproject.toml             # Python package manifest
```

---

## The 13 Domains — 47 Skills

GEOX reasoning spans canonical domains across scales from site to basin:

| Domain | Substrates | Scales | Horizons |
|--------|------------|--------|----------|
| **sensing** | human, machine-fixed, orbital | site → region | immediate, short |
| **geodesy** | machine-fixed, infrastructure | site → corridor | immediate |
| **terrain** | environment-field, orbital | site → district | short, medium |
| **water** | machine-fixed, environment-field | corridor → region | medium, long |
| **atmosphere** | orbital, machine-mobile | district → nation | medium, long |
| **mobility** | machine-mobile, infrastructure | corridor → region | short, medium |
| **infrastructure** | machine-fixed, infrastructure | site → corridor | medium, long |
| **hazards** | environment-field, void | site → maritime | immediate → long |
| **governance** | human, machine-fixed | all | all |
| **time** | human, machine-fixed | all | all |
| **orchestration** | human, machine-fixed | all | all |
| **subsurface** | wireline, seismic, geochemical, thermal-history | well → basin | medium → long |

Full skill definitions: [`registry/registry.json`](registry/registry.json)

---

## MCP Apps Plane — Visual Earth Organs

GEOX MCP Apps are domain-native UI surfaces rendered via the MCP `io.modelcontextprotocol/ui` capability. Each app is launched by a tool that returns `ui: {resourceUri: "ui://..."}` — bridging the physics layer to the visual layer.

### Live MCP Apps

| App | Purpose | Launched By |
|-----|---------|-------------|
| `geox-seismic-viewer` | Interactive seismic section viewer (inline/crossline, amplitude attributes, horizon overlay) | `geox_seismic_load_volume` |
| `well-desk` | Well context desk with LAS curves, petrophysics results, AC_Risk widget | `geox_well_load_bundle` |
| `judge-console` | AC_Risk Console for ToAC calculation + verdict display | `arifos_compute_risk` |
| `seismic-vision-review` | AI-assisted fault pick review scaffold | `geox_seismic_vision_review_stub` |
| `georeference-map` | Map georeferencing plan | `geox_georeference_map` |
| `attribute-audit` | Kozeny-Carman permeability proxy audit | `geox_attribute_audit` |

### App Manifest Schema

Every GEOX MCP App carries a `manifest.json` with:

- `arifOS.required_floors`: F1–F13 enforcement
- `ui_entry.mode`: `inline-or-external`
- `events.supported`: `app.initialize`, `ui.state.sync`, `tool.request`, `tool.result`
- `auth.mode`: JWT with scoped permissions
- `vault_route`: VAULT999 immutable sealing

Apps are deployed to `/srv/mcp/apps/<appname>/dist/` and served via the Traefik `geox-mcp-apps` router on port 8081.

---

## MCP Tools

### Public Earth Tools (`geox_*`)

| Tool | Purpose | Status |
|------|---------|--------|
| `geox_compute_ac_risk` | ToAC AC_Risk calculation | **PROD** |
| `geox_prospect_evaluate` | Full prospect verdict via `_compute_ac_risk_governed` | **PROD** |
| `geox_time4d_verify_timing` | 4D trajectory temporal consistency check | **PROD** |
| `geox_load_seismic_line` | Seismic line load with F4 scale verification | **PROD** |
| `geox_build_structural_candidates` | Multi-model structural interpretation | **PROD** |
| `geox_verify_geospatial` | Coordinate + CRS grounding | **PROD** |
| `geox_feasibility_check` | Constitutional F1–F13 pre-check | **PROD** |
| `geox_earth_signals` | Live Earth observations | **PROD** |
| `geox_well_load_bundle` | Ingest LAS/DLIS well log bundles | **PROD** |
| `geox_well_compute_petrophysics` | Depth-indexed POR, Sw, Vsh curves | **PROD** |
| `geox_well_qc_logs` | QC — spike, flatline, range detection | **PROD** |
| `geox_section_interpret_strata` | Multi-well stratigraphic correlation | **PROD** |
| `geox_cross_summarize_evidence` | Causal evidence synthesis for 888_JUDGE | **PROD** |
| `geox_attribute_audit` | Kozeny-Carman permeability proxy audit | **PREVIEW** |
| `geox_seismic_load_volume` | SEG-Y volume ingest → VTF tile pyramid → geox-seismic-viewer | **PROD** |
| `geox_seismic_compute_attribute` | Compute amplitude/variance/sweetness/coherence via bruges | **PROD** |
| `geox_seismic_render_slice` | Extract inline/crossline/time slice via pyvista | **PROD** |
| `geox_seismic_vision_review` | AI fault pick scaffold | **SCAFFOLD** |
| `geox_georeference_map` | Map georeferencing plan | **SCAFFOLD** |
| `geox_analog_digitizer` | Analog log → structured curve | **SCAFFOLD** |

### arifOS Governance Tools (`arifos_*`)

| Tool | Purpose |
|------|---------|
| `arifos_check_hold` | 888 HOLD authority check |
| `arifos_compute_risk` | ToAC AC_Risk score |
| `arifos_judge_prospect` | Full verdict — routes to VAULT999 |

### MCP Resource URIs

| URI | Returns |
|-----|---------|
| `geox://health` | Server health + `io.modelcontextprotocol/ui` capability advertisement |
| `geox://capabilities` | Full GEOX tool + app + arifOS integration manifest |
| `geox://registry` | Full skill registry |
| `ui://geox_seismic_viewer` | geox-seismic-viewer HTML |
| `ui://ac_risk` | AC_Risk Console HTML |
| `ui://seismic_vision_review` | Seismic Vision Review HTML |

---

## Earth Science Stack — Skill Packs

GEOX exposes open-source geoscience libraries via governed skill pack wrappers in `geox/skills/earth_science/`.

### Installed Libraries (`requirements-earth.txt`)

| Library | Purpose |
|---------|---------|
| `segyio` | SEG-Y binary I/O for seismic volumes |
| `bruges` | Seismic attributes (amplitude, variance, sweetness, coherence, envelope, freq_avg) |
| `welly` | Well log analysis and multi-well correlation |
| `lasio` | LAS file reading (LAS 2.0/3.0) |
| `gempy` | Implicit 3D geological modeling |
| `gstlearn` | Geostatistics + ML (kriging, simulation, variograms) |
| `geone` | Stochastic simulation |
| `landlab` | Landscape evolution modeling |
| `pyvista` | 3D visualization (VTK wrapper) |
| `simpeg` | Geophysical inversion |
| `scikit-gstat` | Variography and geostatistical estimation |

### Seismic Wrappers (`seismic_wrappers.py`)

Each wrapper enforces:

- **ClaimTag**: `OBSERVED` (segyio ingest) or `COMPUTED` (bruges attribute)
- **VAULT999 receipt**: immutable audit trail with SHA256 hash
- **PhysicsGuard bounds**: amplitude/variance/sweetness/coherence ranges enforced

```python
from geox.skills.earth_science.seismic_wrappers import (
    seismic_load_volume,
    seismic_compute_attribute,
    ClaimTag,
)

# Ingest SEG-Y → OBSERVED, VAULT999, render_payload
result = seismic_load_volume(volume_id="MB_3D", segy_path="/data/MB_3D.sgy")
# result["claim_tag"] = "OBSERVED"
# result["render_payload"] = {"type": "volume_slice", "shape": [200,300,801]}

# Compute attribute → COMPUTED, VAULT999, color_map
attr = seismic_compute_attribute("MB_3D", attribute="variance")
# attr["claim_tag"] = "COMPUTED"
# attr["render_payload"]["color_map"] = "OrRd"
```

---

## Subsurface Epistemic Layer

**Audit Reference:** Session 2026-04-18
**Purpose:** Formalize Bayesian graph, encode dependencies explicitly, enforce hard physics constraints, quantify refusal triggers.

### 6 Subsurface Skill Domains

| Skill ID | Title | Purpose |
|----------|-------|---------|
| `geox.subsurface.formation-evaluation` | Formation Evaluation | Vsh, POR, Sw via Archie/Indonesia/Simandoux. Physics bounds enforced. |
| `geox.subsurface.seismic-interpretation` | Seismic Interpretation | Horizon picking + amplitude analysis. Never collapse posterior to single horizon. |
| `geox.subsurface.reservoir-dynamics` | Reservoir Dynamics | Fluid mechanics, PVT, material balance. Net pay requires Sw + POR + Vsh all pass. |
| `geox.subsurface.basin-charge` | Basin Charge | Thermal maturity, migration, charge timing. `charge_ma ≤ trap_ma` enforced. |
| `geox.subsurface.prospect-risk` | Prospect Risk | PoS = P(reservoir) × P(trap) × P(seal) × P(charge) × P(retention). Coupling detection required. |
| `geox.subsurface.posterior-integrity` | Posterior Integrity | AlphaFold pLDDT equivalent. `integrity_score < 0.3` → AUTO_HOLD. |

### PhysicsGuard (`geox/core/physics_guard.py`)

Hard physics constraint enforcement — runs before 888_HOLD queue. Physically impossible outputs never reach human review.

```python
from geox.core.physics_guard import PhysicsGuard

guard = PhysicsGuard()

# Bounds check — rejects impossible values
guard.validate({"porosity": 0.55, "sw": 1.5})
# → {"status": "PHYSICS_VIOLATION", "hold": True}

# Posterior breadth — P90/P10 ratio must ≤ 5.0
guard.check_posterior_breadth(p10=10, p50=100, p90=600)
# → {"status": "POSTERIOR_TOO_BROAD", "hold": True}

# Net pay — ALL THREE criteria required simultaneously
guard.check_net_pay(sw=0.25, por=0.18, vsh=0.20)
# → PASS: net pay confirmed

# Charge timing — charge must precede or coincide with trap formation
guard.check_charge_timing(charge_ma=50, trap_ma=60)
# → PASS
guard.check_charge_timing(charge_ma=70, trap_ma=60)
# → {"status": "TIMING_VIOLATION", "hold": True}
```

**Physics bounds enforced:**

| Parameter | Min | Max | Violation |
|-----------|-----|-----|-----------|
| Porosity | 0.02 | 0.45 | REJECT |
| Water saturation | 0.0 | 1.0 | REJECT |
| Vsh | 0.0 | 1.0 | REJECT |
| Ro oil window | 0.6% | 1.3% | WARNING |
| P90/P10 ratio | — | 5.0 | HOLD |

### Posterior Integrity Scoring

Every subsurface output that flows to WEALTH carries:

```json
{
  "integrity_score": 0.74,
  "posterior_breadth": 4.0,
  "evidence_density": 2.3,
  "model_lineage_hash": "geox_v2_baseline_run_001",
  "recommendation": "CLAIM"
}
```

**Thresholds:**

| Integrity Score | Action |
|----------------|--------|
| < 0.3 | **AUTO_HOLD** — do not pass to WEALTH |
| 0.3 – 0.6 | **PLAUSIBLE** — pass with warning |
| > 0.6 | **CLAIM** — pass to WEALTH normally |

---

## Core Engine: AC_Risk (Theory of Anomalous Contrast)

### The Equation

```
AC_Risk = U_phys × D_transform × B_cog

Where:
    U_phys      = Physical ambiguity (0.0 = certain, 1.0 = fully ambiguous)
    D_transform = Display distortion factor (1.0 = clean, 3.0 = severely distorted)
    B_cog       = Cognitive bias factor (0.20 = rational, 0.42 = biased)

Verdict Thresholds:
    < 0.15  →  SEAL      (safe to proceed)
    < 0.35  →  QUALIFY   (proceed with documented caveats)
    < 0.60  →  HOLD      (888_HOLD triggered — human approval required)
    ≥ 0.60  →  VOID      (physically impossible or governance violation)
```

### Governance Layers

Every AC_Risk result is wrapped in:

| Layer | Purpose |
|-------|---------|
| **ClaimTag** | Epistemic classification: `CLAIM`, `PLAUSIBLE`, `HYPOTHESIS`, `UNKNOWN` |
| **TEARFRAME** | Truth (≥0.85 for CLAIM), Echo (≥0.75 consistency), Amanah (LOCK required for SEAL), Rasa (context fit) |
| **Anti-Hantu** | F9 screen — fail-closed on empathy/feeling attribution |
| **888_HOLD** | Irreversible actions or `amanah_locked=False` → mandatory human veto |
| **VAULT999** | Every verdict sealed to immutable ledger |

---

## Constitutional Floors Enforced

GEOX enforces arifOS F1–F13 on every operation. Non-negotiable:

```
F1  AMANAH     Reversibility first — irreversible claims → 888_HOLD
F2  TRUTH      τ ≥ 0.99 for CLAIM — or declare uncertainty band
F4  CLARITY    Scale, CRS, provenance explicit or tagged UNKNOWN
F6  MARUAH     ASEAN/MY context — stakeholder dignity protected
F7  HUMILITY   Confidence bounded 0.03–0.15 — overclaim prohibited
F8  SAFETY     Law and safety compliance verified
F9  ANTI-HANTU Zero hallucination tolerance — physics or VOID
F10 ONTOLOGY   AI = tool, Model ≠ Reality
F11 AUDIT      Every decision logged with full provenance
F13 SOVEREIGN  Human holds final veto — always supreme
```

---

## Evidence Credit

Each verified tool in the pipeline reduces `D_transform` by a governed credit amount. A fully-evidenced prospect can reach SEAL instead of being trapped at VOID.

| Tool Called | Credit | Cumulative |
|-------------|--------|------------|
| `geox_well_load_bundle` | +0.20 | 0.20 |
| `geox_well_qc_logs` | +0.15 | 0.35 |
| `geox_well_compute_petrophysics` | +0.40 | 0.75 |
| `geox_seismic_load_line` / `load_volume` | +0.30 | 1.05 |
| `geox_section_interpret_strata` | +0.30 | 1.35 |

```
D_transform_effective = max(1.0, D_transform_base − evidence_credit)
```

Max credit = **1.35** → penalty floors at 1.0. SEAL reachable for well-evidenced prospects.

---

## WELL — Biological Substrate (Operator Sovereignty)

WELL is the biological substrate that ensures operator (arif) sovereignty over all GEOX operations. It monitors cognitive pressure and enforces the constitutional hierarchy: **WELL informs. arifOS judges. A-FORGE executes.**

```
WELL/
├── server.py          # Cognitive pressure monitor
├── vault_bridge.py     # Bridge to arifOS VAULT999
├── gate/well_gate.py   # Constitutional gate
└── CHARTER.md         # Operator sovereignty charter
```

**Hierarchy Invariant:**
- WELL holds no veto — it holds a mirror
- arifOS holds judgment authority
- A-FORGE holds execution authority
- Human (W0) holds ultimate sovereignty (F13)

---

## SEALKIT — Constitutional SEAL Ritual

`sealkit/` implements the 999 SEAL protocol — proof-of-work ceremony that validates operator intent before irreversible actions.

```
sealkit/
├── seal.sh          # Shell ceremony
├── SEAL.md         # SEAL protocol documentation
├── manifest.json    # Intent manifest
└── manifest.sig     # Cryptographic signature
```

---

## Quickstart

### Docker (Recommended)

```bash
# Build
docker build -t geox .

# Run with auth
docker run -p 8081:8081 \
  -e GEOX_SECRET_TOKEN=your_token_here \
  -e PORT=8081 \
  geox
```

### Local Development

```bash
pip install -r requirements.txt
python geox_mcp_server.py
# Server starts on http://0.0.0.0:8081
```

### MCP Endpoint

```
POST /mcp   (Streamable HTTP v2 — FastMCP 3.x)
GET  /health → {"status":"ok","seal":"DITEMPA BUKAN DIBERI","service":"geox-mcp"}
GET  /ready
```

Auth: `Authorization: Bearer <GEOX_SECRET_TOKEN>` on `/mcp` endpoints.

### Python API

```python
from geox.core.ac_risk import compute_ac_risk, compute_ac_risk_governed

# Basic AC_Risk
result = compute_ac_risk(u_ambiguity=0.30, transform_stack=[], b_cog=0.35)
# result.ac_risk = SEAL if low ambiguity + low transform + rational bias

# Full governed result (includes TEARFRAME, Anti-Hantu, 888_HOLD)
governed = compute_ac_risk_governed(
    u_ambiguity=0.45,
    transform_stack=["load", "qc", "petrophysics"],
    evidence_credit=1.05,
    bias_scenario="ai_vision_only",
    truth_score=0.85,
    echo_score=0.80,
    amanah_locked=True,
    rasa_present=True,
    model_text="HC zone confirmed 3/4 wells, Horizon A continuous"
)
# governed.verdict, governed.ac_risk, governed.hold_enforced, governed.vault_payload
```

### MCP Tools via FastMCP Client

```python
from geox.geox_mcp.fastmcp_server import mcp

# Load seismic volume → launch geox-seismic-viewer
volume = mcp.call_tool("geox_seismic_load_volume", {
    "volume_id": "MB_3D",
    "segy_path": "/data/MB_3D.sgy"   # omit for scaffold fixture
})
# volume["ui"] → {"resourceUri": "ui://geox_seismic_viewer", "verdict": "SEAL"}
# volume["vault_receipt"] → VAULT999 receipt

# Compute seismic attribute → update viewer with color overlay
attr = mcp.call_tool("geox_seismic_compute_attribute", {
    "volume_id": "MB_3D",
    "attribute": "variance"  # amplitude | variance | sweetness | coherence
})
# attr["render_payload"]["color_map"] = "OrRd"

# Load well bundle → real depth curves
bundle = mcp.call_tool("geox_well_load_bundle", {
    "well_id": "BEK-2",
    "las_path": "/data/BEK-2.las"   # omit for scaffold fixture
})

# Run depth-indexed petrophysics
petro = mcp.call_tool("geox_well_compute_petrophysics", {
    "well_id": "BEK-2",
    "volume_id": "BEK_VOL",
    "saturation_model": "Archie"
})
# petro["curves"] → depth-indexed POR, Sw, Vsh curves
```

---

## Well Test Fixtures

GEOX ships scaffold well data for testing:

| Well | Status | Notes |
|------|--------|-------|
| `BEK-2` | HC CONFIRMED | φ=0.22, Sw=0.35, 82m core HC + 4m fringe |
| `DUL-A1` | HC CONFIRMED | 75m net pay |
| `SEL-1` | HC CONFIRMED | 75m net pay |
| `TIO-3` | UNCLEAR | No resistivity anomaly — possible water leg |

Scaffold returns **depth-indexed curves** (91 points, 2040–2220m MD) with correct zone flags. Load a real `.las` file to replace scaffold with measured data:

```python
geox_well_load_bundle(well_id="BEK-2", las_path="/path/to/BEK-2.las")
# provenance: "las_file:BEK-2.las"  ← real data
# vs scaffold: provenance: "scaffold_fixture"
```

---

## RATLAS — Reference Atlas of Earth Materials

GEOX reasoning is anchored by **RATLAS** — 99 canonical material states across 11 physics families:

```
ρb = (1−φ)·ρm + φ·ρf                # Bulk density mixing law
NPHI ≈ φ·Σ(Si·HIi)                  # Neutron hydrogen index
Rt = a·Rw / (φm·Swⁿ)                # Archie resistivity (clean sandstone)
Vsh = (GRlog − GRmin) / (GRmax − GRmin)  # Shale volume index
```

11 families: Sedimentary Clastic · Sedimentary Carbonate · Sedimentary Chemical/Organic · Igneous Felsic · Igneous Mafic · Igneous Ultramafic · Metamorphic Foliated · Metamorphic Non-Foliated · Unconsolidated/Soil · Engineered Materials

---

## Telemetry — arifOS Metabolic Pipeline

`geox/telemetry/geox_telemetry.py` emits GEOX vital signs to arifOS so the constitutional kernel can see the organ's metabolic state:

```python
from geox.telemetry.geox_telemetry import telemetry_emit, get_telemetry_emitter

# Emit tool use → vault receipt
telemetry_emit(event_type="tool_use", tool_name="geox_seismic_load_volume")

# Full diagnostic for arifOS capability map
diag = get_telemetry_emitter().full_diagnostic()
# {
#   "organ": "GEOX",
#   "mcp_apps_plane": {"connected": True, "host_path": "/srv/mcp/apps/"},
#   "arifos_integration": {"vault_route": "VAULT999", "registered": True},
#   "vital_signs": {"entropy_delta": 0.05, "peace_sq": 1.0, "dominant_claim": "OBSERVED"},
#   "usage": {"tools_used": 3, "vault_receipts": 3}
# }
```

Every seismic tool call automatically emits telemetry with the verdict, claim_tag, and VAULT999 receipt.

---

## arifOS Ecosystem

| Component | URL |
|-----------|-----|
| arifOS Kernel | [github.com/ariffazil/arifOS](https://github.com/ariffazil/arifOS) |
| APEX Codex | [github.com/ariffazil/APEX](https://github.com/ariffazil/APEX) |
| AAA Dataset | [huggingface.co/datasets/ariffazil/AAA](https://huggingface.co/datasets/ariffazil/AAA) |
| GEOX MCP Server | `geoxarifOS.fastmcp.app/mcp` |
| Author | [arif-fazil.com](https://arif-fazil.com) |

---

## Author

**Muhammad Arif bin Fazil**
Sovereign Architect — arifOS & GEOX
13+ years subsurface exploration · Malay Basin, ASEAN
Builder of constitutional AI governance from geological first principles

---

## License

```
APEX Theory (Constitution):  CC0 (Public Domain)
GEOX Runtime:               AGPL-3.0
Trademark:                  Proprietary
```

Physics is not negotiable. Maruah is not optional. Every verdict sealed — 999.

---

```
DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
ΔΩΨ | GEOX | 888_JUDGE | EARTH WITNESS
```