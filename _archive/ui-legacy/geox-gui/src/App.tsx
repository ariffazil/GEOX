import React from 'react';
import { MainLayoutForge } from './components/Layout/MainLayoutForge';
import { SessionGate } from './components/Cockpit/OperatorCockpit';
import { useGEOXStore } from './store/geoxStore';
import './App.css';

/**
 * GEOX Earth Intelligence Core — 000-999 Command Center
 * Phase 1: native React SPA with explicit domain wiring
 *
 * F13 SOVEREIGN GATE: No cockpit hydration without valid SCT token.
 * The mounting layer enforces a hard cryptographic auth boundary.
 * Anonymous actors see ONLY the SessionGate — never the cockpit.
 * DITEMPA BUKAN DIBERI ⚒️
 */
function App(): React.ReactElement {
  // F13 SOVEREIGN: read session identity from the store.
  // Only render MainLayoutForge if sessionToken is cryptographically present.
  const sessionToken = useGEOXStore((s) => s.sessionToken);

  if (!sessionToken || sessionToken.trim() === '') {
    return (
      <div className="app">
        <SessionGate
          onBound={(identity, status) => {
            // After a real SCT bind, the SessionGate calls back into the store.
            // The store's setSessionIdentity propagates to MainLayoutForge on next render.
            if (identity) {
              useGEOXStore.getState().setSessionIdentity(identity.sessionId, identity.actorId);
            }
          }}
        />
      </div>
    );
  }

  return (
    <div className="app">
      <MainLayoutForge />
    </div>
  );
}

export default App;
