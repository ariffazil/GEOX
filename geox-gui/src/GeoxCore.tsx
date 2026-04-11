/**
 * GeoxCore — GEOX Earth Intelligence Core (000-1249)
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 * 
 * Complete 5-domain dimensional architecture with AGI Terminal
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Layers, Box, Terminal, Shield, Zap, Target, 
  Cpu, Database, Clock, Globe, Network, Settings,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { DomainVoid } from './domains/DomainVoid';
import { Domain1D } from './domains/Domain1D';
import { Domain2D } from './domains/Domain2D';
import { Domain3D } from './domains/Domain3D';
import { DomainLEM } from './domains/DomainLEM';
import './styles/designSystem.css';

const Badge: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = "amber" }) => {
  const colors: Record<string, string> = {
    amber: "border-amber-500/30 text-amber-500 bg-amber-500/10",
    emerald: "border-emerald-500/30 text-emerald-500 bg-emerald-500/10",
    slate: "border-slate-500/30 text-slate-400 bg-slate-500/10",
    cyan: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
  };
  return (
    <span className={`px-1.5 py-0.5 text-[10px] font-mono border rounded uppercase tracking-wider ${colors[color]}`}>
      {children}
    </span>
  );
};

const useGeminiAPI = () => {
  const [isLoading, setIsLoading] = useState(false);
  const generate = async (prompt: string): Promise<string> => {
    setIsLoading(true);
    await new Promise(r => setTimeout(r, 1000));
    setIsLoading(false);
    return `ACKNOWLEDGED. Processing: "${prompt.substring(0, 50)}..." [GEOX AGI v2026.04.11]`;
  };
  return { generate, isLoading };
};

export const GeoxCore: React.FC = () => {
  const [activeDomain, setActiveDomain] = useState('void');
  const [time, setTime] = useState('');
  const { generate, isLoading } = useGeminiAPI();
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalLog, setTerminalLog] = useState([
    { sender: 'sys', text: '> CANON_9 Initialized...' },
    { sender: 'sys', text: '> Inverse Mapping Ready...' },
    { sender: 'sys', text: '> 888 Judge Acknowledged.' }
  ]);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const int = setInterval(() => {
      const d = new Date();
      setTime(`${d.getUTCHours().toString().padStart(2,'0')}${d.getUTCMinutes().toString().padStart(2,'0')}Z`);
    }, 1000);
    return () => clearInterval(int);
  }, []);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLog, isLoading]);

  const handleTerminalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!terminalInput.trim() || isLoading) return;

    const userText = terminalInput.trim();
    setTerminalInput('');
    setTerminalLog(prev => [...prev, { sender: 'user', text: `> USER: ${userText}` }]);

    const response = await generate(userText);
    setTerminalLog(prev => [...prev, { sender: 'geox', text: `> GEOX: ${response}` }]);
  };

  const domains = [
    { id: 'void', label: 'VOID [000-249]', icon: Activity },
    { id: '1d', label: '1D_WELL [250-499]', icon: Target },
    { id: '2d', label: '2D_SEIS [500-749]', icon: Layers },
    { id: '3d', label: '3D_META [750-999]', icon: Box },
    { id: 'lem', label: 'LEM_METABOLIZER', icon: Network },
  ];

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden bg-[#0A0C0E] text-slate-200">
      <header className="h-12 border-b border-gray-800 bg-black/50 flex items-center justify-between px-4 z-10 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-amber-500" />
            <h1 className="font-bold tracking-[0.2em] text-sm">GEOX // CORE</h1>
          </div>
          <div className="h-4 w-px bg-gray-800" />
          <div className="hidden md:flex items-center gap-3 text-[10px] font-mono">
            <div className="flex items-center gap-1 text-emerald-500">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>ARIF_OS LINKED</span>
            </div>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400">ΔS: <span className="text-emerald-400">-0.12</span></span>
            <span className="text-gray-400">Ω₀: <span className="text-amber-400">0.04</span></span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="hidden md:flex gap-1">
            <Badge color="cyan">CANON_9 LOCKED</Badge>
            <Badge color="slate">F9: ANTI-HANTU</Badge>
            <Badge color="emerald">F11: COMMAND AUTH</Badge>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-gray-900 border border-gray-700 rounded-sm">
            <Shield className="w-3 h-3 text-amber-500" />
            <span className="text-[11px] font-mono text-amber-500 font-bold tracking-widest">888_JUDGE</span>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-16 md:w-64 border-r border-gray-800 bg-black/30 flex flex-col shrink-0 z-10 overflow-hidden">
          <div className="flex-1 py-4 flex flex-col gap-2 overflow-y-auto">
            {domains.map((d) => {
              const Icon = d.icon;
              const isActive = activeDomain === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setActiveDomain(d.id)}
                  className={`flex items-center gap-3 px-4 py-3 border-l-2 transition-all shrink-0 ${
                    isActive 
                      ? 'border-amber-500 bg-amber-500/10 text-amber-500 glow-amber' 
                      : 'border-transparent text-gray-500 hover:bg-gray-800/50 hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-5 h-5 shrink-0" />
                  <span className="text-xs font-mono tracking-wider hidden md:block text-left">{d.label}</span>
                </button>
              );
            })}
          </div>
          
          {/* AGI Terminal */}
          <div className="h-64 border-t border-gray-800 p-4 flex flex-col gap-2 bg-[#050608] hidden md:flex shrink-0">
            <div className="text-[10px] font-mono text-gray-600 flex items-center gap-2 border-b border-gray-800 pb-2">
              <Zap className="w-3 h-3 text-amber-500" /> AGI TERMINAL
            </div>
            
            <div className="flex-1 overflow-y-auto text-[9px] font-mono flex flex-col gap-1 pr-1">
              {terminalLog.map((log, i) => (
                <div key={i} className={`leading-relaxed ${
                  log.sender === 'user' ? 'text-gray-400' : 
                  log.sender === 'geox' ? 'text-amber-500 glow-amber' : 'text-emerald-700'
                }`}>
                  {log.text}
                </div>
              ))}
              {isLoading && <div className="text-purple-500 animate-pulse">{'>'} SYNTHESIZING...</div>}
              <div ref={terminalEndRef} />
            </div>

            <form onSubmit={handleTerminalSubmit} className="mt-auto flex items-center gap-2 border border-gray-800 bg-black/60 p-1.5 focus-within:border-amber-500/50 transition-colors">
              <Terminal className="w-3 h-3 text-gray-500 shrink-0" />
              <input
                type="text"
                value={terminalInput}
                onChange={(e) => setTerminalInput(e.target.value)}
                placeholder="✨ QUERY AGI..."
                disabled={isLoading}
                className="bg-transparent border-none outline-none text-[9px] font-mono text-amber-100 w-full placeholder-gray-700 disabled:opacity-50"
              />
            </form>
            <div className="flex items-center gap-2 mt-1">
               <Clock className="w-3 h-3 text-gray-600"/>
               <span className="text-[9px] font-mono text-gray-500">{time}</span>
            </div>
          </div>
        </aside>

        <main className="flex-1 relative overflow-hidden bg-gradient-to-br from-[#0A0C0E] to-[#0d1117]">
          {activeDomain === 'void' && <DomainVoid />}
          {activeDomain === '1d' && <Domain1D />}
          {activeDomain === '2d' && <Domain2D />}
          {activeDomain === '3d' && <Domain3D />}
          {activeDomain === 'lem' && <DomainLEM />}
        </main>
      </div>

      <footer className="h-8 border-t border-gray-800 bg-[#050608] flex items-center justify-between px-4 shrink-0 z-10">
        <span className="text-[9px] font-mono text-gray-600 tracking-[0.3em]">
          GEOX_CORE_v2026.04.11 // THERMODYNAMIC STATE ENGINE
        </span>
        <span className="text-[9px] font-mono font-bold text-amber-600/80 tracking-widest uppercase">
          DITEMPA BUKAN DIBERI // 999_SEAL
        </span>
      </footer>
    </div>
  );
};

export default GeoxCore;
