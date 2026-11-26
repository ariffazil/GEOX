# ── GEOX GUI Microfrontend ────────────────────────────────────────────────────
# The Earth Witness Visual Mode
# DITEMPA BUKAN DIBERI
# v2026.04.10-EIC
#
# ── TOPOLOGY NOTE (2026-09-18, musyawawah audit) ──────────────────────────────
# This Dockerfile is COMPOSE-ONLY. The upstream proxy in nginx.conf points to
# http://geox_eic:8000, which assumes a docker-compose service named `geox_eic`
# listening on port 8000.
#
# PRODUCTION DEPLOYMENT does NOT use this Dockerfile. Live runtime:
#   - systemd unit:  geox-mcp.service
#   - listen addr:   127.0.0.1:8081
#   - reverse proxy: Caddy → Cloudflare → :8081
#   - static GUI:    served from /root/GEOX/static/gui/ at /static/gui/
#
# Do not rebuild & redeploy this Dockerfile expecting it to land on the live
# gateway — it will 502 because `geox_eic:8000` does not resolve in the
# non-compose runtime. For local dev / compose experiments only.
# ──────────────────────────────────────────────────────────────────────────────

# Build stage
FROM node:20-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine

# Copy built assets (includes apps via public/ folder)
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config for SPA with API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
