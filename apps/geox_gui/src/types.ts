/**
 * GEOX App Shells — 3 Apps / 9 Substrates
 * DITEMPA BUKAN DIBERI
 *
 * Re-exports from types/index.ts for backward compatibility.
 * All canonical types live in types/index.ts.
 */

// Re-export everything from canonical types module
export type {
  Coordinate,
  CoordinateWithMeta,
  BoundingBox,
  MapLayerType,
  MapLayer,
  GeoSelection,
  SeismicLine,
  SeismicGrounding,
  SeismicData,
  DisplayMode,
  HorizonPick,
  StructuralCandidate,
  Well,
  LogCurveType,
  WellLog,
  LogCurve,
  LogTrack,
  SeismicLogTie,
  DepthCursor,
  OutcropImage,
  Annotation,
  AISuggestion,
  Prospect,
  DecisionGate,
  EvidenceStack,
  EvidenceItem,
  RiskMatrix,
  RiskLevel,
  MissingConstraint,
  FloorId,
  FloorStatus,
  FloorType,
  ConstitutionalFloor,
  GovernanceState,
  GroundingStatus,
  UncertaintyState,
  Tab,
  ViewMode,
  CursorState,
  PanelConfig,
  GeospatialVerification,
  ProspectEvaluation,
  HealthStatus,
  McpConnectionStatus,
  GEOXState,
  GeoxMethod,
  GeoxEvent,
  AppInitializeParams,
  ContextPatchParams,
  UIActionParams,
  UIStateSyncParams,
  ToolRequestParams,
  ToolResponseParams,
  GEOXAction,
} from './types/index.js';

export type AppId = 'x1d' | 'x2d' | 'x3d' | 'arifos';

export type SubstrateId = 
  | 'lithos' | 'pore' | 'fluid'    // X-1D
  | 'strata' | 'break' | 'elastic'  // X-2D
  | 'kinetic' | 'stress' | 'flow';  // X-3D

export interface Substrate {
  id: SubstrateId;
  app: AppId;
  label: string;
  physics_hook: string;
  description: string;
  unit: string;
}

export const SUBSTRATES: Record<SubstrateId, Substrate> = {
  lithos: { id: 'lithos', app: 'x1d', label: 'Lithos', physics_hook: 'Mass', description: 'Rock fabric & density', unit: 'rho_b' },
  pore: { id: 'pore', app: 'x1d', label: 'Pores', physics_hook: 'Volume', description: 'Void space & permeability', unit: 'phi' },
  fluid: { id: 'fluid', app: 'x1d', label: 'Fluids', physics_hook: 'Saturation', description: 'Saturation & fluid type', unit: 'Sw' },
  strata: { id: 'strata', app: 'x2d', label: 'Strata', physics_hook: 'Time', description: 'Stacking & sequence', unit: 't' },
  break: { id: 'break', app: 'x2d', label: 'Breaks', physics_hook: 'Displacement', description: 'Faults & fractures', unit: 'u' },
  elastic: { id: 'elastic', app: 'x2d', label: 'Elastic', physics_hook: 'Velocity', description: 'Impedance & waves', unit: 'V' },
  kinetic: { id: 'kinetic', app: 'x3d', label: 'Kinetic', physics_hook: 'Energy', description: 'Maturity & heat', unit: 'T' },
  stress: { id: 'stress', app: 'x3d', label: 'Stress', physics_hook: 'Pressure', description: 'Pressure & stability', unit: 'P' },
  flow: { id: 'flow', app: 'x3d', label: 'Flow', physics_hook: 'Flux', description: 'Dynamics & flux', unit: 'k' },
};

// ── ToAC v1 Types ────────────────────────────────────────────────────────────

export type PerceptionClass = 'MEASURED' | 'DERIVED' | 'DISPLAY' | 'CORROBORATED' | 'HYPOTHESIS';

export type EvidenceTag =
  | 'EVIDENCE_DIRECT' | 'EVIDENCE_MULTI_ZONE'
  | 'INTERPRET_FROM_LITHOLOGY' | 'SOURCE_UNRESOLVED'
  | 'NN_NOT_PARSED' | 'NO_GDE_SOURCE' | 'GDE_NOT_MAPPED'
  | 'PROXY_FROM_CONTEXT' | 'UNKNOWN';

export type Canon9 = 'rho' | 'Vp' | 'Vs' | 'rho_e' | 'chi' | 'k' | 'P' | 'T' | 'phi';

export type VerticalTrend = 'DEEPENING_UPWARD' | 'SHALLOWING_UPWARD' | 'STABLE_OR_AMBIGUOUS' | 'UNKNOWN';

export type LithoClass = 'CARBONATE' | 'HETEROLITHIC' | 'SAND_PRONE' | 'SILT_PRONE' | 'SHALE_PRONE' | 'COAL_CARBONACEOUS' | 'MIXED_OR_UNSPECIFIED' | 'UNKNOWN';

export interface ToACReport {
  perception_class: PerceptionClass;
  evidence_tag: EvidenceTag;
  canon_9_touched: Canon9[];
  vertical_trend: VerticalTrend;
  litho_class: LithoClass;
  strat_standard: {
    scheme: string;
    reference_chart: string;
  };
}

export interface ToACState {
  currentReport: ToACReport | null;
  history: ToACReport[];
  toolCounts: {
    withPerceptionClass: number;
    withEvidenceTag: number;
    withCanon9: number;
    withVerticalTrend: number;
    withLithoClass: number;
  };
}

export const PERCEPTION_CLASS_META: Record<PerceptionClass, { label: string; color: string; bg: string; description: string }> = {
  MEASURED:     { label: 'Measured',     color: 'text-green-600',  bg: 'bg-green-100',  description: 'Direct sensor measurement' },
  DERIVED:      { label: 'Derived',      color: 'text-blue-600',   bg: 'bg-blue-100',   description: 'Calculated from measured data' },
  DISPLAY:      { label: 'Display',      color: 'text-purple-600', bg: 'bg-purple-100', description: 'Visual artifact, not physical truth' },
  CORROBORATED: { label: 'Corroborated', color: 'text-teal-600',   bg: 'bg-teal-100',   description: 'Multi-evidence confirmation' },
  HYPOTHESIS:   { label: 'Hypothesis',   color: 'text-amber-600',  bg: 'bg-amber-100',  description: 'Proxy without raw signal' },
};

export const CANON9_META: Record<Canon9, { symbol: string; name: string; unit: string }> = {
  rho:  { symbol: 'ρ',     name: 'Bulk density',     unit: 'g/cm³' },
  Vp:   { symbol: 'Vp',    name: 'P-wave velocity',  unit: 'm/s' },
  Vs:   { symbol: 'Vs',    name: 'S-wave velocity',  unit: 'm/s' },
  rho_e:{ symbol: 'ρₑ',    name: 'Resistivity',      unit: 'Ω·m' },
  chi:  { symbol: 'χ',     name: 'Susceptibility',   unit: 'SI' },
  k:    { symbol: 'k',     name: 'Permeability',     unit: 'mD' },
  P:    { symbol: 'P',     name: 'Pressure',         unit: 'MPa' },
  T:    { symbol: 'T',     name: 'Temperature',      unit: '°C' },
  phi:  { symbol: 'φ',     name: 'Porosity',         unit: '%' },
};