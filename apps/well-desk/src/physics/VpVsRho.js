/**
 * VpVsRho.js — Forward Compute for Vp, Vs, Rho
 * =============================================
 * Browser-side forward rock physics calculator.
 * Wraps Gassmann.js for interactive parameter sweeps.
 */

class VpVsRho {
  constructor() {
    this.results = [];
  }

  /**
   * Single-point forward compute
   */
  compute(params) {
    const {
      porosity = 0.20,
      sw = 0.50,
      vsh = 0.20,
      fluidType = "brine",
      lithology = "sand_shale",
      pressureMpa = 25,
      tempC = 80
    } = params;

    const result = GASSMANN.forward(porosity, sw, vsh, fluidType, lithology);

    return {
      input: { porosity, sw, vsh, fluidType, pressureMpa, tempC },
      output: result,
      grade: this._grade(result),
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Parameter sweep: vary one parameter, hold others constant
   */
  sweep(baseParams, sweepParam, sweepRange) {
    this.results = [];
    for (const val of sweepRange) {
      const params = { ...baseParams, [sweepParam]: val };
      const result = this.compute(params);
      this.results.push({ sweepValue: val, ...result });
    }
    return this.results;
  }

  /**
   * Fluid substitution scan: brine -> oil -> gas at fixed por/Sw
   */
  fluidScan(porosity, sw, vsh = 0.20, lithology = "sand_shale") {
    const fluids = ["brine", "oil", "gas"];
    this.results = [];
    for (const fluid of fluids) {
      const result = this.compute({ porosity, sw, vsh, fluidType: fluid, lithology });
      this.results.push({ fluidType: fluid, ...result });
    }
    return this.results;
  }

  /**
   * PhysicsGuard grade assignment
   */
  _grade(result) {
    const { vp, vs, rho } = result;
    if (vp < 1500 || vp > 7000 || rho < 1.0 || rho > 3.5) return "PHYSICS_VIOLATION";
    if (vp >= 1500 && vp <= 6500 && vs >= 500 && vs <= 4000 && rho >= 1.8 && rho <= 2.95) {
      return "AAA";
    }
    return "AA";
  }

  /**
   * Export results as JSON
   */
  export() {
    return JSON.stringify(this.results, null, 2);
  }
}
