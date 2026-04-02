/**
 * useGeoxTool — MCP client hook for GEOX tools.
 * All calls go through this hook so the server URL is centralised.
 * DITEMPA BUKAN DIBERI
 */

import { useState, useCallback } from "react";
import type { McpRequest, McpResponse, McpToolResult } from "../types/geox";
import { useGeoxStore } from "../store/geoxStore";

export interface UseGeoxToolState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

let _requestId = 1;

/**
 * Core fetch — sends a single MCP tools/call and returns the structured_content.
 * Throws on network error or MCP error response.
 */
export async function callGeoxTool<T>(
  geoxUrl: string,
  toolName: string,
  args: Record<string, unknown>
): Promise<T> {
  const body: McpRequest = {
    jsonrpc: "2.0",
    id: _requestId++,
    method: "tools/call",
    params: { name: toolName, arguments: args },
  };

  const resp = await fetch(geoxUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  }

  const json: McpResponse = await resp.json();

  if (json.error) {
    throw new Error(`MCP error ${json.error.code}: ${json.error.message}`);
  }

  const result = json.result as McpToolResult;

  // Prefer structured_content; fall back to parsing first text block
  if (result.structured_content !== undefined && result.structured_content !== null) {
    return result.structured_content as T;
  }

  const text = result.content?.[0]?.text ?? "{}";
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

/**
 * React hook — wraps callGeoxTool with loading/error state.
 *
 * @example
 * const { call, data, loading, error } = useGeoxTool<GeoxHealthResponse>("geox_health");
 * await call({});
 */
export function useGeoxTool<T>(toolName: string) {
  const geoxUrl = useGeoxStore((s) => s.geoxUrl);
  const [state, setState] = useState<UseGeoxToolState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const call = useCallback(
    async (args: Record<string, unknown> = {}) => {
      setState({ data: null, loading: true, error: null });
      try {
        const data = await callGeoxTool<T>(geoxUrl, toolName, args);
        setState({ data, loading: false, error: null });
        return data;
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setState({ data: null, loading: false, error: msg });
        return null;
      }
    },
    [geoxUrl, toolName]
  );

  return { ...state, call };
}
