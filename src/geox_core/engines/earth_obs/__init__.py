"""earth_obs — Earth observation foundation model adapters (Phase A forge).

W₅-W₈: Constitutional wrapper around pretrained EO foundation models.

Currently scaffolding (mock backend). When the user authorizes weight
deployment (888_HOLD ticket), the adapter will switch to live inference.

Models in scope:
- Prithvi-EO-2.0 (NASA-IMPACT + IBM, HuggingFace)
- Clay v1.5 (Clay Foundation)
- TerraMind (IBM + ESA Φ-lab, ICCV 2025)
- Aurora (Microsoft, atmospheric)

DITEMPA BUKAN DIBERI — pretraining weights are forged, not given; trust envelope
is GEOX's job.
"""
