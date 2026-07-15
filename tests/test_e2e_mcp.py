#!/usr/bin/env python3
"""
GEOX MCP Server E2E Test Suite — DITEMPA BUKAN DIBERI

Tests the complete MCP server functionality end-to-end:
1. Server startup
2. Health check endpoints
3. Tool registration
4. Tool invocation
5. FastMCP compatibility layer

Usage:
    python test_e2e_mcp.py [--url https://geoxarifOS.fastmcp.app]

Exit codes:
    0 - All tests passed
    1 - One or more tests failed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from typing import Any

import httpx


class GEOXMCPTestSuite:
    """E2E test suite for GEOX MCP server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.mcp_url = f"{self.base_url}/mcp"
        self.results: list[dict] = []
        self.session_id: str | None = None
        
    def log(self, test: str, status: str, message: str = "", data: dict | None = None):
        """Log test result."""
        result = {
            "test": test,
            "status": status,
            "message": message,
            "data": data,
            "timestamp": time.time(),
        }
        self.results.append(result)
        
        icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"  {icon} {test}: {status}", end="")
        if message:
            print(f" - {message}")
        else:
            print()
            
    async def test_health_endpoint(self) -> bool:
        """Test basic health endpoint."""
        test_name = "Health Check (/health)"
        
        try:
            async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log(test_name, "PASS")
                    return True
                else:
                    self.log(test_name, "FAIL", f"Unexpected response: {data}")
                    return False
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def test_health_details(self) -> bool:
        """Test detailed status endpoint."""
        test_name = "Health Details (/status)"
        
        try:
            async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
                response = await client.get(
                    f"{self.base_url}/status",
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required = ["status", "version", "profile", "canonical_tools"]
                missing = [f for f in required if f not in data]
                
                if missing:
                    self.log(test_name, "FAIL", f"Missing fields: {missing}")
                    return False
                
                self.log(test_name, "PASS", f"Version: {data.get('version')}", data)
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def test_mcp_initialize(self) -> bool:
        """Test MCP initialize method."""
        test_name = "MCP Initialize"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.mcp_url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-25",
                            "capabilities": {},
                            "clientInfo": {"name": "geox-e2e-test", "version": "1.0.0"}
                        }
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                
                # Check protocol version
                if "protocolVersion" not in result:
                    self.log(test_name, "FAIL", "Missing protocolVersion")
                    return False
                
                # Extract session ID from headers
                self.session_id = response.headers.get("mcp-session-id")
                if not self.session_id:
                    self.log(test_name, "FAIL", "Missing mcp-session-id in initialize response headers")
                    return False
                
                self.log(test_name, "PASS", f"Protocol: {result.get('protocolVersion')} | Session: {self.session_id[:8]}...")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def test_mcp_list_tools(self) -> bool:
        """Test MCP tools/list method."""
        test_name = "MCP List Tools"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                tools = result.get("tools", [])
                
                # Check expected tools in geox server
                expected_tools = [
                    "geox_surface_status",
                    "geox_contrast_detect",
                    "geox_well_qc",
                ]
                
                tool_names = [t.get("name") for t in tools]
                missing = [t for t in expected_tools if t not in tool_names]
                
                if missing:
                    self.log(test_name, "FAIL", f"Missing tools: {missing}")
                    return False
                
                self.log(test_name, "PASS", f"Found {len(tools)} tools")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def test_mcp_call_tool(self) -> bool:
        """Test MCP tool invocation."""
        test_name = "MCP Call Tool (geox_surface_status)"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "geox_surface_status",
                            "arguments": {
                                "mode": "registry"
                            }
                        }
                    },
                    timeout=30.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                content = result.get("content", [])
                
                if not content:
                    self.log(test_name, "FAIL", "No content in result")
                    return False
                
                # Parse the content
                text_content = content[0].get("text", "")
                try:
                    parsed = json.loads(text_content)
                    if parsed.get("status") == "OK" or "tool_count" in parsed:
                        self.log(test_name, "PASS", f"Registered tools count: {parsed.get('tool_count', 'N/A')}")
                        return True
                    else:
                        self.log(test_name, "FAIL", f"Tool returned unexpected output: {text_content[:200]}")
                        return False
                except json.JSONDecodeError:
                    self.log(test_name, "FAIL", "Could not parse tool output as JSON")
                    return False
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def test_mcp_call_health_tool(self) -> bool:
        """Test MCP call tool (geox_contrast_detect)."""
        test_name = "MCP Call Tool (geox_contrast_detect)"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {
                            "name": "geox_contrast_detect",
                            "arguments": {
                                "dimension": "all"
                            }
                        }
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                content = result.get("content", [])
                
                if not content:
                    self.log(test_name, "FAIL", "No content")
                    return False
                
                text_content = content[0].get("text", "")
                try:
                    parsed = json.loads(text_content)
                    if parsed.get("status") == "OK":
                        self.log(test_name, "PASS", "Contrast detect executed successfully")
                        return True
                    else:
                        self.log(test_name, "FAIL", f"Tool failed: {text_content[:200]}")
                        return False
                except json.JSONDecodeError:
                    self.log(test_name, "FAIL", "Parse error")
                    return False
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def test_fastmcp_compatibility(self) -> bool:
        """Test FastMCP compatibility layer."""
        test_name = "FastMCP Compatibility"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 5,
                        "method": "tools/call",
                        "params": {
                            "name": "geox_contrast_detect",
                            "arguments": {
                                "dimension": "all"
                            }
                        }
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                # Check for proper JSON-RPC 2.0 format
                if data.get("jsonrpc") != "2.0":
                    self.log(test_name, "FAIL", "Not JSON-RPC 2.0")
                    return False
                
                # Check for content array (FastMCP format)
                result = data.get("result", {})
                if "content" not in result:
                    self.log(test_name, "FAIL", "Missing content array")
                    return False
                
                content = result.get("content", [])
                if not isinstance(content, list):
                    self.log(test_name, "FAIL", "Content not an array")
                    return False
                
                # Check content structure
                for item in content:
                    if "type" not in item or "text" not in item:
                        self.log(test_name, "FAIL", "Invalid content item structure")
                        return False
                
                self.log(test_name, "PASS", "Compatible with FastMCP 2.x/3.x")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False

    async def test_mcp_list_resources(self) -> bool:
        """Test MCP resources/list method."""
        test_name = "MCP List Resources"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 6,
                        "method": "resources/list",
                        "params": {}
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                resources = result.get("resources", [])
                
                self.log(test_name, "PASS", f"Found {len(resources)} resources")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False

    async def test_mcp_read_resource(self) -> bool:
        """Test MCP resources/read method."""
        test_name = "MCP Read Resource (geox://capabilities)"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 7,
                        "method": "resources/read",
                        "params": {
                            "uri": "geox://capabilities"
                        }
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                contents = result.get("contents", [])
                if not contents:
                    self.log(test_name, "FAIL", "No contents in resource response")
                    return False
                
                self.log(test_name, "PASS", "Resource read successfully")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False

    async def test_mcp_list_prompts(self) -> bool:
        """Test MCP prompts/list method."""
        test_name = "MCP List Prompts"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 8,
                        "method": "prompts/list",
                        "params": {}
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                prompts = result.get("prompts", [])
                
                self.log(test_name, "PASS", f"Found {len(prompts)} prompts")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False

    async def test_mcp_get_prompt(self) -> bool:
        """Test MCP prompts/get method."""
        test_name = "MCP Get Prompt (geox_guard)"
        
        if not self.session_id:
            self.log(test_name, "FAIL", "No active session ID")
            return False
            
        try:
            async with httpx.AsyncClient(headers={
                "Accept": "application/json",
                "mcp-session-id": self.session_id,
            }) as client:
                response = await client.post(
                    self.mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 9,
                        "method": "prompts/get",
                        "params": {
                            "name": "geox_guard",
                            "arguments": {}
                        }
                    },
                    timeout=10.0
                )
                
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    self.log(test_name, "FAIL", f"Error: {data['error']}")
                    return False
                
                result = data.get("result", {})
                messages = result.get("messages", [])
                if not messages:
                    self.log(test_name, "FAIL", "No messages in prompt response")
                    return False
                
                self.log(test_name, "PASS", "Prompt retrieved successfully")
                return True
            else:
                self.log(test_name, "FAIL", f"Status {response.status_code}")
                return False
                
        except Exception as exc:
            self.log(test_name, "FAIL", str(exc))
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all E2E tests."""
        print("\n" + "=" * 70)
        print("GEOX MCP Server E2E Test Suite")
        print("DITEMPA BUKAN DIBERI")
        print("=" * 70)
        print(f"\nTarget: {self.base_url}\n")
        
        tests = [
            self.test_health_endpoint,
            self.test_health_details,
            self.test_mcp_initialize,
            self.test_mcp_list_tools,
            self.test_mcp_call_tool,
            self.test_mcp_call_health_tool,
            self.test_mcp_list_resources,
            self.test_mcp_read_resource,
            self.test_mcp_list_prompts,
            self.test_mcp_get_prompt,
            self.test_fastmcp_compatibility,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as exc:
                print(f"  ✗ {test.__name__}: EXCEPTION - {exc}")
                results.append(False)
            await asyncio.sleep(0.1)  # Brief pause between tests
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("\n" + "=" * 70)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("Status: ✓ ALL TESTS PASSED")
            print("=" * 70)
            return True
        else:
            print(f"Status: ✗ {total - passed} test(s) failed")
            print("=" * 70)
            return False
    
    def print_report(self):
        """Print detailed test report."""
        print("\n" + "=" * 70)
        print("Detailed Test Report")
        print("=" * 70)
        
        for result in self.results:
            status_icon = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "⚠"
            print(f"\n{status_icon} {result['test']}")
            print(f"   Status: {result['status']}")
            if result["message"]:
                print(f"   Message: {result['message']}")
            if result["data"]:
                print(f"   Data: {json.dumps(result['data'], indent=2)[:500]}")


async def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(
        description="GEOX MCP Server E2E Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_e2e_mcp.py                    # Test local server
    python test_e2e_mcp.py --url https://...  # Test remote server
        """
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of GEOX MCP server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed report"
    )
    
    args = parser.parse_args()
    
    # Run tests
    suite = GEOXMCPTestSuite(args.url)
    success = await suite.run_all_tests()
    
    if args.verbose:
        suite.print_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())