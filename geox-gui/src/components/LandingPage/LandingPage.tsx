/**
 * GEOX Landing Page — Three Layers: Product / Workspaces / Platform
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Layer 1: Product — Decision cockpit for exploration teams
 * Layer 2: Workspaces — Apps (MCP Apps, Web Apps, Hybrid)
 * Layer 3: Platform — MCP server, tools, resources for developers
 */

import React, { useState, useEffect } from 'react';
import {
  Globe, Activity, AlignLeft, Shield,
  ChevronRight, ExternalLink, ArrowRight,
  Zap, BarChart3, Server, BookOpen, Lock, Eye,
  Cpu, MapPin, Gauge, CheckCircle, AlertTriangle,
  FileSearch, Layers, Database, Terminal, Code,
  Box, Workflow, CpuIcon, Map, Settings
} from 'lucide-react';
import { useGEOXStore } from '../../store/geoxStore';

interface LandingPageProps {
  onEnterCockpit: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Layer 1: PRODUCT — Hero + What GEOX Does
// ═══════════════════════════════════════════════════════════════════════════════

const Hero: React.FC<{ onEnterCockpit: () => void }> = ({ onEnterCockpit }) => {
  const geoxConnected = useGEOXStore((state) => state.geoxConnected);

  return (
    <section className="relative min-h-[85vh] flex flex-col items-center justify-center px-6 py-20 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent" />
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
        backgroundSize: '60px 60px'
      }} />

      <div className="relative z-10 text-center max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6">
          <div className={`w-2 h-2 rounded-full ${geoxConnected ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}`} />
          <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
            {geoxConnected ? 'Live Pilot: Malay Basin' : 'Connecting...'}
          </span>
        </div>

        <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight mb-6 leading-tight">
          Geoscience decisions<br />
          <span className="text-blue-400">grounded in physics.</span>
        </h1>

        <p className="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto mb-4 leading-relaxed">
          GEOX is a constitutional cockpit for exploration teams. Test feasibility, 
          compare interpretations, and issue auditable verdicts—grounded in reservoir 
          physics, geospatial context, and governance constraints.
        </p>

        <p className="text-sm text-slate-500 mb-10 font-mono uppercase tracking-wider">
          For exploration teams · Geoscientists · Technical decision-makers
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onEnterCockpit}
            className="group flex items-center gap-3 px-8 py-4 bg-blue-500 hover:bg-blue-400 text-white font-bold rounded-xl transition-all shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:shadow-[0_0_40px_rgba(59,130,246,0.5)] hover:-translate-y-0.5"
          >
            <Globe className="w-5 h-5" />
            Enter Cockpit
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>

          <a href="#workspaces" className="flex items-center gap-2 px-6 py-4 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 rounded-xl transition-all">
            <Eye className="w-5 h-5" />
            Explore Workspaces
          </a>
        </div>

        <p className="mt-12 text-xs font-mono text-slate-600 tracking-[0.3em] uppercase">
          DITEMPA BUKAN DIBERI — Forged, Not Given
        </p>
      </div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-slate-500">
        <span className="text-[10px] uppercase tracking-widest">Explore</span>
        <ChevronRight className="w-4 h-4 rotate-90 animate-bounce" />
      </div>
    </section>
  );
};

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
        {[
          { icon: FileSearch, title: 'Interpret', desc: 'Load seismic, well logs, and basin data. Every interpretation is tied to physical parameters you can verify.' },
          { icon: BarChart3, title: 'Compare', desc: 'Test multiple scenarios side-by-side. Compare reserves estimates, risk profiles, and structural hypotheses with quantitative deltas.' },
          { icon: Shield, title: 'Govern', desc: 'Every output is scored for feasibility, uncertainty, and risk. High-confidence claims proceed. Uncertain claims trigger hold states—not false confidence.' },
        ].map((item, idx) => (
          <div key={item.title} className="relative p-6 rounded-2xl bg-slate-950 border border-slate-800">
            <div className="absolute -top-3 left-6 px-2 py-1 bg-slate-900 text-xs font-mono text-slate-500 rounded">Step {idx + 1}</div>
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4">
              <item.icon className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">{item.title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Layer 2: WORKSPACES — MCP Apps, Web Apps, Hybrid
// ═══════════════════════════════════════════════════════════════════════════════

const WorkspacesSection: React.FC = () => (
  <section id="workspaces" className="py-20 px-6 bg-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">GEOX Workspaces</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Interactive geoscience environments for different contexts. 
          Same tools, same governance, different surfaces.
        </p>
      </div>

      {/* MCP Apps */}
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-amber-500/10">
            <Box className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">MCP Apps</h3>
            <p className="text-sm text-slate-500">Inside AI hosts · ChatGPT · Claude · Cursor</p>
          </div>
        </div>
        <p className="text-slate-400 mb-4 text-sm">
          Interactive GEOX workspaces running inside compatible AI clients via MCP Apps. 
          Rendered as embedded iframes; uses MCP tools/resources; portable across hosts.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <WorkspaceCard
            icon={MapPin}
            title="Prospect Explorer"
            badge="MCP App"
            audience="Exploration teams"
            benefit="Screen basin prospects with physics-grounded feasibility scoring."
          />
          <WorkspaceCard
            icon={AlignLeft}
            title="Well Desk"
            badge="MCP App"
            audience="Petrophysicists"
            benefit="Analyze well logs with integrated risk widgets and verdict panels."
          />
        </div>
      </div>

      {/* Web Apps */}
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-blue-500/10">
            <Globe className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Web Apps</h3>
            <p className="text-sm text-slate-500">Standalone browser · Full-screen cockpit</p>
          </div>
        </div>
        <p className="text-slate-400 mb-4 text-sm">
          Full-screen GEOX cockpit in your browser. Shares the same tools and contracts as MCP Apps, 
          but runs outside chat for extended analysis sessions.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <WorkspaceCard
            icon={Gauge}
            title="GEOX Cockpit"
            badge="Web App"
            audience="Geoscientists"
            benefit="Unified workspace for basin, seismic, and well interpretation."
          />
          <WorkspaceCard
            icon={Activity}
            title="Risk Console"
            badge="Web App"
            audience="Technical leaders"
            benefit="Real-time risk scoring with SEAL/QUALIFY/HOLD/VOID verdicts."
          />
        </div>
      </div>

      {/* Hybrid */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-violet-500/10">
            <Layers className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">WebMCP / Hybrid</h3>
            <p className="text-sm text-slate-500">Browser + MCP bridge · Embed · Integrate</p>
          </div>
        </div>
        <p className="text-slate-400 mb-4 text-sm">
          Browser apps that also speak MCP, acting as both UI and server client. 
          Use WebMCP to plug GEOX tools into other systems or drive GEOX from external AI.
        </p>
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
          <div className="flex items-center gap-3">
            <Code className="w-5 h-5 text-violet-400" />
            <span className="text-white font-medium">WebMCP Bridge</span>
            <span className="text-slate-500 text-sm">— Connect external systems to GEOX tools</span>
          </div>
        </div>
      </div>
    </div>
  </section>
);

const WorkspaceCard: React.FC<{ icon: any, title: string, badge: string, audience: string, benefit: string }> = 
({ icon: Icon, title, badge, audience, benefit }) => (
  <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-all">
    <div className="flex items-start justify-between mb-3">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-slate-800">
          <Icon className="w-5 h-5 text-slate-300" />
        </div>
        <div>
          <h4 className="font-bold text-white">{title}</h4>
          <p className="text-xs text-slate-500">{audience}</p>
        </div>
      </div>
      <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-bold ${
        badge === 'MCP App' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
        badge === 'Web App' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30' :
        'bg-violet-500/10 text-violet-400 border border-violet-500/30'
      }`}>
        {badge}
      </span>
    </div>
    <p className="text-sm text-slate-400">{benefit}</p>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Layer 3: PLATFORM — MCP Server, Tools, Resources, Skills
// ═══════════════════════════════════════════════════════════════════════════════

const PlatformSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-900 border-y border-slate-800">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Under the hood: GEOX Platform</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          For engineers and integrators. The GEOX platform exposes standardized interfaces 
          for building custom geoscience workflows.
        </p>
      </div>

      {/* Architecture Diagram */}
      <div className="mb-12 p-6 rounded-2xl bg-slate-950 border border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          {/* Top: Apps */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Box className="w-4 h-4 text-amber-400" />
              <Globe className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-sm font-bold text-white">Apps</div>
            <div className="text-xs text-slate-500">MCP Apps · Web Apps</div>
          </div>
          
          {/* Middle: MCP Server */}
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
            <Server className="w-6 h-6 text-blue-400 mx-auto mb-2" />
            <div className="text-sm font-bold text-white">GEOX MCP Server</div>
            <div className="text-xs text-slate-400">Tools · Resources · Prompts</div>
          </div>
          
          {/* Bottom: Data */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <Database className="w-5 h-5 text-slate-400 mx-auto mb-2" />
            <div className="text-sm font-bold text-white">Data & GEO-FABRIC</div>
            <div className="text-xs text-slate-500">CRS · Wells · Seismic</div>
          </div>
        </div>
        
        {/* Arrows */}
        <div className="flex justify-center my-4">
          <ArrowRight className="w-5 h-5 text-slate-600 rotate-90" />
        </div>
        
        <p className="text-center text-xs text-slate-500">
          Apps call the MCP Server. Server queries Data via GEO-FABRIC. All responses pass through Physics9 + Governance.
        </p>
      </div>

      {/* Platform Components */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PlatformCard
          icon={Terminal}
          title="MCP Server"
          description="GEOX MCP server exposes dimension tools (PROSPECT, WELL, SECTION, EARTH_3D, TIME_4D) over standard MCP protocol."
          link="MCP tools registry →"
        />
        <PlatformCard
          icon={Map}
          title="GEO-FABRIC"
          description="Shared coordinate and CRS fabric used by all apps, for PROSPECT ↔ WELL ↔ SECTION ↔ 3D transformations."
          link="Coordinate system docs →"
        />
        <PlatformCard
          icon={Settings}
          title="Tools & Resources"
          description="Tools = actions (search, extract, transform, validate). Resources = reusable artifacts (well headers, polygons, verdict reports)."
          link="Tool schemas →"
        />
        <PlatformCard
          icon={Workflow}
          title="Skills / Workflows"
          description="Predefined workflows for screening prospects, tying wells, issuing governed verdicts. Each skill composes tools + prompts + governance."
          link="Available skills →"
        />
      </div>
    </div>
  </section>
);

const PlatformCard: React.FC<{ icon: any, title: string, description: string, link: string }> = 
({ icon: Icon, title, description, link }) => (
  <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
    <div className="flex items-center gap-3 mb-3">
      <Icon className="w-5 h-5 text-blue-400" />
      <h3 className="font-bold text-white">{title}</h3>
    </div>
    <p className="text-sm text-slate-400 mb-3">{description}</p>
    <a href="#" className="text-xs text-blue-400 hover:text-blue-300">{link}</a>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// MCP & MCP Apps Section
// ═══════════════════════════════════════════════════════════════════════════════

const McpSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-950">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">MCP & MCP Apps in GEOX</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Integrate GEOX into your AI workflow via Model Context Protocol.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800">
          <Box className="w-6 h-6 text-amber-400 mb-3" />
          <h3 className="font-bold text-white mb-2">MCP Apps</h3>
          <p className="text-sm text-slate-400">Interactive workspaces inside ChatGPT, Claude, Cursor. Rendered as embedded iframes via <code className="text-amber-400">ui/*</code> JSON-RPC.</p>
        </div>
        <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800">
          <Globe className="w-6 h-6 text-blue-400 mb-3" />
          <h3 className="font-bold text-white mb-2">Web Apps</h3>
          <p className="text-sm text-slate-400">Full-screen cockpit in browser. Same code, different container. For extended analysis outside chat.</p>
        </div>
        <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800">
          <Layers className="w-6 h-6 text-violet-400 mb-3" />
          <h3 className="font-bold text-white mb-2">Hybrid</h3>
          <p className="text-sm text-slate-400">WebMCP bridge: browser apps that speak MCP. Embed GEOX in your tools, or drive GEOX from external AI.</p>
        </div>
      </div>

      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
        <h3 className="font-bold text-white mb-4">Key integration points</h3>
        <ul className="space-y-3 text-sm text-slate-400">
          <li className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
            <span><strong className="text-slate-300">Typed JSON schemas</strong> for all tools—every dimension has validated inputs and outputs.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
            <span><strong className="text-slate-300">MCP Apps bridge</strong> renders interactive UI (maps, logs, panels) inside AI clients.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
            <span><strong className="text-slate-300">Portable workspaces</strong>—same app code runs as MCP App, Web App, or WebMCP hybrid.</span>
          </li>
        </ul>
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Tools & Skills Section
// ═══════════════════════════════════════════════════════════════════════════════

const ToolsSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-900 border-y border-slate-800">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Tools & Skills</h2>
        <p className="text-slate-400">Concrete capabilities for AI and human workflows.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Tools */}
        <div>
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-blue-400" />
            Tools (for AI + automation)
          </h3>
          <p className="text-sm text-slate-500 mb-4">Actions that return structured JSON with evidence, risk, and verdict.</p>
          <div className="space-y-3">
            <ToolItem name="search_wells" desc="List wells in a basin or around a coordinate." />
            <ToolItem name="project_well_to_map" desc="GEO-FABRIC projection with CRS handling." />
            <ToolItem name="screen_well_against_prospect" desc="Physics validation + governance check." />
            <ToolItem name="compute_stoiip" desc="Volumetric reserves with F7 uncertainty bounds." />
            <ToolItem name="validate_physics" desc="Check parameter sets against Earth Canon 9." />
          </div>
        </div>

        {/* Skills */}
        <div>
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Workflow className="w-5 h-5 text-amber-400" />
            Skills / Workflows (for humans + AI)
          </h3>
          <p className="text-sm text-slate-500 mb-4">Reusable, governed workflows rather than raw prompts.</p>
          <div className="space-y-3">
            <SkillItem name="Prospect Screening" desc="Chain: search → screen → verdict. Outputs feasibility score with HOLD/SEAL." />
            <SkillItem name="Well-to-Prospect Tie" desc="Chain: transform → GEO-FABRIC → validate. Checks datum, units, CRS." />
            <SkillItem name="Reserves Audit" desc="Chain: multi-scenario STOIIP → uncertainty → governance review." />
            <SkillItem name="Seismic QC" desc="Chain: load → physics check → d2t validation → verdict." />
          </div>
        </div>
      </div>
    </div>
  </section>
);

const ToolItem: React.FC<{ name: string, desc: string }> = ({ name, desc }) => (
  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
    <code className="text-sm text-blue-400 font-mono">{name}</code>
    <p className="text-xs text-slate-500 mt-1">{desc}</p>
  </div>
);

const SkillItem: React.FC<{ name: string, desc: string }> = ({ name, desc }) => (
  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
    <div className="text-sm text-amber-400 font-medium">{name}</div>
    <p className="text-xs text-slate-500 mt-1">{desc}</p>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// For Developers Section
// ═══════════════════════════════════════════════════════════════════════════════

const DevelopersSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-950">
    <div className="max-w-4xl mx-auto text-center">
      <h2 className="text-3xl font-bold text-white mb-4">For developers</h2>
      <p className="text-slate-400 mb-8">
        Integrate GEOX via MCP tools or embed GEOX workspaces as MCP Apps.
      </p>
      
      <div className="flex flex-wrap justify-center gap-4">
        <a href="#" className="flex items-center gap-2 px-6 py-3 bg-slate-900 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all">
          <BookOpen className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-slate-300">MCP Server docs →</span>
        </a>
        <a href="#" className="flex items-center gap-2 px-6 py-3 bg-slate-900 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all">
          <Code className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-slate-300">MCP Apps guide →</span>
        </a>
        <a href="#" className="flex items-center gap-2 px-6 py-3 bg-slate-900 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all">
          <Layers className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-slate-300">WebMCP & SDK →</span>
        </a>
      </div>
      
      <p className="mt-8 text-xs text-slate-600">
        GEOX follows MCP best practices: small tools, typed schemas, resources for artifacts.
      </p>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Evidence — Pilot
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

          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Proven in the Malay Basin</h2>
          
          <p className="text-slate-400 mb-6 leading-relaxed">
            GEOX is currently piloted on Malay Basin exploration data. 
            The basin has produced 12+ billion barrels of oil equivalent across 
            142 discovered fields—providing a robust testbed for constitutional workflows.
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
          </div>

          <p className="text-xs text-slate-600">
            Source: GSM-702001 Malay Basin regional synthesis. Pilot uses publicly available basin-scale summaries.
          </p>
        </div>

        <div className="aspect-video rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden relative">
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 225">
            <polygon points="80,60 200,30 320,70 280,160 120,180 60,120" fill="rgba(59,130,246,0.1)" stroke="rgba(59,130,246,0.5)" strokeWidth="1.5" />
            <polygon points="140,80 200,60 250,85 230,140 150,145" fill="rgba(239,68,68,0.15)" stroke="rgba(239,68,68,0.6)" strokeWidth="1" />
            <text x="200" y="115" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="10" fontFamily="monospace">Malay Basin Pilot</text>
          </svg>
        </div>
      </div>
    </div>
  </section>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Governance Section (Bottom)
// ═══════════════════════════════════════════════════════════════════════════════

const GovernanceSection: React.FC = () => (
  <section className="py-20 px-6 bg-slate-950 border-t border-slate-900">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-white mb-4">Governance & Constitution</h2>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Every GEOX call runs through Physics9 and Governance constraints.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { id: 'F1', name: 'REVERSIBLE', desc: 'Every action can be undone' },
          { id: 'F2', name: 'TRUTH', desc: 'Grounded in physical evidence' },
          { id: 'F4', name: 'CLARITY', desc: 'Uncertainty is explicit' },
          { id: 'F7', name: 'HUMILITY', desc: 'Confidence ≤ 15%' },
          { id: 'F9', name: 'TRANSPARENT', desc: 'No hidden reasoning' },
          { id: 'F11', name: 'AUDITABLE', desc: 'Full decision lineage' },
          { id: 'F13', name: 'SOVEREIGN', desc: 'Human holds final authority' },
        ].map((floor) => (
          <div key={floor.id} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center">
            <div className="text-xl font-black text-white mb-1">{floor.id}</div>
            <div className="text-xs font-bold text-slate-300 mb-1">{floor.name}</div>
            <div className="text-[10px] text-slate-500">{floor.desc}</div>
          </div>
        ))}
      </div>

      <div className="text-center">
        <a href="https://arifos.arif-fazil.com" className="text-sm text-blue-400 hover:text-blue-300">
          Read full GEOX constitutional doctrine →
        </a>
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
          <p className="text-xs text-slate-500">Constitutional geoscience cockpit.</p>
        </div>
        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Platform</h4>
          <div className="space-y-2 text-xs">
            <a href="https://arifosmcp.arif-fazil.com" className="block text-slate-500 hover:text-blue-400">arifOS MCP</a>
            <a href="https://wiki.arif-fazil.com" className="block text-slate-500 hover:text-blue-400">Ω-Wiki</a>
          </div>
        </div>
        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Resources</h4>
          <div className="space-y-2 text-xs">
            <a href="https://geox.arif-fazil.com/health" className="block text-slate-500 hover:text-blue-400">System Health</a>
            <a href="https://github.com/ariffazil/GEOX" className="block text-slate-500 hover:text-blue-400">Documentation</a>
          </div>
        </div>
        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase mb-3">Seal</h4>
          <div className="text-xs text-slate-500">
            <p className="font-mono text-amber-500/80 mb-1">DITEMPA BUKAN DIBERI</p>
            <p>v2026.04.12-EIC</p>
          </div>
        </div>
      </div>
      <div className="pt-8 border-t border-slate-900 text-center text-[10px] text-slate-600 font-mono">
        GEOX Earth Intelligence Core · 2026
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
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${showNav ? 'bg-slate-950/80 backdrop-blur border-b border-slate-800' : 'bg-transparent'}`}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Globe className="w-5 h-5 text-blue-400" />
            <span className="font-black text-sm tracking-tight">GEOX</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://github.com/ariffazil/GEOX" target="_blank" rel="noopener noreferrer" className="text-xs text-slate-400 hover:text-white transition-colors hidden sm:block">
              Docs
            </a>
            <button onClick={onEnterCockpit} className="flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-bold rounded-lg border border-blue-500/30 transition-all">
              Enter Cockpit
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </nav>

      <Hero onEnterCockpit={onEnterCockpit} />
      <OutcomesSection />
      <WorkspacesSection />
      <PlatformSection />
      <McpSection />
      <ToolsSection />
      <DevelopersSection />
      <EvidenceSection />
      <GovernanceSection />
      <Footer />
    </div>
  );
};

export default LandingPage;
