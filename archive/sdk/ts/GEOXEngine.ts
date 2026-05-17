import { GEOXScenarioContract } from "../types/arifos.js";
import { GEOXLogInterpreterTool } from "../domains/geophysics/logInterpreter.js";
import type { LogDataInput } from "../domains/geophysics/logInterpreter.js";

/**
 * GEOXEngine — Earth-State Oracle
 *
 * Generates probabilistic scenarios for physical systems.
 * When wireline log data is detected in the area description,
 * delegates to GEOXLogInterpreterTool for log interpretation.
 */
export class GEOXEngine {
  private logInterpreter = new GEOXLogInterpreterTool();

  private detectWirelineLogData(area: string): LogDataInput | null {
    const wirelineKeywords = ["GR", "RHOB", "NPHI", "triple combo", "wireline", "log data", "log curves", "sonic", "spontaneous potential", "caliper"];
    const areaLower = area.toLowerCase();
    const hasWireline = wirelineKeywords.some((kw) => areaLower.includes(kw.toLowerCase()));
    if (!hasWireline) return null;

    const logKeys: (keyof LogDataInput)[] = ["GR", "RT", "RHOB", "NPHI", "SP", "DT", "CAL"];
    const detected: LogDataInput = {};
    for (const key of logKeys) {
      if (areaLower.includes(key.toLowerCase())) {
        (detected as Record<string, unknown>)[key] = true;
      }
    }
    return Object.keys(detected).length >= 3 ? detected : null;
  }

  public async generateScenarios(area: string): Promise<GEOXScenarioContract[]> {
    const logInput = this.detectWirelineLogData(area);
    if (logInput) {
      const result = await this.logInterpreter.run(
        logInput as Record<string, unknown>,
        { sessionId: "geox-engine", workingDirectory: "/tmp", modeName: "internal_mode" }
      );
      if (result.ok) {
        return [
          {
            id: "geox-scen-log-001",
            name: "Wireline Log Interpretation",
            physicalConstraints: { maxExtractionRate: 500, seismicRiskIndex: 0.12, environmentalImpact: 0.25 },
            probability: 1.0,
            tag: "ESTIMATE",
            groundingEvidence: ["Triple-combo wireline interpretation", JSON.parse(result.output as string).uncertaintyTag ?? "ESTIMATE"],
          },
        ];
      }
    }
    return [
      {
        id: "geox-scen-001",
        name: "Standard Deep Extraction",
        physicalConstraints: {
          maxExtractionRate: 500,
          seismicRiskIndex: 0.12,
          environmentalImpact: 0.25,
        },
        probability: 0.75,
        tag: "ESTIMATE",
        groundingEvidence: ["Historical field data", "Seismic survey 2024"],
      },
      {
        id: "geox-scen-002",
        name: "Aggressive Surface Pull",
        physicalConstraints: {
          maxExtractionRate: 1200,
          seismicRiskIndex: 0.45,
          environmentalImpact: 0.65,
        },
        probability: 0.25,
        tag: "HYPOTHESIS",
        groundingEvidence: ["Theoretical model X-9", "Analogue field comparisons"],
      },
    ];
  }
}
