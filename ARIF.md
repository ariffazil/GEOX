# ARIF.md | METABOLIC KERNEL v1.0

> SYSTEM TYPE: LORE INTERFACE
> GOVERNANCE: arifOS AAA
> VETO: 888 JUDGE
>
> INVARIANT: Descriptive memory of repo state.
> This file NEVER modifies Law. It only reports and compresses observed reality.


## 0. IDENTITY & MOUNT POINT

- REPO_NAME: GEOX
- CONTAINER_ID: 2026-04-23
- DOMAIN_ROLE: Physics9 Earth Intelligence — constitutional subsurface reasoning layer for exploration geoscience
- STABILITY_CLASS: RAPID-ITERATE


## 1. CURRENT FOCUS (INSTRUCTION POINTER)

- VPS restoration via Hostinger panel — unblock MCP endpoint (arifosmcp.arif-fazil.com → 502)
- Status: HARD_BLOCK — server offline since 2026-04-23


## 2. OPERATIONAL MANDATE

- What this repo does: GEOX is the Earth Intelligence layer — MCP server exposing 24 subsurface tools (well, seismic, prospect, map, time4D) governed by arifOS F1–F13 constitutional floors
- Upstream: arifOS kernel (mcp.arif-fazil.com) — depends on VPS for MCP transport
- Downstream: Petronas/SLB engineers, geoscientists consuming GEOX MCP tools; AAA workspace references GEOX for well log and seismic data


## 3. THE 999 SEAL (SESSION LOG)

- TIMESTAMP: 2026-04-23 15:30 UTC+8
- CLERK_ID: arifOS_bot / HUMAN-ARIF
- SEAL_SUMMARY:
  - README aligned: 13→24 tools, MIT→Apache 2.0, VPS marked ⚠️ DEGRADED (not LIVE)
  - License confirmed Apache 2.0 (commit 448fe772)
  - FLOORS.md runtime state updated: 6/13 floors wired (F2/F3/F7/F9/F11/F12)
  - wiki/50_TOOLS reference fix needed (path is directory, not file)
  - ARIF.md Gold Seal v1.0 pushed to AAA (c4061f3)
  - arifmeta-v1.0.json schema pushed to AAA (b959e60)
  - Gist published: https://gist.github.com/ariffazil/81314f6cda1ea898f9feb88ce8f8959b
  - ARIF-999-SEAL-RITUAL.md pushed to AAA (69d82eb)
- VAULT_REF: https://github.com/ariffazil/AAA/commit/69d82eb


## 4. ACTIVE TOPOLOGY (MEMORY MAP)

- CRITICAL_FILES:
  - `geox_mcp/server.py` → MCP server (24 @mcp.tool decorators, 11 @mcp.resource, 2 @mcp.prompt)
  - `wiki/70_GOVERNANCE/` → F1–F13 floor definitions
  - `wiki/50_TOOLS/` → tool index (NOTE: is directory, not .md file — path reference fix needed)
  - `LICENSE` → Apache 2.0 (confirmed 448fe772)

- ENTRYPOINTS:
  - `python geox_mcp/server.py` → MCP server on port 8080
  - `curl https://geox.arif-fazil.com/health` → health check (VPS offline — returns error)
  - `pytest` → run test suite

- DATA_FLOWS:
  - `geox_well_load_bundle` → LAS file → petrophysics compute → Sw/Phi/Vsh output
  - `geox_prospect_evaluate` → volumetric input → DRO/DRIL/HOLD verdict → arifOS 888_JUDGE
  - `geox_mcp` → arifOS kernel (mcp.arif-fazil.com) — transport layer on VPS


## 5. INTERRUPTS & FAULTS (BLOCKERS)

- HARD_BLOCK: VPS offline (CF ERROR 1000, port 22 timeout) → MCP endpoint 502, geox.arif-fazil.com down → impact: full MCP transport blocked → workaround: none until Hostinger panel access restored
- SOFT_FRICTION: wiki/50_TOOLS path is directory not file → impact: broken cross-link in README → workaround: update wiki index to point to correct path


## 6. RECENT SCARS (W_scar)

- [README claimed 13 tools but code has 24] → [Ran full tool audit via grep] → [Always audit actual decorators, not marketing docs] → [Never trust README over code]
- [VPS marked LIVE in README but actual status is 502] → [Added ⚠️ DEGRADED badge] → [Status badges must reflect real state, not aspirational]


## 7. EXECUTION BUFFER (COMMANDS)

| Command | Status | Context |
|---------|--------|---------|
| `python geox_mcp/server.py` | ✅ | Local dev — works offline |
| `curl https://geox.arif-fazil.com/health` | ❌ | VPS offline — returns error |
| `pm2 restart all` | ⚠️ | Requires VPS access — run after restore |
| `git push origin main` | ✅ | Works from af-forge |

## 8. PRIVILEGE ESCALATION (888 HOLD)

- [Q]: Should GEOX auto-deploy to alternative VPS if Hostinger is not restored within 48h?
- [CONTEXT]: MCP endpoint is critical for production use. Current VPS is unmanaged. No clear SLA. Ω₀ = 0.7

## 9. PIPELINE PREFETCH (NEXT MOVES)

- [ ] Restore VPS via Hostinger panel → then run `pm2 restart all`
- [ ] Fix wiki/50_TOOLS reference (it's a directory — update index)
- [ ] Run full test suite after VPS restore
- [ ] Merge pending arifOS cleanup branches (cleanup/unix-style-2026-04-23, architecture-normalization-final-clean)


---

*🪙 GOLD SEAL | METABOLIC KERNEL v1.0 | arifOS AAA | 888 JUDGE VETO | DITEMPA BUKAN DIBERI*
*Readable by: single human · couple · company · institution · AI agent · machine · team · civilisation intelligence*