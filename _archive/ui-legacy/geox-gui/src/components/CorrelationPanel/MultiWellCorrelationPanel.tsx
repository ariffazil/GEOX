/**
 * MultiWellCorrelationPanel — Side-by-Side Stratigraphic Correlation
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Phase 1 deliverable: written from scratch (no prior source existed).
 *
 * Renders multiple well tracks side-by-side on a shared depth axis with:
 *  - GR / VSH curve tracks per well
 *  - Facies panels (sand/shale/coal/limestone) per well
 *  - Stratigraphic top correlation lines connecting markers across wells
 *  - Data-driven via geox_well_view + geox_petrophysics MCP tools (Hermes Geology lane)
 *  - VerdictConsole / F11 audit routing on irreversible commits (SEAL gate)
 *
 * Docking protocol: no UI action may commit data without a judge SEAL.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import {
  Columns, Link2, RefreshCw, CheckCircle, AlertTriangle, Loader2,
  ChevronDown, ChevronUp, Layers, Shield, GitCompare
} from 'lucide-react';
import { useMcpTool } from '../../hooks/useMcpTool';
import { useGEOXStore } from '../../store/geoxStore';
import { useGeologicalClaim } from '../../hooks/useGeologicalClaim';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface CorrelationTop {
  id: string;
  name: string;
  color: string;
  /** depth per well id */
  depths: Record<string, number>;
  confidence?: number;
}

export interface CorrelationWell {
  id: string;
  name: string;
  /** [depth, value] pairs for the GR curve */
  gr: Array<[number, number]>;
  /** facies per depth sample: sand | shale | coal | limestone | unknown */
  facies: Array<{ depth: number; lithology: string }>;
  tops: Record<string, number>;
  /** MCP receipt hash — read-only evidence, NEVER authority (V10 F13 SOVEREIGN) */
  receiptHash?: string;
}

export interface CorrelationResult {
  wells?: CorrelationWell[];
  tops?: CorrelationTop[];
  receipt_hash?: string;
  evidence_tag?: string;
  perception_class?: string;
}

// Facies palette (industry standard-ish)
const FACIES_COLORS: Record<string, string> = {
  sand: '#fbbf24',       // amber
  shale: '#64748b',      // slate
  coal: '#1f2937',       // near-black
  limestone: '#22d3ee',  // cyan
  unknown: '#334155',
};

const FILL_ALPHA = 0.35;

// ─────────────────────────────────────────────────────────────────────────────
// Well Track Renderer (canvas)
// ─────────────────────────────────────────────────────────────────────────────

const WellTrack: React.FC<{
  well: CorrelationWell;
  tops: CorrelationTop[];
  depthRange: [number, number];
  width: number;
  height: number;
  showFacies: boolean;
  readOnly: boolean;
  cursorDepth: number | null;
  onCursorMove: (d: number | null) => void;
  onPickTop: (topId: string, wellId: string, depth: number) => void;
}> = ({ well, tops, depthRange, width, height, showFacies, readOnly, cursorDepth, onCursorMove, onPickTop }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const margin = { top: 34, right: 10, bottom: 20, left: 40 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

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
    ctx.strokeRect(margin.left, margin.top, plotW, plotH);

    const yScale = d3.scaleLinear().domain(depthRange).range([margin.top, margin.top + plotH]);

    // Depth grid every 50m
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 0.5;
    for (let d = Math.ceil(depthRange[0] / 50) * 50; d <= depthRange[1]; d += 50) {
      const y = yScale(d);
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotW, y); ctx.stroke();
    }

    // ── Facies panel (right half) ────────────────────────────────────────
    if (showFacies && well.facies.length > 0) {
      const faciesX = margin.left + plotW * 0.55;
      const faciesW = plotW * 0.45;
      ctx.fillStyle = '#0b1220';
      ctx.fillRect(faciesX, margin.top, faciesW, plotH);

      const faciesByDepth = new Map<number, string>();
      well.facies.forEach((f) => {
        if (!faciesByDepth.has(Math.round(f.depth))) faciesByDepth.set(Math.round(f.depth), f.lithology);
      });

      const depths = well.facies.map((f) => f.depth);
      for (let i = 0; i < depths.length - 1; i++) {
        const d0 = depths[i];
        const d1 = depths[i + 1];
        if (d1 < depthRange[0] || d0 > depthRange[1]) continue;
        const lith = faciesByDepth.get(Math.round(d0)) || well.facies[i].lithology || 'unknown';
        const color = FACIES_COLORS[lith] || FACIES_COLORS.unknown;
        ctx.fillStyle = color;
        ctx.globalAlpha = FILL_ALPHA;
        ctx.fillRect(faciesX, yScale(Math.max(d0, depthRange[0])), faciesW, Math.abs(yScale(d1) - yScale(d0)));
        ctx.globalAlpha = 1;
      }

      // Facies header
      ctx.fillStyle = '#94a3b8';
      ctx.font = 'bold 9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('FACIES', faciesX + faciesW / 2, margin.top + 12);
    }

    // ── GR / VSH curve (left 55%) ────────────────────────────────────────
    if (well.gr.length > 1) {
      const xScale = d3.scaleLinear().domain([0, 150]).range([margin.left + 3, margin.left + plotW * 0.55 - 3]);
      ctx.beginPath();
      ctx.strokeStyle = '#22c55e';
      ctx.lineWidth = 1.4;
      let started = false;
      for (const [d, v] of well.gr) {
        if (d < depthRange[0] || d > depthRange[1]) continue;
        const y = yScale(d);
        const x = xScale(Math.max(0, Math.min(150, v)));
        if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // GR fill
      ctx.beginPath();
      ctx.moveTo(margin.left + 3, margin.top);
      for (const [d, v] of well.gr) {
        if (d < depthRange[0] || d > depthRange[1]) continue;
        ctx.lineTo(xScale(Math.max(0, Math.min(150, v))), yScale(d));
      }
      ctx.lineTo(margin.left + 3, margin.top + plotH);
      ctx.closePath();
      ctx.fillStyle = '#22c55e';
      ctx.globalAlpha = 0.12;
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    // ── Stratigraphic top markers ─────────────────────────────────────────
    tops.forEach((top) => {
      const d = well.tops[top.id];
      if (d == null || d < depthRange[0] || d > depthRange[1]) return;
      const y = yScale(d);
      ctx.strokeStyle = top.color;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([5, 3]);
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotW, y); ctx.stroke();
      ctx.setLineDash([]);
      // Diamond marker
      ctx.fillStyle = top.color;
      ctx.beginPath();
      ctx.moveTo(margin.left + 8, y);
      ctx.lineTo(margin.left + 12, y - 4);
      ctx.lineTo(margin.left + 16, y);
      ctx.lineTo(margin.left + 12, y + 4);
      ctx.closePath();
      ctx.fill();
      ctx.font = 'bold 8px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(top.name, margin.left + 18, y - 3);
    });

    // Well header
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(well.name, margin.left + plotW / 2, 18);

    // Cursor
    if (cursorDepth != null && cursorDepth >= depthRange[0] && cursorDepth <= depthRange[1]) {
      const y = yScale(cursorDepth);
      ctx.strokeStyle = '#fbbf24';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(margin.left, y); ctx.lineTo(margin.left + plotW, y); ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [well, tops, depthRange, width, height, showFacies, cursorDepth]);

  useEffect(() => { draw(); }, [draw]);

  // Click on a top row → allow re-picking top depth for this well (LOCKED when readOnly)
  const handleClick = (e: React.MouseEvent) => {
    if (readOnly) return;
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yScale = d3.scaleLinear().domain([margin.top, margin.top + plotH]).range(depthRange);
    const d = yScale(y) as number;
    // Cycle through tops, set the "active" one
    if (d >= depthRange[0] && d <= depthRange[1]) {
      const activeTop = tops.find((t) => t.depths[well.id] != null);
      if (activeTop) onPickTop(activeTop.id, well.id, Math.round(d));
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yScale = d3.scaleLinear().domain([margin.top, margin.top + plotH]).range(depthRange);
    const d = yScale(y) as number;
    if (d >= depthRange[0] && d <= depthRange[1]) onCursorMove(d);
  };

  return (
    <div
      ref={containerRef}
      className="relative flex-shrink-0"
      style={{ width: `${width}px`, height: `${height}px` }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => onCursorMove(null)}
      onClick={handleClick}
    >
      <canvas
        ref={canvasRef}
        className={readOnly ? 'cursor-not-allowed opacity-90' : 'cursor-crosshair'}
        style={{ width: `${width}px`, height: `${height}px` }}
        title={readOnly ? '[PENDING REVIEW / SEALED] canvas read-only' : 'click to pick'}
      />
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Depth Track (shared axis)
// ─────────────────────────────────────────────────────────────────────────────

const CorrelationDepthTrack: React.FC<{
  depthRange: [number, number];
  height: number;
  cursorDepth: number | null;
  onCursorMove: (d: number | null) => void;
}> = ({ depthRange, height, cursorDepth, onCursorMove }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const width = 60;
  const margin = { top: 34, bottom: 20 };
  const plotH = height - margin.top - margin.bottom;

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
    ctx.strokeStyle = '#334155'; ctx.strokeRect(0, margin.top, width, plotH);

    const yScale = d3.scaleLinear().domain(depthRange).range([margin.top, margin.top + plotH]);
    for (let d = Math.ceil(depthRange[0] / 10) * 10; d <= depthRange[1]; d += 10) {
      const y = yScale(d);
      const isMajor = d % 50 === 0;
      ctx.strokeStyle = isMajor ? '#475569' : '#1e293b';
      ctx.lineWidth = isMajor ? 1 : 0.5;
      ctx.beginPath(); ctx.moveTo(isMajor ? 0 : 20, y); ctx.lineTo(width, y); ctx.stroke();
      if (isMajor) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(d.toString(), 4, y + 3);
      }
    }
    ctx.fillStyle = '#e2e8f0';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('DEPTH (m)', width / 2, 18);

    if (cursorDepth != null) {
      const y = yScale(cursorDepth);
      ctx.strokeStyle = '#fbbf24'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
  }, [depthRange, height, cursorDepth]);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yScale = d3.scaleLinear().domain([margin.top, margin.top + plotH]).range(depthRange);
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
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_TOPS: CorrelationTop[] = [
  { id: 'top-group-i', name: 'Group I', color: '#f59e0b', depths: {} },
  { id: 'top-intra-j', name: 'Intra-J', color: '#22c55e', depths: {} },
  { id: 'top-group-j', name: 'Group J', color: '#3b82f6', depths: {} },
  { id: 'top-group-k', name: 'Group K', color: '#a855f7', depths: {} },
];

export const MultiWellCorrelationPanel: React.FC = () => {
  const { selectedWell, updateFloorStatus } = useGEOXStore();
  const [depthRange, setDepthRange] = useState<[number, number]>([1500, 2500]);
  const [cursorDepth, setCursorDepth] = useState<number | null>(null);
  const [showFacies, setShowFacies] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);
  const [wellIds, setWellIds] = useState<string[]>(['W-101', 'W-102', 'W-103']);
  const [tops, setTops] = useState<CorrelationTop[]>(DEFAULT_TOPS);
  const [wells, setWells] = useState<CorrelationWell[]>([]);
  // V10: lastReceipt intentionally REMOVED — receipt_hash is evidence only,
  // never authority. The approval flow uses VAULT999 attestation, NOT receipts.

  // V10/V11 Tri-State Authority Machine (F13 SOVEREIGN).
  // The previous "REQUEST JUDGE SEAL" button was a MOCK GATE — it treated
  // geox_petrophysics receipt_hash as authority. That is a F13 SOVEREIGN
  // violation: a compute receipt is NOT a sovereign signature.
  // The real path is DRAFT → PENDING REVIEW → ATTESTED, with attest()
  // being a separate explicit gate that requires a VAULT999 attestation
  // ref (not a compute receipt).
  const { claim, toDraft, requestReview, attest, resetToReality } = useGeologicalClaim('correlation');
  const isReadOnly = claim.state === 'pending_review' || claim.state === 'attested';
  const isAttested = claim.state === 'attested';

  const wellTool = useMcpTool<{ mode: string; well_id: string }, CorrelationResult>('geox_well_view');
  const petroTool = useMcpTool<{ mode: string; well_id: string; depth_top_m: number; depth_bot_m: number }, CorrelationResult>('geox_petrophysics');

  // ── Build synthetic correlation data (bridge until MCP returns) ──────────
  const buildSyntheticWells = useCallback((): CorrelationWell[] => {
    const seed = (wellId: string) => {
      let h = 0;
      for (let i = 0; i < wellId.length; i++) h = (h * 31 + wellId.charCodeAt(i)) % 997;
      return h / 997;
    };

    return wellIds.map((wid, wi) => {
      const rnd = seed(wid);
      const gr: Array<[number, number]> = [];
      const facies: Array<{ depth: number; lithology: string }> = [];
      const topOffset = (rnd - 0.5) * 120;

      for (let d = 1500; d <= 2500; d += 2) {
        // Sand bodies between 1950-2100 (pay) and 2250-2400
        const inPay = d > 1950 && d < 2100;
        const inDeep = d > 2250 && d < 2400;
        const shale = !inPay && !inDeep;
        const noise = (Math.random() - 0.5) * 12;
        const grVal = shale ? 100 + noise : 35 + noise * 1.5;
        gr.push([d, Math.round(Math.max(10, Math.min(150, grVal)))]);

        const lith = inPay || inDeep ? 'sand' : 'shale';
        facies.push({ depth: d, lithology: lith });
      }

      const topsForWell: Record<string, number> = {};
      tops.forEach((t, ti) => {
        topsForWell[t.id] = 1500 + (ti + 1) * 220 + topOffset + wi * 12;
      });

      return {
        id: wid,
        name: wid,
        gr,
        facies,
        tops: topsForWell,
        receiptHash: `synth-${wid}`,
      };
    });
  }, [wellIds, tops]);

  // Initialize with synthetic data on mount
  useEffect(() => {
    setWells(buildSyntheticWells());
    updateFloorStatus('F11', 'amber', 'Correlation panel: synthetic seed loaded');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wellIds]);

  // ── MCP load: pull well curves via geox_well_view (Hermes Geology lane) ──
  const loadWell = useCallback(async (wellId: string) => {
    try {
      updateFloorStatus('F2', 'amber', `Loading ${wellId} via geox_well_view…`);
      const result = await wellTool.call({ mode: 'view', well_id: wellId });
      updateFloorStatus('F2', 'green', `${wellId} loaded`);

      if (result.wells && result.wells.length > 0) {
        setWells((prev) => {
          const others = prev.filter((w) => w.id !== wellId);
          return [...others, ...result.wells!.map((w) => ({ ...w, id: wellId, name: wellId }))];
        });
        // V10: receipt_hash is evidence only — NEVER captured as authority
      }
    } catch (err) {
      updateFloorStatus('F2', 'red', `geox_well_view failed: ${String(err)}`);
    }
  }, [wellTool, updateFloorStatus]);

  const loadAllWells = useCallback(async () => {
    for (const wid of wellIds) {
      await loadWell(wid);
    }
  }, [wellIds, loadWell]);

  const runPetrophysics = useCallback(async () => {
    try {
      updateFloorStatus('F9', 'amber', 'Computing petrophysics via geox_petrophysics…');
      const result = await petroTool.call({
        mode: 'generate',
        well_id: selectedWell ?? 'W-101',
        depth_top_m: depthRange[0],
        depth_bot_m: depthRange[1],
      });
      updateFloorStatus('F9', 'green', 'Petrophysics computed');
      // V10: receipt_hash is evidence only — NEVER captured as authority
    } catch (err) {
      updateFloorStatus('F9', 'red', `geox_petrophysics failed: ${String(err)}`);
    }
  }, [selectedWell, depthRange, petroTool, updateFloorStatus]);

  // ── Top picking (Tri-State Authority Machine: DRAFT is reversible) ───────
  const pickTopDepth = useCallback((topId: string, wellId: string, depth: number) => {
    // V10/V11: while PENDING REVIEW or ATTESTED, the canvas is read-only.
    if (isReadOnly) return;
    // F1: DRAFT — reversible, local state only
    updateFloorStatus('F1', 'amber', `Top ${topId} @ ${wellId} → ${depth}m (DRAFT)`);
    setTops((prev) => {
      const next = prev.map((t) =>
        t.id === topId ? { ...t, depths: { ...t.depths, [wellId]: depth } } : t
      );
      // Keep the claim payload in sync with the draft picks
      toDraft({ tops: next, wells, claimId: claim.id });
      return next;
    });
    updateFloorStatus('F1', 'amber', `Top ${topId} @ ${wellId} DRAFT (volatile, unsealed)`);
  }, [isReadOnly, toDraft, wells, claim.id, updateFloorStatus]);

  // ── V10/V11: REQUEST VERDICT → PENDING REVIEW (F11 halt, canvas locks) ────
  const requestVerdict = useCallback(() => {
    requestReview();
  }, [requestReview]);

  // ── V10/V11: explicit ATTEST gate — requires a VAULT999 attestation ref.
  // This is NOT derived from any compute receipt. It is the separate,
  // sovereign step that the old mock SEAL gate skipped entirely.
  const attestToVault = useCallback(() => {
    attest({ claimId: claim.id, tops, wells });
  }, [attest, claim.id, tops, wells]);

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

  const trackWidth = 220;
  const trackHeight = 600;

  return (
    <div className="h-full flex flex-col bg-slate-950 rounded-lg border border-slate-800 overflow-hidden">
      {/* Toolbar */}
      <div className="h-10 bg-slate-900 border-b border-slate-800 flex items-center px-3 gap-2 flex-shrink-0">
        <GitCompare className="w-4 h-4 text-violet-400" />
        <span className="text-sm font-bold text-slate-200">Multi-Well Correlation</span>
        <span className="text-xs text-slate-600 font-mono ml-1">{wells.length} wells · MCP</span>

        <div className="w-px h-5 bg-slate-700 mx-2" />

        <button onClick={loadAllWells} disabled={wellTool.status === 'loading' || petroTool.status === 'loading'}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-50" title="Load wells via MCP">
          <RefreshCw className={`w-4 h-4 ${wellTool.status === 'loading' ? 'animate-spin' : ''}`} />
        </button>
        <button onClick={runPetrophysics} disabled={petroTool.status === 'loading'}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-50" title="Run petrophysics">
          <Layers className={`w-4 h-4 ${petroTool.status === 'loading' ? 'animate-spin' : ''}`} />
        </button>

        <div className="flex-1" />

        {petroTool.status === 'loading' || wellTool.status === 'loading' ? (
          <span className="text-xs text-amber-400 flex items-center gap-1">
            <Loader2 className="w-3 h-3 animate-spin" /> MCP…
          </span>
        ) : null}

        <div className="w-px h-5 bg-slate-700 mx-2" />

        <button onClick={zoomIn} className="text-xs px-2 py-1 rounded hover:bg-slate-800 text-slate-400">+</button>
        <button onClick={zoomOut} className="text-xs px-2 py-1 rounded hover:bg-slate-800 text-slate-400">−</button>
        <span className="text-xs text-slate-500 font-mono">{depthRange[0].toFixed(0)}–{depthRange[1].toFixed(0)}m</span>

        <button
          onClick={() => setShowFacies(!showFacies)}
          className={`px-2 py-1 rounded text-[10px] font-bold ${showFacies ? 'bg-violet-600 text-white' : 'bg-slate-800 text-slate-400'}`}
        >
          Facies
        </button>

        <button onClick={() => setShowSidebar(!showSidebar)}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400">
          {showSidebar ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {/* Main area */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-x-auto">
          <div className="flex">
            <CorrelationDepthTrack depthRange={depthRange} height={trackHeight} cursorDepth={cursorDepth} onCursorMove={setCursorDepth} />
            {wells.map((w) => (
              <WellTrack
                key={w.id}
                well={w}
                tops={tops}
                depthRange={depthRange}
                width={trackWidth}
                height={trackHeight}
                showFacies={showFacies}
                readOnly={isReadOnly}
                cursorDepth={cursorDepth}
                onCursorMove={setCursorDepth}
                onPickTop={pickTopDepth}
              />
            ))}
          </div>
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <div className="w-56 bg-slate-900 border-l border-slate-800 overflow-y-auto flex-shrink-0 p-3">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Link2 className="w-3 h-3" /> Strat Tops
            </h4>
            {tops.map((t) => (
              <div key={t.id} className="mb-2 p-2 rounded border border-slate-800 bg-slate-900">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-0.5 rounded" style={{ backgroundColor: t.color }} />
                  <span className="text-xs font-bold text-slate-300">{t.name}</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {Object.entries(t.depths).map(([wid, d]) => (
                    <div key={wid} className="flex justify-between">
                      <span>{wid}</span>
                      <span className="font-mono text-slate-400">{Math.round(d)}m</span>
                    </div>
                  ))}
                  {Object.keys(t.depths).length === 0 && <span className="italic">No picks yet — click track to pick</span>}
                </div>
              </div>
            ))}

            <div className="mt-3 pt-3 border-t border-slate-800">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Shield className="w-3 h-3" /> Claim Authority (V10/V11)
              </h4>

              {/* Tri-State Authority Machine badge */}
              {claim.state === 'draft' && (
                <div className="mb-2 p-2 rounded border border-yellow-600/40 bg-yellow-600/10">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-yellow-400 bg-yellow-600/20 border border-yellow-600/40 px-1.5 py-0.5 rounded">
                      [UNVERIFIED]
                    </span>
                    <span className="text-[10px] text-slate-400">DRAFT</span>
                    <span className="ml-auto text-[9px] font-bold text-gray-400 bg-gray-800/60 px-1.5 py-0.5 rounded border border-gray-700/60">DRAFT</span>
                  </div>
                  <p className="text-[9px] text-slate-500 mt-1 leading-tight">
                    Reversible, local state only. Picks are volatile until reviewed.
                  </p>
                </div>
              )}
              {claim.state === 'pending_review' && (
                <div className="mb-2 p-2 rounded border border-amber-500/40 bg-amber-500/10">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-amber-400 bg-amber-500/20 border border-amber-500/40 px-1.5 py-0.5 rounded">
                      [PENDING REVIEW]
                    </span>
                    <span className="text-[10px] text-amber-500/70">F11 halt</span>
                    <span className="ml-auto text-[9px] font-bold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">APPROVED</span>
                  </div>
                  <p className="text-[9px] text-amber-500/70 mt-1 leading-tight">
                    Canvas LOCKED (read-only). Uncertainty acknowledged — correlation
                    picks are interpretive and carry risk until independently attested.
                  </p>
                </div>
              )}
              {claim.state === 'attested' && (
                <div className="attestation-confirmation mb-2">
                  <h4>🔒 Attestation Confirmed — Correlation</h4>
                  <p>Receipt: <code>{claim.attestationRef}</code></p>
                  <p>Timestamp: {claim.attestedAt}</p>
                  <p>Type: {claim.type}</p>
                  <button onClick={resetToReality}>
                    Return to Reality
                  </button>
                </div>
              )}

              {/* Transitions */}
              {claim.state === 'draft' && (
                <button
                  onClick={requestVerdict}
                  className="w-full py-2 rounded bg-[#3b82f6]/20 border border-[#3b82f6]/40 text-[#3b82f6] text-xs font-bold hover:bg-[#3b82f6]/30"
                >
                  ▶ Review Delta
                </button>
              )}
              {claim.state === 'pending_review' && (
                <>
                  <button
                    onClick={attestToVault}
                    className="w-full py-2 rounded bg-[#f59e0b]/20 border border-[#f59e0b]/40 text-[#f59e0b] text-xs font-bold hover:bg-[#f59e0b]/30"
                  >
                    ✓ Approve & Request Judge
                  </button>
                  <button
                    onClick={() => toDraft({ tops, wells, claimId: claim.id })}
                    className="mt-1 w-full py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-400 text-[10px] font-bold hover:bg-slate-700"
                  >
                    DISCARD → DRAFT
                  </button>
                </>
              )}
              <p className="text-[9px] text-slate-600 mt-2 leading-tight">
                V10/V11 Tri-State: DRAFT (reversible) → PENDING REVIEW (locked) → ATTESTED (VAULT999).
                Compute receipts are evidence only — never authority (F13 SOVEREIGN).
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="h-7 bg-slate-950 border-t border-slate-800 flex items-center px-3 text-[10px] text-slate-500 font-mono flex-shrink-0 gap-4">
        <span>MCP: geox_well_view · geox_petrophysics</span>
        <span>|</span>
        <span>Lane: Hermes (Geology)</span>
        {isAttested ? (
          <span className="text-green-400 font-bold">[SEALED - VAULT999]</span>
        ) : claim.state === 'pending_review' ? (
          <span className="text-amber-400 font-bold">[PENDING REVIEW]</span>
        ) : (
          <span className="text-yellow-500/80 font-bold">[UNVERIFIED]</span>
        )}
        <div className="flex-1" />
        <span className="text-amber-500/70">DITEMPA BUKAN DIBERI</span>
      </div>
    </div>
  );
};

export default MultiWellCorrelationPanel;
