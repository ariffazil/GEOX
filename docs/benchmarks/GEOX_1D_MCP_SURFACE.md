# GEOX 1D MCP Surface

Orthogonal Base calibration tools — MCP-native, JSON-only, DRAFT_ONLY receipts.

| Tool | Phase | Role |
|------|-------|------|
| `geox_well_time_depth_calibrate` | 2 | LAS + checkshot → TDFitResult + PhysicsGuard |
| `geox_well_seismic_mistie_rms` | 3 | Synthetic vs seismic → SEAL/HOLD/VOID @ 25 ms |
| `geox_wavelet_extract_least_squares` | 4 | Wiener wavelet + phase_class |

## Boundary rules

- `np.ndarray` never crosses MCP → always `list[float]`
- `vault_receipt.vault999_status = DRAFT_ONLY` (arifOS seals, not GEOX)
- Resource URIs: `geox://well/{well_id}/{tdfit|mistie|wavelet}/{id}`
- Receipts on disk: `data/egs/receipts/`

## Models

`geox_core/schemas/geox_1d_mcp.py` — TDFitResultMCP, MistieResultMCP, WaveletResultMCP

## Headless GEOX-001

```bash
PYTHONPATH=src pytest tests/benchmarks/test_geox_1d_mcp_surface.py -q
# TB1: benchmark-001/data/GEOX-001-TB1.las + checkshot.csv
```

UI (`_meta.ui.resourceUri`) attaches only after EGS host is stable — physics first.

*DITEMPA BUKAN DIBERI*
