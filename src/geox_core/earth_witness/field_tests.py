"""
GEOX Earth Witness — Field Test Vocabulary and Discriminator Rules
═══════════════════════════════════════════════════════════════════════════
Authority: ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1
Canon: F1-F13 Constitutional Discipline · Invariant I5 (INPUT_REQUIRED)

Field tests are physical discriminators that ELIMINATE competing hypotheses.
They NEVER provide a single synthetic score that "proves" a rock identity.
A camera cannot test acid effervescence, hardness, magnetism, or scratch behaviour.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

# ── Field Test Literal Enums ────────────────────────────────────────────────

HclEffervescence = Literal[
    "vigorous",         # Immediate vigorous effervescence -> Calcite / Limestone
    "weak_on_powder",   # Effervescence only when scratched to powder -> Dolomite / Dolostone
    "none",             # No reaction -> Clastic (Quartz), Shale, Chert, Igneous
    "not_tested",
]

MohsHardnessCategory = Literal[
    "lt_fingernail",    # < 2.5 (e.g. Gypsum, Talc, Halite, soft claystone)
    "lt_copper",        # 2.5 - 3.5 (e.g. Calcite)
    "lt_steel",         # 3.5 - 5.5 (e.g. Dolomite, Fluorite, Apatite)
    "gt_steel",         # > 5.5 (e.g. Quartz, Chert, Feldspar, Pyrite)
    "not_tested",
]

StreakColor = Literal[
    "white",
    "grey_black",
    "red_brown",        # Hematite
    "yellow_brown",     # Limonite / Goethite
    "greenish_black",
    "not_tested",
]

MagnetismResponse = Literal[
    "strongly_magnetic",# Magnetite
    "weakly_magnetic",  # Ilmenite, Pyrrhotite
    "non_magnetic",
    "not_tested",
]

GrainSizeClass = Literal[
    "clay_silt",            # < 0.0625 mm
    "fine_sand",            # 0.0625 - 0.25 mm
    "medium_sand",          # 0.25 - 0.5 mm
    "coarse_sand",          # 0.5 - 2.0 mm
    "gravel_conglomerate",  # > 2.0 mm
    "crystalline_aphanitic",
    "crystalline_phaneritic",
    "not_tested",
]

LustreType = Literal[
    "metallic",
    "submetallic",
    "vitreous",
    "dull_earthy",
    "pearly",
    "silky",
    "not_tested",
]

CleavageFracture = Literal[
    "perfect_rhombohedral", # Calcite / Dolomite
    "cubic",                # Halite / Galena
    "basal_sheet",          # Mica
    "prismatic",            # Feldspar / Amphibole
    "none_conchoidal",      # Quartz / Chert / Obsidian
    "not_tested",
]

FizzOnScratch = Literal[
    "yes_dolomite_behaviour",
    "no",
    "not_tested",
]


class FieldTestInput(BaseModel):
    """Field sensory and physical test inputs provided by human geologist or field tool."""
    hcl: HclEffervescence = "not_tested"
    hardness: MohsHardnessCategory = "not_tested"
    streak: StreakColor = "not_tested"
    magnetism: MagnetismResponse = "not_tested"
    grain_size: GrainSizeClass = "not_tested"
    lustre: LustreType = "not_tested"
    cleavage: CleavageFracture = "not_tested"
    fizz_on_scratch: FizzOnScratch = "not_tested"


class DiscriminatorReport(BaseModel):
    """Output from evaluating physical field tests against candidate hypotheses."""
    tests_applied: list[str] = Field(default_factory=list)
    eliminated_hypotheses: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of {hypothesis, reason_eliminated}",
    )
    surviving_hypotheses: list[str] = Field(default_factory=list)
    remaining_ambiguities: list[str] = Field(default_factory=list)
    required_next_tests: list[str] = Field(default_factory=list)


def evaluate_field_discriminators(
    candidate_hypotheses: list[str],
    field_tests: FieldTestInput,
) -> DiscriminatorReport:
    """Eliminates hypotheses that contradict physical field test results.

    Rule: Never compute a single subjective score that 'proves' a rock.
    Apply negative falsification (Popperian): eliminate what is physically impossible.
    """
    tests_applied: list[str] = []
    eliminated: list[dict[str, str]] = []
    candidates = set(candidate_hypotheses)

    # 1. HCl Effervescence Rules
    if field_tests.hcl != "not_tested":
        tests_applied.append(f"HCl: {field_tests.hcl}")
        if field_tests.hcl == "vigorous":
            # Calcite reacts vigorously; pure quartz, shale, basalt, and dolostone do not
            for c in list(candidates):
                c_lower = c.lower()
                if any(k in c_lower for k in ["quartzite", "chert", "basalt", "sandstone", "shale", "dolostone", "granite"]):
                    if "calcareous" not in c_lower:
                        eliminated.append({
                            "hypothesis": c,
                            "reason_eliminated": "Vigorous HCl effervescence contradicts non-calcareous or pure dolomite lithologies",
                        })
                        candidates.discard(c)
        elif field_tests.hcl == "weak_on_powder":
            for c in list(candidates):
                c_lower = c.lower()
                if "limestone" in c_lower and "dolomitic" not in c_lower:
                    eliminated.append({
                        "hypothesis": c,
                        "reason_eliminated": "Effervescence only on powder indicates dolomite, not pure calcite/limestone",
                    })
                    candidates.discard(c)
        elif field_tests.hcl == "none":
            for c in list(candidates):
                c_lower = c.lower()
                if any(k in c_lower for k in ["limestone", "chalk", "calcite", "marble"]):
                    eliminated.append({
                        "hypothesis": c,
                        "reason_eliminated": "Complete absence of HCl reaction eliminates carbonate lithologies",
                    })
                    candidates.discard(c)

    # 2. Hardness Rules
    if field_tests.hardness != "not_tested":
        tests_applied.append(f"Hardness: {field_tests.hardness}")
        if field_tests.hardness == "gt_steel":
            # Hardness > 5.5: Calcite (3) and Dolomite (3.5-4) are eliminated
            for c in list(candidates):
                c_lower = c.lower()
                if any(k in c_lower for k in ["limestone", "dolostone", "chalk", "halite", "gypsum"]):
                    eliminated.append({
                        "hypothesis": c,
                        "reason_eliminated": "Hardness > steel (> 5.5) eliminates soft carbonate/evaporite minerals",
                    })
                    candidates.discard(c)
        elif field_tests.hardness in ["lt_fingernail", "lt_copper"]:
            # Hardness < 3.5: Quartz and Chert (Mohs 7) are eliminated
            for c in list(candidates):
                c_lower = c.lower()
                if any(k in c_lower for k in ["quartzite", "chert", "granite", "basalt"]):
                    eliminated.append({
                        "hypothesis": c,
                        "reason_eliminated": f"Hardness {field_tests.hardness} eliminates silicate minerals (Mohs 6-7)",
                    })
                    candidates.discard(c)

    # 3. Magnetism Rules
    if field_tests.magnetism != "not_tested":
        tests_applied.append(f"Magnetism: {field_tests.magnetism}")
        if field_tests.magnetism == "strongly_magnetic":
            for c in list(candidates):
                c_lower = c.lower()
                if any(k in c_lower for k in ["limestone", "sandstone", "chert", "pure_shale"]):
                    eliminated.append({
                        "hypothesis": c,
                        "reason_eliminated": "Strong magnetism indicates significant magnetite/ferromagnetic minerals",
                    })
                    candidates.discard(c)

    # 4. Cleavage / Fracture Rules
    if field_tests.cleavage != "not_tested":
        tests_applied.append(f"Cleavage: {field_tests.cleavage}")
        if field_tests.cleavage == "none_conchoidal":
            for c in list(candidates):
                c_lower = c.lower()
                if any(k in c_lower for k in ["calcite_cleavage", "feldspar", "mica_schist"]):
                    eliminated.append({
                        "hypothesis": c,
                        "reason_eliminated": "Conchoidal fracture contradicts minerals with perfect cleavage planes",
                    })
                    candidates.discard(c)

    remaining_ambiguities: list[str] = []
    required_next_tests: list[str] = []

    surviving = sorted(list(candidates))
    if len(surviving) > 1:
        remaining_ambiguities.append(f"Remaining ambiguous hypotheses: {', '.join(surviving)}")
        if field_tests.hcl == "not_tested":
            required_next_tests.append("10% dilute HCl acid effervescence test")
        if field_tests.hardness == "not_tested":
            required_next_tests.append("Mohs scratch hardness test (knife / glass)")
        if field_tests.grain_size == "not_tested":
            required_next_tests.append("Hand-lens grain size & sorting estimate (Wentworth scale)")

    return DiscriminatorReport(
        tests_applied=tests_applied,
        eliminated_hypotheses=eliminated,
        surviving_hypotheses=surviving,
        remaining_ambiguities=remaining_ambiguities,
        required_next_tests=required_next_tests,
    )
