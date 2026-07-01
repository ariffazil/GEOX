"""
server.py — Unified arifOS MCP compatibility proxy for Copilot / agent clients.

Purpose
-------
Provide a small, portable HTTP server that:
1) exposes a stable discovery surface for arifOS MCP,
2) forwards MCP traffic to an upstream arifOS MCP endpoint,
3) rewrites legacy alias tool names (e.g. arifos_init) to runtime names
   (e.g. arif_session_init) before forwarding.

Why this file exists
--------------------
Your enterprise files show two naming surfaces for arifOS tools:
- Canonical / runtime tool names such as arif_session_init, arif_sense_observe,
  arif_evidence_fetch, ..., arif_vault_seal.
- Legacy / compatibility names such as arifos_init, arifos_sense, arifos_fetch,
  ..., arifos_vault.

This proxy gives Copilot/agent clients one endpoint they can discover and call
without needing to care which surface the upstream server currently expects.

Environment variables
---------------------
ARIFOS_UPSTREAM_URL      Upstream MCP URL. Default: https://arifos.arif-fazil.com/mcp
ARIFOS_PUBLIC_BASE_URL   Public URL of *this* proxy (used in manifest generation)
ARIFOS_PROXY_TITLE       Friendly service name
ARIFOS_TIMEOUT_SECONDS   Upstream HTTP timeout (default: 30)
ARIFOS_ALLOW_ORIGINS     Comma-separated CORS origins; '*' allowed
ARIFOS_LOG_LEVEL         DEBUG|INFO|WARNING|ERROR
PORT                     Local bind port when run directly (default: 8088)

Run
---
pip install fastapi uvicorn httpx
python server.py

Then point your Copilot / agent host at:
- /.well-known/mcp/server.json   (discovery)
- /mcp                           (proxy transport)
- /compat/tools                  (alias map / inventory)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
UPSTREAM_URL = os.getenv("ARIFOS_UPSTREAM_URL", "https://arifos.arif-fazil.com/mcp")
PUBLIC_BASE_URL = os.getenv("ARIFOS_PUBLIC_BASE_URL", "").rstrip("/")
PROXY_TITLE = os.getenv("ARIFOS_PROXY_TITLE", "arifOS MCP Unified Compatibility Proxy")
TIMEOUT_SECONDS = float(os.getenv("ARIFOS_TIMEOUT_SECONDS", "30"))
ALLOW_ORIGINS_RAW = os.getenv("ARIFOS_ALLOW_ORIGINS", "*")
LOG_LEVEL = os.getenv("ARIFOS_LOG_LEVEL", "INFO").upper()
PORT = int(os.getenv("PORT", "8088"))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("arifos_compat_proxy")

# ---------------------------------------------------------------------------
# arifOS tool inventory (built from enterprise files)
# ---------------------------------------------------------------------------
RUNTIME_TOOLS: list[dict[str, Any]] = [
    {
        "name": "arif_session_init",
        "description": "000_INIT: Session bootstrap + identity binding.",
        "access": "public",
        "aliases": ["arifos_init"],
    },
    {
        "name": "arif_sense_observe",
        "description": "111_SENSE: Reality-grounded observation.",
        "access": "public",
        "aliases": ["arifos_sense"],
    },
    {
        "name": "arif_evidence_fetch",
        "description": "222_FETCH: Evidence-preserving web ingestion.",
        "access": "public",
        "aliases": ["arifos_fetch"],
    },
    {
        "name": "arif_mind_reason",
        "description": "333_MIND: Inductive reasoning engine.",
        "access": "public",
        "aliases": ["arifos_mind"],
    },
    {
        "name": "arif_kernel_route",
        "description": "444_KERNEL: Kernel syscall and telemetry / route dispatcher.",
        "access": "public",
        "aliases": ["arifos_kernel", "arifos_route"],
    },
    {
        "name": "arif_reply_compose",
        "description": "444r_REPLY: Governed response compositor.",
        "access": "public",
        "aliases": ["arifos_reply"],
    },
    {
        "name": "arif_memory_recall",
        "description": "555_MEMORY: Vector memory and context retrieval.",
        "access": "public",
        "aliases": ["arifos_memory"],
    },
    {
        "name": "arif_heart_critique",
        "description": "666_HEART: Safety, empathy, consequence modelling.",
        "access": "authenticated",
        "aliases": ["arifos_heart"],
    },
    {
        "name": "arif_gateway_connect",
        "description": "666g_GATEWAY: Cross-agent routing / A2A federation.",
        "access": "authenticated",
        "aliases": ["arifos_gateway"],
    },
    {
        "name": "arif_ops_measure",
        "description": "777_OPS: Operations and economic thermodynamics.",
        "access": "public",
        "aliases": ["arifos_ops"],
    },
    {
        "name": "arif_judge_deliberate",
        "description": "888_JUDGE: Constitutional verdict engine.",
        "access": "authenticated",
        "aliases": ["arifos_judge"],
    },
    {
        "name": "arif_forge_execute",
        "description": "010_FORGE: Execution substrate dispatch.",
        "access": "sovereign",
        "aliases": ["arifos_forge"],
    },
    {
        "name": "arif_vault_seal",
        "description": "999_VAULT: Immutable ledger / seal.",
        "access": "authenticated",
        "aliases": ["arifos_vault"],
    },
    {
        "name": "mcp_health_check",
        "description": "Compatibility health tool exposed by some live deployments.",
        "access": "public",
        "aliases": ["arifos_health"],
        "optional": True,
    },
]

ALIAS_TO_RUNTIME: dict[str, str] = {}
for tool in RUNTIME_TOOLS:
    name = tool["name"]
    ALIAS_TO_RUNTIME[name] = name
    for alias in tool.get("aliases", []):
        ALIAS_TO_RUNTIME[alias] = name


def _public_base_from_request(request: Request) -> str:
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    return f"{proto}://{host}".rstrip("/")


def _manifest_payload(request: Request) -> dict[str, Any]:
    base = _public_base_from_request(request)
    return {
        "name": PROXY_TITLE,
        "description": (
            "Compatibility proxy for arifOS MCP. Forwards MCP traffic to the upstream arifOS "
            "endpoint and rewrites legacy alias tool names to runtime tool names."
        ),
        "protocolVersion": "2025-03-26",
        "url": f"{base}/mcp",
        "toolsEndpoint": f"{base}/compat/tools",
        "healthEndpoint": f"{base}/health",
        "metadata": {
            "upstream": UPSTREAM_URL,
            "runtimeToolCount": len([t for t in RUNTIME_TOOLS if not t.get("optional")]),
            "compatibilityToolCount": len(RUNTIME_TOOLS),
            "supportsAliasRewrite": True,
        },
    }


def _normalise_tool_name(name: str) -> str:
    return ALIAS_TO_RUNTIME.get(name, name)


def _rewrite_payload_for_aliases(payload: Any) -> Any:
    """Rewrite known alias tool names inside JSON-RPC payloads.

    Handles common MCP JSON-RPC shapes such as:
    - {"method": "tools/call", "params": {"name": "arifos_init", ...}}
    - batch requests (list[dict])
    """
    if isinstance(payload, list):
        return [_rewrite_payload_for_aliases(item) for item in payload]

    if not isinstance(payload, dict):
        return payload

    rewritten = dict(payload)
    method = rewritten.get("method")
    params = rewritten.get("params")

    if method in {"tools/call", "tool/call"} and isinstance(params, dict):
        params = dict(params)
        name = params.get("name")
        if isinstance(name, str):
            rewritten_name = _normalise_tool_name(name)
            if rewritten_name != name:
                logger.info("Rewriting tool alias '%s' -> '%s'", name, rewritten_name)
                params["name"] = rewritten_name
        rewritten["params"] = params

    return rewritten


async def _forward_request(request: Request, target_url: str) -> Response:
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    raw_body = await request.body()
    content = raw_body

    content_type = request.headers.get("content-type", "")
    if raw_body and "application/json" in content_type.lower():
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            payload = _rewrite_payload_for_aliases(payload)
            content = json.dumps(payload).encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse/normalise JSON payload; forwarding unchanged: %s", exc)
            content = raw_body

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                params=dict(request.query_params),
                headers=headers,
                content=content,
            )
        except httpx.RequestError as exc:  # noqa: PERF203
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in {"content-length", "transfer-encoding", "connection", "content-encoding"}
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title=PROXY_TITLE, version="2026.04.30-compat")

allow_origins = [origin.strip() for origin in ALLOW_ORIGINS_RAW.split(",") if origin.strip()]
if not allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root(request: Request) -> dict[str, Any]:
    base = _public_base_from_request(request)
    return {
        "service": PROXY_TITLE,
        "mode": "compatibility-proxy",
        "upstream": UPSTREAM_URL,
        "discovery": f"{base}/.well-known/mcp/server.json",
        "mcp": f"{base}/mcp",
        "compat_tools": f"{base}/compat/tools",
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    timeout = httpx.Timeout(min(TIMEOUT_SECONDS, 10.0))
    upstream_ok = False
    upstream_status: Optional[int] = None
    error: Optional[str] = None

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await client.get(UPSTREAM_URL)
            upstream_ok = response.status_code < 500
            upstream_status = response.status_code
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    return {
        "status": "healthy" if upstream_ok else "degraded",
        "service": PROXY_TITLE,
        "upstream": {
            "url": UPSTREAM_URL,
            "reachable": upstream_ok,
            "status_code": upstream_status,
            "error": error,
        },
        "compatibility": {
            "runtime_tools": [t["name"] for t in RUNTIME_TOOLS if not t.get("optional")],
            "aliases_supported": sorted(
                alias for alias, runtime in ALIAS_TO_RUNTIME.items() if alias != runtime
            ),
        },
    }


@app.get("/.well-known/mcp/server.json")
async def well_known_server(request: Request) -> JSONResponse:
    return JSONResponse(_manifest_payload(request))


@app.get("/compat/tools")
async def compat_tools() -> dict[str, Any]:
    return {
        "upstream": UPSTREAM_URL,
        "runtime_tools": RUNTIME_TOOLS,
        "alias_to_runtime": ALIAS_TO_RUNTIME,
    }


@app.get("/compat/aliases")
async def compat_aliases() -> dict[str, str]:
    return ALIAS_TO_RUNTIME


@app.api_route("/mcp", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_mcp_root(request: Request) -> Response:
    return await _forward_request(request, UPSTREAM_URL)


@app.api_route(
    "/mcp/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_mcp_subpath(path: str, request: Request) -> Response:
    target = f"{UPSTREAM_URL.rstrip('/')}/{path.lstrip('/')}"
    return await _forward_request(request, target)


@app.get("/robots.txt")
async def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nAllow: /\n")


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
