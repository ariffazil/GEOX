# FEDERATION.md — GEOX

```yaml
role: DOMAIN
organ: geox
layer: L3
citizenship: warga-aaa
canon: ariffazil/ariffazil

depends_on:
  - repo: ariffazil/arifOS
    reason: Evidence routing, governance gates, constitutional compliance

mcp:
  port: 8081
  endpoint: https://geox.arif-fazil.com/mcp
  tools_count: 15
  tool_prefix: geox_
  public_tools:
    - geox_basin
    - geox_petrophysics
    - geox_seismic_compute
    - geox_seismic_ingest
    - geox_seismic_interpret
    - geox_well_ingest
    - geox_well_desk
    - geox_claim
    - geox_deep_time_state
    - geox_falsify
    - geox_geomechanics
    - geox_gravmag_studio
    - geox_prospect
    - geox_sequence
    - geox_subsurface_model
    - geox_surface_status

governance:
  judge: arifOS
  seal: VAULT999
  floors: F1-F13
  mutation_rule: NEVER mutate. Compute evidence only. arifOS judges; A-FORGE executes.

stack_role: |
  GEOX is the earth intelligence organ — L3 DOMAIN.
  It computes geoscience evidence: basin analysis, petrophysics, seismic,
  prospect evaluation, well data. It NEVER adjudicates, NEVER executes.
  All evidence flows through arifOS governance gates before any action.
  GEOX speaks geology. arifOS speaks law. A-FORGE speaks action.

entrypoints:
  - MCP: https://geox.arif-fazil.com/mcp
  - Health: http://localhost:8081/health
  - Code: https://github.com/ariffazil/geox
```

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
**Part of the arifOS Federation. See `/root/AAA/docs/FEDERATION_MAP.md` for canonical topology.**
