# Contributing to GEOX

> **SOT:** 2026-07-25 | **DITEMPA BUKAN DIBERI**

GEOX is the earth intelligence organ of the arifOS Federation. It computes geological evidence — never adjudicates, never authorizes drilling.

## Before You Start

1. Read the [README](README.md) — understand the OBS/DER/INT/SPEC evidence layers
2. Understand Physics9 constraints
3. Run `curl :8081/health` — ensure GEOX is running

## Setup

```bash
git clone git@github.com:ariffazil/GEOX.git && cd GEOX
pip install -e ".[dev]"
python server.py             # starts on :8081
curl http://localhost:8081/health
```

## Making Changes

1. **Fork → Branch → Edit → Test → PR**
2. Run `PYTHONPATH=src pytest tests/ -q --tb=short` before pushing
3. Run `ruff check . && ruff format .` for linting
4. `src/geox_core/` is physics truth — no agent-facing logic there
5. `src/geox_mcp/` is the agent surface — all tools go here

## Boundaries

- GEOX computes evidence — never adjudicates (arifOS does that)
- GEOX interprets geology — never authorizes drilling
- All outputs carry epistemic labels: OBS / DER / INT / SPEC
- Confidence hard-capped at 0.90 (F7 HUMILITY)

## Federation

GEOX is one of 7 organs. See [ariffazil/ariffazil](https://github.com/ariffazil/ariffazil) for the federation map.

---

*Maintained under F13 SOVEREIGN by Muhammad Arif bin Fazil.*
