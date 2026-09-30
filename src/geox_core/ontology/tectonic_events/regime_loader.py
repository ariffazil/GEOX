"""Read-only loader + validator for ``regime_invariants.yaml``.

The registry this module loads answers a different question from its sibling
``tectonic_invariants.yaml`` (TECT-001..012):

    TECT-*  — may GEOX present this as an explanation?          (doctrine)
    REG-*   — how far up the epistemic ladder may a claim travel, and
              which tests may REJECT vs which may only return UNMEASURED.

Two load-bearing properties of this module:

1. **Everything carries provenance.**  Nothing is returned from the YAML
   without an attached :class:`Provenance` (artifact id/version, source file,
   source SHA-256, exact ``yaml_path``).  A threshold without provenance is
   how a rule of thumb silently becomes a hard invariant.

2. **Validation never raises on data.**  ``validate_registry`` asserts the
   registry's *own* internal laws and returns a structured report
   (``passed`` + violation list).  It raises only for file-not-found or
   unparseable YAML.  A validator that dies on malformed data cannot report
   that the data is malformed.

The load-bearing law is Law B (the FALSIFIER DIRECTION RULE): a ``DEFICIT_*``
test (an expected signature merely ABSENT) may only ever return ``UNMEASURED``.
An absence test fires on thin data exactly as readily as on a true negative, so
wiring deficits into a kill set makes the engine reject true hypotheses under
poor data — confident and wrong.  ``DEFICIT_*`` declaring ``KILL`` is a hard
validation failure.

Doctrine: DITEMPA BUKAN DIBERI.  Absence is not contradiction.
Read-only consumer: this module never writes to the ontology directory.

Usage::

    from geox_core.ontology.tectonic_events.regime_loader import (
        hard_invariants,
        threshold_source,
        validate_registry,
    )

    report = validate_registry()                     # verdict + violations
    prov = threshold_source("_COULOMB_TOLERANCE_DEG")  # provenance for a constant
    prov["threshold_status"]                          # -> "RULE_OF_THUMB"
    prov["validity_domain"]                           # -> declared domain
    prov["alternatives"]                              # -> why a deviation is not a regime change

Run as a script to validate the registry on disk::

    python -m geox_core.ontology.tectonic_events.regime_loader

Consumer wiring (gate ids and source constants keep no thresholds of their own) —
a gate that reads ``_COULOMB_TOLERANCE_DEG`` from
``geox_mcp.tools.structure_gates.tectonic_regime`` can stamp its receipt with the
registry's own statement about that number::

    prov = threshold_source("K-COMP-RAMPFLAT")   # aliases to REG-002
    prov["threshold_status"]        # "RULE_OF_THUMB" — NOT a hard invariant
    prov["validity_domain"]         # "New shear fracture in intact isotropic rock, ..."
    prov["alternatives"]            # why a deviation is not a regime change
    prov["provenance"]["source_sha256"]   # the exact registry revision cited
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

__all__ = [
    "REGISTRY_PATH",
    "F0_COMPANION_PATH",
    "CODE_ANCHOR_ALIASES",
    "RegimeRegistryError",
    "RegimeRegistryNotFoundError",
    "RegimeRegistryParseError",
    "Provenance",
    "RegistryMeta",
    "EpistemicTier",
    "ExtractionAxis",
    "HardInvariant",
    "SoftInvariant",
    "DecouplingMechanism",
    "FalsifierTest",
    "FalsifierRegime",
    "Correction",
    "RegimeRegistry",
    "load_registry",
    "get_registry",
    "clear_cache",
    "meta",
    "epistemic_tiers",
    "extraction_axes",
    "hard_invariants",
    "soft_invariants",
    "decoupling_mechanisms",
    "falsifier_registry",
    "falsifier_tests",
    "corrections_log",
    "hard_invariant",
    "soft_invariant",
    "decoupling_mechanism",
    "falsifier_test",
    "correction",
    "threshold_source",
    "threshold_status",
    "validate_registry",
    "f0_companion",
]

_HERE = Path(__file__).resolve().parent

#: The registry this module loads (F0 companion layer).
REGISTRY_PATH = _HERE / "regime_invariants.yaml"

#: The sibling F0 constitution (TECT-001..012) referenced by the registry meta.
F0_COMPANION_PATH = _HERE / "tectonic_invariants.yaml"

#: Verdict vocabulary as declared in the registry (never invented here).
VERDICT_KILL = "KILL"
VERDICT_UNMEASURED = "UNMEASURED"

_LAW_A = "law_a_contradiction_kill_requires_guard"
_LAW_B = "law_b_deficit_never_kills"
_LAW_C = "law_c_hard_invariant_guard_fields"
_LAW_D = "law_d_corrections_log_complete"

#: Accepted key names for a hard invariant's violation action.  ``on_violation``
#: is the regime-registry convention; ``violation_action`` is the sibling F0
#: convention (tectonic_invariants.yaml).  Both are real declared keys — this is
#: a spelling accommodation, not a default.
_ON_VIOLATION_KEYS = ("on_violation", "violation_action")

#: Keys that license a KILL by declaring the evidence / coverage precondition.
_GUARD_KEYS = ("requires", "coverage_requirement")

#: Key names that declare a threshold's epistemic status in the registry.
_THRESHOLD_STATUS_KEYS = ("threshold_source", "threshold_basis")

#: WIRING ONLY — pointers from source-code identifiers to registry anchors.
#:
#: Contains NO registry content: no thresholds, no text, no verdicts.  Each
#: value is an id that must exist in the YAML or resolution fails honestly.
#: Anchors below are the entries whose doctrine the identifier encodes:
#:
#:   Coulomb tolerance / K-COMP-RAMPFLAT -> REG-002 (threshold_source:
#:       RULE_OF_THUMB; the ±15° band is documented as false precision and
#:       recorded as defect CORR-05)
#:   Andersonian dip family / K-EXT-DIP -> REG-001
#:   tier ceiling (DYNAMIC requires slip inversion) -> E3_DYNAMIC
#:   K-REGIME-RESOLUTION -> REG-003 (tuning limit) · K-COMP-SHORTEN -> REG-004
#:   K-REGIME-DISPLAY -> REG-005 · K-REGIME-XCUT -> REG-006
#:   K-REGIME-DIFFERENTIAL -> REG-007 · K-NULL-DIP / K-GRAV-LINKAGE /
#:       K-INV-REVERSAL -> REG-008 · K-SALT-* -> M-SALT
CODE_ANCHOR_ALIASES: Mapping[str, str] = {
    # constants in geox_mcp.tools.structure_gates.tectonic_regime
    "_COULOMB_TOLERANCE_DEG": "REG-002",
    "COULOMB_TOLERANCE_DEG": "REG-002",
    "_ANDERSON": "REG-001",
    # MCP gate ids
    "K-EXT-DIP": "REG-001",
    "K-COMP-RAMPFLAT": "REG-002",
    "K-REGIME-CEILING": "E3_DYNAMIC",
    "K-REGIME-RESOLUTION": "REG-003",
    "K-COMP-SHORTEN": "REG-004",
    "K-REGIME-DISPLAY": "REG-005",
    "K-REGIME-XCUT": "REG-006",
    "K-REGIME-DIFFERENTIAL": "REG-007",
    "K-NULL-DIP": "REG-008",
    "K-GRAV-LINKAGE": "REG-008",
    "K-INV-REVERSAL": "REG-008",
    "K-SALT-BODY": "M-SALT",
    "K-SALT-DRIVER": "M-SALT",
}

#: Sections whose entries are keyed by id and may be resolved by keyword search.
_KEYWORD_SECTIONS = (
    "epistemic_tiers",
    "extraction_axes",
    "hard_invariants",
    "soft_invariants",
    "decoupling_mechanisms",
    "falsifier_registry",
)

#: Section preference when several registry entries claim the same gate id.
_SECTION_PREFERENCE = (
    "hard_invariants",
    "soft_invariants",
    "decoupling_mechanisms",
    "epistemic_tiers",
    "extraction_axes",
    "falsifier_registry",
    "corrections_log",
)

#: Numeric literal in registry text.  Excludes digits preceded by a word
#: character (σ1, F2, REG-002) or by a slash (λ/4, φ/2 are formula fractions,
#: not thresholds).
_LITERAL_RE = re.compile(r"(?<![\w/])(\d+(?:\.\d+)?)")
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]+")
_TOKEN_STOPWORDS = frozenset(
    {
        "TOLERANCE",
        "THRESHOLD",
        "CONSTANT",
        "DEG",
        "DEGREES",
        "DEGREE",
        "BAND",
        "VALUE",
        "REQUIRES",
        "REQUIRED",
    }
)
#: A capitalised word or an opening parenthesis within this window before a
#: numeric literal marks it as a literature citation year (Byerlee (1978),
#: Steno (1669)) rather than a threshold.
_CITATION_WINDOW = 12
_CITATION_CONTEXT_RE = re.compile(r"(?:[A-Z][a-z]{2,}|[\w.]\s*\()\s*$")
_CITATION_YEAR_RANGE = (1500.0, 2100.0)


# ═══════════════════════════════════════════════════════════════════════════
# Errors — raised ONLY for file-not-found / unparseable / unsupported input
# ═══════════════════════════════════════════════════════════════════════════


class RegimeRegistryError(RuntimeError):
    """Base class for regime registry loader failures."""


class RegimeRegistryNotFoundError(RegimeRegistryError, FileNotFoundError):
    """The registry file does not exist."""


class RegimeRegistryParseError(RegimeRegistryError, ValueError):
    """The registry file exists but is not parseable YAML mapping."""


# ═══════════════════════════════════════════════════════════════════════════
# Coercion helpers — tolerant of data, never silently inventive
# ═══════════════════════════════════════════════════════════════════════════


def _text(value: Any) -> str | None:
    """Coerce a YAML scalar to text; containers become ``None`` (not a string).

    Scalars are stringified losslessly enough for provenance quoting.  A
    container where a scalar was expected yields ``None`` — the loader says
    nothing rather than inventing a rendering.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if hasattr(value, "isoformat"):  # datetime / date / time
        try:
            return str(value.isoformat())
        except Exception:  # pragma: no cover - defensive
            return None
    return None


def _text_list(value: Any) -> list[str]:
    """Coerce a scalar-or-sequence YAML value into a list of text."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        return []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            text = _text(item)
            if text is not None and text.strip():
                out.append(text)
        return out
    text = _text(value)
    return [text] if text and text.strip() else []


def _text_map(value: Any) -> dict[str, str]:
    """Coerce a mapping of scalars into ``dict[str, str]``."""
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, str] = {}
    for key, item in value.items():
        text = _text(item)
        if text is not None:
            out[str(key)] = text
    return out


def _jsonable(value: Any) -> Any:
    """Best-effort JSON-safe projection, used for the CLI and for reporting."""
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return _text(value)


def _blank(value: Any) -> bool:
    """True when a field is absent, empty, whitespace, or an empty container."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    return False


def _verdict(value: Any) -> str | None:
    text = _text(value)
    return text.strip().upper() if text else None


def _norm(identifier: Any) -> str:
    """Normalise an identifier for lookup: case, separators and spacing gone."""
    text = _text(identifier) or ""
    return re.sub(r"[\s_\-]+", "", text).upper()


def _declared(owner: Mapping[str, Any], keys: Iterable[str]) -> tuple[str | None, str | None]:
    """Return (value, key) for the first non-blank declared key."""
    for key in keys:
        if not _blank(owner.get(key)):
            return _text(owner.get(key)), key
    return None, None


def _deep_values(value: Any) -> Iterable[tuple[str, Any]]:
    """Yield ``(relative_path, leaf)`` for every leaf under a YAML node."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            for sub_path, leaf in _deep_values(item):
                yield f"{key}.{sub_path}" if sub_path else str(key), leaf
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            for sub_path, leaf in _deep_values(item):
                yield f"[{index}].{sub_path}" if sub_path else f"[{index}]", leaf
    else:
        yield "", value


def _iter_strings(entry: Any) -> Iterable[tuple[str, str]]:
    """Yield ``(relative_path, text)`` for every non-empty string leaf."""
    for rel_path, leaf in _deep_values(entry):
        text = _text(leaf)
        if text is not None and text.strip():
            yield rel_path, text


# ═══════════════════════════════════════════════════════════════════════════
# Models — every entry carries its provenance
# ═══════════════════════════════════════════════════════════════════════════

TextField = Annotated[str | None, BeforeValidator(_text)]
TextListField = Annotated[list[str], BeforeValidator(_text_list)]
TextMapField = Annotated[dict[str, str], BeforeValidator(_text_map)]


class Provenance(BaseModel):
    """Where a loaded value came from.  Attached to every returned object."""

    model_config = ConfigDict(frozen=True, extra="allow")

    artifact_id: str
    artifact_version: str | None = None
    source_file: str
    source_sha256: str | None = None
    yaml_path: str

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class RegistryEntry(BaseModel):
    """Base for every entry: provenance is mandatory, unknown keys are kept.

    ``extra="allow"`` is deliberate — the YAML is owned by a separate layer and
    may gain keys.  A loader that drops or rejects unknown keys would either
    lose data or break on a concurrent edit.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    provenance: Provenance

    def extra_fields(self) -> Mapping[str, Any]:
        return self.model_extra or {}

    def registry_entry(self) -> dict[str, Any]:
        """The full raw entry body, exactly as declared in the YAML."""
        body: dict[str, Any] = {k: v for k, v in self.extra_fields().items()}
        for key, value in self.model_dump(exclude={"provenance"}).items():
            body.setdefault(key, value)
        return _jsonable(body)


class RegistryMeta(RegistryEntry):
    artifact_id: TextField = None
    version: TextField = None
    forged_at: TextField = None
    author: TextField = None
    space: TextField = None
    layer: TextField = None
    paradigm_counterpart: TextField = None
    doctrine: TextField = None
    seal: TextField = None


class EpistemicTier(RegistryEntry):
    id: str
    name: TextField = None
    epistemic_tag: TextField = None
    strength: TextField = None
    what_it_is: TextField = None
    entry_gate: TextField = None
    entry_condition: TextField = None
    cannot_do: TextField = None
    known_blindspots: TextListField = Field(default_factory=list)
    required_declaration: TextListField = Field(default_factory=list)
    degrees_of_freedom: TextField = None
    caveat: TextField = None


class ExtractionAxis(RegistryEntry):
    id: str
    name: TextField = None
    measures: TextListField = Field(default_factory=list)
    source_fields: TextListField = Field(default_factory=list)
    domain_guard: TextField = None
    note: TextField = None
    pitfall: TextField = None
    #: YAML key ``yield`` is a Python keyword — accepted here as ``yield_``.
    yield_note: TextField = Field(default=None, validation_alias="yield", serialization_alias="yield")


class HardInvariant(RegistryEntry):
    id: str
    name: TextField = None
    statement: TextField = None
    on_violation: TextField = None
    epistemic_tag: TextField = None
    gate: TextField = None
    validity_domain: TextField = None
    derivation: TextField = None
    consequence: TextField = None
    attribution: TextField = None
    dimension_note: TextField = None
    involution: TextField = None
    corrected_claim: TextField = None
    warning: TextField = None
    threshold_source: TextField = None
    alternatives_for_deviation: TextListField = Field(default_factory=list)
    invalidated_by: TextListField = Field(default_factory=list)
    floor_ref: TextListField = Field(default_factory=list)
    two_distinct_null_points: TextMapField = Field(default_factory=dict)
    yield_note: TextField = Field(default=None, validation_alias="yield", serialization_alias="yield")


class SoftInvariant(RegistryEntry):
    id: str
    name: TextField = None
    statement: TextField = None
    on_violation: TextField = None
    consequence: TextField = None
    open_tension: TextField = None
    envelope: TextField = None
    corrected_claim: TextField = None
    gate: TextField = None


class DecouplingMechanism(RegistryEntry):
    id: str
    name: TextField = None
    driver: TextField = None
    consequence: TextField = None
    invariant_effect: TextField = None
    verdict_when_active: TextField = None
    warning: TextField = None
    signatures: TextListField = Field(default_factory=list)


class FalsifierTest(RegistryEntry):
    """One falsifier.  ``direction`` is derived from the key prefix in the YAML."""

    id: str
    regime_id: str
    direction: str  # "contradiction" | "deficit" | "undeclared"
    returns: TextField = None
    test: TextField = None
    requires: TextField = None
    coverage_requirement: TextField = None
    why_not_kill: TextField = None
    why_this_kills: TextField = None
    scope: TextField = None
    correction: TextField = None

    def guard(self) -> str | None:
        """The declared licence for a KILL, or ``None`` if none is declared."""
        if not _blank(self.requires):
            return self.requires
        if not _blank(self.coverage_requirement):
            return self.coverage_requirement
        return None

    def guard_field(self) -> str | None:
        _, key = _declared(
            {"requires": self.requires, "coverage_requirement": self.coverage_requirement},
            _GUARD_KEYS,
        )
        return key


class FalsifierRegime(RegistryEntry):
    id: str
    regime: TextField = None
    stress_axis_vertical: TextField = None
    required_positive_evidence: TextListField = Field(default_factory=list)
    critical_correction: TextField = None
    structural_note: TextField = None
    notation_correction: TextField = None
    contradiction_tests: dict[str, FalsifierTest] = Field(default_factory=dict)
    deficit_tests: dict[str, FalsifierTest] = Field(default_factory=dict)


class Correction(RegistryEntry):
    id: str
    defect: TextField = None
    verdict: TextField = None
    reason: TextField = None
    fix: TextField = None


class RegimeRegistry(BaseModel):
    """The whole registry, with provenance on the document and on every entry."""

    model_config = ConfigDict(extra="allow")

    meta: RegistryMeta
    epistemic_tiers: dict[str, EpistemicTier] = Field(default_factory=dict)
    extraction_axes: dict[str, ExtractionAxis] = Field(default_factory=dict)
    hard_invariants: dict[str, HardInvariant] = Field(default_factory=dict)
    soft_invariants: dict[str, SoftInvariant] = Field(default_factory=dict)
    decoupling_mechanisms: dict[str, DecouplingMechanism] = Field(default_factory=dict)
    falsifier_registry: dict[str, FalsifierRegime] = Field(default_factory=dict)
    corrections_log: list[Correction] = Field(default_factory=list)
    provenance: Provenance
    source_file: str
    source_sha256: str | None = None
    #: Raw document exactly as parsed — used by ``validate_registry``.
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)

    # ── typed lookups ──────────────────────────────────────────────────────

    def invariant(self, invariant_id: str) -> HardInvariant | SoftInvariant | None:
        key = _norm(invariant_id)
        for collection in (self.hard_invariants, self.soft_invariants):
            for entry_id, entry in collection.items():
                if _norm(entry_id) == key:
                    return entry
        return None

    def any_entry(self, entry_id: str) -> RegistryEntry | None:
        """Look up any entry by id across every section (None if absent)."""
        key = _norm(entry_id)
        for collection in (
            self.hard_invariants,
            self.soft_invariants,
            self.decoupling_mechanisms,
            self.epistemic_tiers,
            self.extraction_axes,
            self.falsifier_registry,
        ):
            for collection_id, entry in collection.items():
                if _norm(collection_id) == key:
                    return entry
        for correction in self.corrections_log:
            if _norm(correction.id) == key:
                return correction
        for regime in self.falsifier_registry.values():
            for tests in (regime.contradiction_tests, regime.deficit_tests):
                for test_id, test in tests.items():
                    if _norm(test_id) == key:
                        return test
        return None

    def tests(self) -> list[FalsifierTest]:
        out: list[FalsifierTest] = []
        for regime in self.falsifier_registry.values():
            out.extend(regime.contradiction_tests.values())
            out.extend(regime.deficit_tests.values())
        return out


# ═══════════════════════════════════════════════════════════════════════════
# Loading
# ═══════════════════════════════════════════════════════════════════════════


def _read_yaml(path: Path) -> tuple[dict[str, Any], str]:
    """Read + parse a YAML mapping.  Raises only for not-found / unparseable."""
    path = Path(path)
    if not path.exists():
        raise RegimeRegistryNotFoundError(
            f"Regime invariant registry not found: {path}\n"
            "GEOX F0 companion layer requires regime_invariants.yaml; "
            "refusing to substitute an in-code default."
        )
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    try:
        document = yaml.safe_load(data)
    except yaml.YAMLError as exc:  # unparseable
        raise RegimeRegistryParseError(f"Unparseable YAML in {path}: {exc}") from exc
    if not isinstance(document, Mapping):
        raise RegimeRegistryParseError(
            f"Top-level YAML in {path} must be a mapping, got {type(document).__name__}"
        )
    return {str(k): v for k, v in document.items()}, digest


def _as_mapping(value: Any) -> dict[str, Any]:
    return {str(k): v for k, v in value.items()} if isinstance(value, Mapping) else {}


def _body_kwargs(body: Mapping[str, Any], *, explicit: Sequence[str] = ("id",)) -> dict[str, Any]:
    """Body keys minus fields passed explicitly (avoids duplicate-kwarg errors).

    Excluded keys are still preserved: they remain reachable through
    ``registry.raw`` and through the entry's provenance path.
    """
    return {str(key): value for key, value in body.items() if key not in explicit}


def _direction(test_id: str) -> str:
    upper = test_id.upper()
    if upper.startswith("CONTRADICTION"):
        return "contradiction"
    if upper.startswith("DEFICIT"):
        return "deficit"
    return "undeclared"


def _parse_falsifier_test(
    test_id: str, regime_id: str, body: Any, prov: Provenance
) -> FalsifierTest:
    body_map = _as_mapping(body)
    return FalsifierTest(
        id=str(test_id),
        regime_id=regime_id,
        direction=_direction(str(test_id)),
        provenance=prov,
        **_body_kwargs(body_map, explicit=("id", "regime_id", "direction")),
    )


def load_registry(path: str | Path | None = None) -> RegimeRegistry:
    """Load the regime invariant registry.

    Raises:
        RegimeRegistryNotFoundError: file does not exist.
        RegimeRegistryParseError: file exists but is not a parseable YAML mapping.
    """
    registry_path = Path(path) if path is not None else REGISTRY_PATH
    raw, digest = _read_yaml(registry_path)

    meta_raw = _as_mapping(raw.get("meta"))
    artifact_id = _text(meta_raw.get("artifact_id")) or "UNKNOWN_ARTIFACT_ID"
    version = _text(meta_raw.get("version"))
    source_file = str(registry_path)

    def prov(yaml_path: str) -> Provenance:
        return Provenance(
            artifact_id=artifact_id,
            artifact_version=version,
            source_file=source_file,
            source_sha256=digest,
            yaml_path=yaml_path,
        )

    registry = RegimeRegistry(
        meta=RegistryMeta(provenance=prov("meta"), **meta_raw),
        provenance=prov("$"),
        source_file=source_file,
        source_sha256=digest,
        raw=raw,
    )

    for section, model, target in (
        ("epistemic_tiers", EpistemicTier, registry.epistemic_tiers),
        ("extraction_axes", ExtractionAxis, registry.extraction_axes),
        ("hard_invariants", HardInvariant, registry.hard_invariants),
        ("soft_invariants", SoftInvariant, registry.soft_invariants),
        ("decoupling_mechanisms", DecouplingMechanism, registry.decoupling_mechanisms),
    ):
        for entry_id, body in _as_mapping(raw.get(section)).items():
            target[str(entry_id)] = model(  # type: ignore[index]
                id=str(entry_id),
                provenance=prov(f"{section}.{entry_id}"),
                **_body_kwargs(_as_mapping(body)),
            )

    for regime_id, body in _as_mapping(raw.get("falsifier_registry")).items():
        body_map = _as_mapping(body)
        regime_path = f"falsifier_registry.{regime_id}"
        contradiction_tests: dict[str, FalsifierTest] = {}
        deficit_tests: dict[str, FalsifierTest] = {}
        for field, bucket in (
            ("contradiction_tests", contradiction_tests),
            ("deficit_tests", deficit_tests),
        ):
            for test_id, test_body in _as_mapping(body_map.get(field)).items():
                bucket[str(test_id)] = _parse_falsifier_test(
                    str(test_id),
                    str(regime_id),
                    test_body,
                    prov(f"{regime_path}.{field}.{test_id}"),
                )
        registry.falsifier_registry[str(regime_id)] = FalsifierRegime(
            id=str(regime_id),
            provenance=prov(regime_path),
            contradiction_tests=contradiction_tests,
            deficit_tests=deficit_tests,
            **{
                k: v
                for k, v in body_map.items()
                if k not in ("contradiction_tests", "deficit_tests", "id")
            },
        )

    corrections = raw.get("corrections_log")
    if isinstance(corrections, Sequence) and not isinstance(corrections, (str, bytes)):
        for index, body in enumerate(corrections):
            body_map = _as_mapping(body)
            entry_id = _text(body_map.get("id")) or f"corrections_log[{index}]"
            registry.corrections_log.append(
                Correction(
                    id=entry_id,
                    provenance=prov(f"corrections_log[{index}]"),
                    **_body_kwargs(body_map),
                )
            )

    return registry


_DEFAULT_REGISTRY: RegimeRegistry | None = None


def clear_cache() -> None:
    """Drop the cached default registry (used by tests and long-running hosts)."""
    global _DEFAULT_REGISTRY
    _DEFAULT_REGISTRY = None


def get_registry() -> RegimeRegistry:
    """The cached default registry (loaded from :data:`REGISTRY_PATH`)."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = load_registry()
    return _DEFAULT_REGISTRY


# ═══════════════════════════════════════════════════════════════════════════
# Typed accessors — provenance is attached to everything returned
# ═══════════════════════════════════════════════════════════════════════════


def meta() -> RegistryMeta:
    return get_registry().meta


def epistemic_tiers() -> dict[str, EpistemicTier]:
    return get_registry().epistemic_tiers


def extraction_axes() -> dict[str, ExtractionAxis]:
    return get_registry().extraction_axes


def hard_invariants() -> dict[str, HardInvariant]:
    return get_registry().hard_invariants


def soft_invariants() -> dict[str, SoftInvariant]:
    return get_registry().soft_invariants


def decoupling_mechanisms() -> dict[str, DecouplingMechanism]:
    return get_registry().decoupling_mechanisms


def falsifier_registry() -> dict[str, FalsifierRegime]:
    return get_registry().falsifier_registry


def falsifier_tests() -> list[FalsifierTest]:
    return get_registry().tests()


def corrections_log() -> list[Correction]:
    return get_registry().corrections_log


def hard_invariant(invariant_id: str) -> HardInvariant | None:
    return get_registry().hard_invariants.get(invariant_id) or _lookup(
        get_registry().hard_invariants, invariant_id
    )


def soft_invariant(invariant_id: str) -> SoftInvariant | None:
    return get_registry().soft_invariants.get(invariant_id) or _lookup(
        get_registry().soft_invariants, invariant_id
    )


def decoupling_mechanism(mechanism_id: str) -> DecouplingMechanism | None:
    return _lookup(get_registry().decoupling_mechanisms, mechanism_id)


def falsifier_test(test_id: str) -> FalsifierTest | None:
    key = _norm(test_id)
    for test in get_registry().tests():
        if _norm(test.id) == key:
            return test
    return None


def correction(correction_id: str) -> Correction | None:
    key = _norm(correction_id)
    for entry in get_registry().corrections_log:
        if _norm(entry.id) == key:
            return entry
    return None


def _lookup(collection: Mapping[str, Any], entry_id: str) -> Any:
    key = _norm(entry_id)
    for candidate_id, entry in collection.items():
        if _norm(candidate_id) == key:
            return entry
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Threshold provenance
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_path(node: Any, dotted: str) -> tuple[Any, bool]:
    """Resolve ``a.b[0].c`` / ``corrections_log[6]`` against a parsed YAML node."""
    current = node
    for part in dotted.split("."):
        name = part
        indices: list[str] = []
        while name.endswith("]"):
            head, _, index_text = name[:-1].rpartition("[")
            name = head
            indices.append(index_text)
        indices.reverse()
        if name:
            if not isinstance(current, Mapping) or name not in current:
                return None, False
            current = current[name]
        for index_text in indices:
            if not isinstance(current, Sequence) or isinstance(current, (str, bytes)):
                return None, False
            try:
                current = current[int(index_text)]
            except (ValueError, IndexError):
                return None, False
    return current, True


def _id_index(raw: Mapping[str, Any]) -> dict[str, tuple[str, str, str]]:
    """Map normalised id -> (section, id_as_written, yaml_path)."""
    index: dict[str, tuple[str, str, str]] = {}
    for section in (
        "epistemic_tiers",
        "extraction_axes",
        "hard_invariants",
        "soft_invariants",
        "decoupling_mechanisms",
    ):
        for entry_id in _as_mapping(raw.get(section)):
            index.setdefault(
                _norm(entry_id), (section, str(entry_id), f"{section}.{entry_id}")
            )
    for regime_id, body in _as_mapping(raw.get("falsifier_registry")).items():
        index.setdefault(
            _norm(regime_id),
            ("falsifier_registry", str(regime_id), f"falsifier_registry.{regime_id}"),
        )
        for field in ("contradiction_tests", "deficit_tests"):
            for test_id in _as_mapping(_as_mapping(body).get(field)):
                index.setdefault(
                    _norm(test_id),
                    (
                        "falsifier_registry",
                        str(test_id),
                        f"falsifier_registry.{regime_id}.{field}.{test_id}",
                    ),
                )
    corrections = raw.get("corrections_log")
    if isinstance(corrections, Sequence) and not isinstance(corrections, (str, bytes)):
        for position, entry in enumerate(corrections):
            entry_id = _text(_as_mapping(entry).get("id"))
            if entry_id:
                index.setdefault(
                    _norm(entry_id), ("corrections_log", entry_id, f"corrections_log[{position}]")
                )
    return index


def _gate_index(raw: Mapping[str, Any]) -> dict[str, list[tuple[str, str, str]]]:
    """Map normalised gate id -> [(section, id, yaml_path), ...] for declared gates."""
    index: dict[str, list[tuple[str, str, str]]] = {}
    for section in (
        "hard_invariants",
        "soft_invariants",
        "decoupling_mechanisms",
        "epistemic_tiers",
        "extraction_axes",
    ):
        for entry_id, body in _as_mapping(raw.get(section)).items():
            body_map = _as_mapping(body)
            for field in ("gate", "gates", "entry_gate"):
                for gate in _text_list(body_map.get(field)):
                    index.setdefault(_norm(gate), []).append(
                        (section, str(entry_id), f"{section}.{entry_id}")
                    )
    return index


def _is_citation_literal(text: str, start: int, value: float) -> bool:
    """True when a literal looks like a literature year, not a threshold."""
    if not value.is_integer():
        return False
    if not (_CITATION_YEAR_RANGE[0] <= value <= _CITATION_YEAR_RANGE[1]):
        return False
    window = text[max(0, start - _CITATION_WINDOW) : start]
    return bool(_CITATION_CONTEXT_RE.search(window))


def _extract_literals(
    text: str, *, max_length: int = 96, include_citations: bool = False
) -> list[tuple[float, str]]:
    """Numeric literals in a text, each with the quoted source span.

    Citation years (Byerlee 1978, Steno 1669) are excluded unless
    ``include_citations`` is set — they are provenance of the doctrine, not
    thresholds.
    """
    out: list[tuple[float, str]] = []
    for match in _LITERAL_RE.finditer(text):
        try:
            value = float(match.group(1))
        except ValueError:  # pragma: no cover - defensive
            continue
        if not include_citations and _is_citation_literal(text, match.start(), value):
            continue
        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)
        quote = " ".join(text[start:end].split())
        if len(quote) > max_length:
            quote = quote[:max_length] + "…"
        out.append((value, quote))
    return out


def _text_index(raw: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Flat ``(yaml_path, text)`` index over every string leaf of the registry."""
    out: list[tuple[str, str]] = []
    for section in (
        "epistemic_tiers",
        "extraction_axes",
        "hard_invariants",
        "soft_invariants",
        "decoupling_mechanisms",
        "falsifier_registry",
    ):
        for entry_id, body in _as_mapping(raw.get(section)).items():
            base = f"{section}.{entry_id}"
            for rel, text in _iter_strings(body):
                out.append((f"{base}.{rel}" if rel else base, text))
    corrections = raw.get("corrections_log")
    if isinstance(corrections, Sequence) and not isinstance(corrections, (str, bytes)):
        for position, entry in enumerate(corrections):
            for rel, text in _iter_strings(entry):
                out.append((f"corrections_log[{position}].{rel}" if rel else f"corrections_log[{position}]", text))
    return out


def _entry_strings(raw: Mapping[str, Any], yaml_path: str) -> list[tuple[str, str]]:
    body, found = _resolve_path(raw, yaml_path)
    if not found:
        return []
    return [
        (f"{yaml_path}.{rel}" if rel else yaml_path, text) for rel, text in _iter_strings(body)
    ]


def _correction_blobs(raw: Mapping[str, Any]) -> list[tuple[int, str, dict[str, Any]]]:
    """``(position, id, entry_map)`` for each corrections_log entry."""
    out: list[tuple[int, str, dict[str, Any]]] = []
    corrections = raw.get("corrections_log")
    if not isinstance(corrections, Sequence) or isinstance(corrections, (str, bytes)):
        return out
    for position, entry in enumerate(corrections):
        entry_map = _as_mapping(entry)
        out.append(
            (position, _text(entry_map.get("id")) or f"corrections_log[{position}]", entry_map)
        )
    return out


def _correction_blob(entry_map: Mapping[str, Any]) -> str:
    return " ".join(
        filter(
            None,
            (_text(entry_map.get(key)) for key in ("id", "defect", "verdict", "reason", "fix")),
        )
    )


def _related_corrections(
    registry: RegimeRegistry, entry_text: str, literals: Sequence[float]
) -> list[dict[str, Any]]:
    """Corrections sharing a numeric literal or a *distinctive* keyword.

    Heuristic linkage, labelled as such in the payload — the registry declares
    no foreign key between a threshold and a corrections_log entry.  A keyword
    counts only when it is distinctive (length >= 6 and it occurs in exactly one
    corrections entry), so generic doctrine words do not drag in every
    correction in the log.
    """
    tokens = {
        token
        for token in _TOKEN_RE.findall(entry_text.upper())
        if len(token) >= 6 and token not in _TOKEN_STOPWORDS
    }
    entries = _correction_blobs(registry.raw)
    if not entries or not (tokens or literals):
        return []

    blob_tokens = {
        position: {token for token in _TOKEN_RE.findall(_correction_blob(body).upper()) if len(token) >= 6}
        for position, _entry_id, body in entries
    }
    found: list[dict[str, Any]] = []
    for position, entry_id, body in entries:
        blob = _correction_blob(body)
        hits: list[str] = []
        for value in literals:
            literal_text = f"{value:g}"
            if literal_text in blob:
                hits.append(f"literal {literal_text}")
        distinctive = [
            token
            for token in sorted(tokens & blob_tokens[position])
            if sum(1 for other in blob_tokens.values() if token in other) == 1
        ]
        if distinctive:
            hits.append("distinctive keyword " + ", ".join(distinctive[:4]))
        if hits:
            found.append(
                {
                    "id": entry_id,
                    "defect": _text(body.get("defect")),
                    "verdict": _text(body.get("verdict")),
                    "reason": _text(body.get("reason")),
                    "fix": _text(body.get("fix")),
                    "matched_on": hits,
                    "provenance": _provenance_for(registry, f"corrections_log[{position}]"),
                }
            )
    return found


def _keyword_candidates(raw: Mapping[str, Any], tokens: Sequence[str]) -> list[str]:
    """Entry ids whose combined text contains EVERY token (unique-best ranking).

    A token-subset match is not enough — partial overlap would attribute a
    threshold to an unrelated entry just because it shares the word "regime".
    """
    if not tokens:
        return []
    per_entry: dict[str, str] = {}
    for yaml_path, text in _text_index(raw):
        parts = yaml_path.split(".")
        if len(parts) < 2 or parts[0] not in _KEYWORD_SECTIONS:
            continue
        owner_id = f"{parts[0]}.{parts[1]}"
        per_entry[owner_id] = per_entry.get(owner_id, "") + " " + text.upper()
    matched = [
        owner_id
        for owner_id, blob in per_entry.items()
        if all(token in blob for token in tokens)
    ]
    if len(matched) <= 1:
        return matched

    def rank(owner_id: str) -> tuple[int, int]:
        body, found = _resolve_path(raw, owner_id)
        body_map = _as_mapping(body) if found else {}
        declares_status = any(not _blank(body_map.get(key)) for key in _THRESHOLD_STATUS_KEYS)
        section = owner_id.split(".")[0]
        section_rank = (
            _SECTION_PREFERENCE.index(section)
            if section in _SECTION_PREFERENCE
            else len(_SECTION_PREFERENCE)
        )
        return (0 if declares_status else 1, section_rank)

    best = min(rank(owner_id) for owner_id in matched)
    return sorted(owner_id for owner_id in matched if rank(owner_id) == best)


def _provenance_for(registry: RegimeRegistry, yaml_path: str) -> dict[str, Any]:
    return Provenance(
        artifact_id=registry.meta.artifact_id or "UNKNOWN_ARTIFACT_ID",
        artifact_version=registry.meta.version,
        source_file=registry.source_file,
        source_sha256=registry.source_sha256,
        yaml_path=yaml_path,
    ).as_dict()


def _not_found(
    registry: RegimeRegistry,
    query: str,
    note: str,
    candidates: Sequence[str],
    *,
    status: str = "NOT_FOUND",
) -> dict[str, Any]:
    """Honest miss: no invented thresholds, no assumed defaults."""
    return {
        "query": query,
        "resolved": False,
        "status": status,
        "resolved_via": None,
        "registry_id": None,
        "section": None,
        "yaml_path": None,
        "note": note,
        "candidates": list(candidates),
        "provenance": _provenance_for(registry, "$"),
    }


def threshold_source(
    gate_id_or_constant: str,
    *,
    registry: RegimeRegistry | None = None,
    include_literals: bool = True,
) -> dict[str, Any]:
    """Provenance for a threshold: gate id, registry id, or source constant.

    Resolution order — every step is driven by the YAML or by a declared
    pointer, never by an in-code threshold:

    1. exact registry id (``REG-002``, ``M-SALT``, ``DEFICIT_NO_GROWTH_WEDGE`` …)
    2. gate id declared in the YAML (``K-XCUT`` → REG-006)
    3. code anchor wiring (``_COULOMB_TOLERANCE_DEG`` → REG-002) — pointers only
    4. numeric literal / keyword match over registry text

    Returns a payload carrying the declared provenance: threshold status
    (e.g. ``RULE_OF_THUMB``), validity domain, alternatives, related
    corrections, numeric literals found in the registry text (each with its
    quoted source span), and a ``Provenance`` block with the source SHA-256.

    Never invents a value.  If the identifier is not declared in the registry
    the payload says ``NOT_FOUND``.
    """
    active = registry if registry is not None else get_registry()
    raw = active.raw
    query = _text(gate_id_or_constant) or ""
    key = _norm(query)
    ids = _id_index(raw)

    resolved_via: str | None = None
    location = ids.get(key)
    if location is not None:
        resolved_via = "registry_id"
    else:
        owners = _gate_index(raw).get(key)
        if owners:
            owners = sorted(
                owners,
                key=lambda item: _SECTION_PREFERENCE.index(item[0])
                if item[0] in _SECTION_PREFERENCE
                else len(_SECTION_PREFERENCE),
            )
            location = owners[0]
            resolved_via = "gate_id"
        else:
            alias_target = CODE_ANCHOR_ALIASES.get(query) or CODE_ANCHOR_ALIASES.get(key)
            if alias_target:
                location = ids.get(_norm(alias_target))
                if location is None:
                    return _not_found(
                        active,
                        query,
                        (
                            f"code anchor alias declared for {query!r} points at "
                            f"{alias_target!r}, which is not present in the registry "
                            f"({active.source_file})"
                        ),
                        [],
                    )
                resolved_via = "code_anchor_alias"

    if location is None:
        literals = [value for value, _ in _extract_literals(query)]
        text_index = _text_index(raw)
        if literals:
            matched_paths: list[str] = []
            for yaml_path, text in text_index:
                if any(f"{value:g}" in text for value in literals):
                    if yaml_path not in matched_paths:
                        matched_paths.append(yaml_path)
            ranked = _rank_paths(matched_paths, raw)
            if ranked:
                location = next(
                    (
                        (path.split(".")[0], path.split(".")[-1], path)
                        for path in ranked
                    ),
                    None,
                )
                resolved_via = "numeric_literal_match"
        if location is None:
            tokens = [
                token
                for token in _TOKEN_RE.findall(query.upper())
                if len(token) >= 4 and token not in _TOKEN_STOPWORDS
            ]
            candidates = _keyword_candidates(raw, tokens)
            if len(candidates) == 1:
                section_name, entry_name = candidates[0].split(".", 1)
                location = (section_name, entry_name, candidates[0])
                resolved_via = "keyword_match"
            elif candidates:
                return _not_found(
                    active,
                    query,
                    (
                        "several registry entries match every token in the query; "
                        "no single threshold can be attributed without a declared id"
                    ),
                    candidates,
                    status="AMBIGUOUS",
                )
            if location is None:
                return _not_found(
                    active,
                    query,
                    (
                        "no registry entry declares this identifier, gate id or "
                        "threshold anchor — the registry is the only source of "
                        "thresholds and it does not contain one for this name"
                    ),
                    [],
                )

    section, entry_id, yaml_path = location
    body, found = _resolve_path(raw, yaml_path)
    if not found:
        return _not_found(
            active, query, f"resolved path {yaml_path!r} is not present in the YAML", []
        )
    entry = _as_mapping(body)

    status_value, status_key = _declared(entry, _THRESHOLD_STATUS_KEYS)
    validity_domain = _text(entry.get("validity_domain"))
    alternatives = _text_list(entry.get("alternatives_for_deviation"))
    numeric_literals: list[dict[str, Any]] = []
    if include_literals:
        for field_path, text in _entry_strings(raw, yaml_path):
            for value, quote in _extract_literals(text):
                numeric_literals.append(
                    {
                        "value": value,
                        "extraction": "text_literal",
                        "field": field_path,
                        "quote": quote,
                    }
                )

    payload = {
        "query": query,
        "resolved": True,
        "status": "RESOLVED",
        "resolved_via": resolved_via,
        "registry_id": entry_id,
        "section": section,
        "yaml_path": yaml_path,
        "name": _text(entry.get("name")) or _text(entry.get("regime")),
        "gate": _text(entry.get("gate")) or _text(entry.get("entry_gate")),
        # Threshold epistemic status, exactly as declared (None when undeclared).
        "threshold_status": status_value,
        "threshold_status_field": f"{yaml_path}.{status_key}" if status_key else None,
        "is_declared_hard_invariant": section == "hard_invariants",
        "on_violation": _text(entry.get("on_violation")) or _text(entry.get("violation_action")),
        "epistemic_tag": _text(entry.get("epistemic_tag")),
        "statement": _text(entry.get("statement")),
        "justification": _text(entry.get("warning")) or _text(entry.get("corrected_claim")),
        "validity_domain": validity_domain,
        "validity_envelope": _text(entry.get("envelope")),
        "alternatives": alternatives,
        "alternatives_declared": bool(alternatives),
        "returns": _verdict(entry.get("returns")),
        "guard": _text(entry.get("requires")) or _text(entry.get("coverage_requirement")),
        "numeric_literals": numeric_literals,
        "corrections": _related_corrections(
            active,
            " ".join([entry_id, _text(entry.get("name")) or "", _text(entry.get("warning")) or ""]),
            [item["value"] for item in numeric_literals],
        ),
        "correction_linkage": "heuristic — shared numeric literal or entry keyword; not a declared foreign key",
        "registry_entry": _jsonable(entry),
        "provenance": _provenance_for(active, yaml_path),
    }
    return payload


def _rank_paths(matched_paths: Sequence[str], raw: Mapping[str, Any]) -> list[str]:
    """Rank literal-match entry paths: entries declaring a threshold status first.

    Ranking is derived from the registry (which sections declare
    ``threshold_source``), not from an in-code preference for a value.
    """
    owners: list[str] = []
    for path in matched_paths:
        owner = path.rsplit(".", 1)[0] if "." in path else path
        if owner not in owners:
            owners.append(owner)

    def sort_key(owner: str) -> tuple[int, str]:
        body, found = _resolve_path(raw, owner)
        declares_status = False
        if found:
            body_map = _as_mapping(body)
            declares_status = any(
                not _blank(body_map.get(key)) for key in _THRESHOLD_STATUS_KEYS
            )
        section_rank = (
            _SECTION_PREFERENCE.index(owner.split(".")[0])
            if owner.split(".")[0] in _SECTION_PREFERENCE
            else len(_SECTION_PREFERENCE)
        )
        return (0 if declares_status else 1, f"{section_rank:02d}.{owner}")

    return sorted(owners, key=sort_key)


def threshold_status(gate_id_or_constant: str, *, registry: RegimeRegistry | None = None) -> str | None:
    """Convenience: the declared threshold status, or ``None`` if undeclared."""
    return threshold_source(gate_id_or_constant, registry=registry, include_literals=False).get(
        "threshold_status"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Validation — the registry's own internal laws
# ═══════════════════════════════════════════════════════════════════════════


def _finding(law: str, code: str, path: str, detail: str) -> dict[str, str]:
    return {"law": law, "code": code, "path": path, "detail": detail}


def _iter_falsifier_tests(
    falsifiers: Mapping[str, Any],
) -> Iterable[tuple[str, str, str, Mapping[str, Any]]]:
    """Yield ``(regime_id, field, test_id, test_body)`` for every declared test."""
    for regime_id, regime in falsifiers.items():
        regime_map = _as_mapping(regime)
        for field in ("contradiction_tests", "deficit_tests"):
            for test_id, test in _as_mapping(regime_map.get(field)).items():
                yield str(regime_id), field, str(test_id), _as_mapping(test)


def _law_a(raw: Mapping[str, Any]) -> dict[str, Any]:
    """CONTRADICTION_* must declare KILL AND the evidence that licenses it."""
    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    checked = 0
    for regime_id, field, test_id, test in _iter_falsifier_tests(_as_mapping(raw.get("falsifier_registry"))):
        if not test_id.upper().startswith("CONTRADICTION"):
            continue
        checked += 1
        path = f"falsifier_registry.{regime_id}.{field}.{test_id}"
        verdict = _verdict(test.get("returns"))
        if verdict is None:
            violations.append(
                _finding(_LAW_A, "CONTRADICTION_MISSING_RETURNS", path, "no 'returns' declared")
            )
        elif verdict != VERDICT_KILL:
            violations.append(
                _finding(
                    _LAW_A,
                    "CONTRADICTION_DOES_NOT_KILL",
                    path,
                    f"returns={verdict!r}; a CONTRADICTION (measured counter-evidence) is the direction permitted to KILL",
                )
            )
        _guard_value, guard_key = _declared(test, _GUARD_KEYS)
        if guard_key is None:
            violations.append(
                _finding(
                    _LAW_A,
                    "CONTRADICTION_UNGUARDED_KILL",
                    path,
                    (
                        "declares KILL with no "
                        f"{' or '.join(_GUARD_KEYS)} — an unguarded kill has no declared "
                        "evidence or coverage licence"
                    ),
                )
            )
            if not _blank(test.get("scope")):
                warnings.append(
                    _finding(
                        _LAW_A,
                        "CONTRADICTION_SCOPE_ONLY",
                        path,
                        "declares 'scope' (partial applicability guard) but no requires/coverage_requirement",
                    )
                )
        if field != "contradiction_tests":
            warnings.append(
                _finding(
                    _LAW_A,
                    "CONTRADICTION_IN_DEFICIT_SET",
                    path,
                    "a CONTRADICTION_* entry is filed under deficit_tests",
                )
            )
    return {"passed": not violations, "violations": violations, "warnings": warnings, "checked": checked}


def _law_b(raw: Mapping[str, Any]) -> dict[str, Any]:
    """DEFICIT_* may only return UNMEASURED.  Declaring KILL is a hard failure."""
    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    checked = 0
    for regime_id, field, test_id, test in _iter_falsifier_tests(_as_mapping(raw.get("falsifier_registry"))):
        if not test_id.upper().startswith("DEFICIT"):
            continue
        checked += 1
        path = f"falsifier_registry.{regime_id}.{field}.{test_id}"
        verdict = _verdict(test.get("returns"))
        if verdict is None:
            violations.append(
                _finding(_LAW_B, "DEFICIT_MISSING_RETURNS", path, "no 'returns' declared")
            )
        elif verdict == VERDICT_KILL:
            violations.append(
                _finding(
                    _LAW_B,
                    "DEFICIT_DECLARES_KILL",
                    path,
                    (
                        "returns=KILL — FALSIFIER DIRECTION RULE: an absence test fires on thin "
                        "data as readily as on a true negative; a DEFICIT may only return UNMEASURED"
                    ),
                )
            )
        elif verdict != VERDICT_UNMEASURED:
            violations.append(
                _finding(
                    _LAW_B,
                    "DEFICIT_RETURNS_NOT_UNMEASURED",
                    path,
                    f"returns={verdict!r}; a DEFICIT_* test must return UNMEASURED",
                )
            )
        for key, value in test.items():
            if key == "returns":
                continue
            for _rel, leaf in _deep_values(value):
                if isinstance(leaf, str) and leaf.strip().upper() == VERDICT_KILL:
                    violations.append(
                        _finding(
                            _LAW_B,
                            "DEFICIT_DECLARES_KILL",
                            f"{path}.{key}",
                            "KILL declared inside a DEFICIT_* test — deficits may never kill",
                        )
                    )
        if _blank(test.get("why_not_kill")):
            warnings.append(
                _finding(
                    _LAW_B,
                    "DEFICIT_WITHOUT_WHY_NOT_KILL",
                    path,
                    "no 'why_not_kill' rationale declared (structure only; not a violation)",
                )
            )
        if field != "deficit_tests":
            warnings.append(
                _finding(
                    _LAW_B,
                    "DEFICIT_IN_CONTRADICTION_SET",
                    path,
                    "a DEFICIT_* entry is filed under contradiction_tests",
                )
            )
    return {"passed": not violations, "violations": violations, "warnings": warnings, "checked": checked}


def _law_c(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Every hard invariant declares a non-empty on_violation and epistemic_tag."""
    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    hard = _as_mapping(raw.get("hard_invariants"))
    checked = 0
    for invariant_id, body in hard.items():
        checked += 1
        path = f"hard_invariants.{invariant_id}"
        body_map = _as_mapping(body)
        action_value, action_key = _declared(body_map, _ON_VIOLATION_KEYS)
        if action_key is None:
            violations.append(
                _finding(
                    _LAW_C,
                    "HARD_INVARIANT_MISSING_ON_VIOLATION",
                    path,
                    f"none of {', '.join(_ON_VIOLATION_KEYS)} declared (non-empty)",
                )
            )
        elif action_key != "on_violation":
            warnings.append(
                _finding(
                    _LAW_C,
                    "HARD_INVARIANT_ALTERNATE_ACTION_KEY",
                    path,
                    f"action declared as {action_key!r} (F0 spelling) rather than 'on_violation'",
                )
            )
        if _blank(body_map.get("epistemic_tag")):
            violations.append(
                _finding(
                    _LAW_C,
                    "HARD_INVARIANT_MISSING_EPISTEMIC_TAG",
                    path,
                    "no 'epistemic_tag' declared",
                )
            )
    if not hard:
        violations.append(
            _finding(_LAW_C, "SECTION_MISSING", "hard_invariants", "section absent or empty")
        )
    return {"passed": not violations, "violations": violations, "warnings": warnings, "checked": checked}


_REQUIRED_CORRECTION_FIELDS = ("id", "defect", "verdict", "reason", "fix")


def _law_d(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Every corrections_log entry carries id/defect/verdict/reason/fix."""
    violations: list[dict[str, str]] = []
    checked = 0
    corrections = raw.get("corrections_log")
    if not isinstance(corrections, Sequence) or isinstance(corrections, (str, bytes)):
        violations.append(
            _finding(
                _LAW_D,
                "SECTION_MISSING",
                "corrections_log",
                "corrections_log absent or not a sequence",
            )
        )
        return {"passed": False, "violations": violations, "warnings": [], "checked": 0}
    for position, entry in enumerate(corrections):
        checked += 1
        entry_map = _as_mapping(entry)
        entry_id = _text(entry_map.get("id")) or f"[{position}]"
        for field_name in _REQUIRED_CORRECTION_FIELDS:
            if _blank(entry_map.get(field_name)):
                violations.append(
                    _finding(
                        _LAW_D,
                        "CORRECTION_MISSING_FIELD",
                        f"corrections_log[{position}].{field_name}",
                        f"correction {entry_id!r} does not declare '{field_name}'",
                    )
                )
    if not corrections:
        violations.append(
            _finding(_LAW_D, "SECTION_MISSING", "corrections_log", "no corrections recorded")
        )
    return {"passed": not violations, "violations": violations, "warnings": [], "checked": checked}


def validate_registry(
    registry: RegimeRegistry | Mapping[str, Any] | str | Path | None = None,
) -> dict[str, Any]:
    """Assert the registry's own internal laws.  Verdict + violations, no score.

    Laws:
      A. every ``CONTRADICTION_*`` test declares ``returns: KILL`` **and** a
         ``requires`` or ``coverage_requirement`` guard.
      B. **load-bearing** — every ``DEFICIT_*`` test returns ``UNMEASURED`` and
         never declares KILL.
      C. every ``hard_invariants`` entry has a non-empty violation action and
         ``epistemic_tag``.
      D. every ``corrections_log`` entry declares id/defect/verdict/reason/fix.

    Args:
        registry: a :class:`RegimeRegistry`, a raw mapping (in-memory mutation),
            a path to a YAML file, or ``None`` for the on-disk registry.

    Returns:
        ``{"passed": bool, "laws": {...}, "violations": [...], "warnings": [...],
        "checked": {...}, "artifact_id": ..., "source_file": ...}``

    Raises:
        RegimeRegistryNotFoundError / RegimeRegistryParseError: only when a file
        is missing or unparseable.  Malformed *data* is reported, never raised.
    """
    if registry is None:
        raw: Mapping[str, Any] = get_registry().raw
        artifact_id = get_registry().meta.artifact_id or "UNKNOWN_ARTIFACT_ID"
        source_file = get_registry().source_file
    elif isinstance(registry, RegimeRegistry):
        raw = registry.raw
        artifact_id = registry.meta.artifact_id or "UNKNOWN_ARTIFACT_ID"
        source_file = registry.source_file
    elif isinstance(registry, Mapping):
        raw = registry
        artifact_id = _text(_as_mapping(registry.get("meta")).get("artifact_id")) or "UNKNOWN_ARTIFACT_ID"
        source_file = "<in-memory mapping>"
    elif isinstance(registry, (str, Path)):
        loaded = load_registry(registry)
        raw = loaded.raw
        artifact_id = loaded.meta.artifact_id or "UNKNOWN_ARTIFACT_ID"
        source_file = loaded.source_file
    else:
        return {
            "passed": False,
            "artifact_id": "UNKNOWN_ARTIFACT_ID",
            "source_file": "<unsupported input>",
            "laws": {},
            "violations": [
                _finding(
                    "input",
                    "UNSUPPORTED_REGISTRY_INPUT",
                    "$",
                    f"cannot validate input of type {type(registry).__name__}",
                )
            ],
            "warnings": [],
            "checked": {},
        }

    if not isinstance(raw, Mapping):
        return {
            "passed": False,
            "artifact_id": artifact_id,
            "source_file": source_file,
            "laws": {},
            "violations": [
                _finding("input", "REGISTRY_NOT_A_MAPPING", "$", "registry root is not a mapping")
            ],
            "warnings": [],
            "checked": {},
        }

    laws = {
        _LAW_A: _law_a(raw),
        _LAW_B: _law_b(raw),
        _LAW_C: _law_c(raw),
        _LAW_D: _law_d(raw),
    }
    violations = [item for law in laws.values() for item in law["violations"]]
    warnings = [item for law in laws.values() for item in law.get("warnings", [])]
    return {
        "passed": not violations,
        "artifact_id": artifact_id,
        "source_file": source_file,
        "laws": laws,
        "violations": violations,
        "warnings": warnings,
        "checked": {
            "contradiction_tests": laws[_LAW_A]["checked"],
            "deficit_tests": laws[_LAW_B]["checked"],
            "hard_invariants": laws[_LAW_C]["checked"],
            "corrections": laws[_LAW_D]["checked"],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Sibling F0 constitution (read-only convenience)
# ═══════════════════════════════════════════════════════════════════════════


def f0_companion(path: str | Path | None = None) -> dict[str, Any]:
    """Load the sibling F0 file (TECT-001..012) ids + provenance.

    Read-only convenience so callers can cite the paradigm counterpart declared
    in ``meta.paradigm_counterpart`` without hardcoding the TECT ids.
    """
    companion_path = Path(path) if path is not None else F0_COMPANION_PATH
    raw, digest = _read_yaml(companion_path)
    section = _as_mapping(raw.get("tectonic_invariants"))
    meta_map = _as_mapping(raw.get("meta"))
    return {
        "artifact_id": _text(meta_map.get("artifact_id")),
        "version": _text(meta_map.get("version")),
        "ids": list(section.keys()),
        "count": len(section),
        "provenance": Provenance(
            artifact_id=_text(meta_map.get("artifact_id")) or "UNKNOWN_ARTIFACT_ID",
            artifact_version=_text(meta_map.get("version")),
            source_file=str(companion_path),
            source_sha256=digest,
            yaml_path="tectonic_invariants",
        ).as_dict(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI — validate the registry on disk
# ═══════════════════════════════════════════════════════════════════════════


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    path = Path(args[0]) if args else None
    if path is not None:
        report = validate_registry(load_registry(path))
    else:
        report = validate_registry()
    print(json.dumps(_jsonable(report), indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
