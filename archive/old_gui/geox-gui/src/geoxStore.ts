/**
 * GEOX Store — Physics9 Substrate State
 * DITEMPA BUKAN DIBERI
 */

import { AppId, SubstrateId, SUBSTRATES } from './types';

export interface GeoxState {
  // 3 App Shells
  activeApp: AppId;
  
  // 9 Substrates
  activeSubstrate: SubstrateId;
  substrates: {
    [key in SubstrateId]: {
      active: boolean;
      data: unknown;
      evidence_id: string | null;
      lastUpdated: string | null;
    };
  };
  
  // Constitutional state (arifOS Domain)
  verdict: '888_SEAL' | '888_QUALIFY' | '888_HOLD' | '888_VOID' | null;
  authority_level: number;
  
  // Meta
  seal: string;
  version: string;
}

export const GEOX_STORE_INITIAL: GeoxState = {
  activeApp: 'x1d',
  activeSubstrate: 'lithos',
  
  substrates: {
    lithos: { active: true, data: null, evidence_id: null, lastUpdated: null },
    pore: { active: false, data: null, evidence_id: null, lastUpdated: null },
    fluid: { active: false, data: null, lastUpdated: null, lastUpdated: null },
    strata: { active: false, data: null, evidence_id: null, lastUpdated: null },
    break: { active: false, data: null, evidence_id: null, lastUpdated: null },
    elastic: { active: false, data: null, evidence_id: null, lastUpdated: null },
    kinetic: { active: false, data: null, evidence_id: null, lastUpdated: null },
    stress: { active: false, data: null, evidence_id: null, lastUpdated: null },
    flow: { active: false, data: null, evidence_id: null, lastUpdated: null },
  },
  
  verdict: null,
  authority_level: 1,
  
  seal: 'DITEMPA BUKAN DIBERI',
  version: '2.1.0' // Physics9 Seal version
};

// Actions
export function setActiveApp(state: GeoxState, appId: AppId): GeoxState {
  return { ...state, activeApp: appId };
}

export function setActiveSubstrate(state: GeoxState, substrateId: SubstrateId): GeoxState {
  return {
    ...state,
    activeSubstrate: substrateId,
    activeApp: SUBSTRATES[substrateId].app, // Auto-switching apps based on substrate selection
    substrates: {
      ...state.substrates,
      [substrateId]: { ...state.substrates[substrateId], active: true }
    }
  };
}

export function setVerdict(state: GeoxState, verdict: GeoxState['verdict']): GeoxState {
  return { ...state, verdict };
}

export default GEOX_STORE_INITIAL;