/**
 * Domain3D — Volume & Basin (750-999)
 * ═══════════════════════════════════════════════════════════════════════════════
 * Macrostrat True Earth
 */

import React, { useState } from 'react';
import { Box, Globe, BadgeCheck, Zap } from 'lucide-react';

const Badge: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = "emerald" }) => {
  const colors: Record<string, string> = {
    cyan: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
    emerald: "border-emerald-500/30 text-emerald-500 bg-emerald-500/10",
    purple: "border-purple-500/30 text-purple-400 bg-purple-500/10",
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
    return "MALAY BASIN SYNTHESIS: Tertiary rift basin with syn-rift clastic reservoirs and post-rift carbonate platforms. Petroleum system proven with multiple field discoveries. Key play: Miocene deepwater turbidites. Risk: Moderate charge uncertainty in distal areas.";
  };
  return { generate, isLoading };
};

export const Domain3D: React.FC = () => {
  const { generate, isLoading } = useGeminiAPI();
  const [llmBasin, setLlmBasin] = useState('');

  const handleBasinSynthesis = async () => {
    const response = await generate();
    setLlmBasin(response);
  };

  return (
    <div className="flex flex-col h-full gap-4 p-4">
      <div className="flex justify-between items-end mb-2 border-b border-gray-800 pb-2">
        <div>
          <h2 className="text-xl font-bold tracking-widest flex items-center gap-2">
            <Box className="w-5 h-5 text-purple-500" /> THE META DOMAIN [750-999]
          </h2>
          <p className="text-xs text-gray-500 font-mono">MACROSTRAT EARTH ENGINE & 4D CHRONO-UNIFIED INTEL</p>
        </div>
        <div className="flex gap-2">
          <Badge color="cyan">EARTH TRUE SCALE</Badge>
          <Badge color="emerald">F3: TRI-WITNESS (0.98)</Badge>
        </div>
      </div>

      <div className="flex-1 flex gap-4 overflow-hidden relative">
        <div className="flex-1 glass-panel relative overflow-hidden bg-[#050608]">
          <div className="absolute top-2 left-2 z-20 flex items-center gap-2 px-3 py-1.5 bg-black/80 border border-purple-500/30 text-purple-400 text-[10px] font-mono shadow-lg backdrop-blur-md rounded-sm">
            <Globe className="w-3 h-3 animate-pulse" /> LIVE MACROSTRAT TELEMETRY // LNG: 103.0 LAT: 5.0 (MALAY BASIN)
          </div>
          <div className="scanline z-10 pointer-events-none" />
          <iframe 
            src="https://macrostrat.org/map/#/z=5.0/x=103.0/y=5.0/bedrock/lines/" 
            title="Macrostrat Reality Bridge"
            className="absolute inset-0 w-full h-full border-0 opacity-80 mix-blend-screen"
            style={{ filter: 'invert(1) hue-rotate(180deg) contrast(1.2)' }}
          />
          <div className="absolute inset-0 shadow-[inset_0_0_100px_rgba(10,12,14,1)] pointer-events-none z-10" />
        </div>

        <div className="w-64 glass-panel p-4 flex flex-col gap-4 z-20">
          <div className="text-xs font-mono text-gray-500 border-b border-gray-800 pb-2 flex justify-between items-center">
            BASIN INTELLIGENCE <Globe className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-[10px] font-mono text-gray-400 leading-relaxed">
            Live telemetry bridged to Macrostrat. Earth True Scale locked. Initialize LLM coprocessor.
          </div>
          <button 
            onClick={handleBasinSynthesis} 
            disabled={isLoading} 
            className="w-full py-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 text-[10px] font-mono uppercase hover:bg-purple-500/20 transition-colors flex justify-center items-center gap-2 disabled:opacity-50"
          >
            {isLoading ? 'SYNTHESIZING...' : '✨ GENERATE BASIN REPORT'}
          </button>
          {llmBasin && <div className="flex-1 overflow-y-auto mt-2 text-[11px] font-mono text-gray-300 leading-relaxed border-l-2 border-purple-500 pl-3">{llmBasin}</div>}
        </div>
      </div>
    </div>
  );
};

export default Domain3D;
