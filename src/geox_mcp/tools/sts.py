"""
geox_sts — State Transition Surface Engine
===========================================
Reality loop: graph → add_state → add_transition → translate → contrast → loop.
Basin = state machine, not horizon stack. Diachroneity default.

Modes (routed via geox_basin mode=sts):
  graph       — Return full StateGraph summary
  add_node    — Register a BasinNode
  add_sts     — Add a StateTransitionSurface edge
  translate   — Semantic label lookup across schemes
  contrast    — Emit ContrastFlag when two STS disagree beyond threshold
  example     — Return the Layang-Layang canonical example

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal

from geox.egs.models.sts import (
    BasinNode,
    BasinState,
    DiachroneityClass,
    StateGraph,
    StateTransitionSurface,
)
from geox.egs.models.translation import TranslationLayer, layang_layang_example

# ── In-memory state graphs (reality loop working memory) ───────────────────
# Persistence to DSG/VAULT999 is Phase 2.6.
_STATE_GRAPHS: dict[str, StateGraph] = {}
_TRANSLATION_LAYERS: dict[str, TranslationLayer] = {
    "layang_layang": layang_layang_example(),
}


def _get_or_create_graph(graph_id: str, name: str = "", basin_id: str = "") -> StateGraph:
    """Get existing or create new StateGraph."""
    if graph_id not in _STATE_GRAPHS:
        _STATE_GRAPHS[graph_id] = StateGraph(name=name or graph_id, basin_id=basin_id)
    return _STATE_GRAPHS[graph_id]


async def geox_sts(
    graph_id: str = "default",
    mode: Literal["graph", "add_node", "add_sts", "translate", "contrast", "example"] = "graph",
    # add_node params
    node_name: str = "",
    node_states: list[str] | None = None,
    node_bbox: list[float] | None = None,
    node_description: str = "",
    parent_basin_id: str = "",
    # add_sts params
    basin_node_id: str = "",
    from_state: str = "",
    to_state: str = "",
    evidence_types: list[str] | None = None,
    age_min_ma: float | None = None,
    age_max_ma: float | None = None,
    diachroneity_class: str = "strongly_diachronous",
    translation_schemes: dict[str, str] | None = None,
    sts_confidence: Literal["HIGH", "MED", "LOW"] = "MED",
    # translate params
    token: str = "",
    from_scheme: str = "",
    to_scheme: str = "",
    translation_id: str = "layang_layang",
    # contrast params
    sts_a_id: str = "",
    sts_b_id: str = "",
    contrast_metric: str = "age_Myr",
    contrast_threshold: float = 5.0,
    contrast_delta: float = 0.0,
    # graph params
    graph_name: str = "",
    basin_ref_id: str = "",
) -> dict[str, Any]:
    """State Transition Surface engine — basin as state machine.

    THE eureka: a basin is not a stack of horizons. It is a state machine
    over space and time. Reality loop: observe → hypothesize → test → contrast → loop.
    """

    # ── graph — return current state ───────────────────────────────────────
    if mode == "graph":
        g = _STATE_GRAPHS.get(graph_id)
        if g is None:
            return {"graph_id": graph_id, "status": "EMPTY", "hint": "Add nodes and transitions to build the graph."}
        return {"status": "OK", **g.to_summary()}

    # ── example — Layang-Layang canonical ──────────────────────────────────
    if mode == "example":
        tl = _TRANSLATION_LAYERS["layang_layang"]
        # Build a demo StateGraph
        g = StateGraph(name="Layang-Layang Example", basin_id="layang_layang")
        n = BasinNode(
            name="Layang-Layang",
            parent_basin_id="layang_layang",
            states=[BasinState.PRERIFT, BasinState.SYN_RIFT_1, BasinState.SYN_RIFT_2, BasinState.BREAKUP, BasinState.DRIFT],
        )
        g.add_node(n)
        sts1 = StateTransitionSurface(
            basin_node_id=n.id,
            from_state=BasinState.PRERIFT,
            to_state=BasinState.SYN_RIFT_1,
            evidence_types=["seismic_facies_change", "unconformity"],
            age_band_ma=(40.0, 33.0),
            diachroneity_class=DiachroneityClass.STRONGLY_DIACHRONOUS,
            translation_layer={"PCSB": "ROU", "TTE": "ROU_event", "Published": "ROU_Prabal2024"},
        )
        g.add_transition(sts1)
        return {"status": "OK", "translation_layer": tl.to_summary(), **g.to_summary()}

    # ── add_node ───────────────────────────────────────────────────────────
    if mode == "add_node":
        if not node_name:
            return {"status": "ERROR", "reason": "node_name required"}
        states = [BasinState(s) for s in (node_states or [])]
        bbox_tuple: tuple[float, float, float, float] | None = None
        if node_bbox and len(node_bbox) == 4:
            bbox_tuple = (float(node_bbox[0]), float(node_bbox[1]), float(node_bbox[2]), float(node_bbox[3]))
        node = BasinNode(
            name=node_name,
            states=states,
            bbox=bbox_tuple,
            description=node_description,
            parent_basin_id=parent_basin_id or basin_ref_id,
        )
        g = _get_or_create_graph(graph_id, name=graph_name, basin_id=basin_ref_id)
        nid = g.add_node(node)
        return {"status": "OK", "node_id": nid, "graph_id": g.id, "graph_version": g.version}

    # ── add_sts ────────────────────────────────────────────────────────────
    if mode == "add_sts":
        if not basin_node_id or not from_state or not to_state:
            return {"status": "ERROR", "reason": "basin_node_id, from_state, to_state required"}
        try:
            dc = DiachroneityClass(diachroneity_class)
        except ValueError:
            return {
                "status": "ERROR",
                "reason": f"Invalid diachroneity_class: {diachroneity_class}. Valid: {[d.value for d in DiachroneityClass]}",
            }
        age_band: tuple[float, float] | None = None
        if age_min_ma is not None and age_max_ma is not None:
            age_band = (age_min_ma, age_max_ma)
        sts = StateTransitionSurface(
            basin_node_id=basin_node_id,
            from_state=BasinState(from_state),
            to_state=BasinState(to_state),
            evidence_types=evidence_types or [],
            age_band_ma=age_band,
            diachroneity_class=dc,
            translation_layer=translation_schemes or {},
            confidence=sts_confidence,
        )
        g = _get_or_create_graph(graph_id, name=graph_name, basin_id=basin_ref_id)
        try:
            sid = g.add_transition(sts)
            return {"status": "OK", "sts_id": sid, "graph_id": g.id, "graph_version": g.version}
        except ValueError as e:
            return {"status": "ERROR", "reason": str(e)}

    # ── translate — semantic label lookup ──────────────────────────────────
    if mode == "translate":
        if not token:
            return {"status": "ERROR", "reason": "token required"}
        tl = _TRANSLATION_LAYERS.get(translation_id, _TRANSLATION_LAYERS["layang_layang"])
        entry = tl.lookup(token)
        if entry is None:
            return {"status": "NOT_FOUND", "token": token, "hint": "Token not registered in translation layer. Add entry first."}
        result = {"status": "OK", "token": token, "schemes": entry.schemes, "notes": entry.notes}
        if from_scheme and to_scheme:
            translated = tl.translate(token, from_scheme, to_scheme)
            result["translation"] = translated
            result["from_scheme"] = from_scheme
            result["to_scheme"] = to_scheme
        return result

    # ── contrast — emit ContrastFlag, fork scenarios ──────────────────────
    if mode == "contrast":
        if not sts_a_id or not sts_b_id:
            return {"status": "ERROR", "reason": "sts_a_id and sts_b_id required"}
        g = _STATE_GRAPHS.get(graph_id)
        if g is None:
            return {"status": "ERROR", "reason": f"Graph {graph_id} not found"}
        result = g.emit_contrast(sts_a_id, sts_b_id, contrast_metric, contrast_delta, contrast_threshold)
        return {
            "status": "CONTRAST_FORKED",
            **result,
            "hint": "Never force convergence. Fork ScenarioSet A/B/C. Test independently.",
        }

    return {"status": "ERROR", "reason": f"Unknown mode: {mode}"}
