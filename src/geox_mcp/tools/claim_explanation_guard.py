"""
claim_explanation_guard — explanatory-class gate for the GEOX claim lifecycle
=============================================================================

GEOX already tracks three things about a claim:

  * ``claim_type``       — the geological category (horizon, fault, trap, ...)
  * ``truth_class``      — HOW the claim was obtained (FACT | INTERPRETATION | SPECULATION)
  * ``claim_state``      — WHERE the claim is in review (DRAFT → ... → SEALED)

None of them says WHAT KIND of explanation the claim is. That is the axis this
module adds, and it is the axis ``/root/AAA/lib/claim_kernel`` owns:

  ==== ===========================================================
  MEASURED   a quantity with a number and a source
  MECHANISM  a testable cause with a stated pathway
  PATTERN    a regularity that recurs across cases; cause contested
  NARRATIVE  no mechanism, no measure, not falsifiable
  UNCLASSIFIED  undeclared — fails closed
  ==== ===========================================================

Only ``MEASURED``, ``MECHANISM`` and ``PATTERN`` are action-eligible.

THE ONE RULE
------------
A NARRATIVE claim may be true, valuable and worth reading and still carry zero
explanatory power. It may be PUBLISHED; it may never be the SOLE JUSTIFICATION
for a mutation. In the GEOX lifecycle that means:

  * transition → ``APPROVED_INTERPRETATION`` : blocked unless action-eligible
  * transition → ``SEALED``                  : blocked unless action-eligible
  * ``NARRATIVE``                            : stays held, contract recommends REJECTED
  * ``UNCLASSIFIED``                         : fails closed, stays held

Contract: ``contracts/claim_state_machine.yaml`` → ``explanation_axis``
          ``contracts/schemas/claim_card.json`` → ``explanation_class``
Kernel:   ``claim_kernel/v1`` (``action_eligible``)

FAIL-CLOSED
-----------
If ``claim_kernel`` cannot be imported, ``evaluate_explanation_gate`` returns
``allowed=False`` with error code ``HOLD_EXPLANATION_KERNEL_UNAVAILABLE``. An
unverifiable gate is a closed gate; it is never silently skipped.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

# ═══════════════════════════════════════════════════════════════════════════════
# claim_kernel binding — resolver, not a hard dependency
# ═══════════════════════════════════════════════════════════════════════════════

_CLAIM_KERNEL_LIB = "/root/AAA/lib"

_KERNEL: Any = None
_KERNEL_ERROR: str = ""
_KERNEL_RESOLVED = False


def _load_kernel() -> Any:
    """Import claim_kernel, adding /root/AAA/lib to sys.path if needed.

    Returns the module, or None. Never raises — an absent kernel is reported
    as a closed gate, not as an exception on the claim path.
    """
    global _KERNEL, _KERNEL_ERROR, _KERNEL_RESOLVED
    if _KERNEL_RESOLVED:
        return _KERNEL
    _KERNEL_RESOLVED = True
    try:
        import claim_kernel as _k  # type: ignore[import-not-found]
    except Exception:
        try:
            if _CLAIM_KERNEL_LIB not in sys.path:
                sys.path.insert(0, _CLAIM_KERNEL_LIB)
            import claim_kernel as _k  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - environment dependent
            _KERNEL_ERROR = f"claim_kernel unavailable: {type(exc).__name__}: {exc}"
            _KERNEL = None
            return None
    _KERNEL = _k
    _KERNEL_ERROR = ""
    return _KERNEL


def kernel_available() -> bool:
    """True when claim_kernel resolves right now (not merely named)."""
    return _load_kernel() is not None


def kernel_error() -> str:
    """Why the kernel did not resolve. Empty string when it did."""
    _load_kernel()
    return _KERNEL_ERROR


# ── Canonical class vocabulary ────────────────────────────────────────────────
# Literals are the fallback so this module never depends on the kernel to be
# importable; when the kernel IS present, parity is verified below and by test.
MEASURED = "MEASURED"
MECHANISM = "MECHANISM"
PATTERN = "PATTERN"
NARRATIVE = "NARRATIVE"
UNCLASSIFIED = "UNCLASSIFIED"

DEFAULT_EXPLANATION_CLASS = UNCLASSIFIED
EXPLANATION_CLASSES: tuple[str, ...] = (MEASURED, MECHANISM, PATTERN, NARRATIVE, UNCLASSIFIED)
ACTION_ELIGIBLE_EXPLANATION_CLASSES: tuple[str, ...] = (MEASURED, MECHANISM, PATTERN)

CLAIM_KERNEL_SCHEMA = "claim_kernel/v1"


def _kernel_vocabulary() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(CLAIM_CLASSES, ACTION_ELIGIBLE_CLASSES) from the kernel when present."""
    k = _load_kernel()
    if k is None:
        return EXPLANATION_CLASSES, ACTION_ELIGIBLE_EXPLANATION_CLASSES
    classes = tuple(getattr(k, "CLAIM_CLASSES", EXPLANATION_CLASSES))
    eligible = tuple(getattr(k, "ACTION_ELIGIBLE_CLASSES", ACTION_ELIGIBLE_EXPLANATION_CLASSES))
    return classes, eligible


def vocabulary_matches_kernel() -> bool:
    """Local fallback vocabulary must equal the kernel's. False if kernel absent."""
    k = _load_kernel()
    if k is None:
        return False
    classes, eligible = _kernel_vocabulary()
    return classes == EXPLANATION_CLASSES and tuple(sorted(eligible)) == tuple(
        sorted(ACTION_ELIGIBLE_EXPLANATION_CLASSES)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Guarded transitions — the two states that turn a claim into a justification
# ═══════════════════════════════════════════════════════════════════════════════

GUARDED_TARGET_STATES: tuple[str, ...] = ("APPROVED_INTERPRETATION", "SEALED")

ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE = "HOLD_EXPLANATION_NOT_ACTION_ELIGIBLE"
ERROR_EXPLANATION_KERNEL_UNAVAILABLE = "HOLD_EXPLANATION_KERNEL_UNAVAILABLE"

# Contract-conformant fallback for a class that can never justify a mutation.
# claim_state_machine.yaml : transitions[from: ANY, to: REJECTED]
NARRATIVE_FALLBACK_STATE = "REJECTED"
UNCLASSIFIED_FALLBACK_ACTION = (
    "Declare explanation_class as MEASURED, MECHANISM or PATTERN on the claim "
    "(geox_claim_create → explanation_class=...), then retry the transition."
)


# ═══════════════════════════════════════════════════════════════════════════════
# Normalisation — additive, tolerant of every pre-existing record
# ═══════════════════════════════════════════════════════════════════════════════


def normalize_explanation_class(value: Any) -> str:
    """Coerce anything into a declared class.

    ``None``, ``""``, an unknown token or a malformed record all resolve to
    UNCLASSIFIED — which fails closed. Unknown values are never promoted into
    an action-eligible class by accident.
    """
    if value is None:
        return UNCLASSIFIED
    token = str(getattr(value, "value", value)).strip().upper()
    if not token or token not in EXPLANATION_CLASSES:
        return UNCLASSIFIED
    return token


def explanation_class_of(claim: Any) -> str:
    """Read ``explanation_class`` off a claim payload / envelope / dict.

    Pre-existing claim records have no such key: they read as UNCLASSIFIED and
    therefore cannot justify a new mutation. No record is rewritten.
    """
    if claim is None:
        return UNCLASSIFIED
    if isinstance(claim, Mapping):
        raw = claim.get("explanation_class")
    else:
        raw = getattr(claim, "explanation_class", None)
    return normalize_explanation_class(raw)


def is_action_eligible_class(explanation_class: str) -> bool:
    """Local, kernel-independent check of the declared class."""
    return normalize_explanation_class(explanation_class) in ACTION_ELIGIBLE_EXPLANATION_CLASSES


# ═══════════════════════════════════════════════════════════════════════════════
# The gate
# ═══════════════════════════════════════════════════════════════════════════════


def evaluate_explanation_gate(
    claim_text: str = "",
    declared_class: str = UNCLASSIFIED,
    *,
    require_kernel: bool = True,
) -> dict[str, Any]:
    """May this claim (as classified) justify a mutation?

    Returns a stable dict::

        {
          "allowed": bool,                # True only for action-eligible classes
          "explanation_class": str,       # the normalised declared class
          "action_eligible": bool,
          "reasons": [str],
          "error_code": str | None,       # set whenever allowed is False
          "recommended_next_state": str | None,
          "required_action": str,
          "kernel": {"available": bool, "schema": str | None, "error": str},
          "schema": "claim_kernel/v1",
        }

    Fail-closed: an undeclared class, a NARRATIVE class, a disagreement between
    the declared class and the text, or an unresolvable kernel all return
    ``allowed=False``.
    """
    declared = normalize_explanation_class(declared_class)
    kernel = _load_kernel()

    if kernel is None and require_kernel:
        return {
            "allowed": False,
            "explanation_class": declared,
            "action_eligible": False,
            "reasons": [_KERNEL_ERROR or "claim_kernel unavailable"],
            "error_code": ERROR_EXPLANATION_KERNEL_UNAVAILABLE,
            "recommended_next_state": None,
            "required_action": (
                f"Resolve the claim_kernel package (expected at {_CLAIM_KERNEL_LIB}) "
                "before any claim may enter APPROVED_INTERPRETATION or SEALED."
            ),
            "kernel": {"available": False, "schema": None, "error": _KERNEL_ERROR},
            "schema": CLAIM_KERNEL_SCHEMA,
        }

    if kernel is not None:
        verdict = kernel.action_eligible(claim_text or "", declared)
        eligible = bool(verdict.get("eligible"))
        reasons = list(verdict.get("reasons") or [])
        class_verdict = verdict.get("class_verdict") or {}
        baseline_verdict = verdict.get("baseline_verdict") or {}
        schema = verdict.get("schema", CLAIM_KERNEL_SCHEMA)
    else:  # pragma: no cover - require_kernel=False path
        eligible = is_action_eligible_class(declared)
        reasons = [] if eligible else [f"class={declared} is not action-eligible"]
        class_verdict = {"declared": declared, "inferred": None}
        baseline_verdict = {}
        schema = CLAIM_KERNEL_SCHEMA

    if eligible:
        return {
            "allowed": True,
            "explanation_class": declared,
            "action_eligible": True,
            "reasons": [],
            "error_code": None,
            "recommended_next_state": None,
            "required_action": "",
            "kernel": {"available": True, "schema": schema, "error": ""},
            "class_verdict": class_verdict,
            "baseline_verdict": baseline_verdict,
            "schema": schema,
        }

    if declared == NARRATIVE or str(class_verdict.get("declared", declared)) == NARRATIVE:
        recommendation = NARRATIVE_FALLBACK_STATE
        required = (
            "A NARRATIVE claim carries no mechanism, no measure and no falsifier. "
            "It may be published but it may not justify this transition. Either supply "
            "a MECHANISM (stated pathway + test), a MEASURED value (number + source), or "
            "a PATTERN (recurrence across named cases) — or transition the claim to "
            f"{NARRATIVE_FALLBACK_STATE}."
        )
    else:
        recommendation = None
        required = UNCLASSIFIED_FALLBACK_ACTION

    return {
        "allowed": False,
        "explanation_class": declared,
        "action_eligible": False,
        "reasons": reasons or [f"class={declared} is not action-eligible"],
        "error_code": ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE,
        "recommended_next_state": recommendation,
        "required_action": required,
        "kernel": {"available": True, "schema": schema, "error": ""},
        "class_verdict": class_verdict,
        "baseline_verdict": baseline_verdict,
        "schema": schema,
    }


def guard_transition(
    current_state: str,
    target_state: str,
    explanation_class: Any = UNCLASSIFIED,
    claim_text: str = "",
) -> dict[str, Any]:
    """The transition guard: may ``state → target_state`` be taken?

    Guarded targets are ``APPROVED_INTERPRETATION`` and ``SEALED`` (declared in
    ``claim_state_machine.yaml`` → ``explanation_axis.guarded_transitions``).
    Every other transition in the 9-state machine is untouched by this module.

    Returns::

        {"allowed": bool, "from": str, "to": str, "guarded": bool,
         "error_code": str | None, "recommended_next_state": str | None, ...}
    """
    target = str(target_state or "").strip().upper()
    guarded = target in GUARDED_TARGET_STATES
    if not guarded:
        return {
            "allowed": True,
            "from": current_state,
            "to": target_state,
            "guarded": False,
            "explanation_class": normalize_explanation_class(explanation_class),
            "error_code": None,
            "recommended_next_state": None,
            "required_action": "",
            "guard": "explanation_class",
            "schema": CLAIM_KERNEL_SCHEMA,
        }

    verdict = evaluate_explanation_gate(claim_text, explanation_class)
    return {
        "allowed": verdict["allowed"],
        "from": current_state,
        "to": target_state,
        "guarded": True,
        "explanation_class": verdict["explanation_class"],
        "action_eligible": verdict["action_eligible"],
        "reasons": verdict["reasons"],
        "error_code": verdict["error_code"],
        "recommended_next_state": verdict["recommended_next_state"],
        "required_action": verdict["required_action"],
        "kernel": verdict["kernel"],
        "class_verdict": verdict.get("class_verdict"),
        "baseline_verdict": verdict.get("baseline_verdict"),
        "guard": "explanation_class",
        "schema": verdict.get("schema", CLAIM_KERNEL_SCHEMA),
    }


def guarded_transition_states() -> tuple[str, ...]:
    """The target states this guard protects. Read by tests and by the contract."""
    return GUARDED_TARGET_STATES


__all__ = [
    "ACTION_ELIGIBLE_EXPLANATION_CLASSES",
    "CLAIM_KERNEL_SCHEMA",
    "DEFAULT_EXPLANATION_CLASS",
    "ERROR_EXPLANATION_KERNEL_UNAVAILABLE",
    "ERROR_EXPLANATION_NOT_ACTION_ELIGIBLE",
    "EXPLANATION_CLASSES",
    "GUARDED_TARGET_STATES",
    "MEASURED",
    "MECHANISM",
    "NARRATIVE",
    "NARRATIVE_FALLBACK_STATE",
    "PATTERN",
    "UNCLASSIFIED",
    "evaluate_explanation_gate",
    "explanation_class_of",
    "guard_transition",
    "guarded_transition_states",
    "is_action_eligible_class",
    "kernel_available",
    "kernel_error",
    "normalize_explanation_class",
    "vocabulary_matches_kernel",
]
