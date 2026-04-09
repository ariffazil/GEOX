/**
 * GEOX GUI App — DITEMPA BUKAN DIBERI
 * 
 * Main application component for GEOX Earth Witness.
 */

import { useEffect } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { useGEOXStore } from './store/geoxStore';
import { useGeoxBridge } from './hooks/useGeoxBridge';
import './App.css';

// App component
function App() {
  const { setGEOXConnected, geoxUrl } = useGEOXStore();
  const { sendUiAction } = useGeoxBridge();

  // Check GEOX connection on mount
  useEffect(() => {
    // Initial UI event to host
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
  }, [geoxUrl, setGEOXConnected]);

  return (
    <div className="app">
      <MainLayout />
    </div>
  );
}

export default App;