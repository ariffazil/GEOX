/**
 * GEOX TypeScript types — mirrors arifos/geox Python schemas.
 * DITEMPA BUKAN DIBERI
 */

// ── Verdicts ──────────────────────────────────────────────────────────────
export type GeoxVerdict = "SEAL" | "PARTIAL" | "SABAR" | "888_HOLD" | "VOID" | "PHYSICAL_GROUNDING_REQUIRED";
export type FloorStatus = "PASS" | "FAIL" | "UNKNOWN";

// ── Constitutional Floors ─────────────────────────────────────────────────
export interface FloorState {
  id: "F1" | "F2" | "F4" | "F7" | "F9" | "F11" | "F13";
  name: string;
  status: FloorStatus;
  note?: string;
}

// ── Tool responses ────────────────────────────────────────────────────────
export interface GeoxHealthResponse {
  ok: boolean;
  service: string;
  version: string;
  fastmcp_version: string;
  seal: string;
  prefab_ui: boolean;
  seismic_engine: boolean;
  timestamp: string;
  constitutional_floors: string[];
}

export interface SeismicLoadResponse {
  view_type: string;
  mode: string;
  line_id: string;
  survey_path: string;
  status: string;
  views: SeismicView[];
  timestamp: string;
}

export interface SeismicView {
  view_id: string;
  mode: string;
  source: string;
  note?: string;
}

export interface StructuralCandidate {
  model_id: string;
  description: string;
  confidence: number;
  attributes?: Record<string, number>;
}

export interface ProspectVerdictResponse {
  view_type: string;
  prospect_id: string;
  interpretation_id: string;
  verdict: GeoxVerdict;
  confidence: number;
  status: string;
  reason: string;
  session_id: string | null;
  vault_sealed: boolean;
}

export interface MemoryQueryResult {
  entry_id: string;
  prospect_name: string;
  basin: string;
  insight_text: string;
  verdict: string;
  confidence: number;
  timestamp: string;
}

export interface GeoxMemoryResponse {
  query: string;
  basin_filter: string | null;
  results: MemoryQueryResult[];
  count: number;
  memory_backend: string;
  timestamp: string;
}

export interface GeospatialResponse {
  view_type: string;
  lat: number;
  lon: number;
  radius_m: number;
  geological_province: string;
  jurisdiction: string;
  verdict: string;
}

// ── MCP protocol ──────────────────────────────────────────────────────────
export interface McpToolResult {
  content: Array<{ type: "text"; text: string }>;
  structured_content?: unknown;
  isError?: boolean;
}

export interface McpRequest {
  jsonrpc: "2.0";
  id: number;
  method: "tools/call";
  params: { name: string; arguments: Record<string, unknown> };
}

export interface McpResponse {
  jsonrpc: "2.0";
  id: number;
  result?: McpToolResult;
  error?: { code: number; message: string };
}
