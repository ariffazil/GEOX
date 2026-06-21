"""
GEOX-LEM Model — Cross-Modal Fusion Transformer
══════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

The core transformer backbone of GEOX-LEM that:
  1. Takes discrete geological tokens from the VQ tokenizer
  2. Adds positional encoding (depth-aware) + modality embeddings
  3. Applies masked token modeling (MTM) for self-supervised learning
  4. Supports cross-modal fusion (logs + seismic + basin metadata)
  5. Outputs token predictions and latent representations

Architecture: Transformer encoder (6-8 layers) with:
  - Token embeddings from VQ codebook
  - Depth positional encoding (sinusoidal + learned)
  - Modality type embeddings (well log, seismic, basin)
  - Geolocation embeddings (lat/lon)
  - Masked token prediction head
  - Contrastive projection head for stratigraphy-aware learning
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("geox.lem.model")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    torch = None
    nn = None
    F = None


# ── Positional Encoding ─────────────────────────────────────────────────────

class SinusoidalPositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for depth-aware positioning."""

    def __init__(self, d_model: int, max_len: int = 1024):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding to input.
        
        Args:
            x: (B, T, D) input tokens
        Returns:
            (B, T, D) input with position added
        """
        return x + self.pe[:, :x.size(1), :]


class LearnedDepthEncoding(nn.Module):
    """Learned embedding for relative depth position."""

    def __init__(self, max_depth_bins: int = 256, embed_dim: int = 64):
        super().__init__()
        self.embed = nn.Embedding(max_depth_bins, embed_dim)
        self.max_bins = max_depth_bins

    def forward(self, depth_indices: torch.Tensor) -> torch.Tensor:
        """
        Args:
            depth_indices: (B, T) integer depth bin indices [0, max_bins)
        Returns:
            (B, T, D) depth embeddings
        """
        depth_indices = depth_indices.clamp(0, self.max_bins - 1)
        return self.embed(depth_indices)


# ── Geolocation Embedding ───────────────────────────────────────────────────

class GeoLocationEmbedding(nn.Module):
    """Learned embedding for geographic location (basin, lat/lon)."""

    def __init__(
        self,
        num_basins: int = 50,
        lat_lon_dim: int = 16,
        output_dim: int = 32,
    ):
        super().__init__()
        self.basin_embed = nn.Embedding(num_basins, output_dim // 2)
        self.coord_proj = nn.Linear(2, lat_lon_dim)
        self.fusion = nn.Linear(output_dim // 2 + lat_lon_dim, output_dim)

    def forward(
        self,
        basin_ids: Optional[torch.Tensor] = None,
        coords: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            basin_ids: (B,) or (B, 1) integer basin IDs
            coords: (B, 2) float [lat, lon]
        Returns:
            (B, D) geolocation embeddings
        """
        B = basin_ids.shape[0] if basin_ids is not None else (coords.shape[0] if coords is not None else 1)
        device = self.coord_proj.weight.device

        if basin_ids is not None:
            basin_feat = self.basin_embed(basin_ids.squeeze(-1).long())
        else:
            basin_feat = torch.zeros(B, self.basin_embed.embedding_dim, device=device)

        if coords is not None:
            coord_feat = F.relu(self.coord_proj(coords.float()))
        else:
            coord_feat = torch.zeros(B, self.coord_proj.out_features, device=device)

        return F.relu(self.fusion(torch.cat([basin_feat, coord_feat], dim=-1)))


# ── Cross-Modal Fusion Transformer ──────────────────────────────────────────

class LEMTransformer(nn.Module):
    """
    GEOX Large Earth Model — Transformer backbone.
    
    Takes token sequences from VQ tokenizer and learns
    contextual geological representations via masked modeling.
    """

    def __init__(
        self,
        vocab_size: int = 512,           # Codebook size
        embed_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        ff_dim: int = 1024,
        dropout: float = 0.1,
        max_seq_len: int = 512,
        num_modalities: int = 3,         # well_log, seismic, basin
        num_basins: int = 50,
        use_geolocation: bool = True,
    ):
        super().__init__()
        if not _HAS_TORCH:
            raise RuntimeError("LEMTransformer requires PyTorch")

        self.embed_dim = embed_dim
        self.vocab_size = vocab_size
        self.use_geolocation = use_geolocation

        # Token embeddings (from codebook)
        self.token_embed = nn.Embedding(vocab_size, embed_dim)
        
        # Modality type embeddings
        self.modality_embed = nn.Embedding(num_modalities, embed_dim)
        
        # Positional encoding
        self.pos_encoder = SinusoidalPositionalEncoding(embed_dim, max_seq_len)
        
        # Geolocation
        if use_geolocation:
            self.geo_embed = GeoLocationEmbedding(
                num_basins=num_basins,
                output_dim=embed_dim,
            )

        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=ff_dim,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,  # Pre-norm for stability
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        # Prediction head
        self.ln_final = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, vocab_size)

        # Contrastive projection head
        self.contrast_head = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.ReLU(),
            nn.Linear(embed_dim, embed_dim // 2),
        )

        # Depth projection (for depth-aware pretraining)
        self.depth_head = nn.Sequential(
            nn.Linear(embed_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

        # Initialize
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight, gain=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            nn.init.ones_(module.weight)
            nn.init.zeros_(module.bias)

    def forward(
        self,
        tokens: torch.Tensor,
        modality_ids: Optional[torch.Tensor] = None,
        depth_positions: Optional[torch.Tensor] = None,
        basin_ids: Optional[torch.Tensor] = None,
        coords: Optional[torch.Tensor] = None,
        mask: Optional[torch.Tensor] = None,
        return_embeddings: bool = False,
    ) -> dict[str, torch.Tensor]:
        """
        Args:
            tokens: (B, T) discrete token indices
            modality_ids: (B, T) modality type (0=well_log, 1=seismic, 2=basin)
            depth_positions: (B, T) depth bin indices
            basin_ids: (B,) basin identifiers
            coords: (B, 2) lat/lon coordinates
            mask: (B, T) attention mask (True = masked/padded)
            return_embeddings: If True, also return intermediate embeddings
        
        Returns:
            dict with:
                - 'logits': (B, T, V) token predictions
                - 'embeddings': (B, T, D) token embeddings (if requested)
                - 'sequence_embed': (B, D) sequence-level embedding
        """
        B, T = tokens.shape
        device = tokens.device

        # Token embeddings
        x = self.token_embed(tokens)  # (B, T, D)

        # Add modality embeddings
        if modality_ids is not None:
            x = x + self.modality_embed(modality_ids)
        else:
            # Default to well_log modality (0)
            default_mod = torch.zeros(B, T, dtype=torch.long, device=device)
            x = x + self.modality_embed(default_mod)

        # Add depth positional encoding
        if depth_positions is not None:
            depth_ratio = depth_positions.float() / (depth_positions.max() + 1e-8)
            depth_encoding = self.pos_encoder.pe[:, :T, :] * depth_ratio.unsqueeze(-1)
            x = x + depth_encoding
        else:
            x = self.pos_encoder(x)

        # Add geolocation embedding to all tokens
        if self.use_geolocation:
            geo = self.geo_embed(basin_ids, coords)  # (B, D)
            x = x + geo.unsqueeze(1)  # (B, T, D)

        # Transformer
        attn_mask = None
        if mask is not None:
            # Convert bool mask to float mask (True → -inf for attention)
            attn_mask = mask.float().masked_fill(mask, float("-inf")).masked_fill(~mask, 0.0)
            attn_mask = attn_mask.unsqueeze(1).unsqueeze(2)  # (B, 1, 1, T)

        h = self.transformer(x, mask=attn_mask)
        h = self.ln_final(h)

        # Predictions
        logits = self.head(h)  # (B, T, V)

        result = {"logits": logits}

        if return_embeddings:
            result["embeddings"] = h

        # Sequence-level embedding (mean pool over valid tokens)
        if mask is not None:
            valid_mask = (~mask).float().unsqueeze(-1)  # (B, T, 1)
            seq_embed = (h * valid_mask).sum(dim=1) / valid_mask.sum(dim=1).clamp(min=1)
        else:
            seq_embed = h.mean(dim=1)
        result["sequence_embed"] = seq_embed

        return result

    def predict_masked(
        self,
        tokens: torch.Tensor,
        mask_positions: torch.Tensor,
        **kwargs,
    ) -> torch.Tensor:
        """
        Predict tokens at masked positions.
        
        Args:
            tokens: (B, T) tokens with MASK tokens at mask_positions
            mask_positions: (B, M) integer positions of masked tokens
            **kwargs: Passed to forward()
        
        Returns:
            predictions: (B, M, V) logits for each masked position
        """
        outputs = self.forward(tokens, **kwargs)
        logits = outputs["logits"]  # (B, T, V)
        
        # Gather predictions at masked positions
        B, M = mask_positions.shape
        mask_positions = mask_positions.unsqueeze(-1).expand(B, M, logits.size(-1))
        predictions = torch.gather(logits, 1, mask_positions)
        return predictions

    def get_contrastive_embedding(
        self,
        tokens: torch.Tensor,
        **kwargs,
    ) -> torch.Tensor:
        """Get contrastive projection of sequence embedding.
        
        Used for stratigraphy-aware contrastive learning.
        """
        outputs = self.forward(tokens, return_embeddings=False, **kwargs)
        seq = outputs["sequence_embed"]
        return F.normalize(self.contrast_head(seq), dim=-1)


# ── Pretraining Loss ────────────────────────────────────────────────────────

class LEMLoss(nn.Module):
    """Combined loss for GEOX-LEM pretraining."""

    def __init__(
        self,
        contrastive_weight: float = 0.1,
        temperature: float = 0.1,
    ):
        super().__init__()
        self.contrastive_weight = contrastive_weight
        self.temperature = temperature

    def forward(
        self,
        logits: torch.Tensor,
        target_tokens: torch.Tensor,
        mask: torch.Tensor,
        query_embeddings: Optional[torch.Tensor] = None,
        positive_embeddings: Optional[torch.Tensor] = None,
    ) -> dict[str, torch.Tensor]:
        """
        Args:
            logits: (B, T, V) predicted logits
            target_tokens: (B, T) ground truth token IDs
            mask: (B, T) boolean — True where masked (loss computed)
            query_embeddings: (B, D) for contrastive learning
            positive_embeddings: (B, D) positive pairs
        
        Returns:
            dict with 'mtm_loss', 'contrastive_loss', 'total_loss'
        """
        # Masked Token Modeling loss
        logits_flat = logits.view(-1, logits.size(-1))  # (B*T, V)
        targets_flat = target_tokens.view(-1)
        mask_flat = mask.view(-1)

        mtm_loss = F.cross_entropy(
            logits_flat[mask_flat],
            targets_flat[mask_flat],
            reduction="mean",
        )

        total = mtm_loss

        # Contrastive loss
        contrastive_loss = torch.tensor(0.0, device=logits.device)
        if query_embeddings is not None and positive_embeddings is not None:
            # InfoNCE loss
            sim = torch.matmul(
                F.normalize(query_embeddings, dim=-1),
                F.normalize(positive_embeddings, dim=-1).T,
            ) / self.temperature  # (B, B)

            labels = torch.arange(sim.size(0), device=sim.device)
            contrastive_loss = F.cross_entropy(sim, labels)
            total = total + self.contrastive_weight * contrastive_loss

        return {
            "mtm_loss": mtm_loss,
            "contrastive_loss": contrastive_loss,
            "total_loss": total,
        }


__all__ = [
    "LEMTransformer",
    "LEMLoss",
    "SinusoidalPositionalEncoding",
    "GeoLocationEmbedding",
    "LearnedDepthEncoding",
]
