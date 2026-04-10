import React from 'react';
import { 
  TrendingUp, 
  Database, 
  Target, 
  Layers, 
  Info,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

/**
 * MalayBasinPilotDashboard
 * 
 * Visual GUOI for the Malay Basin exploration demo.
 * Displays key metrics, play types, and exploration phases.
 */
export const MalayBasinPilotDashboard: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-slate-950 text-slate-200 overflow-hidden">
      {/* Header Section */}
      <div className="p-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-3xl font-black tracking-tighter text-white uppercase italic">
              Malay Basin <span className="text-blue-500">Pilot</span>
            </h2>
            <p className="text-slate-400 text-sm mt-1 font-mono tracking-widest uppercase">
              Petroleum Exploration Cycle: 1968–2018
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/30 rounded-full text-[10px] font-bold text-blue-400 uppercase tracking-widest">
            <ShieldCheck className="w-3 h-3" />
            GSM Validated Data
          </div>
        </div>

        {/* Rapid Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          <MetricCard 
            label="Total Discoveries" 
            value="181+" 
            sub="Oil & Gas Fields"
            icon={Target}
            color="text-blue-400"
          />
          <MetricCard 
            label="Commulative Resource" 
            value="14.8" 
            sub="BBOE Discovered"
            icon={Database}
            color="text-emerald-400"
          />
          <MetricCard 
            label="Wells Drilled" 
            value="2,100" 
            sub="700 Exploratory"
            icon={Layers}
            color="text-amber-400"
          />
          <MetricCard 
            label="National Share" 
            value="40%" 
            sub="Of Hydrocarbon Resources"
            icon={TrendingUp}
            color="text-purple-400"
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto p-6 space-y-8">
        
        {/* Play Types Analysis */}
        <section>
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Layers className="w-3 h-3" />
            Play Classification (P1–P9)
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <PlayCard 
              code="P1" 
              type="Basin-centre anticline" 
              fields="Tapis, Jerneh, Dulang" 
              share="60%"
              accent="bg-blue-500"
              median="191.6 MMboe"
            />
            <PlayCard 
              code="P3" 
              type="Normal fault / dip closure" 
              fields="Bergading, Abu" 
              share="Medium"
              accent="bg-emerald-500"
              median="52 MMboe"
            />
            <PlayCard 
              code="P9" 
              type="Deep HPHT / Tight" 
              fields="Bergading Deep, Sepat" 
              share="Emerging"
              accent="bg-orange-500"
              status="Frontier"
            />
          </div>
        </section>

        {/* Creaming Curve / EDP Phases */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
              <TrendingUp className="w-3 h-3" />
              Exploration & Discovery (EDP) Phases
            </h3>
            <div className="space-y-3">
              <EDPItem 
                phase="EDP 1" 
                period="1968–1976" 
                title="Basin-centre anticlinal play" 
                outcome="~8.7 BBOE (60% of total)" 
                active 
              />
              <EDPItem 
                phase="EDP 2" 
                period="1977–1989" 
                title="Giant fields plateau" 
                outcome="Basin-centre exhaustion" 
              />
              <EDPItem 
                phase="EDP 3" 
                period="1990–2000" 
                title="Flank plays rejuvenation" 
                outcome="+1.5 BBOE (NE Ramp, JDA)" 
              />
              <EDPItem 
                phase="EDP 5" 
                period="2011–2018" 
                title="Residual mop-up phase" 
                outcome="HPHT, Tight Sands, Basement" 
              />
            </div>
          </div>

          {/* Visual Trend Placeholder */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 flex flex-col items-center justify-center min-h-[300px] group hover:border-blue-500/50 transition-all">
            <div className="w-full h-full flex flex-col items-center justify-center opacity-40 group-hover:opacity-100 transition-opacity">
              <div className="w-full h-40 flex items-end gap-1 px-4">
                <div className="flex-1 bg-blue-500 h-[100%] rounded-t" />
                <div className="flex-1 bg-blue-500/80 h-[40%] rounded-t" />
                <div className="flex-1 bg-blue-500/60 h-[25%] rounded-t" />
                <div className="flex-1 bg-blue-500/40 h-[15%] rounded-t" />
                <div className="flex-1 bg-blue-500/20 h-[10%] rounded-t" />
              </div>
              <p className="mt-4 text-xs font-mono text-slate-500 uppercase tracking-widest">Creaming Curve Decline</p>
            </div>
            <div className="mt-6 flex gap-4 text-[10px] text-slate-400">
              <div className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-500 rounded-sm" /> Discoveries</div>
              <div className="flex items-center gap-1"><div className="w-2 h-2 bg-slate-700 rounded-sm" /> Forecast</div>
            </div>
          </div>
        </section>

        {/* Nodal Infrastructure */}
        <section className="bg-gradient-to-br from-blue-900/20 to-slate-900/20 border border-blue-500/20 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-white font-bold text-lg">Subsurface Reality Check</h4>
              <p className="text-slate-400 text-sm italic">Remaining Potential: ~2.0 BBOE (2020 projection)</p>
            </div>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors">
              EXECUTE SCENARIO
            </button>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
             <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase tracking-tighter">Sustain Rate</p>
                <p className="text-sm font-bold text-slate-300">120 MMboe / Year</p>
             </div>
             <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase tracking-tighter">Min. Activity</p>
                <p className="text-sm font-bold text-slate-300">5+ Wells / Year</p>
             </div>
             <div className="p-3 bg-black/40 rounded-xl border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase tracking-tighter">Median Field</p>
                <p className="text-sm font-bold text-slate-300">&lt; 25 MMboe</p>
             </div>
          </div>
        </section>

      </div>

      {/* Footer Info */}
      <div className="p-4 bg-black/20 border-t border-slate-900 text-[10px] flex justify-between items-center text-slate-500 font-mono">
        <div className="flex items-center gap-2">
           <Info className="w-3 h-3" />
           DATA SRC: GSM-702001 (PETRONAS / GSM ARCHIVES)
        </div>
        <div className="uppercase tracking-widest">
           SEAL: DITEMPA BUKAN DIBERI
        </div>
      </div>
    </div>
  );
};

/* --- Subcomponents --- */

const MetricCard: React.FC<{ label: string; value: string; sub: string; icon: React.ElementType; color: string }> = ({ 
  label, value, sub, icon: Icon, color 
}) => (
  <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl hover:border-slate-700 transition-colors group">
    <div className="flex justify-between items-start">
      <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">{label}</p>
      <Icon className={`w-4 h-4 ${color} opacity-50`} />
    </div>
    <p className={`text-2xl font-black mt-1 ${color}`}>{value}</p>
    <p className="text-[10px] text-slate-500 mt-1 uppercase truncate">{sub}</p>
  </div>
);

const PlayCard: React.FC<{ code: string; type: string; fields: string; share: string; accent: string; median?: string; status?: string }> = ({
  code, type, fields, share, accent, median, status
}) => (
  <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform">
    <div className={`absolute top-0 left-0 w-1 h-full ${accent}`} />
    <div className="flex justify-between items-center mb-2">
      <span className={`px-2 py-0.5 rounded text-[10px] font-black text-white ${accent}`}>{code}</span>
      <span className="text-[10px] font-mono text-slate-500 uppercase">{share}</span>
    </div>
    <h4 className="text-sm font-bold text-white mb-2 leading-tight">{type}</h4>
    <p className="text-[10px] text-slate-400 mb-4 line-clamp-2">Example: {fields}</p>
    <div className="flex items-center justify-between mt-auto pt-2 border-t border-slate-800">
       <span className="text-[10px] text-slate-500 uppercase">Median Size</span>
       <span className="text-xs font-mono text-white">{median || status || 'N/A'}</span>
    </div>
  </div>
);

const EDPItem: React.FC<{ phase: string; period: string; title: string; outcome: string; active?: boolean }> = ({
  phase, period, title, outcome, active
}) => (
  <div className={`flex items-center gap-4 p-3 rounded-xl border ${active ? 'bg-blue-500/10 border-blue-500/30' : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'} transition-all group`}>
    <div className="w-16 text-center">
       <p className={`text-[10px] font-black ${active ? 'text-blue-400' : 'text-slate-500'}`}>{phase}</p>
       <p className="text-[8px] text-slate-600 font-mono">{period}</p>
    </div>
    <div className="flex-1">
      <h5 className="text-xs font-bold text-slate-200">{title}</h5>
      <p className="text-[10px] text-slate-500">{outcome}</p>
    </div>
    <ChevronRight className="w-4 h-4 text-slate-700 group-hover:text-slate-400 transition-colors" />
  </div>
);
