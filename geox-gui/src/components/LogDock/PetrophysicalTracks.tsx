/**
 * PetrophysicalTracks — MCP-wired Petrophysical Interpretation Panel
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Wires the useMcpTool hook to geox_petrophysics (mode=generate) for
 * Vsh, PHIe, Sw, DT curve computation with cutoff overlays.
 *
 * Renders:
 *  - GR track with VSH fill overlay
 *  - NPHI/RHOB crossover track
 *  - DT (sonic) track
 *  - PHIe + Sw computed track
 *  - Cutoff lines: Vsh=0.5, PHIe=0.1, Sw=0.6
 */

import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import {
  FlaskConical, Gauge, Droplets, Activity, RefreshCw,
  ChevronDown, ChevronUp, AlertTriangle, CheckCircle, Loader2
} from 'lucide-react';
import { useMcpTool } from '../../hooks/useMcpTool';
import { useGEOXStore } from '../../store/geoxStore';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface PetrophysicalResult {
  vsh?: number[];
  phie?: number[];
  sw?: number[];
  dt_synth?: number[];
  litho_class?: string;
  pay_flags?: boolean[];
  depth?: number[];
  receipt_hash?: string;
  perception_class?: string;
  evidence_tag?: string;
  canon_9_touched?: string[];
  vertical_trend?: string;
  litho_class_result?: string;
}

interface TrackDef {
  id: string;
  title: string;
  curves: string[];
  colors: Record<string, string>;
  xMin: number;
  xMax: number;
  units: Record<string, string>;
}

const TRACKS: TrackDef[] = [
  {
    id: 'gr-vsh',
    title: 'GR / VSH',
    curves: ['VSH'],
    colors: { VSH: '#f59e0b', GR: '#22c55e' },
    xMin: 0,
    xMax: 1,
    units: { VSH: 'v/v' },
  },
  {
    id: 'nd',
    title: 'NPHI / RHOB',
    curves: ['NPHI', 'RHOB'],
    colors: { NPHI: '#3b82f6', RHOB: '#a855f7' },
    xMin: 0,
    xMax: 1,
    units: { NPHI: 'v/v', RHOB: 'g/cm³' },
  },
  {
    id: 'dt',
    title: 'DT Sonic',
    curves: ['DT'],
    colors: { DT: '#ec4899' },
    xMin: 40,
    xMax: 140,
    units: { DT: 'μs/ft' },
  },
  {
    id: 'computed',
    title: 'PHIe / Sw',
    curves: ['PHIE', 'SW'],
    colors: { PHIE: '#3b82f6', SW: '#06b6d4' },
    xMin: 0,
    xMax: 1,
    units: { PHIE: 'v/v', SW: 'v/v' },
  },
];

const CUTOFFS = {
  vsh: 0.5,
  phi: 0.1,
  sw: 0.6,
};

// ─────────────────────────────────────────────────────────────────────────────
// Single Track Canvas
// ─────────────────────────────────────────────────────────────────────────────

const PetrophysicalTrackRenderer: React.FC<{
  track: TrackDef;
  depth: number[];
  curves: Record<string, (number | null)[]>;
  depthRange: [number, number];
  cursorDepth: number | null;
  onCursorMove: (depth: number | null) => void;
}> = ({ track, depth, curves, depthRange, cursorDepth, onCursorMove }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const width = 150;
  const height = 500;
  const margin = { top: 30, right: 10, bottom: 20, left: 45 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.strokeRect(margin.left, margin.top, plotWidth, plotHeight);

    const yScale = d3.scaleLinear()
      .domain(depthRange)
      .range([margin.top, margin.top + plotHeight]);

    // Depth grid
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 0.5;
    for (let d = Math.ceil(depthRange[0] / 50) * 50; d <= depthRange[1]; d += 50) {
      const y = yScale(d);
      ctx.beginPath();
      ctx.moveTo(margin.left, y);
      ctx.lineTo(margin.left + plotWidth, y);
      ctx.stroke();
    }

    // Draw each curve
    track.curves.forEach((curveName) => {
      const curveData = curves[curveName];
      if (!curveData) return;

      const xScale = d3.scaleLinear()
        .domain([track.xMin, track.xMax])
        .range([margin.left + 2, margin.left + plotWidth - 2]);

      // Fill between curve and left edge
      ctx.beginPath();
      let first = true;
      const baselineX = xScale(track.xMin);
      for (let i = 0; i < depth.length; i++) {
        const d = depth[i];
        if (d < depthRange[0] || d > depthRange[1]) continue;
        const val = curveData[i];
        if (val == null || val === undefined) continue;
        const y = yScale(d);
        const x = xScale(Math.min(Math.max(val, track.xMin), track.xMax));
        if (first) {
          ctx.moveTo(baselineX, y);
          first = false;
        }
        ctx.lineTo(x, y);
      }
      for (let i = depth.length - 1; i >= 0; i--) {
        const d = depth[i];
        if (d < depthRange[0] || d > depthRange[1]) continue;
        ctx.lineTo(baselineX, yScale(d));
      }
      ctx.closePath();
      ctx.fillStyle = track.colors[curveName];
      ctx.globalAlpha = 0.12;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Line
      ctx.beginPath();
      ctx.strokeStyle = track.colors[curveName];
      ctx.lineWidth = 2;
      let started = false;
      for (let i = 0; i < depth.length; i++) {
        const d = depth[i];
        if (d < depthRange[0] || d > depthRange[1]) continue;
        const val = curveData[i];
        if (val == null || val === undefined) { started = false; continue; }
        const y = yScale(d);
        const x = xScale(Math.min(Math.max(val, track.xMin), track.xMax));
        if (!started) { ctx.moveTo(x, y); started = true; }
        else { ctx.lineTo(x, y); }
      }
      ctx.stroke();
    });

    // Cutoff lines
    if (track.id === 'gr-vsh') {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      const cx = d3.scaleLinear().domain([track.xMin, track.xMax]).range([margin.left + 2, margin.left + plotWidth - 2])(CUTOFFS.vsh);
      ctx.beginPath();
      ctx.moveTo(cx, margin.top);
      ctx.lineTo(cx, margin.top + plotHeight);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#f59e0b';
      ctx.font = '8px monospace';
      ctx.fillText(`Vsh=${CUTOFFS.vsh}`, cx + 3, margin.top + 10);
    }
    if (track.id === 'computed') {
      const xScale = d3.scaleLinear().domain([track.xMin, track.xMax]).range([margin.left + 2, margin.left + plotWidth - 2]);
      // PHIe cutoff
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 5]);
      const px = xScale(CUTOFFS.phi);
      ctx.beginPath(); ctx.moveTo(px, margin.top); ctx.lineTo(px, margin.top + plotHeight); ctx.stroke();
      ctx.fillStyle = '#3b82f6'; ctx.fillText(`φ=${CUTOFFS.phi}`, px + 2, margin.top + 10);
      // Sw cutoff
      ctx.strokeStyle = '#06b6d4';
      const sx = xScale(CUTOFFS.sw);
      ctx.beginPath(); ctx.moveTo(sx, margin.top); ctx.lineTo(sx, margin.top + plotHeight); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#06b6d4'; ctx.fillText(`Sw=${CUTOFFS.sw}`, sx + 2, margin.top + 22);
    }

    // Title
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(track.title, margin.left + plotWidth / 2, 18);

    // Scale labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`${track.xMin}`, margin.left + 2, margin.top - 8);
    ctx.textAlign = 'right';
    ctx.fillText(`${track.xMax}`, margin.left + plotWidth - 2, margin.top - 8);

    // Cursor
    if (cursorDepth != null && cursorDepth >= depthRange[0] && cursorDepth <= depthRange[1]) {
      const y = yScale(cursorDepth);
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotWidth, y); ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [track, depth, curves, depthRange, cursorDepth]);

  useEffect(() => { draw(); }, [draw]);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yScale = d3.scaleLinear().domain([margin.top, margin.top + plotHeight]).range(depthRange);
    const d = yScale(y) as number;
    if (d >= depthRange[0] && d <= depthRange[1]) onCursorMove(d);
  };

  return (
    <canvas
      ref={canvasRef}
      className="flex-shrink-0 cursor-crosshair"
      style={{ width: `${width}px`, height: `${height}px` }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => onCursorMove(null)}
    />
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Depth Track
// ─────────────────────────────────────────────────────────────────────────────

const PetrophysicalDepthTrack: React.FC<{
  depthRange: [number, number];
  cursorDepth: number | null;
  onCursorMove: (depth: number | null) => void;
}> = ({ depthRange, cursorDepth, onCursorMove }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const width = 60;
  const height = 500;
  const margin = { top: 30, bottom: 20 };
  const plotHeight = height - margin.top - margin.bottom;

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
    ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = '#334155'; ctx.strokeRect(0, margin.top, width, plotHeight);

    const yScale = d3.scaleLinear().domain(depthRange).range([margin.top, margin.top + plotHeight]);
    for (let d = Math.ceil(depthRange[0] / 10) * 10; d <= depthRange[1]; d += 10) {
      const y = yScale(d);
      const isMajor = d % 50 === 0;
      ctx.strokeStyle = isMajor ? '#475569' : '#1e293b';
      ctx.lineWidth = isMajor ? 1 : 0.5;
      ctx.beginPath(); ctx.moveTo(isMajor ? 0 : 20, y); ctx.lineTo(width, y); ctx.stroke();
      if (isMajor) {
        ctx.fillStyle = '#94a3b8'; ctx.font = 'bold 10px monospace';
        ctx.fillText(d.toString(), 4, y + 3);
      }
    }
    ctx.fillStyle = '#e2e8f0'; ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('DEPTH (m)', width / 2, 18);

    if (cursorDepth != null) {
      const y = yScale(cursorDepth);
      ctx.strokeStyle = '#fbbf24'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
  }, [depthRange, cursorDepth]);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yScale = d3.scaleLinear().domain([margin.top, margin.top + plotHeight]).range(depthRange);
    const d = yScale(y) as number;
    if (d >= depthRange[0] && d <= depthRange[1]) onCursorMove(d);
  };

  return (
    <canvas
      ref={canvasRef}
      className="flex-shrink-0 cursor-crosshair"
      style={{ width: `${width}px`, height: `${height}px` }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => onCursorMove(null)}
    />
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Zone Classification Legend
// ─────────────────────────────────────────────────────────────────────────────

const ZoneLegend: React.FC<{
  cursorDepth: number | null;
  depth: number[];
  vsh: (number | null)[];
  phie: (number | null)[];
  sw: (number | null)[];
}> = ({ cursorDepth, depth, vsh, phie, sw }) => {
  const zoneInfo = useMemo(() => {
    if (cursorDepth == null) return null;
    const idx = depth.findIndex((d) => d >= cursorDepth);
    if (idx < 0) return null;
    const v = vsh[idx];
    const p = phie[idx];
    const s = sw[idx];

    let zone = 'Unknown';
    let color = '#94a3b8';
    if (v != null && p != null) {
      if (v < 0.3 && p > 0.1) {
        zone = s != null && s < 0.5 ? 'Pay Zone' : 'Water Zone';
        color = s != null && s < 0.5 ? '#22c55e' : '#3b82f6';
      } else if (v > 0.5) {
        zone = 'Shale'; color = '#f59e0b';
      } else {
        zone = 'Transition'; color = '#94a3b8';
      }
    }
    return { zone, color, v, p, s };
  }, [cursorDepth, depth, vsh, phie, sw]);

  return (
    <div className="p-3 space-y-2">
      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Zone @ Cursor</h4>
      {zoneInfo ? (
        <>
          <div className="text-sm font-bold" style={{ color: zoneInfo.color }}>
            {zoneInfo.zone}
          </div>
          <div className="space-y-1 text-xs">
            <MetricLine label="Vsh" value={zoneInfo.v} color="#f59e0b" cutoff={CUTOFFS.vsh} />
            <MetricLine label="PHIe" value={zoneInfo.p} color="#3b82f6" cutoff={CUTOFFS.phi} />
            <MetricLine label="Sw" value={zoneInfo.s} color="#06b6d4" cutoff={CUTOFFS.sw} />
          </div>
        </>
      ) : (
        <p className="text-xs text-slate-600 italic">Hover over tracks</p>
      )}
    </div>
  );
};

const MetricLine: React.FC<{ label: string; value: number | null | undefined; color: string; cutoff: number }> =
  ({ label, value, color, cutoff }) => (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-mono" style={{ color }}>
        {value != null ? value.toFixed(3) : '--'}
        <span className="text-slate-600 ml-1">
          {value != null && value > cutoff ? '↑' : value != null ? '↓' : ''}
        </span>
      </span>
    </div>
  );

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export const PetrophysicalTracks: React.FC = () => {
  const { selectedWell, updateFloorStatus } = useGEOXStore();
  const [depthRange, setDepthRange] = useState<[number, number]>([1500, 2200]);
  const [cursorDepth, setCursorDepth] = useState<number | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [lastReceiptHash, setLastReceiptHash] = useState<string | null>(null);

  const petroTool = useMcpTool<{
    mode: string;
    well_id: string;
    depth_top_m: number;
    depth_bot_m: number;
    vsh_cutoff?: number;
    phi_cutoff?: number;
    sw_cutoff?: number;
  }, PetrophysicalResult>('geox_petrophysics');

  // Derived data
  const depth = petroTool.data?.depth ?? [];
  const vshCurve = petroTool.data?.vsh ?? [];
  const phieCurve = petroTool.data?.phie ?? [];
  const swCurve = petroTool.data?.sw ?? [];
  const dtCurve = petroTool.data?.dt_synth ?? [];

  const curves: Record<string, (number | null)[]> = {
    VSH: vshCurve,
    PHIE: phieCurve,
    SW: swCurve,
    DT: dtCurve,
    NPHI: [],
    RHOB: [],
  };

  const hasData = depth.length > 0 && vshCurve.length > 0;

  const runPetrophysics = useCallback(async () => {
    try {
      updateFloorStatus('F9', 'amber', 'Computing petrophysics via MCP…');
      const result = await petroTool.call({
        mode: 'generate',
        well_id: selectedWell ?? 'W-101',
        depth_top_m: depthRange[0],
        depth_bot_m: depthRange[1],
        vsh_cutoff: CUTOFFS.vsh,
        phi_cutoff: CUTOFFS.phi,
        sw_cutoff: CUTOFFS.sw,
      });
      updateFloorStatus('F9', 'green', 'Petrophysics computed');
      if (result.receipt_hash) setLastReceiptHash(result.receipt_hash);
    } catch (err) {
      updateFloorStatus('F9', 'red', `Petrophysics failed: ${String(err)}`);
    }
  }, [selectedWell, depthRange, petroTool, updateFloorStatus]);

  // Auto-run on mount
  useEffect(() => {
    runPetrophysics();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const zoomIn = () => {
    const mid = (depthRange[0] + depthRange[1]) / 2;
    const half = (depthRange[1] - depthRange[0]) / 2;
    setDepthRange([mid - half * 0.7, mid + half * 0.7]);
  };
  const zoomOut = () => {
    const mid = (depthRange[0] + depthRange[1]) / 2;
    const half = (depthRange[1] - depthRange[0]) / 2;
    setDepthRange([Math.max(0, mid - half * 1.4), mid + half * 1.4]);
  };

  return (
    <div className="h-full flex flex-col bg-slate-950 rounded-lg border border-slate-800 overflow-hidden">
      {/* Toolbar */}
      <div className="h-10 bg-slate-900 border-b border-slate-800 flex items-center px-3 gap-2 flex-shrink-0">
        <FlaskConical className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-bold text-slate-200">Petrophysical Tracks</span>
        <span className="text-xs text-slate-600 font-mono ml-1">
          {selectedWell ?? 'W-101'} · MCP
        </span>

        <div className="w-px h-5 bg-slate-700 mx-2" />

        <button onClick={runPetrophysics} disabled={petroTool.status === 'loading'}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-50"
          title="Recompute petrophysics">
          <RefreshCw className={`w-4 h-4 ${petroTool.status === 'loading' ? 'animate-spin' : ''}`} />
        </button>

        <div className="flex-1" />

        {petroTool.status === 'loading' && (
          <span className="text-xs text-amber-400 flex items-center gap-1">
            <Loader2 className="w-3 h-3 animate-spin" /> Computing…
          </span>
        )}
        {petroTool.status === 'success' && (
          <span className="text-xs text-green-400 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" /> {lastReceiptHash ? `Receipt: ${lastReceiptHash.slice(0, 10)}…` : 'Done'}
          </span>
        )}
        {petroTool.status === 'error' && (
          <span className="text-xs text-red-400 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> {petroTool.error}
          </span>
        )}

        <div className="w-px h-5 bg-slate-700 mx-2" />

        <button onClick={zoomIn} className="text-xs px-2 py-1 rounded hover:bg-slate-800 text-slate-400">+</button>
        <button onClick={zoomOut} className="text-xs px-2 py-1 rounded hover:bg-slate-800 text-slate-400">−</button>
        <span className="text-xs text-slate-500 font-mono">{depthRange[0].toFixed(0)}–{depthRange[1].toFixed(0)}m</span>

        <button onClick={() => setShowSidebar(!showSidebar)}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400">
          {showSidebar ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Main tracks area */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-x-auto">
          {hasData ? (
            <div className="flex">
              <PetrophysicalDepthTrack depthRange={depthRange} cursorDepth={cursorDepth} onCursorMove={setCursorDepth} />
              {TRACKS.map((track) => (
                <PetrophysicalTrackRenderer
                  key={track.id}
                  track={track}
                  depth={depth}
                  curves={curves}
                  depthRange={depthRange}
                  cursorDepth={cursorDepth}
                  onCursorMove={setCursorDepth}
                />
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-3">
                <Activity className="w-10 h-10 text-slate-600 mx-auto animate-pulse" />
                <p className="text-slate-500 text-sm">
                  {petroTool.status === 'loading'
                    ? 'Computing petrophysics via MCP…'
                    : petroTool.status === 'error'
                      ? `MCP error: ${petroTool.error}`
                      : 'Click Refresh to compute petrophysics'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <div className="w-52 bg-slate-900 border-l border-slate-800 overflow-y-auto flex-shrink-0">
            <ZoneLegend cursorDepth={cursorDepth} depth={depth} vsh={vshCurve} phie={phieCurve} sw={swCurve} />
            <div className="border-t border-slate-800" />
            <div className="p-3">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Cutoffs</h4>
              <div className="space-y-1 text-xs text-slate-400">
                <div className="flex justify-between"><span>Vsh</span><span className="text-amber-400 font-mono">{CUTOFFS.vsh}</span></div>
                <div className="flex justify-between"><span>PHIe</span><span className="text-blue-400 font-mono">{CUTOFFS.phi}</span></div>
                <div className="flex justify-between"><span>Sw</span><span className="text-cyan-400 font-mono">{CUTOFFS.sw}</span></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="h-7 bg-slate-950 border-t border-slate-800 flex items-center px-3 text-[10px] text-slate-500 font-mono flex-shrink-0 gap-4">
        <span>MCP: geox_petrophysics</span>
        <span>|</span>
        <span>Cutoffs: Vsh={CUTOFFS.vsh} φ={CUTOFFS.phi} Sw={CUTOFFS.sw}</span>
        <div className="flex-1" />
        <span className="text-amber-500/70">DITEMPA BUKAN DIBERI</span>
      </div>
    </div>
  );
};

export default PetrophysicalTracks;
