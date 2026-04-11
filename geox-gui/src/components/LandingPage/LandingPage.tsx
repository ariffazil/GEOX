/**
 * GEOX Landing Page — Earth Intelligence Core
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Constitutional geoscience cockpit for basin, seismic, and well decisions.
 */

import React, { useState, useEffect } from 'react';
import {
  Globe, Activity, AlignLeft, Shield,
  ChevronRight, ExternalLink, ArrowRight,
  Zap, BarChart3, Server, BookOpen, Lock, Eye,
  Cpu, MapPin, Gauge, CheckCircle, AlertTriangle,
  FileSearch, Layers, Database
} from 'lucide-react';
import { useGEOXStore } from '../../store/geoxStore';

interface LandingPageProps {
  onEnterCockpit: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Hero Section — Clear value proposition first
// ═══════════════════════════════════════════════════════════════════════════════

const Hero: React.FC<{ onEnterCockpit: () => void }> = ({ onEnterCockpit }) => {
  const geoxConnected = useGEOXStore((state) => state.geoxConnected);

  return (
    <section className="relative min-h-[85vh] flex flex-col items-center justify-center px-6 py-20 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent" />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }}
      />

      <div className="relative z-10 text-center max-w-4xl mx-auto">
        {/* Status badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6">
          <div className={`w-2 h-2 rounded-full ${geoxConnected ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}`} />
          <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
            {geoxConnected ? 'Live Pilot: Malay Basin' : 'Connecting...'}
          </span>
        </div>

        {/* Main title — Plain language value prop */}
        <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-6 leading-tight">
          Geoscience decisions<br />
          <span className="text-blue-400">grounded in physics.</span>
        </h1>

        {/* Subhead — Who it's for + what it does */}
        <p className="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto mb-4 leading-relaxed">
          GEOX is a constitutional cockpit for exploration teams. Test feasibility, 
          compare interpretations, and issue auditable verdicts—grounded in reservoir 
          physics, geospatial context, and governance constraints.
        </p>

        {/* Audience line */}
        <p className="text-sm text-slate-500 mb-10 font-mono uppercase tracking-wider">
          For exploration teams · Geoscientists · Technical decision-makers
        </p>

        {/* CTAs — One primary, one secondary */}
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
            href="#apps"
            className="flex items-center gap-2 px-6 py-4 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 rounded-xl transition-all"
          >
            <Eye className="w-5 h-5" />
            See how it works
          </a>
        </div>

        {/* Seal — Doctrinal signature */}
        <p className="mt-12 text-xs font-mono text-slate-600 tracking-[0.3em] uppercase">
          DITEMPA BUKAN DIBERI — Forged, Not Given
        </p>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-slate-500">
        <span className="text-[10px] uppercase tracking-widest">Explore</span>
        <ChevronRight className="w-4 h-4 rotate-90 animate-bounce" />
      </div>
    </section>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// What GEOX Does — Three operational outcomes (plain language)
// ═══════════════════════════════════════════════════════════════════════════════

const OUTCOMES = [
  {
    icon: FileSearch,
    title: 'Interpret',
    description: 'Load seismic, well logs, and basin data. Every interpretation is tied to physical parameters you can verify.',
  },
  {
    icon: BarChart3,
    title: 'Compare',
    description: 'Test multiple scenarios side-by-side. Compare reserves estimates, risk profiles, and structural hypotheses with quantitative deltas.',
  },
  {
    icon: Shield,
    title: 'Govern',
    description: 'Every output is scored for feasibility, uncertainty, and risk. High-confidence claims proceed. Uncertain claims trigger hold states—not false confidence.',
  },
];

const OutcomesSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-900 border-y border-slate-800">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">From data to decision</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          GEOX keeps geoscience workflows auditable from raw data to final verdict.
          No black boxes. No unexplained confidence.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {OUTCOMES.map((outcome, idx) => (
          <div key={outcome.title} className="relative p-6 rounded-2xl bg-slate-950 border border-slate-800">
            <div className="absolute -top-3 left-6 px-2 py-1 bg-slate-900 text-xs font-mono text-slate-500 rounded">
              Step {idx + 1}
            </div>
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4">
              <outcome.icon className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">{outcome.title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{outcome.description}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// The 4 Apps — With clear benefit statements
// ═══════════════════════════════════════════════════════════════════════════════

const APPS = [
  {
    icon: Gauge,
    title: 'Risk Console',
    subtitle: 'Feasibility scoring',
    description: 'Calculate risk scores for any geological operation. Get clear verdicts: proceed, qualify, hold, or void—based on physics, not guesswork.',
    status: 'live',
    color: 'amber',
  },
  {
    icon: MapPin,
    title: 'Basin Explorer',
    subtitle: 'Map-based analysis',
    description: 'Interactive basin analysis with Malay Basin pilot data. Explore play fairways, evaluate prospects, and ground decisions in spatial context.',
    status: 'live',
    color: 'blue',
  },
  {
    icon: Activity,
    title: 'Seismic Viewer',
    subtitle: '2D/3D visualization',
    description: 'Visualize seismic data with governance overlays. Track depth, identify anomalies, and maintain audit trails for every interpretation.',
    status: 'live',
    color: 'violet',
  },
  {
    icon: AlignLeft,
    title: 'Well Desk',
    subtitle: 'Log analysis',
    description: 'Petrophysical log analysis with integrated risk scoring. Canvas-based tracks, real-time risk widgets, and full document provenance.',
    status: 'live',
    color: 'cyan',
  },
];

const AppsSection: React.FC = () => (
  <section id="apps" className="py-20 px-6 bg-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Four integrated apps</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Each app routes through the same governance layer. Every interpretation 
          is scored before it becomes a recommendation.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {APPS.map((app) => {
          const colorClass = {
            amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
            blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
            violet: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
            cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
          }[app.color] || 'bg-slate-500/10 text-slate-400';

          return (
            <div
              key={app.title}
              className="group p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${colorClass.split(' ')[0]}`}>
                  <app.icon className={`w-6 h-6 ${colorClass.split(' ')[1]}`} />
                </div>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border bg-green-500/10 text-green-400 border-green-500/30">
                  {app.status}
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mb-1">{app.title}</h3>
              <p className="text-xs font-mono text-slate-500 mb-3 uppercase tracking-wider">{app.subtitle}</p>
              <p className="text-sm text-slate-400 leading-relaxed">{app.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Evidence — Pilot proof
// ═══════════════════════════════════════════════════════════════════════════════

const EvidenceSection: React.FC = () => (
  <section className="py-20 px-6 bg-gradient-to-b from-slate-900 to-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/30 mb-6">
            <Zap className="w-3 h-3 text-green-400" />
            <span className="text-xs font-bold text-green-400 uppercase tracking-wider">Live Pilot</span>
          </div>

          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Proven in the Malay Basin
          </h2>
          
          <p className="text-slate-400 mb-6 leading-relaxed">
            GEOX is currently piloted on real Malay Basin exploration data. 
            The basin has produced 12+ billion barrels of oil equivalent across 
            142 discovered fields—providing a robust testbed for constitutional 
            geoscience workflows.
          </p>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-2xl font-black text-white">12.4</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">Bnboe Recoverable</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-2xl font-black text-white">142</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">Fields Discovered</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-2xl font-black text-white">48</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">Play Types</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-2xl font-black text-white">5.5°N</div>
              <div className="text-xs text-slate-500 uppercase tracking-wider">104.5°E · WGS84</div>
            </div>
          </div>

          <p className="text-xs text-slate-600">
            Source: GSM-702001 Malay Basin regional synthesis and published 
            exploration histories. Pilot data represents publicly available 
            basin-scale summaries, not proprietary field data.
          </p>
        </div>

        <div className="relative">
          <div className="aspect-video rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden relative">
            <div className="absolute inset-0 bg-slate-950" />
            <div
              className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: `linear-gradient(rgba(59,130,246,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.3) 1px, transparent 1px)`,
                backgroundSize: '40px 40px'
              }}
            />
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
                Malay Basin Pilot
              </text>
            </svg>
            <div className="absolute bottom-3 left-3 px-2 py-1 rounded bg-slate-950/80 border border-slate-800 text-[10px] font-mono text-slate-400">
              Pilot visualization
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Governance — Doctrinal depth (below fold)
// ═══════════════════════════════════════════════════════════════════════════════

const FLOORS = [
  { id: 'F1', name: 'REVERSIBLE', desc: 'Every action can be undone' },
  { id: 'F2', name: 'TRUTH', desc: 'Grounded in physical evidence' },
  { id: 'F4', name: 'CLARITY', desc: 'Uncertainty is explicit' },
  { id: 'F7', name: 'HUMILITY', desc: 'Confidence ≤ 15%' },
  { id: 'F9', name: 'TRANSPARENT', desc: 'No hidden reasoning' },
  { id: 'F11', name: 'AUDITABLE', desc: 'Full decision lineage' },
  { id: 'F13', name: 'SOVEREIGN', desc: 'Human holds final authority' },
];

const GovernanceSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Governed by constitutional constraints</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          GEOX implements seven binding constraints from the arifOS constitutional kernel. 
          Every interpretation passes through these gates before becoming a recommendation.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {FLOORS.map((floor) => (
          <div key={floor.id} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center">
            <div className="text-xl font-black text-white mb-1">{floor.id}</div>
            <div className="text-xs font-bold text-slate-300 mb-1">{floor.name}</div>
            <div className="text-[10px] text-slate-500 leading-tight">{floor.desc}</div>
          </div>
        ))}
      </div>

      {/* Verdict taxonomy */}
      <div className="mt-12 p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
        <h3 className="text-center text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
          Decision Verdicts
        </h3>
        <div className="flex flex-wrap justify-center gap-6 text-sm">
          <span><span className="text-green-400 font-bold">SEAL</span> <span className="text-slate-500">— &lt; 0.15 risk</span></span>
          <span><span className="text-blue-400 font-bold">QUALIFY</span> <span className="text-slate-500">— &lt; 0.35 risk</span></span>
          <span><span className="text-amber-400 font-bold">HOLD</span> <span className="text-slate-500">— &lt; 0.60 risk</span></span>
          <span><span className="text-red-400 font-bold">VOID</span> <span className="text-slate-500">— ≥ 0.60 risk</span></span>
        </div>
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Footer
// ═══════════════════════════════════════════════════════════════════════════════

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
            Constitutional geoscience cockpit for exploration teams. 
            Forged through discipline, not granted by authority.
          </p>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Platform</h4>
          <div className="space-y-2 text-xs">
            <a href="https://arifosmcp.arif-fazil.com" className="block text-slate-500 hover:text-blue-400 transition-colors">arifOS MCP</a>
            <a href="https://wiki.arif-fazil.com" className="block text-slate-500 hover:text-blue-400 transition-colors">Ω-Wiki</a>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Resources</h4>
          <div className="space-y-2 text-xs">
            <a href="https://geox.arif-fazil.com/health" className="block text-slate-500 hover:text-blue-400 transition-colors">System Health</a>
            <a href="https://github.com/ariffazil/GEOX" className="block text-slate-500 hover:text-blue-400 transition-colors">Documentation</a>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Seal</h4>
          <div className="text-xs text-slate-500">
            <p className="font-mono text-amber-500/80 mb-1">DITEMPA BUKAN DIBERI</p>
            <p>v2026.04.12-EIC</p>
            <p className="mt-1">arifOS Earth Intelligence</p>
          </div>
        </div>
      </div>

      <div className="pt-8 border-t border-slate-900 text-center text-[10px] text-slate-600 font-mono">
        GEOX Earth Intelligence Core · Constitutional Geoscience Platform · 2026
      </div>
    </div>
  </footer>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Main Landing Page
// ═══════════════════════════════════════════════════════════════════════════════

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
            <a href="https://github.com/ariffazil/GEOX" target="_blank" rel="noopener noreferrer" className="text-xs text-slate-400 hover:text-white transition-colors hidden sm:block">
              Documentation
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
      <OutcomesSection />
      <AppsSection />
      <EvidenceSection />
      <GovernanceSection />
      <Footer />
    </div>
  );
};

export default LandingPage;
