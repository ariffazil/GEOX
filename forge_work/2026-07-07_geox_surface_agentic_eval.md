# GEOX Surface Agentic Evaluation — 2026-07-07

## Measured Runtime Truth

- Live `tools/list` exposed tools: `86`
- Health endpoint still reports `canonical_tools=89`
- Local source unified public tools for new callers: `7 dispatchers`
- Dispatcher atomic capability count from mode branches: `81`
- Hidden backward-compat tools preserved in source: `131`

## Benchmark Coverage

- well ingest: legacy=`True` · unified=`True` · no-tools=`False`
- petrophysics: legacy=`True` · unified=`True` · no-tools=`False`
- basin screening: legacy=`True` · unified=`True` · no-tools=`False`
- RSI interpretation: legacy=`True` · unified=`True` · no-tools=`False`
- map preview: legacy=`True` · unified=`True` · no-tools=`False`
- EGS entity query: legacy=`True` · unified=`True` · no-tools=`False`
- wealth bridge: legacy=`True` · unified=`True` · no-tools=`False`

## Quantitative Scores

| Surface | Exposed Tools | Atomic Capabilities | Coverage | Top-Level Entropy (bits) | Meaning Density | QMI | AEL |
|---|---:|---:|---:|---:|---:|---:|---:|
| vanilla_no_tools | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| legacy_live_flat | 86 | 86 | 1.00 | 6.43 | 1.00 | 1.00 | 0.57 |
| unified_dispatch_7 | 7 | 81 | 1.00 | 2.81 | 11.57 | 11.57 | 0.91 |

## Derived Reading

- Surface compression from live legacy to unified dispatch: `12.29x` fewer top-level tools.
- Top-level routing entropy drops from `6.43` to `2.81` bits: `56.31`% reduction.
- Meaning density rises from `1.00` to `11.57` atomic capabilities per exposed tool.
- Vanilla no-tools has the lowest raw surface entropy, but zero grounded GEOX execution coverage, so its agentic level collapses in evidence-grade work.
- Legacy flat surface is capable but cognitively noisy: full coverage, poor routing efficiency, and no namespace compression.
- Unified dispatch keeps full benchmark coverage while moving complexity behind semantic verbs. That is the highest agentic level of the three because capability is preserved while decision entropy is sharply reduced.

## Quantum Meaningful Reading

- `QMI` here is a derived heuristic: `coverage x meaning_density`.
- `AEL` here is a derived heuristic: grounded access plus coverage, entropy efficiency, and meaning density.
- On both heuristics the order is stable: `unified_dispatch_7 > legacy_live_flat >> vanilla_no_tools`.

## Deploy Gate

- Do not deploy from health alone. Runtime truth is split right now: `health=89`, `tools/list=86`, source target=`7 dispatchers`.
- Restart is justified only if followed immediately by parity checks: `health`, `tools/list`, and one call through each dispatcher.
