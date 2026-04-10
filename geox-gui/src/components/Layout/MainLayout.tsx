/**
 * MainLayout — GEOX GUI Layout
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 * 
 * Three-panel layout:
 * - Left: Data/Layers sidebar
 * - Center: Main workspace (map/seismic/logs)
 * - Right: Governance + Prospect panel
 */

import React, { useState } from 'react';
import { 
  Map, Globe, Activity, AlignLeft, Image as ImageIcon, 
  Target, Shield, FileText, Settings, Search,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import * as Separator from '@radix-ui/react-separator';
import { WitnessBadges, WitnessBadgesCompact } from '../WitnessBadges/WitnessBadges';
import { EarthWitness } from '../EarthWitness/EarthWitness';
import { EarthWitness3D } from '../EarthWitness/EarthWitness3D';
import { AppIframeHost } from '../EarthWitness/AppIframeHost';
import { MalayBasinPilotDashboard } from '../MalayBasinPilot/MalayBasinPilotDashboard';
import { LogDock } from '../LogDock/LogDock';
import { useGEOXStore, useActiveTab, useGovernance, useGEOXConnected } from '../../store/geoxStore';
import type { Tab } from '../../types';


// Tab configuration
const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'map', label: 'Map', icon: Map },
  { id: '3d', label: '3D Earth', icon: Globe },
  { id: 'seismic', label: 'Seismic', icon: Activity },
  { id: 'wells', label: 'Wells & Logs', icon: AlignLeft },
  { id: 'outcrop', label: 'Outcrop', icon: ImageIcon },
  { id: 'prospect', label: 'Prospect', icon: Target },
  { id: 'governance', label: 'Governance', icon: Shield },
  { id: 'qc', label: 'QC / Audit', icon: FileText },
  { id: 'pilot', label: 'Malay Basin Pilot', icon: Target },
];

// Left Sidebar - Data/Layers
const LeftSidebar: React.FC = () => {
  const [expanded, setExpanded] = useState(true);
  
  return (
    <div className={`flex flex-col bg-slate-50 border-r border-slate-200 transition-all duration-300 ${expanded ? 'w-64' : 'w-12'}`}>
      {/* Toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="p-3 hover:bg-slate-200 border-b border-slate-200 flex items-center justify-center"
      >
        {expanded ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      
      {expanded && (
        <>
          {/* Search */}
          <div className="p-3 border-b border-slate-200">
            <div className="relative">
              <Search className="absolute left-2 top-2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search wells, fields..."
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          {/* Layers Tree */}
          <div className="flex-1 overflow-auto p-3">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Layers</h4>
            <div className="space-y-1">
              <LayerItem name="Basemap" checked />
              <LayerItem name="Wells" checked />
              <LayerItem name="Seismic Lines" checked />
              <LayerItem name="Horizons" />
              <LayerItem name="Faults" />
              <LayerItem name="Surface Geology" />
              <LayerItem name="AOI Polygons" />
            </div>
          </div>
          
          {/* Filters */}
          <div className="p-3 border-t border-slate-200">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Filters</h4>
            <div className="space-y-2 text-sm">
              <select className="w-full p-1.5 border border-slate-300 rounded text-sm" title="Formation Filter">
                <option>All Formations</option>
                <option>Carbonate</option>
                <option>Clastic</option>
              </select>
              <select className="w-full p-1.5 border border-slate-300 rounded text-sm" title="Interval Filter">
                <option>All Intervals</option>
                <option>Tertiary</option>
                <option>Cretaceous</option>
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Layer item component
const LayerItem: React.FC<{ name: string; checked?: boolean }> = ({ name, checked = false }) => (
  <label className="flex items-center gap-2 p-1.5 hover:bg-slate-100 rounded cursor-pointer">
    <input type="checkbox" defaultChecked={checked} className="rounded border-slate-300" />
    <span className="text-sm text-slate-700">{name}</span>
  </label>
);

// Right Sidebar - Governance + Prospect
const RightSidebar: React.FC = () => {
  const [activePanel, setActivePanel] = useState<'governance' | 'prospect'>('governance');
  
  return (
    <div className="w-80 flex flex-col bg-white border-l border-slate-200">
      {/* Panel Toggle */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActivePanel('governance')}
          className={`flex-1 py-2 text-sm font-medium ${activePanel === 'governance' ? 'bg-slate-100 text-slate-900 border-b-2 border-blue-500' : 'text-slate-500'}`}
        >
          <Shield className="w-4 h-4 inline mr-1" />
          Governance
        </button>
        <button
          onClick={() => setActivePanel('prospect')}
          className={`flex-1 py-2 text-sm font-medium ${activePanel === 'prospect' ? 'bg-slate-100 text-slate-900 border-b-2 border-blue-500' : 'text-slate-500'}`}
        >
          <Target className="w-4 h-4 inline mr-1" />
          Prospect
        </button>
      </div>
      
      {/* Panel Content */}
      <div className="flex-1 overflow-auto">
        {activePanel === 'governance' ? (
          <WitnessBadges />
        ) : (
          <ProspectPanel />
        )}
      </div>
    </div>
  );
};

// Prospect Panel placeholder
const ProspectPanel: React.FC = () => (
  <div className="p-4 space-y-4">
    <h3 className="font-bold text-slate-800">Prospect Evaluation</h3>
    
    {/* Prospect ID */}
    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
      <label className="text-xs text-slate-500 uppercase">Prospect ID</label>
      <div className="font-mono text-sm">ALPHA-001</div>
    </div>
    
    {/* Play Summary */}
    <div className="space-y-2">
      <h4 className="text-xs font-bold text-slate-500 uppercase">Play Summary</h4>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="p-2 bg-slate-50 rounded">
          <span className="text-slate-500">Trap:</span> 3-way
        </div>
        <div className="p-2 bg-slate-50 rounded">
          <span className="text-slate-500">Reservoir:</span> Carbonate
        </div>
        <div className="p-2 bg-slate-50 rounded">
          <span className="text-slate-500">Seal:</span> Shale
        </div>
        <div className="p-2 bg-slate-50 rounded">
          <span className="text-slate-500">Charge:</span> Mature
        </div>
      </div>
    </div>
    
    {/* Risk Matrix */}
    <div className="space-y-2">
      <h4 className="text-xs font-bold text-slate-500 uppercase">Risk Matrix</h4>
      <div className="space-y-1">
        <RiskBar label="Reservoir" level="moderate" />
        <RiskBar label="Seal" level="high" />
        <RiskBar label="Trap" level="low" />
        <RiskBar label="Charge" level="moderate" />
      </div>
    </div>
    
    {/* Human Decision Zone */}
    <div className="p-3 bg-red-50 border-2 border-red-300 rounded-lg">
      <h4 className="font-bold text-red-800 flex items-center gap-2">
        <Shield className="w-4 h-4" />
        Human Decision Required
      </h4>
      <p className="text-sm text-red-600 mt-1">
        F13 SOVEREIGN: Final approval requires human sign-off.
      </p>
      <div className="flex gap-2 mt-3">
        <button className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700">
          HOLD
        </button>
        <button className="flex-1 px-3 py-2 bg-amber-500 text-white text-sm rounded hover:bg-amber-600">
          PARTIAL
        </button>
      </div>
    </div>
  </div>
);

// Risk bar component
const RiskBar: React.FC<{ label: string; level: 'low' | 'moderate' | 'high' | 'unknown' }> = ({ label, level }) => {
  const colors = {
    low: 'bg-green-500',
    moderate: 'bg-amber-500',
    high: 'bg-red-500',
    unknown: 'bg-gray-400',
  };
  
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-20 text-slate-600">{label}</span>
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${colors[level]} ${level === 'unknown' ? 'w-1/3' : 'w-full'}`} />
      </div>
      <span className={`text-xs font-medium ${
        level === 'low' ? 'text-green-600' :
        level === 'moderate' ? 'text-amber-600' :
        level === 'high' ? 'text-red-600' : 'text-gray-500'
      }`}>
        {level.toUpperCase()}
      </span>
    </div>
  );
};

// Main Workspace
const MainWorkspace: React.FC = () => {
  const activeTab = useActiveTab();
  
  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Tab Navigation */}
      <Tabs.Root value={activeTab} onValueChange={(v) => useGEOXStore.getState().setActiveTab(v as Tab)}>
        <Tabs.List className="flex border-b border-slate-200 bg-slate-50">
          {TABS.map((tab) => (
            <Tabs.Trigger
              key={tab.id}
              value={tab.id}
              className={`
                flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors
                data-[state=active]:border-blue-500 data-[state=active]:text-blue-600 data-[state=active]:bg-white
                data-[state=inactive]:border-transparent data-[state=inactive]:text-slate-600 data-[state=inactive]:hover:text-slate-900
              `}
            >
              <tab.icon className="w-4 h-4" />
              <span className="hidden lg:inline">{tab.label}</span>
            </Tabs.Trigger>
          ))}
        </Tabs.List>
        
        {/* Tab Content */}
        <div className="flex-1 p-4 overflow-auto">
          <Tabs.Content value="map" className="h-full">
            <EarthWitness />
          </Tabs.Content>
          
          <Tabs.Content value="3d" className="h-full">
            <EarthWitness3D />
          </Tabs.Content>
          
          <Tabs.Content value="seismic" className="h-full">
            <AppIframeHost 
              src="/apps/seismic_viewer/index.html" 
              title="SeisView (WebGL)" 
              appId="geox.seismic.viewer" 
            />
          </Tabs.Content>
          
          <Tabs.Content value="wells" className="h-full">
            <LogDock />
          </Tabs.Content>
          
          <Tabs.Content value="outcrop" className="h-full">
            <div className="h-full flex items-center justify-center bg-slate-100 rounded-lg border-2 border-dashed border-slate-300">
              <div className="text-center text-slate-500">
                <ImageIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>OutcropLens</p>
                <p className="text-sm">Field photo analysis</p>
              </div>
            </div>
          </Tabs.Content>
          
          <Tabs.Content value="prospect" className="h-full">
            <div className="h-full flex items-center justify-center bg-slate-100 rounded-lg border-2 border-dashed border-slate-300">
              <div className="text-center text-slate-500">
                <Target className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>ProspectDesk</p>
                <p className="text-sm">Decision panel and risk matrix</p>
              </div>
            </div>
          </Tabs.Content>
          
          <Tabs.Content value="governance" className="h-full">
            <div className="h-full p-8">
              <h2 className="text-2xl font-bold mb-4">Constitutional Governance (F1-F13)</h2>
              <div className="prose max-w-none">
                <p>Full governance dashboard with detailed floor status.</p>
              </div>
            </div>
          </Tabs.Content>
          
          <Tabs.Content value="qc" className="h-full">
            <div className="h-full p-8">
              <h2 className="text-2xl font-bold mb-4">QC / Audit Trail</h2>
              <p>VAULT999 integration for immutable audit logs.</p>
            </div>
          </Tabs.Content>
          
          <Tabs.Content value="pilot" className="h-full">
            <MalayBasinPilotDashboard />
          </Tabs.Content>
        </div>
      </Tabs.Root>
      
      {/* Bottom Synchronized Strip */}
      <div className="h-12 bg-slate-100 border-t border-slate-200 flex items-center px-4 gap-4 text-sm">
        <span className="text-slate-500">Cursor:</span>
        <span className="font-mono">Lat: --</span>
        <span className="font-mono">Lon: --</span>
        <span className="font-mono">Trace: --</span>
        <span className="font-mono">Time: --</span>
        <span className="font-mono">Depth: --</span>
        <div className="flex-1" />
        <WitnessBadgesCompact />
      </div>
    </div>
  );
};

// Header component
const Header: React.FC = () => {
  const governance = useGovernance();
  const geoxConnected = useGEOXConnected();
  
  return (
    <header className="h-14 bg-slate-900 text-white flex items-center px-4 justify-between border-b border-white/10 shadow-lg z-50">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-all">
            <Globe className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />
          </div>
          <div>
            <h1 className="font-black text-lg tracking-tight leading-none uppercase">GEOX <span className="text-blue-400">Earth Witness</span></h1>
            <p className="text-[10px] text-slate-500 font-mono tracking-widest mt-0.5">DITEMPA BUKAN DIBERI</p>
          </div>
        </div>

        {/* Trinity Navigation */}
        <nav className="hidden md:flex items-center gap-1 bg-white/5 p-1 rounded-full border border-white/10">
          <HeaderAppLink href="https://arifosmcp.arif-fazil.com" icon={Shield} label="arifOS" />
          <HeaderAppLink href="https://wiki.arif-fazil.com" icon={FileText} label="Ω-Wiki" />
          <HeaderAppLink href="https://vault.arifosmcp.arif-fazil.com" icon={Target} label="Vault" />
        </nav>
      </div>
      
      <div className="flex items-center gap-6 text-sm">
        <div className="hidden lg:flex flex-col items-end mr-2">
           <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Current Context</span>
           <span className="text-white font-medium text-xs">Baram_North / Prospect-K</span>
        </div>
        
        {/* Connection Status Indicator */}
        <div 
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg border border-white/10 group hover:bg-white/10 transition-all cursor-help" 
          title="Sovereign Connection Status"
        >
          <div className={`w-2 h-2 rounded-full ${geoxConnected ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`} />
          <span className="text-[10px] font-mono font-bold tracking-tight">
            {geoxConnected ? 'AF-FORGE ONLINE' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Governance Badge */}
        <div className={`
          px-3 py-1.5 rounded-lg font-black text-[10px] tracking-widest uppercase border transition-all
          ${governance.overallStatus === 'green' ? 'bg-green-500/20 text-green-400 border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.1)]' : ''}
          ${governance.overallStatus === 'amber' ? 'bg-amber-500/20 text-amber-400 border-amber-500/50' : ''}
          ${governance.overallStatus === 'red' ? 'bg-red-500/20 text-red-400 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.1)]' : ''}
          ${governance.overallStatus === 'grey' ? 'bg-white/5 text-slate-400 border-white/10' : ''}
        `}>
          {governance.overallStatus === 'green' ? 'IGNITED' :
           governance.overallStatus === 'amber' ? 'QUALIFY' :
           governance.overallStatus === 'red' ? 'HOLD' : 'INITIALIZING'}
        </div>
      </div>
    </header>
  );
};

// Internal Header Link component
const HeaderAppLink: React.FC<{ href: string; icon: React.ElementType; label: string }> = ({ href, icon: Icon, label }) => (
  <a 
    href={href} 
    target="_blank" 
    rel="noopener noreferrer"
    className="flex items-center gap-1.5 px-3 py-1 text-[10px] font-bold text-slate-400 hover:text-white hover:bg-white/10 rounded-full transition-all uppercase tracking-tighter"
  >
    <Icon className="w-3 h-3" />
    {label}
  </a>
);

// Toolbar
const Toolbar: React.FC = () => (
  <div className="h-10 bg-white border-b border-slate-200 flex items-center px-2 gap-1">
    <ToolbarButton icon={Search} label="Search" />
    <ToolbarDivider />
    <ToolbarButton icon={Map} label="Layers" />
    <ToolbarButton icon={AlignLeft} label="Wells" />
    <ToolbarButton icon={Activity} label="Seismic" />
    <ToolbarButton icon={AlignLeft} label="Logs" />
    <ToolbarButton icon={ImageIcon} label="Outcrop" />
    <ToolbarButton icon={Target} label="Prospect" />
    <ToolbarDivider />
    <ToolbarButton icon={Globe} label="3D" />
    <ToolbarDivider />
    <ToolbarButton icon={Shield} label="QC" />
    <ToolbarButton icon={FileText} label="Export" />
    <div className="flex-1" />
    <ToolbarButton icon={Settings} label="Settings" />
  </div>
);

const ToolbarButton: React.FC<{ icon: React.ElementType; label: string }> = ({ icon: Icon, label }) => (
  <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100 rounded">
    <Icon className="w-4 h-4" />
    <span className="hidden xl:inline">{label}</span>
  </button>
);

const ToolbarDivider: React.FC = () => (
  <Separator.Root className="w-px h-6 bg-slate-300 mx-1" orientation="vertical" />
);

// Main Layout
export const MainLayout: React.FC = () => {
  return (
    <div className="h-screen flex flex-col bg-white">
      <Header />
      <Toolbar />
      <div className="flex-1 flex overflow-hidden">
        <LeftSidebar />
        <MainWorkspace />
        <RightSidebar />
      </div>
    </div>
  );
};

export default MainLayout;