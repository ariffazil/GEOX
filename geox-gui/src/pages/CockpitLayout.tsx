/**
 * CockpitLayout — Single-screen geologist cockpit.
 * Governance badges always visible at top (constitutional constraint).
 * DITEMPA BUKAN DIBERI
 */

import { WitnessBadges } from "../components/WitnessBadges/WitnessBadges";
import { MapPanel } from "../components/MapPanel/MapPanel";
import { SeismicPanel } from "../components/SeismicPanel/SeismicPanel";
import { WellLogPanel } from "../components/WellLogPanel/WellLogPanel";
import { ProspectPanel } from "../components/ProspectPanel/ProspectPanel";
import { useGeoxStore } from "../store/geoxStore";

export function CockpitLayout() {
  const { showMap, showSeismic, showWellLog, showProspect, togglePanel } = useGeoxStore();

  return (
    <div className="flex flex-col h-screen bg-geox-bg text-gray-100 overflow-hidden">
      {/* ── Governance badges — ALWAYS VISIBLE ──────────────────────────── */}
      <WitnessBadges />

      {/* ── Toolbar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-1 px-3 py-1 border-b border-geox-border text-xs font-mono bg-geox-panel">
        <span className="text-gray-500 mr-2">GEOX v0.5</span>
        {(["map", "seismic", "welllog", "prospect"] as const).map((p) => {
          const active = {
            map: showMap,
            seismic: showSeismic,
            welllog: showWellLog,
            prospect: showProspect,
          }[p];
          return (
            <button
              key={p}
              onClick={() => togglePanel(p)}
              className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider transition-colors ${
                active
                  ? "bg-geox-partial text-white"
                  : "bg-geox-bg text-gray-500 hover:text-gray-300"
              }`}
            >
              {p}
            </button>
          );
        })}
      </div>

      {/* ── Main panels ─────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {showMap && (
          <div className="flex-1 border-r border-geox-border min-w-0">
            <MapPanel />
          </div>
        )}
        {showSeismic && (
          <div className="w-72 border-r border-geox-border shrink-0 overflow-y-auto">
            <SeismicPanel />
          </div>
        )}
        {showWellLog && (
          <div className="w-64 border-r border-geox-border shrink-0 overflow-y-auto">
            <WellLogPanel />
          </div>
        )}
        {showProspect && (
          <div className="w-72 shrink-0 overflow-y-auto">
            <ProspectPanel />
          </div>
        )}
        {!showMap && !showSeismic && !showWellLog && !showProspect && (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-mono">
            Toggle panels from the toolbar above
          </div>
        )}
      </div>
    </div>
  );
}
