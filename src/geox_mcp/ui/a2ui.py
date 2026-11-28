"""a2ui.py — A2UI v1.0 over MCP transport for GEOX evidence surfaces.

Why this module exists (real failure class, measured 2026-11-27):
    GEOX already ships an A2UI v1.0 catalog (``geox.evidence.v1``, staged at
    ``/root/forge_work/a2ui``) and already ships MCP Apps over ``ui://``. But a
    grep of the whole source tree returned **0 hits** for ``a2ui://`` and
    **0 hits** for ``updateDataModel``: no A2UI renderer could ever consume the
    catalog, because no layout resource and no data-update message were served.
    This module adds that missing transport. It changes no public tool.

Protocol contract (probed, not remembered):
    * https://a2ui.org/guides/a2ui-over-mcp/ — publish static layouts as
      ``a2ui://`` resources with MIME ``application/a2ui+json``; the payload is
      ``createSurface`` + ``updateComponents``; per-call results carry
      ``updateDataModel``.
    * https://a2ui.org/concepts/messages/ — v1.0 wire shape is
      ``{"version": "1.0", "<messageKey>": {...}}``; data bindings are
      ``{"@path": "/key"}``; a component may name its own catalog via
      ``"@catalogId"``.
    * Reference sample ``samples/community/mcp/a2ui-over-mcp-recipe`` — the
      resource payload is a JSON **array** of messages.

Staging boundary (do not cross without the P1 gate):
    ``/root/forge_work/a2ui/README.md`` keeps ``geox.evidence.v1`` in OFFLINE
    STAGING until the T1-T7 battery passes LIVE, the T2 announce lands, and F13
    does not object (review 2026-12-21). This module publishes the *transport
    contract* only. It does not ship the catalog to the live cockpit, and it
    does not mutate the catalog.

Evidence-class discipline:
    confidence is capped at 0.90 (F7 HUMILITY, same cap as the catalog schema);
    ``SPEC`` is renderable but must render quarantined, so callers pass the tag
    through unchanged rather than laundering it.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger("geox.ui.a2ui")

# ── Constants ────────────────────────────────────────────────────────────────

A2UI_MIME = "application/a2ui+json"
A2UI_PROTOCOL_VERSION = "1.0"

BASIC_CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"
GEOX_EVIDENCE_CATALOG_ID = "https://arif-fazil.com/a2ui/catalogs/geox/evidence/v1/catalog.json"

STRAT_CARD_URI = "a2ui://geox/evidence/strat-card"
STRAT_CARD_SURFACE_ID = "geox_strat_card"

POINT_WITNESS_URI = "a2ui://geox/point-witness"
POINT_WITNESS_SURFACE_ID = "geox_point_witness"

# Mirrors the catalog enum; unknown tags are rejected rather than rendered.
EPISTEMIC_TAGS = frozenset({"OBS", "DER", "INT", "SPEC", "UNKNOWN"})
COVERAGE_CLASSES = frozenset({"unit_polygon", "map_polygon", "none"})
FRESHNESS_STATES = frozenset({"LIVE", "STALE", "UNKNOWN"})
HUMILITY_CAP = 0.90

# Staged catalog is outside the repo by design (owned by 333-AGI staging).
_CATALOG_STAGE_PATH = Path(
    os.environ.get(
        "GEOX_A2UI_CATALOG_PATH",
        "/root/forge_work/a2ui/catalogs/geox/evidence/v1/catalog.json",
    )
)


def _uri_registered(mcp: FastMCP, uri: str) -> bool:
    local = getattr(mcp, "_local_provider", None)
    comps = getattr(local, "_components", {}) if local else {}
    return f"resource:{uri}@" in comps


# ── Template (static layout, fetched once by the renderer) ───────────────────


def build_strat_card_template() -> list[dict[str, Any]]:
    """Return the ``a2ui://geox/evidence/strat-card`` resource payload.

    Array of two v1.0 messages: ``createSurface`` then ``updateComponents``.
    Root uses the basic catalog so any A2UI renderer can mount it; the four
    evidence components name ``geox.evidence.v1`` per-component.
    """
    create_surface = {
        "version": A2UI_PROTOCOL_VERSION,
        "createSurface": {
            "surfaceId": STRAT_CARD_SURFACE_ID,
            "catalogId": BASIC_CATALOG_ID,
            "sendDataModel": False,
        },
    }

    update_components = {
        "version": A2UI_PROTOCOL_VERSION,
        "updateComponents": {
            "surfaceId": STRAT_CARD_SURFACE_ID,
            "components": [
                {"id": "root", "component": "Card", "child": "card_body"},
                {
                    "id": "card_body",
                    "component": "Column",
                    "children": ["title", "badge", "margin", "coverage", "freshness"],
                },
                {"id": "title", "component": "Text", "text": {"@path": "/title"}},
                {
                    "id": "badge",
                    "component": "EpistemicTagBadge",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "tag": {"@path": "/epistemic_tag"},
                    "label": {"@path": "/label"},
                    "confidence": {"@path": "/confidence"},
                    "source": {"@path": "/source"},
                },
                {
                    "id": "margin",
                    "component": "HumilityMarginBar",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "confidence": {"@path": "/confidence"},
                    "margin_pct": {"@path": "/margin_pct"},
                    "basis": {"@path": "/margin_basis"},
                },
                {
                    "id": "coverage",
                    "component": "CoverageClassBanner",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "coverage_class": {"@path": "/coverage_class"},
                    "answered_by": {"@path": "/answered_by"},
                    "detail": {"@path": "/coverage_detail"},
                },
                {
                    "id": "freshness",
                    "component": "SourceFreshnessBadge",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "freshness": {"@path": "/freshness"},
                    "observed_at": {"@path": "/observed_at"},
                    "instrument": {"@path": "/instrument"},
                },
            ],
        },
    }
    return [create_surface, update_components]


# ── Data model (per-call delta) ──────────────────────────────────────────────


def build_strat_card_data(
    *,
    title: str,
    epistemic_tag: str,
    confidence: float,
    margin_pct: float,
    margin_basis: str,
    coverage_class: str,
    answered_by: str,
    coverage_detail: str,
    freshness: str,
    observed_at: str,
    instrument: str,
    label: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Build the surface data model, enforcing the catalog's own discipline.

    Raises ``ValueError`` on anything the catalog schema would reject, so a bad
    value fails at the producer instead of rendering as a plausible card.
    """
    if epistemic_tag not in EPISTEMIC_TAGS:
        raise ValueError(f"epistemic_tag must be one of {sorted(EPISTEMIC_TAGS)}, got {epistemic_tag!r}")
    if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= HUMILITY_CAP):
        raise ValueError(f"confidence must be within [0, {HUMILITY_CAP}] (F7 cap), got {confidence!r}")
    if not isinstance(margin_pct, (int, float)) or not (0.0 <= float(margin_pct) <= 100.0):
        raise ValueError(f"margin_pct must be within [0, 100], got {margin_pct!r}")
    if coverage_class not in COVERAGE_CLASSES:
        raise ValueError(f"coverage_class must be one of {sorted(COVERAGE_CLASSES)}, got {coverage_class!r}")
    if freshness not in FRESHNESS_STATES:
        raise ValueError(f"freshness must be one of {sorted(FRESHNESS_STATES)}, got {freshness!r}")

    data: dict[str, Any] = {
        "title": title,
        "epistemic_tag": epistemic_tag,
        "confidence": float(confidence),
        "margin_pct": float(margin_pct),
        "margin_basis": margin_basis,
        "coverage_class": coverage_class,
        "answered_by": answered_by,
        "coverage_detail": coverage_detail,
        "freshness": freshness,
        "observed_at": observed_at,
        "instrument": instrument,
    }
    if label is not None:
        data["label"] = label
    if source is not None:
        data["source"] = source
    return data


def build_update_data_model(
    data: dict[str, Any],
    *,
    surface_id: str = STRAT_CARD_SURFACE_ID,
    path: str = "/",
) -> dict[str, Any]:
    """Return a v1.0 ``updateDataModel`` message (delta only, no component tree)."""
    return {
        "version": A2UI_PROTOCOL_VERSION,
        "updateDataModel": {
            "surfaceId": surface_id,
            "path": path,
            "value": data,
        },
    }


def build_strat_card_from_macrostrat(payload: dict[str, Any]) -> dict[str, Any]:
    """Map a GEOX ``macrostrat_units`` interpreted payload onto the card delta.

    Accepts the shape produced by ``geox_basin(mode="macrostrat")``. Missing
    optional fields degrade to honest ``UNKNOWN`` rather than to a guess.
    """
    upstream = payload.get("upstream_api") or {}
    answered_by = f"macrostrat {upstream.get('service', 'unknown')} {upstream.get('version', 'unknown')}".strip()
    build_date = upstream.get("build_date")
    unit_count = payload.get("unit_count")
    coverage_class = payload.get("coverage_class", "none")
    observed_at = build_date if isinstance(build_date, str) else "UNKNOWN"

    return build_strat_card_data(
        title=f"Macrostrat units — {unit_count if unit_count is not None else 'UNKNOWN'} at point",
        epistemic_tag="OBS" if unit_count else "UNKNOWN",
        confidence=HUMILITY_CAP,
        margin_pct=0.0,
        margin_basis="deterministic point query (no stochastic margin); zero units is a coverage statement, not an estimate",
        coverage_class=coverage_class,
        answered_by=answered_by,
        coverage_detail=str(payload.get("coverage_explanation", "")),
        freshness="LIVE" if build_date else "UNKNOWN",
        observed_at=observed_at,
        instrument="macrostrat.org/api/v2/units + /geologic_units/map",
        label=f"{unit_count} units" if unit_count is not None else None,
        source=str(payload.get("source", "macrostrat.org/api/v2/units")),
    )


# ── Point witness (Gap #1: single-call map_query_v2) ────────────────────────


def build_point_witness_template() -> list[dict[str, Any]]:
    """Static layout for ``a2ui://geox/point-witness`` (one globe click).

    Conditionality lives in the DATA, not the layout: the coverage banner text
    and the units summary are server-composed strings bound to paths, so an
    empty coverage renders an explicit NO-COVERAGE sentence instead of an empty
    component tree. No @checks (those validate input; they do not hide UI).
    """
    create_surface = {
        "version": A2UI_PROTOCOL_VERSION,
        "createSurface": {
            "surfaceId": POINT_WITNESS_SURFACE_ID,
            "catalogId": BASIC_CATALOG_ID,
            "sendDataModel": False,
        },
    }
    update_components = {
        "version": A2UI_PROTOCOL_VERSION,
        "updateComponents": {
            "surfaceId": POINT_WITNESS_SURFACE_ID,
            "components": [
                {"id": "root", "component": "Card", "child": "card_body"},
                {
                    "id": "card_body",
                    "component": "Column",
                    "children": [
                        "title",
                        "badge",
                        "margin",
                        "coverage",
                        "freshness",
                        "terrain",
                        "units_summary",
                        "commit_gate",
                    ],
                },
                {"id": "title", "component": "Text", "text": {"@path": "/title"}},
                {
                    "id": "badge",
                    "component": "EpistemicTagBadge",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "tag": {"@path": "/epistemic/tag"},
                    "label": {"@path": "/epistemic/label"},
                    "confidence": {"@path": "/epistemic/confidence"},
                    "source": {"@path": "/provenance/upstream_api"},
                },
                {
                    "id": "margin",
                    "component": "HumilityMarginBar",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "confidence": {"@path": "/epistemic/confidence"},
                    "margin_pct": {"@path": "/epistemic/margin_pct"},
                    "basis": {"@path": "/epistemic/margin_basis"},
                },
                {
                    "id": "coverage",
                    "component": "CoverageClassBanner",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "coverage_class": {"@path": "/epistemic/coverage_class"},
                    "answered_by": {"@path": "/provenance/upstream_api"},
                    "detail": {"@path": "/coverage_note"},
                },
                {
                    "id": "freshness",
                    "component": "SourceFreshnessBadge",
                    "@catalogId": GEOX_EVIDENCE_CATALOG_ID,
                    "freshness": {"@path": "/provenance/freshness"},
                    "observed_at": {"@path": "/provenance/build_date"},
                    "instrument": {"@path": "/provenance/instrument"},
                },
                {"id": "terrain", "component": "Text", "text": {"@path": "/terrain_note"}},
                {"id": "units_summary", "component": "Text", "text": {"@path": "/units_summary"}},
                {"id": "commit_gate", "component": "Text", "text": {"@path": "/commit_gate"}},
            ],
        },
    }
    return [create_surface, update_components]


def _format_upstream(upstream: dict[str, Any]) -> str:
    if not upstream.get("available"):
        return "upstream build: UNKNOWN"
    commit = str(upstream.get("commit") or "")[:7]
    parts = [str(upstream.get("service") or ""), str(upstream.get("version") or "")]
    label = " ".join(p for p in parts if p).strip() or "unknown"
    return f"{label} ({commit})" if commit else label


def build_point_witness_data(
    point: dict[str, Any],
    *,
    lat: float,
    lng: float,
    z: int,
    kernel_verdict: str = "HOLD",
    claim_state: str = "HYPOTHESIS",
    vault999_status: str = "PENDING",
) -> dict[str, Any]:
    """Map a ``macrostrat_point`` payload onto the point-witness data model.

    The kernel verdict is quoted, never upgraded: any verdict other than SEAL
    renders the commit gate as BLOCKED. ``receipt_sha256`` stays None here
    because the A2UI builder never mints receipts — the tool envelope does.
    """
    upstream = point.get("upstream_api") or {}
    coverage_class = str(point.get("coverage_class") or "none")
    units = point.get("units") or []
    refs_count = int(point.get("refs_count") or 0)
    # The compact boundary drops list fields but preserves unit_count/refs_count.
    # Trust the count, not the (possibly compacted) list, or a covered point
    # would render as "0 map polygons" with refs beside it.
    unit_count = int(point.get("unit_count") if point.get("unit_count") is not None else len(units))
    elevation = point.get("elevation_m")
    has_columns = bool(point.get("has_columns"))
    regions = int(point.get("region_count") or 0)

    if coverage_class == "none":
        coverage_note = (
            "Upstream Macrostrat coverage: none at this coordinate. "
            "Use local JMG 1:500k or a Basin Dossier witness — do not read this as no bedrock."
        )
        units_summary = f"0 map polygons · 0 refs · has_columns: {'yes' if has_columns else 'no'}"
        tag, label = "UNKNOWN", "NO UPSTREAM COVERAGE"
    elif coverage_class == "map_polygon":
        coverage_note = (
            "map_polygon — a generalized map polygon exists; formation-level unit "
            "columns do not. Interpretations remain HYPOTHESIS until arifOS adjudication."
        )
        units_summary = _units_line(units, refs_count, unit_count)
        tag, label = "OBS", "MAP POLYGON ONLY"
    else:
        coverage_note = (
            "unit_polygon — formation names, lithology and age resolve from measured "
            "columns. SPEC/HYPOTHESIS until arifOS adjudication."
        )
        units_summary = _units_line(units, refs_count, unit_count)
        tag, label = "OBS", "UNIT POLYGONS PRESENT"

    verdict = str(kernel_verdict or "UNKNOWN")
    commit_gate = (
        "PROMOTE ENABLED — kernel_verdict=SEAL"
        if verdict == "SEAL"
        else f"BLOCKED — kernel_verdict={verdict}; no write or commit from this surface"
    )

    return {
        "title": f"Macrostrat point — {lat:.4f}, {lng:.4f} (z{z})",
        "epistemic": {
            "tag": tag,
            "label": label,
            "confidence": HUMILITY_CAP,
            "margin_pct": 0.0,
            "margin_basis": (
                "deterministic point query (no stochastic margin); zero polygons is a "
                "coverage statement, not an estimate"
            ),
            "coverage_class": coverage_class,
            "claim_state": claim_state,
            "vault999_status": vault999_status,
            "kernel_verdict": verdict,
        },
        "provenance": {
            "upstream_api": _format_upstream(upstream),
            "build_date": upstream.get("build_date") or "UNKNOWN",
            "freshness": "LIVE" if upstream.get("build_date") else "UNKNOWN",
            "instrument": "macrostrat.org/api/v2/mobile/map_query_v2",
            "license": "CC-BY-4.0 · Peters et al. (2018)",
            "receipt_sha256": None,
        },
        "terrain": {
            "elevation_m": elevation,
            "has_columns": has_columns,
            "region_count": regions,
        },
        "terrain_note": (
            f"elevation {elevation if elevation is not None else 'UNKNOWN'} m · "
            f"columns: {'yes' if has_columns else 'no'} · {regions} regions"
        ),
        "coverage_note": coverage_note,
        "units": units or [],
        "units_summary": units_summary,
        "commit_gate": commit_gate,
    }


def _units_line(units: list[dict[str, Any]], refs_count: int, unit_count: int | None = None) -> str:
    count = unit_count if unit_count is not None else len(units)
    if not units:
        # Counts survive the compact boundary; the list may not.
        return f"{count} map polygons · {refs_count} refs"
    first = units[0]
    name = str(first.get("name") or "unnamed").strip()
    age = first.get("age")
    age_txt = str(age) if age else "age UNKNOWN"
    return f"{len(units)} map polygon(s) · {refs_count} refs · first: {name} ({age_txt})"


# ── Registration ─────────────────────────────────────────────────────────────


def register_a2ui_resources(mcp: FastMCP) -> None:
    """Register the A2UI-over-MCP layout resources (idempotent, read-only)."""
    layouts: list[tuple[str, str, Any]] = [
        (
            STRAT_CARD_URI,
            "A2UI v1.0 static layout for a GEOX evidence card "
            "(EpistemicTagBadge + HumilityMarginBar + CoverageClassBanner + "
            "SourceFreshnessBadge). Fetch once; apply updateDataModel deltas.",
            build_strat_card_template,
        ),
        (
            POINT_WITNESS_URI,
            "A2UI v1.0 static layout for a single Macrostrat point click "
            "(coverage_class, elevation, hasColumns, refs, kernel commit gate). "
            "Fetch once; apply one updateDataModel delta per globe click.",
            build_point_witness_template,
        ),
    ]

    for uri, description, builder in layouts:
        if _uri_registered(mcp, uri):
            logger.debug("A2UI resource already registered: %s — skip", uri)
            continue
        template_json = json.dumps(builder(), indent=2)

        def _make_handler(content: str):
            async def _handler() -> str:
                return content

            return _handler

        mcp.resource(uri, description=description, mime_type=A2UI_MIME)(_make_handler(template_json))
        logger.info("A2UI resource registered: %s (%s)", uri, A2UI_MIME)


def catalog_stage_path() -> Path:
    """Exposed for tests/ops: where the staged catalog lives, if present."""
    return _CATALOG_STAGE_PATH
