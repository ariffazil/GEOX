/**
 * SwArchie.js — Archie Water Saturation Calculator
 * =================================================
 * Archie (1942) equation and variations for Sw computation.
 */

class SwArchie {
  /**
   * Archie equation
   * Sw^n = (a * Rw) / (phi^m * Rt)
   *
   * @param rt — formation resistivity (ohm-m)
   * @param phi — porosity (fraction)
   * @param rw — formation water resistivity (ohm-m)
   * @param a — tortuosity factor (default 0.62 for Humble)
   * @param m — cementation exponent (default 2.0)
   * @param n — saturation exponent (default 2.0)
   */
  static archie(rt, phi, rw, a = 0.62, m = 2.0, n = 2.0) {
    if (phi <= 0 || rt <= 0 || rw <= 0) return 1.0;
    const sw = Math.pow((a * rw) / (Math.pow(phi, m) * rt), 1 / n);
    return Math.max(0, Math.min(1, sw));
  }

  /**
   * Indonesian equation (Poupon & Leveaux, 1971)
   * For shaly sands with low Rw
   */
  static indonesian(rt, phi, rw, vsh, rsh, a = 1.0, m = 2.0, n = 2.0) {
    if (phi <= 0 || rt <= 0 || rw <= 0) return 1.0;
    const term1 = Math.pow(vsh, (1 - vsh) / 2) / Math.sqrt(rsh);
    const term2 = Math.pow(phi, m / 2) / Math.sqrt(a * rw);
    const sw = Math.pow((term1 + term2) ** 2 * rt, -1 / n);
    return Math.max(0, Math.min(1, sw));
  }

  /**
   * Simandoux (1963)
   * For shaly sands
   */
  static simandoux(rt, phi, rw, vsh, rsh, a = 1.0, m = 2.0, n = 2.0) {
    if (phi <= 0 || rt <= 0 || rw <= 0) return 1.0;
    const c = (1 - vsh) * a * rw / Math.pow(phi, m);
    const d = c * vsh / (2 * rsh);
    const sw = Math.pow(c / rt + d * d, 0.5) - d;
    return Math.max(0, Math.min(1, sw));
  }

  /**
   * Waxman-Smits (1968)
   * For sands with clay-bound water (requires Qv)
   */
  static waxmanSmits(rt, phi, rw, qv, b = 0.1, a = 1.0, m = 2.0, n = 2.0) {
    if (phi <= 0 || rt <= 0 || rw <= 0) return 1.0;
    const rwStar = 1 / (1 / rw + b * qv);
    const sw = Math.pow((a * rwStar) / (Math.pow(phi, m) * rt), 1 / n);
    return Math.max(0, Math.min(1, sw));
  }

  /**
   * Compute Sw curve from log arrays
   */
  static computeCurve(rtArray, phiArray, rw, vshArray = null, method = "archie", rsh = 4.0) {
    return rtArray.map((rt, i) => {
      const phi = phiArray[i];
      if (vshArray && vshArray[i] > 0.1 && method !== "archie") {
        return this.indonesian(rt, phi, rw, vshArray[i], rsh);
      }
      return this.archie(rt, phi, rw);
    });
  }
}
