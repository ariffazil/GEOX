"""
PINN Layer Tests — CANON-9 Physics Compliance
═══════════════════════════════════════════════════════════════════════════════
Verify:
  1. PINN trains and predicts without crash
  2. Physics loss penalizes out-of-bounds predictions
  3. Archie consistency loss is computed when RT is present
  4. predict() returns physics_violation flag
  5. Save/load round-trip preserves weights

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import pytest
import numpy as np

pytestmark = pytest.mark.skipif(
    not pytest.importorskip("torch", reason="PyTorch not installed"),
    reason="PINN tests require PyTorch",
)

import torch
from geox_core.engines.petrophysics.pinn import PINNPetrophysics, CANON9_DEFAULTS


@pytest.fixture
def synthetic_well_logs():
    """Generate synthetic well log data (GR, RHOB, NPHI, RT, DT)."""
    np.random.seed(42)
    n = 200
    gr = np.random.uniform(20, 150, n)       # API
    rhob = np.random.uniform(2.0, 2.7, n)    # g/cc
    nphi = np.random.uniform(0.0, 0.4, n)    # v/v
    rt = np.random.uniform(0.5, 100.0, n)    # ohm·m
    dt = np.random.uniform(60, 140, n)       # µs/ft
    inputs = np.column_stack([gr, rhob, nphi, rt, dt])

    # Synthetic targets: Vsh, φ, Sw (physically plausible)
    vsh = (gr - 20) / 130.0  # linear GR → Vsh
    vsh = np.clip(vsh, 0.05, 0.95)
    phi = nphi * 0.9  # slightly less than NPHI
    phi = np.clip(phi, 0.02, 0.38)
    # Archie-consistent Sw
    rw = CANON9_DEFAULTS["rw"]
    m = CANON9_DEFAULTS["archie_m"]
    n = CANON9_DEFAULTS["archie_n"]
    sw = ((rw) / (rt * phi ** m)) ** (1.0 / n)
    sw = np.clip(sw, 0.1, 0.95)
    targets = np.column_stack([vsh, phi, sw])

    return inputs.astype(np.float32), targets.astype(np.float32)


def test_pinn_initialization():
    """PINN must initialize with correct architecture."""
    pinn = PINNPetrophysics(input_dim=5, hidden_dims=(64, 32))
    assert pinn.input_dim == 5
    assert pinn.output_dim == 3
    assert len(pinn.net) == 5  # Linear+ReLU, Linear+ReLU, Linear


def test_pinn_forward_shape(synthetic_well_logs):
    """Forward pass must return (N, 3)."""
    inputs, _ = synthetic_well_logs
    pinn = PINNPetrophysics(input_dim=5)
    x = torch.from_numpy(inputs).float()
    out = pinn.forward(x)
    assert out.shape == (inputs.shape[0], 3)


def test_pinn_physics_loss_bounds():
    """Physics loss must be > 0 for out-of-bounds predictions."""
    pinn = PINNPetrophysics(input_dim=5)
    # Create predictions that violate bounds
    pred = torch.tensor([
        [-0.5, 0.5, 1.5],   # Vsh<0, φ>0.40, Sw>1
        [1.5, -0.1, -0.5],  # Vsh>1, φ<0, Sw<0
    ])
    inputs = torch.rand(2, 5) * 100.0
    loss = pinn.physics_loss(pred, inputs)
    assert loss.item() > 0.0


def test_pinn_physics_loss_archie_consistency():
    """Archie loss must be low for physically consistent predictions."""
    pinn = PINNPetrophysics(input_dim=5, rw=0.05, archie_m=2.0, archie_n=2.0)
    # Consistent case: Sw = sqrt(Rw / (Rt * φ^2))
    phi = torch.tensor([[0.20], [0.25]])
    rt = torch.tensor([[10.0], [5.0]])
    sw_archie = ((0.05) / (rt * phi ** 2)) ** 0.5
    pred = torch.cat([torch.ones(2, 1) * 0.3, phi, sw_archie], dim=1)
    inputs = torch.cat([
        torch.ones(2, 1) * 50,   # GR
        torch.ones(2, 1) * 2.35, # RHOB
        phi,                       # NPHI
        rt,                        # RT
        torch.ones(2, 1) * 100,  # DT
    ], dim=1)
    loss = pinn.physics_loss(pred, inputs)
    # Archie loss should be very small (~0)
    assert loss.item() < 0.01


def test_pinn_training_runs(synthetic_well_logs):
    """Training must run without crash and reduce loss."""
    inputs, targets = synthetic_well_logs
    pinn = PINNPetrophysics(input_dim=5, hidden_dims=(32, 16))
    history = pinn.fit(inputs, targets, epochs=50, lr=1e-2, log_interval=0)
    assert len(history["total_loss"]) == 50
    # Loss should generally decrease (not strictly monotonic due to Adam)
    assert history["total_loss"][-1] < history["total_loss"][0]


def test_pinn_predict_structure(synthetic_well_logs):
    """predict() must return correct dict structure."""
    inputs, targets = synthetic_well_logs
    pinn = PINNPetrophysics(input_dim=5, hidden_dims=(32, 16))
    pinn.fit(inputs, targets, epochs=20, lr=1e-2, log_interval=0)
    result = pinn.predict(inputs[:10])

    assert "vsh" in result
    assert "phi" in result
    assert "sw" in result
    assert "physics_violation" in result
    assert "violation_details" in result
    assert "confidence" in result
    assert result["vsh"].shape == (10,)
    assert result["phi"].shape == (10,)
    assert result["sw"].shape == (10,)
    assert isinstance(result["physics_violation"], bool)


def test_pinn_predict_violation_on_untrained():
    """Untrained network should likely produce physics violations."""
    pinn = PINNPetrophysics(input_dim=5)
    inputs = torch.rand(50, 5) * 100.0
    result = pinn.predict(inputs.numpy(), violation_threshold=0.01)
    # Untrained network almost certainly violates physics bounds
    assert result["physics_violation"] is True or result["confidence"] in ("low", "moderate")


def test_pinn_canon9_profile_in_predict(synthetic_well_logs):
    """predict() must include CANON-9 profile metadata."""
    inputs, targets = synthetic_well_logs
    pinn = PINNPetrophysics(input_dim=5, rw=0.03, archie_m=2.1)
    pinn.fit(inputs, targets, epochs=10, lr=1e-2, log_interval=0)
    result = pinn.predict(inputs[:5])
    profile = result["canon9_profile"]
    assert profile["rw"] == 0.03
    assert profile["archie_m"] == 2.1
    assert "phi_max" in profile


def test_pinn_save_load_roundtrip(synthetic_well_logs, tmp_path):
    """Save/load must preserve prediction behavior."""
    inputs, targets = synthetic_well_logs
    pinn1 = PINNPetrophysics(input_dim=5, hidden_dims=(16, 8))
    pinn1.fit(inputs, targets, epochs=20, lr=1e-2, log_interval=0)

    path = tmp_path / "pinn_test.pt"
    pinn1.save(str(path))

    pinn2 = PINNPetrophysics.load(str(path))
    pred1 = pinn1.predict(inputs[:10])
    pred2 = pinn2.predict(inputs[:10])

    np.testing.assert_allclose(pred1["vsh"], pred2["vsh"], rtol=1e-5)
    np.testing.assert_allclose(pred1["phi"], pred2["phi"], rtol=1e-5)
    np.testing.assert_allclose(pred1["sw"], pred2["sw"], rtol=1e-5)


def test_pinn_graceful_no_torch(monkeypatch):
    """If torch is unavailable, initialization must raise RuntimeError."""
    import geox_core.engines.petrophysics.pinn as pinn_module
    monkeypatch.setattr(pinn_module, "_HAS_TORCH", False)
    with pytest.raises(RuntimeError, match="PyTorch"):
        pinn_module.PINNPetrophysics()
