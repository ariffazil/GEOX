# GEOX MCP Server Dockerfile
# Part of Option B Federation Architecture
# Service: geox-mcp (Earth Physics / Seismic)

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastmcp \
    uvicorn \
    starlette \
    pydantic \
    httpx

# Copy GEOX MCP server
COPY geox_mcp_server.py /app/
COPY arifos /app/arifos

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run server
CMD ["python", "geox_mcp_server.py", "--host", "0.0.0.0", "--port", "8081"]