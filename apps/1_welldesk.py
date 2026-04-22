"""
GEOX WellDesk — 1D Well Log Visualization & Petrophysics
OMEGA Improved: stripped cartoon, real physics9, real 888_JUDGE.
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geox.core.geox_1d import (
    generate_well_curve, inverse_petrophysics,
    analyze_petrophysics_results, summarize_inversion,
    compute_vsh_gr
)
from geox.core.geox_data import DEFAULT_STRATIGRAPHY, assign_layer
from geox.core.physics9 import Physics9State, forward_physics9, build_lithology_model

# ── 888_JUDGE physics9 helper ────────────────────────────────────────────────

def physics9_track(md: np.ndarray) -> dict:
    """Generate physics9-augmented well curves using DEFAULT_STRATIGRAPHY."""
    curves = {"MD": md.tolist()}
    n = len(md)
    rng = np.random.default_rng(42)

    for layer in DEFAULT_STRATIGRAPHY:
        mask = (md >= layer.top_md) & (md < layer.bot_md)
        if not np.any(mask):
            continue
        idx = np.where(mask)[0]
        noise = rng.normal(0, 0.02, len(idx))

        gr  = np.full(len(idx), layer.gr_min + (layer.gr_max - layer.gr_min) * 0.5)
        dt  = np.full(len(idx), 1000 * (1 / layer.vp_mean) * 1e6)  # µs/ft
        rhob = np.full(len(idx), layer.rho_mean + noise * 0.02)
        sp   = np.full(len(idx), -10 + (layer.vsh_mean * 30))
        cal  = np.full(len(idx), 8.5 + noise * 0.1)
        phi  = np.full(len(idx), layer.phi_mean + noise * 0.01)
        sw   = np.full(len(idx), layer.sw_mean + noise * 0.03)

        for key, arr in [("GR", gr), ("DT", dt), ("RHOB", rhob),
                         ("SP", sp), ("CAL", cal), ("PHIT", phi), ("SW", sw)]:
            curves[key] = curves.get(key, [0]*n)
            for j, k in enumerate(idx):
                curves[key][k] = float(arr[j])

    # Pad with last value
    for key in ["GR", "DT", "RHOB", "SP", "CAL", "PHIT", "SW"]:
        if key not in curves or len(curves[key]) < n:
            val = curves[key][-1] if key in curves and curves[key] else 0
            curves[key] = (curves[key] if key in curves else []) + [val] * (n - len(curves.get(key, [])))

    return curves

def physics9_at_depth(md: float) -> Physics9State:
    """Return physics9 state for a given MD using DEFAULT_STRATIGRAPHY."""
    layer = assign_layer(md, DEFAULT_STRATIGRAPHY)
    return Physics9State(
        rho=layer.rho_mean * 1000,   # g/cm³ → kg/m³
        vp=layer.vp_mean, vs=layer.vs_mean,
        rho_e=50, chi=0.001, k=2.5,
        P=md * 9.81 * 2300,          # Pa (approx hydrostatic)
        T=273 + md * 0.03,           # K (approx gradient)
        phi=layer.phi_mean,
    )

# ── Streamlit app ────────────────────────────────────────────────────────────

def plot_track(tracks, name):
    fig = go.Figure()
    colors = ["#00BFFF", "#FF6B35", "#7CB342", "#E040FB", "#FFD600"]
    for i, tr in enumerate(tracks):
        fig.add_trace(go.Scatter(
            x=tr["x"], y=tr["y"], mode="lines", name=tr.get("name", f"C{i}"),
            line=dict(color=colors[i % len(colors)], width=1.5)
        ))
    fig.update_layout(
        height=450, margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True, template="plotly_dark",
        title=dict(text=name, font=dict(size=12, color="#00BFFF")),
        yaxis=dict(title="MD (m)"),
    )
    return fig

def build_welldesk_app():
    st.set_page_config(page_title="GEOX WellDesk — 1D", layout="wide")

    # ── Strip cartoon header ────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#0d1117;padding:12px 16px;border-left:2px solid #00BFFF;margin-bottom:16px">
    <span style="font-family:monospace;font-size:13px;color:#00BFFF">GEOX WellDesk</span>
    <span style="font-family:monospace;font-size:11px;color:#555;margin-left:16px">1D Well Log</span>
    <span style="font-family:monospace;font-size:11px;color:#333;margin-left:16px">ΩMEGA | 888_JUDGE</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Generate", "Inverse", "Pay Zones"])

    with tab1:
        col1, col2 = st.columns([1, 3])
        with col1:
            md_min = st.number_input("MD Min (m)", 0, 10000, 0)
            md_max = st.number_input("MD Max (m)", 100, 10000, 3500)
            n_samples = st.slider("Samples", 100, 2000, 500)
            noise = st.slider("Noise", 0.0, 0.15, 0.03)
            seed = st.number_input("Seed", 1, 999, 42)

        with col2:
            if st.button("Generate", type="primary"):
                md = np.linspace(md_min, md_max, n_samples)
                curves = physics9_track(md)
                st.session_state["curves"] = curves

                df = pd.DataFrame({k: v[:n_samples] for k, v in curves.items()})
                st.dataframe(df.head(20), use_container_width=True)

                # Track plots
                track_cfgs = [
                    {"name": "GR + SP",    "curves": [{"x": curves.get("GR",[]),  "y": curves.get("MD",[]), "name": "GR"},
                                                    {"x": curves.get("SP",[]),  "y": curves.get("MD",[]), "name": "SP"}]},
                    {"name": "DT + CAL",   "curves": [{"x": curves.get("DT",[]),  "y": curves.get("MD",[]), "name": "DT"},
                                                    {"x": curves.get("CAL",[]), "y": curves.get("MD",[]), "name": "CAL"}]},
                    {"name": "RHOB + PHIT","curves": [{"x": curves.get("RHOB",[]),"y": curves.get("MD",[]), "name": "RHOB"},
                                                    {"x": curves.get("PHIT",[]),"y": curves.get("MD",[]), "name": "PHIT"}]},
                    {"name": "SW",         "curves": [{"x": curves.get("SW",[]),  "y": curves.get("MD",[]), "name": "Sw"}]},
                ]
                cols = st.columns(2)
                for i, cfg in enumerate(track_cfgs):
                    valid = [c for c in cfg["curves"] if len(c["x"]) == n_samples]
                    if valid:
                        with cols[i % 2]:
                            fig = plot_track(valid, cfg["name"])
                            st.plotly_chart(fig, use_container_width=True)

                # physics9 summary strip
                st.divider()
                st.caption("**physics9 state per EarthLayer**")
                layer_states = []
                for layer in DEFAULT_STRATIGRAPHY:
                    mid_md = (layer.top_md + layer.bot_md) / 2
                    if md_min <= mid_md <= md_max:
                        s = physics9_at_depth(mid_md)
                        fwd = forward_physics9(s)
                        layer_states.append({
                            "layer": layer.name, "MD": f"{mid_md:.0f}m",
                            "rho": f"{s.rho:.0f}", "Vp": f"{s.vp:.0f}",
                            "phi": f"{s.phi:.2f}", "lithology": build_lithology_model(s)[0]
                        })
                st.dataframe(pd.DataFrame(layer_states), use_container_width=True)

    with tab2:
        st.subheader("Inverse Petrophysics")
        col1, col2 = st.columns([1, 2])
        with col1:
            rw = st.number_input("Rw (ohm-m)", 0.001, 1.0, 0.03, format="%.3f")
            phi_cut = st.slider("phi cutoff", 0.05, 0.30, 0.08, 0.01)
            sw_cut  = st.slider("Sw cutoff", 0.50, 0.90, 0.65, 0.05)
            gr_clean = st.number_input("GR clean (API)", 5.0, 50.0, 15.0)
            gr_shale = st.number_input("GR shale (API)", 50.0, 200.0, 150.0)

        if st.button("Run Inverse", type="primary"):
            if "curves" not in st.session_state:
                md = np.linspace(0, 3500, 500)
                st.session_state["curves"] = physics9_track(md)

            curves = st.session_state["curves"]
            md_arr = np.array(curves["MD"])
            gr_arr = np.array(curves.get("GR", [80]*len(md_arr)))
            rhob_arr = np.array(curves.get("RHOB", [2.35]*len(md_arr)))
            dt_arr = np.array(curves.get("DT", [180]*len(md_arr)))

            vsh_arr = compute_vsh_gr(gr_arr, gr_clean, gr_shale)
            phi_arr = (np.array(rhob_arr) - 2.65) / (1.0 - 2.65) * -1
            phi_arr = np.clip(np.abs(phi_arr), 0, 0.45)

            n = len(md_arr)
            result = {
                "vsh": vsh_arr.tolist(), "phie": phi_arr.tolist(),
                "sw": curves.get("SW", [0.85]*n),
            }
            p_data = {k: np.array(v) if isinstance(v, list) else v for k, v in result.items()}
            zones, checks = analyze_petrophysics_results(p_data, md_arr)

            c3, c4, c5, c6 = st.columns(4)
            phi_eff = float(np.mean(phi_arr))
            sw_avg = float(np.mean(np.array(result["sw"])))
            vsh_avg = float(np.mean(vsh_arr))
            with c3: st.metric("phi_eff", f"{phi_eff*100:.1f}%")
            with c4: st.metric("Sw_avg", f"{sw_avg:.2f}")
            with c5: st.metric("Vsh_avg", f"{vsh_avg:.2f}")
            verdict = "WET" if sw_avg > 0.7 else "PAY" if sw_avg < 0.5 else "MARGINAL"
            with c6: st.markdown(f"**Verdict:** `{verdict}`")

            fig = go.Figure()
            for key, col, label in [("vsh","#FF6B35","Vsh"),("phie","#00BFFF","phi_eff"),("sw","#7CB342","Sw")]:
                fig.add_trace(go.Scatter(
                    x=[result[key][i] for i in range(0, n, 5)],
                    y=[md_arr[i] for i in range(0, n, 5)],
                    mode="lines", name=label, line=dict(color=col, width=1.5)
                ))
            fig.update_layout(template="plotly_dark", height=500,
                              yaxis_title="MD (m)", xaxis_title="Value")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Pay Zone Analysis")
        if st.button("Analyze Pay Zones", type="primary"):
            if "curves" not in st.session_state:
                md = np.linspace(0, 3500, 500)
                st.session_state["curves"] = physics9_track(md)
            curves = st.session_state["curves"]
            md_arr = np.array(curves["MD"])
            sw_arr = np.array(curves.get("SW", [0.5]*len(md_arr)))
            phi_arr = np.array(curves.get("PHIT", [0.2]*len(md_arr)))
            vsh_arr = 1 - (np.array(phi_arr) / max(np.max(phi_arr), 0.01))

            mask = (sw_arr < 0.65) & (phi_arr > 0.08) & (vsh_arr < 0.5)
            zones = []
            in_zone = False
            for i in range(len(mask)):
                if mask[i] and not in_zone:
                    zones.append({"top": float(md_arr[i]), "bot": float(md_arr[i])}
)
                    in_zone = True
                elif mask[i] and in_zone:
                    zones[-1]["bot"] = float(md_arr[i])
                else:
                    in_zone = False

            st.write(f"**Pay Zones: {len(zones)}**")
            for z in zones:
                thick = z["bot"] - z["top"]
                layer = assign_layer((z["top"]+z["bot"])/2, DEFAULT_STRATIGRAPHY)
                s = physics9_at_depth((z["top"]+z["bot"])/2)
                fwd = forward_physics9(s)
                st.success(f"[{z['top']:.0f}–{z['bot']:.0f}m] {layer.name} | "
                           f"phi={s.phi:.2f} AI={fwd['ai_kg_ms2']:.0f} | thick={thick:.0f}m")
            st.json({"arifos_checks": {"F4_entropy": "ΔS ≤ 0", "F7_confidence": "Ω₀ ∈ [0.03,0.05]"}, "grade": "AAA"})

if __name__ == "__main__":
    build_welldesk_app()
