# GEOX — Structural-Vision Integration Map

**Type:** read-only architecture audit
**Scope:** how a new *deterministic* structural-vision lane sits against the existing GEOX surfaces
**Auditor:** Hermes subagent (read-only; this file is the only artifact produced)
**Repo root:** `/root/GEOX`
**Interpreter used for all probes:** `/root/GEOX/.venv/bin/python`

## 0. Snapshot discipline

Three other agents were writing to this repo **during** the audit. Every claim below is
tied to the file content observed at the moment of the hash. Re-check hashes before relying
on a claim.

```
SNAPSHOT @ 2026-09-17T20:22:52Z   (local 2026-09-18T04:22:52+08)
git HEAD              886de317
working tree          M src/geox_mcp/tools/structure_gates/__init__.py
                      ?? src/geox_core/ontology/tectonic_events/regime_invariants.yaml
                      ?? src/geox_core/vision_structural/
                      ?? src/geox_mcp/prompts/structural_invariants.py
                      ?? src/geox_mcp/servers/structural_vision.py
                      ?? src/geox_mcp/tools/structural_vision.py
                      ?? src/geox_mcp/tools/structure_gates/tectonic_regime.py
                      ?? tests/test_tectonic_regime_falsification.py

md5
c5ecda9a3ebed938fb882bf178db628c  src/geox_mcp/servers/vision.py
c58930c8cb3f69518c6a58fa5e407959  src/geox_mcp/tools/vision.py
f9de570cc7cbf16ec6c7e08301b4ad30  src/geox_mcp/tools/structural_vision.py
2bbae1268a1c06ca97a4f82c523f12d0  src/geox_mcp/servers/structural_vision.py
aa3481c70329d628cfe772ab37d4e6ab  src/geox_mcp/tools/structure_gates/__init__.py
0e3c9fc6d2e10f021d7362d510de0cd7  src/geox_mcp/tools/structure_gates/tectonic_regime.py
06480501852db81a783905647b57707f  src/geox_mcp/tools/structural_restoration/wiring.py
e7d0d13fa7d190aaab80726d63e939f2  src/geox_mcp/tools/falsify.py
a400653c10fbadcd5801999693423622  src/geox_mcp/tools/seismic_interpret.py
80adcae23766b25d30c08ecf56199477  src/geox_mcp/tools/seismic_classical.py
711cacc0765a8d27eb08aa3fc9923b3d  src/geox_mcp/tools/contrast_views.py
63005f398c414577afb3cfc1dbfc7230  src/geox_mcp/tools/seismic_zen_f1.py
```

**Live observation already made:** `structure_gates/__init__.py` changed hash **three times**
during this audit (`525298ad…` → `aa3481c7…`), and `geox_core/vision_structural/` gained
`orientation.py` mid-probe. Findings that depend on a mid-write state are labelled
`TRANSIENT` and are not counted as defects.

**Notation.** Every claim is marked `OBSERVED` (read in the file at the snapshot) or
`INFERRED` (reasoning from what was read). No claim is made that was not read.

---

## (a) Inventory — every surface audited

| # | Surface | Path | Status at snapshot | What it actually does |
|---|---|---|---|---|
| 1 | VLM domain server | `src/geox_mcp/servers/vision.py` (79 L) | Live code, **mounted but RT1-unreachable** | Declares `_VISION_TOOLS` = 4 names (L30–35) and mounts them via `register_tools_on_server` (L78). No engine logic. |
| 2 | VLM tools | `src/geox_mcp/tools/vision.py` (771 L) | Live code | 4 async tools: `geox_vision_perceptual_inventory` (L109), `geox_vision_minimax_inference` (L300), `geox_vision_calibrate` (L548), `geox_vision_audit` (L655). A 5th, `geox_vision_mimo_inference` (L420), is defined but **never registered**. |
| 3 | VLM engine | `src/geox_core/engines/vision/` | Live | `perceptual_inventory.py` (Pydantic contracts), `minimax_vlm_adapter.py`, `mimo_vlm_adapter.py`, `vision_test_harness.py`, `run_vision_v1_demo.py`. |
| 4 | Structural gate matrix | `src/geox_mcp/tools/structure_gates/__init__.py` (353 L at snapshot) | Live, **modified mid-audit** | Imports 9 core gates + `REGIME_FALSIFIERS` / `falsify_regime` / `run_regime_falsification` (L27–31). `run_all_structure_gates(framework, *, include_regime_gates=True)` (L222) now merges K-REGIME receipts into `gates` and exposes `combined_verdict_with_regime` / `regime_falsification`. |
| 5 | Tectonic regime engine | `src/geox_mcp/tools/structure_gates/tectonic_regime.py` (1150 L, **new, untracked**) | Live, tested | K-REGIME-* universal gates + 7 regime falsifier families; `falsify_regime` (L987), `run_regime_falsification` (L1048). 27 tests collected (`tests/test_tectonic_regime_falsification.py`, verified by `pytest --collect-only`). |
| 6 | Structural restoration tool wiring | `src/geox_mcp/tools/structural_restoration/wiring.py` (382 L) | **PLANNED — declared, never called** | Defines `register_structural_restoration_tools` (L20) registering 9 MCP tool names (verified count = 9). Nothing imports it. |
| 7 | Restoration engines | `src/geox_core/engines/structural_restoration/` | Live library | `state.py` (`RestorationScenario`), `validate_inputs.py`, `accommodation_diff.py`, `basement_subsidence.py`, `fill_ratio.py`, `invariants.yaml`. |
| 8 | Falsification entry point | `src/geox_mcp/tools/falsify.py` (521 L) | Live code, **RT1-unreachable** | Kill Matrix K001–K007 + lightweight contradiction scan; `geox_falsify` (L385). |
| 9 | Mode dispatch layer | `src/geox_mcp/tools/seismic_interpret.py` (1303 L) | Live | 16 live modes (`_LIVE_MODES` L37–56), 6 declared-not-public modes (`_NOT_YET_MODES` L59–69), strict per-mode Pydantic normalisation (L303–418), handler chain L586–1303. |
| 10 | Deterministic CV primitives | `src/geox_mcp/tools/seismic_classical.py` (338 L) | Live library | `structure_tensor` (L38), `semblance_coherence`, `ridge_extraction`, `dp_horizon_tracker`, `rgt_estimation`, `classical_baseline` (L275). |
| 11 | Deterministic raster attributes | `src/geox_mcp/tools/contrast_views.py` (≈680 L) | Live library | 9 attributes incl. `_edge_map` (Sobel, L152), `_local_dip` (structure-tensor atan2, L192), `_phase_symmetry` (Gabor, L219), `_frequency_content` (L236). Async tool `geox_contrast_views` (L394). |
| 12 | Image→gate geometry | `src/geox_mcp/tools/seismic_zen_f1.py` | Live, **reachable** | `compute_attributes_2d` (L180), `track_horizons_2d` (L284), `measure_throw_from_horizons` (L348) → `dmax_m` / `length_m` / `throw_profile_m`; driven by `mode=measure_throw` (seismic_interpret.py L612–627). |
| 13 | Expansion-index derivation | `src/geox_mcp/tools/structure_gates/calibration_derive.py` (579 L) | Live | `_expansion_index` (L347), writes `fw["expansion_index"] = ei_mean` (L562) / `claims["expansion_index"]` (L567). Header L15: "expansion_index from isochores (K-GROWTH)". |
| 14 | Surface manifest / canonical registry | `src/geox_mcp/tools_manifest.yaml`, `src/geox_mcp/registry.py`, `surface_manifest.py` | Live | `CANONICAL_PUBLIC_TOOLS = SURFACE_TOOLS` (registry.py L57, L67). **31 public tools** at snapshot (verified by import). |
| 15 | Governance middleware | `src/geox_mcp/geox_middleware.py` | Live | `RT1` gate at L704–713; `_EXECUTABLE_SURFACE = public ∪ internal ∪ compat` (L290–292). |
| 16 | **In-flight structural-vision lane** | `src/geox_mcp/tools/structural_vision.py` (789 L, untracked) | **Mid-construction** | `geox_structural_vision_extract` (L358), `geox_structural_regime_falsify` (L679), `strip_forbidden_keys` (L148), `assert_no_forbidden_keys` (L166), `bundle_to_framework` (L559). |
| 17 | **In-flight lane server** | `src/geox_mcp/servers/structural_vision.py` (132 L, untracked) | **Mid-construction** | `_STRUCTURAL_VISION_TOOLS` = 2 names (L78–81), `create_structural_vision_server` (L108). Docstring L14–31 is an explicit separation contract against `servers/vision.py`. |
| 18 | **In-flight CV core** | `src/geox_core/vision_structural/` | **Incomplete** | `CONTRACT.md` (frozen v1.0), `types.py` (`Measurement`, `FORBIDDEN_PROBABILITY_KEYS` L28–35), `orientation.py` (28.5 KB, appeared mid-audit). **No `__init__.py`.** |

### Gate inventory (surface 4 + 5)

Core matrix actually executed at `__init__.py` L274–284:

| Gate id | Function | Module | Status vocabulary | Framework keys consumed |
|---|---|---|---|---|
| `K-DIP` | `gate_k_dip` | `k_dip.py` | `PASSED`/`REJECTED`/`INCONCLUSIVE` (→ `PASS`/`KILL`) | `faults`, `calibration`, `measurement_context`, `strict_andersonian` |
| `K-POLARITY` | `gate_k_polarity` | `cutoff.py` | `PASS`/`WARN`/`KILL`/`UNMEASURED` | `faults`, `horizons`, `cutoffs` |
| `K-THROW` | `gate_k_throw` | `k_throw.py` | `PASSED`/`REJECTED`/`INCONCLUSIVE` | `faults` |
| `K-DL` | `gate_k_dl` | `k_dl.py` | `PASS`/`KILL`/`UNMEASURED` | `faults` |
| `G2` | `gate_g2_topology` | `topology.py` | `KILL`/`PASS` | `horizons`, `horizons_cross`, `relay_zone`, `throw_polarity_reversal`, `topology_cross` |
| `K-XCUT` | `gate_g2_topology` (alias, `alias_of: G2`) | `topology.py` | as G2 | as G2 |
| `K-RESTORE` | `gate_k_restore` | `restore.py` | `KILL`/`PASS`/`UNMEASURED` | `faults`, `restore`/`restoration`, `restore_residual`, `restore_closes`, `restore_self_intersection`, `restore_tolerance` |
| `K-VEL` | `gate_k_vel` | `velocity.py` | `KILL`/`PASS`/`UNMEASURED` | `velocity`, `interval_v_m_s`, `lithology_prior`, `td_monotonic`, `v_positive` |
| `K-GROWTH` | `gate_k_growth` | `growth.py` | `KILL`/`WARN`/`UNMEASURED` | `claims.{growth,syn_kinematic,expansion_index}`, `expansion_index`, `growth_claimed`, `syn_kinematic` |

Aggregation vocabulary (`__init__.py` L55–63): `KILL→REJECTED`, `PASS|PARTIAL|PARTIALLY_MEASURED→SURVIVES_CURRENT_TESTS`,
`UNMEASURED|COMPUTABLE→UNTESTED`, `INCONCLUSIVE→INCONCLUSIVE`.

K-REGIME universal gates (`tectonic_regime.py` L1090–1098): `K-REGIME-CEILING`, `K-REGIME-DIFFERENTIAL`,
`K-REGIME-DECOMPACT`, `K-REGIME-DISPLAY`, `K-REGIME-RESOLUTION`, `K-REGIME-XCUT`, `K-REGIME-COVERAGE`.

Regime falsifier gate ids present (`grep -oE 'K-[A-Z]+-[A-Z-]+'`, 22 distinct):
`K-COMP-{RAMPFLAT,SHORTEN,VERGENCE}`, `K-EXT-{ARCH,DIP,GROWTH}`, `K-GRAV-LINKAGE`,
`K-INV-{REACT,REVERSAL}`, `K-SALT-{BODY,DRIVER}`, `K-SS-{FLOWER,MARKER,RIEDEL,THROW}`,
plus the 7 universal ids.

**How `tectonic_regime.py` composes with the older gates — `OBSERVED`:**

* Before today it composed by **import only**: `__init__.py` L27–31 imported `REGIME_FALSIFIERS`,
  `falsify_regime`, `run_regime_falsification`, re-exported them at L50–52 — but the pre-existing
  `gates_spec` list did **not** include any of them.
* At snapshot the file has been extended: `_run_regime_falsification_block` (L139) wraps the engine,
  and `run_all_structure_gates` (L222) takes `include_regime_gates: bool = True` and calls the block
  at L354–355. The docstring (L233–240) states the merge is *additive*: the 9 core gates and the core
  `combined_verdict` / `hypothesis_status` are unchanged, and the merged view lives only in
  `combined_verdict_with_regime` / `hypothesis_status_with_regime`.
* `_regime_gate_receipts` (L168) flattens per-regime receipts into one gate-id map, namespacing
  collisions as `"<regime>:<gate_id>"` (L189–191) rather than overwriting.
* `_classify_receipts` (L195) explicitly keeps `UNMEASURED` out of `passes` (L196–197).
* `TRANSIENT, NOT A DEFECT`: an earlier read of this same file (`md5 525298ad…`, ~60 s before) showed
  the new docstring and helper present while the body of `run_all_structure_gates` did not yet call
  them. That was a mid-write state and was resolved by the next write.

---

## (b) DEFECTS

### D1 — The VLM output contract accepts spatial metrics read from pixels
**Files:** `src/geox_core/engines/vision/perceptual_inventory.py`, `minimax_vlm_adapter.py`, `mimo_vlm_adapter.py`
**Severity:** high — governance hazard if ever wired to a regime/prospect conclusion

`OBSERVED` — the VLM-facing schema carries the exact quantities a structural lane must measure:

```python
# perceptual_inventory.py:168-178
class FaultObservation(BaseModel):
    fault_id: str = Field(..., description="Stable identifier, e.g. 'F_main_boundary'")
    type: FaultType = FaultType.UNKNOWN
    lateral_extent_inlines: tuple[float, float]
    twt_range_ms: tuple[float, float]
    strike_dip_deg: float | None = Field(None, ge=0.0, le=90.0, description="Apparent dip")
    throw_ms: float | None = Field(None, description="Apparent vertical throw in ms TWT")
    confidence: float = Field(..., ge=0.0, le=0.90)
    notes: str | None = None
```

`OBSERVED` — the adapters **instruct the model to emit them** and then pass them straight through:

```python
# minimax_vlm_adapter.py:139-140   (identical at mimo_vlm_adapter.py:121-122)
      "strike_dip_deg": null_or_0_to_90,
      "throw_ms": null_or_number,
```
```python
# minimax_vlm_adapter.py:375-376   (identical at mimo_vlm_adapter.py:428-429)
                        strike_dip_deg=f.get("strike_dip_deg"),
                        throw_ms=f.get("throw_ms"),
```

`OBSERVED` — the shipped demo fixture shows the model path emitting precisely these numbers:
```python
# run_vision_v1_demo.py:48
{"id": "F1", "type": "normal", ..., "strike_dip_deg": 75, "throw_ms": 80, "confidence": 0.74}
```

`INFERRED` — a VLM has no `dz`/`dx`, no sample interval, no vertical-exaggeration factor. It cannot
measure `throw_ms`; it can only emit a fluent number. `throw_ms` is a direct input to `K-THROW`
(`k_throw.py`, key `faults`) and `strike_dip_deg` is a direct input to `K-DIP` (`k_dip.py`) and
`K-EXT-DIP` (`tectonic_regime.py` L488, `_path(f, "dip_deg")`). Any path where a VLM-derived
`throw_ms`/`strike_dip_deg` reaches the gate matrix, or a regime/prospect conclusion, is the
hallucination-in-numbers failure the new lane exists to prevent.

`OBSERVED` — mitigation that exists today is *only* a model-output cap, not a measurement guard:
```python
# tools/vision.py:233
                overall_confidence=min(overall_confidence, 0.90),
```
```python
# perceptual_inventory.py:289-291
        if self.overall_confidence > 0.90:
            raise ValueError(f"F7 HUMILITY violation: overall_confidence {self.overall_confidence} > 0.90")
```
A 0.90 cap on a hallucinated `throw_ms` does not make the number less wrong; it bounds the
model's self-reported certainty, not the physical validity of a spatial metric.

### D2 — The VLM lane is mounted at the MCP transport but blocked at the governance layer
**Files:** `src/geox_mcp/server.py`, `src/geox_mcp/geox_middleware.py`, `src/geox_mcp/tools_manifest.yaml`

`OBSERVED` — mounted in the composed surface:
```python
# server.py:650, 665
    vision = create_vision_server()
    ...
    mcp.mount(vision, namespace=None)
```
`OBSERVED` — but none of the four names is declared anywhere in the registry:
```
geox_vision_perceptual_inventory: public=False internal=False compat=False
geox_vision_minimax_inference:    public=False internal=False compat=False
geox_vision_calibrate:            public=False internal=False compat=False
geox_vision_audit:                public=False internal=False compat=False
```
(measured by importing `geox_mcp.registry` and testing membership in
`CANONICAL_PUBLIC_TOOLS` / `INTERNAL_TOOLS` / `CANONICAL_COMPAT_TOOLS`).
`grep -n "geox_vision" src/geox_mcp/tools_manifest.yaml` → **no matches**;
`geox_mcp.surface_manifest.manifest_tool_map()` has 85 entries, none of them `geox_vision_*`.
`server.py:689–690` only cross-checks `CANONICAL_PUBLIC_TOOLS` against `INTERNAL_TOOLS` and
`CANONICAL_COMPAT_TOOLS`, so a mounted-but-undeclared sub-server raises nothing at boot.

`OBSERVED` — RT1 then rejects the call:
```python
# geox_middleware.py:704-713
        if tool_name not in self._EXECUTABLE_SURFACE:
            if not (self._arifos_route_query_enabled and tool_name == "arifos_route_query"):
                logger.warning(f"RT1_BLOCK: tool '{tool_name}' is not on canonical public surface")
                raise ToolError(
                    f"RT1_GUARD: Tool '{tool_name}' is not on the canonical or compat surface. "
```
`_EXECUTABLE_SURFACE = public ∪ internal ∪ compat` (`geox_middleware.py:290-292`), constructed from
the registry sets in `server.py:412-418`.

`INFERRED` — this is a double-edged condition, and the second edge is the dangerous one:
the VLM lane is currently **unreachable via `tools/call`**, so the D1 numbers cannot reach a user
today; but the *obvious* way to "make the vision lane work" is to add four `geox_vision_*` entries
to `tools_manifest.yaml`, which would simultaneously make D1 live with no physical guard. Any change
that surfaces this lane must be paired with a measurement-provenance guard, not just a registry entry.

### D3 — `geox_vision_mimo_inference` is defined but never registered (dead function)
**File:** `src/geox_mcp/tools/vision.py:420`, `src/geox_mcp/servers/vision.py:30-35`

`OBSERVED` — the function exists and is fully implemented (L420–540) with its own adapter
`MiMoVLMAdapter`, its own error envelope, and the same `throw_ms`/`strike_dip_deg` passthrough path.

`OBSERVED` — the server's registration list contains four names, not five:
```python
# servers/vision.py:30-35
_VISION_TOOLS: list[tuple[str, Any]] = [
    ("geox_vision_perceptual_inventory", geox_vision_perceptual_inventory),
    ("geox_vision_minimax_inference", geox_vision_minimax_inference),
    ("geox_vision_calibrate", geox_vision_calibrate),
    ("geox_vision_audit", geox_vision_audit),
]
```
`_VISION_ANNOTATIONS` (L37–66) likewise has no `geox_vision_mimo_inference` key.
`INFERRED` — if it were added to `_VISION_TOOLS` without a corresponding annotation entry,
`register_tools_on_server` behaviour for a missing key is unverified here and must be checked before
that edit.

### D4 — `falsify.py` treats *absent* context keys as *positive* falsification evidence
**File:** `src/geox_mcp/tools/falsify.py`

`OBSERVED` — K007 scores an indicator from a `.get(..., False)` default, so a caller who simply
omits the key is credited with the indicator:
```python
# falsify.py:222-234
    if not context.get("has_rim_structure", False):
        score += 1
        indicators.append("no_rim")
    if not context.get("has_internal_reflectors", True):
        score += 1
        indicators.append("no_reflectors")
    if context.get("mound_shape") == "isolated":
        score += 1
        indicators.append("isolated_mound")
    slope = context.get("slope_angle_deg", 0) or 0
    if slope > 25:
        score += 1
        indicators.append(f"steep_flanks_{slope}deg")
```
```python
# falsify.py:236-243
    if score >= 3:
        ...  "verdict": "KILL", ...
```
`OBSERVED` — K005 has the same shape on the same key:
```python
# falsify.py:150-156
    if (
        context.get("surface_morphology") == "chaotic"
        and not context.get("has_rim_structure", False)
        and not context.get("has_internal_reflectors", True)
    ):
```
`INFERRED` — `has_rim_structure` omitted → `not False` → `True` → one spurious point toward a KILL.
Two more points from defaults (`slope_angle_deg` omitted → `0`, so no; `mound_shape` omitted → no)
means K007 cannot reach 3 from absence alone, but it *can* reach 2 (REVIEW) and it biases every
KILL/REVIEW decision. Absence of evidence is being converted into evidence of absence — the exact
inversion `tectonic_regime.py` is written to prevent (see D7 and `_measured`, L96–104).

### D5 — `geox_falsify` is registered as an MCP tool but is not on any governed surface
**Files:** `src/geox_mcp/tools_wiring.py:6576`, `src/geox_mcp/registry.py`

`OBSERVED` — the tool is decorated:
```python
# tools_wiring.py:6576
    @mcp.tool(name="geox_falsify", annotations=_geox_annotations("geox_falsify"))
```
`OBSERVED` — and is absent from all three registry sets:
```
geox_falsify:            public=False internal=False compat=False
geox_regime_falsification: public=False internal=False compat=False
geox_structure_validate:   public=False internal=False compat=False
```
`OBSERVED` (same result) the 31-name public surface contains no falsifier at all:
`geox_basin, geox_calibration_register_witness, geox_claim, geox_contrast_metabolize, geox_deep_time,
geox_extract_display_proxy, geox_extract_native_trace, geox_geomechanics, geox_glof_cascade_* (9),
geox_list_registered_sources, geox_map, geox_model, geox_paleobiodb_query, geox_petrophysics,
geox_prospect, geox_register_native_source, geox_seismic_compute, geox_seismic_ingest,
geox_seismic_interpret, geox_source, geox_spatial, geox_temporal, geox_well, geox_well_ingest, geox_well_qc`.

`INFERRED` — with D2's RT1 gate in force, `geox_falsify` is unreachable via `tools/call` too. The
only public falsification-adjacent surface is `geox_seismic_interpret(mode="structure_validate")`
(currently public) and `geox_claim` mode `falsify` mentioned in the manifest description
(`tools_manifest.yaml:1454-1455`).

### D6 — Non-balance has two contradictory semantics in the same repo
**Files:** `src/geox_mcp/tools/structure_gates/restore.py` vs `src/geox_mcp/tools/structure_gates/tectonic_regime.py`

`OBSERVED` — the new regime engine states the doctrine explicitly:
```python
# tectonic_regime.py:22-25
3. **Non-balance is a diagnostic, not an error flag.** Failure to restore means
   a structure is missing from the section, not that the interpretation is
   wrong. Never instruct an interpreter the other way — it produces picks bent
   until they balance, at the cost of the correct interpretation.
```
`OBSERVED` — the older operational gate does the opposite for the same physical fact:
```python
# restore.py:112-118
    # Hard veto: self-intersection
    if self_intersect is True:
        findings.append({"verdict": "KILL", "reason": "Restore self-intersection"})

    # Hard veto: non-closure
    if closes is False:
        findings.append({"verdict": "KILL", "reason": "Restore does not close"})
```
`OBSERVED` — and `K-RESTORE` is in the executed matrix (`__init__.py:281`), so a non-closing restore
still produces a hard KILL inside `run_all_structure_gates`.
`INFERRED` — both statements can be true at once only if `closes`/`self_intersection` are *caller
declarations* rather than engine outputs; note `restore.py:100,104` first honour caller-supplied
`residual`/`closes`. But nothing in `restore.py` distinguishes "caller asserts non-closure" from
"an automated restorer failed to close". Two different physical meanings share one boolean, and one
of them is treated as a KILL. The new lane must not feed automated balance output into `restore.closes`.

### D7 — Framework numbering labels VLM humility inconsistently
**Files:** `src/geox_mcp/tools/vision.py:33`, `servers/vision.py:10`, `perceptual_inventory.py:25`

`OBSERVED` three different labels for the 0.90 cap:
```
tools/vision.py:33       F5 HUMILITY     confidence hard-cap 0.90 enforced in Pydantic schema
servers/vision.py:10     confidence is hard-capped at 0.90 (F7 HUMILITY)
perceptual_inventory.py:25   (F7 HUMILITY hard cap)
```
and the emitted audit keys use the F5 label (`tools/vision.py:273`, `:406`, `:534`:
`"f5_humility_confidence_capped"`) while the tool docstring for `geox_vision_audit`
(`tools/vision.py:673`) says `F5 HUMILITY  overall_confidence hard-cap 0.90` and the exception raised
in the model says `F7 HUMILITY violation` (`perceptual_inventory.py:291`).
`INFERRED` — cosmetic for the code, but it makes receipt-level floor-attribution ambiguous: two
different constitutional floors are claimed for one control. Any new lane's receipts should pin one
floor label.

### D8 — `structural_restoration` tool wrappers have a string default on dict parameters
**File:** `src/geox_mcp/tools/structural_restoration/wiring.py`

`OBSERVED` (five occurrences: L29, L54, L89, L122, L158; also list-typed params L196–197, L233–235, L336–337):
```python
# wiring.py:28-46
    async def _validate_restoration_inputs(
        scenario: dict[str, Any] = "",
        ...
        s = RestorationScenario(**scenario)
```
```python
# wiring.py:195-197
        control_points: list[dict[str, Any]] = "",
        grid_extent: dict[str, float] = "",
```
`INFERRED` — a call that omits `scenario` gets `""`, and `RestorationScenario(**"")` raises
`TypeError: argument of type 'str' is not a mapping`. Because the whole function is still
unreachable (D9) this is latent, but it will fire on the first live call and the failure mode is an
unhandled exception rather than a structured HOLD. `dict[str, Any] = ""` is also rejected by strict
type checkers.

### D9 (verified negative) — `register_structural_restoration_tools` is dead code
**File:** `src/geox_mcp/tools/structural_restoration/wiring.py`

`OBSERVED` — the header claims PLANNED status:
```python
# wiring.py:6-7
Status: PLANNED — wired but not yet connected to tools_wiring.py
To activate: import and call register_structural_restoration_tools(mcp) from tools_wiring.py
```
`OBSERVED` — repo-wide grep for `register_structural_restoration_tools` returns exactly two hits,
both inside that same file (L7 comment, L20 definition). No other module, script, or test imports or
calls it. `grep -n "restoration" src/geox_mcp/tools_wiring.py` → **no matches**.
`OBSERVED` — the registry agrees: `src/geox_mcp/registry/structural_restoration_registry.yaml` header
(L6) says `Status: PLANNED — not LIVE until compute engines are wired to MCP surface`, and the first
tool entry (L38) carries `status: PLANNED`.
**Claim verified, header is accurate.** 9 tool names are declared in the wiring file.

### D10 — Concurrency hazard on shared files
**Files:** `src/geox_mcp/tools/structure_gates/__init__.py`

`OBSERVED` — hash changed during the audit window (`525298ad…` → `aa3481c7…` between two reads
~60 s apart) while three other agents were active; `geox_core/vision_structural/orientation.py`
appeared at 04:22:41 local, after `types.py` at 04:17:22.
`INFERRED` — any agent editing `structure_gates/__init__.py` is in a write race with the
concurrent agents, and `run_all_structure_gates` is imported by at least five modules
(`structure_validate.py:13`, `domain/seismic_interpret/bundle.py:156`,
`seismic_corrections.py:189`, `structure_gates/witness.py:60`, `tests/test_seismic_interpret_contract.py:392`).
Per the authority-envelope doctrine's TOCTOU rule, check time state must equal execution time state
before mutating this file.

---

## (c) WIRING GAP — what must change for the new lane to be reachable

### C1 — The CV core the tool calls does not exist yet (blocking)
`OBSERVED` — the extract tool imports a module and requires two attributes:
```python
# structural_vision.py:416-433
    try:
        core = importlib.import_module("geox_core.vision_structural")
    except Exception as exc:  # ImportError, ModuleNotFoundError, broken __init__
        logger.warning("vision_structural core unavailable: %s", exc)
        return _core_unavailable(f"import geox_core.vision_structural failed: {exc}")
    declared = getattr(core, "declare_calibration_state", None)
    ...
        axes_raw = core.extract_all_axes(
```
`OBSERVED` — measured live:
```
$ ls src/geox_core/vision_structural/
CONTRACT.md  orientation.py  types.py        # no __init__.py

>>> import geox_core.vision_structural
import OK -> None
dir: []
```
`INFERRED` — `geox_core.vision_structural` resolves as a **namespace package** with an empty
namespace, so `getattr(core, "declare_calibration_state", None)` is `None` and the tool returns
`_core_unavailable(...)` — a structured HOLD, not a crash. **Required to close:**
`src/geox_core/vision_structural/__init__.py` exporting `declare_calibration_state` and
`extract_all_axes` (the two symbols the tool actually requires). The CV primitives themselves can be
assembled from surfaces 10–13 before writing new DSP.

### C2 — The new server is never mounted
`OBSERVED` — repo-wide grep for `create_structural_vision_server` returns only the definition
(`servers/structural_vision.py:108`) and the `__all__` entry (L131). `servers/__init__.py` imports
four servers and does not include it:
```python
# servers/__init__.py:5-14
from geox_mcp.servers.claims import create_claims_server
from geox_mcp.servers.paleoscan import create_paleoscan_server
from geox_mcp.servers.vision import create_vision_server
from geox_mcp.servers.witness import create_witness_server
__all__ = ["create_witness_server","create_paleoscan_server","create_claims_server","create_vision_server"]
```
**Required to close — exact edits:**
1. `src/geox_mcp/servers/__init__.py` — add `from geox_mcp.servers.structural_vision import create_structural_vision_server` and add it to `__all__`.
2. `src/geox_mcp/server.py` — inside `compose_geox_servers()` (L630–665), import it in the
   `from geox_mcp.servers import (...)` block (L641–646) and add
   `mcp.mount(create_structural_vision_server(), namespace=None)` next to `mcp.mount(vision, namespace=None)` (L665).
3. `src/geox_mcp/server.py` — add timeout entries for `geox_structural_vision_extract` /
   `geox_structural_regime_falsify` to `TOOL_TIMEOUTS` (L128+) so they do not fall to the default.

### C3 — Registry / manifest declaration (the actual gate)
`OBSERVED` — `CANONICAL_PUBLIC_TOOLS` is derived, not hand-written:
`registry.py:57` `SURFACE_TOOLS = [t for t in public_tool_names() if t not in GHOST_TOOLS]`;
`registry.py:67` `CANONICAL_PUBLIC_TOOLS = list(SURFACE_TOOLS)`; `surface_manifest.py:10`
`MANIFEST_PATH = Path(__file__).with_name("tools_manifest.yaml")`.
`OBSERVED` — `geox_mcp.surface_manifest.manifest_tool_map()` returns 85 entries; a
`grep -n "geox_structural" src/geox_mcp/tools_manifest.yaml` returns **no matches** yet.
**Required to close:** add two `- name:` entries to `src/geox_mcp/tools_manifest.yaml` (model the
shape on the `geox_seismic_interpret` entry, L91–114: `domain/axis/lane/face/visibility/description/
input_schema_source/annotations/ui/plugin/governance/family/tier` with
`governance.action_class: OBSERVE`, `mutation: false`). Until this is done, RT1
(`geox_middleware.py:705`) will reject both tool names exactly as it rejects `geox_vision_*` (D2).
Also required: `src/geox_mcp/organ_governance.py` risk tier (pattern: L107
`"geox_visual_understand": RiskTier.READONLY`) if the lane is to be routed by `check_governance`.

### C4 — Optional: a dispatch mode instead of (or in addition to) a new tool
`OBSERVED` — there is **no** structural-vision mode today, and the manifest docstring for
`geox_seismic_interpret` (L98–99) lists the live modes without one. The `vision` name is explicitly
reserved as a *refusal*:
```python
# seismic_interpret.py:61-64
    "vision": (
        "Vision modes (geox_visual_understand / geox_vision_*) are separate tools. "
        "geox_seismic_interpret does not run VLM. Call geox_visual_understand for OBS_IMAGE."
    ),
```
If a mode-based entry point is wanted instead, the full set of declaration points is:
1. `_LIVE_MODES` frozenset — `seismic_interpret.py:37-56` (currently 16 names).
2. `_MODE_TO_MODEL` — `seismic_interpret.py:303-316`.
3. `model_map` inside `_normalize_request` — `seismic_interpret.py:359-372`.
4. A Pydantic request class in `src/geox_mcp/domain/seismic_interpret/models.py`
   (pattern: `SectionImageMode` L136, `StructureValidateMode` L125, `HorizonContrastMode` L113;
   union at L202; schema re-export at `contracts/seismic_interpret_schema.py:27`).
5. A handler branch **before** the `MODE_HANDLER_MISSING` guard at `seismic_interpret.py:1218`,
   following the `measure_throw` pattern (L612–627).
6. `tools_manifest.yaml:97-100` description text.
7. `src/geox_mcp/server.py:142` `geox_seismic_interpret` timeout if the mode is heavy.
`INFERRED` — a separate tool (C2/C3) is the lower-risk route: it keeps the deterministic lane's
annotations (`idempotentHint: True`, `openWorldHint: False` — `servers/structural_vision.py:90-105`)
honest and avoids widening a public tool's mode surface.

### C5 — Not required (no double-registration needed)
`OBSERVED` — `register_structural_restoration_tools` (D9) is a *different* lane and must not be
bundled into this change: its 9 tools are restoration/geomechanics wrappers, they are PLANNED, and
they carry D8's parameter defect. Activating them at the same time would widen the blast radius of a
single commit.

---

## (d) DUPLICATION RISK

### R1 — Two falsifier engines, no router between them
`OBSERVED` — `falsify.py` runs the K001–K007 Kill Matrix (`KILL_MATRIX`, L258–266) and three
structure gates, imported inline:
```python
# falsify.py:440, 455, 470
        from geox_mcp.tools.structure_gates.k_dip import validate_k_dip
        from geox_mcp.tools.structure_gates.k_dl import validate_k_scale
        from geox_mcp.tools.structure_gates.k_throw import validate_k_taper
```
`OBSERVED` — `geox_falsify` never reaches the regime engine: `falsify_regime` and
`run_regime_falsification` appear nowhere in `falsify.py`. `claim_type` is a free-form string with a
generic default and no enum:
```python
# falsify.py:387
    claim_type: str = "general",
```
`INFERRED` — a caller passing a tectonic-regime claim to `geox_falsify` gets the carbonate/reef-oriented
Kill Matrix (`K004` keys on `claim_type` containing "carbonate"/"reef"/"buildup", L124–132) and never
the 22 K-REGIME/K-EXT/K-COMP/K-SS/K-INV/K-SALT/K-GRAV falsifiers. Two competing falsification
semantics exist with no reconciliation: `K003` calls sub-tuning thickness a `REVIEW` (L111) while
`K-REGIME-RESOLUTION` handles resolution inside a receipted gate; `K-GROWTH` KILLs on `EI <= 1.0`
(`growth.py:68-72`) while `K-EXT-GROWTH` (`tectonic_regime.py:528+`) deliberately returns
`UNMEASURED` when EI is absent rather than killing.

**Reconciliation point (`INFERRED`):** one entry router keyed on `claim_type`, dispatching
regime claims to `run_regime_falsification` and leaving the K001–K007 matrix for the carbonate/reef
claims it was written for. Do **not** port K001–K007 into `tectonic_regime.py`; the regime engine's
`UNMEASURED`-discipline is strictly stronger.

### R2 — Expansion index is gated twice with different thresholds
`OBSERVED` — `growth.py:68`, threshold `ei_min = 1.0`, `KILL` when `ei_f <= 1.0`.
`OBSERVED` — `tectonic_regime.py:477`, EI fetched from three key paths and, equally, `KILL` only on a
*measured* contradiction; absent → `UNMEASURED`:
```python
# tectonic_regime.py:528
    ei, ei_path = _first_measured(fw, ("growth.expansion_index", "expansion_index", "claims.expansion_index"))
```
```python
# tectonic_regime.py:483-489
                "No expansion index measured. ABSENCE OF A GROWTH WEDGE DOES NOT KILL EXTENSION — "
                ...
            thresholds={"ei_min": 1.0}, missing_inputs=["growth.expansion_index"],
```
`INFERRED` — same threshold, different fail semantics, and both now execute in the same
`run_all_structure_gates` call (core matrix L283, merged regime block L354). If the two diverge on
key resolution (core reads `claims.expansion_index` then `framework.expansion_index`; regime reads
`growth.expansion_index` first) a bundle can produce `K-GROWTH = KILL` and `K-EXT-GROWTH = UNMEASURED`
in one response. They must resolve EI from one helper, or the divergence must be declared.

### R3 — Two independent region/attribute stacks produce overlapping intermediate rasters
`OBSERVED` — `contrast_views.py` and `seismic_classical.py` each implement their own structure-tensor
dip and Sobel edge (see §e). `OBSERVED` — a third implementation appears in the new lane's
`geox_core/vision_structural/orientation.py` (28.5 KB, written mid-audit).
`INFERRED` — three structure-tensor call sites. They should share one primitive
(`seismic_classical.structure_tensor`, surface 10) rather than diverge silently; note the new lane
adds circular statistics and DTW, which the older two do not have, so *some* new code is legitimate —
but the tensor/edge core is duplicated and should be imported, not re-derived.

### R4 — VLM lane must never be merged into the structural lane (already declared, keep it)
`OBSERVED` — the new lane states the boundary as a hard prohibition:
```python
# servers/structural_vision.py:26-31
  * DO NOT add the tools below to `servers/vision.py`.
  * DO NOT re-export `servers/vision.py`'s tools here.
  * DO NOT share an annotation table, a registration list, an engine or a
    code path between the two servers.
  * DO NOT let a perception-lane result be used as an input to a
    structural-metric claim, or vice versa.
```
`OBSERVED` — and the disjointness holds at snapshot: `_VISION_TOOLS` (4 names) ∩
`_STRUCTURAL_VISION_TOOLS` (2 names) = ∅.
`INFERRED` — this constraint is load-bearing precisely because of D1: the VLM schema's
`throw_ms` / `strike_dip_deg` fields give it a *plausible* structural-metric output shape, so the
temptation to "just reuse the vision inventory as the extract bundle" is real and must stay blocked.

### R5 — `mode="vision"` string collision is already handled
`OBSERVED` — the dispatch layer explicitly refuses a `vision` mode rather than silently remapping it
(`seismic_interpret.py:59-69`, quoted in C4). `INFERRED` — a new structural-vision mode must choose a
distinct name and must NOT be added to `_NOT_YET_MODES` in a way that repurposes the existing refusal.

---

## (e) REUSE — what already exists and must NOT be rebuilt

| Asset | Location | Reuse for |
|---|---|---|
| Structure tensor + dip/azimuth/coherence | `seismic_classical.py:38-60` (`structure_tensor`); exported `__all__` L329–338 | The canonical 2-D orientation primitive. `Ix/Iz` Sobel → `Ixx/Ixz/Izz` Gaussian-smoothed → eigen decomposition → `dip_rad` (`np.arctan2(Ixz, Izz)`, L60). |
| Semblance coherence / discontinuity | `seismic_classical.py` (`semblance_coherence`) | Fault/discontinuity response map; already paired with `ridge_extraction` and `candidate_faults` output (L300–307). |
| Ridge / skeleton extraction | `seismic_classical.py` (`ridge_extraction`) | Candidate horizon skeletons from a coherence map. |
| DP horizon tracker | `seismic_classical.py` (`dp_horizon_tracker`) | 1-D dynamic-programming tracking; do not write a second tracker. |
| RGT proxy field | `seismic_classical.py` (`rgt_estimation`, `horizons_from_rgt`) | Relative geological time field for isopach/superposition reasoning. |
| Sobel edge map | `contrast_views.py:152-163` (`_edge_map`) | Raster edge/discontinuity attribute. |
| Local dip raster | `contrast_views.py:192-202` (`_local_dip`) | Structure-tensor dip as a 2-D image; explicitly documented as "Attribute 6". |
| Phase symmetry / frequency content | `contrast_views.py:219`, `:236` | Waveform-character proxies for termination / onlap reasoning. |
| 9-attribute envelope + AC_Risk firewall | `contrast_views.py` (Attribute 9, `_ac_risk_heatmap` L276) | Existing governance metric for vision outputs. `geox_contrast_views` (L394) is written but **not** in the manifest — same reachability class as D2. |
| Image → gate-ready fault geometry | `seismic_zen_f1.py:348` `measure_throw_from_horizons` → `dmax_m` / `length_m` / `throw_profile_m` (L467–468); `compute_attributes_2d` L180; `track_horizons_2d` L284 | **The closest existing precedent for the whole new lane.** Already wired and reachable via `mode=measure_throw` (`seismic_interpret.py:612-627`), downstream into the gate matrix. Review this before designing a parallel path. |
| Expansion index from isochores | `calibration_derive.py:347` `_expansion_index`, written at L562/L567; header L15 | K-GROWTH / K-EXT-GROWTH input derivation. Do not re-derive EI. |
| Cutoff pair derivation + polarity sense | `cutoff.py:71` `derive_cutoff_pairs`, `:173` `polarity_from_cutoffs`, `:190` `gate_k_polarity` | Throw/polarity from horizon–fault crossings. Already invoked inside the matrix (`__init__.py:269-273`). |
| Fault field alias normalization | `normalize.py:27-63` (`_D_KEYS`, `_L_KEYS`, `_PROFILE_KEYS`), `:73` `normalize_fault`, `:117` `normalize_framework` | Accept metric-suffixed keys (`dmax_m`, `throw_profile_m`) so gates can KILL instead of going blind `UNMEASURED` (header L3–6). Any new extractor should emit canonical keys and let this normalize. |
| Geometry adaptation (sticks/picks → points) | `geometry_adapt.py:57` `sticks_or_picks_to_points`, `:88` `adapt_fault`, `:145` `adapt_horizon`, `:171` `adapt_framework_geometry` | Chat-shaped geometry → gate-shaped geometry. |
| Gate receipt constructor | `geox_mcp/domain/seismic_physics/receipts.py` (`make_gate_receipt`, `receipt_hash`) — used by every gate and wrapped by `tectonic_regime._receipt` (L60–75) | Use this for any new gate receipt; `_receipt` adds `epistemic_tier` / `scope` / `coverage` into the hash. |
| Regime falsifier engine (single authority) | `tectonic_regime.py:971` `REGIME_FALSIFIERS`, `:987` `falsify_regime`, `:1048` `run_regime_falsification` | The `bundle_to_framework` adapter (`structural_vision.py:559`) maps the extract bundle onto this engine rather than reimplementing it. |
| Measurement envelope (new, frozen) | `geox_core/vision_structural/types.py` (`Measurement`, `ExtractionStatus`, `FORBIDDEN_PROBABILITY_KEYS` L28–35) and `CONTRACT.md` | Value + coverage + method + uncertainty, no probability. Already the contract the extract tool sanitizes against (`structural_vision.py:148`, `:166`). |
| Deterministic orientation core (new, mid-write) | `geox_core/vision_structural/orientation.py` (28.5 KB) | Likely holds the structural-tensor/circular-statistics implementation. **Check it before writing orientation code; it was written after this audit line began.** |
| `Measurement` serialization helper | `structural_vision.py:200` `_to_plain`, `:227` `_plain_axes`, `:242` `_measurement_value`, `:267` `_axis_coverage`, `:287` `aggregate_coverage`, `:305` `unified_status` | Extract-bundle assembly and the mandatory aggregate coverage. |
| Forbidden-key sanitizer | `structural_vision.py:136` `_is_forbidden`, `:148` `strip_forbidden_keys`, `:166` `assert_no_forbidden_keys`, `:186` `_sanitize` | The mechanism that keeps `confidence`/`score`/`probability` out of the deterministic lane's return path (key list: `geox_core/vision_structural/types.py:28-35`). |
| Test harness pattern | `vision_test_harness.py` (`run_synthetic_forward_inverse`, `PerfectVisionMock`, `NoisyVisionMock`) | Synthetic forward/inverse fixtures already exist for the perception lane. The deterministic lane should reuse the *harness pattern* (synthetic section + ground truth), never the VLM mocks. |
| Existing gate tests | `tests/test_seismic_interpret_contract.py:392-442` (calls `run_all_structure_gates`), `tests/test_tectonic_regime_falsification.py` (27 tests) | Regression anchors. `run_all_structure_gates` determinism is already asserted (two calls → same result, L441–442). |

### Verified ABSENT (do not assume these exist)

`OBSERVED` — grep over `src/ docs/ tests/ scripts/` for `isopach|expansion_index|dtw|dynamic_time_warp|hough`:

* **Hough transform** — no implementation anywhere. Absent.
* **DTW / dynamic time warp** — no implementation anywhere. Absent (the new lane's `orientation.py` is the first, per its 04:22 mtime).
* **`skimage` / scikit-image** — exactly one hit: `classical_section_propose.py:160` `from skimage.filters import sato`. No `skimage` structure tensor, no Hough.
* **`cv2` / OpenCV** — zero hits.
* **isopach as a computed primitive** — absent. Only (i) the boolean key `intervals[].isopach_reversal` consumed at `tectonic_regime.py:755-782`, and (ii) the prose caveat `mass_balance_tool.py:113` "Preserved volume depends on mapping and isopach quality". Thickness differencing is *named* (`K-REGIME-DIFFERENTIAL`) but the raster operation is not implemented as a shared primitive.
* **Expansion index** — implemented only as `calibration_derive._expansion_index` (L347) and the two-consuming gate duplication in R2.

---

## Post-snapshot deltas (observed after the snapshot above)

`OBSERVED` — between the snapshot and finishing this report, the concurrent agents added:

```
?? tests/test_structural_vision_mcp.py     (new — structural-vision lane tests)
?? tests/test_regime_gate_matrix.py        (new — K-REGIME merged-matrix tests)
?? src/geox_mcp/prompts/structural_invariants.py
```

`INFERRED` — the structural-vision lane is being built at speed by the concurrent agents and the
`tests/test_structural_vision_mcp.py` file suggests MCP-surface tests now exist for it. Before acting
on C1/C2/C3, re-run the C1 probe:
`python -c "import sys;sys.path.insert(0,'src');import geox_core.vision_structural as m;print(dir(m))"`
— if `declare_calibration_state` and `extract_all_axes` are now present, C1 is closed. Re-check
`grep -n "geox_structural" src/geox_mcp/tools_manifest.yaml` for C3, and
`grep -rn "create_structural_vision_server" src/` for C2. D1/D2/D4/D6/D9 are unaffected by these
deltas because they concern files that were not in this delta set.

---

## Summary of the critical path

1. **D1 + D2 together are the governance story.** The VLM schema asks a language model for
   `throw_ms` and `strike_dip_deg` and pipes them straight into `FaultObservation`; that lane is
   currently blocked by RT1 only because its four names were never added to
   `tools_manifest.yaml`. The fix that "makes vision work" is the fix that makes the hallucination live.
2. **The new lane is real and in flight, not hypothetical.** `structural_vision.py`,
   `servers/structural_vision.py`, `geox_core/vision_structural/` and the `structure_gates/__init__.py`
   regime merge all exist at snapshot. The audit's job is to stop the lane rediscovering
   `seismic_zen_f1.measure_throw_from_horizons`, `seismic_classical.structure_tensor`,
   `contrast_views._local_dip` and `calibration_derive._expansion_index` (§e).
3. **The lane is not yet reachable.** Three edits remain (C2), plus the manifest declaration (C3),
   plus the missing CV-core `__init__.py` exporting `declare_calibration_state` and `extract_all_axes` (C1).
4. **Two falsifier semantics coexist** (R1) and must be routed, not merged; `falsify.py`'s
   default-`False` indicator scoring (D4) should not be inherited by the new lane.
5. **`structural_restoration` is genuinely PLANNED** (D9) — verified, header accurate — and should not
   be activated in the same change as the structural-vision lane.

---

# VERIFIED DELTAS — post-write re-probe (parent session, 2026-09-18)

The audit above was produced **concurrently** with three writing agents and pins itself to
`git HEAD 886de317` + 12 md5s. This section re-probes its load-bearing findings **after all writers
finished**, so a false defect cannot survive into the record. Method: independent probes by the parent
session, encoded as executable tests in `tests/test_structural_vision_integration_verified.py`
(15 tests, all passing).

## C1 — STALE. Not a defect. The blocking gap it describes no longer exists.

| Claim in audit | Re-probe result |
|---|---|
| `geox_core.vision_structural` imports as an **empty namespace package**, `dir() == []` | **FALSE at re-probe.** `__init__.py` present, 2,217 bytes, mtime **04:27** — i.e. written *after* the auditor's probe window. `dir()` returns **35** names including `Measurement`, `apply_ve_correction`, `compute_dip_field`. |
| The lane is unreachable because C1 blocks it | **Partially stale.** The core imports cleanly; all four axis modules (`structure_tensor`, `isopach`, `orientation`, `terminations`) import with all their public functions. The lane remains unreachable — but for the manifest/mount reasons (C2/C3), **not** for C1. |

**Would the audit have been different if C1 were dropped?** Yes, materially: C1 is listed in the
audit's own critical-path summary as one of the three blocking edits. It is zero edits. This is a
race-window artifact, not an analyst error — the auditor flagged the moving-target condition itself.

## D1 — CONFIRMED, independently. Line numbers verified.

```
src/geox_core/engines/vision/minimax_vlm_adapter.py:139-140   "strike_dip_deg": null_or_0_to_90,
                                                              "throw_ms": null_or_number,
src/geox_core/engines/vision/minimax_vlm_adapter.py:375-376   strike_dip_deg=f.get("strike_dip_deg"),
                                                              throw_ms=f.get("throw_ms"),
src/geox_core/engines/vision/mimo_vlm_adapter.py:121-122      (same schema)
src/geox_core/engines/vision/mimo_vlm_adapter.py:428-429      (same pipe-back)
```

The prompt schema solicits a dip magnitude in degrees and a throw in milliseconds **from a language
model**, and pipes both straight into `FaultObservation` — a direct input to K-DIP / K-THROW /
K-EXT-DIP (`tools/structure_gates/k_throw.py:94` resolves `"throw_ms"` among its candidate keys).
The only guard is the F7 cap `min(overall_confidence, 0.90)`, which bounds self-reported certainty
and therefore bounds **nothing** about whether the number is physical. **Confirmed as stated.**

## D2 — CONFIRMED. RT1 is the only thing keeping D1 inert.

- `tools_manifest.yaml`: **zero** `geox_vision` hits.
- `server.py:644-650, 665`: `create_vision_server()` imported, instantiated, `mcp.mount(..., namespace=None)`.
- `geox_middleware.py:704-713`: `RT1_BLOCK` raises `ToolError` for any name absent from `_EXECUTABLE_SURFACE`.
- `registry.py:57`: `SURFACE_TOOLS` derives from `surface_manifest.public_tool_names()` → the YAML.

So the mounted-but-undeclared state is exactly what the audit describes, and the warning holds:
**manifest-adding `geox_vision_*` to "make vision work" would arm D1.** The new deterministic lane
being armed on the same commit is a net safety gain; the two must not travel together.
Recorded as a hard guard in `src/geox_mcp/servers/structural_vision_wiring.py`.

## D4 — CONFIRMED, with the exact mechanism.

`tools/falsify.py:35-65`, `_k001_climate_archetype`:

```python
climate = context.get("climate_archetype", "").lower()   # absent -> ""
depositional = context.get("depositional_environment", "").lower()
...
if issues:
    return {"filter": "K001", "verdict": "REVIEW", "issues": issues}
return {"filter": "K001", "verdict": "PASS", "issues": []}   # <- fires on empty input
```

`_k001_climate_archetype({})` returns **`PASS`** with empty `issues`. Missing inputs fall through
both branches and are scored as a pass. This is the **same defect class** as the falsifier-direction
rule the regression lane enforces: *deficit read as positive evidence*. Verified by executable test.

**Not fixed here — deliberately.** Changing `PASS`→`UNMEASURED` across K001–K007 alters the verdict
semantics of shared tooling consumed by other lanes, which is a different objective from this lane and
outside its authority envelope. Reported, not silently repaired.

## NEW — `import httpx2` is a hard repo-wide breakage (second independent witness)

```
src/geox_mcp/tools/macrostrat_client.py:38      import httpx2  # FastMCP 4 migration
src/geox_mcp/tools/wealth_bridge_tool.py:26     import httpx2
src/geox_core/services/spglobal_client.py:32    import httpx2
src/geox_core/services/npd_client.py:36         import httpx2
```

The package does not exist in this venv (`ModuleNotFoundError`). Consequence: `import geox_mcp.servers`
and `import geox_core.services` both fail transitively — **the entire domain-server mount path is
unreachable.** This blocks arming independently of the manifest change, and it is why the audit's own
`import geox_mcp.servers` probe was replaced by file-path loading.

The intent is defensive (`except (httpx.ConnectError, httpx2.ConnectError)`), i.e. tolerate both
generations. The safe correction is a guarded optional import with the `except` tuples rebuilt
conditionally — but it touches four modules across two packages while other agents may be active, so
it is reported rather than silently patched. **Two of the four files are outside this lane.**

## Reuse warning (R) — CONFIRMED, all four primitives exist

| Primitive | Path | Verified |
|---|---|---|
| `structure_tensor` | `tools/seismic_classical.py` | `def structure_tensor` present |
| `_local_dip` | `tools/contrast_views.py` | `def _local_dip` present |
| `_expansion_index` | `tools/structure_gates/calibration_derive.py` | `def _expansion_index` present |
| `measure_throw_from_horizons` | `tools/seismic_zen_f1.py` | present, reachable via `mode=measure_throw` |

Rebuilding any of these would be duplication of working code. The new lane adds deterministic
primitives that genuinely did not exist (structure-tensor dip **field** with VE correction and named
geometry rules, numpy DTW, circular-statistics azimuth population, termination classification) — the
delta is real, but the overlap must be reconciled before arming, not after.

## Integration state at close

| Item | State |
|---|---|
| Core engine (4 axes + calibration) | BUILT — 113 tests |
| MCP tools, server, invariant prompt | BUILT — 76 tests |
| Regime falsification engine | BUILT — 35 tests |
| Verification of this map | 15 tests |
| **Total** | **239 passing** |
| Mounted / reachable | **NO** — unarmed by design |
| Arming plan | `src/geox_mcp/servers/structural_vision_wiring.py::describe_arming_plan()` |
| Blockers to arming | (1) manifest entries, (2) `server.py` mount, (3) `httpx2` import breakage |
| Hazard if armed carelessly | D1 goes live if `geox_vision_*` is manifest-added in the same change |

DITEMPA BUKAN DIBERI — verified after the writers stopped, not during the race.
