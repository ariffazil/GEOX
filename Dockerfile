# ── GEOX Earth Intelligence — Multi-Stage Build ───────────────────────────
# Stage 1: build venv with all dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create venv so pip packages are isolated from system Python
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install all deps into the venv
COPY requirements.txt requirements-earth.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# ── Stage 2: lean runtime ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder — only the isolated packages, not the system Python
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source — only canonical surface, not archive/docs
COPY src/ ./src/
COPY resources/ ./resources/
COPY data/ ./data/
COPY fixtures/ ./fixtures/
COPY pyproject.toml requirements.txt requirements-earth.txt ./
COPY entrypoint.sh ./

# Production defaults
ENV PYTHONPATH=/app/src
ENV PORT=8081
ENV HOST=0.0.0.0

EXPOSE 8081

CMD ["python", "-m", "geox_mcp.server"]
