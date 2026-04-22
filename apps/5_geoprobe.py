"""
GEOX GeoProbe — 2.5D Map View + Geoid + Attribute Volume
OMEGA Improved: stripped cartoon, real geox_25d, real physics9.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geox.core.geox_25d import (
    compute_geoid_anomalies, compute_geoid_surface,
    build_attribute_volume, time_to_depth_conversion
)
from geox.core.physics9 import Physics9State, anomaly_contrast_theory, forward_physics9

def plot_map(data, x, y, title, colorscale="viridis"):
    fig = go.Figure(go.Heatmap(z=data, x=x, y=y, colorscale=colorscale, zmid=0))
    fig.update_layout(title=title, template="plotly_dark", height=450)
    return fig

def build_geoprobe_app():
    st.set_page_config(page_title="GEOX GeoProbe — 2.5D", layout="wide")

    st.markdown("""
    <div style="background:#0d1117;padding:12px 16px;border-left:2px solid #9C27B0;margin-bottom:16px">
    <span style="font-family:monospace;font-size:13px;color:#9C27B0">GEOX GeoProbe</span>
    <span style="font-family:monospace;font-size:11px;color:#555;margin-left:16px">2.5D Map + Geoid</span>
    <span style="font-family:monospace;font-size:11px;color:#333;margin-left:16px">ΩMEGA | 888_JUDGE</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Gravity/Mag", "Geoid", "Attribute", "Time-Depth"])

    # ── TAB 1: GRAVITY/MAGNETICS ─────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            area_km = st.slider("Area (km)", 10, 200, 50)
            n_grid  = st.slider("Grid", 30, 120, 80)
            lat_c   = st.number_input("Latitude", -90.0, 90.0, 4.0)
            lon_c   = st.number_input("Longitude", -180.0, 180.0, 110.0)

        with col2:
            if st.button("Compute Gravity/Mag", type="primary"):
                result = compute_geoid_anomalies((area_km, area_km), n_grid, lat_c, lon_c)
                st.session_state["grav"] = result
                st.session_state["x_km"] = result["x_km"]
                st.session_state["y_km"] = result["y_km"]

                t1, t2 = st.tabs(["Gravity Bouguer", "Magnetic TMI"])
                with t1:
                    fig = plot_map(np.array(result["gravity_bouguer_mgal"]),
                                   result["x_km"], result["y_km"],
                                   f"Gravity Bouguer (mGal) — {area_km}km", "RdBu")
                    st.plotly_chart(fig, use_container_width=True)
                with t2:
                    fig = plot_map(np.array(result["magnetic_tmi_nt"]),
                                   result["x_km"], result["y_km"],
                                   f"Magnetic TMI (nT)", "Portland")
                    st.plotly_chart(fig, use_container_width=True)
                st.json(result)

    # ── TAB 2: GEOID SURFACE ──────────────────────────────────────────────────
    with tab2:
        if "grav" not in st.session_state:
            st.warning("Compute gravity/magnetics first")
        else:
            r = st.session_state["grav"]
            geo_type = st.selectbox("Geoid Type", ["undulation", "disturbance"])

            if st.button("Compute Geoid Surface", type="primary"):
                geoid = compute_geoid_surface(r["gravity_bouguer_mgal"],
                                              r["x_km"], r["y_km"], geo_type)
                fig = go.Figure(go.Surface(
                    x=r["x_km"], y=r["y_km"],
                    z=np.array(geoid["geoid_height_m"]),
                    colorscale="Viridis", opacity=0.85,
                ))
                fig.update_layout(
                    title="Geoid Undulation Surface",
                    template="plotly_dark", height=550,
                    scene=dict(xaxis_title="X (km)", yaxis_title="Y (km)", zaxis_title="Geoid (m)")
                )
                st.plotly_chart(fig, use_container_width=True)
                st.json(geoid)

    # ── TAB 3: ATTRIBUTE VOLUME ───────────────────────────────────────────────
    with tab3:
        st.subheader("Attribute Volume")
        if st.button("Generate Proxy Cube", type="primary"):
            n_x, n_y, n_z = 30, 30, 50
            rng = np.random.default_rng(99)
            cube = np.zeros((n_z, n_y, n_x))
            for iz in range(n_z):
                for iy in range(n_y):
                    for ix in range(n_x):
                        for th in [n_z//4, n_z//2, 3*n_z//4]:
                            dist = abs(iz - th)
                            cube[iz, iy, ix] += 0.5 * np.exp(-dist**2 / 5) * rng.normal(0, 1)
                        cube[iz, iy, ix] += rng.normal(0, 0.05)
            st.session_state["attr_cube"] = cube.tolist()
            st.session_state["attr_x"] = np.linspace(0, 10, n_x).tolist()
            st.session_state["attr_y"] = np.linspace(0, 10, n_y).tolist()
            st.session_state["attr_z"] = np.linspace(0, 4000, n_z).tolist()

        if "attr_cube" in st.session_state:
            cube_d = st.session_state["attr_cube"]
            x, y, z = st.session_state["attr_x"], st.session_state["attr_y"], st.session_state["attr_z"]
            attr_type = st.selectbox("Attribute", ["envelope", "phase", "frequency"])

            if st.button(f"Compute {attr_type}", type="primary"):
                result = build_attribute_volume(cube_d, x, y, z, attr_type)
                st.json(result)

                z_mid = len(z) // 2
                attr_slice = np.array(result["attribute_data"])[z_mid]
                fig = plot_map(attr_slice, x, y, f"{attr_type} @ {z[z_mid]:.0f} ms", "hot")
                st.plotly_chart(fig, use_container_width=True)

    # ── TAB 4: TIME-DEPTH ─────────────────────────────────────────────────────
    with tab4:
        st.subheader("Time-to-Depth Conversion")
        col1, col2 = st.columns([1, 2])
        with col1:
            horizon_times_str = st.text_area("Horizon Times (ms, comma sep)",
                                              "500,1000,1500,2000,2500,3000", height=80)
            method = st.selectbox("Method", ["layered", "rms"])

        with col2:
            if st.button("Convert to Depth", type="primary"):
                times = [float(t.strip()) for t in horizon_times_str.split(",")]
                velocity_model = {
                    "interval_vels": [1650, 2400, 3000, 3500, 4000, 4500, 5000]
                }
                depths = time_to_depth_conversion(times, velocity_model, method)

                import pandas as pd
                df = pd.DataFrame({"Time (ms)": times, "Depth (m)": [round(d, 1) for d in depths]})

                fig = go.Figure(go.Scatter(
                    x=times, y=depths, mode="lines+markers",
                    line=dict(color="#9C27B0", width=3),
                    marker=dict(size=8, color="#FFD600"),
                ))
                fig.update_layout(template="plotly_dark", title="Time-Depth Curve",
                                 xaxis_title="Time (ms)", yaxis_title="Depth (m)")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)

                # physics9 velocity model AC_Risk
                st.divider()
                st.caption("**physics9 interval velocity model**")
                for i, (t, d, v) in enumerate(zip(times, depths,
                    [1650,2400,3000,3500,4000,4500,5000][:len(times)])):
                    vp = (d / (t/1000)) if t > 0 else 0
                    state = Physics9State(rho=2250+vp*0.05, vp=vp, vs=vp*0.58,
                                          rho_e=50, chi=0.001, k=2.5,
                                          P=d*9.81*2300, T=273+d*0.03, phi=0.20)
                    fwd = forward_physics9(state)
                    st.markdown(f"t={t:.0f}ms d={d:.0f}m Vp={vp:.0f}m/s AI={fwd['ai_kg_ms2']:.0f}")

if __name__ == "__main__":
    build_geoprobe_app()
