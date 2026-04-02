/**
 * GEOX Store — DITEMPA BUKAN DIBERI
 * 
 * Zustand store for GEOX GUI state management with
 * constitutional governance (F1-F13) integration.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type {
  GEOXState,
  Coordinate,
  CursorState,
  Tab,
  ViewMode,
  FloorId,
  FloorStatus,
  GovernanceState,
} from '../types';

// Initial governance state with all F1-F13 floors
const initialGovernance: GovernanceState = {
  floors: {
    F1: {
      id: 'F1',
      name: 'AMANAH',
      description: 'Reversibility - Can this be undone?',
      type: 'hard',
      status: 'grey',
    },
    F2: {
      id: 'F2',
      name: 'TRUTH',
      description: 'Evidence-based - Grounded in evidence?',
      type: 'hard',
      status: 'grey',
    },
    F3: {
      id: 'F3',
      name: 'TRI-WITNESS',
      description: 'Theory/Constitution/Intent alignment',
      type: 'soft',
      status: 'grey',
    },
    F4: {
      id: 'F4',
      name: 'CLARITY',
      description: 'Reduces confusion?',
      type: 'soft',
      status: 'grey',
    },
    F5: {
      id: 'F5',
      name: 'PEACE',
      description: 'Does not destroy?',
      type: 'soft',
      status: 'grey',
    },
    F6: {
      id: 'F6',
      name: 'EMPATHY',
      description: 'Shows understanding?',
      type: 'soft',
      status: 'grey',
    },
    F7: {
      id: 'F7',
      name: 'HUMILITY',
      description: 'Acknowledges uncertainty?',
      type: 'soft',
      status: 'grey',
    },
    F8: {
      id: 'F8',
      name: 'GENIUS',
      description: 'Maintains system health?',
      type: 'soft',
      status: 'grey',
    },
    F9: {
      id: 'F9',
      name: 'ANTI-HANTU',
      description: 'No consciousness claims',
      type: 'hard',
      status: 'green',
    },
    F10: {
      id: 'F10',
      name: 'CONSCIENCE',
      description: 'Non-manipulative?',
      type: 'hard',
      status: 'grey',
    },
    F11: {
      id: 'F11',
      name: 'AUDITABILITY',
      description: 'Logged and inspectable?',
      type: 'soft',
      status: 'grey',
    },
    F12: {
      id: 'F12',
      name: 'RESILIENCE',
      description: 'Fails safely?',
      type: 'soft',
      status: 'grey',
    },
    F13: {
      id: 'F13',
      name: 'SOVEREIGN',
      description: 'Human authority preserved?',
      type: 'hard',
      status: 'green',
    },
  },
  overallStatus: 'grey',
  seal: 'DITEMPA BUKAN DIBERI',
  sessionId: typeof crypto !== 'undefined' ? crypto.randomUUID() : 'session-' + Date.now(),
  timestamp: new Date().toISOString(),
};

// Initial state
const initialState: GEOXState = {
  activeTab: 'map',
  viewMode: '2d',
  panelConfig: {
    leftWidth: 25,
    centerWidth: 50,
    rightWidth: 25,
    bottomHeight: 15,
  },
  layers: [
    {
      id: 'basemap',
      name: 'Basemap',
      type: 'basemap',
      visible: true,
      opacity: 1,
      metadata: {
        source: 'OpenStreetMap',
        lastUpdated: new Date().toISOString(),
        crs: 'EPSG:4326',
      },
    },
  ],
  wells: [],
  seismicLines: [],
  prospects: [],
  selectedCoordinate: null,
  selectedLine: null,
  selectedWell: null,
  selectedProspect: null,
  cursor: null,
  governance: initialGovernance,
  groundingStatus: {
    f4Clarity: {
      datum: 'grey',
      scale: 'grey',
      tie: 'grey',
    },
    f7Humility: {
      candidatesAvailable: 0,
      singleModelCollapsed: false,
    },
  },
  uncertainty: {
    quantified: false,
    sources: [],
  },
  geoxConnected: false,
  geoxUrl: 'https://geoxarifOS.fastmcp.app',
};

// Store interface
interface GEOXStore extends GEOXState {
  setActiveTab: (tab: Tab) => void;
  setViewMode: (mode: ViewMode) => void;
  selectCoordinate: (coord: Coordinate | null) => void;
  selectLine: (lineId: string | null) => void;
  selectWell: (wellId: string | null) => void;
  selectProspect: (prospectId: string | null) => void;
  syncCursor: (cursor: CursorState) => void;
  updateFloorStatus: (floorId: FloorId, status: FloorStatus, message?: string) => void;
  updateGroundingStatus: (update: Partial<GEOXState['groundingStatus']>) => void;
  setGEOXConnected: (connected: boolean) => void;
  setGEOXUrl: (url: string) => void;
  toggleLayer: (layerId: string) => void;
  setLayerOpacity: (layerId: string, opacity: number) => void;
  resetGovernance: () => void;
  getOverallStatus: () => FloorStatus;
}

// Helper function
function calculateOverallStatus(governance: GovernanceState): FloorStatus {
  const floors = Object.values(governance.floors);
  const hardFloors = floors.filter(f => f.type === 'hard');
  
  if (hardFloors.some(f => f.status === 'red')) return 'red';
  if (floors.some(f => f.status === 'red')) return 'red';
  if (floors.some(f => f.status === 'amber')) return 'amber';
  if (floors.every(f => f.status === 'green')) return 'green';
  return 'grey';
}

// Create store
export const useGEOXStore = create<GEOXStore>()(
  immer(
    persist(
      (set, get) => ({
        ...initialState,

        setActiveTab: (tab) => set((state) => { state.activeTab = tab; }),
        setViewMode: (mode) => set((state) => { state.viewMode = mode; }),
        
        selectCoordinate: (coord) => set((state) => {
          state.selectedCoordinate = coord;
        }),

        selectLine: (lineId) => set((state) => { state.selectedLine = lineId; }),
        selectWell: (wellId) => set((state) => { state.selectedWell = wellId; }),
        selectProspect: (prospectId) => set((state) => { state.selectedProspect = prospectId; }),

        syncCursor: (cursor) => set((state) => { state.cursor = cursor; }),

        updateFloorStatus: (floorId, status, message) => set((state) => {
          state.governance.floors[floorId].status = status;
          if (message) state.governance.floors[floorId].message = message;
          state.governance.overallStatus = calculateOverallStatus(state.governance);
        }),

        updateGroundingStatus: (update) => set((state) => {
          Object.assign(state.groundingStatus, update);
          const { datum, scale, tie } = state.groundingStatus.f4Clarity;
          if (datum === 'red' || scale === 'red' || tie === 'red') {
            state.governance.floors.F4.status = 'red';
            state.governance.floors.F4.message = 'Measurement tools disabled — insufficient grounding';
          } else if (datum === 'amber' || scale === 'amber' || tie === 'amber') {
            state.governance.floors.F4.status = 'amber';
            state.governance.floors.F4.message = 'Interpretive mode — verify scale before measurement';
          } else if (datum === 'green' && scale === 'green' && tie === 'green') {
            state.governance.floors.F4.status = 'green';
            state.governance.floors.F4.message = 'Grounding verified';
          }
        }),

        resetGovernance: () => set((state) => {
          state.governance = initialGovernance;
          state.governance.sessionId = typeof crypto !== 'undefined' ? crypto.randomUUID() : 'session-' + Date.now();
          state.governance.timestamp = new Date().toISOString();
        }),

        getOverallStatus: () => calculateOverallStatus(get().governance),

        setGEOXConnected: (connected) => set((state) => { state.geoxConnected = connected; }),
        setGEOXUrl: (url) => set((state) => { state.geoxUrl = url; }),

        toggleLayer: (layerId) => set((state) => {
          const layer = state.layers.find(l => l.id === layerId);
          if (layer) layer.visible = !layer.visible;
        }),

        setLayerOpacity: (layerId, opacity) => set((state) => {
          const layer = state.layers.find(l => l.id === layerId);
          if (layer) layer.opacity = opacity;
        }),
      }),
      {
        name: 'geox-gui-storage',
        partialize: (state) => ({
          panelConfig: state.panelConfig,
          geoxUrl: state.geoxUrl,
          layers: state.layers,
        }),
      }
    )
  )
);

// Selectors
export const useActiveTab = () => useGEOXStore((state) => state.activeTab);
export const useGovernance = () => useGEOXStore((state) => state.governance);
export const useFloorStatus = (floorId: FloorId) => useGEOXStore((state) => state.governance.floors[floorId]);
export const useGEOXConnected = () => useGEOXStore((state) => state.geoxConnected);
export const useSelectedCoordinate = () => useGEOXStore((state) => state.selectedCoordinate);