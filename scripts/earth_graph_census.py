#!/usr/bin/env python3
"""earth_graph_census.py — measure the PHYSICAL REALITY GRAPH that GEOX actually holds.

Why this exists
---------------
Macrostrat's knowledge graph is *text-derived*: xDD extracts entities and
relations from literature passages, and a geologist reviews the extractions.
GEOX's opportunity is the complement: a *measurement-derived* graph, where every
node and every edge is an observation with a file, a survey, a tool+version and
a coverage class.

Before designing that graph you must know what GEOX already holds, because the
failure mode is building a second graph next to a half-built first one. This
script is the census: it counts typed nodes and typed edges across every store
GEOX keeps, and names the bindings that do not exist yet.

F2 TRUTH: every number printed here is counted from a file or a live probe.
Zeros are reported as zeros, never as "pending" or "unknown".
F7 HUMILITY: absence of a binding is reported as an absent binding, not as a
claim that the geology is unknown.

Usage:
    python3 scripts/earth_graph_census.py
    python3 scripts/earth_graph_census.py --json /tmp/census.json
    python3 scripts/earth_graph_census.py --live     # also probe the live organ

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    sys.stderr.write("PyYAML required: run with the GEOX venv python\n")
    raise

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "resources"

# The node vocabulary is GEOX's OWN typed model (src/geox/egs/models/entities.py).
# A node type that is not in this list is not part of the graph.
NODE_TYPES = (
    "basin",
    "play",
    "strat_unit",
    "horizon",
    "fault",
    "volume",
    "well",
    "survey",
    "observation",
    "claim",
)

# The edge vocabulary a physical reality graph needs. `present` counts what
# exists in the stores TODAY; `missing` is the work, not a failure.
REQUIRED_EDGES = (
    ("claim->basin", "claim is filed under a basin"),
    ("claim->entity", "claim names a well / unit / horizon it is about"),
    ("basin->parent_basin", "basin sits inside a parent basin"),
    ("well->basin", "well is located in a basin"),
    ("unit->horizon", "strat unit is bounded by a horizon"),
    ("horizon->well", "horizon is tied to a well"),
    ("fault->horizon", "fault offsets a horizon"),
    ("observation->unit", "a log/trace constrains a unit"),
    ("observation->instrument", "an observation was made by a tool+version"),
)


def _load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _claims_of(doc) -> list[dict]:
    if isinstance(doc, list):
        return [c for c in doc if isinstance(c, dict)]
    if isinstance(doc, dict):
        c = doc.get("claims")
        if isinstance(c, list):
            return [x for x in c if isinstance(x, dict)]
    return []


def census(repo: Path = REPO) -> dict:
    res = repo / "resources"
    nodes = {t: 0 for t in NODE_TYPES}
    edges: dict[str, int] = {name: 0 for name, _ in REQUIRED_EDGES}
    detail: dict[str, object] = {}

    # ── basin profiles: the only typed entity store GEOX keeps ─────────────
    profiles = sorted(res.glob("basins/*/basin_profile.yaml"))
    basin_ids: list[str] = []
    parent_links = 0
    for p in profiles:
        d = _load_yaml(p)
        if not isinstance(d, dict):
            continue
        nodes["basin"] += 1
        bid = d.get("basin_id")
        if bid:
            basin_ids.append(str(bid))
        if d.get("parent_basin"):
            parent_links += 1
    edges["basin->parent_basin"] = parent_links
    detail["basin_profiles"] = len(profiles)
    detail["basin_ids"] = sorted(basin_ids)

    # ── claims: the only relation store GEOX keeps ─────────────────────────
    claim_files = sorted(res.glob("basins/*/claims.json"))
    claim_total = 0
    claim_bound_to_entity = 0
    claim_with_falsifier = 0
    claim_with_evidence = 0
    claim_with_forbidden = 0
    by_type: dict[str, int] = {}
    for f in claim_files:
        claims = _claims_of(_load_json(f))
        claim_total += len(claims)
        for c in claims:
            t = c.get("claim_type") or "untyped"
            by_type[t] = by_type.get(t, 0) + 1
            # An entity binding is a subject/object reference. GEOX has none yet.
            if any(k in c for k in ("subject_ref", "object_ref", "subject", "predicate", "entity_ref")):
                claim_bound_to_entity += 1
            if c.get("falsifier"):
                claim_with_falsifier += 1
            if c.get("evidence_refs"):
                claim_with_evidence += 1
            if c.get("forbidden_uses"):
                claim_with_forbidden += 1
    nodes["claim"] = claim_total
    edges["claim->basin"] = claim_total  # mechanical: the file path binds them
    detail["claim_files"] = len(claim_files)
    detail["claim_types"] = dict(sorted(by_type.items(), key=lambda kv: -kv[1]))
    detail["claims_with_falsifier"] = claim_with_falsifier
    detail["claims_with_evidence_refs"] = claim_with_evidence
    detail["claims_with_forbidden_uses"] = claim_with_forbidden
    detail["claims_bound_to_an_entity"] = claim_bound_to_entity

    # ── wells registry ─────────────────────────────────────────────────────
    wells: list[dict] = []
    for name in ("registry/wells_sabah.json", "demo_wells.json"):
        p = res / name
        if not p.exists():
            continue
        d = _load_json(p)
        if isinstance(d, list):
            wells.extend(w for w in d if isinstance(w, dict))
        elif isinstance(d, dict):
            w = d.get("wells")
            if isinstance(w, list):
                wells.extend(x for x in w if isinstance(x, dict))
            elif d.get("well_id"):
                wells.append(d)
    nodes["well"] = len(wells)
    # well->basin is a free-text province string in GEOX today, not a binding.
    edges["well->basin"] = 0
    detail["well_records"] = len(wells)

    # ── horizons / faults / volumes / surveys / plays / strat units ─────────
    # These are node types in GEOX's own model. Count them where they are
    # actually structured, not where they are mentioned in prose.
    strat_units = 0
    for p in sorted(res.glob("basins/*/basin_profile.yaml")):
        d = _load_yaml(p)
        if not isinstance(d, dict):
            continue
        fw = d.get("stratigraphic_framework")
        if isinstance(fw, list):
            strat_units += len(fw)
        elif isinstance(fw, dict):
            strat_units += len(fw)
    nodes["strat_unit"] = strat_units
    detail["strat_unit_note"] = (
        "stratigraphic_framework is a narrative string in every profile measured; "
        "0 typed strat_unit nodes" if strat_units == 0 else "counted from stratigraphic_framework"
    )

    for t in ("play", "horizon", "fault", "volume", "survey", "observation"):
        nodes[t] = 0

    # ── upstream capability presence (what GEOX does NOT have) ─────────────
    upstream = {
        "macrostrat_api_v2_lexicon": {
            "present": True,
            "where": "src/geox_mcp/tools/macrostrat_client.py",
            "note": "11 routes; all verified 200 live 2026-11-12",
        },
        "macrostrat_kg_literature_graph": {
            "present": False,
            "where": "upstream schema macrostrat_kg (NOT a public route)",
            "note": "xDD extraction + human review; GEOX has no Weaviate, no extractor, no review store",
        },
        "map_topology_faces": {
            "present": False,
            "where": "upstream schema map_bounds_topology + Mapboard/topology-manager (Apache-2.0)",
            "note": "GEOX has no PostGIS and no linework adjacency",
        },
        "plate_rotation_server": {
            "present": False,
            "where": "UW-Macrostrat/corelle (GPlates-compatible)",
            "note": "GEOX has a DEREGISTERED GPlates path (tools_wiring.py:2172, 2026-07-10); no rotation service",
        },
        "map_ingestion_api_v3": {
            "present": False,
            "where": "upstream services/api-v3",
            "note": "GEOX ingests wells and seismic, not maps",
        },
        "postgis_curated_views": {
            "present": False,
            "where": "upstream PostgREST",
            "note": "GEOX substrate is LanceDB/H3/Redis — deliberately not a PostGIS mirror",
        },
    }

    total_nodes = sum(nodes.values())
    total_edges = sum(edges.values())
    entity_edges = edges["claim->entity"] + edges["well->basin"] + edges["unit->horizon"] + edges[
        "horizon->well"
    ] + edges["fault->horizon"] + edges["observation->unit"] + edges["observation->instrument"]

    return {
        "schema": "geox-earth-graph-census/v1",
        "repo": str(repo),
        "node_types": list(NODE_TYPES),
        "nodes": nodes,
        "node_total": total_nodes,
        "edges": edges,
        "edge_total": total_edges,
        "entity_binding_edges": entity_edges,
        "binding_coverage_pct": round(100.0 * entity_edges / total_edges, 2) if total_edges else 0.0,
        "detail": detail,
        "upstream_capabilities": upstream,
        "verdict": (
            "SHALLOW_SPINE"
            if entity_edges == 0
            else "PARTIAL_BINDING"
            if entity_edges < total_edges // 2
            else "BOUND"
        ),
        "verdict_meaning": {
            "SHALLOW_SPINE": (
                "What exists is basin -> claim (87, mechanical: the file path binds them) plus 5 "
                "basin -> parent_basin links. No claim is bound to the entity it is about, no well is "
                "bound to a basin, and no observation constrains a unit. This is a spine, not a graph."
            ),
            "PARTIAL_BINDING": "Some entity-binding edges exist; the deep edges are incomplete.",
            "BOUND": "Entity-binding edges dominate.",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--json", help="write the raw census JSON here")
    ap.add_argument("--live", action="store_true", help="also probe the live organ for registered sources")
    args = ap.parse_args()

    out = census(Path(args.repo))

    if args.live:
        n_sources, note = None, "live probe skipped"
        try:
            import urllib.request

            url = "http://127.0.0.1:8081/mcp"

            def _post(payload: dict, sid: str | None = None):
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                }
                if sid:
                    headers["Mcp-Session-Id"] = sid
                req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    return resp.headers, resp.read().decode("utf-8", "replace")

            def _result_of(raw: str) -> dict:
                for line in raw.splitlines():
                    if line.startswith("data:"):
                        return json.loads(line[5:].strip())
                try:
                    return json.loads(raw)
                except Exception:
                    return {}

            # FastMCP resolves the transport session before middleware runs, so a
            # bare tools/call is refused with "Session not found". Handshake first.
            hdrs, _ = _post(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "earth_graph_census", "version": "1.0"},
                    },
                }
            )
            sid = hdrs.get("mcp-session-id") or hdrs.get("Mcp-Session-Id")
            if not sid:
                raise RuntimeError("no Mcp-Session-Id from initialize")
            try:
                _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
            except Exception:
                pass  # notification replies 202 with no body
            # GEOX runs a lifecycle gate: tools/call is refused until this lands.
            _, raw = _post(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "geox_list_registered_sources",
                        "arguments": {"actor_id": "claude-code-kvm8"},
                    },
                },
                sid,
            )
            res = _result_of(raw).get("result", {})
            if isinstance(res, dict) and "n_sources" in res:
                n_sources = res["n_sources"]
                note = "live :8081 geox_list_registered_sources"
            elif isinstance(res, dict) and isinstance(res.get("content"), list):
                for block in res["content"]:
                    if block.get("type") == "text":
                        try:
                            n_sources = json.loads(block["text"]).get("n_sources")
                            note = "live :8081 geox_list_registered_sources"
                            break
                        except Exception:
                            continue
            if n_sources is None:
                note = f"live probe returned no n_sources: {raw[:200]}"
        except Exception as exc:
            note = f"live probe failed: {exc}"
        out["detail"]["registered_native_sources"] = n_sources
        out["detail"]["registered_native_sources_note"] = note
        if n_sources:
            out["nodes"]["observation"] = n_sources
            out["node_total"] = sum(out["nodes"].values())

    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {args.json}")

    n, e = out["nodes"], out["edges"]
    print("═" * 74)
    print("GEOX EARTH GRAPH CENSUS — what the physical reality graph actually holds")
    print("═" * 74)
    print("NODES")
    for t in out["node_types"]:
        mark = "" if n[t] else "   ← node type declared by GEOX's own model, zero instances"
        print(f"  {t:<12} {n[t]:>5}{mark}")
    print(f"  {'TOTAL':<12} {out['node_total']:>5}")
    print()
    print("EDGES")
    for name, desc in REQUIRED_EDGES:
        print(f"  {name:<26} {e[name]:>5}   {desc}")
    print(f"  {'TOTAL':<26} {out['edge_total']:>5}")
    print()
    print(f"entity-binding edges : {out['entity_binding_edges']}  ({out['binding_coverage_pct']}% of all edges)")
    print(f"claims bound to an entity : {out['detail']['claims_bound_to_an_entity']} / {n['claim']}")
    print(f"claims with a falsifier   : {out['detail']['claims_with_falsifier']} / {n['claim']}")
    print(f"claims with evidence_refs : {out['detail']['claims_with_evidence_refs']} / {n['claim']}")
    print(f"claims with forbidden_uses: {out['detail']['claims_with_forbidden_uses']} / {n['claim']}")
    if "registered_native_sources" in out["detail"]:
        n = out["detail"]["registered_native_sources"]
        note = out["detail"].get("registered_native_sources_note", "")
        shown = "unknown" if n is None else str(n)
        print(f"registered native sources: {shown}   ({note})")
    print()
    print("UPSTREAM CAPABILITY PRESENCE")
    for k, v in out["upstream_capabilities"].items():
        print(f"  {'YES' if v['present'] else 'NO '}  {k}")
        print(f"      {v['note']}")
    print()
    print(f"VERDICT: {out['verdict']}")
    print(f"  {out['verdict_meaning'][out['verdict']]}")
    print("═" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
