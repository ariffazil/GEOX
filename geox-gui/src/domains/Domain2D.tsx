/**
 * Domain2D — Seismic & Planar (500-749)
 * ═══════════════════════════════════════════════════════════════════════════════
 * Open Source Seismic Scale
 */

import React, { useState, useEffect, useRef } from 'react';
import { Layers, CheckCircle2, ScanFace, Globe, Zap, ChevronLeft, ChevronRight, Scan, Crosshair } from 'lucide-react';

const Badge: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = "amber" }) => {
  const colors: Record<string, string> = {
    amber: "border-amber-500/30 text-amber-500 bg-amber-500/10",
    cyan: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
    crimson: "border-red-500/30 text-red-500 bg-red-500/10",
    purple: "border-purple-500/30 text-purple-400 bg-purple-500/10",
    emerald: "border-emerald-500/30 text-emerald-500 bg-emerald-500/10",
  };
  return (
    <span className={`px-1.5 py-0.5 text-[10px] font-mono border rounded uppercase tracking-wider ${colors[color]}`}>
      {children}
    </span>
  );
};

const useGeminiAPI = () => {
  const [isLoading, setIsLoading] = useState(false);
  const generate = async (): Promise<string> => {
    setIsLoading(true);
    await new Promise(r => setTimeout(r, 1500));
    setIsLoading(false);
    return "STRUCTURAL INTERPRETATION: Major listric fault system identified with 150m displacement. Bright spot anomaly at fault hanging wall indicates potential hydrocarbon accumulation. Risk: Medium-High due to fault seal uncertainty.";
  };
  return { generate, isLoading };
};

export const Domain2D: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { generate, isLoading } = useGeminiAPI();
  const [gcpScanned, setGcpScanned] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [llmSeismic, setLlmSeismic] = useState('');
  const [viewStart, setViewStart] = useState(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.offsetWidth || 800;
    const h = canvas.offsetHeight || 600;
    canvas.width = w;
    canvas.height = h;

    const renderSeismic = () => {
      const imgData = ctx.createImageData(w, h);
      const data = imgData.data;

      const getHorizonDepth = (x: number, type: number) => {
        const nx = x / w;
        if (type === 1) return h * 0.3 + Math.sin(nx * 10) * 30 + nx * 50;
        if (type === 2) return h * 0.6 + Math.cos(nx * 8) * 40 - nx * 20;
        return h * 0.8 + Math.sin(nx * 5) * 20;
      };

      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          let fx = x;
          let fy = y;
          if (x > w * 0.4 && x < w * 0.6) {
            const faultDrop = (x - w * 0.4) * 0.5;
            fy -= faultDrop;
          }

          const d1 = fy - getHorizonDepth(fx, 1);
          const d2 = fy - getHorizonDepth(fx, 2);
          const wavelet = Math.sin(fy * 0.5) * Math.cos(fx * 0.05);
          const noise = (Math.random() - 0.5) * 0.5;
          let amplitude = wavelet + noise;
          if (Math.abs(d1) < 20) amplitude += Math.cos(d1 * 0.2) * 2.0;
          if (Math.abs(d2) < 30) amplitude -= Math.cos(d2 * 0.15) * 2.0;
          if (Math.abs(d1) < 15 && fx > w * 0.2 && fx < w * 0.35) amplitude += 3.0;

          let r = 20, g = 20, b = 20;
          if (amplitude > 1.0) { r = Math.min(255, 100 + amplitude * 50); }
          else if (amplitude < -1.0) { b = Math.min(255, 100 + Math.abs(amplitude) * 50); }
          else { const i = 50 + amplitude * 20; r = i; g = i; b = i; }

          const idx = (y * w + x) * 4;
          data[idx] = r; data[idx + 1] = g; data[idx + 2] = b; data[idx + 3] = 255;
        }
      }
      ctx.putImageData(imgData, 0, 0);

      if (gcpScanned) {
        ctx.beginPath();
        ctx.moveTo(w * 0.4, 0);
        ctx.lineTo(w * 0.6, h);
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.8)';
        ctx.lineWidth = 3;
        ctx.setLineDash([10, 5]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    };

    const drawGCP = (x: number, y: number, label: string) => {
      ctx.beginPath(); ctx.arc(x, y, 6, 0, 2 * Math.PI); ctx.fillStyle = '#06B6D4'; ctx.fill();
      ctx.beginPath(); ctx.moveTo(x - 12, y); ctx.lineTo(x + 12, y); ctx.moveTo(x, y - 12); ctx.lineTo(x, y + 12);
      ctx.strokeStyle = '#06B6D4'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = '#06B6D4'; ctx.font = 'bold 10px JetBrains Mono';
      ctx.shadowColor = 'black'; ctx.shadowBlur = 4;
      ctx.fillText(label, x + 10, y - 10);
      ctx.shadowBlur = 0;
    };

    renderSeismic();
    if (gcpScanned) {
      drawGCP(w * 0.1, h * 0.3, "GCP-1: H1 (1200ms)");
      drawGCP(w * 0.8, h * 0.6, "GCP-2: H2 (2400ms)");
      drawGCP(w * 0.5, h * 0.5, "FAULT");
    }
  }, [gcpScanned]);

  const triggerGCPScan = () => { 
    setIsScanning(true); 
    setTimeout(() => { setIsScanning(false); setGcpScanned(true); }, 2000); 
  };

  const handleSeismicAnalysis = async () => {
    const response = await generate();
    setLlmSeismic(response);
  };

  return (
    <div className="flex flex-col h-full gap-4 p-4">
      <div className="flex justify-between items-end mb-2 border-b border-gray-800 pb-2">
        <div>
          <h2 className="text-xl font-bold tracking-widest flex items-center gap-2">
            <Layers className="w-5 h-5 text-blue-500" /> THE 2D INTERFACE [500-749]
          </h2>
          <p className="text-xs text-gray-500 font-mono">SEISMIC VIEWER & SCALE-AWARE FORGE</p>
        </div>
        <div className="flex gap-2">
          {gcpScanned ? <Badge color="cyan">EARTH TRUE SCALE</Badge> : <Badge color="crimson">UNSCALED PIXELS</Badge>}
          <Badge color="purple">LLM: ONLINE</Badge>
          <Badge color="emerald">F8: GENIUS</Badge>
        </div>
      </div>

      <div className="flex-1 flex gap-4 overflow-hidden relative">
        <div className={`flex-1 glass-panel relative overflow-hidden flex flex-col ${isScanning ? 'gcp-active' : ''}`}>
          <div className="h-10 bg-black/60 border-b border-gray-800 flex items-center px-4 gap-4 justify-between">
            <div className="flex items-center gap-4">
              <button className="text-gray-400 hover:text-white transition-colors"><Crosshair size={16}/></button>
              <div className="h-4 w-px bg-gray-700 mx-2" />
              <span className="text-[10px] font-mono text-gray-500">RENDER: FULL WAVEFORM</span>
            </div>
            {gcpScanned && <span className="text-[10px] font-mono text-cyan-500 flex items-center gap-1"><Globe size={12}/> CRS: WGS84 UTM 50N</span>}
          </div>
          <div className="flex-1 relative bg-black">
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
            <div className="scanline" />
            {isScanning && <div className="radar-sweep" style={{ background: 'linear-gradient(to bottom, transparent, rgba(6, 182, 212, 0.2))', animationDuration: '2s' }} />}
            <div className="absolute left-0 top-0 bottom-0 w-12 border-r border-gray-800/50 bg-black/80 flex flex-col justify-between py-4 text-[9px] font-mono text-center items-center shadow-lg">
              {gcpScanned ? (
                <><span className="text-cyan-500 mt-2 font-bold">1000<br/>ms</span><span className="text-cyan-500 font-bold">2000<br/>ms</span><span className="text-cyan-500 mb-2 font-bold">3000<br/>ms</span></>
              ) : (
                <><span className="text-gray-600 mt-2">0<br/>px</span><span className="text-gray-600">300<br/>px</span><span className="text-gray-600 mb-2">600<br/>px</span></>
              )}
            </div>
          </div>
        </div>

        <div className="w-64 glass-panel p-4 flex flex-col gap-4">
          <div className="text-xs font-mono text-gray-500 border-b border-gray-800 pb-2 flex justify-between items-center">
            VISION INTELLIGENCE <ScanFace className="w-4 h-4 text-cyan-500" />
          </div>
          <button 
            onClick={triggerGCPScan} 
            disabled={isScanning || gcpScanned} 
            className={`w-full py-2 border text-[10px] font-mono uppercase transition-colors flex justify-center items-center gap-2 ${
              gcpScanned ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:bg-gray-800'
            }`}
          >
            {isScanning ? 'DETECTING...' : gcpScanned ? 
              <span className="flex items-center gap-2"><CheckCircle2 size={12}/> GCP NETWORK LOCKED</span> : 
              <span className="flex items-center gap-2"><ScanFace size={12}/> AUTO-DETECT GCPs</span>
            }
          </button>
          {gcpScanned && (
            <div className="mt-2 space-y-4">
              <div className="p-2 border border-purple-500/20 bg-purple-500/5 text-[9px] font-mono text-purple-300">
                <div className="flex items-center gap-1 mb-1"><Layers size={10}/> STRUCTURAL ELEMENTS</div>
                <div>- FAULT_A: LISTRIC DETECTED</div>
                <div>- DHI: BRIGHT SPOT AT H1</div>
              </div>
              <button 
                onClick={handleSeismicAnalysis} 
                disabled={isLoading} 
                className="w-full py-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 text-[10px] font-mono uppercase hover:bg-purple-500/20 transition-colors flex justify-center items-center gap-2 disabled:opacity-50"
              >
                {isLoading ? 'TRACING...' : '✨ ANALYZE STRUCTURAL TRAPS'}
              </button>
              {llmSeismic && <div className="mt-3 text-[11px] font-mono text-gray-300 leading-relaxed border-l-2 border-purple-500 pl-3">{llmSeismic}</div>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Domain2D;
