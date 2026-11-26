"""GEOX local-first CLI entrypoint (`geox --airgap --stdio`)."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import fastmcp

from geox.airgap import enable_airgap_guard
from geox_mcp.apps_well_forensic import register_well_forensic_app


def build_stdio_server() -> fastmcp.FastMCP:
    mcp = fastmcp.FastMCP("GEOX Local Forensic MCP")
    register_well_forensic_app(mcp)
    return mcp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geox", description="GEOX local-first MCP server")
    parser.add_argument("--airgap", action="store_true", help="Block all outbound network sockets")
    parser.add_argument("--stdio", action="store_true", help="Run MCP server over stdio transport")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory for local telemetry & EarthGraph DB")
    args = parser.parse_args(argv)

    if args.data_dir:
        d = Path(args.data_dir)
        d.mkdir(parents=True, exist_ok=True)
        os.environ["GEOX_TELEMETRY_PATH"] = str(d / "telemetry.jsonl")
        os.environ["GEOX_EARTHGRAPH_DB"] = str(d / "earthgraph.db")

    if args.airgap:
        enable_airgap_guard()

    mcp = build_stdio_server()
    if args.stdio or True:
        mcp.run(transport="stdio", show_banner=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
