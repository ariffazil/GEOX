# ── GEOX GUI Microfrontend ────────────────────────────────────────────────────
# The Earth Witness Visual Mode
# DITEMPA BUKAN DIBERI
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

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Default Nginx config (supports SPA routing)
RUN printf "server {\n  listen 80;\n  location / {\n    root /usr/share/nginx/html;\n    index index.html;\n    try_files \$uri \$uri/ /index.html;\n  }\n}\n" > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
