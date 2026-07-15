# Deploying GEOX

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `GEOX_SECRET_TOKEN` | **Yes** | — | Bearer token for `/mcp` auth |
| `PORT` | No | `8081` | Server port |
| `HOST` | No | `0.0.0.0` | Bind host |
| `GEOX_ENABLE_SCAFFOLD` | No | `false` | Set `"true"` to expose scaffold tools |

## Docker

```bash
# Build
docker build -t geox .

# Run
docker run -p 8081:8081 \
  -e GEOX_SECRET_TOKEN=your_token_here \
  -e PORT=8081 \
  -e GEOX_ENABLE_SCAFFOLD=false \
  geox
```

### Build Arguments

```bash
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  -t geox:latest .
```

## Railway (Recommended)

1. Connect `github.com/ariffazil/GEOX` to Railway
2. Add environment variable: `GEOX_SECRET_TOKEN=<your_token>`
3. Set start command: `python geox_mcp_server.py`
4. Push to `main` → auto-deploys

## Fly.io

```bash
fly launch --image geox:latest
fly secrets set GEOX_SECRET_TOKEN=your_token_here
fly deploy
```

## Render

1. Connect repo to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python geox_mcp_server.py`
4. Add `GEOX_SECRET_TOKEN` in environment variables

## Verify Deployment

```bash
# Health check
curl https://your-host/health

# MCP tools list (requires auth)
curl -X POST https://your-host/mcp \
  -H "Authorization: Bearer $GEOX_SECRET_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

Expected: `{"result":{"tools":[...18 tools...]}}`

## Health Endpoint

```
GET /health → {"status":"ok","seal":"DITEMPA BUKAN DIBERI","service":"geox-mcp"}
GET /ready  → {"status":"ready"}
GET /       → {"service":"GEOX MCP Server","version":"0.1.0",...}
```

Health and ready are **public** — no auth required.

## Transport

FastMCP 3.x Streamable HTTP v2 — mounted at `/mcp`.
Compatible with: Claude.ai, Cursor, Windsurf, Claude Desktop, any MCP client.

## Ports

- Default: `8081`
- Docker EXPOSE: `8081`
- Host bind: `0.0.0.0` (all interfaces)

## Security

Bearer token auth is **enabled by default** when `GEOX_SECRET_TOKEN` is set.
All `/mcp` calls require `Authorization: Bearer <token>`.
Health endpoints (`/health`, `/ready`, `/`) are public.
