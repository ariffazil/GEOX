#!/usr/bin/env python3
"""
geox_scholar_search — Academic, patent, and local discovery for GEOX organ.
Wraps SERP API scholar/patents/maps engines with GEOX-specific formatting.

Usage:
    python3 geox_scholar_search.py --query "Miocene carbonate platforms" --mode papers
    python3 geox_scholar_search.py --query "petroleum geology" --mode authors --author-id "XYZ"
    python3 geox_scholar_search.py --query "oil trap patent" --mode patents
    python3 geox_scholar_search.py --query "geology consultant Kuala Lumpur" --mode local
    python3 geox_scholar_search.py --query "Malaysian oil royalty" --mode case_law

Modes: papers | authors | case_law | patents | local
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import json
import os
import sys
import subprocess
from pathlib import Path

FORGE_SERPAPI = "/root/A-FORGE/tools/forge_serpapi.py"


def run_serpapi(engine, query, extra_params=None, compact=True):
    """Call forge_serpapi and return parsed result."""
    cmd = [sys.executable, FORGE_SERPAPI, "-e", engine, "-q", query]
    if compact:
        cmd.append("--compact")
    if extra_params:
        cmd.extend(["-p", json.dumps(extra_params)])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        try:
            return json.loads(result.stdout)
        except:
            return {"error": result.stderr or result.stdout or "Unknown error"}
    try:
        return json.loads(result.stdout)
    except:
        return {"error": f"Parse error: {result.stdout[:500]}"}


def format_papers(data):
    """Format scholar results for GEOX consumption."""
    results = data.get("organic_results", [])
    formatted = []
    for r in results[:10]:
        pub = r.get("publication_info", {})
        links = r.get("inline_links", {})
        cited = links.get("cited_by", {})
        resources = r.get("resources", [])

        paper = {
            "title": r.get("title"),
            "snippet": r.get("snippet", "")[:300],
            "authors": pub.get("summary", ""),
            "citations": cited.get("total", 0),
            "link": r.get("link"),
            "pdf_link": resources[0].get("link") if resources else None,
            "year": None,
        }
        # Extract year from publication info
        summary = pub.get("summary", "")
        for part in summary.split(" - ")[-1].split(","):
            part = part.strip()
            if part.isdigit() and 1900 < int(part) < 2100:
                paper["year"] = int(part)
                break

        formatted.append(paper)

    return {
        "domain": "academic",
        "organ": "GEOX",
        "total_results": data.get("search_information", {}).get("total_results", 0),
        "papers": formatted,
        "count": len(formatted),
        "budget_remaining": data.get("budget_remaining", "?"),
    }


def format_authors(data):
    """Format author results."""
    # Author search returns different structure
    results = data.get("organic_results", [])
    return {
        "domain": "academic.authors",
        "organ": "GEOX",
        "results": [
            {
                "name": r.get("author", {}).get("name"),
                "affiliations": r.get("author", {}).get("affiliations", []),
                "email": r.get("author", {}).get("email"),
                "citations": r.get("cited_by", 0),
                "h_index": r.get("h_index"),
                "link": r.get("link"),
            }
            for r in results[:5]
        ],
    }


def format_patents(data):
    """Format patent results."""
    results = data.get("organic_results", [])
    return {
        "domain": "academic.patents",
        "organ": "GEOX",
        "patents": [
            {
                "title": r.get("title"),
                "snippet": r.get("snippet", "")[:300],
                "patent_id": r.get("patent_id"),
                "filing_date": r.get("filing_date"),
                "assignee": r.get("assignee"),
                "link": r.get("link"),
                "pdf_link": r.get("pdf_link"),
            }
            for r in results[:10]
        ],
        "count": len(results),
    }


def format_case_law(data):
    """Format case law results."""
    results = data.get("organic_results", [])
    return {
        "domain": "academic.case_law",
        "organ": "GEOX",
        "cases": [
            {
                "title": r.get("title"),
                "snippet": r.get("snippet", "")[:300],
                "court": r.get("court"),
                "date": r.get("date"),
                "link": r.get("link"),
                "citations": r.get("inline_links", {}).get("cited_by", {}).get("total", 0),
            }
            for r in results[:10]
        ],
        "count": len(results),
    }


def format_local(data):
    """Format local/maps results for geological service discovery."""
    results = data.get("local_results", data.get("places", []))
    return {
        "domain": "local",
        "organ": "GEOX",
        "places": [
            {
                "name": r.get("title"),
                "rating": r.get("rating"),
                "reviews": r.get("reviews"),
                "address": r.get("address"),
                "phone": r.get("phone"),
                "website": r.get("website"),
                "type": r.get("type"),
                "hours": r.get("hours"),
                "gps": r.get("gps_coordinates"),
            }
            for r in results[:10]
        ],
        "count": len(results),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="geox_scholar_search — Academic/patent/local discovery for GEOX")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument(
        "--mode", "-m", default="papers", choices=["papers", "authors", "case_law", "patents", "local"], help="Search mode"
    )
    parser.add_argument("--filters", "-f", help="Extra filters as JSON (e.g. '{\"as_ylo\": 2020}')")
    parser.add_argument("--raw", action="store_true", help="Return raw SERP API response")
    args = parser.parse_args()

    filters = json.loads(args.filters) if args.filters else {}

    # Map mode to engine
    engine_map = {
        "papers": "google_scholar",
        "authors": "google_scholar_author",
        "case_law": "google_scholar_case_law",
        "patents": "google_patents",
        "local": "google_maps",
    }

    engine = engine_map[args.mode]

    # Add location bias for local searches
    if args.mode == "local" and "ll" not in filters:
        filters["ll"] = "@3.1390,101.6869,12z"  # Default: Kuala Lumpur

    # Call SERP API
    data = run_serpapi(engine, args.query, filters if filters else None, compact=False)

    if "error" in data:
        print(json.dumps(data, indent=2))
        sys.exit(1)

    if args.raw:
        print(json.dumps(data, indent=2))
        return

    # Format based on mode
    formatters = {
        "papers": format_papers,
        "authors": format_authors,
        "case_law": format_case_law,
        "patents": format_patents,
        "local": format_local,
    }

    result = formatters[args.mode](data)
    result["query"] = args.query
    result["engine"] = engine
    result["mode"] = args.mode
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
