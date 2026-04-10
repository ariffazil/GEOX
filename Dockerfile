# GEOX Earth Intelligence Core
# DITEMPA BUKAN DIBERI
# Version: v2026.04.10-EIC

FROM python:3.11-slim

LABEL maintainer="arifOS"
LABEL version="v2026.04.10-EIC"
LABEL seal="DITEMPA BUKAN DIBERI"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy canonical GEOX
COPY geox/ ./geox/
COPY data/ ./data/

# Create vault directory
RUN mkdir -p /app/999_vault

# Non-root user for security
RUN useradd -m -u 1000 geox && \
    chown -R geox:geox /app
USER geox

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Earth Intelligence Core
CMD ["python", "-m", "geox.server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
