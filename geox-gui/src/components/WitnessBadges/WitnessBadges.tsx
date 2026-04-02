/**
 * WitnessBadges — Constitutional floor status bar.
 * ALWAYS VISIBLE — governance constraint, never hidden.
 * DITEMPA BUKAN DIBERI
 */

import { useEffect } from "react";
import { useGeoxStore } from "../../store/geoxStore";
import { useGeoxTool } from "../../hooks/useGeoxTool";
import type { GeoxHealthResponse } from "../../types/geox";
import { clsx } from "clsx";

const STATUS_COLORS = {
  PASS: "bg-geox-seal text-white",
  FAIL: "bg-geox-void text-white",
  UNKNOWN: "bg-gray-600 text-gray-300",
};

const VERDICT_BG = {
  SEAL: "border-geox-seal text-geox-seal",
  PARTIAL: "border-geox-partial text-geox-partial",
  SABAR: "border-geox-hold text-geox-hold",
  "888_HOLD": "border-geox-hold text-geox-hold",
  VOID: "border-geox-void text-geox-void",
  PHYSICAL_GROUNDING_REQUIRED: "border-geox-hold text-geox-hold",
};

export function WitnessBadges() {
  const floors = useGeoxStore((s) => s.floors);
  const serverOnline = useGeoxStore((s) => s.serverOnline);
  const setServerHealth = useGeoxStore((s) => s.setServerHealth);
  const lastVerdict = useGeoxStore((s) => s.lastVerdict);

  const { call: fetchHealth } = useGeoxTool<GeoxHealthResponse>("geox_health");

  // Poll server health every 30 s
  useEffect(() => {
    const run = async () => {
      const h = await fetchHealth({});
      if (h) setServerHealth(h);
    };
    run();
    const interval = setInterval(run, 30_000);
    return () => clearInterval(interval);
  }, [fetchHealth, setServerHealth]);

  const verdictKey = lastVerdict?.verdict ?? null;
  const verdictColor = verdictKey ? VERDICT_BG[verdictKey] ?? "border-gray-500 text-gray-400" : null;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-geox-panel border-b border-geox-border flex-wrap">
      {/* Server status dot */}
      <span
        className={clsx(
          "w-2 h-2 rounded-full shrink-0",
          serverOnline ? "bg-geox-seal" : "bg-geox-void"
        )}
        title={serverOnline ? "GEOX server online" : "GEOX server offline"}
      />
      <span className="text-xs text-gray-400 mr-2 font-mono">
        {serverOnline ? "ONLINE" : "OFFLINE"}
      </span>

      {/* Floor badges */}
      {floors.map((floor) => (
        <span
          key={floor.id}
          title={floor.note ?? `${floor.id} ${floor.name}: ${floor.status}`}
          className={clsx(
            "text-xs font-mono px-1.5 py-0.5 rounded",
            STATUS_COLORS[floor.status]
          )}
        >
          {floor.id}
        </span>
      ))}

      {/* Last verdict */}
      {verdictKey && (
        <span
          className={clsx(
            "ml-auto text-xs font-mono border px-2 py-0.5 rounded",
            verdictColor
          )}
        >
          {verdictKey}
        </span>
      )}

      {/* Vault sealed indicator */}
      {lastVerdict?.vault_sealed && (
        <span className="text-xs text-geox-seal font-mono" title="Sealed in VAULT999">
          ✓ VAULT999
        </span>
      )}
    </div>
  );
}
