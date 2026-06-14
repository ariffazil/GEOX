/**
 * useMcpTool — Generic MCP tool caller hook
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Wraps a single MCP tool call with { data, status, error, call, reset }.
 * Sends tool.request via postMessage to the host bridge and resolves on
 * the matching tool.response event. Timeout: 30s.
 *
 * Constitutional integration:
 *   F11 Auditability — marks amber while in-flight, green on success
 *   F12 Resilience   — marks red on error, amber on timeout
 *
 * Usage:
 *   const { data, status, error, call } = useMcpTool<MyArgs, MyResult>('geox_compute_petrophysics');
 *   await call({ model: 'archie', rw: 0.05, ... });
 */

import { useState, useCallback, useRef } from 'react';
import { useGEOXStore } from '../store/geoxStore';
import type { ToACReport } from '../types';

export type McpToolStatus = 'idle' | 'loading' | 'success' | 'error';

export interface McpToolState<T = unknown> {
  data: T | null;
  status: McpToolStatus;
  error: string | null;
  lastCalledAt: string | null;
}

const TIMEOUT_MS = 30_000;
const GEOX_MCP_ENDPOINT = '/mcp/';

/**
 * Detect if we're running in an iframe (ChatGPT/Claude plugin mode)
 * vs standalone (browser direct). Uses same logic as useGeoxBridge.
 */
function isInIframe(): boolean {
  try {
    return typeof window !== 'undefined' && window.parent !== window;
  } catch {
    return false;
  }
}

/**
 * Direct HTTP call to GEOX MCP server via fetch.
 * Used in standalone mode (not in iframe).
 */
async function directMcpCall<TResult>(
  toolName: string,
  args: Record<string, unknown>,
  baseUrl: string,
): Promise<TResult> {
  const url = `${baseUrl}${GEOX_MCP_ENDPOINT}`;
  const body = JSON.stringify({
    jsonrpc: '2.0',
    id: `${toolName}-${Date.now()}`,
    method: 'tools/call',
    params: { name: toolName, arguments: args },
  });

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  });

  if (!response.ok) {
    throw new Error(`GEOX MCP HTTP ${response.status}: ${response.statusText}`);
  }

  const json = await response.json();
  const error = json.error;
  if (error) {
    throw new Error(`GEOX MCP error: ${error.message ?? JSON.stringify(error)}`);
  }

  const content = json?.result?.content;
  if (!content || content.length === 0) {
    throw new Error(`GEOX MCP: empty result for ${toolName}`);
  }

  // MCP returns content[0].text — parse inner JSON result
  const text = content[0].text;
  if (typeof text === 'string' && text.length > 0) {
    try {
      // The tool result is JSON-stringified inside the MCP content text
      const parsed = JSON.parse(text);
      return parsed as TResult;
    } catch {
      // If it's not JSON (e.g. string result), return as-is
      return text as unknown as TResult;
    }
  }

  return text as unknown as TResult;
}

export function useMcpTool<TArgs = Record<string, unknown>, TResult = unknown>(
  toolName: string,
) {
  const [state, setState] = useState<McpToolState<TResult>>({
    data: null,
    status: 'idle',
    error: null,
    lastCalledAt: null,
  });

  const pendingRef = useRef<{
    resolve: (v: TResult) => void;
    reject: (e: string) => void;
    id: string;
    timer: ReturnType<typeof setTimeout>;
    handler?: (event: MessageEvent) => void;
  } | null>(null);

  const { updateFloorStatus, setToACReport, geoxUrl } = useGEOXStore();

  const call = useCallback(
    (args: TArgs): Promise<TResult> => {
      // Cancel any previous in-flight call
      if (pendingRef.current) {
        clearTimeout(pendingRef.current.timer);
        if (pendingRef.current.handler) {
          window.removeEventListener('message', pendingRef.current.handler);
        }
        pendingRef.current.reject(`Superseded by new call to ${toolName}`);
        pendingRef.current = null;
      }

      return new Promise<TResult>((resolve, reject) => {
        setState({
          data: null,
          status: 'loading',
          error: null,
          lastCalledAt: new Date().toISOString(),
        });
        updateFloorStatus('F11', 'amber', `${toolName} in progress…`);

        // ─── PATH B: Standalone mode — direct HTTP fetch ─────────────────
        if (!isInIframe() && geoxUrl) {
          const timer = setTimeout(() => {
            const msg = `${toolName} timed out after ${TIMEOUT_MS / 1000}s (standalone)`;
            setState(prev => ({ ...prev, status: 'error', error: msg }));
            updateFloorStatus('F12', 'amber', msg);
            reject(msg);
          }, TIMEOUT_MS);

          directMcpCall<TResult>(toolName, args as Record<string, unknown>, geoxUrl)
            .then((result) => {
              clearTimeout(timer);
              setState(prev => ({ ...prev, data: result, status: 'success', error: null }));
              updateFloorStatus('F11', 'green', `${toolName} completed`);

              // Extract ToAC v1 fields
              const r = result as Record<string, unknown>;
              if (r && (r['claim_tag'] || r['acrisk'] !== undefined)) {
                setToACReport({
                  perception_class: (r['perception_class'] as ToACReport['perception_class']) || 'HYPOTHESIS',
                  evidence_tag: (r['evidence_tag'] as ToACReport['evidence_tag']) || 'UNKNOWN',
                  canon_9_touched: (r['canon_9_touched'] as ToACReport['canon_9_touched']) || [],
                  vertical_trend: (r['vertical_trend'] as ToACReport['vertical_trend']) || 'UNKNOWN',
                  litho_class: (r['litho_class'] as ToACReport['litho_class']) || 'UNKNOWN',
                  strat_standard: (r['strat_standard'] as ToACReport['strat_standard']) || { scheme: 'NN_zone', reference_chart: '' },
                });
              }

              resolve(result);
            })
            .catch((err) => {
              clearTimeout(timer);
              const errMsg = String(err);
              setState(prev => ({ ...prev, status: 'error', error: errMsg }));
              updateFloorStatus('F12', 'red', `${toolName} error: ${errMsg}`);
              reject(errMsg);
            });

          return;
        }

        // ─── PATH A: iframe mode — postMessage to host LLM ────────────────
        const callId = `${toolName}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

        const timer = setTimeout(() => {
          if (pendingRef.current?.handler) {
            window.removeEventListener('message', pendingRef.current.handler);
          }
          pendingRef.current = null;
          const msg = `${toolName} timed out after ${TIMEOUT_MS / 1000}s (iframe)`;
          setState(prev => ({ ...prev, status: 'error', error: msg }));
          updateFloorStatus('F12', 'amber', msg);
          reject(msg);
        }, TIMEOUT_MS);

        pendingRef.current = { resolve, reject, id: callId, timer };

        function _handleResponse(event: MessageEvent) {
          const data = event.data;
          if (data?.jsonrpc !== '2.0' || data?.method !== 'tool.response') return;
          if (data?.params?.tool !== toolName) return;
          if (data?.id !== callId) return;

          clearTimeout(timer);
          window.removeEventListener('message', _handleResponse);
          pendingRef.current = null;

          if (data.params.error) {
            const errMsg = String(data.params.error);
            setState(prev => ({ ...prev, status: 'error', error: errMsg }));
            updateFloorStatus('F12', 'red', `${toolName} error: ${errMsg}`);
            reject(errMsg);
          } else {
            const result = data.params.result as TResult;
            setState(prev => ({ ...prev, data: result, status: 'success', error: null }));
            updateFloorStatus('F11', 'green', `${toolName} completed`);

            const r = result as Record<string, unknown>;
            if (r && (r['perception_class'] || r['evidence_tag'])) {
              setToACReport({
                perception_class: (r['perception_class'] as ToACReport['perception_class']) || 'HYPOTHESIS',
                evidence_tag: (r['evidence_tag'] as ToACReport['evidence_tag']) || 'UNKNOWN',
                canon_9_touched: (r['canon_9_touched'] as ToACReport['canon_9_touched']) || [],
                vertical_trend: (r['vertical_trend'] as ToACReport['vertical_trend']) || 'UNKNOWN',
                litho_class: (r['litho_class'] as ToACReport['litho_class']) || 'UNKNOWN',
                strat_standard: (r['strat_standard'] as ToACReport['strat_standard']) || { scheme: 'NN_zone', reference_chart: '' },
              });
            }

            resolve(result);
          }
        }

        pendingRef.current.handler = _handleResponse;
        window.addEventListener('message', _handleResponse);

        window.parent.postMessage(
          {
            jsonrpc: '2.0',
            method: 'tool.request',
            params: { tool: toolName, arguments: args },
            id: callId,
            timestamp: new Date().toISOString(),
          },
          '*',
        );
      });
    },
    [toolName, updateFloorStatus, setToACReport, geoxUrl],
  );

  const reset = useCallback(() => {
    if (pendingRef.current) {
      clearTimeout(pendingRef.current.timer);
      pendingRef.current = null;
    }
    setState({ data: null, status: 'idle', error: null, lastCalledAt: null });
  }, []);

  return { ...state, call, reset };
}
