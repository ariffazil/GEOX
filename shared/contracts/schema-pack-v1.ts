import { z } from 'zod';

/**
 * GEOX Contract Pack v1 — Sovereign Witness Schemas
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 */

// ═══════════════════════════════════════════════════════════════════════════════
// Dimensions & App Contracts
// ═════════════════════════════════════════════════════════════════

export const DimensionEnum = z.enum([
  'PROSPECT',  // Basin/Play scale, ranking, economics
  'WELL',      // Borehole scale, logs, markers, petrophysics
  'SECTION',   // 2D interpretation on Seismic/Transects
  'EARTH_3D',  // Volumetric interpretation, attributes, surfaces
  'TIME_4D',   // 4D seismic, production dynamics, reservoir history
  'PHYSICS',   // Governance, thermodynamic audit, constitutional reality
  'MAP',       // Transversal: Geospatial reference, CRS, navigation
]);

export type Dimension = z.infer<typeof DimensionEnum>;

export const VerdictEnum = z.enum([
  "SEAL",     // ≥ 0.80 Confidence, auto-proceed
  "PARTIAL",  // ≥ 0.50 Confidence, caveats apply
  "SABAR",    // ≥ 0.25 Confidence, hold for data
  "VOID",     // < 0.25 Confidence, blocked
  "888_HOLD"  // Sovereign override / high-risk pause
]);
export type VerdictCode = z.infer<typeof VerdictEnum>;

export const AppDomainEnum = z.enum([
  'seismic',
  'petrophysics',
  'geology',
  'economics',
  'governance',
  'general',
]);

// ═══════════════════════════════════════════════════════════════════════════════
// Foundational Primitives
// ═══════════════════════════════════════════════════════════════════════════════

export const UnitRefSchema = z.object({
  name: z.string(),   // e.g. "millisecond"
  symbol: z.string(), // e.g. "ms"
  quantity: z.string() // e.g. "time", "length"
});

export const XYPointSchema = z.object({
  x: z.number(),
  y: z.number(),
});

export const XYZPointSchema = z.object({
  x: z.number(),
  y: z.number(),
  z: z.number(),
});

export const BoundingBoxSchema = z.object({
  min: XYZPointSchema.optional(), // Older version used min_x, newer uses min: XYZPoint
  max: XYZPointSchema.optional(),
  min_x: z.number().optional(),
  max_x: z.number().optional(),
  min_y: z.number().optional(),
  max_y: z.number().optional(),
  min_z: z.number().optional(),
  max_z: z.number().optional(),
  unit: z.string().default("m"),
  crs: z.string().optional(),
});

// ═══════════════════════════════════════════════════════════════════════════════
// GeoContext — Spatial Laws
// ═══════════════════════════════════════════════════════════════════════════════

export const GeoContextSchema = z.object({
  crsName: z.string().optional(),
  crsEpsg: z.number().int().positive().optional(),
  verticalDomain: z.enum(['twt_ms', 'tvdss_m', 'md_m', 'tvd_m']).optional(),
  isTimeDomain: z.boolean().optional(),
  units: z.object({
    horizontal: UnitRefSchema,
    vertical: UnitRefSchema,
  }).optional(),
  // Taxonomy additions
  dimension: DimensionEnum.optional(),
  crs: z.string().default("WGS84"),
  epoch: z.string().optional(),
  precision_level: z.number().min(0).max(1).default(1.0),
  is_simulated: z.boolean().default(false)
});

// ═══════════════════════════════════════════════════════════════════════════════
// Physics9 — The Orthogonal Stack
// ═══════════════════════════════════════════════════════════════════════════════

export const Physics9Schema = z.object({
  density: z.number().describe("ρ (kg/m³)"),
  vp: z.number().describe("Vp (m/s)"),
  vs: z.number().describe("Vs (m/s)"),
  resistivity: z.number().describe("ρₑ (Ω·m)"),
  susceptibility: z.number().describe("χ (SI)"),
  thermal_conductivity: z.number().describe("k (W/m·K)"),
  pore_pressure: z.number().describe("P (Pa)"),
  temperature: z.number().describe("T (K)"),
  porosity: z.number().min(0).max(1).describe("φ (0-1)")
});
export type Physics9 = z.infer<typeof Physics9Schema>;

// ═══════════════════════════════════════════════════════════════════════════════
// Evidence — Observation References
// ═══════════════════════════════════════════════════════════════════════════════

export const EvidenceRefSchema = z.object({
  id: z.string(),
  kind: z.enum(['well', 'seismic', 'map', 'log', 'top', 'verdict', 'MANIFOLD', 'TRUTH', 'CLAIM', 'TEXTURE']),
  sourceUri: z.string().optional(),
  source_path: z.string().optional(),
  timestamp: z.string().datetime().optional(),
  version: z.string().optional(),
  owner: z.string().optional(),
  hash: z.string().optional(),
  name: z.string().optional(),
});

export const EvidenceObjectSchema = z.object({
  ref: EvidenceRefSchema,
  context: GeoContextSchema,
  payload: z.any(),
  metadata: z.record(z.string(), z.any()).optional(),
});

// ═══════════════════════════════════════════════════════════════════════════════
// Transform — Spatial Movements
// ═══════════════════════════════════════════════════════════════════════════════

export const TransformRequestSchema = z.object({
  requestId: z.string().optional(),
  request_id: z.string().uuid().optional(),
  sourceContext: GeoContextSchema.optional(),
  targetContext: GeoContextSchema.optional(),
  context: GeoContextSchema.optional(),
  dataToTransform: z.array(XYZPointSchema).optional(),
  sources: z.array(EvidenceRefSchema).optional(),
  method: z.string().default('bilinear'),
  operator: z.string().optional(),
  parameters: z.record(z.string(), z.any()).default({}),
  priority: z.number().default(5)
});

export const TransformResultSchema = z.object({
  requestId: z.string().optional(),
  request_id: z.string().uuid().optional(),
  transformedData: z.array(XYZPointSchema).optional(),
  errorRms: z.number().optional(),
  status: z.enum(['SUCCESS', 'PARTIAL', 'FAILED']).optional(),
  verdict: VerdictEnum.optional(),
  confidence: z.number().min(0).max(1).optional(),
  outputs: z.array(EvidenceRefSchema).optional(),
  physics_drift: z.number().optional(),
  commentary: z.string().optional()
});

// ═══════════════════════════════════════════════════════════════════════════════
// Governance — The 888_JUDGE Kernel
// ═══════════════════════════════════════════════════════════════════════════════

export const ConstraintSetSchema = z.object({
  laws: z.array(z.string()).optional(),
  thresholds: z.record(z.string(), z.number()).optional(),
  floor_checks: z.record(z.string(), z.boolean()).optional(),
  hard_limits: z.record(z.string(), z.tuple([z.number(), z.number()])).optional(),
  governance_level: z.number().min(0).max(11).default(1)
});

export const RiskAssessmentSchema = z.object({
  score: z.number().min(0).max(1).optional(),
  factors: z.array(z.object({
    key: z.string(),
    impact: z.number(),
    reason: z.string(),
  })).optional(),
  uncertainty_p10: z.number().optional(),
  uncertainty_p50: z.number().optional(),
  uncertainty_p90: z.number().optional(),
  conflation_risk: z.number().min(0).max(1).optional(),
  mitigation_strategy: z.string().optional()
});

export const VerdictSchema = z.object({
  verdictId: z.string().optional(),
  intentId: z.string().optional(),
  status: VerdictEnum,
  confidence: z.number().min(0).max(1),
  author: z.string(),
  rationale: z.string(),
  risk: RiskAssessmentSchema,
  auditTraceId: z.string().optional(),
  timestamp: z.string().datetime(),
});

export const AuditEventSchema = z.object({
  eventId: z.string().optional(),
  actor: z.string().optional(),
  tool: z.string().optional(),
  evidenceRefs: z.array(z.string()).optional(),
  verdictId: z.string().optional(),
  inputSnapshot: z.any().optional(),
  outputSnapshot: z.any().optional(),
  timestamp: z.string().datetime(),
  author: z.string().optional(),
  action: z.string().optional(),
  verdict: VerdictEnum.optional(),
  note: z.string().optional()
});

export const AppManifestSchema = z.object({
  appId: z.string().regex(/^geox\.[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*$/),
  version: z.string(),
  dimension: DimensionEnum,
  domain: AppDomainEnum,
  title: z.string(),
  description: z.string(),
  uiEntry: z.object({
    resourceUri: z.string(),
    mode: z.enum(['inline', 'external', 'inline-or-external']),
    visibility: z.enum(['model', 'app', 'both']),
  }),
  toolsRequired: z.array(z.string()),
  eventsPublished: z.array(z.string()),
  eventsSubscribed: z.array(z.string()),
  metadata: z.record(z.string(), z.any()).optional(),
});

// ═══════════════════════════════════════════════════════════════════════════════
// Composite Contracts
// ═══════════════════════════════════════════════════════════════════════════════

export const VerdictContractSchema = z.object({
  verdict_id: z.string().uuid(),
  code: VerdictEnum,
  rationale: z.string(),
  constraints: ConstraintSetSchema,
  risk: RiskAssessmentSchema,
  audit: z.array(AuditEventSchema),
  sealed_by: z.string().optional(),
  sealed_at: z.string().datetime().optional()
});

// ═══════════════════════════════════════════════════════════════════════════════
// TypeScript Types (Derived)
// ═══════════════════════════════════════════════════════════════════════════════

export type GeoContext = z.infer<typeof GeoContextSchema>;
export type EvidenceRef = z.infer<typeof EvidenceRefSchema>;
export type EvidenceObject = z.infer<typeof EvidenceObjectSchema>;
export type Verdict = z.infer<typeof VerdictSchema>;
export type AuditEvent = z.infer<typeof AuditEventSchema>;
export type XYPoint = z.infer<typeof XYPointSchema>;
export type XYZPoint = z.infer<typeof XYZPointSchema>;
export type BoundingBox = z.infer<typeof BoundingBoxSchema>;
export type AppManifest = z.infer<typeof AppManifestSchema>;
export type VerdictContract = z.infer<typeof VerdictContractSchema>;
