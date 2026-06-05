import type { GEOXScenarioContract } from "../types/arifos.js";

export function buildDefaultGEOXScenarios(mode: "primary" | "secondary"): GEOXScenarioContract[] {
  const primary = mode === "primary";

  return [
    {
      id: primary ? "geox-primary-estimate" : "geox-secondary-estimate",
      name: primary ? "Primary bounded estimate" : "Secondary bounded estimate",
      physicalConstraints: {
        maxExtractionRate: primary ? 650 : 500,
        seismicRiskIndex: primary ? 0.18 : 0.24,
        environmentalImpact: primary ? 0.22 : 0.3,
      },
      probability: primary ? 0.78 : 0.58,
      tag: "ESTIMATE",
      groundingEvidence: [
        "A-FORGE local fallback scenario",
        "No in-repo GEOX engine present",
      ],
    },
    {
      id: primary ? "geox-primary-hypothesis" : "geox-secondary-hypothesis",
      name: primary ? "Primary exploratory hypothesis" : "Secondary exploratory hypothesis",
      physicalConstraints: {
        maxExtractionRate: primary ? 720 : 560,
        seismicRiskIndex: primary ? 0.31 : 0.36,
        environmentalImpact: primary ? 0.42 : 0.47,
      },
      probability: primary ? 0.42 : 0.28,
      tag: "HYPOTHESIS",
      groundingEvidence: primary ? ["Fallback comparative envelope"] : [],
    },
  ];
}
