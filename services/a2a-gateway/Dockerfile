FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY services/a2a-gateway/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# Copy server
COPY services/a2a-gateway/server.js .

# Copy agent cards from the Level 4 skills tree
COPY skills ./skills

EXPOSE 3002

CMD ["node", "server.js"]
