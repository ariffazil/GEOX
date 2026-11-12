# UPGRADE MAP — Macrostrat → GEOX MCP + /earth/ (2026-11-12)

Owner: claude-code/FI-002 · Probe date: 2026-11-12 15:56–16:20 MYT · All numbers OBS unless labelled DER.

---

## 1. THE ANSWER (satu baris)

Tiada apa-apa dari `UW-Macrostrat/macrostrat` yang MEMECAHKAN GEOX hari ini — tapi repo itu
kini RUMAH API (sejak v2.4.1, 2026-10-20) dan ada 17 route + 3 perubahan bentuk respons yang
GEOX belum ambil; yang betul-betul perlu diambil adalah nama kelas liputan (coverage class),
kerana itu yang membuat jawapan GEOX baca "tiada batuan" bila sebenarnya "tiada poligon
unit, ada poligon peta umum".

---

## 2. GEOX state (measured)

| Thing | Value | Label |
|---|---|---|
| Live organ | :8081, 27/27 public tools, surface_drift ok (gap 0) | OBS |
| /health status | `degraded`, kernel_verdict HOLD | OBS |
| Degraded cause | `geox_source_drift.drift=true` — deployed HEAD `7b480f90f` ≠ origin/main `ad150e7a`, 28 files apart | OBS |
| Repo topology | THREE trees on THREE history lines: origin/main (ad150e7a) · /root/GEOX feat branch (00583d3f) · /opt/geox deployed (7b480f90f). None is an ancestor of the others. | OBS |
| /root/GEOX dirty? | Clean on branch `feat/federation-flow-chron-frame` | OBS |

**What I landed (committed, tested, NOT deployed):**
commit `a616818b` on feat branch — coverage class + upstream build stamp in the macrostrat lane.
- `macrostrat_client.get_coverage_class()` — classifies `unit_polygon | map_polygon | none`
- `macrostrat_client.get_api_version()` — reads `/api/v2/version`, honest `available:false`
- `basin.py` macrostrat modes carry `coverage_class`, `coverage_explanation`, `map_polygon_count`, `map_unit`, `upstream_api`
- Tests: 7 offline + 4 live integration; 150 passed / 1 skipped across basin+contract suites; ruff clean
- Live probe of changed code: Sabah shelf (6.0814,116.7241) → `map_polygon`, 0 unit polys, 1 map poly ("Cenozoic sedimentary rocks"); Madison control → `unit_polygon`, 15 units; upstream `api-v2 2.6.0 commit 0ec2ff00`

The 2 changed files are byte-identical between my branch parent and the deployed tree, so the
change applies with **zero collateral** — but see §5 before deploying.

---

## 3. /earth/ site state (measured)

| Thing | Value |
|---|---|
| Preflight gate | PASS (split-root, orphan-assets, phantom-200) |
| Upstream build stamp | **DEPLOYED + LIVE** — stat-meta and click panel now name `api-v2 2.6.0`; omitted honestly if the probe fails |
| Committed | `9e68f5e` on branch `feat/earth-upstream-build-stamp` (only the earth file; the repo's other 28 dirty files are another lane's parked work, untouched) |
| Rollback | `/var/www/html/earth/index.html.bak-20261112T161617` · `/var/www/html/arif/earth/index.html.bak-20261112T161646` |

**New defect found and filed (`p2-earth-split-root-homepage-served-from-arif-copy`):**
`/earth/` (homepage) is served from `/var/www/html/arif/earth/` via `handle @static_dirs`
(literal `/earth` paths outrank `handle /earth*`), while `/earth/*` subpages come from
`/var/www/html/earth/` via `handle /earth*`. My first rsync went to the wrong copy and the
live page did not change; site-preflight PASSed anyway because it reads the vhost text and
does not model Caddy matcher precedence. Deploy now goes to BOTH roots; verify by comparing
the live body, not the status code.

---

## 4. Macrostrat upstream delta (what GEOX has not absorbed)

**Client coverage today:** units · columns · geologic_units/map · defs/{lithologies, environments,
strat_names, intervals, minerals, sources} · fossils · stats. All 11 still answer 200 with their
documented shapes (probed live). **Nothing breaks.**

**Verified-live routes GEOX does not reach (all probed 200 on 2026-11-12):**
`/version` · `/health` · `/age_model` · `/sections` · `/measurements` · `/carto/small` · `/elevation` ·
`/mobile/map_query_v2` · defs: `timescales` · `econs` · `lithology_attributes` · `projects` ·
`strat_name_concepts` · `structures` · `plates` · `refs` · `grainsizes` · `groups` · `languages` ·
`measurement_sources` · `drilling_sites` · `autocomplete`

**Response-shape changes since the client was written (all additive, none break current parsing):**
- v2.4.1 `/defs/intervals` honors `late_age`/`early_age` as aliases for `t_age`/`b_age`
- v2.5.0 `/columns?response=long` adds `refs_expanded` (citation + verb + locator) and `project_name`
- v2.3.10 `/columns` adds `status_code`; `/units` allows `unit_id` without `project_id`
- v2.4.0 `/version` + `/health` (503 when DB down) — the build stamp GEOX now carries
- v2.6.0 `mobile/map_query*` answers from carto under `CARTO_BUILD=compilation`

**Tileserver:** the `.changes` entries (staged-map colors, compilation polygon weeding) touch
*compilation/staged-map* tiles only. The globe's `/carto/{z}/{x}/{y}.png` layer is unchanged. DER.

**Tile proxy note:** `tiles.macrostrat.org` now sends `access-control-allow-origin: *` itself, but the
Caddy proxy also adds `Cache-Control: immutable` and measured faster than direct from here
(0.09s vs 1.42s steady-state). **Keep the proxy.** Do not churn a working globe.

---

## 5. MENUNGGU ARIF (perintah tepat, jangan laksana dari lane ini)

**Why not me:** GATE HOLD (G 0.55/0.80, W3 0.61/0.75) + /health degraded (source drift) + a restart
of a production organ under HOLD. Also: the only reconciliation target for the deployed tree is
origin/main, and that swap is 28 files wide including `session_enforcement.py` and
`stateless_era.py` — that is the open P0's scope, not mine.

**(a) Setelah P0 reconcile selesai — satu laluan ke hadapan:**
```
cd /root/GEOX && git checkout main && git cherry-pick a616818b   # my 2-file change onto origin/main
cd /opt/geox && git pull && systemctl restart geox-mcp
make deploy-gate
# verify: geox_basin(mode='macrostrat_units', lat=6.0814, lng=116.7241) → coverage_class=map_polygon
```
Recommendation: reconcile /opt/geox onto origin/main first (28-file swap, needs its own gate),
THEN apply my commit. Do not swap origin/main onto the live organ blind.

**(b) Site push (publish):**
```
cd /root/arif-fazil.com && git push -u origin feat/earth-upstream-build-stamp
```
The change is already live and verified on the wire; push only syncs the public repo.

---

## 6. Receipts

- GEOX commit: `a616818b` (signed, claude lane key) — /root/GEOX feat/federation-flow-chron-frame
- Site commit: `9e68f5e` (signed) — /root/arif-fazil.com feat/earth-upstream-build-stamp
- Queue: `p2-geox-macrostrat-coverage-class` updated · `p2-earth-split-root-homepage-served-from-arif-copy` appended (tasks.json 626→627, backup `tasks.json.bak-20261112T082139Z`)
- Live verification: /earth/ serves `msBuild` x4 + `api/v2/version` x1, `cf-cache-status: DYNAMIC`
- Receipt dir: this file

---

## 7. FEDERATION + MCP ERA (added 2026-11-12, after the observatory probe)

`/root/GEOX/scripts/federation_conformance.py` (commit 4d2d15cc) measures four axes. Results:

| Axis | Verdict | Owner | Measured |
|---|---|---|---|
| AAA state | **FUSED** | — | GEOX in `organs.yaml` AND in AAA's live registry `/federation/organs`: `organId=geox, state=active, trustGrade=B, registeredAt 2026-11-11T17:59:20.974Z` |
| arifOS kernel | PARTIAL | arifOS (T3) | GEOX in the manifest; both edge directions declared (`arifos→geox`, `geox→arifos`); published aggregate `declared 11, reachable 11, semantic_proven 0, TRANSPORT_ALIGNED`; the per-edge LIST is not projected |
| GEOX own surface | PARTIAL | GEOX deploy lane | `/federation` and `/flow` are 404 live — the routes exist only on the undeployed branch |
| MCP era | **NOT_ALIGNED** | GEOX deploy lane | a 2026-07-28 client is downgraded to 2025-11-25; installed fastmcp 3.4.7 (knows eras ≤ 2025-06-18) vs pyproject pin `fastmcp[apps,tasks]==4.1.4`; fastmcp-slim 4.1.4 carries the 2026-07-28 era |

**The pin is already correct — the venvs are stale.** No source change is required for the era; the fix is a venv sync inside the deploy, sequenced after the P0 /opt/geox reconciliation, with the suite run against 4.1.4 before the restart.

**Fixed on the site side (commit 842c614, live-verified):** the Observatory edge panel claimed
`3 directed · 0 observed · 3 declared overlays` while the kernel declares and probes 11 with
11/11 transport-reachable. It now reads the published aggregate:
`11 declared · 11 transport-reachable · 0 semantically proven · TRANSPORT_ALIGNED · 3 declared overlays · per-edge detail not published in public-state`.

Queue rows added: `p1-geox-mcp-era-2026-07-28-not-negotiated` ·
`p2-geox-federation-flow-routes-only-on-branch` ·
`p2-arifos-edge-list-not-published-and-0-of-11-semantically-proven` ·
`p2-observatory-live-renderer-ahead-of-repo`.
