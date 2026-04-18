FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy server
COPY server.js .

# Copy agent cards
COPY agents ./agents

EXPOSE 3002

CMD ["node", "server.js"]
