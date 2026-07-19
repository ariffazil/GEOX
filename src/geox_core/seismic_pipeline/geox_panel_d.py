#!/usr/bin/env python3
"""
GEOX Panel D — Cognitive Interpretation Render
================================================
v1.0 — Forged 2026-07-06 under F13 SOVEREIGN.

Renders what the geologist judges — not what pixels show.

The cognitive panel is NOT an annotated photograph.
It is a GEOLOGICAL INTERPRETATION rendered visually:

    Zone bands      → what geological system is this zone?
    Termination symbols → onlap ▲, downlap ▽, truncation ┴, concordance —
    Fault labels    → ranked hypothesis, not just "F1"
    Horizon labels  → sequence significance, continuity confidence
    Artifact boxes  → "image may be lying here"
    Epistemic rulers → what is OBS / DER / INT on this panel

This is the panel a senior geologist would show to a partner
to justify a drilling decision.

Usage:
    from geox_panel_d import render_cognitive_panel
    render_cognitive_panel(attrs, fp, faults, horizons,
                           packages, terminations, artifacts, hypotheses,
                           raw_arr, crop_bbox, prov, output_dir)

DITEMPA BUKAN DIBERI.
"""

import matplotlib
import numpy as np

matplotlib.use('Agg')
import os

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ── Colour palette (geologist convention) ──────────────────────────────
FAULT_COLOR   = '#FF4444'       # red — fault
HORIZON_COLORS = ['#00FF87', '#00D4FF', '#FFE566', '#FF6BD6',
                  '#87CEEB', '#FF9F43', '#A8FF78', '#FF8EFF']
ZONE_COLORS   = {
    'PARALLEL':        ('#1a3a5c', 0.18),  # deep blue — marine
    'SUBPARALLEL':     ('#1a4a2e', 0.18),  # green — coastal
    'DIVERGENT_RIGHT': ('#4a2e1a', 0.22),  # brown — growth
    'DIVERGENT_LEFT':  ('#4a2e1a', 0.22),
    'CHAOTIC':         ('#4a1a1a', 0.28),  # dark red — basement/MTC
    'TRANSPARENT':     ('#2a2a4a', 0.22),  # grey-blue — massive/evap
    'HUMMOCKY':        ('#3a3a1a', 0.22),  # olive — carbonate
    'IRREGULAR':       ('#3a2a4a', 0.18),  # purple — mixed
}
ZONE_LABELS = {
    'PARALLEL':        'Post-rift thermal sag / marine',
    'SUBPARALLEL':     'Coastal plain / shallow marine',
    'DIVERGENT_RIGHT': 'Growth fault / differential subsidence →',
    'DIVERGENT_LEFT':  '← Growth fault / differential subsidence',
    'CHAOTIC':         'Basement / MTC / fault damage / volcanic',
    'TRANSPARENT':     'Massive sand / evaporite / gas wipeout?',
    'HUMMOCKY':        'Carbonate build-up / reef / mud volcano',
    'IRREGULAR':       'Mixed / deformed / onlap zone',
}

# Termination symbols (sequence stratigraphy convention)
TERM_SYMBOLS = {
    'ONLAP':               ('▲', '#00FF87', 'Onlap — transgressive'),
    'DOWNLAP':             ('▽', '#FFE566', 'Downlap — progradational'),
    'TRUNCATION_OR_TOPLAP':('┴', '#FF6BD6', 'Truncation/Toplap — unconformity?'),
    'CONCORDANCE':         ('—', '#888888', 'Concordance — continuous'),
}


def render_cognitive_panel(attrs: dict, fp: np.ndarray,
                            faults: list, horizons: list,
                            packages: list, terminations: list,
                            artifacts: dict, hypotheses: dict,
                            raw_arr: np.ndarray, crop_bbox: list,
                            prov: dict, output_dir: str) -> str:
    """Render Panel D — the cognitive interpretation panel.

    Layout (4-panel figure):
    ┌─────────────────────────────────┬──────────────┐
    │                                 │  ZONE LEGEND │
    │   MAIN COGNITIVE PANEL          │  (§1 arch.)  │
    │   (AGC + zones + picks +        ├──────────────┤
    │    terminations + hypotheses)   │  FAULT TABLE │
    │                                 │  (§3 ranked) │
    ├──────────────────────────────┬──┴──────────────┤
    │  FAULT PROBABILITY          │  EPISTEMIC RULER │
    │  (heat map + artifact flags) │  (OBS/DER/INT)  │
    └──────────────────────────────┴─────────────────┘
    """
    os.makedirs(output_dir, exist_ok=True)

    x0, y0, x1, y1 = crop_bbox
    agc = attrs['agc']
    hc, wc = agc.shape
    prov_short = f"img:{prov.get('image_sha256_short','?')} | {prov.get('run_tag','?')}"

    fig = plt.figure(figsize=(24, 14), facecolor='#0a0d14')

    # ── Grid layout ──────────────────────────────────────────────────
    gs = GridSpec(2, 3, figure=fig,
                  width_ratios=[3, 0.8, 1.0],
                  height_ratios=[3, 1],
                  hspace=0.08, wspace=0.06)

    ax_main   = fig.add_subplot(gs[0, 0])   # main cognitive panel
    ax_legend = fig.add_subplot(gs[0, 1])   # zone legend + sequence strat
    ax_table  = fig.add_subplot(gs[0, 2])   # fault/horizon hypothesis table
    ax_fp     = fig.add_subplot(gs[1, 0])   # fault probability + artifacts
    ax_epist  = fig.add_subplot(gs[1, 1:])  # epistemic ruler

    for ax in [ax_main, ax_legend, ax_table, ax_fp, ax_epist]:
        ax.set_facecolor('#0a0d14')
        for spine in ax.spines.values():
            spine.set_edgecolor('#1e2a3a')

    # ════════════════════════════════════════════════════════════════
    # MAIN PANEL — the geologist's section
    # ════════════════════════════════════════════════════════════════

    # Base: AGC (seismic-convention colourmap)
    ax_main.imshow(agc, cmap='seismic', aspect='auto', vmin=-1.5, vmax=1.5, alpha=0.92)

    # ── Zone bands ──────────────────────────────────────────────────
    for pkg in packages:
        r0, r1 = pkg['row_range']
        geom   = pkg['geometry']
        fc, alpha = ZONE_COLORS.get(geom, ('#222', 0.15))
        rect = mpatches.Rectangle(
            (0, r0), wc, r1 - r0,
            facecolor=fc, alpha=alpha, edgecolor='none', zorder=2)
        ax_main.add_patch(rect)
        # Zone label on left margin
        geo_label = ZONE_LABELS.get(geom, geom)
        ax_main.text(-wc * 0.01, (r0 + r1) / 2, f'{pkg["zone_id"]}',
                     color='#aaaacc', fontsize=7, va='center', ha='right',
                     fontweight='bold',
                     path_effects=[pe.withStroke(linewidth=1.5, foreground='black')])
        # Thin zone boundary line
        ax_main.axhline(r1, color='#334466', linewidth=0.5, alpha=0.6, zorder=3)

    # ── Horizons with termination symbols ───────────────────────────
    term_lookup = {t['horizon_id']: t for t in terminations}

    for i, h in enumerate(horizons):
        col   = HORIZON_COLORS[i % len(HORIZON_COLORS)]
        pts   = np.array(h['pts'])
        contp = int(h['continuity'] * 100)

        # Main horizon line
        ax_main.plot(pts[:, 0], pts[:, 1], '-', color=col,
                     linewidth=2.5, alpha=0.92, zorder=5,
                     path_effects=[pe.withStroke(linewidth=4, foreground='black')])

        # Horizon FULL epistemic label at 65% — geologist-readable block
        lx = int(wc * 0.65)
        ly = int(pts[lx, 1]) if lx < len(pts) else int(pts[-1, 1])
        t  = term_lookup.get(h['id'])
        seq_flag = '▲' if t and t['sequence_significance'] == 'HIGH' else ''
        artifact_flag = '⚠' if any('ARTIFACT' in af for af in
                                     next((hh.get('artifact_flags', [])
                                           for hh in hypotheses.get('horizons', [])
                                           if hh['horizon_id'] == h['id']), [])) else ''
        # Full epistemic block
        hh_data = next((hh for hh in hypotheses.get('horizons', [])
                        if hh['horizon_id'] == h['id']), {})
        top_h_hyp = hh_data.get('hypotheses_ranked', [{}])[0].get('hypothesis', '?')[:28]
        alts = [r['hypothesis'][:22] for r in hh_data.get('hypotheses_ranked', [])[1:3]]
        alt_str = ' / '.join(alts) if alts else 'unknown'
        h_conf   = hh_data.get('confidence_cap', 0)
        term_str = ''
        if t:
            lt = t['left_termination']['type'].split('_')[0]
            rt = t['right_termination']['type'].split('_')[0]
            term_str = f"L:{lt} R:{rt}  seq={t['sequence_significance']}"
        status_str = 'HOLD → INT_GEOLOGY' if contp < 70 or artifact_flag else 'INT_SEISMIC'

        label_lines = (
            f"{h['id']} {seq_flag} {artifact_flag}"
            f"\nINT_SEISMIC: {top_h_hyp}"
            f"\nconf: {h_conf:.0%}  cont={contp}%"
            f"\nalt: {alt_str[:30]}"
            f"\n{term_str}"
            f"\nstatus: {status_str}"
        )
        ax_main.text(lx + 6, ly - 10, label_lines,
                     color=col, fontsize=6.2, fontweight='bold', va='bottom',
                     path_effects=[pe.withStroke(linewidth=2.0, foreground='black')],
                     bbox=dict(boxstyle='round,pad=0.35', facecolor='#0a0d14', alpha=0.82),
                     zorder=6)

        # Termination symbols at left and right endpoints
        if t:
            # Left termination
            lt = t['left_termination']['type']
            sym, scol, slabel = TERM_SYMBOLS.get(lt, ('?', '#888', lt))
            ax_main.text(wc * 0.02, pts[0, 1],
                         sym, color=scol, fontsize=13, va='center',
                         path_effects=[pe.withStroke(linewidth=2, foreground='black')],
                         zorder=7)
            # Right termination
            rt = t['right_termination']['type']
            sym_r, scol_r, _ = TERM_SYMBOLS.get(rt, ('?', '#888', rt))
            ax_main.text(wc * 0.96, pts[-1, 1],
                         sym_r, color=scol_r, fontsize=13, va='center',
                         path_effects=[pe.withStroke(linewidth=2, foreground='black')],
                         zorder=7)

    # ── Faults with hypothesis labels ───────────────────────────────
    fault_hyps = {fh['fault_id']: fh for fh in hypotheses.get('faults', [])}

    for f in faults:
        fpts = np.array(f['pts'])
        fh   = fault_hyps.get(f['id'], {})
        top_hyp = fh.get('hypotheses_ranked', [{}])[0].get('hypothesis', 'unknown')
        # Shorten label for space
        short = top_hyp.split('(')[0].strip()[:22]
        conf_cap = fh.get('confidence_cap', 0)

        ax_main.plot(fpts[:, 1], fpts[:, 0], '-', color=FAULT_COLOR,
                     linewidth=2.8, alpha=0.92, zorder=5,
                     path_effects=[pe.withStroke(linewidth=4.5, foreground='black')])

        mid = len(fpts) // 2
        # Full epistemic block per doctrine: not just "F1" but the full judgment
        top_hyp_full = fh.get('hypotheses_ranked', [{}])[0].get('hypothesis', 'unknown')
        alts_f = [r['hypothesis'][:24] for r in fh.get('hypotheses_ranked', [])[1:3]]
        alt_f_str = ' /\n   '.join(alts_f) if alts_f else 'unknown'
        label = (
            f"{f['id']}  dip={f.get('dip_est','?')}"
            f"\nINT_SEISMIC: {top_hyp_full[:28]}"
            f"\nconfidence: {conf_cap:.0%}"
            f"\nalt: {alt_f_str[:28]}"
            f"\n   {(alts_f[1] if len(alts_f) > 1 else '')[:28]}"
            f"\nstatus: HOLD → INT_GEOLOGY"
        )
        ax_main.annotate(
            label,
            xy=(fpts[mid, 1], fpts[mid, 0]),
            xytext=(fpts[mid, 1] + wc * 0.07, fpts[mid, 0] - hc * 0.05),
            color=FAULT_COLOR, fontsize=6.2, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=FAULT_COLOR,
                            lw=1.2, connectionstyle='arc3,rad=0.2'),
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#1a0505', alpha=0.90),
            zorder=8,
        )

    # ── Artifact warning overlays ────────────────────────────────────
    art_detail = artifacts.get('artifacts', {})
    for at_name, at_data in art_detail.items():
        if at_name == 'velocity_pullup_sag':
            for cand in at_data.get('candidates', [])[:2]:
                hid  = cand.get('horizon_id', '')
                h_match = next((h for h in horizons if h['id'] == hid), None)
                if h_match:
                    pts = np.array(h_match['pts'])
                    ax_main.fill_between(pts[:, 0], pts[:, 1] - 8, pts[:, 1] + 8,
                                         alpha=0.25, color='#FFAA00', zorder=4)
                    ax_main.text(wc * 0.5, pts[wc // 2, 1] + 12,
                                 f"⚠ VELOCITY {cand['shape']}?",
                                 color='#FFAA00', fontsize=7, ha='center',
                                 path_effects=[pe.withStroke(linewidth=1.5, foreground='black')],
                                 zorder=8)
        elif at_name == 'gas_wipeout_chimney':
            for cand in at_data.get('candidates', [])[:1]:
                r_lo, r_hi = cand.get('wipeout_rows', [0, 0])
                rect = mpatches.Rectangle(
                    (wc * 0.3, r_lo), wc * 0.4, r_hi - r_lo,
                    facecolor='#FF8C00', alpha=0.12,
                    edgecolor='#FF8C00', linewidth=1, linestyle='--', zorder=4)
                ax_main.add_patch(rect)
                ax_main.text(wc * 0.5, (r_lo + r_hi) / 2,
                             '⚠ GAS WIPEOUT / CHIMNEY?',
                             color='#FF8C00', fontsize=7, ha='center', va='center',
                             path_effects=[pe.withStroke(linewidth=1.5, foreground='black')],
                             zorder=8)

    # ── Main panel styling ───────────────────────────────────────────
    ax_main.set_xlim(0, wc)
    ax_main.set_ylim(hc, 0)
    ax_main.set_title(
        'GEOX Cognitive Interpretation — Malay Basin Context\n'
        'CV detects · LLM explains · Agent tests · Geologist judges',
        color='white', fontsize=11, fontweight='bold', pad=8)
    ax_main.set_xlabel('Trace (pixel)', color='#667')
    ax_main.set_ylabel('TWT proxy (pixel) — NOT TRUE DEPTH', color='#667')
    ax_main.tick_params(colors='#445', labelsize=7)

    # Epistemic banner top-left
    ax_main.text(0.01, 0.01,
                 "INT_SEISMIC ≠ OBS_GEOLOGY  |  All features = ranked hypotheses  |  cap=0.90",
                 transform=ax_main.transAxes,
                 color='#FFE566', fontsize=7, va='bottom',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a0a', alpha=0.85),
                 zorder=10)

    # ════════════════════════════════════════════════════════════════
    # ZONE LEGEND + SEQUENCE STRAT KEY
    # ════════════════════════════════════════════════════════════════
    ax_legend.axis('off')
    ax_legend.set_title('Zone Architecture', color='#aaccff',
                         fontsize=9, fontweight='bold', pad=6)

    y_pos = 0.97
    for pkg in packages:
        geom  = pkg['geometry']
        fc, _ = ZONE_COLORS.get(geom, ('#444', 0.3))
        geo_label = ZONE_LABELS.get(geom, geom)
        # Colour swatch
        rect = mpatches.FancyBboxPatch(
            (0.02, y_pos - 0.04), 0.08, 0.035,
            boxstyle='round,pad=0.005',
            facecolor=fc, edgecolor='#334', linewidth=0.5,
            transform=ax_legend.transAxes, clip_on=False)
        ax_legend.add_patch(rect)
        coh = pkg['metrics']['mean_coherence']
        ax_legend.text(0.13, y_pos - 0.022,
                       f"{pkg['zone_id']}: {geom}\n  coh={coh:.2f}",
                       transform=ax_legend.transAxes,
                       color='#ccddeeff', fontsize=6.5, va='center')
        ax_legend.text(0.13, y_pos - 0.055,
                       f"  → {geo_label[:35]}",
                       transform=ax_legend.transAxes,
                       color='#8899aa', fontsize=5.8, va='center')
        y_pos -= 0.13

    # Termination symbol key
    y_pos -= 0.06
    ax_legend.text(0.02, y_pos, 'Termination Symbols:',
                   transform=ax_legend.transAxes,
                   color='#aaccff', fontsize=7.5, fontweight='bold')
    y_pos -= 0.07
    for ttype, (sym, scol, label) in TERM_SYMBOLS.items():
        ax_legend.text(0.04, y_pos, f'{sym}  {ttype.split("_")[0]}',
                       transform=ax_legend.transAxes,
                       color=scol, fontsize=7.5)
        ax_legend.text(0.04, y_pos - 0.048,
                       f'   {label}',
                       transform=ax_legend.transAxes,
                       color='#778899', fontsize=6)
        y_pos -= 0.11

    # Sequence significance
    y_pos -= 0.04
    ax_legend.text(0.02, y_pos, '▲ = HIGH seq significance',
                   transform=ax_legend.transAxes,
                   color='#FF6BD6', fontsize=7)
    y_pos -= 0.07
    ax_legend.text(0.02, y_pos, '⚠ = artifact flag — test first',
                   transform=ax_legend.transAxes,
                   color='#FFAA00', fontsize=7)

    # ════════════════════════════════════════════════════════════════
    # HYPOTHESIS TABLE — faults and horizons ranked
    # ════════════════════════════════════════════════════════════════
    ax_table.axis('off')
    ax_table.set_title('Ranked Hypotheses\n(Malay Basin prior)',
                        color='#aaccff', fontsize=9, fontweight='bold', pad=6)

    y = 0.97
    # Faults
    ax_table.text(0.02, y, 'FAULTS', transform=ax_table.transAxes,
                  color=FAULT_COLOR, fontsize=8, fontweight='bold')
    y -= 0.06
    for fh in hypotheses.get('faults', []):
        ax_table.text(0.02, y, f"{fh['fault_id']}  {fh['dip_class']}  cap={fh['confidence_cap']:.0%}",
                      transform=ax_table.transAxes, color='#ccddee', fontsize=7, fontweight='bold')
        y -= 0.05
        for rh in fh['hypotheses_ranked'][:3]:
            bar_w = rh['prior_prob'] * 0.85
            bar = mpatches.FancyBboxPatch(
                (0.02, y - 0.025), bar_w, 0.028,
                boxstyle='round,pad=0.003',
                facecolor=FAULT_COLOR, alpha=0.25 + rh['prior_prob'] * 0.4,
                transform=ax_table.transAxes, clip_on=False)
            ax_table.add_patch(bar)
            short = rh['hypothesis'][:28]
            ax_table.text(0.04, y - 0.012, f"#{rh['rank']} {short}",
                          transform=ax_table.transAxes, color='#ffcccc', fontsize=5.8)
            ax_table.text(0.87, y - 0.012, f"P={rh['prior_prob']:.2f}",
                          transform=ax_table.transAxes, color='#ff9999', fontsize=5.8,
                          ha='right')
            y -= 0.045
        y -= 0.02

    # Horizons
    ax_table.text(0.02, y, 'HORIZONS', transform=ax_table.transAxes,
                  color='#00FF87', fontsize=8, fontweight='bold')
    y -= 0.06
    for hh in hypotheses.get('horizons', [])[:4]:
        col = HORIZON_COLORS[list(h['id'] for h in horizons).index(hh['horizon_id'])
                              if hh['horizon_id'] in [h['id'] for h in horizons]
                              else 0]
        term_l = hh['termination_context']['left'][:5]
        term_r = hh['termination_context']['right'][:5]
        seq    = hh['termination_context']['sequence_significance']
        seq_m  = '▲' if seq == 'HIGH' else '·'
        ax_table.text(0.02, y,
                      f"{hh['horizon_id']} {seq_m} cont={hh['continuity']:.0%}  L={term_l} R={term_r}",
                      transform=ax_table.transAxes, color=col, fontsize=7, fontweight='bold')
        y -= 0.045
        for rh in hh['hypotheses_ranked'][:2]:
            short = rh['hypothesis'][:28]
            ax_table.text(0.04, y, f"#{rh['rank']} {short}  P={rh['prior_prob']:.2f}",
                          transform=ax_table.transAxes, color='#aaddcc', fontsize=5.8)
            y -= 0.038
        if hh['artifact_flags']:
            ax_table.text(0.04, y, f"⚠ {hh['artifact_flags'][0][:35]}",
                          transform=ax_table.transAxes, color='#FFAA00', fontsize=5.5)
            y -= 0.038
        y -= 0.01

    # ════════════════════════════════════════════════════════════════
    # FAULT PROBABILITY PANEL
    # ════════════════════════════════════════════════════════════════
    ax_fp.imshow(fp, cmap='YlOrRd', aspect='auto',
                 vmin=0, vmax=np.percentile(fp, 98), alpha=0.9)
    ax_fp.set_title('Fault Probability (DER_IMAGE_CONTRAST)',
                     color='#ffddaa', fontsize=8, pad=4)
    ax_fp.set_xlabel('Trace', color='#555', fontsize=7)
    ax_fp.tick_params(colors='#445', labelsize=6)

    # Overlay artifact zones on fault prob panel
    art_detail = artifacts.get('artifacts', {})
    n_flags = artifacts.get('n_artifact_types_flagged', 0)
    verdict_color = '#FF4444' if n_flags >= 2 else '#FFAA00' if n_flags == 1 else '#00FF87'
    ax_fp.text(0.02, 0.97, f"Artifact screen: {artifacts['screen_verdict'][:40]}",
               transform=ax_fp.transAxes, color=verdict_color, fontsize=6.5, va='top',
               bbox=dict(boxstyle='round', facecolor='#0a0d14', alpha=0.85))

    # ════════════════════════════════════════════════════════════════
    # EPISTEMIC RULER
    # ════════════════════════════════════════════════════════════════
    ax_epist.axis('off')
    ax_epist.set_facecolor('#0a0d14')

    # The evidence ladder — horizontal ruler
    ladder = [
        ('OBS_IMAGE_PIXEL',    '#555577', 'Raw pixel values.\nNo geological claim.',          0.00),
        ('DER_IMAGE_CONTRAST', '#4477aa', 'Computed from pixels:\nAGC, phase, disc, edge.',   0.22),
        ('INT_SEISMIC',        '#44aa77', 'Detected features:\nFaults, horizons, zones.',      0.44),
        ('INT_GEOLOGY',        '#aaaa44', 'HOLD until:\nwell tie + multi-line + AVO.',         0.66),
        ('CAPITAL_CONSEQUENCE','#aa4444', 'HOLD until:\nWEALTH NPV/EMV + sovereign.',         0.88),
    ]

    ax_epist.set_title('Epistemic Ladder (what tier are we on?)',
                        color='#aaccff', fontsize=9, fontweight='bold', pad=6)

    for label, col, desc, xpos in ladder:
        # Column box
        rect = mpatches.FancyBboxPatch(
            (xpos + 0.01, 0.15), 0.19, 0.70,
            boxstyle='round,pad=0.01',
            facecolor=col, alpha=0.18,
            edgecolor=col, linewidth=1.5,
            transform=ax_epist.transAxes, clip_on=False)
        ax_epist.add_patch(rect)

        ax_epist.text(xpos + 0.105, 0.82, label,
                      transform=ax_epist.transAxes,
                      color=col, fontsize=6.5, fontweight='bold', ha='center')
        ax_epist.text(xpos + 0.105, 0.50, desc,
                      transform=ax_epist.transAxes,
                      color='#8899aa', fontsize=6, ha='center', va='center')

        # "Current tier" marker
        if label == 'INT_SEISMIC':
            ax_epist.text(xpos + 0.105, 0.22, '◀ NOW',
                          transform=ax_epist.transAxes,
                          color='#FFE566', fontsize=7, fontweight='bold', ha='center',
                          bbox=dict(boxstyle='round,pad=0.2', facecolor='#3a3a10', alpha=0.9))

        # Arrow between boxes
        if xpos < 0.88:
            ax_epist.annotate('', xy=(xpos + 0.22, 0.50), xytext=(xpos + 0.20, 0.50),
                              transform=ax_epist.transAxes,
                              arrowprops=dict(arrowstyle='->', color='#334466', lw=1.5))

    ax_epist.text(0.50, 0.04,
                  f"OBS_IMAGE ≠ OBS_GEOLOGY  ·  No alternatives, no confidence  ·  {prov_short}",
                  transform=ax_epist.transAxes,
                  color='#445566', fontsize=6.5, ha='center')

    # ── Figure title ─────────────────────────────────────────────────
    fig.suptitle(
        'GEOX Cognitive Interpretation Panel  ·  '
        'CV detects → LLM explains → Agent tests → Geologist judges → Governance seals',
        color='#aaccff', fontsize=10, fontweight='bold', y=0.995)

    plt.tight_layout(rect=[0, 0, 1, 0.99])
    out_path = os.path.join(output_dir, 'D_cognitive_panel.png')
    plt.savefig(out_path, dpi=180, bbox_inches='tight', facecolor='#0a0d14')
    plt.close()
    print(f"  ✅ Panel D (cognitive): {out_path}")
    return out_path
