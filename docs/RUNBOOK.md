# RUNBOOK.md — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Port:** 8081 | **Canonical tools:** Runtime fact — verify with `tools/list`
> **Last Updated:** 2026-07-09
> **Source of truth:** `src/geox_mcp/registry.py` + `server.py` _EXPECTED_CANONICAL

## Start / Stop
```bash
systemctl start geox-mcp
systemctl stop geox-mcp
systemctl restart geox-mcp
systemctl status geox-mcp
```

## Health Check
```bash
curl -s http://127.0.0.1:8081/health | python3 -m json.tool
# Expected: status=healthy, service=geox-unified, canonical_tools=56
```

## Federation Map (W16+)

GEOX is one of **7 organs** in the arifOS federation. Live at `https://geox.arif-fazil.com/mcp`.

| Organ | Port | Transport | Tools | Status |
|-------|------|-----------|-------|--------|
| arifOS | 8088 | streamable-http | 22 canonical | ✅ healthy |
| **GEOX** | **8081** | **streamable-http** | **56 canonical** | **✅ healthy** |
| WEALTH | 18082 | streamable-http | 19+ | ✅ ALIVE |
| WELL | 18083 | streamable-http | 21 | ⚠️ degraded |
| A-FORGE | 7071/7072 | streamable-http | sense + 77 | ✅ healthy |
| AAA | 3001 | mcp-endpoint-registry | 0 | ✅ healthy |
| VAULT999 | 5001/8100 | (append-only) | 0 | ✅ healthy |

All organs use FastMCP 3.x + streamable-http + protocol_version `2025-11-25`.

## Logs
```bash
journalctl -u geox-mcp -n 50 --no-pager
journalctl -u geox-mcp -f   # follow
```

## Tests
```bash
cd /root/geox
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -q --tb=short
# Expected: 89 passed, 3 skipped (live-server drift)
```

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `/health` returns no canonical_tools field | Service not restarted after registry change | `systemctl restart geox-mcp` |
| `/health` unreachable | Service crashed | `systemctl restart geox-mcp` then `journalctl -xe` |
| `/mcp` returns 404 | Caddy misroute | Check `/etc/caddy/Caddyfile` GEOX block |
| Tools returning errors | Python env broken | `pip install -e ".[dev]"` then restart |
| F0_CONSTITUTION_BREACH at startup | `_EXPECTED_CANONICAL` out of sync with registry | Update both `server.py` and `contracts/canonical_registry.py` |
| Port conflict | Another process on 8081 | `ss -tlnp | grep 8081` |
| `EMAG2Fetcher.fetch()` returns mode=offline_stub | Local cache missing or `GEOX_EMAG2_OFFLINE=1` | Set `GEOX_EMAG2_OFFLINE=0`; ensure `/root/.cache/geox/emag2/EMAG2_V3_UpCont_DataTiff.tif` exists |
| `geox_prithvi_eo_inference` returns mock data | `GEOX_PRITHVI_LIVE` not set | Requires `terratorch` + Prithvi weights + GPU (888_HOLD) |

## What NOT to Do
- Do NOT bind to 0.0.0.0 (must be 127.0.0.1 — Caddy/Tunnel handles public)
- Do NOT modify GENESIS/ without F13 approval
- Do NOT change canonical tool surface without updating BOTH `src/geox_mcp/registry.py` AND `contracts/canonical_registry.py` AND `server.py:_EXPECTED_CANONICAL`
- Do NOT deploy FM live weights without 888_HOLD
- Do NOT skip the F0 registry truth test before deploy (`pytest tests/unit/test_registry_runtime_truth.py`)

## W2-W13+ FORGE Operational Notes

### Doctrine tools (JUDGMENT lane — lease + session required)
```python
# Register an assumption in the lineage
await geox_doctrine_assumption_register({
    "introduced_by": "geox_seismic_compute",
    "rung_origin": 3,  # DERIVATION
    "description": "Faust velocity with k=2.288, exp=1/6"
})

# Audit a claim for rhetoric-vs-evidence ratio
audit = await geox_doctrine_anti_beautiful_one({
    "text": "Clearly proven beyond doubt that...",
    "grounding_evidence_count": 1,
    "grounding_evidence_rungs": [3],
})
# Returns beauty_overreach_score; if > 1.5 → FORCE_DECOMPOSITION

# Seal a claim via Gödel Wall
verdict = await geox_doctrine_godel_review({
    "claim_id": "CLM-abc123",
    "action": "seal"  # or "review" or "void"
})
# Returns KNOWN/UNKNOWN/UNDECIDABLE_YET/VOID verdict
```

### Multi-physics joint inversion
```python
result = await geox_joint_inversion({
    "observations": [
        {"modality": "seismic_impedance", "value": 6.93e6, "uncertainty": 0.05},
        {"modality": "gravity", "value": -0.42, "uncertainty": 0.10, "depth_m": 2000},
        {"modality": "magnetic", "value": 12.5, "uncertainty": 0.20, "depth_m": 2000},
        {"modality": "mt_resistivity", "value": 20.0, "uncertainty": 0.10, "depth_m": 2000},
    ],
    "max_iter": 50,
    "tolerance": 1e-3,
})
# Returns: state (Physics9State), grade (RAW/AAA), residual_rms, per_modality breakdown
```

### WEALTH feed
```python
feed = await geox_wealth_feed({
    "cell_states": [sandstone.to_dict(), sandstone.to_dict(), ...],
    "areal_extent_m2": 1e6,
    "pay_zone_thickness_m": 50,
    "water_saturation": 0.20,
})
# Returns: STOIIP, P10/P50/P90 phi, ADVANCE/DEFER/REJECT verdict
```

### WELL operator gate
```python
gate = await geox_well_decision_class({
    "operator_id": "arif",
})
# Returns: C1/C2/C3/C4/C5 decision_class
# C5 = HOLD — no joint inversions allowed
```

### Geomechanics
```python
result = await geox_geomechanics({
    "state": sandstone.to_dict(),
})
# Returns: K_GPa, G_GPa, E_GPa, ν, AI, sanity_flags, grade
```

## Open Data Refresh

### EMAG2v3 V3
```bash
# Check current cache
ls -la /root/.cache/geox/emag2/

# Re-download (~228 MB)
GEOX_EMAG2_OFFLINE=0 python3 -c "
from geox_core.io.emag2_fetcher import EMAG2Fetcher
EMAG2Fetcher().download_emag2()
"

# Verify SHA-256
sha256sum /root/.cache/geox/emag2/EMAG2_V3_UpCont_DataTiff.tif
# Expected: 719db9d060a423b7292f09fa4312e7d0ebd4e284ba652079b34e3d05be5a370a
```

### Prithvi-EO-2.0 (when greenlit)
```bash
# Install terratorch
pip install terratorch

# Set weights path
export GEOX_PRITHVI_LIVE=1
export GEOX_PRITHVI_WEIGHTS=/srv/models/prithvi-eo-2.0

# Restart service
systemctl restart geox-mcp
```

## Rollback Procedure

If the W13+ FORGE breaks something in production:

```bash
# 1. Roll back to last known-good commit
cd /root/geox
git log --oneline -5
git revert --no-commit 657b9eb0
# Or: git reset --hard 7cb1d5c8 (HEAD before W13+)

# 2. Restart service
systemctl restart geox-mcp

# 3. Verify health
curl -s http://127.0.0.1:8081/health | python3 -m json.tool

# 4. Run regression
PYTHONPATH=src pytest tests/ -q --tb=short
```

## Emergency Contacts

- **Live service down:** `journalctl -u geox-mcp -n 100 --no-pager`
- **Constitutional breach:** File 888_HOLD via `geox_claim_seal` route
- **Data corruption:** Check EMAG2 cache SHA-256 vs expected

---

*Last operator: FORGE (000Ω) under F13 SOVEREIGN authorization, 2026-06-21.*
