"""
GEOX-LEM Configuration
═══════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

All configuration for training the GEOX Large Earth Model.
Single source of truth — edit here, not in code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Tokenizer ───────────────────────────────────────────────────────────────


@dataclass
class TokenizerConfig:
    """VQ-VAE tokenizer configuration for well log discretization."""

    # Input
    input_curves: tuple[str, ...] = ("GR", "RT", "RHOB", "NPHI", "DT", "SP")
    patch_length: int = 32  # Depth window (samples)
    patch_stride: int = 8  # Stride between patches

    # VQ codebook
    codebook_size: int = 512  # Number of geological tokens
    codebook_dim: int = 64  # Embedding dimension per token
    commitment_beta: float = 0.25  # VQ commitment loss weight

    # Encoder/Decoder
    encoder_hidden: tuple[int, ...] = (128, 64)
    decoder_hidden: tuple[int, ...] = (64, 128)

    # Training
    tokenizer_lr: float = 3e-4
    tokenizer_epochs: int = 200
    tokenizer_batch_size: int = 256


# ── Pretraining ─────────────────────────────────────────────────────────────


@dataclass
class PretrainConfig:
    """Self-supervised pretraining configuration."""

    # Model architecture
    embed_dim: int = 256
    num_heads: int = 8
    num_layers: int = 6
    ff_dim: int = 1024
    dropout: float = 0.1
    max_seq_len: int = 512

    # Geolocation embedding
    use_geolocation: bool = True
    geo_embed_dim: int = 32

    # Missing modality handling
    modality_dropout: float = 0.15  # Probability to drop a curve group

    # Training
    lr: float = 1e-4
    weight_decay: float = 0.01
    warmup_steps: int = 1000
    max_epochs: int = 500
    batch_size: int = 64
    gradient_clip: float = 1.0

    # Masked Token Modeling
    mask_ratio: float = 0.30
    mask_block_size: int = 8  # Consecutive tokens to mask as block

    # Contrastive learning
    contrastive_weight: float = 0.1
    contrastive_temperature: float = 0.1
    contrastive_similarity_threshold: float = 0.7

    # Hardware
    num_workers: int = 4
    device: str = "cpu"  # Fallback — will detect CUDA if available
    amp: bool = False  # Mixed precision (requires GPU)


# ── Physics Head ────────────────────────────────────────────────────────────


@dataclass
class PhysicsHeadConfig:
    """Forward-physics decoder for constraining LEM outputs."""

    # Rock physics models to apply
    use_gardner: bool = True  # Density from Vp
    use_faust: bool = True  # Velocity from resistivity + depth
    use_archie: bool = True  # Sw from resistivity + porosity
    use_density_porosity: bool = True  # Phi from density

    # Physics loss weights
    lambda_physics: float = 1.0
    lambda_archie: float = 0.5
    lambda_density: float = 0.3

    # Physics bounds (CANON-9)
    phi_max: float = 0.45
    vsh_max: float = 1.0
    sw_max: float = 1.0


# ── Data Pipeline ───────────────────────────────────────────────────────────


@dataclass
class DataConfig:
    """Training data pipeline configuration."""

    # Data sources
    well_data_dir: str = "data/wells"
    las_file_pattern: str = "*.las"
    segy_data_dir: str | None = None
    panel_data_dir: str = "data/geox_panels"

    # Well log selection
    min_depth_samples: int = 100  # Skip wells with fewer samples
    max_null_pct: float = 0.50  # Skip wells with >50% missing curves
    required_curves: tuple[str, ...] = ("GR",)  # At minimum GR must exist

    # Normalization
    normalize_per_well: bool = True  # Z-score per well
    clip_outliers: bool = True
    outlier_std_threshold: float = 5.0

    # Splits
    val_wells: float = 0.15
    test_wells: float = 0.10
    seed: int = 42


# ── Master Config ───────────────────────────────────────────────────────────


@dataclass
class LEMConfig:
    """Master configuration for GEOX-LEM."""

    tokenizer: TokenizerConfig = field(default_factory=TokenizerConfig)
    pretrain: PretrainConfig = field(default_factory=PretrainConfig)
    physics: PhysicsHeadConfig = field(default_factory=PhysicsHeadConfig)
    data: DataConfig = field(default_factory=DataConfig)
    run_name: str = "geox-lem-v1"
    checkpoint_dir: str = "checkpoints/lem"
    log_dir: str = "logs/lem"


# Singleton
CONFIG = LEMConfig()
