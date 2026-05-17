"""
GEOX PINN — Physics-Informed Neural Network for Petrophysics
═══════════════════════════════════════════════════════════════════════════════
CANON-9 aligned: physics constraints are enforced as loss terms,
not post-hoc clipping. Every prediction carries a physics_violation
flag. If True → 888HOLD before reaching geox_mcp.

Architecture: 3-layer MLP (input → hidden → hidden → output)
Inputs:  normalized well log curves (GR, RHOB, NPHI, RT, DT)
Outputs: Vsh, φ, Sw — each bounded [0, 1] (φ default max 0.40)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("geox.pinn")

# ═══════════════════════════════════════════════════════════════════════════════
# Optional torch import — fail gracefully if not installed
# ═══════════════════════════════════════════════════════════════════════════════
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    _HAS_TORCH = True
except Exception as exc:
    _HAS_TORCH = False
    logger.warning(f"PyTorch not available; PINN layer disabled. Error: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# CANON-9 Physics Defaults
# ═══════════════════════════════════════════════════════════════════════════════

CANON9_DEFAULTS: dict[str, float] = {
    "rw": 0.05,
    "archie_a": 1.0,
    "archie_m": 2.0,
    "archie_n": 2.0,
    "matrix_density": 2.65,
    "fluid_density": 1.0,
    "vsh_max": 1.0,
    "phi_max": 0.40,
    "sw_max": 1.0,
}


class PINNPetrophysics:
    """
    Physics-Informed Neural Network for well-log petrophysics.

    Not a raw nn.Module wrapper — this is a GEOX engine that owns
    normalization, training, physics loss, and CANON-9 violation detection.
    """

    def __init__(
        self,
        input_dim: int = 5,
        hidden_dims: tuple[int, ...] = (128, 64),
        output_dim: int = 3,
        *,
        rw: float = CANON9_DEFAULTS["rw"],
        archie_a: float = CANON9_DEFAULTS["archie_a"],
        archie_m: float = CANON9_DEFAULTS["archie_m"],
        archie_n: float = CANON9_DEFAULTS["archie_n"],
        matrix_density: float = CANON9_DEFAULTS["matrix_density"],
        fluid_density: float = CANON9_DEFAULTS["fluid_density"],
        vsh_max: float = CANON9_DEFAULTS["vsh_max"],
        phi_max: float = CANON9_DEFAULTS["phi_max"],
        sw_max: float = CANON9_DEFAULTS["sw_max"],
        lambda_phys: float = 1.0,
        lambda_archie: float = 0.5,
        lambda_density: float = 0.3,
        device: Optional[str] = None,
    ) -> None:
        if not _HAS_TORCH:
            raise RuntimeError(
                "PINNPetrophysics requires PyTorch. Install: pip install torch"
            )

        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim

        # Archie parameters
        self.rw = rw
        self.archie_a = archie_a
        self.archie_m = archie_m
        self.archie_n = archie_n

        # Density parameters
        self.matrix_density = matrix_density
        self.fluid_density = fluid_density

        # Bounds
        self.vsh_max = vsh_max
        self.phi_max = phi_max
        self.sw_max = sw_max

        # Loss weights
        self.lambda_phys = lambda_phys
        self.lambda_archie = lambda_archie
        self.lambda_density = lambda_density

        # Device
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        # Build MLP
        layers: list[nn.Module] = []
        prev = input_dim
        for h in hidden_dims:
            layers.extend([nn.Linear(prev, h), nn.ReLU()])
            prev = h
        layers.append(nn.Linear(prev, output_dim))
        self.net = nn.Sequential(*layers).to(self.device)

        # Normalization stats (fit during training)
        self._input_mean: Optional[torch.Tensor] = None
        self._input_std: Optional[torch.Tensor] = None

        logger.info(
            f"PINNPetrophysics initialized: {input_dim}→{hidden_dims}→{output_dim} "
            f"on {self.device} | Archie(a={archie_a}, m={archie_m}, n={archie_n})"
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _normalize(self, x: torch.Tensor) -> torch.Tensor:
        if self._input_mean is None or self._input_std is None:
            return x
        std = self._input_std.clamp(min=1e-8)
        return (x - self._input_mean) / std

    def _fit_normalizer(self, x: torch.Tensor) -> None:
        self._input_mean = x.mean(dim=0, keepdim=True)
        self._input_std = x.std(dim=0, keepdim=True)

    def _parse_inputs(self, inputs: np.ndarray | torch.Tensor) -> torch.Tensor:
        if isinstance(inputs, np.ndarray):
            inputs = torch.from_numpy(inputs).float()
        return inputs.to(self.device)

    def _parse_targets(self, targets: np.ndarray | torch.Tensor) -> torch.Tensor:
        if isinstance(targets, np.ndarray):
            targets = torch.from_numpy(targets).float()
        return targets.to(self.device)

    # ── Forward pass ──────────────────────────────────────────────────────────

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Raw network output — no bounds applied."""
        x = self._normalize(x)
        return self.net(x)

    # ── Physics loss ──────────────────────────────────────────────────────────

    def physics_loss(
        self,
        pred: torch.Tensor,
        inputs: torch.Tensor,
    ) -> torch.Tensor:
        """
        Enforce CANON-9 physics constraints as differentiable loss terms.

        Args:
            pred: Network output (N, 3) — [Vsh, φ, Sw]
            inputs: Well log curves (N, 5+) — must contain RT at index 3
        """
        vsh = pred[:, 0]
        phi = pred[:, 1]
        sw = pred[:, 2]

        # Hard bounds via ReLU penalties
        bound_loss = (
            F.relu(-vsh).mean() + F.relu(vsh - self.vsh_max).mean()
            + F.relu(-phi).mean() + F.relu(phi - self.phi_max).mean()
            + F.relu(-sw).mean() + F.relu(sw - self.sw_max).mean()
        )

        # Archie consistency loss
        # Sw_archie = (a·Rw / (Rt · φ^m))^(1/n)
        # inputs[:, 3] = RT (deep resistivity)
        if inputs.shape[1] > 3:
            rt = inputs[:, 3].clamp(min=1e-8)
            phi_clamped = phi.clamp(min=1e-8)
            sw_archie = (
                (self.archie_a * self.rw)
                / (rt * phi_clamped ** self.archie_m)
            ) ** (1.0 / self.archie_n)
            sw_archie = sw_archie.clamp(0, self.sw_max)
            archie_loss = F.mse_loss(sw, sw_archie)
        else:
            archie_loss = torch.tensor(0.0, device=self.device)

        # Density-neutron crossplot consistency (optional)
        # ρ_log ≈ ρ_ma(1-φ) + ρ_fl·φ
        # inputs[:, 1] = RHOB
        if inputs.shape[1] > 1:
            rhob = inputs[:, 1]
            rhob_pred = self.matrix_density * (1.0 - phi) + self.fluid_density * phi
            density_loss = F.mse_loss(rhob, rhob_pred)
        else:
            density_loss = torch.tensor(0.0, device=self.device)

        total = (
            self.lambda_phys * bound_loss
            + self.lambda_archie * archie_loss
            + self.lambda_density * density_loss
        )
        return total

    def total_loss(
        self,
        pred: torch.Tensor,
        targets: torch.Tensor,
        inputs: torch.Tensor,
    ) -> torch.Tensor:
        """Data loss + physics loss."""
        data_loss = F.mse_loss(pred, targets)
        phys_loss = self.physics_loss(pred, inputs)
        return data_loss + phys_loss

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(
        self,
        inputs: np.ndarray | torch.Tensor,
        targets: np.ndarray | torch.Tensor,
        epochs: int = 1000,
        lr: float = 1e-3,
        log_interval: int = 100,
    ) -> dict[str, list[float]]:
        """
        Train the PINN on (inputs, targets) pairs.

        Args:
            inputs: Well log curves (N, input_dim) — numpy or tensor
            targets: Petrophysical properties (N, 3) — [Vsh, φ, Sw]
            epochs: Training iterations
            lr: Adam learning rate
            log_interval: How often to log loss

        Returns:
            History dict with 'data_loss', 'phys_loss', 'total_loss' lists.
        """
        x = self._parse_inputs(inputs)
        y = self._parse_targets(targets)

        self._fit_normalizer(x)
        x = self._normalize(x)

        optimizer = torch.optim.Adam(self.net.parameters(), lr=lr)
        history: dict[str, list[float]] = {
            "data_loss": [],
            "phys_loss": [],
            "total_loss": [],
        }

        self.net.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            pred = self.net(x)
            loss = self.total_loss(pred, y, x)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                dl = F.mse_loss(pred, y).item()
                pl = self.physics_loss(pred, x).item()
                tl = loss.item()

            history["data_loss"].append(dl)
            history["phys_loss"].append(pl)
            history["total_loss"].append(tl)

            if log_interval > 0 and (epoch + 1) % log_interval == 0:
                logger.info(
                    f"PINN epoch {epoch + 1}/{epochs} | "
                    f"data={dl:.6f} phys={pl:.6f} total={tl:.6f}"
                )

        logger.info(f"PINN training complete. Final total_loss={tl:.6f}")
        return history

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(
        self,
        inputs: np.ndarray | torch.Tensor,
        *,
        violation_threshold: float = 1e-3,
    ) -> dict[str, Any]:
        """
        Run inference with CANON-9 physics violation detection.

        Args:
            inputs: Well log curves (N, input_dim)
            violation_threshold: Physics loss above this → violation=True

        Returns:
            dict with:
                - vsh, phi, sw: np.ndarray (N,)
                - physics_violation: bool
                - violation_details: dict
                - confidence: str (high / moderate / low)
        """
        x = self._parse_inputs(inputs)
        self.net.eval()
        with torch.no_grad():
            xn = self._normalize(x)
            pred = self.net(xn)
            phys_loss_val = self.physics_loss(pred, xn).item()

        vsh = pred[:, 0].cpu().numpy()
        phi = pred[:, 1].cpu().numpy()
        sw = pred[:, 2].cpu().numpy()

        # Detect violations
        violation = phys_loss_val > violation_threshold
        details: dict[str, Any] = {
            "physics_loss": phys_loss_val,
            "threshold": violation_threshold,
            "bounds_checked": {
                "vsh_out_of_range": bool(
                    np.any((vsh < 0) | (vsh > self.vsh_max))
                ),
                "phi_out_of_range": bool(
                    np.any((phi < 0) | (phi > self.phi_max))
                ),
                "sw_out_of_range": bool(
                    np.any((sw < 0) | (sw > self.sw_max))
                ),
            },
        }

        if violation:
            logger.warning(
                f"PINN physics violation detected (loss={phys_loss_val:.6f} > {violation_threshold}). "
                f"Details: {details['bounds_checked']}"
            )
            confidence = "low"
        elif phys_loss_val > violation_threshold * 0.1:
            confidence = "moderate"
        else:
            confidence = "high"

        return {
            "vsh": vsh,
            "phi": phi,
            "sw": sw,
            "physics_violation": violation,
            "violation_details": details,
            "confidence": confidence,
            "canon9_profile": {
                "rw": self.rw,
                "archie_a": self.archie_a,
                "archie_m": self.archie_m,
                "archie_n": self.archie_n,
                "phi_max": self.phi_max,
            },
        }

    # ── State persistence ─────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Save model weights + normalizer stats."""
        state = {
            "net": self.net.state_dict(),
            "input_mean": self._input_mean.cpu().numpy() if self._input_mean is not None else None,
            "input_std": self._input_std.cpu().numpy() if self._input_std is not None else None,
            "config": {
                "input_dim": self.input_dim,
                "hidden_dims": self.hidden_dims,
                "output_dim": self.output_dim,
                "rw": self.rw,
                "archie_a": self.archie_a,
                "archie_m": self.archie_m,
                "archie_n": self.archie_n,
                "phi_max": self.phi_max,
            },
        }
        torch.save(state, path)
        logger.info(f"PINN state saved to {path}")

    @classmethod
    def load(cls, path: str, device: Optional[str] = None) -> "PINNPetrophysics":
        """Load model weights + normalizer stats."""
        state = torch.load(path, map_location=device or "cpu", weights_only=False)
        config = state["config"]
        inst = cls(**config, device=device)
        inst.net.load_state_dict(state["net"])
        if state["input_mean"] is not None:
            inst._input_mean = torch.from_numpy(state["input_mean"]).float().to(inst.device)
        if state["input_std"] is not None:
            inst._input_std = torch.from_numpy(state["input_std"]).float().to(inst.device)
        logger.info(f"PINN state loaded from {path}")
        return inst
