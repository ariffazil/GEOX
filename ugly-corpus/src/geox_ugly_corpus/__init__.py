"""GEOX Ugly Corpus — a 100% synthetic, deterministic benchmark.

Every fixture is generated from a fixed seed at run time. Nothing here is real
well data, and nothing is downloaded. Each fixture carries a SHA-256 so any
claim about a run can be re-derived from the bytes that produced it.

The corpus does not promise that GEOX passes. It measures the truth contracts
that GEOX claims: raw-vs-computed curve separation (L5), fail-closed QC, and
refusal of unphysical input (G-1). A red contract is the product working.
"""

__version__ = "0.1.0"
SEED = 20261124
