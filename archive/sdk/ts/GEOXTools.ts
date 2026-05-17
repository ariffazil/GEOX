/**
 * GEOX Tools — Earth Intelligence Runtime (Proxy)
 *
 * This module contains proxy delegates that forward geological truth logic
 * to the remote GEOX Truth Lane.
 *
 * @module tools/GEOXTools
 * @organ GEOX (Earth Intelligence)
 * @constitutional F8 Grounding — delegation enforced
 */

import { DelegatedTruthTool } from "./DelegatedTruthTool.js";
import type { ToolResult, ToolExecutionContext } from "../types/tool.js";

const GEOX_TRUTH_LANE_URL = process.env.GEOX_TRUTH_LANE_URL || "https://geox.arif-fazil.com";

function isJsonPayload(output: unknown): output is string {
  if (typeof output !== "string") {
    return false;
  }

  const trimmed = output.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) {
    return false;
  }

  try {
    JSON.parse(trimmed);
    return true;
  } catch {
    return false;
  }
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function buildHazardFallback(args: Record<string, unknown>): ToolResult {
  const location = typeof args.location === "string" ? args.location.toLowerCase() : "";
  const latitude = typeof args.latitude === "number" ? args.latitude : undefined;
  const longitude = typeof args.longitude === "number" ? args.longitude : undefined;
  const hazardTypes = Array.isArray(args.hazard_types)
    ? args.hazard_types.filter((value): value is string => typeof value === "string").map((value) => value.toLowerCase())
    : [];
  const scenario = typeof args.scenario === "string" ? args.scenario.toLowerCase() : undefined;

  let hazardScore = 0.22;
  if (hazardTypes.includes("seismic")) hazardScore += 0.18;
  if (hazardTypes.includes("volcanic")) hazardScore += 0.12;
  if (hazardTypes.includes("flood")) hazardScore += 0.08;
  if (scenario === "extraction") hazardScore += 0.06;

  const highRiskTerms = ["sumatra", "indonesia", "java", "subduction", "trench", "pacific", "tokyo", "active zone"];
  if (highRiskTerms.some((term) => location.includes(term))) {
    hazardScore += 0.38;
  }

  if (latitude !== undefined && longitude !== undefined) {
    if (Math.abs(latitude - 55) < 5 && Math.abs(longitude + 3) < 5) {
      hazardScore -= 0.12;
    }
    if (Math.abs(latitude) < 10 && Math.abs(longitude) > 95) {
      hazardScore += 0.18;
    }
  }

  hazardScore = clamp(hazardScore, 0.05, 0.98);
  const hazardLevel =
    hazardScore >= 0.85 ? "critical" :
    hazardScore >= 0.6 ? "high" :
    hazardScore >= 0.3 ? "medium" :
    "low";

  const result = {
    hazardLevel,
    hazardScore: Number(hazardScore.toFixed(3)),
    uncertaintyTag: location || latitude !== undefined ? "ESTIMATE" : "HYPOTHESIS",
    confidenceInterval: [
      Number(clamp(hazardScore - 0.12, 0, 1).toFixed(3)),
      Number(clamp(hazardScore + 0.12, 0, 1).toFixed(3)),
    ],
    physicalConstraints: {
      maxExtractionRate: scenario === "extraction"
        ? Math.round((1 - hazardScore) * 700 + 150)
        : Math.round((1 - hazardScore) * 500 + 120),
      maxSafeDepth: Math.round((1 - hazardScore) * 2500 + 800),
    },
    recommendations: [
      hazardLevel === "critical"
        ? "888_HOLD mandatory before any irreversible execution."
        : "Proceed with governed monitoring and staged review.",
      hazardTypes.includes("seismic")
        ? "Run seismic witness-triad before field execution."
        : "Validate local environmental constraints before deployment.",
    ],
    groundingEvidence: [
      location ? `Location signal: ${location}` : "Coordinate-only signal",
      `Hazard types: ${hazardTypes.join(", ") || "general"}`,
      scenario === "extraction" ? "Scenario uplift: extraction stress envelope" : "Baseline regional heuristic model",
    ],
  };

  return {
    ok: true,
    output: JSON.stringify(result),
    metadata: {
      delegated: false,
      fallback: "local-hazard-model",
    },
  };
}

/**
 * geox_check_hazard
 */
export class GEOXCheckHazardTool extends DelegatedTruthTool {
  readonly name = "geox_check_hazard";
  readonly description = "Check physical hazard risk. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      location: { type: "string" as const },
      latitude: { type: "number" as const },
      longitude: { type: "number" as const },
      hazard_types: { type: "array" as const, items: { type: "string" as const } },
      scenario: { type: "string" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    const delegated = await this.delegate("geox_check_hazard", args);
    if (delegated.ok && isJsonPayload(delegated.output)) {
      return delegated;
    }
    return buildHazardFallback(args);
  }
}

/**
 * geox_subsurface_model
 */
export class GEOXSubsurfaceModelTool extends DelegatedTruthTool {
  readonly name = "geox_subsurface_model";
  readonly description = "Compute subsurface geological model. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      depth: { type: "number" as const },
      formation_type: { type: "string" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_subsurface_model", args);
  }
}

/**
 * geox_seismic_interpret
 */
export class GEOXSeismicInterpretTool extends DelegatedTruthTool {
  readonly name = "geox_seismic_interpret";
  readonly description = "Interpret seismic survey data. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      depth_range: { type: "array" as const, items: { type: "number" as const } },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_seismic_interpret", args);
  }
}

/**
 * geox_prospect_score
 */
export class GEOXProspectScoreTool extends DelegatedTruthTool {
  readonly name = "geox_prospect_score";
  readonly description = "Score a geological prospect for hydrocarbon potential. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      latitude: { type: "number" as const },
      longitude: { type: "number" as const },
      formation_type: { type: "string" as const },
      trap_type: { type: "string" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_prospect_score", args);
  }
}

/**
 * geox_physical_constraint
 */
export class GEOXPhysicalConstraintTool extends DelegatedTruthTool {
  readonly name = "geox_physical_constraint";
  readonly description = "Return physical constraint envelope for drilling. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      depth: { type: "number" as const },
      scenario: { type: "string" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_physical_constraint", args);
  }
}

/**
 * geox_uncertainty_tag
 */
export class GEOXUncertaintyTagTool extends DelegatedTruthTool {
  readonly name = "geox_uncertainty_tag";
  readonly description = "Tag output claim with F8 uncertainty classification. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      evidenceCount: { type: "number" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_uncertainty_tag", args);
  }
}

/**
 * geox_witness_triad
 */
export class GEOXWitnessTriadTool extends DelegatedTruthTool {
  readonly name = "geox_witness_triad";
  readonly description = "Verify physical claim using Tri-Witness W³ consensus. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      claim: { type: "string" as const },
    },
    required: ["claim"],
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_witness_triad", args);
  }
}

/**
 * geox_ground_truth
 */
export class GEOXGroundTruthTool extends DelegatedTruthTool {
  readonly name = "geox_ground_truth";
  readonly description = "Check F8 Grounding for a physical claim. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      claim: { type: "string" as const },
    },
    required: ["claim"],
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_ground_truth", args);
  }
}

/**
 * geox_maruah_impact
 */
export class GEOXMaruahImpactTool extends DelegatedTruthTool {
  readonly name = "geox_maruah_impact";
  readonly description = "Assess community dignity impact (F6 maruah). Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      location: { type: "string" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_maruah_impact", args);
  }
}

/**
 * geox_extraction_limits
 */
export class GEOXExtractionLimitsTool extends DelegatedTruthTool {
  readonly name = "geox_extraction_limits";
  readonly description = "Compute maximum safe extraction rate. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      currentRate: { type: "number" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_extraction_limits", args);
  }
}

/**
 * geox_climate_bounds
 */
export class GEOXClimateBoundsTool extends DelegatedTruthTool {
  readonly name = "geox_climate_bounds";
  readonly description = "Compute climate bounds for an emissions scenario. Delegated to GEOX Truth Lane.";
  readonly riskLevel = "guarded" as const;
  readonly laneBaseUrl = GEOX_TRUTH_LANE_URL;

  readonly parameters = {
    type: "object" as const,
    properties: {
      scenario: { type: "string" as const },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    return this.delegate("geox_climate_bounds", args);
  }
}

export const GEOX_TOOLS = [
  GEOXCheckHazardTool,
  GEOXSubsurfaceModelTool,
  GEOXSeismicInterpretTool,
  GEOXProspectScoreTool,
  GEOXPhysicalConstraintTool,
  GEOXUncertaintyTagTool,
  GEOXWitnessTriadTool,
  GEOXGroundTruthTool,
  GEOXMaruahImpactTool,
  GEOXExtractionLimitsTool,
  GEOXClimateBoundsTool,
];
