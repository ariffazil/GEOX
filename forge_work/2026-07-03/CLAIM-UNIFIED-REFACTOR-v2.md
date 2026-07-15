# CLAIM-UNIFIED-REFACTOR-v2 — Literature-to-Claims Extraction Support

**Date:** 2026-07-03
**Target:** `src/geox_mcp/tools/claim_unified.py` + `src/geox_mcp/tools/claims.py`
**Phase:** 2.5

## Changes Applied

### 1. `claim_unified.py` — Refactored dispatch + new fields
- **Removed** `kwargs = locals().copy()` fragile pattern — replaced with explicit per-mode dict construction
- **Grouped** parameters by mode (core, challenge, seal, evidence, literature) with section headers
- **Added** `EpistemicLabel = Literal["OBS", "DER", "INT", "SPEC"]` type
- **Added** `LitCategory` type with 13 literature taxonomy values
- **Added** 4 new optional parameters: `epistemic_label`, `forbidden_uses`, `source_citation`, `category`
- **Threaded** literature metadata into `geox_claim_create` via `extra_metadata` dict

### 2. `claims.py` — Backward-compatible `extra_metadata` passthrough
- **Added** `extra_metadata: dict[str, Any] | None = None` to `_build_claim_envelope()`
- **Added** `extra_metadata` param to `geox_claim_create()` public signature
- **Stored** `extra_metadata` in payload dict and reflected in response

## Verification
- ✅ All 6 existing EGS claim tests pass (no regression)
- ✅ All 5 modes (create, validate, challenge, seal, attach_evidence) work
- ✅ Create with full literature metadata: epistemic_label, forbidden_uses, source_citation, category
- ✅ Create with partial metadata (only some fields)
- ✅ Create with no metadata (backward compat — returns `extra_metadata: null`)

## Diff Summary
- `claim_unified.py`: +68 lines (new types + docs + lit fields), -70 lines (removed kwargs) — net cleaner
- `claims.py`: +12 lines intentional (extra_metadata plumbing), ~50 lines auto-format noise

## Enables
- Literature-to-claims extraction pipeline (GEOX → claim with epistemic labels + forbidden uses + citations)
- Multi-model surface/tract tracking with confidence scores
- arifOS OBS/DER/INT/SPEC standard across GEOX claims

DITEMPA BUKAN DIBERI
