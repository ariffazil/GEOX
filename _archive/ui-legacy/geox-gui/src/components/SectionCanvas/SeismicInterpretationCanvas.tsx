/**
 * SeismicInterpretationCanvas — Interactive Seismic Horizon/Fault Picker
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Wires useMcpTool to geox_seismic_interpret:
 *  - mode=horizon_contrast  → picks stratigraphic horizons
 *  - mode=fault_sticks       → picks fault planes
 *
 * Renders:
 *  - Canvas-based seismic section display (grayscale variable-area)
 *  - Interactive pick mode for horizons (click to add points)
 *  - Fault stick mode (click-drag to draw fault planes)
 *  - Hypothesis panel showing candidates
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import {
  Layout, MousePointer2, PenTool, Trash2, Layers,
  RefreshCw, CheckCircle, AlertTriangle, Target, Eye, EyeOff,
  ShieldCheck,
} from 'lucide-react';
import { useMcpTool } from '../../hooks/useMcpTool';
import { useGEOXStore } from '../../store/geoxStore';
import { useGeologicalClaim } from '../../hooks/useGeologicalClaim';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface SeismicInterpretResult {
  horizons?: Array<{
    id: string;
    name: string;
    points: Array<[number, number]>; // [trace, time]
    confidence?: number;
    geological_query?: string;
  }>;
  faults?: Array<{
    id: string;
    name: string;
    points: Array<[number, number]>;
    throw_m?: number;
    confidence?: number;
  }>;
  receipt_hash?: string;
  evidence_tag?: string;
  candidates?: Array<{
    id: string;
    name: string;
    type: string;
    confidence: number;
    physical_basis?: string;
  }>;
}

type PickMode = 'horizon' | 'fault' | 'none';

/** V11: Audit trail entry for every state mutation */
interface AuditEntry {
  timestamp: string;
  action: 'add_pick' | 'add_point' | 'clear' | 'undo' | 'mcp_horizon' | 'mcp_fault';
  pickType: 'horizon' | 'fault' | 'both';
  claimState: string;
  detail: string;
}

interface LocalPick {
  id: string;
  name: string;
  type: 'horizon' | 'fault';
  points: Array<{ trace: number; time: number }>;
  color: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Seismic Section Canvas
// ─────────────────────────────────────────────────────────────────────────────

const seismicColors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#06b6d4'];
const faultColors = ['#ef4444', '#f97316', '#dc2626'];

const SeismicSectionRenderer: React.FC<{
  picks: LocalPick[];
  pickMode: PickMode;
  onCanvasClick: (trace: number, time: number) => void;
  showHorizons: boolean;
  showFaults: boolean;
  readOnly: boolean;
}> = ({ picks, pickMode, onCanvasClick, showHorizons, showFaults, readOnly }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const width = 700;
  const height = 450;
  const margin = { top: 10, right: 10, bottom: 40, left: 50 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  // Generate synthetic seismic section background
  const synthData = useRef<number[][]>([]);

  useEffect(() => {
    // Generate synthetic wiggle trace data
    if (synthData.current.length > 0) return;
    const traces = 80;
    const samples = 400;
    const data: number[][] = [];
    for (let t = 0; t < traces; t++) {
      const trace: number[] = [];
      for (let s = 0; s < samples; s++) {
        // Realistic seismic wavelet model: Ricker + noise + structure
        const freq = 0.06;
        const amp = Math.sin(s * freq + t * 0.15) * 0.5
          + Math.sin(s * freq * 2.5 + t * 0.08) * 0.3
          + Math.sin(s * freq * 0.4 + t * 0.3) * 0.2;
        trace.push(amp + (Math.random() - 0.5) * 0.08);
      }
      data.push(trace);
    }
    synthData.current = data;
  }, []);

  const draw = useCallback(() => {
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
    ctx.strokeStyle = '#334155'; ctx.lineWidth = 1;
    ctx.strokeRect(margin.left, margin.top, plotW, plotH);

    const timeRange: [number, number] = [0, 4000];
    const yScale = d3.scaleLinear().domain(timeRange).range([margin.top, margin.top + plotH]);

    // Grid
    ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 0.5;
    for (let t = 0; t <= 4000; t += 500) {
      const y = yScale(t);
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotW, y); ctx.stroke();
      ctx.fillStyle = '#475569'; ctx.font = '9px monospace'; ctx.textAlign = 'right';
      ctx.fillText(`${t}ms`, margin.left - 4, y + 3);
    }

    // Trace labels
    ctx.fillStyle = '#475569'; ctx.font = '9px monospace'; ctx.textAlign = 'center';
    for (let i = 0; i <= 80; i += 10) {
      const x = margin.left + (plotW * i) / 80;
      ctx.fillText(`${i}`, x, margin.top + plotH + 15);
    }

    // Draw wiggles (variable area fill)
    if (synthData.current.length > 0) {
      const traceW = plotW / synthData.current.length;
      synthData.current.forEach((trace, ti) => {
        const cx = margin.left + ti * traceW + traceW / 2;
        const maxW = traceW * 0.45;

        // Variable area fill (positive amplitudes)
        ctx.beginPath();
        ctx.fillStyle = '#1e3a5f';
        let first = true;
        trace.forEach((sample, si) => {
          const y = yScale((si / trace.length) * timeRange[1]);
          const xOff = sample > 0 ? sample * maxW * 2 : 0;
          if (first) { ctx.moveTo(cx, y); first = false; }
          else ctx.lineTo(cx + xOff, y);
        });
        ctx.lineTo(cx, yScale(timeRange[1]));
        ctx.closePath();
        ctx.fill();

        // Wiggle trace
        ctx.beginPath();
        ctx.strokeStyle = '#64748b'; ctx.lineWidth = 0.8;
        first = true;
        trace.forEach((sample, si) => {
          const y = yScale((si / trace.length) * timeRange[1]);
          const x = cx + sample * maxW * 2;
          if (first) { ctx.moveTo(x, y); first = false; }
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      });
    }

    // Draw picks
    picks.forEach((pick, _pi) => {
      if ((pick.type === 'horizon' && !showHorizons) || (pick.type === 'fault' && !showFaults)) return;

      ctx.strokeStyle = pick.color;
      ctx.lineWidth = pick.type === 'fault' ? 2.5 : 2;
      if (pick.type === 'fault') ctx.setLineDash([6, 3]);

      ctx.beginPath();
      let started = false;
      pick.points.forEach((pt) => {
        const x = margin.left + (pt.trace / 80) * plotW;
        const y = yScale(pt.time);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw point markers
      pick.points.forEach((pt) => {
        const x = margin.left + (pt.trace / 80) * plotW;
        const y = yScale(pt.time);
        ctx.fillStyle = pick.color;
        ctx.beginPath();
        ctx.arc(x, y, pick.type === 'fault' ? 3 : 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1;
        ctx.stroke();
      });
    });

    // Pick mode indicator
    if (readOnly) {
      ctx.fillStyle = '#d4af37';
      ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'left';
      ctx.fillText('🔒 LOCKED — PENDING REVIEW / SEALED', margin.left + 4, margin.top + 14);
    } else if (pickMode !== 'none') {
      ctx.fillStyle = pickMode === 'horizon' ? '#22c55e' : '#ef4444';
      ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'left';
      ctx.fillText(`MODE: ${pickMode.toUpperCase()} — Click to pick`, margin.left + 4, margin.top + 14);
    }
  }, [picks, pickMode, showHorizons, showFaults, readOnly, margin.left, margin.top, plotW, plotH]);

  useEffect(() => { draw(); }, [draw]);

  const handleClick = (e: React.MouseEvent) => {
    if (readOnly || pickMode === 'none') return;
    const rect = e.currentTarget.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (mx < margin.left || mx > margin.left + plotW || my < margin.top || my > margin.top + plotH) return;

    const trace = Math.round(((mx - margin.left) / plotW) * 80);
    const yScale = d3.scaleLinear().domain([margin.top, margin.top + plotH]).range([0, 4000]);
    const time = yScale(my);
    onCanvasClick(trace, time);
  };

  return (
    <canvas
      ref={canvasRef}
      className={`border border-slate-800 rounded ${readOnly ? 'cursor-not-allowed opacity-90' : 'cursor-crosshair'}`}
      style={{ width: `${width}px`, height: `${height}px` }}
      onClick={handleClick}
      title={readOnly ? '[PENDING REVIEW / SEALED] canvas read-only' : 'click to pick'}
    />
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export const SeismicInterpretationCanvas: React.FC = () => {
  const { updateFloorStatus } = useGEOXStore();
  const [pickMode, setPickMode] = useState<PickMode>('none');
  const [picks, setPicks] = useState<LocalPick[]>([]);
  const [showHorizons, setShowHorizons] = useState(true);
  const [showFaults, setShowFaults] = useState(true);
  const [activeHorizonIdx, setActiveHorizonIdx] = useState(0);
  // V10/V11 Tri-State Authority Machine (F13 SOVEREIGN).
  // Two claim instances — one per pick family — replace the single
  // "REQUEST JUDGE SEAL" mock gate that called geox_judge_verdict and
  // treated the verdict as authority. A compute receipt is NOT a sovereign
  // signature. The real path is DRAFT → PENDING REVIEW → ATTESTED, with
  // attest() being a separate explicit gate requiring a VAULT999 ref.
  const horizon = useGeologicalClaim('horizon');
  const fault = useGeologicalClaim('fault');
  // Canvas is locked if EITHER claim is non-DRAFT — interpretive commits
  // are not the only concern; the operator must be able to attest cleanly.
  const horizonReadOnly = horizon.claim.state !== 'draft';
  const faultReadOnly = fault.claim.state !== 'draft';
  const anyReadOnly = horizonReadOnly || faultReadOnly;
  const nextPickId = useRef(1);

  // ─── V11: Audit trail — every mutation is logged with timestamp ────────
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const logMutation = useCallback((
    action: AuditEntry['action'],
    pickType: AuditEntry['pickType'],
    claimState: string,
    detail: string,
  ) => {
    setAuditLog((prev) => [...prev.slice(-49), { // keep last 50 entries
      timestamp: new Date().toISOString(),
      action, pickType, claimState, detail,
    }]);
  }, []);

  // ─── V11: commitPick — the ONLY way to mutate picks state ──────────────
  // Every setPicks call MUST go through this function to ensure:
  // 1. The mutation is logged in the audit trail
  // 2. The geological claim state machine is synced via toDraft()
  const commitPick = useCallback((
    updater: (prev: LocalPick[]) => LocalPick[],
    action: AuditEntry['action'],
    pickType: AuditEntry['pickType'],
    detail: string,
  ) => {
    setPicks((prev) => {
      const next = updater(prev);
      // Sync claim state machine — picks are ALWAYS in DRAFT after mutation
      if (pickType === 'horizon' || pickType === 'both') {
        horizon.toDraft({ picks: next.filter((p) => p.type === 'horizon') });
      }
      if (pickType === 'fault' || pickType === 'both') {
        fault.toDraft({ picks: next.filter((p) => p.type === 'fault') });
      }
      return next;
    });
    logMutation(action, pickType, horizon.claim.state, detail);
  }, [horizon, fault, logMutation]);

  const interpretTool = useMcpTool<{
    mode: string;
    geological_query?: string;
    peak_threshold?: number;
    volume_ref?: string;
  }, SeismicInterpretResult>('geox_seismic_interpret');

  const runHorizonContrast = useCallback(async () => {
    try {
      updateFloorStatus('F2', 'amber', 'Running horizon contrast via MCP…');
      const result = await interpretTool.call({
        mode: 'horizon_contrast',
        geological_query: 'sequence_boundary',
        peak_threshold: 1.5,
      });
      updateFloorStatus('F2', 'green', 'Horizon candidates returned');

      // Convert server horizons to local picks — V11: ALL mutations via commitPick
      if (result.horizons) {
        const newPicks: LocalPick[] = result.horizons.map((h, i) => ({
          id: `h-${nextPickId.current++}`,
          name: h.name || `Horizon-${i + 1}`,
          type: 'horizon' as const,
          points: h.points?.map(([t, time]) => ({ trace: t, time })) ?? [],
          color: seismicColors[i % seismicColors.length],
        }));
        commitPick(
          (prev) => [...prev, ...newPicks],
          'mcp_horizon',
          'horizon',
          `MCP horizon_contrast: ${newPicks.length} horizons added`,
        );
      }
    } catch (err) {
      updateFloorStatus('F2', 'red', `Horizon pick failed: ${String(err)}`);
    }
  }, [interpretTool, updateFloorStatus, commitPick]);

  const runFaultDetection = useCallback(async () => {
    try {
      updateFloorStatus('F2', 'amber', 'Detecting fault sticks via MCP…');
      const result = await interpretTool.call({
        mode: 'fault_sticks',
        volume_ref: 'MY-2026-SEISMIC-01',
      });
      updateFloorStatus('F2', 'green', 'Fault sticks returned');

      if (result.faults) {
        const newPicks: LocalPick[] = result.faults.map((f, i) => ({
          id: `f-${nextPickId.current++}`,
          name: f.name || `Fault-${i + 1}`,
          type: 'fault' as const,
          points: f.points?.map(([t, time]) => ({ trace: t, time })) ?? [],
          color: faultColors[i % faultColors.length],
        }));
        // V11: ALL mutations via commitPick
        commitPick(
          (prev) => [...prev, ...newPicks],
          'mcp_fault',
          'fault',
          `MCP fault_sticks: ${newPicks.length} faults added`,
        );
      }
    } catch (err) {
      updateFloorStatus('F2', 'red', `Fault detection failed: ${String(err)}`);
    }
  }, [interpretTool, updateFloorStatus, commitPick]);

  const handleCanvasClick = useCallback((trace: number, time: number) => {
    // V10/V11 Tri-State: while the relevant claim is PENDING REVIEW or
    // ATTESTED, the canvas is read-only. No picks are accepted.
    if (pickMode === 'horizon' && horizonReadOnly) return;
    if (pickMode === 'fault' && faultReadOnly) return;
    if (pickMode === 'none') return;

    if (pickMode === 'horizon') {
      const existing = picks.filter((p) => p.type === 'horizon');
      if (existing.length === 0) {
        // V11: first horizon creation — commitPick routes through audit trail + state machine
        const newPick: LocalPick = {
          id: `h-${nextPickId.current++}`,
          name: `Horizon-${nextPickId.current}`,
          type: 'horizon',
          points: [{ trace, time }],
          color: seismicColors[0],
        };
        commitPick(
          (prev) => [...prev, newPick],
          'add_pick', 'horizon',
          `New horizon created at trace=${trace} time=${time}`,
        );
        return;
      }
      // Continuation of an already-existing horizon — V11: commitPick for audit
      const target = existing[activeHorizonIdx % existing.length];
      commitPick(
        (prev) => prev.map((p) =>
          p.id === target.id ? { ...p, points: [...p.points, { trace, time }].sort((a, b) => a.trace - b.trace) } : p
        ),
        'add_point', 'horizon',
        `Point added to ${target.name} at trace=${trace} time=${time}`,
      );
    } else if (pickMode === 'fault') {
      const existing = picks.filter((p) => p.type === 'fault');
      if (existing.length === 0) {
        const newPick: LocalPick = {
          id: `f-${nextPickId.current++}`,
          name: `Fault-${nextPickId.current}`,
          type: 'fault',
          points: [{ trace, time }],
          color: faultColors[0],
        };
        commitPick(
          (prev) => [...prev, newPick],
          'add_pick', 'fault',
          `New fault created at trace=${trace} time=${time}`,
        );
        return;
      }
      const lastFault = existing[existing.length - 1];
      commitPick(
        (prev) => prev.map((p) =>
          p.id === lastFault.id ? { ...p, points: [...p.points, { trace, time }] } : p
        ),
        'add_point', 'fault',
        `Point added to ${lastFault.name} at trace=${trace} time=${time}`,
      );
    }
  }, [pickMode, activeHorizonIdx, picks, horizonReadOnly, faultReadOnly, commitPick]);

  // ── V10/V11: Tri-State transitions for horizon and fault claims ──────────────
  const requestHorizonReview = useCallback(() => horizon.requestReview(), [horizon]);
  const requestFaultReview = useCallback(() => fault.requestReview(), [fault]);
  const attestHorizon = useCallback(() => {
    horizon.attest({ claimId: horizon.claim.id, picks: picks.filter(p => p.type === 'horizon') });
  }, [horizon, picks]);
  const attestFault = useCallback(() => {
    fault.attest({ claimId: fault.claim.id, picks: picks.filter(p => p.type === 'fault') });
  }, [fault, picks]);

  // V11: clearPicks and undoLast also go through commitPick for audit trail
  const clearPicks = () => {
    commitPick(
      () => [],
      'clear', 'both',
      `All picks cleared`,
    );
  };

  const undoLast = () => {
    commitPick(
      (prev) => {
        if (prev.length === 0) return prev;
        const last = prev[prev.length - 1];
        return last.points.length <= 1
          ? prev.slice(0, -1)
          : prev.map((p) => (p.id === last.id ? { ...p, points: p.points.slice(0, -1) } : p));
      },
      'undo', 'both',
      `Undo last action`,
    );
  };

  const horizonPicks = picks.filter((p) => p.type === 'horizon');
  const faultPicks = picks.filter((p) => p.type === 'fault');

  return (
    <div className="h-full flex flex-col bg-[#0f172a] text-slate-300 overflow-hidden">
      {/* Toolbar */}
      <div className="h-10 border-b border-slate-800 bg-slate-900/50 flex items-center px-4 justify-between flex-shrink-0">
        <div className="flex items-center gap-4 text-xs font-bold uppercase tracking-widest text-slate-500">
          <div className="flex items-center gap-2">
            <Layout className="w-3 h-3 text-blue-400" />
            <span>Seismic Interpretation Canvas</span>
          </div>
          <span className="text-blue-400/50">|</span>
          <span>Line: MY-2026-SEISMIC-01</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPickMode('horizon')}
            disabled={horizonReadOnly}
            className={`px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1.5 transition-all
              ${pickMode === 'horizon' && !horizonReadOnly ? 'bg-green-600 text-white' : horizonReadOnly ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
          >
            <MousePointer2 className="w-3 h-3" /> Horizon{horizonReadOnly ? ' 🔒' : ''}
          </button>
          <button
            onClick={() => setPickMode('fault')}
            disabled={faultReadOnly}
            className={`px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1.5 transition-all
              ${pickMode === 'fault' && !faultReadOnly ? 'bg-red-600 text-white' : faultReadOnly ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-slate-800 text-slate-400 hover:text-white'}`}
          >
            <PenTool className="w-3 h-3" /> Fault{faultReadOnly ? ' 🔒' : ''}
          </button>
          <button onClick={() => setPickMode('none')}
            className="px-3 py-1.5 rounded text-xs font-bold bg-slate-800 text-slate-400 hover:text-white">
            None
          </button>

          <div className="w-px h-5 bg-slate-700 mx-1" />

          <button onClick={runHorizonContrast}
            disabled={interpretTool.status === 'loading'}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-50"
            title="Run horizon contrast via MCP">
            <RefreshCw className={`w-4 h-4 ${interpretTool.status === 'loading' ? 'animate-spin' : ''}`} />
            <span className="text-[9px] ml-1">Auto-H</span>
          </button>
          <button onClick={runFaultDetection}
            disabled={interpretTool.status === 'loading'}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-50"
            title="Run fault sticks via MCP">
            <Target className="w-4 h-4" />
            <span className="text-[9px] ml-1">Auto-F</span>
          </button>

          <div className="w-px h-5 bg-slate-700 mx-1" />

          <button onClick={() => setShowHorizons(!showHorizons)}
            className={`p-1.5 rounded ${showHorizons ? 'text-green-400' : 'text-slate-600'} hover:bg-slate-800`}>
            {showHorizons ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button onClick={() => setShowFaults(!showFaults)}
            className={`p-1.5 rounded ${showFaults ? 'text-red-400' : 'text-slate-600'} hover:bg-slate-800`}>
            {showFaults ? <Layers className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>

          <button onClick={undoLast} className="p-1.5 rounded hover:bg-slate-800 text-slate-400" title="Undo last point">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="space-y-4 text-center">
            <SeismicSectionRenderer
              picks={picks}
              pickMode={pickMode}
              onCanvasClick={handleCanvasClick}
              showHorizons={showHorizons}
              showFaults={showFaults}
              readOnly={anyReadOnly}
            />
          </div>
        </div>

        {/* Right sidebar — Pick legend */}
        <div className="w-52 bg-slate-900 border-l border-slate-800 overflow-y-auto flex-shrink-0 p-3">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Interpretation Picks</h4>

          {horizonPicks.map((p, i) => (
            <div key={p.id}
              onClick={() => setActiveHorizonIdx(i)}
              className={`mb-2 p-2 rounded cursor-pointer border transition-all
                ${activeHorizonIdx === i && pickMode === 'horizon' ? 'border-green-500 bg-green-500/10' : 'border-slate-800 bg-slate-900'}`}>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 rounded" style={{ backgroundColor: p.color }} />
                <span className="text-xs font-bold text-slate-300">{p.name}</span>
              </div>
              <span className="text-[10px] text-slate-500">{p.points.length} points</span>
            </div>
          ))}

          {faultPicks.map((p) => (
            <div key={p.id} className="mb-2 p-2 rounded border border-slate-800 bg-slate-900">
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 rounded" style={{ backgroundColor: p.color }} />
                <span className="text-xs font-bold text-red-400">{p.name}</span>
              </div>
              <span className="text-[10px] text-slate-500">{p.points.length} picks</span>
            </div>
          ))}

          {picks.length === 0 && (
            <p className="text-xs text-slate-600 italic">
              Click "Horizon" or "Fault" mode, then click on the seismic section to pick. Or use "Auto-H" / "Auto-F" for MCP picks.
            </p>
          )}

          {picks.length > 0 && (
            <button onClick={clearPicks} className="mt-3 w-full text-xs bg-red-900/30 text-red-400 py-1.5 rounded hover:bg-red-900/50 border border-red-900/50">
              Clear All Picks
            </button>
          )}

          {/* V10/V11 Tri-State Authority Machine — Horizon */}
          <div className="mt-3 pt-3 border-t border-slate-800">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-green-400" /> Horizon Claim (V10/V11)
            </h4>
            {horizon.claim.state === 'draft' && (
              <div className="mb-2 p-2 rounded border border-yellow-600/40 bg-yellow-600/10">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-yellow-400 bg-yellow-600/20 border border-yellow-600/40 px-1.5 py-0.5 rounded">
                    [UNVERIFIED]
                  </span>
                  <span className="text-[10px] text-slate-400">DRAFT</span>
                  <span className="ml-auto text-[9px] font-bold text-gray-400 bg-gray-800/60 px-1.5 py-0.5 rounded border border-gray-700/60">DRAFT</span>
                </div>
                <p className="text-[9px] text-slate-500 mt-1 leading-tight">
                  {horizonPicks.length} horizon(s) · {horizonPicks.reduce((s, p) => s + p.points.length, 0)} pts · volatile
                </p>
              </div>
            )}
            {horizon.claim.state === 'pending_review' && (
              <div className="mb-2 p-2 rounded border border-amber-500/40 bg-amber-500/10">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-amber-400 bg-amber-500/20 border border-amber-500/40 px-1.5 py-0.5 rounded">
                    [PENDING REVIEW]
                  </span>
                  <span className="text-[10px] text-amber-500/70">F11 halt</span>
                  <span className="ml-auto text-[9px] font-bold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">APPROVED</span>
                </div>
                <p className="text-[9px] text-amber-500/70 mt-1 leading-tight">
                  Canvas LOCKED. Uncertainty acknowledged — horizon picks are
                  interpretive and carry risk until independently attested.
                </p>
              </div>
            )}
            {horizon.claim.state === 'attested' && (
              <div className="attestation-confirmation mb-2">
                <h4>🔒 Attestation Confirmed — Horizon</h4>
                <p>Receipt: <code>{horizon.claim.attestationRef}</code></p>
                <p>Timestamp: {horizon.claim.attestedAt}</p>
                <p>Type: {horizon.claim.type}</p>
                <button onClick={() => horizon.resetToReality()}>
                  Return to Reality
                </button>
              </div>
            )}
            {horizon.claim.state === 'draft' && (
              <button
                onClick={requestHorizonReview}
                className="w-full py-2 rounded bg-[#3b82f6]/20 border border-[#3b82f6]/40 text-[#3b82f6] text-xs font-bold hover:bg-[#3b82f6]/30"
              >
                ▶ Review Delta
              </button>
            )}
            {horizon.claim.state === 'pending_review' && (
              <>
                <button
                  onClick={attestHorizon}
                  className="w-full py-2 rounded bg-[#f59e0b]/20 border border-[#f59e0b]/40 text-[#f59e0b] text-xs font-bold hover:bg-[#f59e0b]/30"
                >
                  ✓ Approve & Request Judge
                </button>
                <button
                  onClick={() => horizon.toDraft({ picks: horizonPicks })}
                  className="mt-1 w-full py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-400 text-[10px] font-bold hover:bg-slate-700"
                >
                  DISCARD → DRAFT
                </button>
              </>
            )}
          </div>

          {/* V10/V11 Tri-State Authority Machine — Fault */}
          <div className="mt-3 pt-3 border-t border-slate-800">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-red-400" /> Fault Claim (V10/V11)
            </h4>
            {fault.claim.state === 'draft' && (
                <div className="mb-2 p-2 rounded border border-yellow-600/40 bg-yellow-600/10">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-yellow-400 bg-yellow-600/20 border border-yellow-600/40 px-1.5 py-0.5 rounded">
                      [UNVERIFIED]
                    </span>
                    <span className="text-[10px] text-slate-400">DRAFT</span>
                    <span className="ml-auto text-[9px] font-bold text-gray-400 bg-gray-800/60 px-1.5 py-0.5 rounded border border-gray-700/60">DRAFT</span>
                  </div>
                  <p className="text-[9px] text-slate-500 mt-1 leading-tight">
                    {faultPicks.length} fault(s) · {faultPicks.reduce((s, p) => s + p.points.length, 0)} pts · volatile
                  </p>
                </div>
              )}
              {fault.claim.state === 'pending_review' && (
                <div className="mb-2 p-2 rounded border border-amber-500/40 bg-amber-500/10">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-amber-400 bg-amber-500/20 border border-amber-500/40 px-1.5 py-0.5 rounded">
                      [PENDING REVIEW]
                    </span>
                    <span className="text-[10px] text-amber-500/70">F11 halt</span>
                    <span className="ml-auto text-[9px] font-bold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">APPROVED</span>
                  </div>
                  <p className="text-[9px] text-amber-500/70 mt-1 leading-tight">
                    Canvas LOCKED. Uncertainty acknowledged — fault picks are
                    interpretive and carry risk until independently attested.
                  </p>
                </div>
              )}
              {fault.claim.state === 'attested' && (
                 <div className="attestation-confirmation mb-2">
                   <h4>🔒 Attestation Confirmed — Fault</h4>
                   <p>Receipt: <code>{fault.claim.attestationRef}</code></p>
                   <p>Timestamp: {fault.claim.attestedAt}</p>
                   <p>Type: {fault.claim.type}</p>
                   <button onClick={() => fault.resetToReality()}>
                     Return to Reality
                   </button>
                 </div>
              )}
            {fault.claim.state === 'draft' && (
              <button
                onClick={requestFaultReview}
                className="w-full py-2 rounded bg-[#3b82f6]/20 border border-[#3b82f6]/40 text-[#3b82f6] text-xs font-bold hover:bg-[#3b82f6]/30"
              >
                ▶ Review Delta
              </button>
            )}
            {fault.claim.state === 'pending_review' && (
              <>
                <button
                  onClick={attestFault}
                  className="w-full py-2 rounded bg-[#f59e0b]/20 border border-[#f59e0b]/40 text-[#f59e0b] text-xs font-bold hover:bg-[#f59e0b]/30"
                >
                  ✓ Approve & Request Judge
                </button>
                <button
                  onClick={() => fault.toDraft({ picks: faultPicks })}
                  className="mt-1 w-full py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-400 text-[10px] font-bold hover:bg-slate-700"
                >
                  DISCARD → DRAFT
                </button>
              </>
            )}
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800">
            <p className="text-[9px] text-slate-600 leading-tight">
              V10/V11 Tri-State: DRAFT → PENDING REVIEW (locked) → ATTESTED (VAULT999).
              Compute receipts are evidence only — never authority (F13 SOVEREIGN).
            </p>
          </div>

          {/* V11: Audit Trail — every mutation logged */}
          {auditLog.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-800">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Audit Trail ({auditLog.length})
              </h4>
              <div className="max-h-32 overflow-y-auto space-y-1">
                {auditLog.slice().reverse().map((entry, i) => (
                  <div key={i} className="text-[8px] text-slate-600 font-mono leading-tight">
                    <span className="text-slate-500">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                    {' '}
                    <span className={
                      entry.action.includes('add') ? 'text-green-500/70' :
                      entry.action === 'clear' ? 'text-red-500/70' :
                      entry.action === 'undo' ? 'text-amber-500/70' :
                      'text-blue-500/70'
                    }>
                      {entry.action}
                    </span>
                    {' '}<span className="text-slate-500">{entry.detail}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Status */}
          <div className="mt-4 pt-3 border-t border-slate-800">
            {interpretTool.status === 'loading' && (
              <span className="text-xs text-amber-400 flex items-center gap-1">
                <RefreshCw className="w-3 h-3 animate-spin" /> Running MCP…
              </span>
            )}
            {interpretTool.status === 'success' && (
              <span className="text-xs text-green-400 flex items-center gap-1">
                <CheckCircle className="w-3 h-3" /> MCP complete
              </span>
            )}
            {interpretTool.status === 'error' && (
              <span className="text-xs text-red-400 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> {interpretTool.error}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="h-8 bg-black/40 border-t border-slate-800 flex items-center px-4 gap-6 text-[10px] uppercase font-black text-slate-600 flex-shrink-0">
        <span>MCP: geox_seismic_interpret</span>
        <span>|</span>
        <span>Picks: {picks.length} ({horizonPicks.length}H, {faultPicks.length}F)</span>
        <span>|</span>
        <span>Mode: {pickMode}</span>
        <span>|</span>
        <span className={
          horizon.claim.state === 'attested' ? 'text-green-400' :
          horizon.claim.state === 'pending_review' ? 'text-amber-400' :
          'text-yellow-500/70'
        }>
          H:{horizon.claim.state.toUpperCase()}
        </span>
        <span className={
          fault.claim.state === 'attested' ? 'text-green-400' :
          fault.claim.state === 'pending_review' ? 'text-amber-400' :
          'text-yellow-500/70'
        }>
          F:{fault.claim.state.toUpperCase()}
        </span>
        <div className="flex-1" />
        <span className="text-amber-500/70">DITEMPA BUKAN DIBERI</span>
      </div>
    </div>
  );
};

export default SeismicInterpretationCanvas;
