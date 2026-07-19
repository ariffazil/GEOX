"""
assumption_lineage.py — Gap X (WAJIB)
The DNA layer of GEOX reasoning.

Every assumption that touches an output must carry a lineage record:
where it came from, which tool introduced it, what rung it sits at,
and whether it has been falsified.

Without this layer we cannot:
- Track where errors originate.
- See which assumption corrupts multiple downstream outputs.
- Audit how interpretation chains propagate.

Per GENESIS 003 + GEOX_FOUNDATIONAL_GAPS_AND_GODEL_LOCK.md Part IV Gap X.

DITEMPA BUKAN DIBERI — Lineage is forged, not given.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

# ───────────────────────────── EPISTEMIC RUNG (canonical, mirrors geox_core/enums) ──
# Mirrors the Rung 1-7 ladder from GEOX_FOUNDATIONAL_GAPS. Kept local so this
# module remains importable without the full geox_core package (e.g. from tests).
RUNG_SIGNAL = 1
RUNG_MEASUREMENT = 2
RUNG_DERIVATION = 3
RUNG_INTERPRETATION = 4
RUNG_MODEL = 5
RUNG_JUDGMENT = 6
RUNG_NARRATIVE = 7

RUNG_NAMES = {
    1: "SIGNAL",
    2: "MEASUREMENT",
    3: "DERIVATION",
    4: "INTERPRETATION",
    5: "MODEL",
    6: "JUDGMENT",
    7: "NARRATIVE",
}


# ───────────────────────────── MODELS ──────────────────────────────────────────────
class Assumption(BaseModel):
    """One assumption in a reasoning chain.

    The minimum identity a reasoning-step assumption must carry.
    """

    assumption_id: str = Field(default_factory=lambda: f"ASM-{uuid.uuid4().hex[:12]}")
    parent_assumption_id: str | None = None
    introduced_by: str = Field(..., description="Tool name that introduced this assumption")
    rung_origin: int = Field(..., ge=1, le=7, description="Epistemic rung where this assumption was born")
    description: str = Field(..., min_length=1)
    current_status: Literal["active", "falsified", "inherited"] = "active"
    falsified_at: datetime | None = None
    falsified_by: str | None = Field(default=None, description="Evidence ID that falsified this assumption")
    inherited_from: str | None = Field(default=None, description="Assumption ID this was inherited from")
    introduced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Provenance tag — required by F2 TRUTH.
    epistemic_label: Literal["OBS", "DER", "INT", "SPEC"] = "DER"

    def is_active(self) -> bool:
        return self.current_status == "active"

    def rung_name(self) -> str:
        return RUNG_NAMES[self.rung_origin]


class LineageNode(BaseModel):
    """A node in the lineage graph — the assumption + its descendants summary."""

    assumption: Assumption
    children_ids: list[str] = Field(default_factory=list)
    depth: int = 0


class LineageGraph(BaseModel):
    """The full lineage graph (subgraph reachable from a root assumption)."""

    root_id: str
    nodes: dict[str, LineageNode] = Field(default_factory=dict)
    edges: list[tuple[str, str]] = Field(default_factory=list)


# ───────────────────────────── REGISTRY (thread-safe) ────────────────────────────
class AssumptionRegistry:
    """Thread-safe registry of assumptions.

    The DNA layer. Every tool that introduces an assumption must call
    `register(...)`. Every falsification must call `falsify(...)`.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._assumptions: dict[str, Assumption] = {}

    # ── write ────────────────────────────────────────────────────────────────
    def register(
        self,
        introduced_by: str,
        rung_origin: int,
        description: str,
        *,
        parent_assumption_id: str | None = None,
        inherited_from: str | None = None,
        epistemic_label: Literal["OBS", "DER", "INT", "SPEC"] = "DER",
        assumption_id: str | None = None,
    ) -> Assumption:
        """Add a new assumption to the lineage. Returns the persisted model."""
        if not (1 <= rung_origin <= 7):
            raise ValueError(f"rung_origin must be 1..7, got {rung_origin}")
        if not description.strip():
            raise ValueError("description cannot be empty")

        asm = Assumption(
            assumption_id=assumption_id or f"ASM-{uuid.uuid4().hex[:12]}",
            parent_assumption_id=parent_assumption_id,
            introduced_by=introduced_by,
            rung_origin=rung_origin,
            description=description,
            inherited_from=inherited_from,
            epistemic_label=epistemic_label,
        )
        with self._lock:
            if asm.assumption_id in self._assumptions:
                raise ValueError(f"duplicate assumption_id: {asm.assumption_id}")
            # Validate parent exists if claimed.
            if asm.parent_assumption_id and asm.parent_assumption_id not in self._assumptions:
                raise ValueError(
                    f"parent_assumption_id {asm.parent_assumption_id!r} not in registry"
                )
            self._assumptions[asm.assumption_id] = asm
        return asm

    def falsify(
        self,
        assumption_id: str,
        evidence_id: str,
        *,
        reason: str | None = None,
    ) -> Assumption:
        """Mark an assumption as falsified. Cascades status to descendants."""
        with self._lock:
            asm = self._assumptions.get(assumption_id)
            if asm is None:
                raise KeyError(f"unknown assumption_id: {assumption_id}")
            if asm.current_status == "falsified":
                return asm  # idempotent

            updated = asm.model_copy(
                update={
                    "current_status": "falsified",
                    "falsified_at": datetime.now(UTC),
                    "falsified_by": evidence_id,
                    "description": (
                        asm.description + f" [FALSIFIED by {evidence_id}]"
                        if reason is None
                        else asm.description + f" [FALSIFIED by {evidence_id}: {reason}]"
                    ),
                }
            )
            self._assumptions[assumption_id] = updated

            # Cascade: mark all descendants as inherited-from-falsified
            descendants = self.descendants(assumption_id)
            for child in descendants:
                self._assumptions[child.assumption_id] = child.model_copy(
                    update={"current_status": "inherited"}
                )
            return updated

    # ── read ─────────────────────────────────────────────────────────────────
    def get(self, assumption_id: str) -> Assumption | None:
        with self._lock:
            return self._assumptions.get(assumption_id)

    def all(self) -> list[Assumption]:
        with self._lock:
            return list(self._assumptions.values())

    def active(self) -> list[Assumption]:
        with self._lock:
            return [a for a in self._assumptions.values() if a.current_status == "active"]

    def active_for_tool(self, tool_name: str) -> list[Assumption]:
        with self._lock:
            return [
                a
                for a in self._assumptions.values()
                if a.introduced_by == tool_name and a.current_status == "active"
            ]

    def falsified(self) -> list[Assumption]:
        with self._lock:
            return [a for a in self._assumptions.values() if a.current_status == "falsified"]

    def descendants(self, assumption_id: str) -> list[Assumption]:
        """All assumptions that descend from assumption_id via parent_assumption_id."""
        with self._lock:
            children_idx: dict[str, list[str]] = {}
            for a in self._assumptions.values():
                if a.parent_assumption_id:
                    children_idx.setdefault(a.parent_assumption_id, []).append(a.assumption_id)

            out: list[Assumption] = []
            stack = list(children_idx.get(assumption_id, []))
            seen: set[str] = set()
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                a = self._assumptions.get(cur)
                if a is not None:
                    out.append(a)
                stack.extend(children_idx.get(cur, []))
            return out

    def lineage(self, assumption_id: str) -> LineageGraph:
        """Build a LineageGraph rooted at assumption_id."""
        with self._lock:
            root = self._assumptions.get(assumption_id)
            if root is None:
                raise KeyError(f"unknown assumption_id: {assumption_id}")

            children_idx: dict[str, list[str]] = {}
            for a in self._assumptions.values():
                if a.parent_assumption_id:
                    children_idx.setdefault(a.parent_assumption_id, []).append(a.assumption_id)

            nodes: dict[str, LineageNode] = {}
            edges: list[tuple[str, str]] = []
            stack: list[tuple[str, int]] = [(assumption_id, 0)]
            while stack:
                cur_id, depth = stack.pop()
                cur = self._assumptions.get(cur_id)
                if cur is None or cur_id in nodes:
                    continue
                nodes[cur_id] = LineageNode(assumption=cur, depth=depth)
                if cur.parent_assumption_id and cur.parent_assumption_id in self._assumptions:
                    edges.append((cur.parent_assumption_id, cur_id))
                for child_id in children_idx.get(cur_id, []):
                    stack.append((child_id, depth + 1))

            return LineageGraph(root_id=assumption_id, nodes=nodes, edges=edges)

    # ── diagnostics ──────────────────────────────────────────────────────────
    def stats(self) -> dict:
        with self._lock:
            return {
                "total": len(self._assumptions),
                "active": sum(1 for a in self._assumptions.values() if a.current_status == "active"),
                "falsified": sum(1 for a in self._assumptions.values() if a.current_status == "falsified"),
                "inherited": sum(1 for a in self._assumptions.values() if a.current_status == "inherited"),
                "tools_touched": sorted({a.introduced_by for a in self._assumptions.values()}),
            }

    def clear(self) -> None:
        """Test-only. Production code must never call this."""
        with self._lock:
            self._assumptions.clear()


# ───────────────────────────── PROCESS-LOCAL SINGLETON ────────────────────────────
_default_registry: AssumptionRegistry | None = None
_default_lock = threading.Lock()


def get_default_registry() -> AssumptionRegistry:
    """Return the process-local AssumptionRegistry (lazy init)."""
    global _default_registry
    if _default_registry is None:
        with _default_lock:
            if _default_registry is None:
                _default_registry = AssumptionRegistry()
    return _default_registry


def reset_default_registry() -> None:
    """Test-only. Production code must never call this."""
    global _default_registry
    with _default_lock:
        _default_registry = None


__all__ = [
    "Assumption",
    "LineageNode",
    "LineageGraph",
    "AssumptionRegistry",
    "get_default_registry",
    "reset_default_registry",
    "RUNG_SIGNAL",
    "RUNG_MEASUREMENT",
    "RUNG_DERIVATION",
    "RUNG_INTERPRETATION",
    "RUNG_MODEL",
    "RUNG_JUDGMENT",
    "RUNG_NARRATIVE",
    "RUNG_NAMES",
]
