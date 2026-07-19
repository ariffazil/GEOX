"""
GEOX-LEM — Large Earth Model Engine
══════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

GEOX's neural architecture for fusing multi-modal Earth data
(well logs, seismic, petrophysics, basin maps) into a unified
latent representation with physics constraints and governance.

Modules:
  config.py     — Configuration dataclasses
  tokenizer.py  — VQ-VAE for well log discretization
  dataset.py    — Training data pipeline from LAS files
  model.py      — Cross-modal fusion transformer
  physics_head.py — Forward-physics constraint decoder
  pretrain.py   — Self-supervised training pipeline

Usage:
  from geox_core.engines.lem import LEMConfig, WellLogVQVAE, LEMTransformer
  from geox_core.engines.lem.pretrain import run_pretraining_pipeline

  config = LEMConfig()
  summary = run_pretraining_pipeline(config)
"""

from .config import CONFIG, DataConfig, LEMConfig, PhysicsHeadConfig, PretrainConfig, TokenizerConfig
from .dataset import WellLogDataset, create_lem_dataloader, inspect_data
from .model import LEMLoss, LEMTransformer
from .physics_head import PhysicsConstraintHead
from .pretrain import pretrain_transformer, run_pretraining_pipeline, train_tokenizer
from .tokenizer import CURVE_DEFINITIONS, NUM_CURVES, VectorQuantizer, WellLogVQVAE

__all__ = [
    "LEMConfig", "CONFIG", "TokenizerConfig", "PretrainConfig",
    "PhysicsHeadConfig", "DataConfig",
    "WellLogVQVAE", "VectorQuantizer",
    "WellLogDataset", "create_lem_dataloader", "inspect_data",
    "LEMTransformer", "LEMLoss",
    "PhysicsConstraintHead",
    "train_tokenizer", "pretrain_transformer", "run_pretraining_pipeline",
    "CURVE_DEFINITIONS", "NUM_CURVES",
]
