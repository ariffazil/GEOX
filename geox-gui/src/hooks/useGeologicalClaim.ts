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
  attestedAt?: string;     // ISO timestamp of attestation
  isStale?: boolean;       // true if data source has changed since last fetch
  lastFetchedAt?: string;  // ISO timestamp of last data fetch
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
    // STALE structural lock: cannot promote stale nodes
    if (claim.isStale) {
      updateFloorStatus('F1', 'red', 'BLOCKED: Stale node. Refresh required before promotion.');
      return; // Block the promotion
    }
    setClaim((prev) => ({ ...prev, payload, state: 'draft', isStale: false }));
    updateFloorStatus('F1', 'amber', 'DRAFT: reversible, local state only');
  }, [updateFloorStatus, claim.isStale]);

  const requestReview = useCallback(() => {
    setClaim((prev) => ({ ...prev, state: 'pending_review' }));
    updateFloorStatus('F11', 'amber', 'PENDING REVIEW: canvas locked (F1 halt)');
  }, [updateFloorStatus]);

  const attest = useCallback(async (payload: Record<string, unknown>) => {
    setClaim((prev) => ({ ...prev, state: 'pending_review' }));
    updateFloorStatus('F13', 'amber', 'Attestation intent sent to arifOS kernel…');

    try {
      // Route through arifOS, not directly to VAULT999
      // GEOX's maximum is QUALIFIED_CANDIDATE, not SEAL
      const response = await fetch('/api/attest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool: 'arif_seal',
          arguments: {
            subject: claim.type,
            payload,
            source: 'geox_gui',
          },
        }),
      });

      const result = await response.json();
      if (result.receipt_id) {
        setClaim((prev) => ({
          ...prev,
          state: 'attested',
          attestationRef: result.receipt_id,
          attestedAt: new Date().toISOString(),
        }));
        updateFloorStatus('F13', 'green', `ATTESTED: ${result.receipt_id} — VAULT999`);
      } else {
        updateFloorStatus('F13', 'red', `Attestation rejected: ${result.error}`);
      }
    } catch (err) {
      updateFloorStatus('F13', 'red', `Attestation failed: ${err}`);
    }
  }, [updateFloorStatus, claim.type]);

  const resetToReality = useCallback(() => {
    setClaim((prev) => ({
      ...prev,
      state: 'draft',
      attestationRef: undefined,
      attestedAt: undefined,
    }));
    updateFloorStatus('F1', 'amber', 'Reset to Reality — local state only');
  }, [updateFloorStatus]);

  return { claim, toDraft, requestReview, attest, resetToReality };
}