import { useState, useCallback } from 'react';
import { useGEOXStore } from '../store/geoxStore';

export type ClaimState = 'draft' | 'pending_review' | 'attested';

export interface GeologicalClaim {
  id: string;
  type: 'horizon' | 'fault' | 'correlation' | 'reservoir_boundary';
  state: ClaimState;
  createdAt: string;
  payload: Record<string, unknown>;
  receiptHash?: string;  // NOT authority — only evidence
  attestationRef?: string; // VAULT999 ref after real SEAL
}

export function useGeologicalClaim(claimType: GeologicalClaim['type']) {
  const { updateFloorStatus } = useGEOXStore();
  const [claim, setClaim] = useState<GeologicalClaim>({
    id: `${claimType}-${Date.now()}`,
    type: claimType,
    state: 'draft',
    createdAt: new Date().toISOString(),
    payload: {},
  });

  const toDraft = useCallback((payload: Record<string, unknown>) => {
    setClaim((prev) => ({ ...prev, payload, state: 'draft' }));
    updateFloorStatus('F1', 'amber', 'DRAFT: reversible, local state only');
  }, [updateFloorStatus]);

  const requestReview = useCallback(() => {
    setClaim((prev) => ({ ...prev, state: 'pending_review' }));
    updateFloorStatus('F11', 'amber', 'PENDING REVIEW: canvas locked (F1 halt)');
  }, [updateFloorStatus]);

  const attest = useCallback((attestationRef: string) => {
    setClaim((prev) => ({
      ...prev,
      state: 'attested',
      attestationRef,
    }));
    updateFloorStatus('F13', 'green', `ATTESTED: ${attestationRef} — VAULT999`);
  }, [updateFloorStatus]);

  return { claim, toDraft, requestReview, attest };
}