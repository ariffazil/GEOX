# RUNBOOK — GEOX Operations

> Concrete, executable steps. Not theory. Not doctrine.

## 1. Start / Stop / Restart

```bash
# systemd (production)
sudo systemctl start geox-mcp.service
sudo systemctl stop geox-mcp.service
sudo systemctl restart geox-mcp.service
sudo systemctl status geox-mcp.service

# local dev
uv run python -m geox_mcp.server --host 127.0.0.1 --port 8081

# health check
curl -s http://127.0.0.1:8081/health | jq
curl -s http://127.0.0.1:8081/drift | jq
```

## 2. Surface drift (canonical vs live)

```bash
# Compare SOT (31) to runtime
curl -s http://127.0.0.1:8081/drift | jq '.drift_count, .gap_count, .ok'

# Regenerate manifests (after a tool add/remove in registry.py)
uv run python scripts/generate_all_surfaces.py

# Re-deploy to clear drift
cd /opt/geox && git pull && sudo systemctl restart geox-mcp.service
```

## 3. Constitutional audit (every push to main)

```bash
bash scripts/governance-gate.sh
# Required: PASS: ≥8, FAIL: 0
# Common fail modes:
#   - README.md < 500 lines → WARN; < 200 → FAIL
#   - hardcoded secret → FAIL (gate Q6)
#   - missing AGENTS.md / FEDERATION.md / FEDERATION_CONTRACT.md → FAIL
#   - port not mentioned in README → WARN
```

## 4. Add a tool (the right way)

1. Implement the function in `src/geox_mcp/tools/<family>.py`
2. Decorate with `@mcp.tool(name="geox_<name>", annotations=_geox_annotations(...))`
3. Register in `src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS`
4. Add tool name to `CANONICAL_PUBLIC_SURFACE.json` (or re-run `generate_all_surfaces.py`)
5. Add 3-line entry to `contracts/tools.yaml` (name, tier, action_class)
6. Update README "Tool inventory" section
7. Run `bash scripts/governance-gate.sh` (must pass)
8. Run `pytest tests/ -q` (must pass)
9. Commit on a branch, push, open PR with the federation `REPO=` trailer

## 5. Investigate a failing tool

```bash
# Tail the service logs
sudo journalctl -u geox-mcp.service -n 200 -f

# Or, in dev:
uv run python -m geox_mcp.server --host 127.0.0.1 --port 8081 \
    --log-level DEBUG

# Run a single tool directly:
PYTHONPATH=src python -c "
import asyncio
from geox_mcp.server import create_mcp_server
mcp = create_mcp_server()
tool = mcp._local_provider._components['tool:geox_basin@local']
print(tool.fn)
"

# Run pytest with -k for one tool:
PYTHONPATH=src pytest tests/test_basin_synthesis_pipeline.py -v -k test_basin_overview
```

## 6. Federation gate (arifOS-side)

If arifOS's `Kernel ABI generated-surface drift guard` fails on GEOX:
1. Run `uv run python scripts/sync_kernel_abi.py` locally — should print
   "Kernel ABI verified"
2. If it does, regenerate the GEOX-side surface files and re-push
3. If it doesn't, the tool count is drifting; fix in `registry.py`

## 7. NW Borneo Collision System (specific)

The 6 basin entities live in `resources/basins/`:
- `nw_borneo_collision_system/` — parent + event registry
- `layang_layang_basin/` — lower plate (RU drowning)
- `sabah_trough/` — foredeep / flexural moat
- `kinabalu_basin/` — upper plate (DRU uplift)
- `dangerous_grounds/` — crustal source province
- `northwest_borneo_trough/` — fossil trench axis (HOLD: polarity/timing)

One event → three expressions per position. **Do not unify the reflectors.**

To regenerate:
```bash
PYTHONPATH=src pytest tests/test_sabah_collision_system_ingest.py -v
```

## 8. Banned patterns (the gate enforces)

- **Empty SUCCESS** — `ok: true` with empty `observed/derived/interpreted`. Refuse.
- **Verdict smuggling** — returning `SEAL`/`HOLD`/`VOID` from GEOX. Use signals.
- **Path leaks** — error messages containing `/root/WELL/...` (test paths only).
- **Forbidden claims** — `crystalline_basement_default`, `drilling_decision`, etc.
  Always populate `forbidden_claims` from per-claim `forbidden_uses`.

## 9. When the well is dry (you suspect a regression)

```bash
# 1. Drift
curl -s http://127.0.0.1:8081/drift | jq

# 2. Audit
bash scripts/governance-gate.sh

# 3. Tests (quick)
PYTHONPATH=src pytest tests/ -q --tb=short

# 4. Tests (specific module)
PYTHONPATH=src pytest tests/test_seismic_interpret_contract.py -v

# 5. Federation surface
uv run python scripts/sync_kernel_abi.py --check

# 6. Logs
sudo journalctl -u geox-mcp.service -n 200 --no-pager

# 7. If still stuck, file an incident in the AAA cockpit:
#    POST /cockpit/incident with run URL + symptoms + recent commits
```

## 10. The 3 sentences that sum up GEOX

1. **GEOX computes evidence; arifOS judges.**
2. **Empty SUCCESS is a lie.**
3. **If canonical and live disagree, redeploy — the gap means the runtime hasn't caught up.**
