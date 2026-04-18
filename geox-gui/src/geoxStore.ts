/**
 * GEOX Store — Seven Dimensional State
 * DITEMPA BUKAN DIBERI
 */

import { DimensionId, DIMENSIONS } from './types';

export interface GeoxState {
  // Seven dimensions
  activeDimension: DimensionId;
  dimensions: {
    [key in DimensionId]: {
      active: boolean;
      data: unknown;
      lastUpdated: string | null;
    };
  };
  
  // Scene state (888_JUDGE)
  scene: {
    prospect_id: string | null;
    well_ids: string[];
    section_id: string | null;
    earth3d_volume_id: string | null;
    time4d_scenario_id: string | null;
    map_id: string | null;
  };
  
  // Constitutional state
  verdict: '888_SEAL' | '888_QUALIFY' | '888_HOLD' | '888_VOID' | null;
  authority_level: number;
  
  // Meta
  seal: string;
  version: string;
}

export const GEOX_STORE_INITIAL: GeoxState = {
  activeDimension: 'prospect',
  
  dimensions: {
    prospect: { active: true, data: null, lastUpdated: null },
    well: { active: false, data: null, lastUpdated: null },
    section: { active: false, data: null, lastUpdated: null },
    earth3d: { active: false, data: null, lastUpdated: null },
    time4d: { active: false, data: null, lastUpdated: null },
    physics: { active: false, data: null, lastUpdated: null },
    map: { active: false, data: null, lastUpdated: null }
  },
  
  scene: {
    prospect_id: null,
    well_ids: [],
    section_id: null,
    earth3d_volume_id: null,
    time4d_scenario_id: null,
    map_id: null
  },
  
  verdict: null,
  authority_level: 1,
  
  seal: 'DITEMPA BUKAN DIBERI',
  version: '2026.04.11'
};

// Actions
export function setActiveDimension(state: GeoxState, dimension: DimensionId): GeoxState {
  return {
    ...state,
    activeDimension: dimension,
    dimensions: {
      ...state.dimensions,
      [dimension]: { ...state.dimensions[dimension], active: true }
    }
  };
}

export function setSceneProspect(state: GeoxState, prospectId: string): GeoxState {
  return {
    ...state,
    scene: { ...state.scene, prospect_id: prospectId }
  };
}

export function setVerdict(state: GeoxState, verdict: GeoxState['verdict']): GeoxState {
  return { ...state, verdict };
}

export function setAuthorityLevel(state: GeoxState, level: number): GeoxState {
  return { ...state, authority_level: level };
}

export default GEOX_STORE_INITIAL;