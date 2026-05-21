# Repo Hygiene Audit - 2026-05-21

## git status --short
```
 M docs/AGENT_LAYOUT_CONTRACT.md
 M docs/ANALOG_DIGITIZATION_MODE_SPEC.md
 M docs/GEOX_PETROPHYSICS_BLUEPRINT.md
 M docs/GEOX_TECHNICAL_ARCHITECTURE_v0.7.0.md
 M docs/GEOX_UNIFIED_ARCHITECTURE.md
 M docs/analysis/GEOX_CONTRAST_ANALYSIS.md
 M docs/analysis/MACROSTRAT_ANALYSIS.md
 M docs/analysis/MACROSTRAT_REPO_ANALYSIS.md
 M src/geox_core/core/physics_guard.py
 M src/geox_core/engines/seismic/vision_bridge.py
 M src/geox_mcp/tools/seismic_well_tie.py
?? docs/REPO_HYGIENE_AUDIT_2026-05-21.md
```

## git branch --show-current
```
chore/repo-hygiene-geox-20260521
```

## git log --oneline --decorate --graph --max-count=12
```
* b4a12f31 (HEAD -> chore/repo-hygiene-geox-20260521, origin/main, origin/HEAD, main) genesis: inscribe GEOX scar-weight doctrine into canonical charter
* f212dbf7 REPO=ariffazil/geox
* 17ece167 test: add verified E2E suite for all 10 registered GEOX tools
* 42ddc52f deps: add torch optional dep for PINN; purge dead registry
* 93a0b047 deps: resurrect fastmcp from pre-1.0 extinction to 3.2.4
* 607d4863 feat(GEOX): add seismic well-tie, vision membrane, and PhysicsGuard
* 4f0ed554 (tag: v2026.05.19) chore(GEOX): bump version for smithery contract fix release
* 1da9d390 fix(GEOX): fix YAML syntax in smithery.yaml governance floors
* 2eebb8e3 docs: SOT header + AGENTS.md + CHANGELOG + CODEOWNERS
* 6e0d4c00 docs: forge boundary governance baseline
* aac9ce43 chore: advance next-horizon state and reduce chaos
* c32d0c73 GEOX ontology: electrofacies cross-ref + petrophysics assumptions registry
```

## git log --oneline origin/main..HEAD
```
```

## git diff --stat
```
 docs/AGENT_LAYOUT_CONTRACT.md                  | 155 ++++++++++++++++++-------
 docs/ANALOG_DIGITIZATION_MODE_SPEC.md          |   2 +-
 docs/GEOX_PETROPHYSICS_BLUEPRINT.md            |  30 ++---
 docs/GEOX_TECHNICAL_ARCHITECTURE_v0.7.0.md     |  14 +--
 docs/GEOX_UNIFIED_ARCHITECTURE.md              |  22 ++--
 docs/analysis/GEOX_CONTRAST_ANALYSIS.md        |  36 +++---
 docs/analysis/MACROSTRAT_ANALYSIS.md           |   8 +-
 docs/analysis/MACROSTRAT_REPO_ANALYSIS.md      |   6 +-
 src/geox_core/core/physics_guard.py            |   2 +
 src/geox_core/engines/seismic/vision_bridge.py |  21 ++--
 src/geox_mcp/tools/seismic_well_tie.py         |   2 +-
 11 files changed, 183 insertions(+), 115 deletions(-)
```

## git diff --check
```
PASS
```

## verification

```txt
pytest tests/test_geox_mcp_benchmark.py tests/test_geox_sovereign_e2e.py -q: PASS (6/6)
pytest tests/ -q: PASS (51 passed, 1 skipped)
```
