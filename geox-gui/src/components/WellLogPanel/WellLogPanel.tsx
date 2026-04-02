/**
 * WellLogPanel — Well log viewer stub. Ready for LAS data integration.
 * Connects to geox_query_memory to surface past well evaluations.
 */

import { useState } from "react";
import { useGeoxTool } from "../../hooks/useGeoxTool";
import type { GeoxMemoryResponse } from "../../types/geox";

export function WellLogPanel() {
  const [query, setQuery] = useState("");
  const [basin, setBasin] = useState("");
  const { call: queryMemory, loading, error, data } = useGeoxTool<GeoxMemoryResponse>("geox_query_memory");

  const handleQuery = async () => {
    if (!query.trim()) return;
    await queryMemory({ query, basin: basin || null, limit: 5 });
  };

  return (
    <div className="flex flex-col h-full bg-geox-panel text-gray-200">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-geox-border text-xs font-mono text-gray-400">
        WELL LOG + MEMORY
      </div>

      <div className="p-3 flex flex-col gap-2">
        <div className="flex gap-2">
          <input
            className="flex-1 bg-geox-bg border border-geox-border rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-geox-partial"
            placeholder="Search past evaluations…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
          />
          <input
            className="w-28 bg-geox-bg border border-geox-border rounded px-2 py-1 text-xs font-mono text-gray-400"
            placeholder="Basin"
            value={basin}
            onChange={(e) => setBasin(e.target.value)}
          />
          <button
            onClick={handleQuery}
            disabled={loading || !query.trim()}
            className="px-3 py-1 text-xs font-mono bg-geox-partial text-white rounded disabled:opacity-50 hover:bg-blue-500"
          >
            {loading ? "…" : "RECALL"}
          </button>
        </div>

        {error && (
          <div className="text-xs text-geox-void font-mono bg-red-950 border border-red-800 rounded p-2">
            {error}
          </div>
        )}

        {data && (
          <div className="space-y-1 text-xs font-mono">
            <div className="text-gray-500">{data.count} result(s) · {data.memory_backend}</div>
            {data.results.map((r, i) => (
              <div key={i} className="border border-geox-border rounded p-2 space-y-0.5">
                <div className="text-gray-200 font-semibold">{r.prospect_name}</div>
                <div className="text-gray-500">{r.basin} · {r.verdict} · {(r.confidence * 100).toFixed(0)}%</div>
                <div className="text-gray-400 text-[10px] line-clamp-2">{r.insight_text}</div>
              </div>
            ))}
            {data.count === 0 && (
              <div className="text-gray-600">No prior evaluations found for this query.</div>
            )}
          </div>
        )}

        <div className="mt-4 border-t border-geox-border pt-3 text-gray-600 text-[10px] font-mono">
          LAS file upload — coming in v0.6.0
        </div>
      </div>
    </div>
  );
}
