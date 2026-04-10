/**
 * MainLayout — GEOX Earth Intelligence Core
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 * 
 * Simplified three-panel layout:
 * - Left: Data/Layers sidebar
 * - Center: Main workspace (4 apps)
 * - Right: Governance panel
 * 
 * EIC Tabs: 5 total (4 apps + pilot)
 */

import React, { useState } from 'react';
import { 
  Map, Activity, AlignLeft, Gauge, Target,
  ChevronLeft, ChevronRight, Search, Shield,
  Settings, FileText
} from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import * as Separator from '@radix-ui/react-separator';
import { WitnessBadges, WitnessBadgesCompact } from '../WitnessBadges/WitnessBadges';
import { EarthWitness } from '../EarthWitness/EarthWitness';
import { MalayBasinPilotDashboard } from '../MalayBasinPilot/MalayBasinPilotDashboard';
import { LogDock } from '../LogDock/LogDock';
import { AppIframeHost } from '../EarthWitness/AppIframeHost';
import { useGEOXStore, useActiveTab, useGovernance, useGEOXConnected } from '../../store/geoxStore';
import type { Tab } from '../../types';


// ═══════════════════════════════════════════════════════════════════════════════
// Tab Configuration — EIC Aligned (5 tabs: 4 apps + pilot)
// ═══════════════════════════════════════════════════════════════════════════════

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'basin', label: 'Basin Explorer', icon: Map },
  { id: 'seismic', label: 'Seismic Viewer', icon: Activity },
  { id: 'wells', label: 'Well Context Desk', icon: AlignLeft },
  { id: 'acrisk', label: 'AC_Risk Console', icon: Gauge },
  { id: 'pilot', label: 'Malay Basin Pilot', icon: Target },
];

// ═══════════════════════════════════════════════════════════════════════════════
// Left Sidebar — Data/Layers
// ═══════════════════════════════════════════════════════════════════════════════

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
              <LayerItem name="Seismic Lines" />
              <LayerItem name="Fields" />
              <LayerItem name="License Blocks" />
            </div>
          </div>
          
          {/* Filters */}
          <div className="p-3 border-t border-slate-200">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Filters</h4>
            <div className="space-y-2 text-sm">
              <select className="w-full p-1.5 border border-slate-300 rounded text-sm" title="Play Type">
                <option>All Play Types</option>
                <option>Clastic Reservoirs</option>
                <option>Carbonate Buildups</option>
              </select>
              <select className="w-full p-1.5 border border-slate-300 rounded text-sm" title="Status">
                <option>All Statuses</option>
                <option>Producing</option>
                <option>Development</option>
                <option>Exploration</option>
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const LayerItem: React.FC<{ name: string; checked?: boolean }> = ({ name, checked = false }) => (
  <label className="flex items-center gap-2 p-1.5 hover:bg-slate-100 rounded cursor-pointer">
    <input type="checkbox" defaultChecked={checked} className="rounded border-slate-300" />
    <span className="text-sm text-slate-700">{name}</span>
  </label>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Right Sidebar — Governance
// ═══════════════════════════════════════════════════════════════════════════════

const RightSidebar: React.FC = () => (
  <div className="w-80 flex flex-col bg-white border-l border-slate-200">
    <div className="p-3 border-b border-slate-200 bg-slate-50">
      <h3 className="font-bold text-slate-800 flex items-center gap-2">
        <Shield className="w-4 h-4" />
        Constitutional Governance
      </h3>
    </div>
    <div className="flex-1 overflow-auto">
      <WitnessBadges />
    </div>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// Main Workspace — The 4 Apps
// ═══════════════════════════════════════════════════════════════════════════════

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
        
        {/* Tab Content — The 4 MCP Apps */}
        <div className="flex-1 overflow-hidden">
          {/* Basin Explorer */}
          <Tabs.Content value="basin" className="h-full">
            <AppIframeHost 
              src="/apps/basin_explorer/index.html" 
              title="Basin Explorer" 
              appId="geox.basin.explorer" 
            />
          </Tabs.Content>
          
          {/* Seismic Viewer */}
          <Tabs.Content value="seismic" className="h-full">
            <AppIframeHost 
              src="/apps/seismic_viewer/index.html" 
              title="Seismic Viewer" 
              appId="geox.seismic.viewer" 
            />
          </Tabs.Content>
          
          {/* Well Context Desk */}
          <Tabs.Content value="wells" className="h-full">
            <AppIframeHost 
              src="/apps/well_context_desk/index.html" 
              title="Well Context Desk" 
              appId="geox.well.context-desk" 
            />
          </Tabs.Content>
          
          {/* AC_Risk Console */}
          <Tabs.Content value="acrisk" className="h-full">
            <AppIframeHost 
              src="/apps/ac_risk_console/index.html" 
              title="AC_Risk Console" 
              appId="geox.ac_risk.console" 
            />
          </Tabs.Content>
          
          {/* Malay Basin Pilot */}
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
        <span className="font-mono">AC_Risk: --</span>
        <span className="font-mono">Verdict: --</span>
        <div className="flex-1" />
        <WitnessBadgesCompact />
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// Header
// ═══════════════════════════════════════════════════════════════════════════════

const Header: React.FC = () => {
  const governance = useGovernance();
  const geoxConnected = useGEOXConnected();
  
  return (
    <header className="h-14 bg-slate-900 text-white flex items-center px-4 justify-between border-b border-white/10 shadow-lg z-50">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="p-2 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-all">
            <Gauge className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />
          </div>
          <div>
            <h1 className="font-black text-lg tracking-tight leading-none uppercase">GEOX <span className="text-blue-400">EIC</span></h1>
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
        {/* Connection Status */}
        <div 
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg border border-white/10 group hover:bg-white/10 transition-all cursor-help" 
          title="MCP Server Status"
        >
          <div className={`w-2 h-2 rounded-full ${geoxConnected ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`} />
          <span className="text-[10px] font-mono font-bold tracking-tight">
            {geoxConnected ? 'EIC ONLINE' : 'DISCONNECTED'}
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
          {governance.overallStatus === 'green' ? 'SEAL' :
           governance.overallStatus === 'amber' ? 'QUALIFY' :
           governance.overallStatus === 'red' ? 'HOLD' : 'INITIALIZING'}
        </div>
      </div>
    </header>
  );
};

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

// ═══════════════════════════════════════════════════════════════════════════════
// Toolbar
// ═══════════════════════════════════════════════════════════════════════════════

const Toolbar: React.FC = () => (
  <div className="h-10 bg-white border-b border-slate-200 flex items-center px-2 gap-1">
    <ToolbarButton icon={Search} label="Search" />
    <ToolbarDivider />
    <ToolbarButton icon={Map} label="Basin" />
    <ToolbarButton icon={Activity} label="Seismic" />
    <ToolbarButton icon={AlignLeft} label="Wells" />
    <ToolbarButton icon={Gauge} label="AC_Risk" />
    <ToolbarDivider />
    <ToolbarButton icon={Target} label="Pilot" />
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

// ═══════════════════════════════════════════════════════════════════════════════
// Main Layout
// ═══════════════════════════════════════════════════════════════════════════════

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
