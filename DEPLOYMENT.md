# GEOX Deployment Runbook
> Version: 2.0.0-UNIFIED
> Seal: DITEMPA BUKAN DIBERI

## 1. Local Environment
1. Ensure Python 3.13 is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements-earth.txt
   ```
3. Set secret and ignite:
   ```bash
   export GEOX_SECRET_TOKEN="your_seal"
   python3 control_plane/fastmcp/server.py --port 8081
   ```

## 2. VPS Deployment (Docker/PM2)
The kernel should bind to `0.0.0.0` to allow proxy pass.

### PM2 Setup
```bash
pm2 start control_plane/fastmcp/server.py --name geox-kernel --interpreter python3 -- --port 8081
```

### Docker
Ensure `GEOX_SECRET_TOKEN` is passed via Docker Secrets or Environment.

## 3. Health Verification
After deployment, run these checks:
- `curl http://localhost:8081/health` -> Expect 200 `{status: "healthy"}`
- `curl http://localhost:8081/status` -> Expect 200 `{canonical_tools: 13, legacy_aliases: 40}`

## 4. Rollback Plan
If critical failure:
1. Re-point entrypoint to `archive/deprecated/geox_mcp_server.root.py`.
2. Revert `GEOX_VERSION` to `1.x`.

---
⬡ GEOX DEPLOYMENT SEALED ⬡
