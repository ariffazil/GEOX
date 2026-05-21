# GEOX Petrophysics Report Template
# DITEMPA BUKAN DIBERI
#
# PURPOSE: Standardized output format for geologist's petrophysical interpretation.
#   This template structures the FINAL DELIVERABLE — the interpretation that
#   goes into the well report, the reserves submission, or the geocellular model.
#
#   A petrophysics report is a CHAIN OF REASONING, not just a table of numbers.
#   Every number must be traceable to a measurement, a calibration, or an assumption.
#
#   CLAIM LIMITS: Every assumption must be stated explicitly with uncertainty bounds.
#     "Porosity is estimated from density log with ±2 p.u. uncertainty at 1σ."
#     "Water saturation uses Archie with m=2.0, n=2.0 — calibrated to core."
#
#   PHYSICS-9 RULE: The report must make the GENETIC STORY coherent with the NUMBERS.
#     GR motif, cross-plot, and log-derived properties must all tell the same story.

# ─────────────────────────────────────────────────────────────────────────────
# REPORT HEADER
# ─────────────────────────────────────────────────────────────────────────────

report_metadata:
  well_name: "WELL-XXX"
  field: "FIELD NAME"
  basin: "BASIN NAME"
  country: "COUNTRY"
  report_date: "YYYY-MM-DD"
  interpreter: "NAME / COMPANY"
  report_type: "Final Interpretation / Quick-Look / Re-interpretation"
  data_version: "e.g., 2024-03-15 v2 (updated with new Core data)"
  confidence_level: "High / Medium / Low"

  well_metadata:
    operator: "Company name"
    spud_date: "YYYY-MM-DD"
    TD_md: "mMD / ftMD"
    TD_tvd: "mTVDSS / ftTVDSS"
    completion_date: "YYYY-MM-DD or Ongoing"
   KB_elevation: "m / ft"
    water_depth: "m / ft (if offshore)"
    formation_at_TD: "Formation name"

  data_available:
    wireline_logs: [list curves, e.g., "GR, RT, RHOB, NPHI, DT, CAL, SP"]
    LWD_logs: [list if available]
    core_data: [routine_core, SCAL, special_core — specify depths]
    fluid_samples: [DST, RCI, MDT — specify depths and pressures]
    pressure_surveys: [YES/NO — number of build-up tests]
    production_data: [if completed — initial rates, cumulative]

# ─────────────────────────────────────────────────────────────────────────────
# LOG QUALITY ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────

log_quality:
  description: "QC of raw log data before environmental correction"

  runs_and_repeats:
    run_1:
      date: "YYYY-MM-DD"
      tool_string: "Tool string description"
      depth_range_MD: [top, bottom]
      repeat_section: "Depth range (if any) — compare passes for quality"
    run_2:
      # If multiple runs

  environmental_conditions:
    borehole:
      hole_size_caliper: "inches — compare to bit size"
      washouts: "Depth ranges with CAL > nominal + 0.5 in"
      key_seats: "YES/NO — depth ranges"
      breakout_analysis: "YES/NO — if image log available"
    mud_system:
      type: "WBM / OBM / SBM — specify"
      mud_weight: "ppg or kg/m³"
      mud_resistivity_Rm: "ohm·m at surface and bottomhole temperature"
      mud_filtrate_Rmf: "ohm·m (at surface and BHT)"
      mud_filtrate_invasion: "diameter estimates from RT/RXO comparison"
    borehole_temperature:
      BHT: "°F or °C — from BHT survey"
      temperature_gradient: "°F/ft or °C/m — estimated from BHT and surface T"
      mud_temperature: "Calculate mud temperature at each log depth"

  data_quality_flags:
    - depth_range: "mD range"
      issue: "e.g., Cycle-skip in sonic, spikes in GR"
      severity: "High / Medium / Low"
      action_taken: "e.g., edited, excluded from interpretation"
    - # repeat for each problematic zone

  corrections_applied:
    caliper_corrected: YES/NO
    neutron_corrected: [borehole_size, mud_weight, temperature]
    density_corrected: [borehole_size, mud_filtrate]
    sonic_corrected: [borehole, compaction]
    resistivity_corrected: [invasion profile, borehole (if shallow)]
    SP_corrected: [bed_thickness, borehole_resistance]

# ─────────────────────────────────────────────────────────────────────────────
# PETROPHYSICAL PARAMETERS — SOURCE AND JUSTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

parameters:
  description: "All parameters used in the interpretation — state source and uncertainty"

  # Matrix and mineral properties
  mineral_properties:
    primary_lithology:
      mineral: "e.g., Quartz"
      density_matrix_rho_ma: "g/cm³"
      neutron_matrix_NPHI_ma: "v/v (limestone or sandstone unit)"
      sonic_transit_time_DT_ma: "μsec/ft"
      used_for: "e.g., Quartz sandstone interpretation"

    secondary_mineral:
      mineral: "e.g., Dolomite"
      density_matrix_rho_ma: "g/cm³"
      used_for: "Carbonate intervals"

    clay_mineral:
      type: "e.g., Illite / Smectite mixed layer"
      gamma_ray_clay_GR_cl: "API — from shale baseline"
      Vsh_equation_used: "e.g., Linear GR: Vsh = (GR - GR_clean) / (GR_shale - GR_clean)"
      density_clay_rho_cl: "g/cm³"
      neutron_clay_NPHI_cl: "v/v"
      sonic_clay_DT_cl: "μsec/ft"

  porosity_parameters:
    porosity_model: "Single mineral / dual mineral / neutron-density crossover"
    neutron_matrix: "LIMESTONE (default) or SANDSTONE — specify"
    density_porosity_equation: "PHId = (RHOB_ma - RHOB) / (RHOB_ma - RHOB_fluid)"
    fluid_density_RHOB_f: "1.00 g/cm³ (WBM filtrate) or 0.80 g/cm³ (OBM filtrate)"
    effective_vs_total_porosity: "Specify — usually effective (minus clay-bound water)"
    clay-bound_water_porosity_phi_cbv: "v/v — from core or estimated from GR-porosity cross-plot"
    porosity_cutoff_for_net_pay: "e.g., PHIE > 0.08 v/v (8 p.u.)"

  water_saturation_parameters:
    saturation_model: "Archie / Dual-Water / Simandoux / Waxman-Smits — specify"
    Archie_parameters:
      a_tortuosity: "value — e.g., 0.81 (from core calibration)"
      m_cementation: "value — e.g., 1.90 (from Pickett plot or core)"
      n_saturation: "value — e.g., 2.00 (from SCAL or assumed)"
      Rw_resistivity_of_water: "ohm·m — from SP or water sample"
      Rw_source: "e.g., SP calculation, water grab sample, deepest water-bearing zone"
      Rw_temperature: "°F — temperature at which Rw was measured"
      Rw_validity: "Assumption — verify Rw against water zone (Ro/Ra method)"
    dual_water_parameters:
      Rw_bulk: "ohm·m — bulk water resistivity (connate water)"
      Rw_clay: "ohm·m — clay-bound water resistivity (lower, more conductive)"
      B_cec_factor: "Cation exchange capacity factor — from cross-plot or core"
      Qv_meq_mL: "Clay exchange capacity per pore volume"
    saturation_cutoff_Sw: "e.g., Sw < 0.60 (60%) for pay — or height-dependent"
    Sw_height_function: "YES/NO — if capillary pressure data available"

  permeability_estimation:
    permeability_model: "Coates / Timur / K (φ-K) correlation / NMR / Core"
    Coates_equation: "k = (100 × φ^4.4 / Swc^2) or equivalent"
    Timur_equation: "k = (0.136 × φ^4.4 / Swc^2)"
    Swc_used_permeability: "fraction — irreducible water saturation (e.g., 0.25)"
    permeability_cutoff: "e.g., k > 1 mD for reservoir"
    NMR_T2_distribution: "Available YES/NO — if YES, T2 cutoff used for bound fluid"
    core_permeability_Klinkenberg: "Corrected to liquid permeability — state value"

  capillary_pressure_and_pay:
    height_above_FWL: "m or ft — measured from Free Water Level"
    FWL_determined_from: "e.g., Capillary pressure from core, log signature, water zone"
    Pc_height_model: "Brooks-Corey / J-function / Core-derived — specify"
    Pc_entry_pressure: "psi — from core or estimated from K"
    Sw_height_relationship: "Table or equation — e.g., Sw = Swc + (a / h)^b"
    transition_zone_thickness: "e.g., 10 m — from FWL to 100% mobile oil"
    net_pay_definition: "Zone where Sw < Sw_cutoff AND φ > φ_cutoff AND k > k_cutoff"

# ─────────────────────────────────────────────────────────────────────────────
# ZONE-BY-ZONE INTERPRETATION
# ─────────────────────────────────────────────────────────────────────────────

zone_interpretation:
  - zone_name: "ZONE A — Upper Sandakan Formation"
    depth_range:
      MD: [top, bottom]  # metersMD
      TVDSS: [top, bottom]  # metersTVDSS
    formation_age: "Late Miocene"
    depositional_environment: "Delta front — coarsening-upward motif"
    GR_motif: "Funnel (coarsening-upward), serrated at base"

    # Interval log values (average, range)
    log_averages:
      GR_API: [average, min, max]
      RT_ohm_m: [average, min, max]
      RHOB_g_cm3: [average, min, max]
      NPHI_vv: [average, min, max]
      PHIE_vv: [average, min, max]  # Effective porosity
      Vsh_vv: [average, min, max]
      Sw_vv: [average, min, max]
      permeability_mD: [average_geometric, min, max]

    # Net pay summary
    gross_thickness_m: "m"
    net_pay_m: "m"
    net_to_gross: "fraction"
    porosity_average: "v/v or %"
    Sw_average: "v/v or %"
    permeability_geometric_mean: "mD"
    hydrocarbon_saturation_Sh: "1 - Sw"

    # Pay flags
    pay_flags:
      phi_min: 0.08
      sw_max: 0.60
      k_min_mD: 1.0
      vsh_max: 0.45
      thickness_min_m: 0.5

    # Notable features
    observations:
      - "Thick amalgamated sand at base (blocky motif) — possible distributary channel"
      - "Porosity degradation at top due to quartz cement (see core)"
      - "Possible gas cap at crest — RT spikes, NPHI-RHOB separation"

    fluid_contact_indicators:
      GOC: "mTVDSS — indicated by RT increase and ND separation"
      OWC: "mTVDSS — indicated by GR shift and resistivity decrease"
      transition_zone: "m — from capillary pressure model"

    # Comparison with other data
    core_calibration: "Core at top 10 m — excellent agreement (φ diff < 1 p.u.)"
    test_data: "DST #2: 1500 BOPD + 5 MMSCFGD (gas cap)"
    pressure_data: "MDT at 2450 mTVDSS: 3850 psi (initial reservoir pressure)"

    confidence: "HIGH — good log quality, core calibration, test confirmation"

  - zone_name: "ZONE B — Labang Shale (Seal)"
    # (Repeat structure for each zone interpreted)

# ─────────────────────────────────────────────────────────────────────────────
# FLUID PROPERTIES SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

fluid_properties:
  oil:
    API_gravity: "e.g., 38° API"
    viscosity_surface: "cp"
    viscosity_reservoir: "cp at BHT"
    gas_oil_ratio_GOR: "SCF/STB"
    formation_volume_factor_Bo: "rb/STB"
    bubblepoint_pressure_Pb: "psi"
    oil_compressibility_Co: "1/psi"
    formation_density_rho_o: "g/cm³ at reservoir conditions"

  gas:
    gas_specific_gravity: "e.g., 0.65 (air = 1.0)"
    H2S_content: "ppm or %"
    CO2_content: "ppm or %"
    formation_volume_factor_Bg: "rb/SCF at reservoir conditions"
    gas_compressibility_Cg: "1/psi"
    gas_viscosity: "cp at reservoir conditions"

  water:
    resistivity_Rw: "ohm·m"
    salinity_TDS: "mg/L or ppm"
    formation_volume_factor_Bw: "rb/STB"
    water_compressibility_Cw: "1/psi"
    viscosity: "cp at reservoir conditions"

  pvt_summary_source: "e.g., PVT report from laboratory (DDT-2024-001) or correlation"

# ─────────────────────────────────────────────────────────────────────────────
# RESERVES ESTIMATE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

reserves_summary:
  # STOIIP (Stock Tank Oil Initially In Place)
  stoiip:
    gross_rock_volume: "m³ or acres-ft"
    porosity_average: "fraction"
    Sw_average: "fraction"
    formation_volume_factor_Bo: "rb/STB"
    stoiip_stock_tank_bbl: "bbl"
    uncertainty_range: "± X% (low, mid, high cases)"

  # Gas Initially In Place
  giip:
    gross_rock_volume: "m³ or acres-ft"
    porosity_average: "fraction"
    Sg_average: "fraction"
    formation_volume_factor_Bg: "rb/SCF"
    giip_bcf: "BCF"
    uncertainty_range: "± X%"

  # Recoverable (with recovery factor)
  recoverable:
    oil:
      recovery_factor: "e.g., 0.35 (35% — solution gas drive)"
      recoverable_bbl: "bbl"
      recovery_mechanism: "Solution gas drive / Waterflood / Gas cap drive"
    gas:
      recovery_factor: "e.g., 0.75"
      recoverable_bcf: "BCF"

  # Key uncertainties
  uncertainties:
    - parameter: "Porosity"
      range: "± 1 p.u."
      impact_on_STOIIP: "± 8%"
    - parameter: "Sw"
      range: "± 0.05"
      impact_on_STOIIP: "± 5%"
    - parameter: "Thickness"
      range: "± 10%"
      impact_on_STOIIP: "± 10%"
    - parameter: "Recovery factor"
      range: "± 0.05"
      impact_on_recoverable: "± 15%"

# ─────────────────────────────────────────────────────────────────────────────
# ASSUMPTIONS AND LIMITATIONS
# ─────────────────────────────────────────────────────────────────────────────

assumptions_and_limitations:
  critical_assumptions:
    - assumption: "Wettability is water-wet — Archie saturation model is valid"
      basis: "SCAL indicates water-wet (Amott test, USBM)"
      risk_if_wrong: "Sw may be overestimated in oil-wet zones"
    - assumption: "Rw = 0.12 ohm·m at formation temperature (75°F BHT)"
      basis: "SP calculation and deepest water-bearing zone"
      risk_if_wrong: "Sw proportional to 1/Rw — 10% error in Rw → 10% error in Sw"
    - assumption: "m = 2.0 (cementation exponent)"
      basis: "Pickett plot slope — no core calibration"
      risk_if_wrong: "±0.2 in m → ±10% error in Sw"
    - assumption: "No invasion effect on deep resistivity (Rt = Rxd)"
      basis: "RT/RXO ratio < 1.5 (mild invasion)"
      risk_if_wrong: "Minimal risk"

  data_quality_issues:
    - zone: "2100–2150 mMD"
      issue: "Cycle-skip in DT — sonic porosity unreliable"
      workaround: "Used density-neutron porosity only"
      impact: "Minor — thin interval"

  interpretation_limitations:
    - limitation: "No SCAL data for this field"
      workaround: "Used generalized Brooks-Corey Pc curve from analogue field"
      uncertainty: "±15–20% on Sw-height relationship"
    - limitation: "Single DST — no pressure transient analysis for kh"
      workaround: "Used log-derived permeability only"
      uncertainty: "±50% on permeability"

  recommendations:
    - "Acquire full diameter core through Zone A for SCAL calibration"
    - "Run NMR tool for bound fluid / free fluid distinction"
    - "Run MDT for in-situ fluid sampling and pressure survey"
    - "Acquire repeat formation tester (RFT) for pressure-depth profile"

# ─────────────────────────────────────────────────────────────────────────────
# CERTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

certification:
  interpreter_name: ""
  company: ""
  date: ""
  reviewer_name: ""
  reviewer_company: ""
  review_date: ""
  approval_signature: ""  # If applicable

  statement: |
    I certify that the interpretation presented in this report is based on
    the log and sample data available at the time of interpretation, using
    industry-standard methodologies and parameter values justified by
    available calibration data. All assumptions and uncertainties are
    explicitly stated as required by [Company] Petrophysics Guidelines [Version, Year].

  disclaimer: |
    This interpretation is a model of the subsurface based on indirect
    measurements. Actual fluid volumes and properties can only be determined
    by direct sampling (drill stem test, core, production). The uncertainty
    bounds stated in this report represent statistical estimates at 1σ confidence
    unless otherwise stated.
