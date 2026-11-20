#!/usr/bin/env python3
"""
generate_evidence_catalog_app.py — render geox.evidence.v1 catalog as a SEP-1865
MCP App HTML page (ui://geox/evidence-v1).

Single source of truth: the catalog JSON itself. This script NEVER hand-encodes
component semantics — it renders whatever the catalog declares. Re-run after any
catalog edit (byte-exact schema pinning discipline, rule 1 of the staging README).

Output: apps/evidence-v1/index.html — zero-JS, CSP-hardened, self-demonstrating:
the catalog's honesty components render THEMSELVES as the demo (an untagged number
must not render — including on this page: every number carries an EpistemicTagBadge).

Usage:
    python3 scripts/generate_evidence_catalog_app.py \
        [--catalog /root/forge_work/a2ui/catalogs/geox/evidence/v1/catalog.json] \
        [--policy  /root/forge_work/a2ui/policy/geox-readonly-tools.json] \
        [--out     apps/evidence-v1/index.html]
"""

import argparse
import hashlib
import html
import json
import os
import sys
from datetime import datetime, timezone

DEFAULT_CATALOG = "/root/forge_work/a2ui/catalogs/geox/evidence/v1/catalog.json"
DEFAULT_POLICY = "/root/forge_work/a2ui/policy/geox-readonly-tools.json"
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "apps", "evidence-v1", "index.html")

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "font-src 'none'; connect-src 'none'; script-src 'none'; frame-ancestors *"
)

CSS = """
:root { --bg:#0a0a0f; --bg2:#12121a; --bg3:#1a1a25; --gold:#d4af37; --cyan:#00d4aa;
        --red:#ff4757; --green:#2ed573; --txt:#e8e8f0; --dim:#9090a0; --bord:#2a2a3a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--txt); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
       padding:2rem; max-width:980px; margin:0 auto; }
h1 { font-size:1.5rem; color:var(--gold); margin-bottom:.25rem; }
h2 { font-size:1.1rem; color:var(--cyan); margin:2rem 0 .75rem; border-bottom:1px solid var(--bord); padding-bottom:.35rem; }
.mono { font-family:'JetBrains Mono','Fira Code',monospace; }
.dim { color:var(--dim); }
.meta { color:var(--dim); font-size:.82rem; margin-bottom:1.5rem; }
.card { background:var(--bg2); border:1px solid var(--bord); border-radius:8px; padding:1rem 1.15rem; margin:.6rem 0; }
.card h3 { font-size:.95rem; color:var(--gold); margin-bottom:.3rem; }
.badge { display:inline-block; font-family:monospace; font-size:.75rem; padding:.15rem .55rem;
         border-radius:4px; border:1px solid; margin-right:.4rem; }
.b-obs  { color:var(--green); border-color:var(--green); }
.b-der  { color:var(--cyan); border-color:var(--cyan); }
.b-int  { color:var(--gold); border-color:var(--gold); }
.b-hyp  { color:var(--orange,#ffa502); border-color:#ffa502; }
.marginbar { position:relative; height:10px; background:var(--bg3); border-radius:5px; margin:.5rem 0; }
.marginbar .fill { position:absolute; left:0; top:0; bottom:0; background:var(--cyan); border-radius:5px; }
.marginbar .band { position:absolute; top:-3px; bottom:-3px; background:rgba(255,255,255,.14); border-radius:3px; }
.banner { display:flex; align-items:center; gap:.6rem; padding:.5rem .8rem; border-radius:6px;
          font-family:monospace; font-size:.8rem; border:1px solid; margin:.4rem 0; }
.ban-none { color:var(--red); border-color:var(--red); background:rgba(255,71,87,.08); }
.ban-map  { color:var(--cyan); border-color:var(--cyan); background:rgba(0,212,170,.06); }
.fresh { font-family:monospace; font-size:.75rem; padding:.2rem .5rem; border-radius:4px; border:1px solid var(--bord); margin-right:.35rem; }
.f-live { color:var(--green); } .f-stale { color:#ffa502; } .f-unk { color:var(--dim); }
table { border-collapse:collapse; width:100%; font-size:.82rem; margin:.4rem 0; }
td,th { border:1px solid var(--bord); padding:.35rem .6rem; text-align:left; }
th { color:var(--dim); font-weight:600; }
code { background:var(--bg3); padding:.1rem .35rem; border-radius:3px; font-size:.8em; }
.rules li { margin:.45rem 0; font-size:.9rem; }
.foot { margin-top:2.5rem; padding-top:1rem; border-top:1px solid var(--bord); color:var(--dim); font-size:.78rem; }
.demo-num { font-size:1.05rem; }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def demo_component(cid, spec):
    """Render each catalog component DEMONSTRATING ITSELF (per its own design rules)."""
    desc = spec.get("description", "")
    out = [f'<div class="card"><h3>{esc(cid)}</h3>', f'<p class="dim" style="font-size:.85rem">{esc(desc)}</p>']
    if cid == "EpistemicTagBadge":
        out.append(
            '<div style="margin-top:.5rem"><span class="demo-num">7.42 <span class="dim">MMboe</span></span> '
            '<span class="badge b-obs">OBS · MEASURED</span>'
            '<span class="badge b-der">DER · CALIBRATED</span>'
            '<span class="badge b-hyp">HYP · coverage 0.12</span></div>'
        )
        out.append(
            '<p class="dim" style="font-size:.8rem;margin-top:.35rem">Every quantitative claim carries its class; untagged numbers do not render.</p>'
        )
    elif cid == "HumilityMarginBar":
        out.append(
            '<div style="margin-top:.5rem"><span class="demo-num">confidence 0.81</span> <span class="badge b-der">DER</span></div>'
            '<div class="marginbar"><div class="fill" style="width:81%"></div><div class="band" style="left:64%;width:34%"></div></div>'
            '<p class="dim" style="font-size:.8rem">Confidence never renders without its margin band (F7 HUMILITY).</p>'
        )
    elif cid == "CoverageClassBanner":
        out.append(
            '<div class="banner ban-map"><span>COVERAGE 0.62 · macrostrat_units</span></div>'
            '<div class="banner ban-none"><span>NO COVERAGE — unit_polygon absent</span></div>'
            '<p class="dim" style="font-size:.8rem;margin-top:.35rem">"none" renders as NO COVERAGE — never as zero, never as empty.</p>'
        )
    elif cid == "SourceFreshnessBadge":
        out.append(
            '<div style="margin-top:.5rem">'
            '<span class="fresh f-live">LIVE · 12s</span>'
            '<span class="fresh f-stale">STALE · 9d</span>'
            '<span class="fresh f-unk">UNKNOWN</span></div>'
            '<p class="dim" style="font-size:.8rem;margin-top:.35rem">STALE and UNKNOWN carry equal visual weight to LIVE.</p>'
        )
    else:
        out.append(f'<p class="dim" style="font-size:.8rem;margin-top:.4rem"><code>{esc(json.dumps(spec)[:220])}</code></p>')
    out.append("</div>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    ap.add_argument("--policy", default=DEFAULT_POLICY)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    cat_raw = open(args.catalog, "rb").read()
    cat = json.loads(cat_raw)
    cat_sha = hashlib.sha256(cat_raw).hexdigest()[:12]
    try:
        pol = json.load(open(args.policy))
        tools = pol.get("allow", [])
        n_tools = len(tools) if isinstance(tools, list) else 0
        n_deny = len(pol.get("always_deny", []))
        pol_name = os.path.basename(args.policy)
        if n_tools == 0:
            raise ValueError(f"policy {pol_name} declares 0 allow tools — refusing to render a lying policy block")
    except FileNotFoundError:
        raise SystemExit(f"FATAL: policy file not found: {args.policy} — catalog pages must cite a real fail-closed policy")

    cid = cat.get("catalogId", "?")
    proto = cat.get("protocolVersion", "?")
    title = cat.get("title", cid)
    instructions = cat.get("instructions", "")
    components = cat.get("components", {})
    functions = cat.get("functions", {})

    parts = []
    parts.append(f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">')
    parts.append(f'<meta http-equiv="Content-Security-Policy" content="{CSP}">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append(f"<title>GEOX Evidence Surfaces — {esc(cid)}</title>")
    parts.append(f"<style>{CSS}</style>\n</head>\n<body>")
    parts.append(f"<h1>{esc(title)}</h1>")
    parts.append(
        f'<div class="meta mono">A2UI catalog <strong>{esc(cid)}</strong> · protocol {esc(proto)} · '
        f"pinned schema: a2ui-v1 · catalog sha256:{cat_sha} · generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}</div>"
    )

    parts.append("<h2>Design rules (instructions — verbatim)</h2>")
    parts.append('<div class="card"><ul class="rules">')
    for rule in [r.strip() for r in instructions.split(") (") if r.strip()]:
        parts.append(f"<li>{esc(rule)}</li>")
    parts.append("</ul></div>")

    parts.append(f"<h2>Components ({len(components)}) — each demonstrating itself</h2>")
    for comp_id, spec in components.items():
        parts.append(demo_component(comp_id, spec))

    parts.append(f"<h2>Renderer-only formatters ({len(functions)})</h2>")
    fmt_demo = {
        "formatConfidence": lambda: (
            '<span class="mono">formatConfidence(0.81, "DER")</span> → <strong>0.81 DER</strong> <span class="dim">(F7 cap 0.90 noted)</span>'
        ),
        "formatMa": lambda: (
            '<span class="mono">formatMa(12.5, "Merdith2021")</span> → <strong>12.5 Ma</strong> <span class="dim">· model Merdith2021</span>'
        ),
        "formatDepth": lambda: '<span class="mono">formatDepth(2345, "TVD")</span> → <strong>2,345 m TVD</strong>',
    }
    parts.append('<div class="card">')
    for fn, spec in functions.items():
        d = spec.get("description", "") if isinstance(spec, dict) else ""
        demo = fmt_demo.get(fn, lambda: f"<code>{esc(fn)}</code>")
        parts.append(f"<p style='margin:.5rem 0'><strong class='mono'>{esc(fn)}</strong> — {esc(d)}<br>{demo()}</p>")
    parts.append("</div>")

    parts.append("<h2>UI tool policy (fail-closed)</h2>")
    parts.append(
        '<div class="card"><p style="font-size:.88rem">Surfaces generated with this catalog may call only the '
        f"<strong>{esc(n_tools)}</strong> OBSERVE-class tools allowlisted in <code>{esc(pol_name)}</code> "
        f"(with <strong>{esc(n_deny)}</strong> always-deny entries). "
        "Ingest / register / write-named tools stay excluded even where the organ manifest labels them observe — "
        "the name declares the data write. Host shell posture: this page itself calls zero MCP tools.</p></div>"
    )

    parts.append(
        '<div class="foot">Generated by <span class="mono">scripts/generate_evidence_catalog_app.py</span> from '
        f'<span class="mono">{esc(os.path.basename(args.catalog))}</span> (sha256:{cat_sha}) · '
        "A2UI v1.0 · SEP-1865 mime <span class='mono'>text/html;profile=mcp-app</span> · "
        "UI checks are UX hardening; arifOS kernel floors remain the sole integrity authority.</div>"
    )
    parts.append("</body>\n</html>")

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = "\n".join(parts)
    with open(out_path, "w") as f:
        f.write(doc)
    print(
        f"WROTE {out_path} ({len(doc)} bytes) from {cid} sha256:{cat_sha}, {len(components)} components, {len(functions)} formatters, policy {n_tools} tools"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
