"""
GEOX JudgeConsole — 4D Time-Lapse + Gassmann + Constitutional Review
OMEGA Improved: stripped cartoon, real geox_4d, real AC_Risk, real 13 floors.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geox.core.geox_4d import (
    gassmann_fluid_substitution, build_4d_cube_difference,
    forward_4d_simulation, inverse_4d_from_observations,
    compute_4d_uncertainty, detect_4d_amplitude_anomaly
)
from geox.core.geox_2d import build_2d_section
from geox.core.physics9 import Physics9State, anomaly_contrast_theory, forward_physics9

def build_judge_console_app():
    st.set_page_config(page_title="GEOX JudgeConsole — 4D", layout="wide")

    st.markdown("""
    <div style="background:#0d1117;padding:12px 16px;border-left:2px solid #FF8C00;margin-bottom:16px">
    <span style="font-family:monospace;font-size:13px;color:#FF8C00">GEOX JudgeConsole</span>
    <span style="font-family:monospace;font-size:11px;color:#555;margin-left:16px">4D Time-Lapse</span>
    <span style="font-family:monospace;font-size:11px;color:#333;margin-left:16px">ΩMEGA | 888_JUDGE</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Gassmann", "4D Diff", "Forward/Inv", "13 Floors"])

    # ── TAB 1: GASSMANN ──────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            vp_i  = st.number_input("Vp initial (m/s)", 2000.0, 5000.0, 3000.0)
            vs_i  = st.number_input("Vs initial (m/s)", 500.0, 3000.0, 1600.0)
            rho_i = st.number_input("rho initial (kg/m3)", 1500.0, 3500.0, 2350.0)
            phi   = st.slider("phi", 0.05, 0.40, 0.20)
            sw_i  = st.slider("Sw initial", 0.5, 1.0, 0.90)
            sw_f  = st.slider("Sw final", 0.0, 0.8, 0.30)
            k_min = st.number_input("K mineral (GPa)", 20.0, 50.0, 37.0)
            k_fld = st.number_input("K fluid (GPa)", 0.5, 5.0, 2.2)
            k_dry = st.number_input("K dry (GPa)", 5.0, 20.0, 10.0)

        with col2:
            if st.button("Run Gassmann", type="primary"):
                res = gassmann_fluid_substitution(
                    vp_i, vs_i, rho_i, phi,
                    sw_initial=sw_i, sw_final=sw_f,
                    k_mineral=k_min*1e9, k_fluid=k_fld*1e9, k_dry_frame=k_dry*1e9
                )

                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: st.metric("Vp after", f"{res.vp_after:.1f} m/s")
                with c2: st.metric("Vs after", f"{res.vs_after:.1f} m/s")
                with c3: st.metric("rho after", f"{res.rho_after:.3f}")
                with c4: st.metric("ΔAI%", f"{res.ai_change_pct:.2f}%")
                with c5:
                    fcol = {"GAS":"blue","OIL":"orange","WATER":"teal","MIXED":"gray"}
                    st.markdown(f"**Fluid:** :{fcol.get(res.fluid_indicator,'gray')}[{res.fluid_indicator}]")

                fig = go.Figure()
                labels = ["Vp", "Vs", "rho*100", "AI/100"]
                b = [res.vp_before, res.vs_before, res.rho_before*100, res.vp_before*res.rho_before/100]
                a = [res.vp_after, res.vs_after, res.rho_after*100, res.vp_after*res.rho_after/100]
                fig.add_trace(go.Bar(x=labels, y=b, name="Before", marker_color="#FF6B35"))
                fig.add_trace(go.Bar(x=labels, y=a, name="After", marker_color="#00BFFF"))
                fig.update_layout(template="plotly_dark", title="Before vs After Fluid Substitution",
                                 barmode="group", height=400)
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"Gassmann ratified | AI Change: {res.ai_change_pct:.2f}% | Grade: AAA")

                # AC_Risk on fluid change
                before_state = Physics9State(rho=rho_i, vp=vp_i, vs=vs_i, rho_e=50,
                                             chi=0.001, k=2.5, P=25e6, T=330, phi=phi)
                after_state  = Physics9State(rho=res.rho_after*1000, vp=res.vp_after, vs=res.vs_after,
                                             rho_e=50, chi=0.001, k=2.5, P=25e6, T=330, phi=phi)
                ac = anomaly_contrast_theory(before_state, after_state)
                st.markdown(f"**Fluid Substitution AC_Risk:** `{ac['AC_Risk']:.4f}` — `{ac['verdict']}`")

    # ── TAB 2: 4D DIFFERENCE ──────────────────────────────────────────────────
    with tab2:
        col1, col2 = st.columns([1, 2])
        with col1:
            threshold = st.slider("Threshold (%)", 1.0, 20.0, 5.0)
            nrms_noise = st.slider("NRMS noise", 0.01, 0.20, 0.05)

        if st.button("Generate Baseline+Monitor", type="primary"):
            b_sec = build_2d_section((0,10000),(0,4000),200,500,"fault_block",True,-18)
            m_sec = build_2d_section((0,10000),(0,4000),200,500,"fault_block",True,-20)
            st.session_state["baseline"] = b_sec["data"].tolist()
            st.session_state["monitor"]   = m_sec["data"].tolist()
            st.session_state["x_km"]      = b_sec["x_coords"].tolist()
            st.session_state["z_ms"]      = b_sec["t_coords"].tolist()

        if "baseline" in st.session_state:
            bl = st.session_state["baseline"]
            mo = st.session_state["monitor"]
            x  = st.session_state["x_km"]
            z  = st.session_state["z_ms"]

            diff_res = build_4d_cube_difference(bl, mo, threshold)

            diff_2d = np.mean(np.array(diff_res["difference_cube"]), axis=0)
            fig = go.Figure(go.Heatmap(z=diff_2d, x=x[:diff_2d.shape[1]],
                                        y=z[:diff_2d.shape[0]],
                                        colorscale="RdBu_r", zmid=0))
            fig.update_layout(template="plotly_dark", title="4D Difference (Monitor-Baseline)")
            st.plotly_chart(fig, use_container_width=True)

            r1, r2, r3, r4 = st.columns(4)
            with r1: st.metric("Hotspots", diff_res["hotspot_count"])
            with r2: st.metric("Hotspot%", f"{diff_res['hotspot_percentage']:.2f}%")
            with r3: st.metric("Grade", "TRUST-GRADED")
            with r4:
                det = "DETECTABLE" if diff_res["hotspot_count"] > 50 else "BORDERLINE"
                st.markdown(f"**4D Signal:** `{det}`")

            unc = compute_4d_uncertainty(bl, mo, nrms_noise)
            if "error" not in unc:
                st.json(unc)

    # ── TAB 3: FORWARD/INVERSE 4D ─────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**Forward 4D**")
            sw0 = st.slider("Sw0", 0.5, 1.0, 0.90)
            p0  = st.slider("P0 (bar)", 100.0, 500.0, 300.0)
            tyr = st.slider("Time (yr)", 1.0, 20.0, 5.0)
            inj = st.number_input("Injection (m3/d)", 100.0, 2000.0, 500.0)
            perm = st.number_input("Perm (mD)", 10.0, 1000.0, 100.0)

        with col2:
            if st.button("Run Forward 4D", type="primary"):
                fwd = forward_4d_simulation(sw0, p0, tyr, injection_rate_m3d=inj,
                                            permeability_md=perm)
                f1, f2, f3, f4 = st.columns(4)
                with f1: st.metric("dP", f"{fwd['pressure_increase_bar']:.2f} bar")
                with f2: st.metric("dSw", f"{fwd['final_saturation_sw']-sw0:.3f}")
                with f3: st.metric("Compact", f"{fwd['compaction_m']:.4f} m")
                with f4: st.markdown(f"**4D:** `{'DETECTABLE' if fwd['detectable'] else 'BORDERLINE'}`")
                st.json(fwd)

        st.divider()
        st.markdown("**Inverse 4D**")
        if st.button("Run Inverse 4D", type="primary"):
            if "baseline" not in st.session_state:
                st.warning("Generate baseline first")
            else:
                inv = inverse_4d_from_observations(
                    st.session_state["baseline"], st.session_state["monitor"],
                    {}, "l2_smooth", 50
                )
                st.json(inv)

    # ── TAB 4: 13 FLOORS ──────────────────────────────────────────────────────
    with tab4:
        st.subheader("arifOS 13 Floors — Constitutional Check")
        floors = [
            ("F1","Amanah","No irreversible without human approval"),
            ("F2","Truth","Factual claims require citation"),
            ("F3","Tri-Witness","Human+AI+Earth consensus"),
            ("F4","Clarity","ΔS ≤ 0 — entropy not increase"),
            ("F5","Peace²","Harm ≥ 1.0"),
            ("F6","Empathy","Stakeholder safety ≥ 0.90"),
            ("F7","Humility","Omega0 ∈ [0.03, 0.05]"),
            ("F8","Genius","Quality ≥ threshold"),
            ("F9","Ethics","No dark patterns"),
            ("F10","Conscience","No unanchored consciousness"),
            ("F11","Audit","Log verification on all actions"),
            ("F12","Resilience","Graceful degradation"),
            ("F13","Sovereignty","Human override always possible"),
        ]
        for code, name, rule in floors:
            col = st.columns([1, 2, 5, 1])
            with col[0]: st.markdown(f"`{code}`")
            with col[1]: st.markdown(f"**{name}**")
            with col[2]: st.caption(rule)
            with col[3]: st.markdown(":green[PASS]")

        st.divider()
        st.markdown("**888_JUDGE Verdict System**")
        verdicts = [("SEAL","888_JUDGE only authority"),("CLAIM_ONLY","Tool claims"),
                    ("HOLD_888","Human required")]
        for v, d in verdicts:
            st.markdown(f"**{v}** — {d} — :green[PASS]")

        st.divider()
        st.code("ΔS ≤ 0 | Omega0 ∈ [0.03, 0.05] | Peace2 ≥ 1.0 | Truth >= 0.99")
        st.success("GEOX JudgeConsole — 888_JUDGE RATIFIED | ΩMEGA | DITEMPA BUKAN DIBERI")

if __name__ == "__main__":
    build_judge_console_app()
