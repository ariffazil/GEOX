# GEOX-LEM v0.1 — Forge Receipt
**DITEMPA BUKAN DIBERI — Forged, Not Given.**

## Timestamp
2026-06-21 21:00 UTC

## Engineer
FORGE (000Ω) — OpenCode 333-AGI

## What Was Forged

### 1. Fusion Architecture Schema
**File:** `src/geox_core/lem/schemas/fusion_architecture.json`
- Canonical draft: 6-organ architecture (3 FMs + 3 engines)
- Shared Earth coordinate frame (x, y, z, t, basin, play, horizon)
- MCP integration plan (6 new tools needed)
- Scaling budget: CPU-trainable well FM, GPU needed for seismic/EO

### 2. Physics Organ (External)
**File:** `src/geox_core/lem/organ_physics.py`
- TEACH: synthetic well logs + seismic traces from forward physics
- GUARD: constraint check on vsh/phi/sw against CANON-9 bounds + Archie
- SCORE: epistemic uncertainty + feasibility + causality violation
- Zero dependency on FM weights — callable as MCP tool

### 3. Well/Petrophysics FM Engine
**Dir:** `src/geox_core/engines/lem/`
**Files:**
- `config.py` — All configuration dataclasses for tokenizer, pretrain, physics, data
- `tokenizer.py` — VQ-VAE for well log discretization (512 geological tokens, 6 curves)
- `dataset.py` — Data pipeline from 715 real LAS files (1.4 GB training data)
- `model.py` — Cross-modal fusion transformer (6 layers, 8 heads, 256 embed dim)
- `physics_head.py` — DEPRECATED — physics refactored to external organ
- `pretrain.py` — 3-phase training: tokenizer → tokenize → pretrain transformer
- `__init__.py` — Clean public API

### 4. Verified Operational
- Physics organ TEACH/GUARD/SCORE all working
- Well log data pipeline: 715 LAS files → patches → training batches
- VQ-VAE and LEMTransformer instantiable and runnable
- Fusion architecture schema validated

## What's NOT Forged (Needs 888_HOLD or GPU)
- Seismic FM pretraining (requires GPU burst compute)
- EO/Basin FM (requires terratorch + GPU + Prithvi weights)
- GEOX Router cross-attention fusion (needs all 3 FMs operational first)
- 6 new MCP tools (need to go through AGENTS.md registry)

## Evidence Paths
- `/root/geox/src/geox_core/lem/schemas/fusion_architecture.json`
- `/root/geox/src/geox_core/lem/organ_physics.py`
- `/root/geox/src/geox_core/engines/lem/` (5 files + __init__)

## Next Action
Arif: review the architecture. If approved → 888_SEAL → begin well_petro_fm training.
