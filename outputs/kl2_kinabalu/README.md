# outputs/kl2_kinabalu — provenance

First-pass NN age scaffold for the KL2 well roster. **Not a well-correlation product.**

| File | Status |
|---|---|
| `kl2_kinabalu_penetration_v3.py`, `kl2_kinabalu_well_data_v3.xlsx`, `kl2_kinabalu_penetration_chart_v3.png` | Current. Rotan-1 seabed/TD are **public** (Oil & Gas Journal, 5 Feb 2007: TD 7,024 ft in 3,773 ft of water). Exact pick depths, TWT, pay/GWC depths and VSP parameters were **redacted 2026-10-15** (ARIF, AMANAH) and are held outside this repo. |
| `kl2_kinabalu_penetration_v2.py`, `kl2_kinabalu_well_data_v2.xlsx`, `kl2_kinabalu_penetration_chart_v2.png` | Superseded. Rotan-1 row (3200 m / 2810 ms / 750 m) is a known DATA-LINEAGE FAULT (fixture value, not the well). |
| `wells_summary.json`, `qc_samples.csv` | **DER_SYNTHETIC fixtures** (from `tests/fixtures/kinabalu_synth.py`). `"type": "measured"` describes the fixture's checkshot style, not real measurements. No value here is real well data. |
| `_audit_extract.py`, `_canonize_*.py` | Tooling. |

Do not add internal well data (WCR values, picks, TWT, contacts, LAS/SEG-Y) here. The local `.gitignore` blocks new files by default.
