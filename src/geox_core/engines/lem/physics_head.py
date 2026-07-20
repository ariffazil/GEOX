"""
GEOX-LEM Physics Head — Forward-Physics Constraint Decoder
══════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

Enforces CANON-9 physics on LEM latent representations.

This is GEOX's unique differentiator: every LEM output is
constrained by forward physics models (rock physics, Archie,
density-porosity) so the model cannot hallucinate geologically
impossible values.

Architecture:
  Latent → Physics Forward Model → Physical Properties → Physics Loss
  The loss gradients backpropagate into the LEM transformer,
  embedding physics into the latent space itself.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("geox.lem.physics")

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


# ── Forward Physics Models ─────────────────────────────────────────────────

# These are pure torch functions that mirror geox_core.physics.parameters
# but operate on tensors for differentiable loss computation.


def gardner_density_torch(vp: torch.Tensor, alpha: float = 310.0, beta: float = 0.25) -> torch.Tensor:
    """ρ = α · Vp^β — Gardner's equation (differentiable)."""
    return alpha * (vp.clamp(min=1.0) ** beta)


def faust_velocity_torch(
    resistivity: torch.Tensor,
    depth: torch.Tensor,
    a: float = 2000.0,
    c: float = 0.5,
) -> torch.Tensor:
    """Vp = a · (depth · resistivity)^(1/6) — Faust's equation."""
    return a * ((depth.clamp(min=1.0) * resistivity.clamp(min=0.01)) ** (1.0 / 6.0))


def archie_sw_torch(
    rt: torch.Tensor,
    phi: torch.Tensor,
    rw: float = 0.05,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
) -> torch.Tensor:
    """Sw = (a · Rw / (Rt · φ^m))^(1/n) — Archie's equation."""
    phi = phi.clamp(min=0.001)
    rt = rt.clamp(min=0.01)
    return ((a * rw) / (rt * phi**m)) ** (1.0 / n)


def density_porosity_torch(
    rhob: torch.Tensor,
    rho_matrix: float = 2.65,
    rho_fluid: float = 1.0,
) -> torch.Tensor:
    """φ = (ρ_ma - ρ_log) / (ρ_ma - ρ_fl) — density porosity."""
    return (rho_matrix - rhob) / (rho_matrix - rho_fluid)


# ── Physics Head ────────────────────────────────────────────────────────────


class PhysicsConstraintHead(nn.Module):
    """
    Forward physics decoder that predicts physical properties
    from LEM latent representations and computes physics loss.

    This is NOT a separate network head — it is a mathematical
    constraint layer that enforces GEOX CANON-9 physics.
    """

    def __init__(
        self,
        latent_dim: int = 256,
        use_gardner: bool = True,
        use_faust: bool = True,
        use_archie: bool = True,
        use_density_porosity: bool = True,
        # Physics parameters
        rw: float = 0.05,
        archie_a: float = 1.0,
        archie_m: float = 2.0,
        archie_n: float = 2.0,
        rho_matrix: float = 2.65,
        rho_fluid: float = 1.0,
        # Loss weights
        lambda_physics: float = 1.0,
        lambda_archie: float = 0.5,
        lambda_density: float = 0.3,
        # Bounds
        phi_max: float = 0.45,
        vsh_max: float = 1.0,
        sw_max: float = 1.0,
    ):
        super().__init__()
        if not _HAS_TORCH:
            raise RuntimeError("PhysicsConstraintHead requires PyTorch")

        self.use_gardner = use_gardner
        self.use_faust = use_faust
        self.use_archie = use_archie
        self.use_density_porosity = use_density_porosity

        # Physics parameters
        self.rw = rw
        self.archie_a = archie_a
        self.archie_m = archie_m
        self.archie_n = archie_n
        self.rho_matrix = rho_matrix
        self.rho_fluid = rho_fluid

        # Loss weights
        self.lambda_physics = lambda_physics
        self.lambda_archie = lambda_archie
        self.lambda_density = lambda_density

        # Bounds
        self.phi_max = phi_max
        self.vsh_max = vsh_max
        self.sw_max = sw_max

        # Property prediction heads (latent → physical properties)
        # These are small MLPs that map the LEM latent to each property
        self.vsh_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )
        self.phi_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),  # φ ∈ [0, 1]
        )
        self.sw_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )
        self.vp_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
        self.density_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def enforce_bounds(self, vsh: torch.Tensor, phi: torch.Tensor, sw: torch.Tensor) -> torch.Tensor:
        """CANON-9 bound penalty: penalize values outside physical ranges."""
        bound_loss = (
            F.relu(vsh - self.vsh_max).mean()
            + F.relu(-vsh).mean()  # below 0
            + F.relu(phi - self.phi_max).mean()
            + F.relu(-phi).mean()
            + F.relu(sw - self.sw_max).mean()
            + F.relu(-sw).mean()
        )
        return bound_loss

    def forward(
        self,
        latents: torch.Tensor,
        gr: torch.Tensor | None = None,
        rt: torch.Tensor | None = None,
        rhob: torch.Tensor | None = None,
        nphi: torch.Tensor | None = None,
        depth: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        """
        Predict physical properties and compute physics loss.

        Args:
            latents: (B, T, D) LEM token embeddings
            gr: (B, T) gamma ray (optional, for Vsh calibration)
            rt: (B, T) resistivity (optional, for Archie)
            rhob: (B, T) bulk density (optional, for density φ)
            nphi: (B, T) neutron porosity (optional)
            depth: (B, T) depth in meters (optional, for Faust)

        Returns:
            dict with predicted properties and loss terms
        """
        # Predict properties from latents
        vsh = self.vsh_head(latents).squeeze(-1)  # (B, T)
        phi = self.phi_head(latents).squeeze(-1)  # (B, T)
        sw = self.sw_head(latents).squeeze(-1)  # (B, T)
        vp = self.vp_head(latents).squeeze(-1)  # (B, T)
        density = self.density_head(latents).squeeze(-1)  # (B, T)

        # Bound penalty
        bound_loss = self.enforce_bounds(vsh, phi, sw)

        # Physics loss terms
        total_physics_loss = bound_loss

        # Archie consistency: Sw_pred ≈ Sw_Archie(Rt, φ)
        if self.use_archie and rt is not None:
            sw_archie = archie_sw_torch(
                rt,
                phi,
                rw=self.rw,
                a=self.archie_a,
                m=self.archie_m,
                n=self.archie_n,
            ).clamp(0, self.sw_max)
            archie_loss = F.mse_loss(sw, sw_archie)
            total_physics_loss = total_physics_loss + self.lambda_archie * archie_loss
        else:
            archie_loss = torch.tensor(0.0, device=latents.device)

        # Density-porosity consistency: ρ_pred ≈ ρ(φ)
        if self.use_density_porosity and rhob is not None:
            rhob_pred = self.rho_matrix * (1.0 - phi) + self.rho_fluid * phi
            density_loss = F.mse_loss(rhob, rhob_pred)
            total_physics_loss = total_physics_loss + self.lambda_density * density_loss
        else:
            density_loss = torch.tensor(0.0, device=latents.device)

        # Gardner consistency: ρ_pred ≈ Gardner(Vp)
        if self.use_gardner:
            gardner_rho = gardner_density_torch(vp.clamp(min=1500.0, max=6500.0))
            gardner_loss = F.mse_loss(density, gardner_rho / 1000.0)  # Scale to g/cc
            total_physics_loss = total_physics_loss + gardner_loss * 0.2
        else:
            gardner_loss = torch.tensor(0.0, device=latents.device)

        return {
            "vsh": vsh,
            "phi": phi,
            "sw": sw,
            "vp": vp,
            "density": density,
            "bound_loss": bound_loss,
            "archie_loss": archie_loss,
            "density_loss": density_loss,
            "gardner_loss": gardner_loss,
            "total_physics_loss": total_physics_loss,
        }


__all__ = [
    "PhysicsConstraintHead",
    "archie_sw_torch",
    "gardner_density_torch",
    "faust_velocity_torch",
    "density_porosity_torch",
]
