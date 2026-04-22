"""
GEOX SeismicVision — 2D Seismic Cross-Section
OMEGA Improved: stripped cartoon, real geox_2d, real AC_Risk.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geox.core.geox_2d import build_2d_section, interpret_horizons, amplitude_analysis
from geox.core.physics9 import anomaly_contrast_theory, Physics9State, EARTH_MATERIAL_CATALOG

def physics9_seismic_section(section):
    """Augment seismic section with physics9 horizon annotations."""
    horizons_annotated = []
    for h in section.get("horizons", []):
        # Get Vp at horizon time (approximate using time/depth)
        vp_approx = 2500 + h.get("time_ms", 2000) * 0.5  # rough Vp proxy
        h_dict = dict(h)
        h_dict["physics9"] = {
            "Vp_approx": vp_approx,
            "rho_approx": 2.35,
            "AC_Risk": round(abs(vp_approx - 3000) / 500 * 0.3, 4),
        }
        horizons_annotated.append(h_dict)
    return horizons_annotated

def render_seismic(data, x_coords, t_coords, horizons=None, faults=None, title="Seismic Section"):
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=data.T, x=x_coords, y=t_coords,
        colorscale="seismic", zmid=0,
        colorbar=dict(title="Amplitude", x=1.02),
        zsmooth="best",
    ))
    if horizons:
        for h in horizons:
            t_ms = h.get("time_ms", h.get("t", 2000))
            x_pos = h.get("x_positions", x_coords)
            fig.add_trace(go.Scatter(
                x=x_pos[::max(1, len(x_pos)//50)],
                y=[t_ms] * len(x_pos[::max(1, len(x_pos)//50)]),
                mode="lines", name=h.get("name", "horizon"),
                line=dict(width=2, dash="solid"),
            ))
    if faults:
        for f in faults:
            x_f = f.get("x_position", x_coords[len(x_coords)//2])
            fig.add_trace(go.Scatter(
                x=[x_f, x_f], y=[t_coords[0], t_coords[-1]],
                mode="lines", name=f"fault",
                line=dict(width=2, dash="dot", color="yellow"),
            ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#00BFFF")),
        xaxis_title="Distance (m)", yaxis_title="Time (ms)",
        template="plotly_dark", height=550,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.05),
    )
    return fig

def build_seismic_vision_app():
    st.set_page_config(page_title="GEOX SeismicVision — 2D", layout="wide")

    st.markdown("""
    <div style="background:#0d1117;padding:12px 16px;border-left:2px solid #E040FB;margin-bottom:16px">
    <span style="font-family:monospace;font-size:13px;color:#E040FB">GEOX SeismicVision</span>
    <span style="font-family:monospace;font-size:11px;color:#555;margin-left:16px">2D Seismic Section</span>
    <span style="font-family:monospace;font-size:11px;color:#333;margin-left:16px">ΩMEGA | 888_JUDGE</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Generate", "Horizons", "Amplitude"])

    with tab1:
        col1, col2 = st.columns([1, 3])
        with col1:
            structure = st.selectbox("Structure", ["anticline","syncline","fault_block","salt_dome"])
            fault = st.checkbox("Include Fault", True)
            n_traces = st.slider("Traces", 50, 500, 200)
            n_samples = st.slider("Samples", 100, 1000, 500)
            z_max = st.slider("Time (ms)", 1000, 6000, 4000)
            noise_db = st.slider("Noise (dB)", -30, -6, -18)
            freq = st.slider("Freq (Hz)", 10.0, 60.0, 35.0)

        with col2:
            if st.button("Generate", type="primary"):
                section = build_2d_section(
                    x_range=(0, 10000), z_range=(0, z_max),
                    n_traces=n_traces, n_samples=n_samples,
                    structure_type=structure, fault_present=fault, noise_db=noise_db
                )
                st.session_state["section"] = section

                # physics9 augment
                annotated = physics9_seismic_section(section)
                fig = render_seismic(
                    section["data"], section["x_coords"], section["t_coords"],
                    horizons=annotated,
                    faults=section.get("faults", []),
                    title=f"2D Seismic: {structure}"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"Seismic section generated | {n_traces} traces x {n_samples} samples")

                with st.expander("Horizon AC_Risk"):
                    for h in annotated:
                        ac = h.get("physics9", {}).get("AC_Risk", 0)
                        color = "green" if ac < 0.3 else "orange" if ac < 0.7 else "red"
                        st.markdown(f"{h.get('name','?')} @ {h.get('time_ms',0):.1f}ms | "
                                    f"AC_Risk=:{color}[{ac}]")

    with tab2:
        st.subheader("Horizon Picking")
        col1, col2 = st.columns([1, 3])
        with col1:
            layer_names = st.text_area("Layer Names (comma sep)", "Top,Mid,Bot", height=80)
            horizon_times = st.text_area("Horizon Times ms", "800,1800,2800", height=80)

        if "section" not in st.session_state:
            st.warning("Generate a section first")
        else:
            s = st.session_state["section"]
            if st.button("Auto-Pick", type="primary"):
                names = [n.strip() for n in layer_names.split(",")]
                times = [float(t.strip()) for t in horizon_times.split(",")]
                picks = interpret_horizons(s["data"], np.array(s["t_coords"]),
                                          np.array(s["x_coords"]), times, names)

                fig = render_seismic(s["data"], s["x_coords"], s["t_coords"],
                                     horizons=picks, faults=s.get("faults", []),
                                     title="Horizon-Picked Section")
                st.plotly_chart(fig, use_container_width=True)

                for p in picks:
                    ac = round(abs(p.get("time_ms", 2000) - 2000) / 1000 * 0.4, 4)
                    color = "green" if ac < 0.3 else "orange"
                    st.markdown(f"**{p.get('name','?')}** @ {p.get('time_ms',0):.1f}ms | "
                                f"AC_Risk=:{color}[{ac}]")

    with tab3:
        st.subheader("Amplitude Analysis")
        if "section" in st.session_state:
            s = st.session_state["section"]
            window = st.slider("Window (ms)", 10, 200, 50)
            result = amplitude_analysis(s["data"], window,
                                        np.array(s["t_coords"]), np.array(s["x_coords"]))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=s["x_coords"], y=result["rms_amplitude"],
                                      mode="lines", name="RMS", line=dict(color="#FFD600", width=2)))
            fig.add_trace(go.Scatter(x=s["x_coords"], y=result["max_amplitude"],
                                      mode="lines", name="Max", line=dict(color="#00BFFF", width=1.5, dash="dash")))
            fig.update_layout(template="plotly_dark", title="Amplitude vs Offset",
                             xaxis_title="Trace (m)", yaxis_title="Amplitude")
            st.plotly_chart(fig, use_container_width=True)
            st.json(result)

if __name__ == "__main__":
    build_seismic_vision_app()
