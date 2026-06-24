<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-24
valid_from: 2026-06-24
valid_until: 2026-07-24
confidence: high
scope: /root/geox
-->

# Federation Contract — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Repo:** `ariffazil/geox` | **Port:** 8081
> **Canonical federation contract:** [`ariffazil/arifos/FEDERATION_CONTRACT.md`](https://github.com/ariffazil/arifos/blob/main/FEDERATION_CONTRACT.md)
> **Role:** Earth evidence coprocessor — witness, never authorize.
> **DITEMPA BUKAN DIBERI — Forged, Not Given.**

---

## 1. Position in the Federation

```
Arif (F13 SOVEREIGN)
  → arifOS kernel (8088) — constitutional judgment
    → GEOX (8081) — Earth evidence
      → arifOS 888 JUDGE — SEAL / SABAR / HOLD / VOID
        → A-FORGE (7071/7072) — execution under SEAL
          → VAULT999 — immutable audit ledger
```

GEOX is the **Earth Intelligence** organ. It ingests seismic, well logs, gravity, magnetic, MT, and EO data; runs physics-constrained computations; and outputs structured evidence receipts.

---

## 2. Authority

### GEOX OWNS
- Well log analysis, petrophysics, stratigraphy
- Seismic intelligence: attributes, AVO, inversion, well tie
- Basin screening, prospect evaluation, volumetrics
- Multi-physics joint inversion (Physics9State)
- Vision AI interpretation with AC_Risk scoring
- Structured claim creation, validation, and challenge

### GEOX NEVER
- Issues drilling decisions
- Allocates capital or authorizes trades
- Adjudicates constitutional verdicts
- Self-authorizes irreversible actions
- Claims certainty without uncertainty bands

---

## 3. External Contracts

| Contract | Canonical Location | Purpose |
|---|---|---|
| Federation topology | `ariffazil/arifos/FEDERATION_CONTRACT.md` | Organ roles and authority chain |
| Constitutional floors | `ariffazil/arifos/static/arifos/theory/000/000_CONSTITUTION.md` | F1–F13 |
| Agent landing | `/root/geox/AGENTS.md` | Build/test/run rules for this repo |
| Constitutional charter | `/root/geox/GENESIS/` | Binding GEOX doctrine |
| Tool registry | `/root/geox/src/geox_mcp/registry.py` | Canonical tool surface |

---

## 4. MCP Surface

- **HTTP/SSE:** `https://geox.arif-fazil.com/mcp`
- **stdio:** `python3 -m geox_mcp.server --transport stdio`
- **Canonical tools:** 16 mode-based / 56 compat names (W16+ FORGE)
- **Binary transport:** `geox://render/cubes/{cube_id}/...` MCP resources

---

## 5. Handoffs

| To | When | Format |
|---|---|---|
| arifOS 888 JUDGE | Claim ready for constitutional verdict | `geox_claim_seal` |
| WEALTH | Prospect economics | `geox_wealth_feed` |
| WELL | Human-readiness gate before field ops | `geox_well_decision_class` |
| AAA | Cockpit display | `RenderPayload` + MCP resources |
| A-FORGE | Execution under SEAL | Via arifOS `arif_forge_execute` |

---

## 6. Verdict

GEOX tells you what the Earth looks like. It does not tell you to drill. The sovereign decides.

*DITEMPA BUKAN DIBERI.*
