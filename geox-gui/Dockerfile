# ── GEOX GUI Microfrontend ────────────────────────────────────────────────────
# The Earth Witness Visual Mode
# DITEMPA BUKAN DIBERI
# v2026.04.10-EIC
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
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    location /health { \
        proxy_pass http://geox_eic:8000/health; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
    location /mcp { \
        proxy_pass http://geox_eic:8000/mcp; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header Connection ""; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
