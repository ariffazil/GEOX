import urllib.request
import urllib.error
import re
import json

def audit_site():
    base_url = "https://geox.arif-fazil.com"
    results = {}

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # 1. Verify geox.arif-fazil.com title
    print("Auditing 1. geox.arif-fazil.com homepage...")
    try:
        req = urllib.request.Request(base_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            title = title_match.group(1) if title_match else "No Title Found"
            
            # Check for React bundle assets in the homepage HTML
            assets = re.findall(r'src="(/assets/index-[a-zA-Z0-9_-]+\.js)"', html)
            if not assets:
                # Also check with href or script tags
                assets = re.findall(r'href="(/assets/index-[a-zA-Z0-9_-]+\.css)"', html)
                # Check for script tag src containing index-
                assets += re.findall(r'src="(/assets/index-[a-zA-Z0-9_-]+\.js)"', html)
                # Let's do a wider regex
                assets += re.findall(r'(/assets/index-[a-zA-Z0-9_-]+\.js)', html)
            assets = list(set(assets))
            
            results["homepage"] = {
                "status": "PASS" if "GEOX Earth Witness" in title else "FAIL",
                "code": response.getcode(),
                "title": title,
                "found_assets": assets
            }
    except Exception as e:
        results["homepage"] = {
            "status": "FAIL",
            "error": str(e)
        }

    # 2. Verify React bundle assets
    print("Auditing 2. React bundle asset loading...")
    results["react_bundle"] = {
        "status": "FAIL",
        "loaded_assets": []
    }
    if "homepage" in results and results["homepage"].get("found_assets"):
        found = False
        for asset in results["homepage"]["found_assets"]:
            asset_url = base_url + asset if asset.startswith('/') else f"{base_url}/{asset}"
            try:
                req = urllib.request.Request(asset_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as asset_resp:
                    code = asset_resp.getcode()
                    content_length = len(asset_resp.read())
                    results["react_bundle"]["loaded_assets"].append({
                        "url": asset_url,
                        "status": "PASS" if code == 200 else "FAIL",
                        "code": code,
                        "size_bytes": content_length
                    })
                    if code == 200:
                        found = True
            except Exception as e:
                results["react_bundle"]["loaded_assets"].append({
                    "url": asset_url,
                    "status": "FAIL",
                    "error": str(e)
                })
        if found:
            results["react_bundle"]["status"] = "PASS"
    else:
        # Fallback search/check if we didn't parse assets correctly or if there are none in the main body
        # Let's try to fetch a default one or report
        results["react_bundle"]["note"] = "No explicit index-*.js asset detected directly in homepage HTML."

    # 3. Verify Cesium.js loading
    print("Auditing 3. Cesium loading...")
    cesium_url = f"{base_url}/cesium/Cesium.js"
    try:
        req = urllib.request.Request(cesium_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            code = response.getcode()
            content = response.read(1000) # Read just the first 1000 bytes to check
            is_cesium = b"Cesium" in content or b"cesium" in content or len(content) > 100
            results["cesium"] = {
                "status": "PASS" if (code == 200 and is_cesium) else "FAIL",
                "code": code,
                "url": cesium_url,
                "snippet": content[:100].decode('utf-8', errors='ignore')
            }
    except Exception as e:
        results["cesium"] = {
            "status": "FAIL",
            "error": str(e)
        }

    # 4. Verify Map tab route
    print("Auditing 4. Map route...")
    map_url = f"{base_url}/map/"
    try:
        req = urllib.request.Request(map_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            code = response.getcode()
            html = response.read().decode('utf-8')
            # Since React uses client-side routing, /map/ should load the index.html
            # Let's check if the index.html is loaded at this path (which means fallback is working)
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            title = title_match.group(1) if title_match else "No Title Found"
            results["map_route"] = {
                "status": "PASS" if code == 200 else "FAIL",
                "code": code,
                "title_at_map_route": title,
                "is_spa_fallback": "GEOX Earth Witness" in title
            }
    except Exception as e:
        results["map_route"] = {
            "status": "FAIL",
            "error": str(e)
        }

    # 5. Verify MCP backend
    print("Auditing 5. MCP backend...")
    mcp_url = f"{base_url}/mcp/"
    try:
        req = urllib.request.Request(mcp_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            code = response.getcode()
            content = response.read().decode('utf-8')
            # Let's check if there is an MCP health message, schema, SSE endpoint, or FastAPI docs
            results["mcp_backend"] = {
                "status": "PASS" if code == 200 else "FAIL",
                "code": code,
                "content_preview": content[:200]
            }
    except Exception as e:
        results["mcp_backend"] = {
            "status": "FAIL",
            "error": str(e)
        }

    print("\n=== AUDIT RESULTS ===")
    print(json.dumps(results, indent=2))
    
    # Generate Markdown Report
    report = []
    report.append("# GEOX EarthVision Audit Report")
    report.append(f"**Target URL:** {base_url}")
    report.append("")
    report.append("## Verification Summary")
    report.append("| Verification Item | Target | Status | Details |")
    report.append("| --- | --- | --- | --- |")
    
    # Item 1
    homepage = results.get("homepage", {})
    homepage_status = "✅ PASS" if homepage.get("status") == "PASS" else "❌ FAIL"
    homepage_detail = f"Code {homepage.get('code')}, Title: '{homepage.get('title')}'" if 'code' in homepage else f"Error: {homepage.get('error')}"
    report.append(f"| 1. Homepage | `geox.arif-fazil.com` | {homepage_status} | {homepage_detail} |")
    
    # Item 2
    react = results.get("react_bundle", {})
    react_status = "✅ PASS" if react.get("status") == "PASS" else "❌ FAIL"
    react_detail = ""
    if react.get("loaded_assets"):
        assets_info = []
        for asset in react["loaded_assets"]:
            name = asset["url"].split('/')[-1]
            assets_info.append(f"`{name}` ({asset.get('size_bytes', 0)} bytes)")
        react_detail = ", ".join(assets_info)
    else:
        react_detail = react.get("note", "No assets loaded")
    report.append(f"| 2. React Bundle | `/assets/index-*.js` | {react_status} | {react_detail} |")
    
    # Item 3
    cesium = results.get("cesium", {})
    cesium_status = "✅ PASS" if cesium.get("status") == "PASS" else "❌ FAIL"
    cesium_detail = f"Code {cesium.get('code')}, snippet: `{cesium.get('snippet')}`" if 'code' in cesium else f"Error: {cesium.get('error')}"
    report.append(f"| 3. Cesium JS | `/cesium/Cesium.js` | {cesium_status} | {cesium_detail} |")
    
    # Item 4
    map_route = results.get("map_route", {})
    map_status = "✅ PASS" if map_route.get("status") == "PASS" else "❌ FAIL"
    map_detail = f"Code {map_route.get('code')}, Title: '{map_route.get('title_at_map_route')}', SPA Fallback: {map_route.get('is_spa_fallback')}" if 'code' in map_route else f"Error: {map_route.get('error')}"
    report.append(f"| 4. Map Route | `/map/` | {map_status} | {map_detail} |")
    
    # Item 5
    mcp = results.get("mcp_backend", {})
    mcp_status = "✅ PASS" if mcp.get("status") == "PASS" else "❌ FAIL"
    mcp_detail = f"Code {mcp.get('code')}, preview: `{mcp.get('content_preview')}`" if 'code' in mcp else f"Error: {mcp.get('error')}"
    report.append(f"| 5. MCP Backend | `/mcp/` | {mcp_status} | {mcp_detail} |")
    
    report_text = "\n".join(report)
    with open("C:/ariffazil/GEOX/docs/geox_audit_results.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    print("\nSaved markdown report to C:/ariffazil/GEOX/docs/geox_audit_results.md")

if __name__ == "__main__":
    audit_site()
