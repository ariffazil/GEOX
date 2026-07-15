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

# Install GEOX package + all deps into the venv
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .


# ── Stage 2: lean runtime ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime OS deps
# libgl1: OpenGL headless rendering backend (Debian trixie renamed libgl1-mesa-gl → libgl1)
# libpq5: asyncpg PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder — only the isolated packages, not the system Python
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source — only canonical surface, not archive/docs
COPY src/ ./src/
COPY resources/ ./resources/
COPY data/ ./data/
COPY fixtures/ ./fixtures/
COPY pyproject.toml entrypoint.sh ./

# Build-time git provenance (optional — enables test receipt commit binding)
ARG GIT_SHA=""
ARG GIT_DATE=""
ENV GIT_SHA=${GIT_SHA}
ENV GIT_DATE=${GIT_DATE}

# Production defaults
ENV PYTHONPATH=/app/src
ENV PORT=8081
ENV HOST=0.0.0.0

EXPOSE 8081

LABEL org.opencontainers.image.source="https://github.com/ariffazil/geox" \
      org.opencontainers.image.description="Earth intelligence — 31-tool geoscience surface" \
      org.opencontainers.image.version="v2.0.0-UNIFIED" \
      org.opencontainers.image.licenses="BSL-1.1" \
      arifos.organ="GEOX" \
      arifos.authority="EVIDENCE_ONLY"

CMD ["python", "-m", "geox_mcp.server"]
