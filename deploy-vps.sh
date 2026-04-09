#!/bin/bash
# GEOX VPS Deployment Script
# DITEMPA BUKAN DIBERI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_HOST="srv1325122.hstgr.cloud"
VPS_USER="root"
DEPLOY_DIR="/opt/arifos/geox"
REPO_URL="https://github.com/ariffazil/arifos-geox.git"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  GEOX Earth Witness — VPS Deployment${NC}"
echo -e "${BLUE}  DITEMPA BUKAN DIBERI${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to run command on VPS
run_on_vps() {
    ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} "$1"
}

# Step 1: Check VPS connectivity
echo -e "${YELLOW}Step 1: Checking VPS connectivity...${NC}"
if ! run_on_vps "echo 'VPS is reachable'" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to VPS${NC}"
    exit 1
fi
echo -e "${GREEN}✓ VPS is reachable${NC}"

# Step 2: Clone or update repository
echo -e "${YELLOW}Step 2: Updating code on VPS...${NC}"
run_on_vps "
    if [ -d ${DEPLOY_DIR} ]; then
        cd ${DEPLOY_DIR}
        git pull origin main
    else
        mkdir -p ${DEPLOY_DIR}
        git clone ${REPO_URL} ${DEPLOY_DIR}
    fi
"
echo -e "${GREEN}✓ Code updated${NC}"

# Step 3: Build and deploy
echo -e "${YELLOW}Step 3: Building and deploying...${NC}"
run_on_vps "
    cd ${DEPLOY_DIR}
    
    # Stop existing container
    docker compose down geox_server 2>/dev/null || true
    
    # Build new image
    docker compose build --no-cache geox_server
    
    # Start services
    docker compose up -d geox_server
    
    # Clean up old images
    docker image prune -f
"
echo -e "${GREEN}✓ Deployment complete${NC}"

# Step 4: Health check
echo -e "${YELLOW}Step 4: Health check...${NC}"
sleep 5

HEALTH_STATUS=$(run_on_vps "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || echo '000'")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (status: ${HEALTH_STATUS})${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    run_on_vps "cd ${DEPLOY_DIR} && docker compose logs --tail=50 geox_server"
    exit 1
fi

# Step 5: Verify endpoints
echo -e "${YELLOW}Step 5: Verifying endpoints...${NC}"
echo ""
echo "  Health:"
run_on_vps "curl -s http://localhost:8000/health | head -c 100"
echo ""
echo ""
echo "  Details:"
run_on_vps "curl -s http://localhost:8000/health/details | head -c 200"
echo ""

# Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deployment Successful!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  URLs:"
echo "    • Health:     https://geox.arif-fazil.com/health"
echo "    • Details:    https://geox.arif-fazil.com/health/details"
echo "    • MCP:        https://geox.arif-fazil.com/mcp"
echo ""
echo "  Horizon (FastMCP Cloud):"
echo "    • https://geoxarifOS.fastmcp.app/mcp"
echo ""
echo "  Commands:"
echo "    • Logs:     ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose logs -f geox_server'"
echo "    • Restart:  ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose restart geox_server'"
echo "    • Stop:     ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose down geox_server'"
echo ""
echo -e "${BLUE}DITEMPA BUKAN DIBERI${NC}"
