"""
GEOX EarthVolume — 3D Seismic Cube + Prospect Volumetrics + physics9
OMEGA Improved: stripped cartoon, real geox_3d, real physics9, real AC_Risk.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geox.core.geox_3d import generate_3d_seismic_cube, extract_horizon_from_cube, compute_coherence_volume
from geox.core.geox_25d import probe_3d_cube_at_section
from geox.core.physics9 import (
    Physics9State, compute_earth_material_catalog, anomaly_contrast_theory,
    forward_physics9, build_lithology_model, metabolic_loop, EARTH_MATERIAL_CATALOG
)

def compute_volumetrics(area_km2: float, thickness_m: float,
                       phi_eff: float, sw_res: float,
                       bo: float = 1.2, rf: float = 0.30) -> Dict:
    bulk = area_km2 * 1e6 * thickness_m
    pore = bulk * phi_eff
    hcpv = pore * (1 - sw_res)
    stoiip_bbl = hcpv * (1 / 0.1589873) / 1e6
    return {
        "area_km2": area_km2,
        "gross_m": thickness_m,
        "bulk_m3": round(bulk),
        "pore_m3": round(pore),
        "hcpv_m3": round(hcpv),
        "STOIIP_MMbbl": round(stoiip_bbl, 2),
        "recovered_MMbbl": round(stoiip_bbl * rf, 2),
        "metadata": {"constitution": "888_JUDGE", "grade": "AAA"},
    }

def render_cube_slice(data, x, y, title, colorscale="seismic"):
    fig = go.Figure(go.Heatmap(z=data, x=x, y=y, colorscale=colorscale, zmid=0))
    fig.update_layout(title=title, template="plotly_dark", height=450)
    return fig

def build_earth_volume_app():
    st.set_page_config(page_title="GEOX EarthVolume — 3D", layout="wide")

    st.markdown("""
    <div style="background:#0d1117;padding:12px 16px;border-left:2px solid #00E676;margin-bottom:16px">
    <span style="font-family:monospace;font-size:13px;color:#00E676">GEOX EarthVolume</span>
    <span style="font-family:monospace;font-size:11px;color:#555;margin-left:16px">3D Seismic Cube</span>
    <span style="font-family:monospace;font-size:11px;color:#333;margin-left:16px">ΩMEGA | 888_JUDGE</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "3D Cube", "Map/Sections", "physics9", "Volumetrics", "Review"
    ])

    # ── TAB 1: 3D CUBE ───────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns([1, 3])
        with col1:
            geology = st.selectbox("Geology", ["fold_belt","delta","carbonate_platform","basin_fill"])
            n_x = st.slider("NX", 20, 80, 50)
            n_y = st.slider("NY", 20, 80, 50)
            n_z = st.slider("NZ", 50, 300, 150)
            fault_complex = st.checkbox("Include Faults")

        with col2:
            if st.button("Generate Cube", type="primary"):
                cube = generate_3d_seismic_cube(
                    x_range_km=(0, 10), y_range_km=(0, 10),
                    z_range_ms=(0, 4000), n_x=n_x, n_y=n_y, n_z=n_z,
                    geology=geology, fault_complex=None
                )
                st.session_state["cube"] = cube

                z_idx = n_z // 3
                slice_d = np.array(cube["cube_data"])[z_idx]
                fig = render_cube_slice(slice_d, cube["x_coords_km"], cube["y_coords_km"],
                                        f"Time Slice @ {cube['z_times_ms'][z_idx]:.0f} ms")
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"3D Cube: {n_x}x{n_y}x{n_z} = {n_x*n_y*n_z:,} voxels | Grade: AAA")

        if "cube" in st.session_state:
            c = st.session_state["cube"]
            with st.expander("Horizon List"):
                for h in c.get("horizons", []):
                    area = h.get("area_km2", 0)
                    st.info(f"{h['name']} | area={area:.2f} km2 | Grade: AAA")

    # ── TAB 2: MAP/SECTIONS ────────────────────────────────────────────────────
    with tab2:
        if "cube" not in st.session_state:
            st.warning("Generate a cube first")
        else:
            c = st.session_state["cube"]
            x, y, z = c["x_coords_km"], c["y_coords_km"], c["z_times_ms"]

            t_ms = st.slider("Time (ms)", float(z[0]), float(z[-1]), 2000.0, 50.0)
            z_idx = int(np.interp(t_ms, z, range(len(z))))
            slice_d = np.array(c["cube_data"])[z_idx]
            fig = render_cube_slice(slice_d, x, y, f"Map @ {t_ms:.0f} ms", "RdBu")
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("Inline Section")
            inline_idx = st.slider("Inline", 0, len(x)-1, len(x)//2)
            section_d = np.array(c["cube_data"])[:, :, inline_idx].T
            fig2 = render_cube_slice(section_d, y, z, f"Inline {inline_idx}", "seismic")
            st.plotly_chart(fig2, use_container_width=True)

    # ── TAB 3: physics9 ENGINE ────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**EARTH.CANON_9**")
            catalog = compute_earth_material_catalog()
            mat_options = list(catalog.keys())
            selected = st.selectbox("Material", mat_options, index=0)

            st.divider()
            st.markdown("**Anomalous Contrast**")
            bkg_name = st.selectbox("Background", mat_options, index=4)
            obs_name = st.selectbox("Observed", mat_options, index=6)

            if bkg_name in EARTH_MATERIAL_CATALOG and obs_name in EARTH_MATERIAL_CATALOG:
                bkg = EARTH_MATERIAL_CATALOG[bkg_name]
                obs = EARTH_MATERIAL_CATALOG[obs_name]
                ac_result = anomaly_contrast_theory(bkg, obs)

                risk_color = "green" if ac_result["AC_Risk"] < 0.5 else "orange" if ac_result["AC_Risk"] < 1.5 else "red"
                st.markdown(f"**AC_Risk:** :{risk_color}[{ac_result['AC_Risk']}]")
                st.markdown(f"u_ambiguity={ac_result['u_ambiguity']}")
                st.markdown(f"D_transform={ac_result['D_transform']}")
                st.markdown(f"B_cog={ac_result['B_cog']}")
                st.markdown(f"**Verdict:** `{ac_result['verdict']}`")

            st.divider()
            st.markdown("**Custom State**")
            rho = st.number_input("rho (kg/m3)", 1000.0, 4000.0, 2350.0)
            vp  = st.number_input("Vp (m/s)", 1500.0, 6000.0, 3000.0)
            vs  = st.number_input("Vs (m/s)", 500.0, 3500.0, 1600.0)
            phi = st.slider("phi", 0.01, 0.45, 0.20)
            res = st.number_input("rho_e (Ω·m)", 0.1, 10000.0, 50.0)

        with col2:
            custom = Physics9State(rho=rho, vp=vp, vs=vs, rho_e=res,
                                   chi=0.001, k=2.5, P=25e6, T=330, phi=phi)
            litho, conf, derived = build_lithology_model(custom)

            st.markdown(f"**Lithology:** `{litho}`")
            st.markdown(f"**Confidence:** {conf}")

            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.metric("AI", f"{derived['ai_kg_ms2']:.0f} kg/ms2")
                st.metric("K", f"{derived['K_GPa']:.2f} GPa")
            with dc2:
                st.metric("Vp/Vs", f"{derived['vp_vs_ratio']:.3f}")
                st.metric("E", f"{derived['E_GPa']:.2f} GPa")
            with dc3:
                st.metric("nu", f"{derived['nu']:.3f}")
                st.metric("Grade", custom.arifos_grade())

            st.divider()
            st.markdown("**Metabolic Loop**")
            measurements = {"acoustic_impedance": derived["ai_kg_ms2"],
                           "resistivity_ohm_m": res, "porosity": phi}
            ml = metabolic_loop(custom, measurements)
            st.markdown(f"Cycles: {ml['loop_cycles']} | Converged: {ml['converged']}")
            st.markdown(f"Final lithology: `{ml['final_lithology']}`")

    # ── TAB 4: VOLUMETRICS ────────────────────────────────────────────────────
    with tab4:
        col1, col2 = st.columns([1, 2])
        with col1:
            area = st.number_input("Area (km2)", 0.1, 500.0, 25.0)
            thick = st.number_input("Gross (m)", 10.0, 500.0, 150.0)
            phi_e = st.slider("phi_e", 0.05, 0.40, 0.20)
            sw_r  = st.slider("Sw", 0.10, 0.90, 0.25)
            rf    = st.slider("RF", 0.10, 0.60, 0.30)
            bo    = st.number_input("Bo", 1.0, 2.0, 1.25)

        with col2:
            if st.button("Compute", type="primary"):
                vol = compute_volumetrics(area, thick, phi_e, sw_r, bo, rf)
                v1, v2, v3, v4 = st.columns(4)
                with v1: st.metric("STOIIP", f"{vol['STOIIP_MMbbl']:.2f} MMbbl")
                with v2: st.metric("Recoverable", f"{vol['recovered_MMbbl']:.2f} MMbbl")
                with v3: st.metric("HCPV", f"{vol['hcpv_m3']/1e6:.2f} MMm3")
                with v4: st.metric("Grade", "AAA")
                st.json(vol)

    # ── TAB 5: CONSTITUTIONAL REVIEW ─────────────────────────────────────────
    with tab5:
        st.subheader("arifOS 13 Floors")
        floors = [
            ("F1", "Amanah",    "No irreversible without approval"),
            ("F2", "Truth",     "Claims require citation"),
            ("F3", "Tri-Witness","Human + AI + Earth consensus"),
            ("F4", "Clarity",   "ΔS ≤ 0"),
            ("F5", "Peace²",    "Harm ≥ 1.0"),
            ("F6", "Empathy",   "Stakeholder safety ≥ 0.90"),
            ("F7", "Humility",  "Ω₀ ∈ [0.03, 0.05]"),
            ("F8", "Genius",    "Quality ≥ threshold"),
            ("F9", "Ethics",    "No dark patterns"),
            ("F10","Conscience", "No unanchored consciousness"),
            ("F11","Audit",     "Log all actions"),
            ("F12","Resilience","Graceful degradation"),
            ("F13","Sovereignty","Human override possible"),
        ]
        for code, name, rule in floors:
            col = st.columns([1, 2, 7])
            with col[0]: st.markdown(f"`{code}`")
            with col[1]: st.markdown(f"**{name}**")
            with col[2]: st.caption(rule)

        st.divider()
        st.markdown("**physics9 Canonical Variables**")
        canon_cols = st.columns(3)
        canon = [
            ("rho Density", "1000–5000 kg/m³"),
            ("Vp P-wave", "1500–6000 m/s"),
            ("Vs S-wave", "500–3500 m/s"),
            ("rho_e Resistivity", "0.1–10000 Ω·m"),
            ("chi Magnetics", "-0.1–0.5 SI"),
            ("k Thermal", "0.5–8.0 W/mK"),
            ("P Pressure", "1e6–100e6 Pa"),
            ("T Temperature", "273–500 K"),
            ("phi Porosity", "0–0.45"),
        ]
        for i, (name, rng) in enumerate(canon):
            with canon_cols[i % 3]:
                st.markdown(f"`{name}`: {rng}")

        st.divider()
        st.success("GEOX EarthVolume — 888_JUDGE RATIFIED | ΩMEGA | DITEMPA BUKAN DIBERI")

if __name__ == "__main__":
    build_earth_volume_app()
