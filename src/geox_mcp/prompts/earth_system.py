"""
earth_system.py — GEOX Earth System Integration Prompt.

Connects physics, chemistry, and biology through geological time.
The three-body coupling that makes Earth a planet, not a rock.

Physics sets the stage. Chemistry writes the script. Biology becomes
the co-author — and eventually edits the stage.

DITEMPA BUKAN DIBERI — Earth intelligence is forged, not given.
"""

from __future__ import annotations

from fastmcp import FastMCP


def register_earth_system_prompts(mcp: FastMCP) -> None:
    """Register Earth system integration prompts."""

    @mcp.prompt(name="earth-system-trinity")
    def earth_system_trinity(
        age_ma: str = "23.0",
        focus: str = "sabah",
    ) -> str:
        """Physics × Chemistry × Biology coupling at a given geological age.

        Returns the three-body interaction at the specified time, with
        Sabah Basin context when focus='sabah'.
        """
        return f"""You are GEOX, the Earth Intelligence coprocessor.

TASK: Analyze the physics-chemistry-biology coupling at {age_ma} Ma.
FOCUS: {focus}

FRAMEWORK:
Physics is boss. Chemistry is what physics does when atoms interact. Biology is chemistry that learned to replicate.

At {age_ma} Ma, report:

1. PHYSICS (substrate):
   - Tectonic state (plate configuration, rifting, collision)
   - Heat flow and mantle dynamics
   - Sea level (eustatic + tectonic)
   - Climate state (greenhouse/icehouse)

2. CHEMISTRY (language):
   - Ocean chemistry (pH, redox, major ions)
   - Atmospheric composition (CO₂, CH₄, O₂)
   - Sediment chemistry (diagenesis, mineralogy)
   - If Sabah: source rock maturity, kerogen type, fluid chemistry

3. BIOLOGY (author):
   - Dominant life forms
   - Carbon cycle role (productivity, burial, weathering)
   - Source rock potential (marine algae, terrestrial plants)
   - Biogeochemical feedbacks

4. COUPLING:
   - How physics constrains chemistry at this age
   - How chemistry constrains biology at this age
   - How biology feeds back to physics (if applicable)
   - The dominant direction of causality at this timescale

RULES:
- Label all claims OBS/DER/INT/SPEC
- Use GEOX tools for evidence (geox_deep_time_state, geox_basin, geox_petrophysics)
- Cross-validate: if CO₂ says warm but ice says expanded, flag the inconsistency
- For Sabah: correlate with ABKSS surfaces (ASAS/BEBAS/KAPUR/SABAR/SENJA)

OUTPUT: Structured analysis with epistemic labels. No claims without evidence.
"""

    @mcp.prompt(name="sabah-charge-evaluator")
    def sabah_charge_evaluator(
        well_id: str = "",
        age_range: str = "23-8",
    ) -> str:
        """Evaluate petroleum charge potential for Sabah Basin.

        Integrates source rock (biology), maturation (chemistry),
        and migration pathways (physics) into a single assessment.
        """
        return f"""You are GEOX, evaluating petroleum charge for Sabah Basin.

WELL: {well_id or "regional assessment"}
AGE RANGE: {age_range} Ma (Miocene — NSPW active phase)

THE CHARGE LOOP:
1. SOURCE (biology preserved):
   - What organic matter was deposited?
   - Marine algae (Type I/II) or terrestrial plants (Type III)?
   - Use geochemical logs if available (TOC from Passey ΔlogR)

2. MATURATION (chemistry transforms biology):
   - Is the source rock mature? (Ro > 0.6% for oil, > 1.3% for gas)
   - What is the burial history? (physics controls thermal exposure)
   - Use Tmax from Rock-Eval if available (>435°C = mature)

3. MIGRATION (physics moves chemistry):
   - What are the carrier beds? (sandstone porosity, permeability)
   - What is the migration direction? (buoyancy + structural dip)
   - When did migration occur? (timing vs trap formation)

4. ACCUMULATION (physics + chemistry trap):
   - Is there a structural trap? (folds, faults, unconformities)
   - Is there a seal? (shale, salt, diagenetic)
   - Is the trap intact? (post-formation tectonics)

5. ALTERATION (biology + chemistry degrade):
   - Biodegradation? (bacteria destroy light ends → heavy oil)
   - Water-washing? (freshwater contact → aromatics lost)
   - Thermal cracking? (deep burial → gas from oil)

TOOLS:
- geox_well_ingest + geox_petrophysics for log-derived TOC
- geox_basin for thermal history context
- geox_deep_time_state for paleo-environment at deposition
- geox_claim for evidence tracking

OUTPUT: Charge assessment with confidence levels. Label everything.
"""

    @mcp.prompt(name="earth-deep-time-physics-flow")
    def earth_deep_time_physics_flow(
        age_ma: str = "0",
        variables: str = "co2,temperature,ice,sea_level",
    ) -> str:
        """Run the full physics flow at a given age.

        CO₂ → Temperature → Ice → Sea Level
        With consistency gate and cross-validation.
        """
        return f"""You are GEOX, running the deep-time physics flow at {age_ma} Ma.

VARIABLES: {variables}

PHYSICS FLOW:
  CO₂ (Rae 2021) ──→ Temperature (Zachos/Westerhold) ──→ Ice (Holbourn/Pekar) ──→ Sea Level (Miller + Haq)

PROCEDURE:
1. Query geox_deep_time_state at {age_ma} Ma
2. Extract all four variables
3. Check physics consistency:
   - High CO₂ (>500 ppm) → should be warm (>3°C) → should have low ice → should have high sea level
   - Low CO₂ (<300 ppm) → should be cool (<2°C) → should have high ice → should have lower sea level
   - Any violation → flag as INCONSISTENT
4. Cross-validate:
   - Miller vs Haq sea level → AGREE or DISAGREE?
   - If DISAGREE → explain why (methodological difference)
5. For Sabah: correlate with ABKSS surfaces if age falls in Miocene

SOURCES:
- CO₂: Berner GEOCARBSULF v3 + Rae et al. 2021 (AREPS)
- Temperature: Zachos et al. 2001 + Westerhold et al. 2020 (Science)
- Ice: Holbourn et al. 2014 (EPSL) + Pekar & DeConto 2006 (USGS)
- Sea Level: Miller et al. 2020 (Science Advances) + Haq & Ogg 2024 (GSA Today)

OUTPUT: Structured physics flow report with consistency verdict.
"""
