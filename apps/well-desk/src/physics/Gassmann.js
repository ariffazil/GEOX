/**
 * Gassmann.js — Fluid Substitution Engine (Browser-Side)
 * =======================================================
 * Client-side Gassmann fluid substitution for interactive modeling.
 * Mirrors Python rock_physics_engine.py for consistency.
 */

const GASSMANN = {
  // Mineral catalog (Mavko et al.)
  minerals: {
    quartz:   { k: 36.6, g: 45.0, rho: 2.650 },
    calcite:  { k: 76.8, g: 32.0, rho: 2.710 },
    dolomite: { k: 94.9, g: 45.0, rho: 2.870 },
    clay:     { k: 20.9, g: 6.85, rho: 2.550 }
  },

  fluids: {
    brine: { k: 2.50, rho: 1.024 },
    oil:   { k: 1.50, rho: 0.850 },
    gas:   { k: 0.02, rho: 0.100 }
  },

  /**
   * Voigt-Reuss-Hill average
   */
  vrh(f1, k1, k2) {
    const f2 = 1 - f1;
    const kVoigt = f1 * k1 + f2 * k2;
    const kReuss = 1 / (f1 / k1 + f2 / k2);
    return 0.5 * (kVoigt + kReuss);
  },

  /**
   * Mineral mix from vsh and lithology
   */
  mineralMix(vsh, lithology = "sand_shale") {
    const vshC = Math.max(0, Math.min(1, vsh));
    const vq = 1 - vshC;
    const m = this.minerals;

    if (lithology === "lime_shale") {
      return {
        k: this.vrh(vshC, m.clay.k, m.calcite.k),
        g: this.vrh(vshC, m.clay.g, m.calcite.g),
        rho: vshC * m.clay.rho + vq * m.calcite.rho
      };
    }
    if (lithology === "dolomite_shale") {
      return {
        k: this.vrh(vshC, m.clay.k, m.dolomite.k),
        g: this.vrh(vshC, m.clay.g, m.dolomite.g),
        rho: vshC * m.clay.rho + vq * m.dolomite.rho
      };
    }
    // Default: sand-shale
    return {
      k: this.vrh(vshC, m.clay.k, m.quartz.k),
      g: this.vrh(vshC, m.clay.g, m.quartz.g),
      rho: vshC * m.clay.rho + vq * m.quartz.rho
    };
  },

  /**
   * Fluid mix from Sw and hydrocarbon type
   */
  fluidMix(sw, fluidType = "brine") {
    const swC = Math.max(0, Math.min(1, sw));
    const hcSat = 1 - swC;
    const f = this.fluids;
    const hc = f[fluidType] || f.brine;

    if (swC >= 1) return { k: f.brine.k, rho: f.brine.rho };
    if (hcSat >= 1) return { k: hc.k, rho: hc.rho };

    const kFl = 1 / (swC / f.brine.k + hcSat / hc.k);
    const rhoFl = swC * f.brine.rho + hcSat * hc.rho;
    return { k: kFl, rho: rhoFl };
  },

  /**
   * Gassmann substitution: dry frame + fluid -> saturated
   */
  substitute(kDry, gDry, kMin, kFl, phi) {
    const phiC = Math.max(0.001, Math.min(phi, 0.50));
    const num = phiC * kDry - (1 + phiC) * kFl * kDry / kMin + kFl;
    const den = (1 - phiC) * kFl + phiC * kMin - kFl * kDry / kMin;
    const kSat = den > 0 ? num / den : kDry;
    return { kSat: Math.max(0, kSat), gSat: gDry };
  },

  /**
   * Velocities from moduli (k, g in GPa, rho in g/cm3 -> m/s)
   */
  velocities(kSat, gSat, rhoSat) {
    const rhoKgM3 = rhoSat * 1000;
    const kPa = kSat * 1e9;
    const gPa = gSat * 1e9;
    const vp = Math.sqrt((kPa + 4 * gPa / 3) / rhoKgM3);
    const vs = gPa > 0 ? Math.sqrt(gPa / rhoKgM3) : 0;
    return {
      vp: Math.round(vp * 100) / 100,
      vs: Math.round(vs * 100) / 100,
      rho: Math.round(rhoSat * 1000) / 1000,
      ai: Math.round(rhoSat * vp) / 1000,
      vpVs: vs > 0 ? Math.round((vp / vs) * 1000) / 1000 : 0
    };
  },

  /**
   * Full forward compute: por, sw, vsh, fluid -> Vp, Vs, rho, AI
   */
  forward(porosity, sw, vsh, fluidType, lithology = "sand_shale") {
    const phi = Math.max(0, Math.min(0.50, porosity));
    const matrix = this.mineralMix(vsh, lithology);
    const fluid = this.fluidMix(sw, fluidType);

    // Approximate dry frame (simplified for client-side)
    const kDry = Math.max(0.1, matrix.k * (1 - phi) * 0.7);
    const gDry = Math.max(0.1, matrix.g * (1 - phi) * 0.7);

    const sat = this.substitute(kDry, gDry, matrix.k, fluid.k, phi);
    const rhoSat = (1 - phi) * matrix.rho + phi * fluid.rho;

    return this.velocities(sat.kSat, sat.gSat, rhoSat);
  }
};
