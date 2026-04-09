# ── GEOX MCP Server ───────────────────────────────────────────────────────────
# Geospatial earth-witness co-agent for arifOS Trinity Architecture
# DITEMPA BUKAN DIBERI [ΔΩΨ | ARIF]
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .
COPY geox_mcp_server.py .
COPY arifos/ arifos/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir ".[apps]" && \
    pip install --no-cache-dir numpy prefab-ui


FROM python:3.12-slim AS runtime

RUN groupadd -g 1000 arifos && \
    useradd -u 1000 -g arifos -m -s /bin/bash arifos

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local /usr/local
COPY --from=build /build /app

RUN mkdir -p /app/data && chown -R arifos:arifos /app

USER arifos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS --max-time 3 http://localhost:8000/health || exit 1

CMD ["python", "geox_mcp_server.py", "--transport", "http", "--port", "8000", "--host", "0.0.0.0"]
