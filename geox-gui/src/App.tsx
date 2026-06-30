/**
 * GEOX GUI App — DITEMPA BUKAN DIBERI
 *
 * Main application component for GEOX Earth Witness.
 * Landing page first, then cockpit on demand.
 */

import { useState, useEffect } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { LandingPage } from './components/LandingPage/LandingPage';
import { useGEOXStore } from './store/geoxStore';
import { useGeoxBridge } from './hooks/useGeoxBridge';
import { MainLayoutForge } from './components/Layout/MainLayoutForge';
import { X1D_Shell } from './apps/x1d/X1D_Shell';
import { X2D_Shell } from './apps/x2d/X2D_Shell';
import { X3D_Shell } from './apps/x3d/X3D_Shell';
import './App.css';

type AppMode = 'default' | 'forge' | 'x1d' | 'x2d' | 'x3d';

function useAppMode(): AppMode {
  const [mode, setMode] = useState<AppMode>(() => {
    if (typeof window === 'undefined') return 'default';
    const params = new URLSearchParams(window.location.search);
    const x = params.get('x');
    if (x === '1d') return 'x1d';
    if (x === '2d') return 'x2d';
    if (x === '3d') return 'x3d';
    if (params.get('forge') === '1' || localStorage.getItem('geox-forge-mode') === '1') return 'forge';
    return 'default';
  });

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.shiftKey && e.key === 'F') {
        setMode((prev) => {
          const next = prev === 'forge' ? 'default' : 'forge';
          localStorage.setItem('geox-forge-mode', next === 'forge' ? '1' : '0');
          return next;
        });
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return mode;
}

function App() {
  const [showCockpit, setShowCockpit] = useState(false);
  const { setGEOXConnected, geoxUrl } = useGEOXStore();
  const appMode = useAppMode();
  const { sendUiAction } = useGeoxBridge();

  // Check GEOX connection on mount
  useEffect(() => {
    sendUiAction('app.mounted', { timestamp: new Date().toISOString() });

    const checkConnection = async () => {
      try {
        const response = await fetch(`${geoxUrl}/health`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });

        if (response.ok) {
          setGEOXConnected(true);
          console.log('[GEOX] Connected to:', geoxUrl);
        } else {
          setGEOXConnected(false);
          console.warn('[GEOX] Connection failed');
        }
      } catch (error) {
        setGEOXConnected(false);
        console.warn('[GEOX] Connection error:', error);
      }
    };

    checkConnection();

    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [geoxUrl, setGEOXConnected, sendUiAction]);

  if (appMode === 'forge') {
    return (
      <div className="app">
        <MainLayoutForge />
      </div>
    );
  }

  if (appMode === 'x1d') return <X1D_Shell />;
  if (appMode === 'x2d') return <X2D_Shell />;
  if (appMode === 'x3d') return <X3D_Shell />;

  return (
    <div className="app">
      {showCockpit ? (
        <MainLayout />
      ) : (
        <LandingPage onEnterCockpit={() => setShowCockpit(true)} />
      )}
    </div>
  );
}

export default App;
