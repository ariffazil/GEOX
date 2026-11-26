/**
 * TemporalAnimation — Basin Lifecycle Time-Slider with MCP-wired Temporal Tools
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Wires useMcpTool to 4 temporal MCP tools:
 *  - geox_temporal_decline (exponential decline curve)
 *  - geox_temporal_rrr (reserve replacement ratio)
 *  - geox_temporal_basin_lifecycle (lifecycle stage classification)
 *  - geox_temporal_cadence (exploration licensing cadence)
 *
 * Renders:
 *  - Interactive time slider with basin lifecycle animation
 *  - Decline curve chart (canvas-based)
 *  - RRR gauge
 *  - Lifecycle stage indicator
 *  - Cadence metrics
 */

import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import {
  Clock, Play, Pause, SkipBack, SkipForward, BarChart2, Activity,
  TrendingDown, Target, Calendar, Gauge, Layers, RefreshCw,
  CheckCircle, AlertTriangle, Loader2
} from 'lucide-react';
import { useMcpTool } from '../../hooks/useMcpTool';
import { useGEOXStore } from '../../store/geoxStore';

// ─────────────────────────────────────────────────────────────────────────────
// Types for temporal MCP results
// ─────────────────────────────────────────────────────────────────────────────

interface DeclineResult {
  annual_decline_rate?: number;
  trend?: string;
  forecast?: Array<{ year: number; rate_bpd: number }>;
  years_to_threshold?: number;
  threshold_bpd?: number;
}

interface RRRResult {
  rrr?: number;
  reserves_end?: number;
  years_at_current_rate?: number;
  verdict?: string;
}

interface LifecycleResult {
  lifecycle_stage?: string;
  remaining_potential_pct?: number;
  decline_rate?: number;
  verdict?: string;
}

interface CadenceResult {
  award_rate_pct?: number;
  pipeline_lag_years?: number;
  capacity_gap?: string;
  production_impact?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Decline Curve Canvas
// ─────────────────────────────────────────────────────────────────────────────

const DeclineCurve: React.FC<{ data: DeclineResult | null; loading: boolean }> = ({ data, loading }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const width = 420;
  const height = 200;
  const margin = { top: 15, right: 15, bottom: 30, left: 55 };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr; canvas.height = height * dpr;
    canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#020617'; ctx.fillRect(0, 0, width, height);

    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;

    ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 1;
    ctx.strokeRect(margin.left, margin.top, plotW, plotH);

    if (!data?.forecast || data.forecast.length === 0) {
      ctx.fillStyle = '#64748b'; ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(loading ? 'Computing…' : 'No decline data — run compute', width / 2, height / 2);
      return;
    }

    const years = data.forecast.map((f) => f.year);
    const rates = data.forecast.map((f) => f.rate_bpd);
    const xScale = d3.scaleLinear().domain(d3.extent(years) as [number, number]).range([margin.left, margin.left + plotW]);
    const yScale = d3.scaleLinear().domain([0, d3.max(rates) ?? 1]).range([margin.top + plotH, margin.top]);

    // Grid
    ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 0.5;
    for (let i = 0; i <= 5; i++) {
      const y = margin.top + (plotH * i) / 5;
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotW, y); ctx.stroke();
    }

    // Line
    ctx.beginPath();
    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 2;
    let started = false;
    for (let i = 0; i < data.forecast.length; i++) {
      const x = xScale(data.forecast[i].year);
      const y = yScale(data.forecast[i].rate_bpd);
      if (!started) { ctx.moveTo(x, y); started = true; }
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Labels
    ctx.fillStyle = '#94a3b8'; ctx.font = '9px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${d3.max(rates)?.toLocaleString()} bpd`, margin.left + 2, margin.top + 10);
    ctx.textAlign = 'center';
    data.forecast.filter((_, i) => i % 2 === 0).forEach((f) => {
      ctx.fillText(`${f.year}`, xScale(f.year), margin.top + plotH + 16);
    });

    // Threshold line
    if (data.threshold_bpd) {
      const ty = yScale(data.threshold_bpd);
      ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(margin.left, ty); ctx.lineTo(margin.left + plotW, ty); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#f59e0b'; ctx.font = '9px monospace';
      ctx.fillText(`Threshold: ${data.threshold_bpd.toLocaleString()}`, margin.left + 2, ty - 4);
    }

    ctx.fillStyle = '#e2e8f0'; ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Production Decline Forecast', margin.left + plotW / 2, 14);
  }, [data, loading]);

  return <canvas ref={canvasRef} className="rounded-lg border border-slate-800" style={{ width: `${width}px`, height: `${height}px` }} />;
};

// ─────────────────────────────────────────────────────────────────────────────
// Gauge component for RRR
// ─────────────────────────────────────────────────────────────────────────────

const RRRGauge: React.FC<{ rrr: number | null | undefined; loading: boolean }> = ({ rrr, loading }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const size = 120;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr; canvas.height = size * dpr;
    canvas.style.width = `${size}px`; canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, size, size);
    const cx = size / 2; const cy = size / 2 + 5; const r = 45;

    // Arc background
    ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, 0); ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 10; ctx.stroke();

    if (rrr != null && !loading) {
      const ratio = Math.min(rrr / 2, 1);
      const angle = Math.PI + ratio * Math.PI;
      const color = rrr >= 1.0 ? '#22c55e' : rrr >= 0.5 ? '#f59e0b' : '#ef4444';
      ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI, angle); ctx.strokeStyle = color; ctx.lineWidth = 10; ctx.stroke();

      ctx.fillStyle = '#e2e8f0'; ctx.font = 'bold 20px monospace';
      ctx.textAlign = 'center'; ctx.fillText(rrr.toFixed(2), cx, cy + 4);
      ctx.font = '9px sans-serif'; ctx.fillStyle = '#94a3b8';
      ctx.fillText('RRR', cx, cy + 18);
    } else {
      ctx.fillStyle = '#64748b'; ctx.font = '11px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(loading ? '…' : '—', cx, cy + 4);
    }

    // Tick marks
    ctx.font = '8px monospace'; ctx.fillStyle = '#475569'; ctx.textAlign = 'center';
    ctx.fillText('0', cx - r + 5, cy + 22);
    ctx.fillText('1', cx, cy - r + 10);
    ctx.fillText('2', cx + r - 5, cy + 22);
  }, [rrr, loading]);

  return <canvas ref={canvasRef} style={{ width: `${size}px`, height: `${size}px` }} />;
};

// ─────────────────────────────────────────────────────────────────────────────
// Main TemporalAnimation Component
// ─────────────────────────────────────────────────────────────────────────────

export const TemporalAnimation: React.FC = () => {
  const { updateFloorStatus } = useGEOXStore();
  const [playing, setPlaying] = useState(false);
  const [currentYear, setCurrentYear] = useState(2024);
  const [maxYear] = useState(2034);
  const [minYear] = useState(2010);

  // MCP tools
  const declineTool = useMcpTool<{
    production_data: Array<{ year: number; rate_bpd: number }>;
    forecast_years: number;
    threshold_bpd: number;
  }, DeclineResult>('geox_temporal_decline');

  const rrrTool = useMcpTool<{
    reserves_start: number;
    additions: number;
    production: number;
  }, RRRResult>('geox_temporal_rrr');

  const lifecycleTool = useMcpTool<{
    basin_name: string;
    peak_production: number;
    current_production: number;
    discovery_year: number;
    peak_year: number;
  }, LifecycleResult>('geox_temporal_basin_lifecycle');

  const cadenceTool = useMcpTool<{
    blocks_offered: number;
    blocks_awarded: number;
    years_span: number;
    average_cycle_time_years: number;
  }, CadenceResult>('geox_temporal_cadence');

  const computeAll = useCallback(async () => {
    try {
      updateFloorStatus('F4', 'amber', 'Computing temporal metrics…');

      // Synthetic Malay Basin production data (2010-2024)
      const prodData = [
        { year: 2010, rate_bpd: 550000 },
        { year: 2012, rate_bpd: 520000 },
        { year: 2014, rate_bpd: 490000 },
        { year: 2016, rate_bpd: 460000 },
        { year: 2018, rate_bpd: 430000 },
        { year: 2020, rate_bpd: 400000 },
        { year: 2022, rate_bpd: 380000 },
        { year: 2024, rate_bpd: 350000 },
      ];

      await Promise.allSettled([
        declineTool.call({ production_data: prodData, forecast_years: 10, threshold_bpd: 250000 }),
        rrrTool.call({ reserves_start: 5000, additions: 200, production: 400 }),
        lifecycleTool.call({ basin_name: 'Malay Basin', peak_production: 550000, current_production: 350000, discovery_year: 1968, peak_year: 1979 }),
        cadenceTool.call({ blocks_offered: 15, blocks_awarded: 8, years_span: 5, average_cycle_time_years: 4.5 }),
      ]);

      updateFloorStatus('F4', 'green', 'Temporal metrics computed');
    } catch (err) {
      updateFloorStatus('F4', 'red', `Temporal compute failed: ${String(err)}`);
    }
  }, [declineTool, rrrTool, lifecycleTool, cadenceTool, updateFloorStatus]);

  useEffect(() => { computeAll(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Animation loop
  useEffect(() => {
    if (!playing) return;
    const interval = setInterval(() => {
      setCurrentYear((y) => {
        if (y >= maxYear) {
          setPlaying(false);
          return maxYear;
        }
        return y + 1;
      });
    }, 800);
    return () => clearInterval(interval);
  }, [playing, maxYear]);

  const isLoading = declineTool.status === 'loading' || rrrTool.status === 'loading'
    || lifecycleTool.status === 'loading' || cadenceTool.status === 'loading';

  const lifecycleStage = lifecycleTool.data?.lifecycle_stage ?? 'Unknown';
  const remainingPct = lifecycleTool.data?.remaining_potential_pct ?? 0;
  const awardRate = cadenceTool.data?.award_rate_pct ?? 0;

  const stageColor =
    lifecycleStage === 'growth' ? '#22c55e'
    : lifecycleStage === 'plateau' ? '#3b82f6'
    : lifecycleStage === 'mature' ? '#f59e0b'
    : lifecycleStage === 'decline' ? '#ef4444'
    : '#64748b';

  const yearFraction = (currentYear - minYear) / (maxYear - minYear);

  return (
    <div className="h-full flex flex-col bg-[#020617] text-slate-300 overflow-hidden">
      {/* Header */}
      <div className="h-14 border-b border-slate-800 bg-slate-900/30 flex items-center px-6 justify-between flex-shrink-0">
        <div>
          <div className="flex items-center gap-2 text-xs font-black text-blue-500 uppercase tracking-[0.2em] mb-0.5">
            <Clock className="w-3 h-3" />
            <span>Dimension_5: Chronos_4D</span>
          </div>
          <h2 className="text-lg font-black text-white leading-none uppercase tracking-tighter italic">
            Basin Lifecycle Animation
          </h2>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 rounded-full px-4 py-1.5">
          <button onClick={() => setCurrentYear(minYear)} className="text-slate-500 hover:text-white transition-colors">
            <SkipBack className="w-4 h-4" />
          </button>
          <button
            onClick={() => setPlaying(!playing)}
            className="w-8 h-8 flex items-center justify-center bg-blue-600 rounded-full text-white hover:bg-blue-500 transition-all"
          >
            {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
          </button>
          <button onClick={() => { setCurrentYear(maxYear); setPlaying(false); }} className="text-slate-500 hover:text-white transition-colors">
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={computeAll} disabled={isLoading}
            className="p-2 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <div className="text-right">
            <span className="block text-[10px] text-slate-500 uppercase font-black">Year</span>
            <span className="text-blue-400 font-mono text-sm">{currentYear}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6 space-y-4">
        {/* Time Slider */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase">Timeline</span>
            <span className="text-xs text-slate-600 font-mono">{minYear} – {maxYear}</span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden cursor-pointer relative"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const frac = (e.clientX - rect.left) / rect.width;
              setCurrentYear(Math.round(minYear + frac * (maxYear - minYear)));
            }}>
            <div className="h-full bg-gradient-to-r from-green-500 via-amber-500 to-red-500 transition-all duration-300"
              style={{ width: `${yearFraction * 100}%` }} />
            <div className="absolute top-0 w-3 h-3 bg-white rounded-full shadow-lg -mt-0.5 transition-all duration-300"
              style={{ left: `${yearFraction * 100}%`, transform: 'translateX(-50%)' }} />
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Gauge className="w-4 h-4" style={{ color: stageColor }} />
              <span className="text-xs font-bold text-slate-500 uppercase">Lifecycle Stage</span>
            </div>
            <div className="text-2xl font-black" style={{ color: stageColor }}>{lifecycleStage}</div>
            <div className="text-xs text-slate-600 mt-1">{remainingPct.toFixed(0)}% remaining potential</div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-4 h-4 text-red-400" />
              <span className="text-xs font-bold text-slate-500 uppercase">Annual Decline</span>
            </div>
            <div className="text-2xl font-black text-red-400">
              {declineTool.data?.annual_decline_rate != null
                ? `${(declineTool.data.annual_decline_rate * 100).toFixed(1)}%`
                : '—'}
            </div>
            <div className="text-xs text-slate-600 mt-1">{declineTool.data?.years_to_threshold ?? '—'} yrs to threshold</div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col items-center">
            <span className="text-xs font-bold text-slate-500 uppercase mb-2">Reserve Replacement</span>
            <RRRGauge rrr={rrrTool.data?.rrr} loading={rrrTool.status === 'loading'} />
            <span className="text-xs text-slate-600 mt-1">Yrs reserve: {rrrTool.data?.years_at_current_rate ?? '—'}</span>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-slate-500 uppercase">Licensing Cadence</span>
            </div>
            <div className="text-2xl font-black text-cyan-400">{awardRate > 0 ? `${awardRate.toFixed(0)}%` : '—'}</div>
            <div className="text-xs text-slate-600 mt-1">Award rate · {cadenceTool.data?.capacity_gap ?? '—'} capacity</div>
          </div>
        </div>

        {/* Decline Curve */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
          <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Decline Forecast</h4>
          <DeclineCurve data={declineTool.data} loading={declineTool.status === 'loading'} />
        </div>

        {/* Timeline bar visualization */}
        <div className="w-full max-w-2xl mx-auto h-12 flex items-end gap-0.5">
          {[...Array(24)].map((_, i) => {
            const yr = minYear + i;
            const h = yr <= currentYear ? 20 + Math.abs(Math.sin(i * 0.5)) * 60 : 10;
            const color = yr <= currentYear ? (yr >= 2020 ? '#ef4444' : yr >= 2014 ? '#f59e0b' : '#22c55e') : '#334155';
            return (
              <div key={i} className="flex-1 rounded-t-sm transition-all duration-500"
                style={{ height: `${h}%`, backgroundColor: color }} />
            );
          })}
        </div>
        <div className="w-full max-w-2xl mx-auto flex justify-between text-[10px] font-mono text-slate-600">
          <span>{minYear}</span>
          <span>{minYear + 8}</span>
          <span>{minYear + 16}</span>
          <span>{maxYear}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="h-8 bg-black/40 border-t border-slate-800 flex items-center px-4 gap-4 text-[10px] uppercase font-black text-slate-600 flex-shrink-0">
        <span>MCP: geox_temporal_* (4 tools)</span>
        {isLoading && <span className="text-amber-400"><Loader2 className="w-3 h-3 inline animate-spin mr-1" />Computing…</span>}
        <div className="flex-1" />
        <span className="text-amber-500/70">DITEMPA BUKAN DIBERI</span>
      </div>
    </div>
  );
};

export default TemporalAnimation;
