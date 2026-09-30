"""
GEOX MCP Prompt — STRUCTURAL INVARIANTS
══════════════════════════════════════════════════════════════════════════
Forged 2026-09-18 · Authority: F13 Arif · Contract: CONTRACT.md v1.0 (frozen)
DITEMPA BUKAN DIBERI — Forged, Not Given

WHAT THIS PROMPT IS FOR
-----------------------
Inject the structural-invariant set into a model's context BEFORE any
tectonic-regime inference. It is a membrane, not a tutorial: every clause below
exists because its absence has produced a specific, named, wrong answer.

It is deliberately usable WITHOUT a vision tool in reach — a model that has read
these invariants and then says "I cannot measure that" is succeeding. A model
that has read them and then reads a dip angle off a picture is failing anyway,
and at least fails with the ceiling stated.

THE INVARIANT SET
-----------------
    I01  Andersonian mechanics (sigma1/sigma2/sigma3 vertical)
    I02  Coulomb failure angle and the deviation band (a RULE OF THUMB)
    I03  Stratal balance — Dahlstrom, concentric, constant bed thickness
    I04  Non-balance is a DIAGNOSTIC, never an error flag (Dahlstrom corollary)
    I05  Resolution — below lambda/4 a thickness is MODEL, not observation
    I06  Display distortion — tan(theta_app) = VE * tan(theta_true)
    I07  Migration state — MIGRATED data do NOT follow the tan relation
    I08  The differential test — tectonic control needs the SAME interval
    I09  Uniform thickness is NON-DISCRIMINATING (the eustatic test is onlap)
    I10  Inheritance beats current stress — weak planes reactivate first
    I11  Growth strata need deformation rate above sedimentation rate
    I12  Epistemic ceiling — geometry gives KINEMATICS, never stress
    I13  The null hypothesis is MANDATORY in every bundle
    I14  Cross-cutting is Steno/Hutton/Lyell — it is NOT Walther's Law
    I15  Salt is a DECOUPLING MECHANISM, not a tectonic regime

ADDENDUM CORRECTIONS BAKED IN (independent audit of the same source material)
------------------------------------------------------------------------------
  * I02 is labelled a RULE OF THUMB, not a hard invariant. Block rotation that
    preserves pure extension is a legitimate cause of dip deviation.
  * I06 states VE is the DIMENSIONLESS display ratio (v_display / v_true), NOT a
    velocity; I07 adds that the tan relation is NOT sufficient for a migrated
    section.
  * I09 states plainly that uniform thickness is non-discriminating and must NOT
    be called evidence for the null hypothesis.
  * I15 reclassifies halokinesis: salt does not express the regional stress
    field, it decouples and MASKS it. Verdict DECOUPLED; where salt is in
    section the stress-regime tests are NOT_APPLICABLE, not failed.
"""

from __future__ import annotations

from typing import Any

from fastmcp.prompts.base import Message

# ══════════════════════════════════════════════════════════════════════════════
# I01-I15 — the invariant set, one entry per invariant, keyed for audit
# ══════════════════════════════════════════════════════════════════════════════

STRUCTURAL_INVARIANTS: tuple[tuple[str, str], ...] = (
    (
        "I01_ANDERSONIAN_MECHANICS",
        """I01 · ANDERSONIAN MECHANICS (Anderson 1951)
    The fault type follows whichever principal stress is VERTICAL, because the
    free surface is a principal plane:

      sigma1 vertical  ->  NORMAL faults, dips ~60 deg from horizontal
      sigma3 vertical  ->  REVERSE / THRUST faults, dips ~30 deg from horizontal
      sigma2 vertical  ->  STRIKE-SLIP faults, near-vertical dips

    "~60" and "~30" are the ANDERSONIAN REFERENCE ANGLES for a Mohr-Coulomb
    material, not constants of nature. A measured population far from them is a
    question, never a conclusion — see I02.""",
    ),
    (
        "I02_COULOMB_DEVIATION_RULE_OF_THUMB",
        """I02 · COULOMB FAILURE ANGLE — AND THE DEVIATION BAND IS A RULE OF THUMB
    theta_failure = 45 - phi/2, with Byerlee friction mu ~ 0.6-0.85 (phi ~ 30 deg,
    so theta ~ 60 deg for a normal fault). Byerlee 1978.

    The +/- 15 deg BAND AROUND THAT REFERENCE IS A RULE OF THUMB, NOT A HARD
    PHYSICS INVARIANT. Do not present it as one, and do not treat an excursion
    as a measurement failure. Legitimate causes of a dip population outside the
    band include:

      * BLOCK ROTATION that preserves PURE EXTENSION — domino/bookshelf
        rotation changes the observed dip of a planar fault while the tectonic
        regime is unchanged;
      * a weak substrate or detachment (salt, shale, overpressured mudstone);
      * OVERPRESSURE, which lowers effective normal stress and rotates the
        failure angle;
      * PRE-EXISTING FABRIC (inherited basement or rift faults) — see I10.

    NEVER CONCLUDE "THE REGIME CHANGED" FROM A DIP DEVIATION ALONE. A regime
    change needs an independent observation — a polarity switch, a restored
    shortening or extension, a cross-cutting sense reversal — not an angle.""",
    ),
    (
        "I03_STRATAL_BALANCE_DAHLSTROM",
        """I03 · STRATAL BALANCE — DAHLSTROM 1969, AND ITS SCOPE
    Stratal balance (Dahlstrom 1969, "Balanced cross sections") holds for
    CONCENTRIC deformation at CONSTANT BED THICKNESS, measured IN A
    CROSS-SECTION. Line length and bed area are conserved only inside those
    assumptions.

    It does NOT survive:
      * COMPACTION  — thickness is not conserved in depth (see I12's sibling
        rule: decompact before any thickness argument);
      * PRESSURE SOLUTION / chemical compaction — material leaves the bed along
        stylolites, so line length is NOT conserved;
      * LAYER-PARALLEL SHEAR — beds slide past one another, so bed thickness
        and line length decouple.

    Where any of those operate, non-balance is EXPECTED and carries no
    information about the interpreter.""",
    ),
    (
        "I04_NON_BALANCE_IS_A_DIAGNOSTIC",
        """I04 · NON-BALANCE IS A DIAGNOSTIC, NEVER AN ERROR FLAG
    Failure to restore a section without gaps or overlaps MEANS A STRUCTURE IS
    MISSING FROM THE SECTION. The candidate list, in order of how often it is
    the answer:

      * a blind or sub-seismic fault that was never mapped;
      * layer-parallel shear / a detachment that was not carried;
      * out-of-plane flow (the section is not a plane-strain section);
      * the section is OBLIQUE to tectonic transport, so the true shortening is
        larger than the apparent shortening.

    IT DOES NOT MEAN THE INPUT PICKS WERE WRONG. Never instruct an interpreter
    to bend picks until they balance: picks bent until they balance DESTROY a
    correct interpretation, and the destruction is invisible because the
    resulting section looks tidy. Report non-balance as a diagnostic, with the
    missing-structure candidate list attached.""",
    ),
    (
        "I05_RESOLUTION_TUNING_LIMIT",
        """I05 · RESOLUTION — BELOW lambda/4 A THICKNESS IS MODEL, NOT OBSERVATION
    The tuning (Widess 1973) thickness is lambda/4 at the dominant frequency.
    Below that limit a thinning bed does not produce a shorter wavelet — it
    produces a changing amplitude and a distortion, and any "thickness"
    extracted there is a MODEL-dependent inversion, not an observation.

    Consequence: a sub-tuning fault or bed appears as a REGIONAL FLEXURE or a
    reflectivity distortion, NOT as a picked offset. Do not call a sub-tuning
    feature absent because no offset is picked, and do not call it present
    because a wavelet changed shape.""",
    ),
    (
        "I06_DISPLAY_VERTICAL_EXAGGERATION",
        """I06 · DISPLAY DISTORTION — tan(theta_apparent) = VE * tan(theta_true)
    where VE is the DIMENSIONLESS DISPLAY RATIO

        VE = v_display / v_true

    i.e. the ratio of the vertical scale of the display to its true vertical
    scale. VE IS NOT A VELOCITY. It has no units. Never substitute an interval
    velocity for VE, and never treat a velocity as a correction for VE — they
    are different quantities that happen to share the letter V in a handbook.

    An apparent dip read off an exaggerated display is not geometry. At VE = 2
    a true 15 deg dip displays as ~28 deg; at VE = 5 it displays as ~53 deg.
    Correct, or declare the dips unreliable and refuse the dip argument.""",
    ),
    (
        "I07_MIGRATION_STATE_TAN_RELATION_INSUFFICIENT",
        """I07 · MIGRATION STATE — THE tan RELATION IS NOT SUFFICIENT FOR MIGRATED DATA
    The tan relation in I06 is a DISPLAY correction. It is NOT a migration
    correction.

    MIGRATED DATA DO NOT FOLLOW THE tan RELATION: migration moves reflections
    laterally and steepens or steepens-to-vertical the apparent dip of steep
    events, so the apparent dip on a migrated section is a function of the
    migration algorithm and velocity field as well as the display. On
    UNMIGRATED data the apparent dip is a function of the recording geometry
    instead.

    Therefore A MIGRATION-STATE DECLARATION IS REQUIRED alongside VE: is this
    section pre-migration (stacked), post-migration, or a depth conversion of
    one of those? Without that declaration, state that apparent dips cannot be
    converted to true dips — do not simply apply the tan relation and proceed.""",
    ),
    (
        "I08_DIFFERENTIAL_TEST",
        """I08 · THE DIFFERENTIAL TEST (the only geometry-based tectonic discriminator)
    Tectonic control requires the SAME INTERVAL to show a SPATIAL THICKNESS
    DIFFERENTIAL ACROSS THE STRUCTURE. Not at the structure — ACROSS it.

    Isopachs of one and the same interval, mapped over the structure and its
    flanks, must change. An expansion index (EI = hangingwall / footwall
    thickness) greater than 1 supports syn-tectonic growth for THAT interval.
    That is the test. Everything else is corroboration.""",
    ),
    (
        "I09_UNIFORM_THICKNESS_IS_NON_DISCRIMINATING",
        """I09 · UNIFORM THICKNESS IS NON-DISCRIMINATING — IT IS NOT EVIDENCE OF EUSTASY
    A uniform interval does NOT mean eustasy. Uniform thickness also arises from:

      * STEADY SEDIMENT SUPPLY that tracked accommodation;
      * THERMAL (post-rift) SUBSIDENCE, which is broad and unfaulted;
      * PURE STRIKE-SLIP, which creates little or no vertical accommodation;
      * POST-DEPOSITIONAL SAG or a later regional subsidence event.

    UNIFORM THICKNESS IS NON-DISCRIMINATING: it excludes nothing and supports
    nothing. Do NOT present it as evidence for the null (depositional /
    eustatic) hypothesis, and do not upgrade the null because a differential
    was not found.

    THE EUSTATIC TEST IS NOT THE ABSENCE OF THICKNESS CHANGE. It is a
    REGIONALLY CORRELATIVE SURFACE WITH SYNCHRONOUS ONLAP — the same surface,
    with the same onlapping geometry, at the same stratigraphic level across
    the region, independent of local structure. Test for that, or report the
    null as UNTESTED rather than supported.""",
    ),
    (
        "I10_INHERITANCE_BEATS_CURRENT_STRESS",
        """I10 · INHERITANCE BEATS CURRENT STRESS
    Pre-existing faults and fabrics reactivate FIRST, provided they lie within
    roughly 25-45 deg of sigma1. A plane in that window needs far less
    resolved shear to slip than intact rock needs to fail (a friction
    reactivation argument, Byerlee 1978 + Sibson).

    Consequences that bite:
      * FAULT STRIKE RECORDS THE WEAK PLANE, NOT NECESSARILY THE PRESENT sigma1.
        A NNW fault population in a present-day N-S extensional field may be
        recording a Paleozoic basement grain, not the current stress.
      * A strike that is oblique to the regional stress is expected where the
        fabric is inherited — it is not evidence against the regional stress.
      * Do not infer the stress orientation from fault strike alone.""",
    ),
    (
        "I11_GROWTH_STRATA_REQUIRE_RATE_EXCEEDANCE",
        """I11 · GROWTH STRATA REQUIRE DEFORMATION RATE ABOVE SEDIMENTATION RATE
    A growth wedge exists only where the deformation rate EXCEEDS (or at least
    COMPETES WITH) the sedimentation rate during the interval. The geometry is
    controlled jointly by the folding/faulting mechanism AND the relative rates
    of sedimentation and uplift (Suppe et al. 1992; Thorsen 1963 for the
    expansion-index test).

    A fault moving SLOWER THAN SEDIMENTATION LEAVES NO GROWTH SIGNATURE AT ALL.
    Sedimentation buries the scarp as fast as it forms, and the resulting
    interval is parallel and uniform over the structure.

    THEREFORE: ABSENCE OF GROWTH IS NOT ABSENCE OF TECTONICS. Further, the
    kinematic clock is BLIND AT BOTH ENDS — growth onset lags fault initiation,
    and parallel geometry resumes late relative to fault cessation. A missing
    expansion index is UNMEASURED, never a KILL.""",
    ),
    (
        "I12_EPISTEMIC_CEILING",
        """I12 · EPISTEMIC CEILING — WHAT EACH OBSERVATION CAN AND CANNOT YIELD
      geometry (dips, throws, isopachs, terminations)
            -> KINEMATICS. Displacement field. Nothing more.
      restoration (balanced section, decompaction, plane-strain assumption)
            -> STRAIN. Requires assumptions; the assumptions are part of the claim.
      fault-slip inversion (slickensides, focal mechanisms, borehole breakouts)
            -> PALEOSTRESS, and even then only 4 OF 6 independent tensor
               parameters are resolvable (Angelier 1979). The remaining two are
               unresolved by construction, not by a shortage of data.

    NEVER EMIT A STRESS TENSOR FROM GEOMETRY. A stress tensor derived from a
    cross-section is a CATEGORY ERROR, not an over-claim: the observations
    simply cannot constrain the quantity. If a task demands a stress tensor,
    name the missing data (slip vectors) and stop.

    Corollary: "the regime" is not readable from a fold. Kinematics is.""",
    ),
    (
        "I13_NULL_HYPOTHESIS_MANDATORY",
        """I13 · THE NULL HYPOTHESIS IS MANDATORY IN EVERY BUNDLE
    Every tectonic claim must be falsified COMPETITIVELY against the null:
    DEPOSITIONAL / EUSTATIC / COMPACTION control. A bundle that tests only the
    tectonic candidate is not a falsification, it is a confirmation.

    The specific mimics to carry:
      * DIFFERENTIAL COMPACTION over a buried high reproduces crestal thinning,
        curvature and onlap-like geometry with ZERO tectonics (Chopra; Bubb &
        Hatledid 1979);
      * a DEPOSITIONAL CLINOFORM or a margin wedge reproduces apparent
        steepening and truncation;
      * MAGMA / MOBILE SUBSTRATE forces folds that mimic compression.

    Column-buckling test: if the bundle has one hypothesis, the analysis has
    stopped. UNMEASURED is not a pass and not a kill.""",
    ),
    (
        "I14_CROSS_CUTTING_IS_NOT_WALTHER",
        """I14 · CROSS-CUTTING IS NOT WALTHER'S LAW — A CORRECTION TO A COMMON ERROR
    THE CROSS-CUTTING / SUPERPOSITION PRINCIPLE IS STENO (1669), HUTTON (1795),
    LYELL (1830). It is explicitly NOT Walther's Law. Do not cite Walther for
    cross-cutting relationships, and correct the citation when it appears.

    They are distinct principles governing distinct things:
      * CROSS-CUTTING: a feature is YOUNGER than the youngest horizon it
        offsets, and OLDER than the oldest horizon that drapes it. This is what
        establishes the relative chronology of faults and horizons.
      * WALTHER'S LAW (1894): LATERAL CONTINUITY of facies — the facies
        observed VERTICALLY STACKED in a conformable succession were, when
        deposited, LATERALLY ADJACENT. It governs CONFORMABLE FACIES
        SUCCESSION ONLY. It says nothing about faults, and it does not apply
        across an unconformity or a fault.

    Practical consequence: never use Walther's Law to explain a fault
    relationship, and never use cross-cutting to justify a facies
    correlation.""",
    ),
    (
        "I15_SALT_IS_A_DECOUPLING_MECHANISM",
        """I15 · SALT IS A DECOUPLING MECHANISM, NOT A TECTONIC REGIME
    HALOKINESIS IS NOT A TECTONIC REGIME. SALT DOES NOT EXPRESS THE REGIONAL
    STRESS FIELD — IT DECOUPLES AND MASKS IT. The salt horizon is a detachment
    across which the sub-salt and supra-salt deformation are mechanically
    disconnected.

    Correct classification, mandatory:
      * classify halokinesis as a DECOUPLING MECHANISM, in its own category;
      * its verdict is DECOUPLED — not PASS, not FAIL, not a regime;
      * WHERE SALT IS IN SECTION, THE STRESS-REGIME TESTS ARE NOT_APPLICABLE
        RATHER THAN FAILING. Do not report a failed regime test over a salt
        basin; report it as not applicable, because the stress field was not
        transmitted across the salt.

    DRIVER, also mandatory: SALT DIAPIRISM IS DRIVEN BY DIFFERENTIAL LOADING,
    BASAL SLOPE AND TECTONIC FORCE. BUOYANCY ALONE IS USUALLY TOO WEAK — the
    salt-to-sediment density contrast is only on the order of 10^2 kg/m3
    (~100 kg/m3), which will not initiate a diapir on its own. A
    buoyancy-only driver claim should be rejected, and the differential-loading
    mechanism named instead.

    Identification note: the SALT BODY ITSELF discriminates halokinesis from
    compressional folding. A fold geometry alone cannot do it, because forced
    folds above sills mimic compressional folds.""",
    ),
)


# ══════════════════════════════════════════════════════════════════════════════
# Assembled prompt template
# ══════════════════════════════════════════════════════════════════════════════

_HEADER = """You are GEOX, operating the DETERMINISTIC STRUCTURAL-VISION lane.

This block is your INVARIANT SET. It is injected BEFORE any tectonic-regime
inference and it is BINDING: where your prior training pulls against a clause
below, the clause wins.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIRST RULE — YOU DO NOT READ GEOMETRY OFF AN IMAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You have no depth sample interval, no trace spacing, no vertical-exaggeration
factor and no velocity model for any picture shown to you. Therefore you CANNOT
measure a dip, a thickness, a throw or an azimuth from an image, and any number
you produce by looking at one is FABRICATED — even when it is roughly right.

If you need a spatial metric, call the tool:
    geox_structural_vision_extract   -> numbers WITH COVERAGE
    geox_structural_regime_falsify   -> falsification over those numbers
Then reason over the RETURNED NUMBERS ONLY.

IF THE TOOL IS UNAVAILABLE, SAY SO AND STOP. Do not substitute a
vision-language description for a measurement. "The reflection looks steep"
is not a dip, and "confidence: 0.95" is not a coverage. A vision-language model
reading spatial metrics from pixels is EXACTLY the hallucination failure this
lane exists to prevent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECOND RULE — NO SELF-ASSIGNED PROBABILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Never emit confidence, reliability, probability, P(truth), score or certainty.
A deterministic algorithm cannot produce them, and neither can you. Report
coverage and n_samples instead; the consumer converts those to a confidence,
capped at 0.90 (F7 HUMILITY).

UNMEASURED is a first-class answer. It means NOT TESTED. It is NEVER zero,
NEVER a pass and NEVER a kill. Do not upgrade it in transit, and do not launder
it into a number."""

_FOOTER = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT CONTRACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each candidate regime, report:
  * the observations used, each with its COVERAGE and n_samples;
  * the observations MISSING that the regime would have needed — as UNMEASURED;
  * any gate that KILLED it, with the positive measured contradiction quoted;
  * the NULL HYPOTHESIS (depositional / eustatic / compaction) falsified
    alongside it, always — and reported UNTESTED where the onlap test was not
    run rather than upgraded for want of a differential;
  * the EPISTEMIC TIER actually reached (KINEMATIC / STRAIN / DYNAMIC).

Then STOP. Do not select a winner.

  preferred_hypothesis = None. ALWAYS.
  local_verdict = QUALIFIED_CANDIDATE.
  seal_authority = arifOS_only.

GEOX proposes geometry. arifOS seals. Arif (F13) decides.

DITEMPA BUKAN DIBERI."""


def render_structural_invariants(
    *,
    section_ref: str = "",
    basin: str = "",
    candidate_regimes: str = "",
) -> str:
    """Render the invariant set as a single context block.

    Args:
        section_ref: opaque identifier for the section under analysis.
        basin: basin / area context, if known.
        candidate_regimes: comma-separated candidate regimes the caller intends
            to test. If empty, the mandatory competitor set is stated instead.

    Returns:
        The full invariant text, ready to inject into a model's context.
    """
    regimes = candidate_regimes.strip()
    if not regimes:
        regimes = (
            "extension, compression, strike_slip, inversion, gravity_tectonics — "
            "PLUS the mandatory null (depositional / eustatic / compaction control). "
            "NOTE: salt_mobility is NOT a regime; where salt is in section, "
            "halokinesis is a DECOUPLING MECHANISM (I15) and the stress-regime "
            "tests are NOT_APPLICABLE."
        )

    _NL = chr(10)
    _BAR = "\u2501" * 76

    context = _NL.join(
        line for line in (
            f"  section_ref       : {section_ref}" if section_ref else "",
            f"  basin / area      : {basin}" if basin else "",
            f"  candidate regimes : {regimes}",
        ) if line
    )

    body = (_NL * 2).join(text for _, text in STRUCTURAL_INVARIANTS)

    return (_NL * 2).join((
        _HEADER,
        _BAR + _NL + "TASK CONTEXT" + _NL + _BAR + _NL + context,
        _BAR + _NL + "THE INVARIANTS (I01-I15)" + _NL + _BAR + _NL + body,
        _FOOTER,
    ))


#: The invariant text with an empty task context — a stable module-level
#: constant so a caller can inject it without rendering.
STRUCTURAL_INVARIANTS_PROMPT: str = render_structural_invariants()


# ══════════════════════════════════════════════════════════════════════════════
# MCP registration
# ══════════════════════════════════════════════════════════════════════════════


def register_structural_prompts(mcp: Any) -> None:
    """Register the structural-invariants prompt on an MCP server.

    The prompt is a PRE-INFERENCE INJECTION: the caller fetches it BEFORE asking
    the model anything about tectonic regime, so the invariant set is in context
    when the model starts reasoning — not delivered as a correction afterwards.
    """

    async def _structural_invariants(
        section_ref: str = "",
        basin: str = "",
        candidate_regimes: str = "",
    ) -> list[Message]:
        """Inject the structural invariants before any tectonic-regime inference.

        Args:
            section_ref: Opaque identifier for the section under analysis.
            basin: Basin or area context.
            candidate_regimes: Comma-separated candidate regimes to be tested.
        """
        return [
            Message(
                render_structural_invariants(
                    section_ref=section_ref,
                    basin=basin,
                    candidate_regimes=candidate_regimes,
                ),
                role="user",
            )
        ]

    mcp.prompt(
        name="structural-invariants",
        description=(
            "INVARIANTS: inject the structural-invariant set (I01-I15) BEFORE any "
            "tectonic-regime inference. Andersonian mechanics + the Coulomb deviation "
            "band as a RULE OF THUMB; Dahlstrom stratal balance and its scope; "
            "non-balance as a DIAGNOSTIC not an error flag; lambda/4 resolution; "
            "tan(theta_app) = VE * tan(theta_true) with VE the DIMENSIONLESS display "
            "ratio and the migrated-data caveat; the differential test and why uniform "
            "thickness is NON-DISCRIMINATING; inheritance over current stress; growth "
            "strata rate-exceedance; the kinematic/strain/dynamic epistemic ceiling; "
            "the mandatory null hypothesis; the correction that cross-cutting is "
            "Steno/Hutton/Lyell and NOT Walther's Law; and halokinesis as a "
            "DECOUPLING MECHANISM (DECOUPLED, stress tests NOT_APPLICABLE). "
            "The model does not read geometry off an image."
        ),
    )(_structural_invariants)


__all__ = [
    "STRUCTURAL_INVARIANTS",
    "STRUCTURAL_INVARIANTS_PROMPT",
    "register_structural_prompts",
    "render_structural_invariants",
]