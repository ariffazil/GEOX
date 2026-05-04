import pytest
import os
from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP

def get_llms_txt_tools():
    llms_path = os.path.join(os.getcwd(), "llms.txt")
    if not os.path.exists(llms_path):
        pytest.skip("llms.txt not found, skipping parity test.")

    tools = []
    with open(llms_path, "r") as f:
        in_canonical_section = False
        for line in f:
            line = line.strip()
            if "1. Canonical Sovereign 13" in line or "## 1. Canonical Sovereign 13" in line:
                in_canonical_section = True
                continue
            if in_canonical_section:
                if "## 2." in line:
                    break
                if line.startswith(tuple(f"{i}." for i in range(1, 14))):
                    raw = line.split(".", 1)[1].strip()
                    # Strip bold markdown (**name**) and trailing colon
                    tool_name = raw.split(" ", 1)[0].strip("*:").strip()
                    if tool_name.startswith("geox_"):
                        tools.append(tool_name)
    return tools

def get_manifest_tools():
    manifest_tools = set()
    manifest_dir = os.path.join(os.getcwd(), "control_plane/fastmcp/manifests")
    if not os.path.exists(manifest_dir):
        return list(manifest_tools)

    for filename in os.listdir(manifest_dir):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(manifest_dir, filename)) as f:
                    manifest = json.load(f)
                # Support both "tools" list-of-dicts and "required_tools" list-of-strings
                for key in ("tools", "required_tools"):
                    entries = manifest.get(key, [])
                    for entry in entries:
                        name = entry if isinstance(entry, str) else entry.get("name", "")
                        if name.startswith("geox_"):
                            manifest_tools.add(name)
            except Exception:
                pass
    return list(manifest_tools)

def test_llms_txt_parity_with_canonical_tools():
    llms_txt_tools = get_llms_txt_tools()
    assert set(llms_txt_tools) == set(CANONICAL_PUBLIC_TOOLS), \
        f"llms.txt tool list does not match CANONICAL_PUBLIC_TOOLS. Missing: {set(CANONICAL_PUBLIC_TOOLS) - set(llms_txt_tools)}, Extra: {set(llms_txt_tools) - set(CANONICAL_PUBLIC_TOOLS)}"

def test_manifest_parity_with_canonical_tools():
    manifest_tools = get_manifest_tools()
    if not manifest_tools:
        pytest.skip("No manifests found in control_plane/fastmcp/manifests — skipping parity check.")

    non_canonical = [t for t in manifest_tools if t not in CANONICAL_PUBLIC_TOOLS and t not in LEGACY_ALIAS_MAP]
    assert not non_canonical, (
        f"Manifests reference non-canonical, non-alias tools: {non_canonical}. "
        "Add to CANONICAL_PUBLIC_TOOLS or LEGACY_ALIAS_MAP, or remove from manifests."
    )
