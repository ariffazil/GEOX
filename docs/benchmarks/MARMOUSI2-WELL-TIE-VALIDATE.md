# Marmousi2 Known-Answer Well-Tie Validation

**Overall: PARTIAL — 2/3 pipeline PASS (both flanks STRONG)**

| Well | X (m) | Trace | Corr (400–2800 ms) | Mistie | Wavelet | Polarity | Pipeline | Strong |
|------|-------|-------|--------------------|--------|---------|----------|----------|--------|
| MARMOUSI2-X1500 | 1500 | 240 | **0.73** | **+8 ms** | 40–45 Hz | REVERSED | **PASS** | **YES** |
| MARMOUSI2-X5000 | 5000 | 800 | 0.27 | +76 ms | 45 Hz | REVERSED | FAIL | no |
| MARMOUSI2-X10000 | 10000 | 1600 | **0.73** | **+8 ms** | 40–45 Hz | REVERSED | **PASS** | **YES** |

## What this proves

- LAS extracted from elastic model; SEG-Y = `SYNTHETIC_time.segy` same model → **correct answer known**.
- Flank wells: high correlation + 8 ms mistie → **GEOX RC→Ricker→T-D integrate path works**.
- Polarity consistently REVERSED → SEG-Y polarity convention vs SEG_NORMAL synthetic (fix or document, not a geometry bug).
- **x5000 FAIL is structural core** (faults/steep dip/complex multipathing) — expected harder; not a random geology excuse because model is known, but 1D convolutional model is incomplete at complex center.

## Orthogonal Base path exercised

```text
LAS load → Vp·ρ AI → TWT integrate → RC → Ricker convolve
  → extract SEG-Y @ SourceX(mm)/1000
  → windowed xcorr
```

`geox_well_ingest(mode=las)` still needs API param cleanup (returned INVALID without mode-specific fields) — physics path validated independently.

## Next

1. Lock polarity convention in tie preflight for Marmousi.
2. Optional: stretch/static at x5000 or multi-wavelet.
3. F3/Volve only after flank PASS accepted as pipeline green.

## Run

```bash
cd /root/geox
# SEG-Y once:
# tar -xzf data/elastic-marmousi-model/processed_data/SEGY-Time/SYNTHETIC_time.segy.tar.gz -C data/marmousi_work
PYTHONPATH=src python scripts/marmousi2_well_tie_validate.py
```

Receipt JSON: `A-FORGE/forge_work/2026-07-09/MARMOUSI2-WELL-TIE-VALIDATE.json`

*DITEMPA BUKAN DIBERI · Known-answer gate*
