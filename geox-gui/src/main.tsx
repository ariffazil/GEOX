/**
 * GEOX GUI Main Entry — GeoxCore Edition
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import GeoxCore from './GeoxCore';
import './styles/designSystem.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <GeoxCore />
  </React.StrictMode>
);
