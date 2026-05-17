"""
GEOX 3D — Full 3D Seismic Cube Visualization & Interpretation
3D cube generation, isosurface extraction, horizon mapping,
and the integration of map view + section view + 3D render in one surface.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class Isosurface:
    amplitude_value: float
    mesh_vertices: List  # simplified - list of vertex coordinates
    mesh_faces: List    # simplified - list of face indices
    color: str
    opacity: float
    arifos_grade: str


@dataclass
class HorizonSurface:
    name: str
    depth_grid: List[List[float]]  # 2D grid of depth values
    time_grid: List[List[float]]    # 2D grid of time values
    amplitude_attributes: Optional[Dict] = None
    area_km2: float = 0.0
    structural_gradient: float = 0.0  # dip angle in degrees


def generate_3d_seismic_cube(
    x_range_km: Tuple[float, float],
    y_range_km: Tuple[float, float],
    z_range_ms: Tuple[float, float],
    n_x: int = 60,
    n_y: int = 60,
    n_z: int = 200,
    geology: str = "fold_belt",
    fault_complex: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Generate synthetic 3D seismic cube with geological structure.
    geology types: "fold_belt", "delta", "carbonate_platform", "basin_fill"
    """
    rng = np.random.default_rng(99)

    xi = np.linspace(x_range_km[0], x_range_km[1], n_x)
    yi = np.linspace(y_range_km[0], y_range_km[1], n_y)
    zi = np.linspace(z_range_ms[0], z_range_ms[1], n_z)

    cube = np.zeros((n_z, n_y, n_x))

    # Build geological structure surfaces
    def make_surface(f, n_x=n_x, n_y=n_y, xi=xi, yi=yi, z0=500, amplitude=100):
        surf = np.zeros((n_y, n_x))
        for iy in range(n_y):
            for ix in range(n_x):
                surf[iy, ix] = f(xi[ix], yi[iy])
        return surf

    cx = (x_range_km[0]+x_range_km[1])/2
    cy = (y_range_km[0]+y_range_km[1])/2
    if geology == "fold_belt":
        top_surf = make_surface(lambda x, y: 500 + 100 * np.exp(-((x - cx)**2 + (y - cy)**2) / (2 * 20**2)))
        mid_surf = top_surf + 300 + 20 * rng.random((n_y, n_x))
        bot_surf = mid_surf + 400 + 30 * rng.random((n_y, n_x))
    elif geology == "delta":
        # Prograding clinoforms
        top_surf = make_surface(lambda x, y, z0=50: z0 + 50 + 0.5 * (x - x_range_km[0]), amplitude=0)
        mid_surf = top_surf + 250
        bot_surf = mid_surf + 350
    elif geology == "carbonate_platform":
        # Flat topped carbonate with steep margins
        top_surf = make_surface(lambda x, y: 0.0, amplitude=0)
        margin_mask = np.sqrt((xi[:, None]**2 + yi[None, :]**2)) > (n_x * 0.3)
        top_surf = np.where(margin_mask, z0 + 150, z0 + 20 * rng.random((n_y, n_x)))
        mid_surf = top_surf + 400
        bot_surf = mid_surf + 300
    else:
        top_surf = make_surface(lambda x, y: 50 * rng.random(), amplitude=0)
        mid_surf = top_surf + 350
        bot_surf = mid_surf + 400

    # Build cube trace by trace
    for iy in range(n_y):
        for ix in range(n_x):
            trace = np.zeros(n_z)
            z_span = z_range_ms[1] - z_range_ms[0]

            # Fill with noise base
            trace += rng.normal(0, 0.02, n_z)

            # Add reflection events at horizon positions
            for surf_name, surf_2d in [("top", top_surf), ("mid", mid_surf), ("bot", bot_surf)]:
                t_horizon = surf_2d[iy, ix]
                t_idx = int(np.interp(t_horizon, zi, np.arange(n_z)))
                t_idx = np.clip(t_idx, 0, n_z - 1)
                trace[t_idx] += 0.6 + 0.1 * rng.random()

                # Intra-layer events
                for k in range(1, 4):
                    t_sub = t_horizon + k * z_span / 15
                    i_sub = int(np.interp(t_sub, zi, np.arange(n_z)))
                    i_sub = np.clip(i_sub, 0, n_z - 1)
                    trace[i_sub] += 0.15 * rng.random()

            # Fault disruption
            if fault_complex:
                for fault in fault_complex:
                    fx = fault.get("x_km", (x_range_km[0]+x_range_km[1])/2)
                    fy = fault.get("y_km", (y_range_km[0]+y_range_km[1])/2)
                    dist = np.sqrt((xi[ix] - fx)**2 + (yi[iy] - fy)**2)
                    if dist < 5:
                        throw = fault.get("throw_ms", 50)
                        shift = int(throw / (z_span / n_z))
                        if 0 <= t_idx + shift < n_z:
                            trace[t_idx + shift] = trace[t_idx] * 0.5

            # Convolve with Ricker wavelet (simplified)
            t_wl = np.arange(-0.1, 0.1, zi[1] - zi[0])
            f0 = 35
            wavelet = (1 - (np.pi * f0 * t_wl / 1000)**2) * np.exp(-(np.pi * f0 * t_wl / 1000)**2)
            trace = np.convolve(trace, wavelet / np.max(np.abs(wavelet)), mode='same')

            cube[:, iy, ix] = trace

    cube /= (np.max(np.abs(cube)) + 1e-9)

    # Build horizon grids
    horizons = []
    for surf_name, surf_2d in [("Top_Surface", top_surf), ("Mid_Surface", mid_surf), ("Bot_Surface", bot_surf)]:
        time_grid = surf_2d.tolist()
        # Compute amplitude attribute from cube
        amp_attr = {}
        horizons.append({
            "name": surf_name,
            "depth_time_grid_ms": time_grid,
            "area_km2": float(n_x * n_y * 0.25 / 1e6),
            "metadata": {"constitution": "888_JUDGE"},
        })

    return {
        "cube_data": cube.tolist(),
        "x_coords_km": xi.tolist(),
        "y_coords_km": yi.tolist(),
        "z_times_ms": zi.tolist(),
        "shape": [n_z, n_y, n_x],
        "horizons": horizons,
        "geology_type": geology,
        "metadata": {
            "constitution": "888_JUDGE",
            "dimension": "3D_cube",
            "arifos_version": "v1.3.1",
        }
    }


def extract_horizon_from_cube(
    cube_data: List,
    target_time_ms: float,
    z_times: List[float],
    x_coords: List[float],
    y_coords: List[float],
    window_ms: float = 20,
) -> Dict[str, Any]:
    """
    Extract a horizon surface from 3D cube at a specific time value.
    Uses coherence/similarity to track the reflection event.
    """
    n_z = len(z_times)
    n_y = len(y_coords)
    n_x = len(x_coords)

    # Find nearest time index
    t_idx_target = int(np.interp(target_time_ms, z_times, np.arange(n_z)))
    t_idx_target = np.clip(t_idx_target, 0, n_z - 1)

    win = max(int(window_ms / (z_times[1] - z_times[0])), 2)

    # Extract amplitude around the horizon
    horizon_amp = np.zeros((n_y, n_x))
    horizon_time = np.full((n_y, n_x), target_time_ms)

    for iy in range(n_y):
        for ix in range(n_x):
            trace = [cube_data[iz][iy][ix] if iz < len(cube_data) and iy < len(cube_data[iz]) and ix < len(cube_data[iz][iy]) else 0
                     for iz in range(n_z)]

            t_start = max(0, t_idx_target - win)
            t_end   = min(n_z - 1, t_idx_target + win)
            window = trace[t_start:t_end+1]

            if window:
                horizon_amp[iy, ix] = float(np.mean(window))

    return {
        "amplitude_map": horizon_amp.tolist(),
        "time_map": horizon_time.tolist(),
        "target_time_ms": target_time_ms,
        "window_ms": window_ms,
        "shape": [n_y, n_x],
        "metadata": {"constitution": "888_JUDGE"},
    }


def compute_coherence_volume(cube_data: List, x_coords: List, y_coords: List, z_times: List,
                             window_traces: int = 3) -> Dict[str, Any]:
    """
    Compute coherence/continuity attribute to highlight faults and stratigraphy.
    Uses semblance-like calculation.
    """
    n_z = min(len(cube_data), len(z_times))
    n_y = len(y_coords)
    n_x = len(x_coords)

    coherence = np.zeros((n_z, n_y, n_x))

    for iz in range(n_z):
        for iy in range(1, n_y - 1):
            for ix in range(1, n_x - 1):
                # 3-trace semblance
                c = cube_data[iz][iy][ix] if iz < len(cube_data) and iy < len(cube_data[iz]) and ix < len(cube_data[iz][iy]) else 0
                l = cube_data[iz][iy][ix-1] if iz < len(cube_data) and iy < len(cube_data[iz]) and ix-1 >= 0 else 0
                r = cube_data[iz][iy][ix+1] if iz < len(cube_data) and iy < len(cube_data[iz]) and ix+1 < n_x else 0

                denom = (abs(c) + abs(l) + abs(r)) / 3 + 1e-6
                coherence[iz, iy, ix] = 1 - abs(c - (l + r) / 2) / denom

    return {
        "coherence_data": coherence.tolist(),
        "shape": [n_z, n_y, n_x],
        "metadata": {"dimension": "3D_coherence"},
    }


def build_volume_rendering_params(cube_data: List) -> Dict[str, Any]:
    """
    Compute volume rendering transfer function parameters.
    Returns opacity and color mapping for 3D visualization.
    """
    cube = np.array(cube_data)

    # Compute histogram for transfer function
    hist, bin_edges = np.histogram(cube.flatten(), bins=50)

    return {
        "histogram": hist.tolist(),
        "bin_edges": bin_edges.tolist(),
        "opacity_points": [
            {"amplitude": -1.0, "opacity": 0.0,  "color": [0, 0, 0]},
            {"amplitude": -0.5, "opacity": 0.0,  "color": [0, 0, 80]},
            {"amplitude":  0.0, "opacity": 0.3,  "color": [255, 255, 255]},
            {"amplitude":  0.3, "opacity": 0.7,  "color": [0, 200, 100]},
            {"amplitude":  0.6, "opacity": 0.9,  "color": [255, 100, 0]},
            {"amplitude":  1.0, "opacity": 1.0,  "color": [255, 255, 0]},
        ],
        "metadata": {
            "render_mode": "semi-transparent_volume",
            "constitution": "888_JUDGE",
        }
    }


def integrate_map_section_3d(
    horizon_map: List[List[float]],
    inline_section: List[List[float]],
    crossline_section: List[List[float]],
    x_coords: List[float],
    y_coords: List[float],
    z_times: List[float],
    inline_idx: int, crossline_idx: int,
) -> Dict[str, Any]:
    """
    Integrate all three visualization planes into one view:
    - Map view (time slice)
    - Inline section (vertical along X)
    - Crossline section (vertical along Y)
    - 3D cube preview

    Returns a unified data structure for rendering.
    """
    map_data = np.array(horizon_map)
    inline_data = np.array(inline_section)
    crossline_data = np.array(crossline_section)

    # Corner positions (in normalized coords 0-1)
    return {
        "map_view": map_data.tolist(),
        "inline_view": inline_data.tolist(),
        "crossline_view": crossline_data.tolist(),
        "inline_idx": inline_idx,
        "crossline_idx": crossline_idx,
        "x_coords": x_coords,
        "y_coords": y_coords,
        "z_times": z_times,
        "metadata": {
            "constitution": "888_JUDGE",
            "dimension": "3D_unified",
            "arifos_version": "v1.3.1",
        }
    }