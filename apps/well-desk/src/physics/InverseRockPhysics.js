/**
 * InverseRockPhysics.js — Iterative Inversion (Browser-Side)
 * ===========================================================
 * Gradient-free inverse rock physics for client-side estimation.
 * Uses Nelder-Mead simplex (amoeba) — no scipy dependency.
 */

class InverseRockPhysics {
  constructor() {
    this.maxIter = 200;
    this.tolerance = 1e-6;
  }

  /**
   * Invert observed Vp, Vs, rho to estimate porosity, Sw, vsh, fluid
   */
  invert(observed, prior = {}) {
    const { vp: vpObs, vs: vsObs, rho: rhoObs } = observed;
    const {
      porosity: priorPor = 0.20,
      sw: priorSw = 0.50,
      vsh: priorVsh = 0.20
    } = prior;

    // Nelder-Mead simplex in 3D: [porosity, sw, vsh]
    let simplex = [
      { x: [priorPor, priorSw, priorVsh], f: 0 },
      { x: [priorPor * 1.1, priorSw, priorVsh], f: 0 },
      { x: [priorPor, priorSw * 1.1, priorVsh], f: 0 },
      { x: [priorPor, priorSw, priorVsh * 1.1], f: 0 }
    ];

    // Evaluate initial simplex
    for (const vertex of simplex) {
      vertex.f = this._misfit(vertex.x, vpObs, vsObs, rhoObs);
    }

    // Iterate
    for (let iter = 0; iter < this.maxIter; iter++) {
      // Sort by misfit (best first)
      simplex.sort((a, b) => a.f - b.f);

      // Check convergence
      if (simplex[0].f < this.tolerance) break;
      const spread = simplex[simplex.length - 1].f - simplex[0].f;
      if (spread < this.tolerance * 10) break;

      // Centroid of best vertices
      const centroid = [0, 0, 0];
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          centroid[j] += simplex[i].x[j];
        }
      }
      for (let j = 0; j < 3; j++) centroid[j] /= 3;

      // Reflection
      const worst = simplex[3];
      const reflected = this._reflect(centroid, worst.x);
      const reflectedF = this._misfit(reflected, vpObs, vsObs, rhoObs);

      if (reflectedF < simplex[0].f) {
        // Expansion
        const expanded = this._expand(centroid, reflected);
        const expandedF = this._misfit(expanded, vpObs, vsObs, rhoObs);
        simplex[3] = { x: expandedF < reflectedF ? expanded : reflected, f: Math.min(expandedF, reflectedF) };
      } else if (reflectedF < simplex[2].f) {
        simplex[3] = { x: reflected, f: reflectedF };
      } else {
        // Contraction
        const contracted = this._contract(centroid, worst.x);
        const contractedF = this._misfit(contracted, vpObs, vsObs, rhoObs);
        if (contractedF < worst.f) {
          simplex[3] = { x: contracted, f: contractedF };
        } else {
          // Shrink
          for (let i = 1; i < 4; i++) {
            simplex[i].x = this._shrink(simplex[0].x, simplex[i].x);
            simplex[i].f = this._misfit(simplex[i].x, vpObs, vsObs, rhoObs);
          }
        }
      }
    }

    // Best estimate
    const best = simplex[0];
    const [estPor, estSw, estVsh] = best.x.map(v => Math.max(0, Math.min(1, v)));

    // Determine fluid type from misfit with different fluids
    const fluidMisfits = [
      { fluid: "brine", f: this._misfitWithFluid(best.x, vpObs, vsObs, rhoObs, "brine") },
      { fluid: "oil", f: this._misfitWithFluid(best.x, vpObs, vsObs, rhoObs, "oil") },
      { fluid: "gas", f: this._misfitWithFluid(best.x, vpObs, vsObs, rhoObs, "gas") }
    ];
    fluidMisfits.sort((a, b) => a.f - b.f);
    const estFluid = fluidMisfits[0].fluid;

    // Integrity score
    const integrityScore = 1 / (1 + best.f);

    return {
      estimated: {
        porosity: Math.round(estPor * 1000) / 1000,
        sw: Math.round(estSw * 1000) / 1000,
        vsh: Math.round(estVsh * 1000) / 1000,
        fluidType: estFluid
      },
      uncertainty: {
        porosity: Math.round(Math.abs(estPor - priorPor) * 0.5 * 1000) / 1000 + 0.02,
        sw: Math.round(Math.abs(estSw - priorSw) * 0.3 * 1000) / 1000 + 0.05,
        fluidConfidence: best.f < 0.01 ? "high" : best.f < 0.05 ? "medium" : "low"
      },
      integrityScore: Math.round(integrityScore * 10000) / 10000,
      misfit: Math.round(best.f * 100000) / 100000,
      iterations: iter,
      grade: this._gradeResult(estPor, estSw)
    };
  }

  // ── Nelder-Mead helpers ───────────────────────────────────────────────────

  _misfit(x, vpObs, vsObs, rhoObs) {
    // Default to brine for simplex evolution
    return this._misfitWithFluid(x, vpObs, vsObs, rhoObs, "brine");
  }

  _misfitWithFluid(x, vpObs, vsObs, rhoObs, fluidType) {
    const [por, sw, vsh] = x.map(v => Math.max(0, Math.min(1, v)));
    try {
      const fwd = GASSMANN.forward(por, sw, vsh, fluidType);
      const dVp = ((fwd.vp - vpObs) / Math.max(vpObs, 1)) ** 2;
      const dVs = vsObs > 0 ? ((fwd.vs - vsObs) / Math.max(vsObs, 1)) ** 2 : 0;
      const dRho = ((fwd.rho - rhoObs) / Math.max(rhoObs, 0.1)) ** 2;
      return dVp + dVs + dRho;
    } catch (e) {
      return 1e6;
    }
  }

  _reflect(centroid, worst) {
    const alpha = 1;
    return centroid.map((c, i) => Math.max(0, Math.min(1, c + alpha * (c - worst[i]))));
  }

  _expand(centroid, reflected) {
    const gamma = 2;
    return centroid.map((c, i) => Math.max(0, Math.min(1, c + gamma * (reflected[i] - c))));
  }

  _contract(centroid, worst) {
    const rho = 0.5;
    return centroid.map((c, i) => Math.max(0, Math.min(1, c + rho * (worst[i] - c))));
  }

  _shrink(best, point) {
    const sigma = 0.5;
    return best.map((b, i) => b + sigma * (point[i] - b));
  }

  _gradeResult(por, sw) {
    if (por < 0 || por > 0.50 || sw < 0 || sw > 1) return "PHYSICS_VIOLATION";
    if (por > 0.45) return "RAW";
    return "AAA";
  }
}
