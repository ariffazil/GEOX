# KIMI SWARM DIRECTIVE: GEOX DESIGN FORGE (000-999)

## MISSION IDENTITY: THE GEOX CORE
GEOX is not a visualization tool; it is a **Governed Earth Intelligence Engine**. It is the subsurface coprocessor for **arifOS**, designed to provide "Actionable Ground Truth" for the 888_JUDGE paradigm. The core philosophy is **"DITEMPA BUKAN DIBERI" (Forged, Not Given)**.

## ARCHITECTURAL SCOPE: 000-999 (VOID TO META-DIMENSIONAL)
You are tasked with forging the final interface manifest for the GEOX Command Center. Your design must scale across the following domains:

### 1. THE VOID (000-249): Decision & Risk
- **Focus**: Volumetrics, Economics, and 888_HOLD Governance.
- **Aesthetic**: Brutalist, forensic, high-contrast. The "Decision Manifold".
- **Interaction**: Stochastic model results, GCOS distribution curves, and constitutional floor validations.

### 2. THE 1D INTERFACE (250-499): Borehole Intelligence
- **Focus**: Well Context Desk & RATLAS.
- **Aesthetic**: Surgical precision. JetBrains Mono typography. High-density data strips.
- **Interaction**: LAS log comparisons, material calibration overlays, and probabilistic formation matching.

### 3. THE 2D INTERFACE (500-749): Planar Operations
- **Focus**: Seismic Viewer & Analog Forge.
- **Aesthetic**: Signal-centric. Vibrant spectral gradients. Scan-line overlays.
- **Interaction**: Real-time attribute generation (RMS, Sweetness), pixel-to-depth calibration, and automated GCP detection.

### 4. THE 3D/META DOMAIN (750-999): Volume & Unified Intel
- **Focus**: Basin Explorer & 3D Volume Interpretation.
- **Aesthetic**: Immersive, holographic, meta-dimensional.
- **Interaction**: GemPy structural meshes, regional stratigraphic hydration via Macrostrat, and unified manifold views where 1D/2D/3D intersect logically.

## DESIGN PHILOSOPHY & UI REQUIREMENTS
- **Elite Aesthetics**: Modern dark mode (#0A0C0E), glassmorphism, accent amber (#F59E0B), and emerald status indicators (#10B981).
- **Zero Theater**: Every UI element must represent real data or governing logic. No decorative generic charts.
- **Typography**: Inter for UI, JetBrains Mono for data/coordinates.
- **Micro-animations**: Subtle transitions for context switching and data hydration.
- **Consistency**: Unified headers, constitutional floor badges (F1, F2, F7, F11, etc.), and system status telemetry.

## YOUR TASK: FORGE THE MANIFEST
1.  **Refine the Core UI**: Standardize the shared component library across all apps.
2.  **Hydrate with Complexity**: Ensure each app (Well Context, Seismic, Basin, Forge, Risk) feels like a professional-grade instrument.
3.  **Seal the Interface**: Implement the final responsive layout, iconography, and spectral themes that define the v1.0.0 GEOX "Heavy Witness" state.

## GOLDEN AESTHETIC & INTELLIGENCE MANIFEST (CANONICAL DNA)
The following React manifest serves as the **Canonical Specification** for both UI/UX and Intelligence Integration. Use its styling logic and LLM-coprocessor patterns as the ground truth.

```jsx
// --- CANONICAL STYLING & INTELLIGENCE MANIFEST ---
import React, { useState, useEffect, useRef } from 'react';

// --- INTELLIGENCE FLOOR: useGeminiAPI ---
// All geological interpretations and decision verdicts must flow through this bridge.
const useGeminiAPI = () => {
  const [isLoading, setIsLoading] = useState(false);
  const generate = async (prompt, systemInstruction) => {
    setIsLoading(true);
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=YOUR_API_KEY`;
    const payload = {
      contents: [{ parts: [{ text: prompt }] }],
      systemInstruction: { parts: [{ text: systemInstruction || "You are an elite, brutalist geological AI assistant." }] }
    };
    // Fetch logic with exponential backoff...
  };
  return { generate, isLoading };
};

const StyleInject = () => (
  <style dangerouslySetInnerHTML={{ __html: `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
    :root {
      --bg-void: #0A0C0E; --accent-amber: #F59E0B; --accent-emerald: #10B981; --accent-purple: #8B5CF6;
      --glass-border: rgba(255, 255, 255, 0.05); --glass-bg: rgba(20, 24, 28, 0.6);
    }
    body { background-color: var(--bg-void); color: #E2E8F0; font-family: 'Inter', sans-serif; }
    .glass-panel { background: var(--glass-bg); backdrop-filter: blur(12px); border: 1px solid var(--glass-border); }
    .scanline { position: absolute; top:0; left:0; right:0; bottom:0; background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.1)); background-size: 100% 4px; pointer-events: none; opacity: 0.3; }
    @keyframes sweep { 0% { transform: translateY(-100%); } 100% { transform: translateY(1000%); } }
    .radar-sweep { position: absolute; top:0; left:0; width:100%; height:10%; background: linear-gradient(to bottom, transparent, rgba(16, 185, 129, 0.1)); animation: sweep 8s linear infinite; pointer-events: none; }
  `}} />
);

// [Domain Execution Highlights]
// 1. DomainVoid: Monte Carlo P90/P50/P10 analysis + LGG GCOS Verdicts.
// 2. Domain1D: Automated Petrophysical Interpretation via SVG log-pattern analysis.
// 3. Domain2D: Attribute Synthesis (RMS, Coherence mapping).
// 4. Domain3D: Volumetric Mesh Integration & Basin Hydration.
```

## SEAL


DITEMPA BUKAN DIBERI. Proceed with the Design Forge.

999_SEAL.
