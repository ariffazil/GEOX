FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY arifos ./arifos
COPY geox_mcp_server.py fastmcp.json ./

RUN uv pip install --system -e .

EXPOSE 8000

CMD ["python", "geox_mcp_server.py", "--transport", "http", "--port", "8000", "--host", "0.0.0.0"]