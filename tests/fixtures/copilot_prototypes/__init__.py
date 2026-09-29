"""
Copilot prototype fixtures — ROTAN-1 seismic interpretation (v3 → v7).

These files preserve the algorithm and approach that Copilot developed
through 5 successive iterations on the Morley et al. 2023 seismic section
(NW Sabah / Block H). The PROVENANCE is the same workflow that
`geox_seismic_display_trace.v1`, `geox_seismic_display_spectral_character.v1`
(forthcoming), and `geox_seismic_alternative_interpret.v1` now automate.

Each file is self-contained: it programmatically generates a SYNTHETIC
PNG that mimics the structural style of the original Morley figure (per
the user's "public synthetic data only" directive), then runs Copilot's
algorithm on that synthetic input and prints summary diagnostics.

DO NOT use the Morley et al. 2023 seismic image from /mnt/user-data/uploads/
or any other real-data source — those are excluded by sovereign policy.

Reference iteration:
  v3 — dip line + mini-basin polygons (geometry only)
  v4 — v3 + diapir interpretation (purple polygons)
  v5 — v4 + DRU/UIU/SRU horizons + thickness plausibility gate
  v6 — v5 + regional interpretation (foreland/wedge/mobile-shale) + frequency proxy (proxy only, NOT true instantaneous frequency)
  v7 — v6 + spectral decomposition RGB blend + sweetness attribute + final interpretation

Citations:
  Copilot session (2026-09-29) — algorithm developer
  Morley et al. 2023 (Geosphere v19 no.1) — stratigraphic ages + structure model
  Chopra & Marfurt 2007 — spectral decomposition methods
  van der Baan & Fomel 2009 — kurtosis-based phase rotation
"""
