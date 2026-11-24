# GEOX Ugly Corpus

A 60-second truth benchmark for GEOX. **100% synthetic, public-safe, deterministic.**
No real well data, no network, no downloaded fixtures.

```bash
pip install geox-ugly-corpus geox-mcp
geox-ugly
```

```
GEOX UGLY CORPUS v0.1.0 — 100% synthetic, seed 20261124
[PASS] L5-computed-not-measured: computed VSH/PHIE/TVDSS and unknown-origin aliases SONIC/PHI must not count as measured (measured=1, leaked=[])
[PASS] QC-missing-source-fails-closed: an unregistered/missing source must return ERROR+HOLD+NO_VALID_EVIDENCE with qc_passed=False
[PASS] G1-inverted-interval-refused: top>base must refuse, got status='INVALID'
...
14/14 contracts passed in 2.70s (budget 60s) → PASS
```

## What it measures

| Contract | Claim being tested |
|---|---|
| `L5-measured-baseline` | nine canonical measured curves all count as measured |
| `L5-computed-not-measured` | computed (`VSH`, `PHIE`, `TVDSS`) and unknown-origin aliases (`SONIC`, `PHI`) never satisfy measured completeness |
| `L5-token-outranks-name` | `RHOB_INTERP` is interpreted, not measured — the token rule outranks the name |
| `L5-unknown-stays-in-inventory` | an unknown mnemonic (`ZZZ9`) stays in inventory and stays out of measured |
| `L5-spliced-not-measured` | `GR_SPLICE` is spliced, not measured |
| `QC-missing-source-fails-closed` | a missing/unregistered source cannot pass QC (ERROR + HOLD + `NO_VALID_EVIDENCE`) |
| `G1-inverted-interval-refused` | depth top > base is refused as `INVALID` |
| `G1-negative-porosity-refused` | negative porosity cutoff is refused as `INVALID` |
| `G1-superluminal-velocity-refused` | 8000 m/s in sedimentary rock returns `ERROR/HOLD/REJECTED/NO_VALID_EVIDENCE` |
| `GUARD-uncomputed-is-not-pass` | an envelope from a tool that ran no physics guard must not emit `guard_passed: True` |
| `corpus-determinism` | two builds produce the same SHA-256 manifest |
| `corpus-synthetic-provenance` | every fixture header names the generator and the seed |
| `corpus-ugly-is-actually-ugly` | the ugly fixture really is ugly (duplicate depths, ≥50% nulls, impossible RHOB) |
| `budget-60s` | the whole run stays inside 60 seconds, imports included |

## What it does NOT claim

- It is **not** a certification. Passing means the named contracts hold on the
  tree you ran; it says nothing about contracts not listed here.
- Curve origin is **mnemonic screening**, never provenance. A curve named `RHOB`
  is assumed measured at **low confidence**; if a vendor computed it and kept the
  name, this benchmark cannot see that. Real provenance must come from source
  metadata, not names.
- It is **not** a dataset. There are no real wells, no type logs, no production
  data. The fixtures are waveforms with deliberate defects.

## Receipt

`geox-ugly --json receipt.json` writes a receipt containing the fixture SHA-256
manifest, the full contract table, host/Python, and the wall-clock budget. The
manifest digest is one hash over `name:sha256` pairs, so any run can be compared
to any other without trusting the report.

## Exit codes

`0` all contracts pass · `1` a contract failed · `2` GEOX is not importable.

DITEMPA BUKAN DIBERI.
