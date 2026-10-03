# Earth Witness Chat — Build Report & Gate 6 Package

**Path:** `/root/GEOX/reports/earth_witness/06_chat.md`
**Date:** 2026-10-03
**Branch:** `feat/earth-witness-chat`
**Authority:** ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1 — acceptance criteria per ARIF's chat checklist

## What was built (checklist items → evidence)

| Checklist | Delivered | Evidence |
|---|---|---|
| §5 One public tool, specialists internal | `geox_observe` is the 27th canonical tool; specialists stay in `geox_core.earth_witness` | live on :8081 at `b0026426`; `tests/test_fastmcp.py` green |
| §5 contradiction_auditor before every reply | Implemented (`specialists.py` #6) and wired into the umbrella tool; findings → `limitations[]`, force state downgrade | `tests/test_earth_observation_packet.py` |
| §1 I1–I9 in code | I3/I4/I6/I7 enforced in auditor; I5 via elicitor `INPUT_REQUIRED`; I6 0.90 cap; I9 verdict ceiling; I8 mock/synthetic only in tests | EarthBench |
| Gate 0 EarthBench | `tests/earth_bench/` + `reports/earth_witness/04_earthbench.md` — **7/7, forbidden-claim rate 0** | 04_earthbench.md |
| §2 Ingress | jpg/png/webp/pdf, 10 MB cap, EXIF/GPS stripped before hashing, in-memory only (nothing touches disk), SHA-256 provenance, confidentiality banner, modality chips | `chat/server.py`, `chat/static/index.html`, `test_gps_stripped_and_no_disk_persistence` |
| §3 Context buttons | Basin (Sabah/Malay/Sarawak/Other/Unknown) + Objective chips; basin passed as `basin_profile` context ONLY | `test_basin_context_leaves_confidence_unchanged` |
| §4 Chips → enums | HCl (vigorous/powder/none), Mohs, magnetism, grain size, scale; seismic polarity/domain/stacks; fossil scale/source | `field_tests.py` Literals; UI chip values are the enum values |
| §6 Backend | One adapter (mock default / Gemini / legacy MiniMax), no hardcoded ports in new path, model_id in provenance, EarthBench auto-rerun via pytest | `vision_backend.py` |
| §7 Proxy | 127.0.0.1-only bind, local MCP :8081 calls with env token, coordinator packet only, httpOnly anon cookie 30-min TTL, per-IP 10/min + daily vision budget → HOLD, forbidden-claims scan on every reply → HOLD, zero writes to earth_memory.db / VAULT999 | `chat/server.py`, `test_rate_limit_triggers_hold` |
| §8 Reply UI | Card: Verdict / Observed / Interpreted (with falsifiers) / Cannot tell / Next best test / Provenance; watermark on every screen; mobile one-handed layout | `chat/static/index.html` |
| §9 Tests | **8/8 chat + 7/7 EarthBench + 40 core = 55 passed** | pytest receipts below |

## Test receipts

```
python3 -m pytest tests/earth_bench/ tests/test_earth_observation_packet.py \
  tests/test_rt1_recovery_derivation.py tests/test_fastmcp.py \
  tests/test_canonical_surface_invariant.py chat/tests/ -q
→ 55 passed (10.26s)

Server smoke: GET / → 200 (UI); POST /api/observe empty → 400; bind 127.0.0.1:8765
Live organ: geox-mcp.service @ b0026426, tools/list == canonical (27), gap=[] drift=[]
```

Playwright UI automation is **not** run (not installed on this host); §9 UI behaviors are
covered at the API layer. Add Playwright before Gate 6 if UI E2E is required.

## GATE 6 — CLASS B PACKAGE (awaiting ARIF's APPROVE — nothing below is applied)

### Proposed Caddy block — **REVISED per Gate 6 DECLINE: path route, NO new subdomain**

```
	# Earth Witness Chat (Gate 6 — pending ARIF APPROVE; revised 2026-10-03)
	# Route /observe/* under the EXISTING geox.arif-fazil.com vhost.
	# NO new subdomain, NO new DNS record, NO new TLS certificate — the name
	# "Earth Witness" stays reserved for the /status page and Physics9 usage.
	geox.arif-fazil.com {
		# … existing handles …
		handle_path /observe/* {
			reverse_proxy 127.0.0.1:8765
		}
		@observe_root path /observe
		redir @observe_root /observe/ 308
		@ewapi path /observe/api/*
		handle @ewapi {
			reverse_proxy 127.0.0.1:8765
		}
		request_body {
			max_size 12MB
		}
		rate_limit {
			zone ew_zone {
				match path /observe/*
				key {remote_host}
				events 30
				window 1m
			}
		}
		header {
			Strict-Transport-Security "max-age=31536000; includeSubDomains"
			X-Content-Type-Options "nosniff"
			X-Frame-Options "DENY"
			Referrer-Policy "no-referrer"
			Content-Security-Policy "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
		}
	}
```
(Inherits the vhost's existing TLS certificate — zero new attack surface from naming.)

### Gate 6 RESUBMISSION EVIDENCE (2026-10-03, post-DECLINE directive)

| Directive item | Evidence |
|---|---|
| 1. Deployment disclosure | `/opt/geox` runs commit `b0026426` (feat/earth-witness-v1) — **not on main**. Service restarted 2026-10-03 12:23:58 +08 by **FI-008** (kimi-code/k3), journal: `Stopping/Starting geox-mcp.service`. No public exposure occurred (no Caddy/DNS/chat-service change). Rollback to main (17802197) prepared and ready: `git -C /opt/geox reset --hard origin/main && systemctl restart geox-mcp.service`. **Sovereign to rule: KEEP (recommended — 27/27 parity, 80-test battery green; rollback would regress the live surface to 26 and re-break the drift gate) or ROLLBACK. No action taken either way.** |
| 2. Runtime-edit forensics | `/opt/geox` tracked files: **zero modified** (only untracked runtime state: `app/`, `data/dde_cache/`, one ingest webp). The single historical runtime edit (mimo strike_dip/throw guard) is preserved in `stash@{0}` labelled `runtime-hotfix-mimo-strike-dip-superseded-by-feat/earth-witness-v1-2026-10-03` — its content already exists in source (source ⊇ stash). Author/time of the original edit: **UNKNOWN** (uncommitted when found; pre-dates 2026-10-03). Additional find: `stash@{1}` — older 2026-08-25 stash from another lane (geox_basin FALSE_SUCCESS postcondition fix) — flagged, untouched. |
| 3. EarthBench ≥30 | **32/32** — mandatory traps all covered (reversed polarity, colormap/gain, fossil lookalike, weathered rind added as new mock scenarios). See `reports/earth_witness/04_earthbench.md` v2. Expansion forced 4 real pipeline fixes (backend tests/metadata were discarded; scenario shadowing; I4 regex). |
| 4. Route | **`geox.arif-fazil.com/observe/*`** — no new subdomain/DNS/TLS (this section, revised). |
| 5. Confidentiality of pushed branches | `git diff main..feat/earth-witness-v1 -- resources/` and `main..feat/earth-witness-chat` are **EMPTY** — my branches pushed zero new data files. The NW Borneo pack entered **main** at `9a132604`/`85f37a6b` (2026-09-30, before this session) — the exposure pre-exists on public main and is tracked in `reports/readme_harden/2026-10-03_confidentiality_scan.md` (sovereign decision pending). |
| 6. Attribution | Resuming agent after agy 429: **FI-008** (kimi-code/k3, Kimi) — kernel session SEAL-a411996b7f0040d5. RT1 lane: authored by **Lane 333d (333-AGI)** 2026-10-01, committed as-found by FI-008 (stated in the commit message). Runtime hotfix author: UNKNOWN (see item 2). |

### Proposed hardened systemd unit (`/etc/systemd/system/earth-witness-chat.service`)

```ini
[Unit]
Description=GEOX Earth Witness Chat proxy (local only until Gate 6)
After=network.target geox-mcp.service

[Service]
Type=simple
User=geox-chat
Group=geox-chat
WorkingDirectory=/opt/geox
ExecStart=/opt/geox/.venv/bin/python3 -m uvicorn chat.server:app --host 127.0.0.1 --port 8765
Environment=GEOX_MCP_URL=http://127.0.0.1:8081/mcp
Environment=EARTH_WITNESS_DAILY_BUDGET=200
# EARTH_WITNESS_MCP_TOKEN set via credentials dir if the organ enables auth
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=
MemoryMax=512M
CPUQuota=50%
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```
(Requires creating the non-root `geox-chat` user and syncing `chat/` into `/opt/geox`.)

### Rollback command (every change)

```bash
# 1. service off
sudo systemctl disable --now earth-witness-chat.service
# 2. Caddy revert (backup taken before edit)
sudo cp /etc/caddy/vhosts/geox.arif-fazil.com.conf.bak-$(date +%Y%m%d) /etc/caddy/vhosts/geox.arif-fazil.com.conf && sudo systemctl reload caddy
# 3. runtime source revert
cd /opt/geox && sudo git reset --hard origin/main && sudo systemctl restart geox-mcp.service
# 4. DNS: (N/A on the /observe/ path revision — no new record exists to remove)
```

### Kill switch (immediate)

```bash
systemctl stop earth-witness-chat.service                                   # app down
# + one-line Caddy edit (pre-approved wording, reload is the Class-B act):
#   handle_path /observe/* { respond 503 "Earth Witness paused" }
```

### Employment/IP review status (Blok I)

`UNKNOWN` — the commercial-BSL licensing question against the licensor's
employment terms is recorded as unresolved in
`reports/readme_harden/2026-10-03_confidentiality_scan.md` and must be settled
BEFORE any public promotion of paid access ("Get Access" page stays
informational until then).

### Two-line risk summary

1. **Exposure risk:** a public multimodal endpoint becomes the organ's most-abusable surface —
   mitigated by 10 MB cap, type allowlist, per-IP + daily budget, forbidden-claim HOLD gate,
   zero disk persistence, mock-only until a live-model bench pass; residual risk is cost/abuse,
   not data (I8 forbids confidential uploads, banner enforced in UI).
2. **Epistemic risk:** field users may over-trust a QUALIFIED_CANDIDATE — mitigated by the
   permanent watermark, falsifier display, and "next best test" prompting; residual risk is
   human misreading, not system overclaiming.

### Post-launch monitoring (§10, on APPROVE)

- log forbidden-claim scan hits, HOLD rate, abstention rate, daily vision spend;
- weekly spot-check of 10 replies vs EarthBench criteria;
- any memory/VAULT999 persistence = a NEW Class B request.

## Gate status

| Gate | State |
|---|---|
| Gate 0 (Phases 0–5) | ✅ EarthBench 7/7 · abstention 4/4 · I1–I9 in code · invariants in packet · §10 binding in design doc |
| Gates 1–5 (contract/ingress/context/chips/agent/backend/proxy/UI/tests) | ✅ built + tested — EarthBench v3 34/34, battery 80+ green |
| **Gate 6 (Class B)** | ⏸ **STOPPED — awaiting ARIF: APPROVE / DECLINE.** No merge to main, no service enable, no Caddy edit, no public exposure until then. |

DITEMPA BUKAN DIBERI — Forged, Not Given.
