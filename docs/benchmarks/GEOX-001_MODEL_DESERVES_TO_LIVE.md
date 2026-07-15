# GEOX-001: Model Deserves To Live

**Well-Seismic Truth Test** — first proof wedge.

Full doctrine: [`GENESIS/012_GEOX_001_WELL_SEISMIC_TRUTH.md`](../../GENESIS/012_GEOX_001_WELL_SEISMIC_TRUTH.md)

## Run

```bash
cd /root/geox
PYTHONPATH=src python -m geox_core.benchmarks.geox_001_well_seismic_truth --scenario mistie_hold
PYTHONPATH=src pytest tests/benchmarks/test_geox_001_well_seismic_truth.py -q
```

## MCP

```text
geox_benchmark_001(scenario="mistie_hold")
```

## Thesis

If the well does not tie, the model does not get to speak as truth.
