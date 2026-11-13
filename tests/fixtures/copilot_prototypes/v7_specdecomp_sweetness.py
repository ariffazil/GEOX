"""
Copilot prototype v7 — v6 + spectral decomposition RGB blend + sweetness.

Original Copilot output: ROTAN1_specdecomp_RGB_proxy.png + ROTAN1_sweetness_proxy.png + ROTAN1_final_interpretation_v7.png

Algorithm:
  PNG → red-minus-blue color difference as amplitude proxy
  STFT along vertical axis (8.27 ms/pixel sampling, Nyquist ~60 Hz)
  Bandpass at 10, 20, 30 Hz (Gaussian bandpass, 25% fractional bandwidth)
  Sweetness = envelope / sqrt(instantaneous_frequency)
  RGB blend: R = 30 Hz band, G = 20 Hz band, B = 10 Hz band
  Final interpretation: v6 + sweetness overlay + frequency panel

Key finding: IVC at D2 crest has HIGHEST sweetness (0.082) + broadband
brightness → consistent with gas-charged Rotan Sands.
No low-frequency shadow above D2 crest → gas chimney NOT supported.

This is the workflow that `geox_seismic_display_spectral_character.v1`
formalizes. PUBLIC SYNTHETIC ONLY.

The Copilot code uses `/mnt/user-data/uploads/image.png` — that path is
not available in this fixture (per sovereign "public synthetic only" policy).
The code below uses a synthetic PNG generated in-place.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image
from scipy.signal import hilbert
from scipy.ndimage import gaussian_filter


def synth_seismic_png(
    width: int = 600, height: int = 400, seed: int = 17
) -> Image.Image:
    """Synthetic seismic-like PNG with stratified color patterns.

    Mimics the visual character of a real seismic section (banding,
    chaotic zones vs layered zones) using only color, not real amplitudes.
    """
    rng = np.random.RandomState(seed)
    img = Image.new("RGB", (width, height), (240, 240, 230))
    pix = np.asarray(img).copy()
    for y in range(height):
        for x in range(width):
            # Banded background (simulating reflectors)
            band_freq = 0.05
            layered_signal = 128 + int(40 * np.sin(y * band_freq))
            # Chaotic zones (in selected regions)
            if 200 < x < 350 and 250 < y < 380:
                noise = int(rng.randint(-60, 60))
            elif 400 < x < 500 and 200 < y < 350:
                noise = int(rng.randint(-50, 50))
            else:
                noise = int(rng.randint(-15, 15))
            pix[y, x] = [np.clip(layered_signal + noise, 0, 255)] * 3
    return Image.fromarray(pix)


def v7_spectral(
    png_image: Image.Image,
    dt_seconds: float = 8.27e-3,
    target_bands_hz: tuple = (10, 20, 30),
) -> dict:
    """v7 algorithm: PNG → amplitude proxy → STFT → bands → sweetness.

    Returns: dict with ordinal zone table + band summary (NO raw arrays).
    """
    rgb = np.asarray(png_image.convert("RGB"), dtype=float)
    height, width = rgb.shape[:2]
    # Amplitude proxy: red-minus-blue channel difference (Copilot convention)
    amp = (rgb[..., 0] - rgb[..., 2]) / 255.0

    # Nyquist
    nyquist = 1.0 / (2.0 * dt_seconds)

    # STFT along vertical axis (per column)
    freqs = np.fft.rfftfreq(height, dt_seconds)
    spec = np.fft.rfft(amp, axis=0)

    bands = {}
    for fc in target_bands_hz:
        if fc >= nyquist:
            continue
        bw = fc * 0.35  # 25% fractional bandwidth
        gauss = np.exp(-0.5 * ((freqs - fc) / bw) ** 2)[:, None]
        filtered = np.fft.irfft(spec * gauss, n=height, axis=0)
        env = np.abs(hilbert(filtered, axis=0))
        bands[fc] = gaussian_filter(env, (2, 3))

    # Instantaneous frequency (broadband)
    bb = np.fft.irfft(
        spec * ((freqs > 5) & (freqs < 45)).astype(float)[:, None],
        n=height, axis=0,
    )
    analytic = hilbert(bb, axis=0)
    phase = np.unwrap(np.angle(analytic), axis=0)
    ifreq = np.gradient(phase, axis=0) / (2.0 * np.pi * dt_seconds)
    ifreq = gaussian_filter(ifreq, (6, 4))
    ifreq = np.clip(ifreq, 3, 50)

    # Sweetness
    env_bb = np.abs(analytic)
    sweet = gaussian_filter(env_bb, (3, 3)) / np.sqrt(np.maximum(ifreq, 1e-4))

    # ORDINAL ZONE TABLE — canonical output per display_spectral_character.v1 spec
    # Pre-defined zones (matches Copilot's v7 manual analysis)
    zones = {
        "Foreland layered": (slice(0, 280), slice(50, 300)),
        "NSPW wedge":       (slice(280, 700), slice(350, 700)),
        "D2 core":          (slice(200, 380), slice(800, 1000)),
        "D3 core":          (slice(280, 600), slice(1200, 1400)),
        "MB-B fill":        (slice(50, 200), slice(700, 1100)),
        "IVC ROTAN crest":  (slice(50, 200), slice(800, 1000)),
        "IVC SE of D3":     (slice(150, 250), slice(1100, 1400)),
    }
    zone_table = []
    for zone_name, (y_slice, x_slice) in zones.items():
        # Compute median band values in this zone
        band_medians = {
            f"{fc}hz": float(np.median(bands[fc][y_slice, x_slice]))
            for fc in bands
        }
        sweet_med = float(np.median(sweet[y_slice, x_slice]))
        # ORDINAL ranking only (no absolute Hz returned)
        # Rank within image: compare to all other zones
        all_sweets = [
            float(np.median(sweet[zs, xs]))
            for zs, xs in zones.values()
        ]
        rank_pct = sum(s <= sweet_med for s in all_sweets) / len(all_sweets)
        if rank_pct >= 0.8:
            ordinal = "highest"
        elif rank_pct >= 0.6:
            ordinal = "high"
        elif rank_pct >= 0.4:
            ordinal = "mid"
        elif rank_pct >= 0.2:
            ordinal = "low"
        else:
            ordinal = "lowest"
        zone_table.append({
            "zone_id": zone_name,
            "ordinal": ordinal,
            "sweetness_rank": round(rank_pct, 3),
            # CRUCIAL: NO absolute Hz values returned
        })

    return {
        "algorithm": "v7_specdecomp_sweetness",
        "calibration": {"dt_seconds": dt_seconds, "nyquist_hz": nyquist},
        "ordinal_zone_table": zone_table,
        "claim_ceiling": "CHARACTER",
        # CRUCIAL: no numpy arrays, no base64 panels, no absolute Hz
    }


if __name__ == "__main__":
    png = synth_seismic_png()
    result = v7_spectral(png)
    for row in result["ordinal_zone_table"]:
        print(row)
    print("\nNO ABSOLUTE HZ IN OUTPUT — ordinal ranking only.")
    print("claim_ceiling:", result["claim_ceiling"])
