# SITE_AUDIT.md — geox.arif-fazil.com audit & improvement plan

Audited 2026-11-24 by kimi-code/FI-008. Read-only: fetched the public surfaces and compared
them against the live registry (`/health`, `tools/list` = 29 public / 29 total).

---

## 1. What exists

| Surface | State | Verdict |
|---|---|---|
| `/` (human landing) | Renders essentially one line: "Earth Witness — Tanya Bumi · Apps & GUIs (7) · Sabah Observatory · Operator Cockpit" | **WEAK** — no explanation of what GEOX is, no status, no entry point for a newcomer |
| `/llms.txt` | Rich, accurate, well-structured: 29 tools with tiers, capability graph, 4 workflow packs, discipline statements | **STRONG** — best asset on the site |
| `/health` | JSON with `status`, `kernel_verdict`, `service` | OK |
| `/mcp` | Streamable HTTP MCP, 29 tools | OK |
| `/.well-known/agent-card.json`, `mcp.json` | Present | OK |
| Repo `README.md` | 396 lines, unusually honest ("What is not yet proven") | **STRONG** |

**The core finding:** the site is excellent for an agent and near-empty for a human.
An evaluator who is not an agent lands on a page that tells them nothing, while the
machine-readable layer they will never read contains the entire case.

---

## 2. Improvements, ranked by value per hour

### P0 — a human landing page that states the position (≈2 h)

Replace the one-line root with:

1. **One sentence**: "GEOX is a physics-and-honesty gate for AI agents working on
   subsurface data. It labels every number MEASURED / DERIVED / INTERPRETED / ASSUMED /
   UNKNOWN, and refuses impossible input."
2. **Maturity badge, unmissable**: `prototype · 0 external users · 1 public benchmark`.
   Stating this raises trust; hiding it destroys it the first time a visitor probes.
3. **Three live facts** pulled at render time: tool count, service status, last deploy SHA.
   Never hand-typed — a stale number is worse than no number.
4. **One worked example**: the Volve answer-key check (STOIIP 18.70, decline 41.0 %/yr,
   class I AVO) with a link to the golden suite. One real result beats a feature list.
5. **Two doors**: "I am an agent" → `/llms.txt`; "I am a human" → README.

### P1 — make the honest gaps a page, not a footnote (≈1 h)

`/gaps` — machine and human readable — listing every UNMEASURED and UNPROVEN item
(pre-drill POS, closure area, Volve Rock-Eval, geothermal gradient, 0 seismic cubes,
0 external users). This is the differentiator; it should be a first-class URL.

### P1 — status page (≈1 h)

`/status` with: service up, tool count, deployed SHA, last successful deploy, last failed
verify, VAULT999 chain state. Today that information exists only inside a JSON the visitor
must already know to request.

### P2 — versioned capability index (≈1 h)

`/capabilities.json` — machine-readable tier map with `since_version` per tool, so an agent
can ask "what changed since I last integrated" instead of diffing `llms.txt` by eye.

### P2 — provenance on every number rendered on the site (≈2 h)

Wherever the landing page shows a figure, render its label next to it (`MEASURED` etc.)
and its source. The site should practise what the tools enforce.

---

## 3. Things not to do

- Do not add a marketing hero image carousel. It signals product maturity GEOX does not have.
- Do not publish a benchmark number that is not reproducible from the repo.
- Do not quote a bare "90 tools" or a bare "29 tools" without its scope: 29 is the
  public/discovery surface, 90 is the runtime total (39 internal). Both are true; mixing
  them is how this figure got wrong twice.
- Do not show a tool count as a health metric.

---

## 4. Acceptance check

A person with no context, in 60 seconds on the root page, should be able to answer:
what is this, is it real, who has used it, and what does it refuse to do.
Today they cannot answer any of the four.
