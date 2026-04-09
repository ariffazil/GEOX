#!/bin/bash
# GEOX VPS Deployment Script
# DITEMPA BUKAN DIBERI
#
# Usage: ./deploy-vps.sh
# Deploys GEOX MCP server to production VPS at geox.arif-fazil.com

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "GEOX Earth Witness — VPS Deployment"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Configuration
VPS_HOST="srv1325122.hstgr.cloud"
VPS_USER="root"
DEPLOY_DIR="/opt/arifos/geox"
DOMAIN="geox.arif-fazil.com"

echo "Step 1: Building Docker image locally..."
docker build -t geox:latest .

echo ""
echo "Step 2: Pushing to VPS..."
# Save and transfer image
docker save geox:latest | ssh ${VPS_USER}@${VPS_HOST} "docker load"

echo ""
echo "Step 3: Deploying on VPS..."
ssh ${VPS_USER}@${VPS_HOST} << EOF
  mkdir -p ${DEPLOY_DIR}
  cd ${DEPLOY_DIR}
  
  # Pull latest code
  if [ -d ".git" ]; then
    git pull origin main
  else
    git clone https://github.com/ariffazil/GEOX.git .
  fi
  
  # Ensure Traefik network exists
  docker network create traefik_network 2>/dev/null || true
  
  # Stop existing container
  docker compose down geox_server 2>/dev/null || true
  
  # Start with new image
  docker compose up -d geox_server
  
  # Wait for health check
  echo "Waiting for health check..."
  sleep 10
  
  # Verify deployment
  echo ""
  echo "Health check:"
  curl -s http://localhost:8000/health || echo "Health check failed"
  
  echo ""
  echo "Server info:"
  curl -s http://localhost:8000/health/details 2>/dev/null | head -20 || echo "Details unavailable"
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Deployment Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Endpoints:"
echo "  Health:  https://${DOMAIN}/health"
echo "  Details: https://${DOMAIN}/health/details"
echo "  MCP:     https://${DOMAIN}/mcp"
echo ""
echo "Test with:"
echo "  curl https://${DOMAIN}/health"
echo "  fastmcp list https://${DOMAIN}/mcp"
echo ""
echo "DITEMPA BUKAN DIBERI — 999 SEAL ALIVE"
