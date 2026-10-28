"""disclosure.py — public/enterprise separation for basin claims (2026-10-28).

WHY THIS EXISTS
    The public MCP endpoint (geox.arif-fazil.com/mcp) serves anonymous sessions.
    Measured 2026-10-28 by an external grader: the KINABALU_BASIN profile returned
    /root/GEOX/outputs/kl2_kinabalu/ absolute paths and a de-identified well's
    pay-zone attribution (DW-A, GWC within NN10) to anyone who asked.

    The F13 purge of 2026-10-08 removed well-file VALUES. The narrative survived,
    and the narrative said where the contact sits. Removing the number while
    publishing the zone does not protect the well: for a competent reader the
    zone IS the information, and the metres were always an estimate.

DESIGN RULE — custody, not credit
    The origin of an INPUT does not own the OUTPUT. Arif's reading rules,
    correlation law, SRU rule, stage framework and contradiction notes are his
    own reasoning and belong in the public layer, credited to him. A third
    party's well file is not his to publish. Those are two different claims and
    they are NOT both answered by labelling the basin "enterprise data".

    So classification keys on WHAT IS DISCLOSED, never on who supplied an input:

        a statement that can locate a confidential well's pay zone
            -> ENTERPRISE, regardless of author or de-identification
        a statement about framework, method, geometry, contradiction, or
        falsifier with no well attribution
            -> PUBLIC

RE-IDENTIFICATION RULE (the one that decides edge cases)
    A well code plus a stratigraphic position is the well. The well code alone,
    the zone alone, or the depth alone may each be innocent; the coupling is
    not. WELL_ATTRIBUTION_RE detects the coupling and any of its parts that
    only a well file could supply.

FAIL-CLOSED
    An entry whose classification function raises is ENTERPRISE. Nothing becomes
    public by omission or by a parser bug.

NOT A VERDICT
    This module decides presentation, not truth. It never edits a claim, never
    ranks it, never promotes a truth class. It drops or withholds; it does not
    judge. Authority ceiling stays 555_COMPUTE_ONLY.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

PUBLIC = "PUBLIC"
ENTERPRISE = "ENTERPRISE"

# Signals that a claim is coupled to a confidential well file.
# Deliberately conservative: a false ENTERPRISE costs a public omission,
# a false PUBLIC costs the sovereign his protection.
WELL_ATTRIBUTION_RE = re.compile(
    r"\bDW-[A-Z]\b"  # de-identified well codes (DW-A)
    r"|\bWCR\b"  # well completion report
    r"|\bwell[- ]file\b"
    r"|\bwell[- ]completion\b"
    r"|\bGWC\b"  # gas-water contact
    r"|\bTVDSS\b|\bTVD\b"
    r"|\bseabed\b.*\bTD\b"
    r"|\bformation tops\b"
    r"|\bpenetration chart\b"
    r"|\bgas pay\b",
    re.IGNORECASE,
)

# NOTE (2026-10-28): a bare biostrat zone token (NN10, NN11A) is NOT a disclosure
# signal. NN zones are public science (Martini 1971) and they carry Arif's stage
# framework, which belongs in the public layer. The risk is the COUPLING of a
# zone to a specific well's pay — caught above by the well code, the contact, or
# the pay language, never by the zone name alone.

# Absolute repository paths must never reach any external session.
ABS_PATH_RE = re.compile(r"(/root/[\w./-]+|/opt/[\w./-]+|/var/[\w./-]+)")

_ANON_ACTORS = {"", None, "auto-anon", "anonymous", "anon"}


def is_public_session(session_id: str | None, actor_id: str | None) -> bool:
    """True when the caller is an anonymous/public session.

    Fail-closed: an unrecognised session is treated as public, because a
    public caller who is misread as enterprise is a leak, while an enterprise
    caller misread as public is only a nuisance.
    """
    if actor_id in _ANON_ACTORS:
        return True
    if not actor_id:
        return True
    sid = (session_id or "").upper()
    return sid.startswith("ANON") or sid == ""


def _text_of(claim: dict[str, Any]) -> str:
    """Claim text + source only — deliberately NOT evidence_refs.

    Refs are pointers, not assertions. A framework claim grounded in a well
    ("SRU age narrowed inboard, well-witnessed") is Arif's reasoning and stays
    public; only the pointer is withheld (see scrub_refs). Classifying on refs
    too would bury his own framework because of where it was checked.
    """
    parts = [str(claim.get("claim", ""))]
    src = claim.get("source")
    if src:
        parts.append(str(src))
    return "\n".join(parts)


def classify_claim(claim: dict[str, Any]) -> str:
    """Return PUBLIC or ENTERPRISE for one claim. Fail-closed to ENTERPRISE."""
    try:
        explicit = str(claim.get("disclosure") or "").strip().upper()
        if explicit in (PUBLIC, ENTERPRISE):
            return explicit
        if WELL_ATTRIBUTION_RE.search(_text_of(claim)):
            return ENTERPRISE
        return PUBLIC
    except Exception:
        return ENTERPRISE


def scrub_refs(refs: Iterable[Any]) -> list[str]:
    """Replace unsafe pointers with an artifact-id marker; keep safe refs.

    /root/GEOX/outputs/kl2_kinabalu/x.yaml -> withheld:absolute_path
    internal WCR header + formation tops   -> withheld:confidential_source
    basins/kinabalu_basin/basin_profile.yaml -> unchanged
    """
    out: list[str] = []
    for r in refs or []:
        s = str(r)
        if ABS_PATH_RE.search(s):
            out.append("withheld:absolute_path")
        elif WELL_ATTRIBUTION_RE.search(s):
            out.append("withheld:confidential_source")
        else:
            out.append(s)
    return out


def scrub_text(text: str) -> str:
    """Strip absolute paths from free text (claim keys are used as dict keys)."""
    try:
        return ABS_PATH_RE.sub("withheld:absolute_path", text)
    except Exception:
        return "withheld:unrenderable"


# Sources that are human attestation, relay, or editorial resolution — never
# machine observation. An entry from these must not sit in `observed`.
_RELAY_SOURCE_RE = re.compile(
    r"relay"
    r"|class\b"
    r"|resolution"
    r"|sovereign"
    r"|enterprise"
    r"|audit"
    r"|validation"
    r"|confirmed",
    re.IGNORECASE,
)


def is_machine_observation(claim: dict[str, Any]) -> bool:
    """True only when the claim's source reads as a machine measurement.

    `observed` is a promise to the reader: the machine saw this. A sovereign
    attestation, an enterprise relay, or an audit resolution is an authority
    statement, not an observation, even when it is true. Routing it elsewhere
    does not demote it — it labels it honestly.
    """
    src = str(claim.get("source") or "")
    if not src:
        return False
    return not _RELAY_SOURCE_RE.search(src)


def split_for_public(claims: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Drop ENTERPRISE claims for a public response. Returns (kept, withheld_count)."""
    kept = [c for c in claims if classify_claim(c) == PUBLIC]
    return kept, len(claims) - len(kept)
