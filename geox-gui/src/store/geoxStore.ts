/**
 * geoxStore — Zustand global state for GEOX cockpit.
 * MCP server URL, active session, floor states, active panels.
 * DITEMPA BUKAN DIBERI
 */

import { create } from "zustand";
import type {
  FloorState,
  GeoxVerdict,
  ProspectVerdictResponse,
  SeismicLoadResponse,
  GeoxHealthResponse,
} from "../types/geox";

// ── Floor defaults ────────────────────────────────────────────────────────
const DEFAULT_FLOORS: FloorState[] = [
  { id: "F1", name: "Amanah", status: "UNKNOWN" },
  { id: "F2", name: "Truth", status: "UNKNOWN" },
  { id: "F4", name: "Clarity", status: "UNKNOWN" },
  { id: "F7", name: "Humility", status: "UNKNOWN" },
  { id: "F9", name: "Anti-Hantu", status: "UNKNOWN" },
  { id: "F11", name: "Authority", status: "UNKNOWN" },
  { id: "F13", name: "Sovereign", status: "UNKNOWN" },
];

// ── Store shape ───────────────────────────────────────────────────────────
interface GeoxState {
  // Server connection
  geoxUrl: string;
  setGeoxUrl: (url: string) => void;

  // Health / connectivity
  serverHealth: GeoxHealthResponse | null;
  serverOnline: boolean;
  setServerHealth: (h: GeoxHealthResponse | null) => void;

  // Constitutional floors (always visible — governance constraint)
  floors: FloorState[];
  setFloorStatus: (id: FloorState["id"], status: FloorState["status"], note?: string) => void;
  setFloorsFromVerdict: (verdict: GeoxVerdict) => void;

  // Active session
  sessionId: string | null;
  setSessionId: (id: string | null) => void;

  // Active seismic line
  activeLineId: string | null;
  seismicData: SeismicLoadResponse | null;
  setSeismicData: (lineId: string, data: SeismicLoadResponse) => void;

  // Last prospect verdict
  lastVerdict: ProspectVerdictResponse | null;
  setLastVerdict: (v: ProspectVerdictResponse | null) => void;

  // Panel visibility
  showMap: boolean;
  showSeismic: boolean;
  showWellLog: boolean;
  showProspect: boolean;
  togglePanel: (panel: "map" | "seismic" | "welllog" | "prospect") => void;
}

export const useGeoxStore = create<GeoxState>((set) => ({
  // ── Connection ────────────────────────────────────────────────────────
  geoxUrl: import.meta.env.VITE_GEOX_URL ?? "http://localhost:8100/mcp",
  setGeoxUrl: (url) => set({ geoxUrl: url }),

  // ── Health ────────────────────────────────────────────────────────────
  serverHealth: null,
  serverOnline: false,
  setServerHealth: (h) => set({ serverHealth: h, serverOnline: h?.ok ?? false }),

  // ── Constitutional floors (always visible) ────────────────────────────
  floors: DEFAULT_FLOORS,

  setFloorStatus: (id, status, note) =>
    set((s) => ({
      floors: s.floors.map((f) => (f.id === id ? { ...f, status, note } : f)),
    })),

  setFloorsFromVerdict: (verdict) =>
    set((s) => {
      // Map a GEOX verdict to floor pass/fail states
      const allPass = verdict === "SEAL";
      const allFail = verdict === "VOID";
      return {
        floors: s.floors.map((f) => ({
          ...f,
          status: allFail ? "FAIL" : allPass ? "PASS" : "UNKNOWN",
        })),
      };
    }),

  // ── Session ───────────────────────────────────────────────────────────
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),

  // ── Seismic ───────────────────────────────────────────────────────────
  activeLineId: null,
  seismicData: null,
  setSeismicData: (lineId, data) => set({ activeLineId: lineId, seismicData: data }),

  // ── Verdict ───────────────────────────────────────────────────────────
  lastVerdict: null,
  setLastVerdict: (v) => set({ lastVerdict: v }),

  // ── Panels ────────────────────────────────────────────────────────────
  showMap: true,
  showSeismic: true,
  showWellLog: false,
  showProspect: false,
  togglePanel: (panel) =>
    set((s) => ({
      showMap: panel === "map" ? !s.showMap : s.showMap,
      showSeismic: panel === "seismic" ? !s.showSeismic : s.showSeismic,
      showWellLog: panel === "welllog" ? !s.showWellLog : s.showWellLog,
      showProspect: panel === "prospect" ? !s.showProspect : s.showProspect,
    })),
}));
