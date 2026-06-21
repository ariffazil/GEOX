"""
GEOX-LEM Pretraining — Self-Supervised Training Loop
═══════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

End-to-end pretraining pipeline for GEOX-LEM:

  Phase 1: Train VQ-VAE tokenizer on well log patches
  Phase 2: Tokenize all well data into discrete tokens
  Phase 3: Pretrain LEMTransformer with masked token modeling
  Phase 4: (Future) Fine-tune on labeled data

Each phase is independently runnable with logging and checkpointing.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

from .config import LEMConfig
from .tokenizer import WellLogVQVAE, NUM_CURVES
from .dataset import WellLogDataset, create_lem_dataloader
from .model import LEMTransformer, LEMLoss
from .physics_head import PhysicsConstraintHead

logger = logging.getLogger("geox.lem.pretrain")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader
    from torch.optim import AdamW
    from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    torch = None
    nn = None
    F = None
    DataLoader = None
    AdamW = None
    CosineAnnealingWarmRestarts = None


# ── Phase 1: Tokenizer Training ─────────────────────────────────────────────

def train_tokenizer(
    config: LEMConfig,
    resume_from: Optional[str] = None,
) -> dict[str, Any]:
    """
    Phase 1: Train VQ-VAE tokenizer on well log patches.
    
    Returns training summary with loss history and codebook statistics.
    """
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch required for training")

    device = torch.device(config.pretrain.device)
    logger.info(f"Phase 1: Training VQ-VAE tokenizer on {device}")

    # Data
    dataset = WellLogDataset(
        data_dir=config.data.well_data_dir,
        patch_length=config.tokenizer.patch_length,
        patch_stride=config.tokenizer.patch_stride,
    )
    loader = DataLoader(
        dataset,
        batch_size=config.tokenizer.tokenizer_batch_size,
        shuffle=True,
        num_workers=config.pretrain.num_workers,
    )

    # Model
    tokenizer = WellLogVQVAE(
        in_channels=NUM_CURVES,
        latent_dim=config.tokenizer.codebook_dim,
        codebook_size=config.tokenizer.codebook_size,
        codebook_dim=config.tokenizer.codebook_dim,
        commitment_beta=config.tokenizer.commitment_beta,
    ).to(device)

    if resume_from:
        tokenizer.load_state_dict(torch.load(resume_from, map_location=device))
        logger.info(f"Resumed tokenizer from {resume_from}")

    # Optimizer
    optimizer = AdamW(tokenizer.parameters(), lr=config.tokenizer.tokenizer_lr)

    # Training loop
    history = {"recon_loss": [], "commitment_loss": [], "codebook_loss": [], "total_loss": []}
    best_loss = float("inf")
    n_batches = len(loader)

    tokenizer.train()
    for epoch in range(config.tokenizer.tokenizer_epochs):
        epoch_losses: dict[str, float] = {"recon": 0.0, "commit": 0.0, "codebook": 0.0, "total": 0.0}

        for batch_idx, batch in enumerate(loader):
            curves = batch["curves"].to(device)  # (B, C, L)

            optimizer.zero_grad()
            x_recon, tokens, commitment_loss, codebook_loss = tokenizer(curves)
            losses = tokenizer.loss(curves, x_recon, commitment_loss, codebook_loss)
            losses["total_loss"].backward()
            optimizer.step()

            epoch_losses["recon"] += losses["recon_loss"].item()
            epoch_losses["commit"] += losses["commitment_loss"].item()
            epoch_losses["codebook"] += losses["codebook_loss"].item()
            epoch_losses["total"] += losses["total_loss"].item()

        # Average
        for k in epoch_losses:
            epoch_losses[k] /= n_batches

        history["recon_loss"].append(epoch_losses["recon"])
        history["commitment_loss"].append(epoch_losses["commit"])
        history["codebook_loss"].append(epoch_losses["codebook"])
        history["total_loss"].append(epoch_losses["total"])

        if (epoch + 1) % 10 == 0:
            logger.info(
                f"Tokenizer epoch {epoch+1}/{config.tokenizer.tokenizer_epochs} | "
                f"recon={epoch_losses['recon']:.6f} commit={epoch_losses['commit']:.6f} "
                f"total={epoch_losses['total']:.6f}"
            )

        # Checkpoint
        if epoch_losses["total"] < best_loss:
            best_loss = epoch_losses["total"]
            os.makedirs(config.checkpoint_dir, exist_ok=True)
            ckpt_path = os.path.join(config.checkpoint_dir, "tokenizer_best.pt")
            torch.save(tokenizer.state_dict(), ckpt_path)

    # Save final
    final_path = os.path.join(config.checkpoint_dir, "tokenizer_final.pt")
    torch.save(tokenizer.state_dict(), final_path)

    # Codebook analysis
    vocab = tokenizer.get_geological_vocabulary()

    summary = {
        "status": "complete",
        "epochs": config.tokenizer.tokenizer_epochs,
        "best_loss": best_loss,
        "final_loss": epoch_losses["total"],
        "codebook_size": config.tokenizer.codebook_size,
        "final_ckpt": final_path,
        "num_training_patches": len(dataset),
        "codebook_usage": len(vocab),
    }
    logger.info(f"Phase 1 complete: {json.dumps(summary, indent=2)}")
    return summary


# ── Phase 2: Tokenize All Data ──────────────────────────────────────────────

def tokenize_dataset(
    config: LEMConfig,
    tokenizer_ckpt: str,
) -> dict[str, Any]:
    """
    Phase 2: Run trained tokenizer on all well data to produce token sequences.
    
    Saves tokenized dataset to checkpoint_dir for Phase 3 pretraining.
    """
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch required")

    device = torch.device(config.pretrain.device)
    logger.info(f"Phase 2: Tokenizing dataset with {tokenizer_ckpt}")

    # Load tokenizer
    tokenizer = WellLogVQVAE(
        in_channels=NUM_CURVES,
        latent_dim=config.tokenizer.codebook_dim,
        codebook_size=config.tokenizer.codebook_size,
        codebook_dim=config.tokenizer.codebook_dim,
    ).to(device)
    tokenizer.load_state_dict(torch.load(tokenizer_ckpt, map_location=device))
    tokenizer.eval()

    # Data
    dataset = WellLogDataset(
        data_dir=config.data.well_data_dir,
        patch_length=config.tokenizer.patch_length,
        patch_stride=config.tokenizer.patch_stride,
    )
    loader = DataLoader(
        dataset,
        batch_size=256,
        shuffle=False,
        num_workers=config.pretrain.num_workers,
    )

    # Tokenize
    all_tokens: list[np.ndarray] = []
    all_well_ids: list[str] = []
    token_frequencies: dict[int, int] = {}

    with torch.no_grad():
        for batch in loader:
            curves = batch["curves"].to(device)
            _, _, commit_loss, codebook_loss = tokenizer(curves)

            # Get token indices
            z = tokenizer.encoder(curves)
            z_q, tokens, _, _ = tokenizer.quantizer(z)

            all_tokens.append(tokens.cpu().numpy())
            all_well_ids.extend(batch["well_id"])

            # Update frequencies
            for t in tokens.cpu().numpy().flatten():
                token_frequencies[int(t)] = token_frequencies.get(int(t), 0) + 1

    # Save tokenized dataset
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    token_data = {
        "tokens": np.concatenate(all_tokens, axis=0),
        "well_ids": all_well_ids,
        "token_frequencies": token_frequencies,
        "config": {
            "codebook_size": config.tokenizer.codebook_size,
            "patch_length": config.tokenizer.patch_length,
        },
    }
    save_path = os.path.join(config.checkpoint_dir, "tokenized_data.npz")
    np.savez_compressed(save_path, **token_data)

    summary = {
        "status": "complete",
        "num_patches": len(all_tokens),
        "unique_tokens_used": len(token_frequencies),
        "codebook_coverage": f"{len(token_frequencies)}/{config.tokenizer.codebook_size}",
        "save_path": save_path,
        "most_common_token": max(token_frequencies, key=token_frequencies.get),
        "most_common_count": max(token_frequencies.values()),
    }
    logger.info(f"Phase 2 complete: {json.dumps(summary, indent=2)}")
    return summary


# ── Phase 3: Transformer Pretraining ────────────────────────────────────────

def pretrain_transformer(
    config: LEMConfig,
    tokenized_data_path: Optional[str] = None,
    resume_from: Optional[str] = None,
) -> dict[str, Any]:
    """
    Phase 3: Pretrain LEMTransformer with masked token modeling.
    
    Uses tokenized data from Phase 2.
    """
    if not _HAS_TORCH:
        raise RuntimeError("PyTorch required")

    device = torch.device(config.pretrain.device)
    logger.info(f"Phase 3: Pretraining LEMTransformer on {device}")

    # Load tokenized data
    if tokenized_data_path is None:
        tokenized_data_path = os.path.join(config.checkpoint_dir, "tokenized_data.npz")

    data = np.load(tokenized_data_path, allow_pickle=True)
    tokens = data["tokens"]  # (N, T)
    token_frequencies = data.get("token_frequencies", {}).item() if "token_frequencies" in data else {}

    # Build model
    model = LEMTransformer(
        vocab_size=config.tokenizer.codebook_size,
        embed_dim=config.pretrain.embed_dim,
        num_heads=config.pretrain.num_heads,
        num_layers=config.pretrain.num_layers,
        ff_dim=config.pretrain.ff_dim,
        dropout=config.pretrain.dropout,
        max_seq_len=config.pretrain.max_seq_len,
    ).to(device)

    if resume_from:
        model.load_state_dict(torch.load(resume_from, map_location=device))
        logger.info(f"Resumed model from {resume_from}")

    # Physics head (for consistency loss)
    physics_head = PhysicsConstraintHead(
        latent_dim=config.pretrain.embed_dim,
        phi_max=config.physics.phi_max,
    ).to(device)

    # Loss
    criterion = LEMLoss(
        contrastive_weight=config.pretrain.contrastive_weight,
        temperature=config.pretrain.contrastive_temperature,
    )

    # Optimizer & scheduler
    optimizer = AdamW(
        list(model.parameters()) + list(physics_head.parameters()),
        lr=config.pretrain.lr,
        weight_decay=config.pretrain.weight_decay,
    )
    scheduler = CosineAnnealingWarmRestarts(
        optimizer, T_0=config.pretrain.warmup_steps, T_mult=2,
    )

    # Convert tokens to tensors
    tokens_tensor = torch.from_numpy(tokens).long().to(device)
    N, T = tokens_tensor.shape

    # Training loop
    history = {"mtm_loss": [], "physics_loss": [], "total_loss": []}
    best_loss = float("inf")
    step = 0

    model.train()
    physics_head.train()

    for epoch in range(config.pretrain.max_epochs):
        # Shuffle
        perm = torch.randperm(N, device=device)
        epoch_losses: dict[str, float] = {"mtm": 0.0, "physics": 0.0, "total": 0.0}
        batch_size = config.pretrain.batch_size
        n_batches = (N + batch_size - 1) // batch_size

        for batch_start in range(0, N, batch_size):
            batch_idx = perm[batch_start: batch_start + batch_size]
            batch_tokens = tokens_tensor[batch_idx]  # (B, T)

            # Create masked version
            masked_tokens, mask, mask_positions = _create_masked_input(
                batch_tokens,
                mask_ratio=config.pretrain.mask_ratio,
                mask_block_size=config.pretrain.mask_block_size,
                mask_token_id=config.tokenizer.codebook_size,  # Use vocab_size as [MASK]
            )

            # Forward
            outputs = model(masked_tokens, return_embeddings=True)
            logits = outputs["logits"]
            embeddings = outputs["embeddings"]

            # Loss
            losses = criterion(logits, batch_tokens, mask)

            # Physics consistency loss on embeddings
            physics_out = physics_head(embeddings)
            physics_loss = physics_out["total_physics_loss"]
            total = losses["total_loss"] + physics_loss * 0.1

            # Backward
            optimizer.zero_grad()
            total.backward()
            torch.nn.utils.clip_grad_norm_(
                list(model.parameters()) + list(physics_head.parameters()),
                config.pretrain.gradient_clip,
            )
            optimizer.step()
            scheduler.step()
            step += 1

            epoch_losses["mtm"] += losses["mtm_loss"].item()
            epoch_losses["physics"] += physics_loss.item()
            epoch_losses["total"] += total.item()

        # Average
        for k in epoch_losses:
            epoch_losses[k] /= n_batches

        history["mtm_loss"].append(epoch_losses["mtm"])
        history["physics_loss"].append(epoch_losses["physics"])
        history["total_loss"].append(epoch_losses["total"])

        if (epoch + 1) % 10 == 0:
            logger.info(
                f"Pretrain epoch {epoch+1}/{config.pretrain.max_epochs} | "
                f"mtm={epoch_losses['mtm']:.4f} physics={epoch_losses['physics']:.4f} "
                f"total={epoch_losses['total']:.4f}"
            )

        # Checkpoint
        if epoch_losses["total"] < best_loss:
            best_loss = epoch_losses["total"]
            os.makedirs(config.checkpoint_dir, exist_ok=True)
            ckpt_path = os.path.join(config.checkpoint_dir, "lem_best.pt")
            torch.save({
                "model": model.state_dict(),
                "physics_head": physics_head.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch,
                "loss": best_loss,
                "config": {
                    "vocab_size": config.tokenizer.codebook_size,
                    "embed_dim": config.pretrain.embed_dim,
                    "num_layers": config.pretrain.num_layers,
                    "num_heads": config.pretrain.num_heads,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, ckpt_path)

        # Early stopping check
        if epoch > 50 and epoch_losses["total"] > best_loss * 3:
            logger.info(f"Early stopping at epoch {epoch+1} (loss diverging)")
            break

    # Save final
    final_path = os.path.join(config.checkpoint_dir, "lem_final.pt")
    torch.save({
        "model": model.state_dict(),
        "physics_head": physics_head.state_dict(),
        "config": {
            "vocab_size": config.tokenizer.codebook_size,
            "embed_dim": config.pretrain.embed_dim,
            "num_layers": config.pretrain.num_layers,
            "num_heads": config.pretrain.num_heads,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, final_path)

    summary = {
        "status": "complete",
        "epochs": epoch + 1,
        "best_loss": float(best_loss),
        "final_loss": float(epoch_losses["total"]),
        "final_mtm_loss": float(epoch_losses["mtm"]),
        "final_physics_loss": float(epoch_losses["physics"]),
        "model_size_m_params": sum(p.numel() for p in model.parameters()) / 1e6,
        "final_ckpt": final_path,
        "num_training_sequences": N,
        "sequence_length": T,
    }
    logger.info(f"Phase 3 complete: {json.dumps(summary, indent=2)}")
    return summary


# ── Masking Helper ──────────────────────────────────────────────────────────

def _create_masked_input(
    tokens: torch.Tensor,
    mask_ratio: float = 0.30,
    mask_block_size: int = 8,
    mask_token_id: int = 99999,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Create masked input for MTM pretraining.
    
    Args:
        tokens: (B, T) input tokens
        mask_ratio: Fraction of tokens to mask
        mask_block_size: Consecutive tokens masked as a block
        mask_token_id: Token ID to use for [MASK]
    
    Returns:
        masked_tokens: (B, T) input with mask tokens
        mask: (B, T) boolean — True where masked
        mask_positions: (B, M) indices of masked positions
    """
    B, T = tokens.shape
    device = tokens.device

    # Randomly select positions to mask
    num_masked = max(1, int(T * mask_ratio))
    mask = torch.zeros(B, T, dtype=torch.bool, device=device)

    for b in range(B):
        # Choose starting positions
        starts = torch.randperm(T - mask_block_size + 1, device=device)
        n_blocks = max(1, num_masked // mask_block_size)
        selected_starts = starts[:n_blocks]
        for s in selected_starts:
            mask[b, s: s + mask_block_size] = True

    # Create masked input
    masked_tokens = tokens.clone()
    masked_tokens[mask] = mask_token_id

    # Positions
    mask_positions = mask.nonzero(as_tuple=True)[1].view(B, -1)

    return masked_tokens, mask, mask_positions


# ── Main ────────────────────────────────────────────────────────────────────

def run_pretraining_pipeline(config: LEMConfig) -> dict[str, Any]:
    """
    Run the full pretraining pipeline end-to-end.
    
    Returns combined summary of all phases.
    """
    # Phase 1: Train tokenizer
    tokenizer_summary = train_tokenizer(config)
    tokenizer_ckpt = tokenizer_summary["final_ckpt"]

    # Phase 2: Tokenize all data
    tokenize_summary = tokenize_dataset(config, tokenizer_ckpt)

    # Phase 3: Pretrain transformer
    tokenized_path = tokenize_summary["save_path"]
    transformer_summary = pretrain_transformer(config, tokenized_path)

    return {
        "run_name": config.run_name,
        "tokenizer": tokenizer_summary,
        "tokenize": tokenize_summary,
        "transformer": transformer_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


__all__ = [
    "train_tokenizer",
    "tokenize_dataset",
    "pretrain_transformer",
    "run_pretraining_pipeline",
]
