/**
 * GEOX_log_interpreter — Triple-Combo Log Interpretation Tool
 *
 * Core implementation of the anomalous contrast decoding protocol.
 * Takes triple-combo log data (GR, RT, RHOB, NPHI, SP, DT, CAL) and
 * computes: Vsh, PHIE, SW, fluid type, lithology, and anomaly quality.
 *
 * Theory: Anomalous Contrast = delta(physical_property) from background.
 * Every geological feature manifests as contrast in ≥2 independent properties.
 * No single-curve anomaly is sufficient — cross-plot confirmation mandatory.
 *
 * @module domains/geophysics/logInterpreter
 * @organ GEOX
 * @pipeline 333_MIND
 */

import { BaseTool } from "../../tools/base.js";
import type { ToolResult, ToolExecutionContext } from "../../types/tool.js";

export interface LogDataInput {
  GR?: number[];
  RT?: number[];
  RHOB?: number[];
  NPHI?: number[];
  SP?: number[];
  DT?: number[];
  CAL?: number[];
  depth?: number[];
  GR_clean?: number;
  GR_shale?: number;
  RW?: number;
  RT_bg?: number;
  RHOB_matrix?: number;
  fluid_density?: number;
}

export interface AnomalyResult {
  Vsh?: number[];
  PHIE?: number[];
  SW?: number[];
  BVW?: number[];
  anomalyScore?: number[];
  fluidFlag?: Array<"WATER" | "GAS" | "OIL" | "INDETERMINATE">;
  lithology?: string[];
  quality?: Array<"GOOD" | "FAIR" | "POOR">;
  anomalyContrast?: {
    kappa_GR: number;
    kappa_RHOB: number;
    kappa_NPHI: number;
    kappa_RT: number;
    compositeAnomaly: number;
  };
  uncertaintyTag: "ESTIMATE" | "HYPOTHESIS" | "UNKNOWN";
  reasoning: string[];
  recommendations: string[];
}

const MATRIX_DENSITY: Record<string, number> = {
  sandstone: 2.65,
  limestone: 2.71,
  dolomite: 2.87,
  anhydrite: 2.98,
  gypsum: 2.31,
  halite: 2.16,
  coal: 1.35,
};
const FLUID_DENSITY_WATER = 1.0;
const FLUID_DENSITY_GAS = 0.7;
const ARCHIE_N = 2;
const ARCHIE_M = 2;

function median(values: number[]): number {
  const sorted = [...values].filter((v) => v > 0 && isFinite(v)).sort((a, b) => a - b);
  if (sorted.length === 0) return 0;
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function stdDev(values: number[]): number {
  const m = median(values);
  const squaredDiffs = values.map((v) => (v - m) ** 2);
  return Math.sqrt(median(squaredDiffs));
}

export class GEOXLogInterpreterTool extends BaseTool {
  readonly name = "GEOX_log_interpreter";
  readonly description = "Interpret triple-combo wireline logs (GR, RT, RHOB, NPHI, SP, DT, CAL) to compute Vsh, PHIE, SW, fluid type, and lithology using anomalous contrast theory. All outputs tagged ESTIMATE/HYPOTHESIS/UNKNOWN per F8.";
  readonly riskLevel = "guarded" as const;

  readonly parameters = {
    type: "object" as const,
    properties: {
      GR: { type: "array" as const, items: { type: "number" as const }, description: "Gamma Ray API values" },
      RT: { type: "array" as const, items: { type: "number" as const }, description: "Deep resistivity ohm-m" },
      RHOB: { type: "array" as const, items: { type: "number" as const }, description: "Bulk density g/cc" },
      NPHI: { type: "array" as const, items: { type: "number" as const }, description: "Neutron porosity fraction" },
      SP: { type: "array" as const, items: { type: "number" as const }, description: "Spontaneous potential mV" },
      DT: { type: "array" as const, items: { type: "number" as const }, description: "Sonic transit time us/ft" },
      CAL: { type: "array" as const, items: { type: "number" as const }, description: "Caliper inches" },
      depth: { type: "array" as const, items: { type: "number" as const }, description: "Depth values matching log arrays" },
      GR_clean: { type: "number" as const, description: "GR for clean sand (baseline)" },
      GR_shale: { type: "number" as const, description: "GR for shale (100% Vsh baseline)" },
      RW: { type: "number" as const, description: "Formation water resistivity ohm-m" },
      matrix: { type: "string" as const, description: "Matrix type for PHIE computation", default: "limestone" },
    },
    additionalProperties: false,
  };

  async run(args: Record<string, unknown>, _context: ToolExecutionContext): Promise<ToolResult> {
    const GR = (args.GR as number[]) ?? [];
    const RT = (args.RT as number[]) ?? [];
    const RHOB = (args.RHOB as number[]) ?? [];
    const NPHI = (args.NPHI as number[]) ?? [];
    const SP = (args.SP as number[]) ?? [];
    const DT = (args.DT as number[]) ?? [];
    const CAL = (args.CAL as number[]) ?? [];
    const matrix = (args.matrix as string) ?? "limestone";

    const RW = (args.RW as number) ?? 0.055;
    const GR_clean = (args.GR_clean as number) ?? 20;
    const GR_shale = (args.GR_shale as number) ?? 120;

    if (GR.length === 0 || RHOB.length === 0 || NPHI.length === 0) {
      return { ok: false, output: "Minimum required logs: GR, RHOB, NPHI" };
    }

    const n = Math.min(GR.length, RHOB.length, NPHI.length);

    // ─── Step 1: Establish background (shale baseline) ─────────────────────
    const GR_clean_val = GR_clean;
    const GR_shale_val = GR_shale;

    // Find shale zone: top GR values (high GR = shale)
    const GR_sorted = [...GR].sort((a, b) => b - a);
    const GR_p33 = GR_sorted[Math.floor(GR_sorted.length * 0.33)] ?? GR_shale_val;
    const GR_p67 = GR_sorted[Math.floor(GR_sorted.length * 0.67)] ?? GR_shale_val;
    const RHOB_shale_bg = median(RHOB.slice(0, Math.floor(n * 0.3)));
    const NPHI_shale_bg = median(NPHI.slice(0, Math.floor(n * 0.3)));
    const RT_bg = (args.RT as number[])?.length ? median((args.RT as number[]).slice(0, Math.floor(n * 0.3))) : 10;

    const RHOB_matrix = MATRIX_DENSITY[matrix] ?? 2.71;
    const fluidDensity = FLUID_DENSITY_WATER;

    // ─── Step 2: Vsh from GR ─────────────────────────────────────────────────
    const Vsh = GR.map((g) => {
      if (g <= GR_clean_val) return 0;
      if (g >= GR_shale_val) return 1;
      return (g - GR_clean_val) / (GR_shale_val - GR_clean_val);
    });

    // ─── Step 3: PHIE from RHOB-NPHI cross-plot (density-neutron method) ─────
    const PHIE = RHOB.map((rho, i) => {
      if (rho <= 0 || rho >= RHOB_matrix) return 0;
      const phi_total = (RHOB_matrix - rho) / (RHOB_matrix - fluidDensity);
      const nphi_val = NPHI[i] ?? 0;
      // Neutron-density crossover for gas detection
      const crossover = nphi_val - phi_total;
      // Effective porosity corrected for shale
      const phi_eff = Math.max(0, phi_total * (1 - Vsh[i] * 0.7));
      return Math.min(0.45, Math.max(0, phi_eff));
    });

    // ─── Step 4: SW via Archie ───────────────────────────────────────────────
    const SW = RT.map((rt, i) => {
      const phi_e = PHIE[i];
      if (phi_e < 0.01 || rt <= 0) return 1;
      const sw = Math.pow(RW / rt, 1 / ARCHIE_N) * Math.pow(phi_e, -ARCHIE_M / ARCHIE_N);
      return Math.min(1, Math.max(0, sw));
    });

    // ─── Step 5: BVW ────────────────────────────────────────────────────────
    const BVW = PHIE.map((p, i) => p * SW[i]);

    // ─── Step 6: Anomalous contrast computation ─────────────────────────────
    const GR_std = stdDev(GR);
    const RHOB_std = stdDev(RHOB);
    const NPHI_std = stdDev(NPHI);
    const RT_log_avg = Math.log10(RT_bg);

    const anomalyScore = GR.map((_, i) => {
      const dGR = Math.abs(GR[i] - GR_shale_val) / Math.max(GR_std, 1);
      const dRHOB = Math.abs(RHOB[i] - RHOB_shale_bg) / Math.max(RHOB_std, 0.05);
      const dNPHI = Math.abs(NPHI[i] - NPHI_shale_bg) / Math.max(NPHI_std, 0.02);
      const dRT = Math.abs(Math.log10(Math.max(RT[i], 0.1)) - RT_log_avg);
      const A = 0.2 * dGR + 0.3 * dRHOB + 0.3 * dNPHI + 0.2 * dRT;
      return Math.round(A * 100) / 100;
    });

    const kappa_GR = stdDev(GR) > 0 ? stdDev(GR) / median(GR) : 0;
    const kappa_RHOB = stdDev(RHOB) / median(RHOB);
    const kappa_NPHI = stdDev(NPHI) / Math.max(median(NPHI), 0.01);
    const kappa_RT = Math.abs(Math.log10(Math.max(...RT.filter((r) => r > 0), 1)) - Math.log10(Math.min(...RT.filter((r) => r > 0), 100))) / 2;
    const compositeAnomaly = (kappa_GR * 0.2 + kappa_RHOB * 0.3 + kappa_NPHI * 0.3 + kappa_RT * 0.2);

    // ─── Step 7: Fluid type flagging ─────────────────────────────────────────
    const fluidFlag: AnomalyResult["fluidFlag"] = PHIE.map((p, i) => {
      if (p < 0.02) return "INDETERMINATE";
      const dRHOB = RHOB[i] - RHOB_shale_bg;
      const dNPHI = NPHI[i] - NPHI_shale_bg;
      const dRT = Math.log10(RT[i] / RT_bg);
      const crossover = NPHI[i] - ((RHOB_matrix - RHOB[i]) / (RHOB_matrix - fluidDensity));
      if (crossover > 0.05 && dRT > 0.5 && dRHOB < -0.05) return "GAS";
      if (SW[i] < 0.6 && RT[i] > RT_bg * 3 && dRHOB > 0.05) return "OIL";
      if (SW[i] > 0.8) return "WATER";
      return "INDETERMINATE";
    });

    // ─── Step 8: Lithology ────────────────────────────────────────────────────
    const lithology: string[] = Vsh.map((v, i) => {
      const rho = RHOB[i];
      const nphi = NPHI[i];
      const phi = PHIE[i];
      if (v > 0.7) return "SHALE";
      if (rho > 2.85 && nphi < 0.05) return "ANHYDRITE";
      if (rho > 2.75 && nphi < 0.1 && v < 0.15) return "DENSE_LIMESTONE";
      if (rho < 1.8 && nphi > 0.3 && v < 0.1) return "COAL";
      if (rho < 2.5 && nphi > phi && v < 0.2) return "POROUS_SAND";
      if (rho < 2.65 && v < 0.2 && phi > 0.15) return "SANDSTONE";
      if (rho > 2.78 && rho < 2.9 && nphi > 0.08) return "DOLOMITE";
      return "LIMESTONE";
    });

    // ─── Step 9: Quality ─────────────────────────────────────────────────────
    const quality: AnomalyResult["quality"] = anomalyScore.map((A) => {
      if (A > 1.5) return "GOOD";
      if (A > 0.5) return "FAIR";
      return "POOR";
    });

    const uncertaintyTag: AnomalyResult["uncertaintyTag"] =
      compositeAnomaly > 0.3 ? "ESTIMATE" : compositeAnomaly > 0.1 ? "HYPOTHESIS" : "UNKNOWN";

    const reasoning: string[] = [
      `Background: GR_shale={GR_shale_val}, RHOB_shale={RHOB_shale_bg.toFixed(2)}, NPHI_shale={NPHI_shale_bg.toFixed(2)}, RT_shale={RT_bg.toFixed(2)}`,
      `Matrix: ${matrix} (RHOB_matrix=${RHOB_matrix})`,
      `Computed Vsh range: ${Math.min(...Vsh).toFixed(2)}-${Math.max(...Vsh).toFixed(2)}`,
      `Computed PHIE range: ${Math.min(...PHIE).toFixed(3)}-${Math.max(...PHIE).toFixed(3)}`,
      `Computed SW range: ${Math.min(...SW).toFixed(2)}-${Math.max(...SW).toFixed(2)}`,
      `Anomalous contrast: A=${compositeAnomaly.toFixed(3)} (κGR=${kappa_GR.toFixed(2)}, κRHOB=${kappa_RHOB.toFixed(2)}, κNPHI=${kappa_NPHI.toFixed(2)}, κRT=${kappa_RT.toFixed(2)})`,
      `Gas flags: ${fluidFlag.filter((f) => f === "GAS").length}, Oil: ${fluidFlag.filter((f) => f === "OIL").length}, Water: ${fluidFlag.filter((f) => f === "WATER").length}`,
      `Uncertainty: ${uncertaintyTag}`,
    ];

    const recommendations: string[] = [];
    if (fluidFlag.filter((f) => f === "GAS").length > 0) {
      recommendations.push("GAS DETECTED: Apply gas correction PHIE_gas = PHIE * 0.85 (Raymer-Hunt)");
      recommendations.push("Confirm with resistivity elevation (RT > 3x background)");
    }
    if (compositeAnomaly > 1.5) {
      recommendations.push("STRONG ANOMALY: Proceed to quantitative interpretation — cross-plot confirmation recommended");
    } else if (compositeAnomaly < 0.5) {
      recommendations.push("WEAK ANOMALY: Use GEOX_witness_triad for W³ consensus before committing");
      recommendations.push("888_HOLD if lithology ambiguous");
    }

    const result: AnomalyResult = {
      Vsh: Vsh.map((v) => Math.round(v * 1000) / 1000),
      PHIE: PHIE.map((p) => Math.round(p * 1000) / 1000),
      SW: SW.map((s) => Math.round(s * 1000) / 1000),
      BVW: BVW.map((b) => Math.round(b * 1000) / 1000),
      anomalyScore: anomalyScore.map((A) => Math.round(A * 100) / 100),
      fluidFlag,
      lithology,
      quality,
      anomalyContrast: {
        kappa_GR: Math.round(kappa_GR * 100) / 100,
        kappa_RHOB: Math.round(kappa_RHOB * 100) / 100,
        kappa_NPHI: Math.round(kappa_NPHI * 100) / 100,
        kappa_RT: Math.round(kappa_RT * 100) / 100,
        compositeAnomaly: Math.round(compositeAnomaly * 1000) / 1000,
      },
      uncertaintyTag,
      reasoning,
      recommendations,
    };

    return { ok: true, output: JSON.stringify(result, null, 2) };
  }
}
