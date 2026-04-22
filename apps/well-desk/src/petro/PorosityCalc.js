/**
 * PorosityCalc.js — Porosity Calculator
 * ======================================
 * Density porosity, neutron-density crossplot, and sonic porosity.
 */

class PorosityCalc {
  // Matrix densities (g/cm3)
  static RHO_MATRIX = {
    sandstone: 2.650,
    limestone: 2.710,
    dolomite: 2.870
  };

  static FLUID_DENSITY = 1.0;  // Fresh water

  /**
   * Density porosity
   * phi_d = (rho_matrix - rho_bulk) / (rho_matrix - rho_fluid)
   */
  static densityPorosity(rhob, matrixType = "sandstone") {
    const rhoMatrix = this.RHO_MATRIX[matrixType] || this.RHO_MATRIX.sandstone;
    const phi = (rhoMatrix - rhob) / (rhoMatrix - this.FLUID_DENSITY);
    return Math.max(0, Math.min(0.50, phi));
  }

  /**
   * Neutron porosity (returns input — NPHI is already porosity units)
   */
  static neutronPorosity(nphi) {
    return Math.max(0, Math.min(0.50, nphi));
  }

  /**
   * Neutron-Density crossplot porosity
   * Averages the two, with gas correction when NPHI < phi_d
   */
  static ndCrossplotPorosity(nphi, rhob, matrixType = "sandstone") {
    const phiD = this.densityPorosity(rhob, matrixType);
    const phiN = this.neutronPorosity(nphi);

    // Gas correction: when NPHI < phi_d (gas crossover), use density as upper bound
    if (phiN < phiD - 0.03) {
      // Gas-bearing: use closer to density porosity
      return phiD * 0.7 + phiN * 0.3;
    }

    // Shale correction: when NPHI > phi_d, average both
    return (phiD + phiN) / 2;
  }

  /**
   * Sonic (Wyllie) porosity
   * phi_s = (dt_log - dt_matrix) / (dt_fluid - dt_matrix)
   */
  static sonicPorosity(dt, dtMatrix = 55.5, dtFluid = 189) {
    const phi = (dt - dtMatrix) / (dtFluid - dtMatrix);
    return Math.max(0, Math.min(0.50, phi));
  }

  /**
   * Effective porosity: total porosity minus bound water in shale
   */
  static effectivePorosity(phiTotal, vsh, phiShale = 0.12) {
    return Math.max(0, phiTotal - vsh * phiShale);
  }

  /**
   * Compute porosity curves from log arrays
   */
  static computeCurves(rhobArray, nphiArray, dtArray, vshArray, matrixType = "sandstone") {
    const n = rhobArray.length;
    const phiD = rhobArray.map(rhob => this.densityPorosity(rhob, matrixType));
    const phiN = nphiArray.map(nphi => this.neutronPorosity(nphi));
    const phiS = dtArray.map(dt => this.sonicPorosity(dt));
    const phiX = phiD.map((pd, i) => this.ndCrossplotPorosity(phiN[i], rhobArray[i], matrixType));
    const phiE = phiX.map((px, i) => this.effectivePorosity(px, vshArray[i] || 0));

    return { phiD, phiN, phiS, phiX, phiE };
  }
}
