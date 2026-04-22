/**
 * VshCalc.js — Shale Volume Calculator
 * =====================================
 * GR linear index and Larionov methods for Vsh computation.
 */

class VshCalc {
  /**
   * Linear GR index (simplest, most robust)
   * Vsh = (GR - GR_clean) / (GR_shale - GR_clean)
   */
  static linear(gr, grClean = 30, grShale = 130) {
    const vsh = (gr - grClean) / (grShale - grClean);
    return Math.max(0, Math.min(1, vsh));
  }

  /**
   * Larionov (1969) — Tertiary rocks
     * Vsh = 0.083 * (2^(3.7 * Igr) - 1)
   */
  static larionovTertiary(gr, grClean = 30, grShale = 130) {
    const igr = this.linear(gr, grClean, grShale);
    const vsh = 0.083 * (Math.pow(2, 3.7 * igr) - 1);
    return Math.max(0, Math.min(1, vsh));
  }

  /**
   * Larionov (1969) — older rocks
   */
  static larionovOlder(gr, grClean = 30, grShale = 130) {
    const igr = this.linear(gr, grClean, grShale);
    const vsh = 0.33 * (Math.pow(2, 2 * igr) - 1);
    return Math.max(0, Math.min(1, vsh));
  }

  /**
   * Steiber (1969)
   */
  static steiber(gr, grClean = 30, grShale = 130) {
    const igr = this.linear(gr, grClean, grShale);
    const vsh = igr / (3 - 2 * igr);
    return Math.max(0, Math.min(1, vsh));
  }

  /**
   * Clavier (1971)
   */
  static clavier(gr, grClean = 30, grShale = 130) {
    const igr = this.linear(gr, grClean, grShale);
    const vsh = 1.7 - Math.sqrt(3.38 - Math.pow(igr + 0.7, 2));
    return Math.max(0, Math.min(1, vsh));
  }

  /**
   * Compute Vsh curve from GR log array
   */
  static computeCurve(grArray, method = "linear", grClean = 30, grShale = 130) {
    const methods = {
      linear: this.linear,
      larionov_tertiary: this.larionovTertiary,
      larionov_older: this.larionovOlder,
      steiber: this.steiber,
      clavier: this.clavier
    };

    const fn = methods[method] || this.linear;
    return grArray.map(gr => fn(gr, grClean, grShale));
  }
}
