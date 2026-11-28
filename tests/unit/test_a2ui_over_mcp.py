"""A2UI v1.0 over MCP — transport contract tests (staged, no cockpit ship).

These tests guard the layer that was missing on 2026-11-27: GEOX had a catalog
(``geox.evidence.v1``) and ``ui://`` MCP Apps, but served no ``a2ui://`` layout
and returned no ``updateDataModel``. They assert the wire shapes against the
contract read from a2ui.org (not from memory), and they cross-check the template
against the staged catalog so the two cannot drift.

They do NOT assert that the catalog is deployed at its ``$id`` URL, and they do
NOT ship anything to the live cockpit — the P1 gate in
``/root/forge_work/a2ui/README.md`` still owns that decision.
"""

from __future__ import annotations

import json

import pytest

from geox_mcp.ui import a2ui

FORBIDDEN = ("javascript:", "data:text/html", "vbscript:", "file://", "openUrl")


def _walk_paths(node, out: set[str]) -> None:
    if isinstance(node, dict):
        if set(node) == {"@path"} and isinstance(node["@path"], str):
            out.add(node["@path"])
            return
        for value in node.values():
            _walk_paths(value, out)
    elif isinstance(node, list):
        for value in node:
            _walk_paths(value, out)


def _components() -> list[dict]:
    template = a2ui.build_strat_card_template()
    return template[1]["updateComponents"]["components"]


def test_template_is_array_of_two_v1_messages():
    template = a2ui.build_strat_card_template()
    assert isinstance(template, list) and len(template) == 2
    keys = [set(msg) - {"version"} for msg in template]
    assert keys == [{"createSurface"}, {"updateComponents"}]
    assert all(msg["version"] == "1.0" for msg in template)


def test_surface_ids_match_across_messages():
    create, update = a2ui.build_strat_card_template()
    assert create["createSurface"]["surfaceId"] == update["updateComponents"]["surfaceId"] == a2ui.STRAT_CARD_SURFACE_ID


def test_root_and_references_resolve():
    comps = _components()
    ids = [c["id"] for c in comps]
    assert len(ids) == len(set(ids)), "component ids must be unique"
    assert "root" in ids
    for comp in comps:
        for key in ("child",):
            if key in comp:
                assert comp[key] in ids, f"{comp['id']}.{key} -> {comp[key]} missing"
        for child in comp.get("children", []):
            assert child in ids, f"{comp['id']} child {child} missing"


def test_domain_components_name_the_geox_catalog():
    domain = [c for c in _components() if "@catalogId" in c]
    assert {c["component"] for c in domain} == {
        "EpistemicTagBadge",
        "HumilityMarginBar",
        "CoverageClassBanner",
        "SourceFreshnessBadge",
    }
    assert all(c["@catalogId"] == a2ui.GEOX_EVIDENCE_CATALOG_ID for c in domain)


def test_every_bound_path_is_supplied_by_the_data_model():
    data = a2ui.build_strat_card_data(
        title="Macrostrat units — 0 at point",
        epistemic_tag="UNKNOWN",
        confidence=0.9,
        margin_pct=0.0,
        margin_basis="deterministic point query",
        coverage_class="none",
        answered_by="macrostrat api-v2 2.6.0",
        coverage_detail="No mapped bedrock at this point.",
        freshness="LIVE",
        observed_at="2026-11-03T06:40:03.629Z",
        instrument="macrostrat.org/api/v2/units",
        label="0 units",
        source="macrostrat.org/api/v2/units",
    )
    bound: set[str] = set()
    _walk_paths(_components(), bound)
    missing = {p for p in bound if p.strip("/").split("/")[0] not in data}
    assert not missing, f"template binds paths with no value: {sorted(missing)}"


def test_update_data_model_shape():
    msg = a2ui.build_update_data_model({"title": "x"})
    assert msg["version"] == "1.0"
    payload = msg["updateDataModel"]
    assert payload["surfaceId"] == a2ui.STRAT_CARD_SURFACE_ID
    assert payload["path"] == "/"
    assert payload["value"] == {"title": "x"}


@pytest.mark.parametrize(
    "field,value",
    [
        ("epistemic_tag", "FACT"),
        ("confidence", 0.95),
        ("confidence", -0.1),
        ("margin_pct", 101),
        ("coverage_class", "bedrock"),
        ("freshness", "FRESH"),
    ],
)
def test_catalog_discipline_is_enforced_at_the_producer(field, value):
    kwargs = dict(
        title="t",
        epistemic_tag="OBS",
        confidence=0.5,
        margin_pct=10.0,
        margin_basis="b",
        coverage_class="unit_polygon",
        answered_by="a",
        coverage_detail="d",
        freshness="LIVE",
        observed_at="2026-11-27T00:00:00Z",
        instrument="i",
    )
    kwargs[field] = value
    with pytest.raises(ValueError):
        a2ui.build_strat_card_data(**kwargs)


def test_macrostrat_mapping_keeps_zero_honest():
    payload = {
        "unit_count": 0,
        "coverage_class": "none",
        "coverage_explanation": "No mapped bedrock at this point.",
        "upstream_api": {
            "service": "api-v2",
            "version": "2.6.0",
            "build_date": "2026-11-03T06:40:03.629Z",
        },
        "source": "macrostrat.org/api/v2/units",
    }
    data = a2ui.build_strat_card_from_macrostrat(payload)
    assert data["epistemic_tag"] == "UNKNOWN"
    assert data["coverage_class"] == "none"
    assert data["confidence"] <= a2ui.HUMILITY_CAP
    assert "api-v2" in data["answered_by"]


def test_no_executable_or_link_affordances():
    blob = json.dumps(a2ui.build_strat_card_template())
    for token in FORBIDDEN:
        assert token not in blob, f"forbidden token in template: {token}"


def _resolve(data, path: str):
    cur = data
    for part in path.strip("/").split("/"):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur


def test_point_witness_binds_only_paths_the_model_supplies():
    point = {
        "coverage_class": "unit_polygon",
        "coverage_explanation": "unit polygons",
        "has_columns": True,
        "elevation_m": 1601,
        "region_count": 3,
        "units": [{"name": "Broadway Alluvium", "age": "Late Pleistocene"}],
        "unit_count": 1,
        "refs_count": 2,
        "upstream_api": {
            "available": True,
            "service": "api-v2",
            "version": "2.6.0",
            "commit": "0ec2ff00610459b929da7c2577df467a12d71686",
            "build_date": "2026-11-03T06:40:03.629Z",
        },
    }
    data = a2ui.build_point_witness_data(point, lat=39.7392, lng=-104.9903, z=8)
    template = a2ui.build_point_witness_template()
    bound: set[str] = set()
    _walk_paths(template[1]["updateComponents"]["components"], bound)
    for path in bound:
        _resolve(data, path)  # raises KeyError if the layout binds a missing value


def test_point_witness_zero_coverage_is_explicit_and_never_bedrock():
    point = {
        "coverage_class": "none",
        "has_columns": False,
        "elevation_m": 0,
        "region_count": 2,
        "units": [],
        "unit_count": 0,
        "refs_count": 0,
        "upstream_api": {"available": True, "service": "api-v2", "version": "2.6.0"},
    }
    data = a2ui.build_point_witness_data(point, lat=5.3, lng=115.0, z=8)
    assert data["epistemic"]["coverage_class"] == "none"
    assert data["epistemic"]["tag"] == "UNKNOWN"
    assert "NO UPSTREAM COVERAGE" in data["epistemic"]["label"]
    assert "none at this coordinate" in data["coverage_note"]
    assert "no bedrock" in data["coverage_note"]
    assert data["units"] == []


def test_point_witness_summary_survives_compacted_unit_list():
    # The compact boundary drops list fields but preserves unit_count. The card
    # must report the count, not "0 map polygons" with refs beside it.
    point = {
        "coverage_class": "unit_polygon",
        "has_columns": True,
        "elevation_m": 1601,
        "region_count": 3,
        "units": None,
        "unit_count": 3,
        "refs_count": 5,
        "upstream_api": {"available": True, "service": "api-v2", "version": "2.6.0"},
    }
    data = a2ui.build_point_witness_data(point, lat=39.7392, lng=-104.9903, z=8)
    assert data["units_summary"].startswith("3 map polygons")
    assert "5 refs" in data["units_summary"]
    assert data["units"] == []


def test_point_witness_commit_gate_quotes_the_kernel():
    point = {"coverage_class": "none", "upstream_api": {"available": False}}
    held = a2ui.build_point_witness_data(point, lat=0, lng=0, z=8, kernel_verdict="HOLD")
    sealed = a2ui.build_point_witness_data(point, lat=0, lng=0, z=8, kernel_verdict="SEAL")
    assert held["commit_gate"].startswith("BLOCKED")
    assert "HOLD" in held["commit_gate"]
    assert sealed["commit_gate"].startswith("PROMOTE ENABLED")
    assert held["provenance"]["receipt_sha256"] is None  # never minted by the UI layer


def test_summarize_mobile_point_normalizes_three_coverage_classes():
    from geox_mcp.tools.macrostrat_client import MacrostratClient

    client = MacrostratClient.__new__(MacrostratClient)  # no cache init, pure function

    denver = {
        "success": {
            "data": {
                "elevation": 1601,
                "hasColumns": True,
                "regions": [{}, {}, {}],
                "mapData": [{"name": "Gravels", "age": "Quaternary", "refs": [{}, {}]}],
            }
        }
    }
    offshore = {"success": {"data": {"elevation": 0, "hasColumns": False, "regions": [{}, {}], "mapData": []}}}
    map_only = {"success": {"data": {"elevation": 10, "hasColumns": False, "regions": [], "mapData": [{"name": "x"}]}}}

    d = client.summarize_mobile_point(denver)
    assert d["coverage_class"] == "unit_polygon"
    assert d["has_columns"] is True
    assert d["elevation_m"] == 1601
    assert d["refs_count"] == 2

    o = client.summarize_mobile_point(offshore)
    assert o["coverage_class"] == "none"
    assert o["unit_count"] == 0
    assert o["region_count"] == 2

    m = client.summarize_mobile_point(map_only)
    assert m["coverage_class"] == "map_polygon"


def test_template_matches_staged_catalog_when_present():
    path = a2ui.catalog_stage_path()
    if not path.exists():
        pytest.skip("staged catalog not present on this host")
    catalog = json.loads(path.read_text())
    assert catalog["catalogId"] or catalog["$id"]
    assert catalog["$id"] == a2ui.GEOX_EVIDENCE_CATALOG_ID
    declared = set(catalog["components"])
    used = {c["component"] for c in _components() if "@catalogId" in c}
    assert used <= declared, f"template uses undeclared components: {sorted(used - declared)}"
    assert catalog["protocolVersion"] == a2ui.A2UI_PROTOCOL_VERSION
