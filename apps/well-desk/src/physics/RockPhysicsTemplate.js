/**
 * RockPhysicsTemplate.js — Material Catalog
 * ==========================================
 * Rock physics templates for common lithology-fluid combinations.
 * Pre-computed reference points for QC and validation.
 */

const ROCK_PHYSICS_TEMPLATES = {
  // Clastic suite
  clean_sand_brine: {
    lithology: "sand_shale", vsh: 0.05, porosity: 0.25, sw: 1.0, fluid: "brine",
    expected: { vp: 3800, vs: 2100, rho: 2.35, ai: 8930 }
  },
  clean_sand_oil: {
    lithology: "sand_shale", vsh: 0.05, porosity: 0.25, sw: 0.20, fluid: "oil",
    expected: { vp: 3400, vs: 2100, rho: 2.25, ai: 7650 }
  },
  clean_sand_gas: {
    lithology: "sand_shale", vsh: 0.05, porosity: 0.25, sw: 0.10, fluid: "gas",
    expected: { vp: 2800, vs: 2050, rho: 2.05, ai: 5740 }
  },
  shaly_sand_brine: {
    lithology: "sand_shale", vsh: 0.30, porosity: 0.18, sw: 1.0, fluid: "brine",
    expected: { vp: 3600, vs: 1800, rho: 2.45, ai: 8820 }
  },
  shaly_sand_oil: {
    lithology: "sand_shale", vsh: 0.30, porosity: 0.18, sw: 0.25, fluid: "oil",
    expected: { vp: 3300, vs: 1800, rho: 2.38, ai: 7854 }
  },
  shale: {
    lithology: "sand_shale", vsh: 0.85, porosity: 0.12, sw: 1.0, fluid: "brine",
    expected: { vp: 3200, vs: 1400, rho: 2.55, ai: 8160 }
  },

  // Carbonate suite
  limestone: {
    lithology: "lime_shale", vsh: 0.05, porosity: 0.10, sw: 1.0, fluid: "brine",
    expected: { vp: 5500, vs: 2800, rho: 2.60, ai: 14300 }
  },
  limestone_gas: {
    lithology: "lime_shale", vsh: 0.05, porosity: 0.10, sw: 0.15, fluid: "gas",
    expected: { vp: 4800, vs: 2750, rho: 2.50, ai: 12000 }
  },
  dolomite: {
    lithology: "dolomite_shale", vsh: 0.05, porosity: 0.08, sw: 1.0, fluid: "brine",
    expected: { vp: 6200, vs: 3200, rho: 2.75, ai: 17050 }
  },

  // Scaffold fixtures
  bek_2: {
    lithology: "sand_shale", vsh: 0.12, porosity: 0.22, sw: 0.35, fluid: "brine",
    expected: { vp: 3700, vs: 2000, rho: 2.38, ai: 8806 }
  },
  dul_a1: {
    lithology: "sand_shale", vsh: 0.25, porosity: 0.18, sw: 0.42, fluid: "oil",
    expected: { vp: 3400, vs: 1800, rho: 2.40, ai: 8160 }
  }
};

/**
 * Template matcher: find closest template to computed values
 */
function matchTemplate(computed) {
  let bestMatch = null;
  let bestScore = Infinity;

  for (const [name, tmpl] of Object.entries(ROCK_PHYSICS_TEMPLATES)) {
    const dVp = ((computed.vp - tmpl.expected.vp) / tmpl.expected.vp) ** 2;
    const dVs = ((computed.vs - tmpl.expected.vs) / tmpl.expected.vs) ** 2;
    const dRho = ((computed.rho - tmpl.expected.rho) / tmpl.expected.rho) ** 2;
    const score = dVp + dVs + dRho;

    if (score < bestScore) {
      bestScore = score;
      bestMatch = { name, template: tmpl, score: Math.round(score * 10000) / 10000 };
    }
  }

  return {
    ...bestMatch,
    confidence: bestScore < 0.01 ? "high" : bestScore < 0.05 ? "medium" : "low"
  };
}
