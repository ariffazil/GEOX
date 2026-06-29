<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-29
valid_from: 2026-06-14
valid_until: 2026-07-29
confidence: high
scope: /root/geox
-->

```
    ____ _____  ___  _  __
   / ___| ____|/ _ \| |/ /
  | |  _|  _| | | | | ' / 
  | |_| | |___| |_| | . \ 
   \____|_____|\___/|_|\_\
                          
   EARTH INTELLIGENCE — GOVERNED WORLD MODEL
```

# GEOX — Governed Subsurface Coprocessor & Earth Intelligence

GEOX is a physics-constrained, evidence-grounded subsurface reasoning engine. It operates as the **Earth Intelligence organ** of the [arifOS Constitutional Federation](https://github.com/ariffazil/arifos), preparing geoscience, petrophysics, and seismic data into governed evidence. 

GEOX is **evidence-only**; it never authorizes drilling, commits capital, or replaces human geological judgment. 

---

## 1. Executive Summary & SOT

| Field | Description / Status |
|---|---|
| **Sovereign Owner** | [Muhammad Arif bin Fazil](https://arif-fazil.com) |
| **Runtime Engine** | Python FastMCP 3.4.2 |
| **Port & Protocols** | Port `8081` (HTTP/SSE) & Local `stdio` |
| **Public MCP Surface** | 30 canonical tools (26 surface-facing + 4 internal) |
| **Backward-Compat** | 49 legacy aliases mapped and routed to canonical tools |
| **License** | [Business Source License 1.1 (BSL-1.1)](LICENSE) — Free for non-production/academics |
| **Governance Kernel** | arifOS F1–F13 · 888 JUDGE · VAULT999 |
| **SOT Verification** | `curl http://127.0.0.1:8081/health` |

---

## 2. Epistemic Rigor & Earth Physics

GEOX enforces rigorous physical constraints rather than relying on unconstrained LLM heuristics:

*   **Epistemic Grading:** Every output carries a strict grade: `CLAIM` (proven) · `PLAUSIBLE` (consistent with physics) · `HYPOTHESIS` (under test) · `ESTIMATE` (numerical range) · `UNKNOWN`.
*   **Uncertainty Quantiles:** Single-number estimates are disallowed. All computations return `P10 / P50 / P90` distributions.
*   **Hypothesis Scaffolding:** Geological propositions are rejected unless they specify four vectors:
    1. `evidence_for` (supporting observations)
    2. `evidence_against` (contradicting features)
    3. `expected_additional_signatures` (consequences if true)
    4. `missing_tests` (data required to resolve)
*   **Substrate Anchoring:** Grounded in the Cenozoic crustal domain grammar of **Huang et al. (2021)** (*Tectonics*, OBS2013-1 profile), using 10,346 picked arrivals to constrain seismic velocity boundaries.
*   **RASA Alignment:** Relevance-Aware Substrate Alignment ($RASA = \text{evidence\_credit} \times (1 - u_{\text{ambiguity}})$) measures how closely an interpretation matches the empirical dataset, hard-capped at $0.90$ (F7 Humility).

---

## 3. Ingestion & Invariants (F1–F13)

GEOX is bound by 13 constitutional floors from the arifOS kernel:

```
                         ┌──────────────────┐
                         │   ARIF FAZIL      │
                         │  F13 SOVEREIGN    │
                         │  Final Veto       │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │     arifOS        │
                         │  Constitutional   │
                         │  Kernel (8088)    │
                         │  F1-F13 · 888     │
                         │  JUDGE · VAULT999 │
                         └──┬────┬────┬─────┘
                            │    │    │
            ┌───────────────┘    │    └───────────────┐
            │                    │                    │
   ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
   │      GEOX       │  │     WEALTH     │  │      WELL      │
   │  Earth Evidence │  │ Capital Intel  │  │ Human Readiness│
   │    Port 8081    │  │  Port 18082    │  │  Port 18083    │
   │  EVIDENCE-ONLY  │  │  ADVISORY ONLY │  │ REFLECT-ONLY   │
   └─────────────────┘  └────────────────┘  └────────────────┘
```

*   **F1 AMANAH (Sacred Trust):** No irreversible action (e.g. data export, prospect seal) without explicit human signature.
*   **F2 TRUTH:** Claims must cite physical evidence (logs, seismic, cores) with an empirical verification index $\tau \ge 0.99$.
*   **F7 HUMILITY:** Vision AI and statistical inferences are capped at $0.90$ confidence to leave room for unexpected structural anomalies.
*   **F9 ANTI-HANTU:** Blocks dark-clever overrides and technically-correct-but-misleading interpretations.

---

## 4. Capability Map: 30 Canonical Tools

GEOX consolidates its capabilities into 30 canonical tools. Legacy client calls are translated automatically by compatibility middleware.

| Category | Tools | Description |
|---|---|---|
| **Well Logging** | `geox_well_ingest`, `geox_well_qc`, `geox_well_desurvey`, `geox_petrophysics`, `geox_sequence` | LAS/CSV log processing, depth normalization, petrophysical interpretation, and systems tract segmentation. |
| **Seismic Processing** | `geox_seismic_ingest`, `geox_seismic_compute`, `geox_seismic_interpret`, `geox_vision` | Attribute computation, synthetic well ties, AVO analysis, and computer vision structural tracking. |
| **Geomechanics & Basin** | `geox_subsurface_model`, `geox_geomechanics`, `geox_basin`, `geox_deep_time_state`, `geox_surface_status` | 3D subsurface block mapping, stress tensor analysis, basin-wide charge simulation, and deep-time plate configurations. |
| **EGS Governance** | `geox_egs_*` (8 tools) | API surface for querying, challenging, and attaching evidence to claims. |
| **Internal Plugs** | `geox_claim`, `geox_evidence`, `geox_prospect`, `geox_doctrine` | Core data structures that define evidence validity, prospects, and policy limits. |

---

## 5. Testing & Verification

### 5.1 Verification for Human Operators
Ensure the local or production service is alive and listening:

```bash
# Verify daemon health
curl -f http://127.0.0.1:8081/health

# expected json output:
# {
#   "status": "healthy",
#   "canonical_tools": 30,
#   "git_version": "geox-797a7d57",
#   "contract_epoch": "2026-06-28-GEOX-30TOOLS-PHASE21"
# }
```

### 5.2 Verification for AI Agents
To wire GEOX directly into Claude Code or other local MCP harnesses, append this to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "geox": {
      "command": "python3",
      "args": ["-m", "geox_mcp.server", "--transport", "stdio"],
      "cwd": "/root/geox"
    }
  }
}
```

### 5.3 Technical Verification for Developers & Institutions
Run the complete physical test suite (1,007 tests validating coordinate projection, Archie/density loss constraints, and AVO residuals):

```bash
# Synchronize virtual environment
uv sync --frozen

# Run full test suite
make test

# Run security forge audit (Trivy + Gitleaks + Semgrep)
make forge
```

---

## 6. License, Sovereignty & Verification

### License
GEOX is licensed under the **Business Source License 1.1 (BSL-1.1)**. 
*   **Permissions:** You may use the software freely for non-production purposes, testing, evaluation, and academic research.
*   **Commercial Production:** Production use in commercial enterprises (oil, gas, geothermal, carbon capture, or hosting SaaS instances) requires a separate paid license from the Licensor.
*   **Transitive Open Source:** This license automatically converts to the **Apache License 2.0** on the Change Date (June 29, 2029).

### Sovereignty
*   **Sovereign:** Muhammad Arif bin Fazil
*   **Final Veto:** F13 Absolute Veto
*   **Contact:** [arif-fazil.com](https://arif-fazil.com) | [github.com/ariffazil](https://github.com/ariffazil)

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    GEOX does not tell you where to drill.                        ║
║    GEOX tells you what the Earth looks like.                     ║
║                                                                  ║
║    arifOS tells you if the evidence is admissible.               ║
║    Arif tells you if the well gets drilled.                      ║
║                                                                  ║
║         The Earth speaks. GEOX listens. The sovereign            ║
║         decides. That is the federation. That is the law.        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```
