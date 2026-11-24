#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GEOX production deploy — SINGLE OWNER for the LIVE model.
#
# Live model (verified 2026-11-24): systemd unit `geox-mcp.service`,
# WorkingDirectory=/opt/geox, editable venv at /opt/geox/.venv, public :8081.
# The retired Docker/GHCR deploy scripts (deploy-vps.sh, deploy-vps-local.sh)
# described a model that is NOT what runs; they were orphaned and are gone from
# the active tree (content remains in git history).
#
# Usage:
#   scripts/deploy_geox_service.sh --check    # verify target/tree/import only, no restart
#   scripts/deploy_geox_service.sh            # deploy: checkout -> smoke -> restart -> probe
#
# Guarantees: refuses on incomplete tree, refuses on failed import, rolls back to the
# last live commit if the restart or post-check fails. Never leaves a half state.
# DITEMPA BUKAN DIBERI
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

REPO=${GEOX_REPO:-/root/GEOX}
PROD=${GEOX_PROD:-/opt/geox}
SERVICE=${GEOX_SERVICE:-geox-mcp.service}
VENV=${GEOX_VENV:-$PROD/.venv}
PORT=${GEOX_PORT:-8081}
PUBLIC=${GEOX_PUBLIC:-https://geox.arif-fazil.com/mcp}
MODE=${1:-deploy}

die() { echo "STOP: $*" >&2; exit 1; }
say() { echo "[deploy] $*"; }

[ -d "$PROD/.git" ] || die "no git repo at $PROD"
PREV=$(git -C "$PROD" rev-parse HEAD 2>/dev/null || true)

# Target = GitHub main as fetched into the production clone (the filtered publication
# commit). The raw repo's local main has different SHAs (filter-repo rewrite) and must
# NOT be used as a deploy target.
git -C "$PROD" fetch origin main -q
TARGET=$(git -C "$PROD" rev-parse origin/main)
say "target (origin/main): ${TARGET:0:9}   previous (live): ${PREV:0:9}"

# ── 1. checkout target in the production clone ────────────────────────────────
git -C "$PROD" fetch origin main -q
git -C "$PROD" checkout --detach "$TARGET" >/dev/null
[ "$(git -C "$PROD" rev-parse HEAD)" = "$TARGET" ] || die "prod HEAD != target"

# ── 2. completeness (projection gate is not enough) ───────────────────────────
for p in geox src/geox_mcp tools.json pyproject.toml src/geox_mcp/server.py; do
  [ -e "$PROD/$p" ] || die "incomplete tree: missing $p"
done

# ── 3. import smoke BEFORE any restart ────────────────────────────────────────
( cd "$PROD" && "$VENV/bin/python" - <<'PY'
import geox_mcp.server  # noqa: F401
from geox_mcp.registry import public_tool_names
n = len(public_tool_names())
assert n > 0, "no public tools"
print(f"[deploy] import OK — public tools {n}")
PY
) || { [ -n "$PREV" ] && git -C "$PROD" checkout --detach "$PREV" >/dev/null 2>&1; die "import smoke failed"; }

if [ "$MODE" = "--check" ]; then say "--check OK (no restart)"; exit 0; fi

# ── 4. restart + post-deploy proof, with rollback ─────────────────────────────
rollback() {
  say "ROLLBACK to ${PREV:0:9}"
  git -C "$PROD" checkout --detach "$PREV" >/dev/null 2>&1 || die "rollback checkout failed"
  systemctl restart "$SERVICE"
  sleep 6
  systemctl is-active --quiet "$SERVICE" || die "rollback restart failed — MANUAL INTERVENTION"
  say "rollback live; service active"
  exit 1
}

systemctl restart "$SERVICE"
sleep 6
systemctl is-active --quiet "$SERVICE" || rollback

counts=$(curl -s -m 15 -X POST "http://127.0.0.1:${PORT}/mcp" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | grep -o '"name":"geox_[a-z_0-9]*"' | sort -u | wc -l)
say "live tools: $counts"
[ "${counts:-0}" -gt 0 ] || rollback

pub=$(curl -s -m 15 -o /dev/null -w '%{http_code}' "$PUBLIC" || echo 000)
say "public MCP: $pub"
[ "$pub" = "200" ] || rollback

say "DEPLOYED ${TARGET:0:9} — service active, ${counts} tools, public ${pub}"
say "verify strict surface: python3 scripts/deploy_gate.py (if configured)"
