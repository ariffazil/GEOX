/**
 * SeismicPanel — Seismic line loader + structural candidate viewer.
 * ToAC: visual contrast ≠ physical reality.
 */

import { useState } from "react";
import { useGeoxStore } from "../../store/geoxStore";
import { useGeoxTool } from "../../hooks/useGeoxTool";
import type { SeismicLoadResponse } from "../../types/geox";

export function SeismicPanel() {
  const [lineId, setLineId] = useState("");
  const [surveyPath, setSurveyPath] = useState("default_survey");
  const setSeismicData = useGeoxStore((s) => s.setSeismicData);

  const { call: loadLine, loading, error, data } = useGeoxTool<SeismicLoadResponse>("geox_load_seismic_line");

  const handleLoad = async () => {
    if (!lineId.trim()) return;
    const result = await loadLine({ line_id: lineId, survey_path: surveyPath, generate_views: true });
    if (result) setSeismicData(lineId, result);
  };

  return (
    <div className="flex flex-col h-full bg-geox-panel text-gray-200">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-geox-border text-xs font-mono text-gray-400">
        SEISMIC SECTION
      </div>

      <div className="p-3 flex flex-col gap-2">
        <div className="flex gap-2">
          <input
            className="flex-1 bg-geox-bg border border-geox-border rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-geox-partial"
            placeholder="Line ID (e.g. LINE_001)"
            value={lineId}
            onChange={(e) => setLineId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLoad()}
          />
          <input
            className="w-36 bg-geox-bg border border-geox-border rounded px-2 py-1 text-xs font-mono text-gray-400 focus:outline-none focus:border-geox-partial"
            placeholder="Survey path"
            value={surveyPath}
            onChange={(e) => setSurveyPath(e.target.value)}
          />
          <button
            onClick={handleLoad}
            disabled={loading || !lineId.trim()}
            className="px-3 py-1 text-xs font-mono bg-geox-partial text-white rounded disabled:opacity-50 hover:bg-blue-500"
          >
            {loading ? "…" : "LOAD"}
          </button>
        </div>

        {error && (
          <div className="text-xs text-geox-void font-mono bg-red-950 border border-red-800 rounded p-2">
            {error}
          </div>
        )}

        {data && (
          <div className="text-xs font-mono space-y-1">
            <div className="text-geox-seal">STATUS: {data.status ?? "IGNITED"}</div>
            {Array.isArray(data.views) && data.views.map((v, i) => (
              <div key={i} className="text-gray-400 pl-2 border-l border-geox-border">
                {v.view_id} · {v.mode}
              </div>
            ))}
            <div className="text-geox-hold mt-2 text-[10px]">
              ToAC: Scale unknown — measurement tools disabled (F4). Contrast canon active.
            </div>
          </div>
        )}

        {!data && !loading && (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-xs font-mono">
            Enter a line ID to load seismic data
          </div>
        )}
      </div>
    </div>
  );
}
