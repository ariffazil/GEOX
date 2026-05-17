# GEOX MCP Next Horizon
## Eureka Insights & Roadmap Synthesis

**Status:** APPROVED
**Authority:** Arif (Human Architect) — F13 Sovereign Veto
**Epoch:** 2026-05-18T05:08:00+08:00
**Framework:** arifOS L4 Sovereign
**Seal:** DITEMPA BUKAN DIBERI — 999 SEAL ALIVE

***

## Executive Summary

GEOX is not a visualization tool, not a petrophysics calculator, and not a documentation dump. It is designed to be a **governed Earth API** — a three-layer intelligence stack where a deterministic physics engine (`geox_core`) exposes a thin, schema-validated surface (`geox_mcp`) to AI agents, guided by a structured knowledge pack (`resources/`). MCP is the alignment bridge: it makes a physics-blind LLM talk to a physics-grounded Earth model through a governed, claim-disciplined contract. The LLM narrates and red-teams. GEOX computes and governs. Arif judges.

***

## Part 1 — Eureka Insights from the Forge

### 1 · The Repo Entropy Principle

A messy repo is not a *big repo* problem. It is a *competing-root* problem. GEOX had multiple MCP servers, multiple registries, and multiple entry points. Agents hallucinate when given too many doors.

**Resolution:** One root. One server. One registry. The target bundle provides a strict separation between standard library (`src/`) and MCP exposure layer (`src/geox_mcp/`).

### 2 · The Abstraction Paradox (Earth vs. Language)

**The Problem:** LLMs are excellent at pattern-matching curves (e.g., "GR rising, RT dropping") but fail at causal, cross-scale 3D geological storytelling if allowed to guess. Geology requires causal constraints; otherwise, AI hallucinations invent impossible rocks.

**The Solution:** The target GEOX bundle provides hard separation. The LLM handles **language, red-teaming, and hypotheses**. The GEOX MCP backend handles **deterministic petrophysics, strict equations, and geometric limits**. The LLM queries; the engine calculates.

### 3 · MCP is the USB-C of Intelligence

MCP provides async tasks, skills, elicitation, and session-handling. It moves GEOX from being a basic script to being an actual "Earth Intelligence Node" that agents plug into. The standard gives us the protocol to enforce constitutional physics.

***

## Part 2 — GEOX MCP Target Surface Specification

This is the specification of what GEOX MCP is designed to expose.

### 1 · Tools (13 Canonical + 4 Abductive)

The target architectural surface implements strict boundaries between data, reasoning, simulation, and governance.

**Tier 1 — Data Ingestion & QC (Layer 0)**
* `geox_task_ingest_las_batch` — Async ingestion of raw curves.
* `geox_qc_log_integrity` — Detects gaps, spikes, and missing headers.
* `geox_fetch_core_data` — Retrieve deterministic core reports.

**Tier 2 — Petrophysics & Deterministic Computation (Phase B)**
* `geox_calc_vshale`
* `geox_calc_porosity`
* `geox_calc_water_saturation`
* `geox_evaluate_net_pay`

**Tier 3 — Structural & Seismic (Phase C/D)**
* `geox_query_horizon`
* `geox_simulate_fault_seal`
* `geox_extract_seismic_attribute`

**Tier 4 — The "Abductive" Synthesizers (New Horizon)**
* `geox_hypothesize_depo_env` — Given Phase B logs, suggest valid facies (with confidence %).
* `geox_scan_contradictions` — (e.g., "You claim deep marine, but core shows root traces.")
* `geox_simulate_forward_model` — If we assume Facies X, what should the synthetic seismic look like?

**Tier 5 — The Governed Gate**
* `geox_seal_interpretation` — Pushes a validated narrative to the Vault.

### 2 · Prompts (The Forge Templates)

The target bundle provides templates that constrain LLM behavior:

* `geox_prompt_red_team_logs` — Force the LLM to attack a petrophysical interpretation.
* `geox_prompt_facies_narrative` — Force the LLM to write a facies story using *only* retrieved core/log facts.
* `geox_prompt_seismic_tie` — Guide the LLM to correlate well tops with seismic horizons.

### 3 · Resources (The Knowledge Substrate)

Resources the target bundle exposes to agents as structured data:

* `resource://geox/manual/petrophysics` — The equations and limits GEOX uses.
* `resource://geox/catalogs/depositional_environments` — The valid taxonomy of environments.
* `resource://geox/data/project_xyz/summary` — The live state of the current project.

***

## Part 3 — Architectural Directives

1. **Never Compute in the Prompt.** The LLM must not do math. It must call `geox_calc_*`.
2. **Confidence is Mandatory.** Every subjective tool must return a confidence score and a list of alternative hypotheses.
3. **Contradiction is a Feature.** `geox_scan_contradictions` is the most important tool. The engine must actively fight the LLM if the LLM proposes an interpretation that violates the physics or the data.

## Validation Status

- **Validated ✅:** GEOX live registry exists and is healthy; Governance framing is correct; Low-entropy design is correct.
- **Partial / Target ⚖️:** Phase B petrophysics, X3D rendering, and specific Tier 3/4 tools are target architectural specifications under active implementation.
