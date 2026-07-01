# GEOX Copilot — Resource Index
> arifOS Federation | Sovereign: Arif | Last reorganised: 2026-06-10
> DITEMPA BUKAN DIBERI — Forged, Not Given

---

## What this folder is

This folder contains all resources for deploying and operating the **GEOX Copilot agent** — across Microsoft Copilot Studio, GitHub Copilot (VS Code), and the arifOS federation MCP surface.

It is organised by purpose, not file type. Copilot-loadable files are clearly separated from archives.

---

## Load map — what goes where

| File | Load target | Notes |
|------|-------------|-------|
| `system-prompts/00-geox-coarch.md` | Copilot Studio → Instructions field | Primary GEOX coarchitect system prompt |
| `system-prompts/01-arifo-kernel.md` | Copilot Studio → Instructions field | arifOS kernel — use when sovereign context is primary |
| `system-prompts/02-arifo-constitutional.md` | Copilot Studio → Instructions field | Full 13-floor constitutional spec (SEALED v46.2) |
| `system-prompts/03-audience-calibration.md` | Copilot Studio → Instructions field | **Persona-aware reply protocol** — Arif / VP / Geoscientist / Auditor |
| `knowledge/federation/AGENTS.md` | Copilot Studio → Knowledge | arifOS integration + 13 floors overview |
| `knowledge/federation/federation-index.md` | Copilot Studio → Knowledge | **START HERE** — 7-repo map, roles, boundaries |
| `knowledge/federation/llms.md` | Copilot Studio → Knowledge | LLM governance — thermodynamic model, deployment steps |
| `knowledge/federation/physics-math-language.md` | Copilot Studio → Knowledge | Physics-Math-Language trinity architecture |
| `knowledge/geox/geox-spec.md` | Copilot Studio → Knowledge | GEOX full spec — 4-plane architecture, contracts, tools |
| `knowledge/geox/geox-arifo-spec.md` | Copilot Studio → Knowledge | GEOX condensed spec — copy-paste ready for Studio |
| `knowledge/geox/kinabalu-basin.md` | Copilot Studio → Knowledge | Kinabalu Basin biostratigraphy + domain context |
| `knowledge/aaa/aaa-identity-spec.md` | Copilot Studio → Knowledge | AAA identity control plane surface |
| `knowledge/a-forge/aforge-execution-spec.md` | Copilot Studio → Knowledge | A-FORGE execution layer surface |
| `knowledge/wealth/wealth-mcp-summary.md` | Copilot Studio → Knowledge | WEALTH capital organ surface |
| `knowledge/well/well-vitality-spec.md` | Copilot Studio → Knowledge | WELL vitality substrate surface |
| `artifacts/artifact-a-search.md` | Copilot Studio → Knowledge | Governed web/file search artifact spec |
| `artifacts/dtc-999-template.md` | Copilot Studio → Knowledge | Decision Trace Card template (DTC-999) |
| `agents/GEOX.agent` | VS Code / Copilot Studio import | Binary agent definition — import directly |
| `agents/copilot-studio-guide.md` | Reference only | Step-by-step Copilot Studio build guide |
| `mcp/server.py` | Deploy to VPS | MCP compatibility proxy — forwards to arifOS upstream |
| `_archive/*` | Reference only — do NOT load | Raw repo exports (5–6M chars each, unusable as knowledge) |

---

## Federation coverage

| Repo | Copilot file |
|------|-------------|
| arifOS | `system-prompts/01-arifo-kernel.md`, `system-prompts/02-arifo-constitutional.md`, `knowledge/federation/AGENTS.md` |
| geox | `knowledge/geox/geox-spec.md`, `knowledge/geox/geox-arifo-spec.md` |
| AAA | `knowledge/aaa/aaa-identity-spec.md` |
| A-FORGE | `knowledge/a-forge/aforge-execution-spec.md` |
| wealth | `knowledge/wealth/wealth-mcp-summary.md` |
| well | `knowledge/well/well-vitality-spec.md` |
| ariffazil | `knowledge/federation/federation-index.md` (cross-repo map) |

---

## Hard rules for this folder

1. **Nothing in `_archive/` gets loaded into Copilot** — those are raw exports, not knowledge.
2. **No new tools added to `src/geox_mcp/registry.py`** without Arif explicit approval.
3. **System prompt files stay under 8,000 chars** for Copilot Studio Instructions field compatibility.
4. **Knowledge files: FACT vs INTERPRETATION vs UNKNOWN must be explicit** — no silent assumption.
5. **Agent behaviour rule (Arif's explicit directive 2026-06-10):** GEOX must distinguish bijaksana from bangang. Call out unsupported claims. Never assume vendor maturity without evidence. Say "NO DATA OR EVIDENCE" when there is none.

---

## Epistemic posture (mandatory)

GEOX does not say "not biased." GEOX says:
> "My reasoning is constrained to authorised data. Where data is absent, I say UNKNOWN. Where a claim has no evidence, I say NO EVIDENCE FOUND. I do not fill gaps with assumptions."

This is stronger than "balance." Balance is a form of bias. Evidence discipline is not.
