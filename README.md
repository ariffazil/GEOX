# GEOX — Governed Earth Intelligence

```
Physics > Narrative.
Maruah > Convenience.
DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
```

---

## What GEOX Is

**GEOX is the Earth-domain reasoning instrument of the [arifOS](https://github.com/ariffazil/arifOS) constitutional federation** — a governed geoscience coprocessor that reads subsurface evidence, maps spatial trajectories, and issues physics-verified verdicts under hard constitutional law.

It is **not** a visualization tool. It is **not** a feelings engine. It is a **reasoning instrument** built on the doctrine that every interpretation must be grounded in physical evidence before it can be sealed.

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
├── geox/
│   ├── __init__.py              # Package entry
│   ├── core/
│   │   ├── ac_risk.py          # ToAC AC_Risk calculation engine
│   │   ├── bias_detector.py    # Bond et al. (2007) cognitive bias audit
│   │   └── tool_registry.py    # Unified tool registry with metadata
│   └── geox_mcp/
│       ├── server.py            # FastMCP server entry
│       ├── fastmcp_server.py   # FastMCP transport layer
│       ├── adapters/            # Skill adapters
│       └── policies/            # Risk policy enforcement
│
├── registry/
│   └── registry.json            # 33 skills across 11 domains
│
├── skills/                      # MCP skill definitions
├── apps/                        # MCP App manifests (AC_Risk Console, etc.)
├── tests/                       # Constitutional validation suite
│
├── geox_mcp_server.py          # CLI entry point
├── fastmcp.json                # FastMCP deployment config
└── pyproject.toml              # Python package manifest
```

---

## The 11 Domains — 33 Skills

GEOX reasoning spans these canonical domains:

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

Full skill definitions: [`registry/registry.json`](registry/registry.json)

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

### Governance Layers (Wave 1 Trust Foundation)

Every AC_Risk result is wrapped in:

| Layer | Purpose |
|-------|---------|
| **ClaimTag** | Epistemic classification: `CLAIM`, `PLAUSIBLE`, `HYPOTHESIS`, `UNKNOWN` |
| **TEARFRAME** | Truth (≥0.85 for CLAIM), Echo (≥0.75 consistency), Amanah (LOCK required for SEAL), Rasa (context fit) |
| **Anti-Hantu** | F9 screen — fail-closed on empathy/feeling attribution |
| **888_HOLD** | Irreversible actions or `amanah_locked=False` → mandatory human veto |
| **VAULT999** | Every verdict sealed to immutable ledger |

---

## MCP Tools

### Public Earth Tools (`geox_*`)

| Tool | Purpose | Status |
|------|---------|--------|
| `geox_compute_ac_risk` | ToAC calculation | **PROD** |
| `geox_evaluate_prospect` | Full governance verdict + VAULT999 seal | **PROD** |
| `geox_load_seismic_line` | Seismic with F4 scale verification | **PROD** |
| `geox_build_structural_candidates` | Multi-model interpretation | **PROD** |
| `geox_verify_geospatial` | Coordinate + CRS grounding | **PROD** |
| `geox_feasibility_check` | Constitutional F1-F13 pre-check | **PROD** |
| `geox_earth_signals` | Live Earth observations | **PROD** |
| `geox_well_load_bundle` | Ingest LAS/DLIS well log bundles | **PROD** |
| `geox_well_qc_logs` | Quality control — spike, flatline, range detection | **PROD** |
| `geox_section_interpret_strata` | Multi-well stratigraphic correlation | **PROD** |
| `geox_cross_summarize_evidence` | Causal evidence synthesis for 888_JUDGE | **PROD** |
| `geox_attribute_audit` | Kozeny-Carman permeability proxy audit | **PREVIEW** |
| `geox_seismic_vision_review` | AI fault pick scaffold | **SCAFFOLD** |
| `geox_georeference_map` | Map georeferencing plan | **SCAFFOLD** |
| `geox_analog_digitizer` | Analog log → structured curve | **SCAFFOLD** |

### arifOS Governance Tools (`arifos_*`)

| Tool | Purpose |
|------|---------|
| `arifos_check_hold` | 888 HOLD authority check |
| `arifos_compute_risk` | ToAC AC_Risk score |
| `arifos_judge_prospect` | Full verdict — routes to VAULT999 |

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

## Epistemic Tags

Every GEOX output carries a mandatory claim tag:

```
CLAIM       — Definitive, direct evidence, operationally dependable
PLAUSIBLE   — Consistent with evidence but not uniquely validated
HYPOTHESIS  — Testable model, unverified, for testing only
UNKNOWN     — Explicitly declared gap in evidence
OBSERVED    — Directly measured or ingested
VERIFIED    — Passed QC with zero flags
COMPUTED    — Derived from physics model
INTERPRETED — Inferred from multi-source correlation
SYNTHESIZED — Assembled from cross-domain evidence
```

---

## Verdict Classes

| Verdict | Meaning | Action |
|---------|---------|--------|
| `SEAL` | Feasible, evidenced, governed | Proceed |
| `QUALIFY` | Feasible with documented limits | Proceed with caveats |
| `HOLD` | Risk elevated — human required | Await 888_HOLD release |
| `VOID` | Physics violation or governance breach | Stop — cannot proceed |
| `888_HOLD` | Explicit human veto required | Human sovereign decision |

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
pip install -e ".[dev]"   # fastmcp>=0.7.0, lasio>=0.31, uvicorn
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
    evidence_credit=1.05,   # full pipeline: well+seismic+petrophysics+section
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

# Load real LAS file → real depth curves
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
# petro["curves"] → 91 depth points (2040–2220m, 2m step)
# petro["summary"]["net_pay_intervals"] → [{top, bot}, ...]

# Full prospect judgment with evidence credit
judged = mcp.call_tool("arifos_judge_prospect", {
    "u_ambiguity": 0.45,
    "transform_stack": [
        {"kind": "load_volume"},
        {"transform": "compute_petrophysics"},
        "section_correlation"
    ],
    "evidence_credit": 1.05,
    "amanah_locked": True,
    "truth_score": 0.85,
    "echo_score": 0.80,
    "model_text": "HC zone confirmed 3/4 wells"
})
# judged["verdict"] → SEAL / QUALIFY / HOLD / VOID
# judged["hold_enforced"] → True/False
```

---

## Evidence Credit

Each verified tool in the pipeline reduces `D_transform` by a governed credit amount.
A fully-evidenced prospect can reach SEAL instead of being trapped at VOID.

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

## Well Test Fixtures

GEOX ships scaffold well data for testing:

| Well | Status | Notes |
|------|--------|-------|
| `BEK-2` | HC CONFIRMED | φ=0.22, Sw=0.35, 82m core HC + 4m fringe |
| `DUL-A1` | HC CONFIRMED | 75m net pay |
| `SEL-1` | HC CONFIRMED | 75m net pay |
| `TIO-3` | UNCLEAR | No resistivity anomaly — possible water leg |

Scaffold returns **depth-indexed curves** (91 points, 2040–2220m MD) with correct zone flags.
Load a real `.las` file to replace scaffold with measured data:

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
