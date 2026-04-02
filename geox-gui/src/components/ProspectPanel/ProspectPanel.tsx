/**
 * ProspectPanel — Prospect evaluation with governed verdict.
 * Human decision explicit at prospect gate (F13 Sovereign).
 * DITEMPA BUKAN DIBERI
 */

import { useState } from "react";
import { useGeoxStore } from "../../store/geoxStore";
import { useGeoxTool } from "../../hooks/useGeoxTool";
import type { ProspectVerdictResponse } from "../../types/geox";
import { clsx } from "clsx";

const VERDICT_STYLE: Record<string, string> = {
  SEAL: "border-geox-seal text-geox-seal bg-green-950",
  PARTIAL: "border-geox-partial text-geox-partial bg-blue-950",
  SABAR: "border-geox-hold text-geox-hold bg-yellow-950",
  "888_HOLD": "border-geox-hold text-geox-hold bg-yellow-950",
  VOID: "border-geox-void text-geox-void bg-red-950",
  PHYSICAL_GROUNDING_REQUIRED: "border-geox-hold text-geox-hold bg-yellow-950",
};

export function ProspectPanel() {
  const [prospectId, setProspectId] = useState("");
  const [interpretationId, setInterpretationId] = useState("INT_001");
  const setLastVerdict = useGeoxStore((s) => s.setLastVerdict);
  const setFloorsFromVerdict = useGeoxStore((s) => s.setFloorsFromVerdict);
  const lastVerdict = useGeoxStore((s) => s.lastVerdict);

  const { call: evaluate, loading, error } = useGeoxTool<ProspectVerdictResponse>("geox_evaluate_prospect");

  const handleEvaluate = async () => {
    if (!prospectId.trim()) return;
    const result = await evaluate({
      prospect_id: prospectId,
      interpretation_id: interpretationId,
    });
    if (result) {
      setLastVerdict(result);
      setFloorsFromVerdict(result.verdict);
    }
  };

  const verdictStyle = lastVerdict ? VERDICT_STYLE[lastVerdict.verdict] ?? "border-gray-500" : null;

  return (
    <div className="flex flex-col h-full bg-geox-panel text-gray-200">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-geox-border text-xs font-mono text-gray-400">
        PROSPECT GATE
        <span className="text-[10px] ml-auto text-geox-hold">F13 SOVEREIGN ACTIVE</span>
      </div>

      <div className="p-3 flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <input
            className="bg-geox-bg border border-geox-border rounded px-2 py-1.5 text-xs font-mono text-gray-200 focus:outline-none focus:border-geox-partial"
            placeholder="Prospect ID (e.g. PROSPECT_ALPHA)"
            value={prospectId}
            onChange={(e) => setProspectId(e.target.value)}
          />
          <input
            className="bg-geox-bg border border-geox-border rounded px-2 py-1.5 text-xs font-mono text-gray-400"
            placeholder="Interpretation ID"
            value={interpretationId}
            onChange={(e) => setInterpretationId(e.target.value)}
          />
          <button
            onClick={handleEvaluate}
            disabled={loading || !prospectId.trim()}
            className="mt-1 px-3 py-2 text-xs font-mono bg-geox-partial text-white rounded disabled:opacity-50 hover:bg-blue-500 uppercase tracking-wider"
          >
            {loading ? "Evaluating…" : "Evaluate Prospect"}
          </button>
        </div>

        {error && (
          <div className="text-xs text-geox-void font-mono bg-red-950 border border-red-800 rounded p-2">
            {error}
          </div>
        )}

        {lastVerdict && verdictStyle && (
          <div className={clsx("border rounded p-3 text-xs font-mono space-y-2", verdictStyle)}>
            <div className="text-base font-bold">{lastVerdict.verdict}</div>
            <div className="text-gray-300">
              Confidence: {(lastVerdict.confidence * 100).toFixed(0)}%
            </div>
            <div className="text-gray-400">{lastVerdict.reason}</div>
            <div className="text-[10px] text-gray-500 pt-1 border-t border-current/20 flex justify-between">
              <span>{lastVerdict.vault_sealed ? "✓ VAULT999 sealed" : "VAULT999 write skipped"}</span>
              {lastVerdict.session_id && <span>session: {lastVerdict.session_id.slice(0, 12)}…</span>}
            </div>
          </div>
        )}

        <div className="mt-auto text-[10px] text-gray-600 font-mono border-t border-geox-border pt-2">
          Human decision required before proceeding past this gate. F13 Sovereign veto active.
        </div>
      </div>
    </div>
  );
}
