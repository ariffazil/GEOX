FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Production defaults
ENV PYTHONPATH=/app
ENV PORT=8081
ENV HOST=0.0.0.0

EXPOSE 8081

CMD ["python", "geox_mcp_server.py"]
