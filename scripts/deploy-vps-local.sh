#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Autonomous VPS Deploy (Local) — Earth coprocessor deployment
#
# Purpose: Build, push, and deploy GEOX image on the federation VPS.
#          This is the LOCAL variant — for remote VPS deployment see deploy-vps.sh.
#
# Flow:
#   1. Get current commit SHA
#   2. Check if ghcr.io/ariffazil/geox:<sha> already exists
#   3. If missing → build locally → push to GHCR
#   4. Update /root/compose/docker-compose.yml image pin
#   5. Restart container
#   6. Verify health
#
# Usage:
#   ./scripts/deploy-vps-local.sh           # full deploy
#   ./scripts/deploy-vps-local.sh --check   # only check if image exists
#
# DITEMPA BUKAN DIBERI — Forged, Not Given
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

REPO_NAME="geox"
IMAGE_BASE="ghcr.io/ariffazil/geox"
COMPOSE_FILE="/root/compose/docker-compose.yml"
CONTAINER_NAME="geox_eic"
COMPOSE_SERVICE="geox"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── 1. Get current commit SHA ────────────────────────────────────────────────
SHORT_SHA=$(git rev-parse --short HEAD)
FULL_SHA=$(git rev-parse HEAD)
log_info "Deploying GEOX commit: $SHORT_SHA"

# ── 2. Check if image already exists on GHCR ─────────────────────────────────
log_info "Checking GHCR for image: $IMAGE_BASE:$SHORT_SHA"
if docker manifest inspect "$IMAGE_BASE:$SHORT_SHA" >/dev/null 2>&1; then
    log_info "Image already exists on GHCR — skipping build"
    NEED_BUILD=false
else
    log_warn "Image not found on GHCR — local build required"
    NEED_BUILD=true
fi

# ── --check mode: exit after check ───────────────────────────────────────────
if [[ "${1:-}" == "--check" ]]; then
    if $NEED_BUILD; then
        log_warn "Image missing — run without --check to build and deploy"
        exit 1
    else
        log_info "Image present — no action needed"
        exit 0
    fi
fi

# ── 3. Build and push if needed ──────────────────────────────────────────────
if $NEED_BUILD; then
    log_info "Building GEOX image locally..."
    docker build -t "$IMAGE_BASE:$SHORT_SHA" -t "$IMAGE_BASE:latest" .

    # Ensure GHCR login (uses gh CLI token if available)
    if command -v yq >/dev/null 2>&1 && [[ -f ~/.config/gh/hosts.yml ]]; then
        GH_TOKEN=$(yq '.["github.com"].oauth_token' ~/.config/gh/hosts.yml)
        echo "$GH_TOKEN" | docker login ghcr.io -u ariffazil --password-stdin
    elif [[ -n "${GITHUB_TOKEN:-}" ]]; then
        echo "$GITHUB_TOKEN" | docker login ghcr.io -u ariffazil --password-stdin
    else
        log_error "No GHCR credentials found. Run: gh auth login"
        exit 1
    fi

    log_info "Pushing to GHCR..."
    docker push "$IMAGE_BASE:$SHORT_SHA"
    docker push "$IMAGE_BASE:latest"
    log_info "Push complete"
fi

# ── 4. Update compose pin ────────────────────────────────────────────────────
if [[ -f "$COMPOSE_FILE" ]]; then
    CURRENT_PIN=$(grep -E "^\s+image:\s+$IMAGE_BASE:" "$COMPOSE_FILE" | awk '{print $2}' || true)
    NEW_PIN="$IMAGE_BASE:$SHORT_SHA"

    if [[ "$CURRENT_PIN" != "$NEW_PIN" ]]; then
        log_info "Updating compose pin: $CURRENT_PIN → $NEW_PIN"
        sed -i "s|image: $IMAGE_BASE:[a-z0-9_-]*|image: $NEW_PIN|" "$COMPOSE_FILE"
    else
        log_info "Compose pin already correct"
    fi
else
    log_warn "Compose file not found at $COMPOSE_FILE"
fi

# ── 5. Restart container ─────────────────────────────────────────────────────
log_info "Restarting $CONTAINER_NAME container..."
cd /root/compose

# Stop and remove old container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

docker compose up -d --no-deps "$COMPOSE_SERVICE"

# ── 6. Health check ──────────────────────────────────────────────────────────
log_info "Waiting for health check..."
for i in {1..30}; do
    if curl -sf http://localhost:8081/health \
        -H "Content-Type: application/json" >/dev/null 2>&1; then
        log_info "GEOX is healthy and responding on port 8081"
        break
    fi
    if [[ $i -eq 30 ]]; then
        log_error "GEOX failed health check after 30 seconds"
        exit 1
    fi
    sleep 1
done

log_info "═══════════════════════════════════════════════════════════════════════════════"
log_info "GEOX deploy complete: $SHORT_SHA"
log_info "Image: $IMAGE_BASE:$SHORT_SHA"
log_info "═══════════════════════════════════════════════════════════════════════════════"
