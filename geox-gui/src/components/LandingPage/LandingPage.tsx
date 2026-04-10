/**
 * GEOX Landing Page
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Clean, focused entry point for GEOX Earth Witness.
 * Not a cockpit — a doorway. The cockpit is behind the "Enter" button.
 */

import React, { useState, useEffect } from 'react';
import {
  Globe, Activity, AlignLeft, Image as ImageIcon,
  Target, Shield, ChevronRight, ExternalLink,
  Zap, Layers, BarChart3, Radio, ArrowRight, Server,
  BookOpen, Lock, Eye, Cpu, MapPin
} from 'lucide-react';
import { useGEOXStore } from '../../store/geoxStore';

interface LandingPageProps {
  onEnterCockpit: () => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hero Section
// ─────────────────────────────────────────────────────────────────────────────

const Hero: React.FC<{ onEnterCockpit: () => void }> = ({ onEnterCockpit }) => {
  const geoxConnected = useGEOXStore((state) => state.geoxConnected);

  return (
    <section className="relative min-h-[70vh] flex flex-col items-center justify-center px-6 py-20 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent" />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }}
      />

      <div className="relative z-10 text-center max-w-4xl mx-auto">
        {/* Status badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8">
          <div className={`w-2 h-2 rounded-full ${geoxConnected ? 'bg-green-500 animate-pulse' : 'bg-amber-500'} shadow-[0_0_8px_currentColor]`} />
          <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
            {geoxConnected ? 'System Online — v0.6.1' : 'Connecting...'}
          </span>
        </div>

        {/* Main title */}
        <h1 className="text-5xl md:text-7xl font-black text-white tracking-tight mb-4 leading-tight">
          GEOX <span className="text-blue-400">Earth Witness</span>
        </h1>

        <p className="text-lg md:text-xl text-slate-400 mb-2 font-mono tracking-widest uppercase text-[10px] md:text-xs">
          DITEMPA BUKAN DIBERI — Forged, Not Given
        </p>

        <p className="text-lg text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed">
          A constitutional geoscience platform that uses multi-agent architecture
          and tri-witness consensus to deliver verified geological interpretations.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onEnterCockpit}
            className="group flex items-center gap-3 px-8 py-4 bg-blue-500 hover:bg-blue-400 text-white font-bold rounded-xl transition-all shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:shadow-[0_0_40px_rgba(59,130,246,0.5)] hover:-translate-y-0.5"
          >
            <Globe className="w-5 h-5" />
            Enter Cockpit
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>

          <a
            href="https://wiki.arif-fazil.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-6 py-4 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 rounded-xl transition-all"
          >
            <BookOpen className="w-5 h-5" />
            Ω-Wiki
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-slate-500">
        <span className="text-[10px] uppercase tracking-widest">Explore</span>
        <ChevronRight className="w-4 h-4 rotate-90 animate-bounce" />
      </div>
    </section>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Capability Cards
// ─────────────────────────────────────────────────────────────────────────────

const CAPABILITIES = [
  {
    icon: MapPin,
    title: '2D Map Grounding',
    description: 'MapLibre GL JS powered basin exploration with Malay Basin pilot data, AOI polygons, and real-time coordinate sync.',
    status: 'live',
    color: 'blue',
  },
  {
    icon: Globe,
    title: '3D Earth Witness',
    description: 'CesiumJS globe with terrain draping, well sticks, and structural visualization. Basin-scale context at your fingertips.',
    status: 'skeleton',
    color: 'indigo',
  },
  {
    icon: Activity,
    title: 'Seismic Viewer',
    description: 'WebGL2 seismic interpretation with candidate overlays, fault detection, and horizon picking. Multiple models visible.',
    status: 'shell',
    color: 'violet',
  },
  {
    icon: AlignLeft,
    title: 'Well Log Analysis',
    description: 'Canvas-based log tracks with petrophysical computations — Vsh, PHIe, Sw via Archie, Clavier-Fertl, and Wyllie methods.',
    status: 'building',
    color: 'cyan',
  },
  {
    icon: ImageIcon,
    title: 'Outcrop Lens',
    description: 'Field photo analysis with bedding, fracture, and fossil annotation. Analog grounding for subsurface interpretation.',
    status: 'planned',
    color: 'emerald',
  },
  {
    icon: Target,
    title: 'Prospect Desk',
    description: 'Decision panel with risk matrix, evidence stack, and 888_HOLD human sovereignty gates. DRIL / DRO / HOLD verdicts.',
    status: 'partial',
    color: 'amber',
  },
];

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const styles: Record<string, string> = {
    live: 'bg-green-500/10 text-green-400 border-green-500/30',
    skeleton: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    shell: 'bg-violet-500/10 text-violet-400 border-violet-500/30',
    building: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 animate-pulse',
    partial: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    planned: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${styles[status] || styles.planned}`}>
      {status}
    </span>
  );
};

const CapabilitiesSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Six Pillars of Interpretation</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          GEOX integrates six evidence streams through constitutional governance.
          Each pillar is independently grounded before contributing to the final verdict.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {CAPABILITIES.map((cap) => {
          const colorClass = {
            blue: 'bg-blue-500/10 text-blue-400',
            indigo: 'bg-indigo-500/10 text-indigo-400',
            violet: 'bg-violet-500/10 text-violet-400',
            cyan: 'bg-cyan-500/10 text-cyan-400',
            emerald: 'bg-emerald-500/10 text-emerald-400',
            amber: 'bg-amber-500/10 text-amber-400',
          }[cap.color] || 'bg-slate-500/10 text-slate-400';

          return (
            <div
              key={cap.title}
              className="group p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-black/20"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${colorClass.split(' ')[0]}`}>
                  <cap.icon className={`w-6 h-6 ${colorClass.split(' ')[1]}`} />
                </div>
                <StatusBadge status={cap.status} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">{cap.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{cap.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  </section>
);

// ─────────────────────────────────────────────────────────────────────────────
// MCP Tools Showcase
// ─────────────────────────────────────────────────────────────────────────────

const TOOL_CATEGORIES = [
  {
    title: 'Foundation (Phase A)',
    icon: Layers,
    tools: ['geox_load_seismic_line', 'geox_build_structural_candidates', 'geox_evaluate_prospect', 'geox_feasibility_check', 'geox_verify_geospatial', 'geox_calculate_saturation'],
  },
  {
    title: 'Physics Engine (Phase B)',
    icon: Cpu,
    tools: ['geox_select_sw_model', 'geox_compute_petrophysics', 'geox_validate_cutoffs', 'geox_petrophysical_hold_check'],
  },
  {
    title: 'Demo & System',
    icon: Server,
    tools: ['geox_malay_basin_pilot', 'geox_health', 'geox_petrophysics_health'],
  },
];

const ToolsSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-900">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">13 MCP Tools</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Governed geoscience tools accessible via FastMCP. Each tool validates against F1-F13 constitutional floors before execution.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {TOOL_CATEGORIES.map((cat) => (
          <div key={cat.title} className="p-6 rounded-2xl bg-slate-950/50 border border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <cat.icon className="w-5 h-5 text-blue-400" />
              <h3 className="font-bold text-white">{cat.title}</h3>
            </div>
            <div className="space-y-2">
              {cat.tools.map((tool) => (
                <div key={tool} className="flex items-center gap-2 text-sm">
                  <Zap className="w-3 h-3 text-slate-600" />
                  <code className="text-slate-300 font-mono text-xs">{tool}</code>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 rounded-xl bg-slate-950/50 border border-slate-800 font-mono text-xs text-slate-400 overflow-x-auto">
        <div className="flex items-center gap-2 mb-2 text-slate-500">
          <Server className="w-4 h-4" />
          <span>MCP Endpoint</span>
        </div>
        <code className="text-blue-400">fastmcp run https://geox.arif-fazil.com/mcp</code>
      </div>
    </div>
  </section>
);

// ─────────────────────────────────────────────────────────────────────────────
// Constitutional Floors
// ─────────────────────────────────────────────────────────────────────────────

const FLOORS = [
  { id: 'F1', name: 'AMANAH', desc: 'Reversible operations', icon: Lock },
  { id: 'F2', name: 'TRUTH', desc: 'Evidence-based outputs', icon: Eye },
  { id: 'F3', name: 'TRI-WITNESS', desc: 'Human × AI × System', icon: Layers },
  { id: 'F4', name: 'CLARITY', desc: 'Zero entropy decisions', icon: Zap },
  { id: 'F5', name: 'PEACE', desc: 'Non-adversarial', icon: Shield },
  { id: 'F7', name: 'HUMILITY', desc: 'Confidence ≤ 0.90', icon: BarChart3 },
  { id: 'F9', name: 'ANTI-HANTU', desc: 'Ghost detection', icon: Eye },
  { id: 'F13', name: 'SOVEREIGN', desc: 'Human override', icon: Lock },
];

const GovernanceSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Constitutional Governance</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          13 floors of constitutional discipline. Every interpretation passes through F1-F13 validation gates.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {FLOORS.map((floor) => (
          <div key={floor.id} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center hover:border-blue-500/30 transition-colors">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10 mb-3">
              <floor.icon className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-xl font-black text-white mb-1">{floor.id}</div>
            <div className="text-sm font-bold text-slate-300 mb-1">{floor.name}</div>
            <div className="text-xs text-slate-500">{floor.desc}</div>
          </div>
        ))}
      </div>
    </div>
  </section>
);

// ─────────────────────────────────────────────────────────────────────────────
// Malay Basin Pilot Showcase
// ─────────────────────────────────────────────────────────────────────────────

const PilotSection: React.FC = () => (
  <section className="py-20 px-6 bg-gradient-to-b from-slate-900 to-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/30 mb-6">
            <Radio className="w-3 h-3 text-green-400 animate-pulse" />
            <span className="text-xs font-bold text-green-400 uppercase tracking-wider">Live Pilot</span>
          </div>

          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Malay Basin Petroleum Exploration</h2>
          <p className="text-slate-400 mb-6 leading-relaxed">
            The live demonstration of GEOX capabilities. Real exploration metrics,
            play type distribution, creaming curve analysis, and constitutional governance
            applied to the Malay Basin — our primary operational domain.
          </p>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-2xl font-black text-white">500+</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">MMBOE Cumulative</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-2xl font-black text-white">4</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">Play Types</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-2xl font-black text-white">EDP15</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">Baseline</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-2xl font-black text-white">F1-F13</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">Floors Active</div>
            </div>
          </div>
        </div>

        <div className="relative">
          <div className="aspect-video rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden relative">
            {/* Stylized map preview */}
            <div className="absolute inset-0 bg-slate-950" />
            <div
              className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: `linear-gradient(rgba(59,130,246,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.3) 1px, transparent 1px)`,
                backgroundSize: '40px 40px'
              }}
            />
            {/* Mock basin polygon */}
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 225">
              <polygon
                points="80,60 200,30 320,70 280,160 120,180 60,120"
                fill="rgba(59,130,246,0.1)"
                stroke="rgba(59,130,246,0.5)"
                strokeWidth="1.5"
              />
              <polygon
                points="140,80 200,60 250,85 230,140 150,145"
                fill="rgba(239,68,68,0.15)"
                stroke="rgba(239,68,68,0.6)"
                strokeWidth="1"
              />
              <text x="200" y="115" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="10" fontFamily="monospace">
                Malay Basin
              </text>
            </svg>

            {/* Corner label */}
            <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-slate-950/80 border border-slate-800 text-[10px] font-mono text-slate-400">
              5.5°N, 104.5°E · WGS84
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);

// ─────────────────────────────────────────────────────────────────────────────
// Footer
// ─────────────────────────────────────────────────────────────────────────────

const Footer: React.FC = () => (
  <footer className="py-12 px-6 bg-slate-950 border-t border-slate-900">
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-blue-400" />
            <span className="font-black text-white">GEOX</span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Constitutional geoscience platform. Forged through discipline, not granted by authority.
          </p>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Platform</h4>
          <div className="space-y-2 text-xs">
            <a href="https://arifosmcp.arif-fazil.com" className="block text-slate-500 hover:text-blue-400 transition-colors">arifOS MCP</a>
            <a href="https://wiki.arif-fazil.com" className="block text-slate-500 hover:text-blue-400 transition-colors">Ω-Wiki</a>
            <a href="https://vault.arifosmcp.arif-fazil.com" className="block text-slate-500 hover:text-blue-400 transition-colors">VAULT999</a>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Resources</h4>
          <div className="space-y-2 text-xs">
            <a href="https://geox.arif-fazil.com/mcp" className="block text-slate-500 hover:text-blue-400 transition-colors">MCP Endpoint</a>
            <a href="https://geox.arif-fazil.com/health" className="block text-slate-500 hover:text-blue-400 transition-colors">Health Check</a>
            <span className="block text-slate-600">GitHub (Private)</span>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Seal</h4>
          <div className="text-xs text-slate-500">
            <p className="font-mono text-amber-500/80 mb-1">DITEMPA BUKAN DIBERI</p>
            <p>v0.6.1 · AGPL-3.0</p>
            <p className="mt-1">Muhammad Arif bin Fazil</p>
          </div>
        </div>
      </div>

      <div className="pt-8 border-t border-slate-900 text-center text-[10px] text-slate-600 font-mono">
        GEOX Earth Witness · Constitutional Geoscience Platform · 2026
      </div>
    </div>
  </footer>
);

// ─────────────────────────────────────────────────────────────────────────────
// Main Landing Page
// ─────────────────────────────────────────────────────────────────────────────

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterCockpit }) => {
  const [showNav, setShowNav] = useState(false);

  useEffect(() => {
    const handleScroll = () => setShowNav(window.scrollY > 100);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Floating nav */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${showNav ? 'bg-slate-950/80 backdrop-blur border-b border-slate-800' : 'bg-transparent'}`}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Globe className="w-5 h-5 text-blue-400" />
            <span className="font-black text-sm tracking-tight">GEOX</span>
          </div>

          <div className="flex items-center gap-4">
            <a href="https://wiki.arif-fazil.com" target="_blank" rel="noopener noreferrer" className="text-xs text-slate-400 hover:text-white transition-colors hidden sm:block">
              Ω-Wiki
            </a>
            <button
              onClick={onEnterCockpit}
              className="flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-bold rounded-lg border border-blue-500/30 transition-all"
            >
              Enter Cockpit
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </nav>

      <Hero onEnterCockpit={onEnterCockpit} />
      <CapabilitiesSection />
      <ToolsSection />
      <GovernanceSection />
      <PilotSection />
      <Footer />
    </div>
  );
};

export default LandingPage;
