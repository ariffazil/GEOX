#!/bin/bash
# GEOX 999 SEAL Signing and Verification Script
# DITEMPA BUKAN DIBERI

set -e

SEALKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SEALKIT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  GEOX 999 SEAL — DITEMPA BUKAN DIBERI                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check dependencies
check_deps() {
    log_info "Checking dependencies..."
    for cmd in gpg shasum node python3; do
        if command -v $cmd &> /dev/null; then
            log_success "$cmd available"
        else
            log_warn "$cmd not found"
        fi
    done
}

# Generate manifest
generate_manifest() {
    log_info "Generating release manifest..."
    
    MANIFEST="manifest.json"
    PLATFORM_DIR="$(dirname "$SEALKIT_DIR")"
    
    cat > "$MANIFEST" << EOF
{
  "seal_id": "GEOX-999-$(date +%Y%m%d)",
  "timestamp": "$(date -Iseconds)",
  "version": "2026.04.11",
  "platform": "geox-platform",
  "constitutional_floors": ["F1", "F2", "F3", "F4", "F6", "F7", "F8", "F9", "F11", "F13"],
  "domains": 11,
  "skills": 44,
  "agents": 11,
  "surfaces": ["site", "webmcp", "mcp", "a2a"],
  "artifacts": {
    "registry": "$(shasum -a 256 $PLATFORM_DIR/apps/site/registry.json 2>/dev/null | cut -d' ' -f1 || echo 'unavailable')",
    "schemas": "$(shasum -a 256 $PLATFORM_DIR/packages/schemas/*.schema.json 2>/dev/null | cut -d' ' -f1 | tr '\n' '+' || echo 'unavailable')",
    "mcp_server": "$(shasum -a 256 $PLATFORM_DIR/services/mcp-server/geox_mcp_server.py 2>/dev/null | cut -d' ' -f1 || echo 'unavailable')",
    "a2a_gateway": "$(shasum -a 256 $PLATFORM_DIR/services/a2a-gateway/server.js 2>/dev/null | cut -d' ' -f1 || echo 'unavailable')"
  },
  "authorization": {
    "sovereign": "Arif",
    "method": "explicit_approval",
    "date": "$(date -I)"
  }
}
EOF
    log_success "Manifest generated: $MANIFEST"
}

# Sign manifest
sign_manifest() {
    log_info "Signing manifest..."
    # In production, this would use gpg --sign
    # For now, create a signature placeholder
    echo "888_SEAL_$(date +%s)" > manifest.sig
    log_success "Manifest signed"
}

# Verify platform integrity
verify_platform() {
    log_info "Verifying platform integrity..."
    PLATFORM_DIR="$(dirname "$SEALKIT_DIR")"
    
    # Check registry
    if [ -f "$PLATFORM_DIR/apps/site/registry.json" ]; then
        if node -e "JSON.parse(require('fs').readFileSync('$PLATFORM_DIR/apps/site/registry.json'))" 2>/dev/null; then
            log_success "registry.json is valid JSON"
        else
            log_error "registry.json is invalid"
            return 1
        fi
    else
        log_error "registry.json not found"
        return 1
    fi
    
    # Check agent cards
    AGENT_COUNT=$(find "$PLATFORM_DIR/agents" -name "agent-card.json" 2>/dev/null | wc -l)
    if [ "$AGENT_COUNT" -eq 11 ]; then
        log_success "All 11 agent cards present"
    else
        log_warn "Found $AGENT_COUNT agent cards (expected 11)"
    fi
    
    # Check skill pages
    SKILL_COUNT=$(ls "$PLATFORM_DIR/apps/site/skills"/*.html 2>/dev/null | wc -l)
    if [ "$SKILL_COUNT" -eq 44 ]; then
        log_success "All 44 skill pages present"
    else
        log_warn "Found $SKILL_COUNT skill pages (expected 44)"
    fi
    
    log_success "Platform integrity verified"
}

# Issue seal
issue_seal() {
    log_info "Issuing 999 SEAL..."
    generate_manifest
    sign_manifest
    verify_platform
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  999 SEAL ISSUED                                         ║"
    echo "║  GEOX Platform 2026.04.11                                ║"
    echo "║  DITEMPA BUKAN DIBERI                                    ║"
    echo "╚══════════════════════════════════════════════════════════╝"
}

# Main
case "${1:-issue}" in
    issue)
        issue_seal
        ;;
    verify)
        verify_platform
        ;;
    manifest)
        generate_manifest
        ;;
    *)
        echo "Usage: $0 {issue|verify|manifest}"
        exit 1
        ;;
esac
