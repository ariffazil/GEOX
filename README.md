<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-05-19
valid_from: 2026-05-19
valid_until: 2026-06-19
confidence: high
scope: /root/geox
epistemic_status: CLAIM
-->

# 🪨 GEOX — Earth Intelligence Engine

> **Governed subsurface coprocessor for the arifOS federation.**
> Domain: `geox.arif-fazil.com` | Organ: FIELD (γ) | Authority: Arif Fazil
> Status: OPERATIONAL | Seal: DITEMPA BUKAN DIBERI

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

## MCP Surface (Live — 2026-05-17)

```
PYTHONPATH=src python -m geox_mcp.server
→ 21 canonical tools exposed (no internal legacy aliases)
→ Universal output contract v0.4
→ Version v2026.05.17
```

### Tool Groups

| Group | Tools | Purpose |
|-------|-------|---------|
| `data` | `geox_data_ingest_bundle`, `geox_data_qc_bundle` | Load and validate well log data |
| `well` | `geox_well_analyze_sequence`, `geox_well_infer_seq_strat` | Well log interpretation |
| `well` | `geox_well_build_packages`, `geox_well_compute_gr_bins` | GR binning and package building |
| `subsurface` | `geox_subsurface_generate_candidates`, `geox_subsurface_verify_integrity` | Petrophysical candidates |
| `seismic` | `geox_seismic_analyze_volume` | Seismic evidence preparation |
| `section` | `geox_section_interpret_correlation` | Cross-section correlation |
| `map` | `geox_map_context_scene` | Geospatial grounding |
| `time4d` | `geox_time4d_analyze_system` | 4D systems tract analysis |
| `abduction` | `geox_process_abduction`, `geox_evidence_contradiction_scan` | Geological process hypothesis + red-team |
| `cross` | `geox_evidence_summarize_cross` | Cross-domain synthesis |
| `prospect` | `geox_prospect_evaluate`, `geox_prospect_judge_preview`, `geox_prospect_judge_seal` | Risk quantification and verdict |
| `history` | `geox_history_audit` | Immutable audit trail |
| `registry` | `geox_system_registry_status` | Registry health |
| `governance` | `mcp_health_check` | F1–F13 enforcement, 888HOLD |

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
│       └── tools/             # 21 canonical tools (one module per domain)
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
# List all 21 tools
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
693 passed, 1 skipped, 3 xfailed, 0 failures
```

Golden tests anchor agent behavior — tool output shape, claim_state correctness, failure mode coverage, no secret/path leaks.

***

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONPATH` | `src` | Required — must include `src/` for imports |
| `GEOX_HOST` | `0.0.0.0` | HTTP bind host |
| `GEOX_PORT` | `8081` | HTTP bind port |
| `GEOX_TRANSPORT` | `streamable-http` | `stdio` or `streamable-http` |
| `GEOX_LOG_LEVEL` | `INFO` | Logging level |
| `GEOX_SECRET_TOKEN` | `stdio-bypass` | Fail-closed auth for HTTP transport |

***

*Last Verified: 2026-05-18 | 999 SEAL ALIVE*

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
