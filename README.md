<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-04
valid_from: 2026-05-22
valid_until: 2026-06-22
confidence: high
scope: /root/geox
epistemic_status: CLAIM
-->

# 🪨 GEOX — Earth Intelligence Engine

> **Governed subsurface coprocessor for the arifOS federation.**
> Domain: `geox.arif-fazil.com` | Organ: FIELD (γ) | Authority: Arif Fazil
> Status: OPERATIONAL | Seal: DITEMPA BUKAN DIBERI
>
> ⚠️ **For live/degraded/disabled status of ALL federation organs, see:**
> **`ariffazil/arifOS/FEDERATION_STATUS.md`** — canonical source of truth.

***

## What GEOX Is

GEOX is the **Earth Evidence Layer** in the arifOS federation. It prepares, computes, and governs subsurface evidence — well logs, petrophysics, stratigraphy, geomechanics, seismic, and prospect risk — and exposes that evidence through a canonical FastMCP surface.

Every output passes through the **F3 WITNESS floor** before reaching the reasoning kernel.

**GEOX computes. MCP exposes. Resources guide. Artifacts remember. Agent reasons. Arif judges.**

> GEOX owns the **FIELD** — the empirical grounding layer for earth sciences.
> GEOX does **not** own constitutional judgment (arifOS) or economic logic (WEALTH).

***

## Architecture — Three Layers

```
┌─────────────────────────────────────────────────────────┐
│  GEOX repo                                              │
│                                                         │
│  src/geox_core/    ← Truth Engine. Computes.           │
│                       Never exposed to agents directly. │
│                                                         │
│  src/geox_mcp/     ← MCP Surface. The only surface    │
│                       AI agents touch. Governed by      │
│                       CANON-9, ToAC, F1–F13.           │
│                                                         │
│  resources/        ← Agent Knowledge Pack.              │
│                       Playbooks, ontology, prompts,      │
│                       toolcards, schemas, examples.      │
└─────────────────────────────────────────────────────────┘
```

### Epistemic Tier Separation

| Tier | Layer | Capability |
|------|-------|-----------|
| 0 | Observed | Raw witness — depth, GR, RT, RHOB, NPHI, DTC |
| 1 | Derived | Deterministic transforms — Vsh, φ, Sw, AI, pore pressure |
| 2 | Interpreted (Local) | Pattern — facies motif, lithology, single-well |
| 3 | Process Hypothesis | Abduction — transgression, forced regression, sequence |
| 4 | Contradiction Scan | Red-team — cross-evidence conflict, 888HOLD trigger |
| 5 | Prospect Risk | ACRisk, ToAC, basin charge, sovereign verdict |

**The LLM is the structured language interface — not the geologist. Arif judges.**

***

## MCP Surface (Live — 2026-06-04)

```
PYTHONPATH=src python -m geox_mcp.server --host 0.0.0.0 --port 8081
→ 20 canonical tools exposed (no internal legacy aliases)
→ Universal output contract v0.4
→ Version v2026.05.27
→ Contract epoch: 2026-05-12-GEOX-13TOOLS-v0.7
```

### The 20 canonical tools

The canonical list lives at `src/geox_mcp/server.py` → `CANONICAL_PUBLIC_TOOLS` and is served live by `geox_system_registry_status`. **Always trust the live registry, not this table.**

| Domain | Tools |
|--------|-------|
| **Data intake** | `geox_data_ingest_bundle`, `geox_data_qc_bundle`, `geox_dst_ingest_test` |
| **Inspect (pre-ingest)** | `geox_las_inspect`, `geox_seismic_inspect`, `geox_deviation_survey_inspect`, `geox_tops_inspect`, `geox_seismic_segy_inspect` |
| **Subsurface (petrophysics + integrity)** | `geox_subsurface_generate_candidates`, `geox_subsurface_verify_integrity` |
| **Seismic physics** | `geox_seismic_compute` (modes: synthetic, well_tie, time_depth_anchor, anomalous_contrast, attribute) |
| **Sequence stratigraphy** | `geox_sequence_interpret` (modes: single_well, project, section_correlation) |
| **Evidence reasoning** | `geox_evidence_reason` (phases: synthesize, abduct, contradict, full) |
| **Prospect** | `geox_prospect_evaluate` (modes: screen, appraise, develop) |
| **Map context** | `geox_map_context_scene` |
| **Claim governance** | `geox_claim_create`, `geox_claim_challenge`, `geox_evidence_attach`, `geox_claim_seal` |
| **Registry / system** | `geox_system_registry_status` |

> **F13 honored** — every capability lives in an existing tool's modes/params, not a new tool. Eureka forges (E1 multi-method T-D fitters, E7 cascade demotion) add depth inside `geox_seismic_compute` and `geox_claim_*` without expanding the surface.

### Universal Output Envelope (v0.4)

Every tool returns the same outer contract:

```json
{
  "execution_status": "SUCCESS | HOLD | VOID",
  "tool_class": "well_stratigraphy",
  "claim_state": "SEAL | QUALIFY | HOLD | VOID",
  "observed": {},
  "derived": {},
  "interpreted": {},
  "artifact_refs": {},
  "evidence_refs": [],
  "missing_inputs_schema": [],
  "claim_limits": [],
  "next_best_actions": [],
  "audit_receipt": {},
  "human_final_authority": "Arif"
}
```

> `claim_state` maps directly to ACRisk thresholds: SEAL (< 0.25), QUALIFY (0.25–0.50), HOLD (0.50–0.75), VOID (> 0.75).

***

## Repository Structure

```
geox/
├── src/
│   ├── geox_core/              # Truth Engine (not agent-facing)
│   │   ├── engines/
│   │   │   ├── petrophysics/  # Archie, Sw ensemble, Vsh, cutoffs
│   │   │   ├── stratigraphy/  # Recursive ToAC, GR motif, parasequence
│   │   │   ├── geomechanics/  # Eaton pore pressure, mechanical strat
│   │   │   ├── seismic/       # Well tie, attribute preparation
│   │   │   ├── map_context/   # Geospatial grounding
│   │   │   └── prospect/      # Basin charge, ACRisk math
│   │   ├── io/                # LAS, SEG-Y, tops, checkshot readers
│   │   ├── governance/         # physics_guard.py, ac_risk.py, judge.py
│   │   ├── artifacts/          # store.py, refs.py, exporter.py
│   │   └── schemas/            # Pydantic models — well, seismic, prospect
│   │
│   └── geox_mcp/              # MCP Surface (agent-facing)
│       ├── server.py           # THE canonical FastMCP entrypoint
│       ├── registry.py         # Single tool registry — one source of truth
│       ├── contracts/          # MCP protocol contracts
│       └── tools/             # 20 canonical tools (one module per domain)
│
├── resources/                  # Agent Knowledge Pack
│   ├── capabilities/
│   │   └── geox_capabilities.json    # THE canonical registry source
│   ├── toolcards/                     # YAML — intent, limits, failure modes
│   ├── playbooks/                     # Workflow guides for agents
│   ├── prompts/                       # Claim discipline, failure policy, etc.
│   ├── ontology/                      # curve_aliases, lithology, depositional env
│   ├── schemas/                      # Exported JSON schemas
│   └── examples/                     # Golden examples (danum1, etc.)
│
├── tests/                       # 693 passing
│   ├── unit/
│   ├── integration/
│   └── golden/                 # Agent behavior anchor tests
├── docs/                        # Architecture, deployment, changelog
├── scripts/                     # generate_live_sot.py, seed_evidence.py
├── deploy/                      # Dockerfiles, systemd, Caddy
├── archive/                     # Legacy (read-only, never runtime)
│   ├── WELL/                   # Archived WELL integration
│   └── arifos/                # Archived legacy domain logic
├── .mcpignore                  # Prevents agent ingestion of archive/vault/raw
└── server.py                   # Legacy entrypoint (points to src/geox_mcp/server.py)
```

***

## Getting Started

```bash
# Install
pip install -e ".[dev]"

# Run canonical MCP server
PYTHONPATH=src python -m geox_mcp.server

# Run tests
PYTHONPATH=src python -m pytest tests/ -q

# Lint
ruff check src/
ruff format src/
mypy src/geox_mcp/server.py
```

### Connect via FastMCP CLI

```bash
# List all 28 tools
fastmcp list src/geox_mcp/server.py

# Call a tool
fastmcp call src/geox_mcp/server.py mcp_health_check

# Inspect capabilities
fastmcp inspect src/geox_mcp/server.py
```

### Connect via Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "geox": {
      "command": "python",
      "args": ["-m", "geox_mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/geox/src"
      }
    }
  }
}
```

### Remote (VPS)

```bash
# Health check
curl https://geox.arif-fazil.com/health

# MCP endpoint
# wss://geox.arif-fazil.com/mcp
```

***

## The Agent Operating Loop

An AI agent should experience GEOX in this sequence:

```
1. list_resources → read geox://resources/index
2. read relevant playbook (e.g., geox://resources/playbooks/well_sequence_stratigraphy.yaml)
3. call geox_data_ingest_bundle (artifact_ref returned)
4. call geox_data_qc_bundle (claim_state verified)
5. call domain computation tool (well, petro, strat, seismic)
6. call geox_process_abduction (ranked process hypotheses)
7. call geox_evidence_contradiction_scan (red-team the hypotheses)
8. call geox_evidence_summarize_cross (governed narrative)
9. agent writes explanation with claim_limits
10. Arif renders final judgment (F13 sovereign veto)
```

> The agent does **not** search source files. It reads the governed operating manual (`resources/`), then calls governed tools.

***

## Governance Model

All tools enforce the **arifOS F1–F13 constitutional floors**:

| Floor | Principle | GEOX Implementation |
|-------|-----------|---------------------|
| F1 | Reversible | All operations non-destructive; artifact_refs are immutable |
| F2 | ≥99% truth or declare band | `claim_state` with explicit uncertainty band |
| F3 | Human-AI-Evidence align | Tri-witness on every output |
| F5 | Peace ≥ 1.0 | 888HOLD before irreversible subsurface decisions |
| F7 | Humility band 0.03–0.15 | ACRisk declared on every claim |
| F9 | Anti-Hantu | No hallucinated geology — missing inputs trigger HOLD |
| F13 | Sovereign human veto | `human_final_authority: "Arif"` on every envelope |

### 888HOLD Protocol

When ACRisk exceeds threshold or evidence is contradicted:

```python
# Automatic hold — never silently proceeds
if acrisk > 0.60 or contradiction_detected:
    return envelope(
        execution_status="HOLD",
        verdict="888HOLD",
        hold_reason="...",
        human_final_authority="Arif"
    )
```

***

## ACRisk — Theory of Anomalous Contrast

Every claim carries a risk score:

```
ACRisk = U_phys × D_transform × B_cog
```

Where:
- **U_phys** — physical uncertainty of the raw signal
- **D_transform** — distortion introduced by visual/computational transforms
- **B_cog** — cognitive bias from display seduction (VLM/human)

| ACRisk | Verdict | Action |
|--------|---------|--------|
| < 0.25 | SEAL | Auto-proceed |
| 0.25–0.50 | QUALIFY | Proceed with declared caveats |
| 0.50–0.75 | HOLD | Human review required |
| > 0.75 | VOID | Unsafe — do not use |

***

## Artifact Reference Protocol

Stable cross-tool evidence transport. No raw file paths.

```
geox://artifact/DATA-LAS-DANUM1-QIDB2025
geox://artifact/PETRO-SW-DANUM1-INT001
geox://artifact/STRAT-TOAC-DANUM1-Z1
```

Artifact refs are immutable, auditable, and federation-portable (arifOS ↔ WEALTH ↔ GEOX).

***

## Federation

| Organ | Repo | Role |
|-------|------|------|
| **arifOS** | [ariffazil/arifOS](https://github.com/ariffazil/arifOS) | Kernel — constitutional judgment, F3 WITNESS, 000–999 pipeline |
| **GEOX** | [ariffazil/GEOX](https://github.com/ariffazil/GEOX) | FIELD — Earth evidence, petrophysics, governed computation |
| **WEALTH** | [ariffazil/wealth](https://github.com/ariffazil/wealth) | Capital — economic constraints on field development |

GEOX feeds governed evidence to arifOS. arifOS renders constitutional verdict. WEALTH applies economic constraints. Arif holds F13 sovereign veto over all three.

### AAA Terminology Note

When GEOX docs or agents reference AAA, qualify the surface:

| Term | Surface | Role |
|------|---------|------|
| **AAA-HF** | Hugging Face dataset | Supplies doctrine and evaluation references for agent behavior |
| **AAA-Cockpit** | GitHub `ariffazil/AAA` | Displays and routes federation state — does not own F1–F13 judgment |
| **arifOS** | `ariffazil/arifos` | **The judge** — applies constitutional floors to all GEOX computations |

GEOX computes earth evidence only. GEOX does not judge. GEOX does not define doctrine.

> "AAA is polymorphic by design. When precision matters, qualify the surface."

***

## Roadmap

| Horizon | Status | Description |
|---------|--------|-------------|
| H1 — Clean Surface | ✅ SEALED | One server, one registry, strict `.mcpignore` |
| H2 — `geox_process_abduction` | ✅ SEALED | Earth abduction engine — pattern → process hypothesis |
| H3 — Async Tasks (`task=True`) | 🔧 Next | Long-running batch LAS ingest, basin metabolize (FastMCP 3.0 unblocked) |
| H4 — MCP Resources | ✅ SEALED | playbooks + prompts wired as MCP resources |
| H5 — MCP Elicitation (888HOLD UI) | 🔧 Next | Multi-select elicitation via SEP-1330 — partial unblock in FastMCP 2.14 |
| H6 — Server Card + Registry | ✅ SEALED | `server-card.json` published |
| H7 — MCP Skills | ❌ Blocked | Awaiting MCP Skills WG finalization |
| PINN Layer | 🔧 Future | Physics-informed neural net for Vsh/φ/Sw |
| DRP Synthetic Core | 🔧 Future | GAN super-resolution for micro-CT training data |

***

## Test Suite

```
229 passed, 0 skipped, 0 xfailed, 0 failures
*Eureka forge (E1 + E7) + physics guard suites — full integration suite lives in `tests/integration/` and runs separately.*

Golden tests anchor agent behavior — tool output shape, claim_state correctness, failure mode coverage, no secret/path leaks.

***

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONPATH` | `src` | Required — must include `src/` for imports |
| `GEOX_HOST` | `0.0.0.0` | HTTP bind host |
| `GEOX_PORT` | `8081` | HTTP bind port (organ-standard, live on `geox-mcp.service`) |
| `GEOX_TRANSPORT` | `streamable-http` | `stdio` or `streamable-http` |
| `GEOX_LOG_LEVEL` | `INFO` | Logging level |
| `GEOX_SECRET_TOKEN` | `stdio-bypass` | Fail-closed auth for HTTP transport |

***

*Last Verified: 2026-06-04 | 999 SEAL ALIVE*

**DITEMPA BUKAN DIBERI — Forged, Not Given.**

---

## TREE777 Wiki

Full federation knowledge base — architecture decisions, earth-intelligence theory, agent documentation:
→ **https://wiki.arif-fazil.com**

*Last Verified: 2026-06-04 | 999 SEAL ALIVE*
**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**
