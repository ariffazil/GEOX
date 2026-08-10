/**
 * WellCorrelationPanel — Multi-Well Stratigraphic Correlation
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Side-by-side well log tracks with correlation lines connecting
 * stratigraphic tops across wells. Canvas-based rendering via d3.js.
 *
 * Renders per well: GR (green), RHOB (red), NPHI (blue), DT (orange)
 * Correlation features: stratigraphic top picks, facies zone coloring
 * Supports d3.zoom for depth axis pan/zoom.
 */

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import * as d3 from 'd3';
import {
  Layers, ZoomIn, ZoomOut, RefreshCw, AlertTriangle,
  CheckCircle, Loader2, GitMerge, ChevronDown, ChevronUp,
} from 'lucide-react';
import { useMcpTool } from '../../hooks/useMcpTool';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface WellInput {
  wellId: string;
  depthTop?: number;
  depthBase?: number;
}

interface WellIngestResult {
  well_id?: string;
  curves?: {
    depth?: number[];
    gr?: number[];
    rhob?: number[];
    nphi?: number[];
    dt?: number[];
    [key: string]: number[] | undefined;
  };
  tops?: { depth: number; name: string; facies?: string }[];
  facies?: string[];
  depth_range?: [number, number];
  receipt_hash?: string;
}

interface WellPetroResult {
  vsh?: number[];
  phie?: number[];
  sw?: number[];
  depth?: number[];
  litho_class?: string;
  facies?: string[];
}

interface WellColumn {
  wellId: string;
  curves: {
    depth: number[];
    gr: number[];
    rhob: number[];
    nphi: number[];
    dt: number[];
  } | null;
  tops: { depth: number; name: string; facies?: string }[] | null;
  facies: string[] | null;
  loading: boolean;
  error: string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Curve config
// ─────────────────────────────────────────────────────────────────────────────

interface CurveConfig {
  key: 'gr' | 'rhob' | 'nphi' | 'dt';
  label: string;
  color: string;
  unit: string;
  min: number;
  max: number;
}

const CURVE_CONFIGS: CurveConfig[] = [
  { key: 'gr', label: 'GR', color: '#22c55e', unit: 'API', min: 0, max: 200 },
  { key: 'rhob', label: 'RHOB', color: '#ef4444', unit: 'g/cm³', min: 1.6, max: 2.8 },
  { key: 'nphi', label: 'NPHI', color: '#3b82f6', unit: 'v/v', min: -0.1, max: 0.6 },
  { key: 'dt', label: 'DT', color: '#f97316', unit: 'μs/ft', min: 40, max: 140 },
];

// ─────────────────────────────────────────────────────────────────────────────
// Facies color map
// ─────────────────────────────────────────────────────────────────────────────

const FACIES_COLORS: Record<string, string> = {
  sand: 'rgba(250, 204, 21, 0.12)',
  shale: 'rgba(148, 163, 184, 0.12)',
  carbonate: 'rgba(59, 130, 246, 0.12)',
  limestone: 'rgba(59, 130, 246, 0.12)',
  dolomite: 'rgba(99, 102, 241, 0.12)',
  siltstone: 'rgba(217, 187, 55, 0.08)',
  mudstone: 'rgba(100, 116, 139, 0.12)',
  unknown: 'transparent',
};

function getFaciesColor(facies: string | undefined): string {
  if (!facies) return FACIES_COLORS.unknown;
  return FACIES_COLORS[facies.toLowerCase()] ?? FACIES_COLORS.unknown;
}

// ─────────────────────────────────────────────────────────────────────────────
// Layout constants
// ─────────────────────────────────────────────────────────────────────────────

const HEADER_HEIGHT = 44;
const WELL_NAME_HEIGHT = 28;
const DEPTH_AXIS_WIDTH = 56;
const TRACK_WIDTH = 80;
const TRACKS_PER_WELL = CURVE_CONFIGS.length; // 4
const WELL_TOTAL_WIDTH = DEPTH_AXIS_WIDTH + TRACK_WIDTH * TRACKS_PER_WELL + 16; // padding
const CORRELATION_GAP = 40; // gap between wells for correlation lines
const TRACK_HEIGHT = 600;
const MARGIN = { top: 8, right: 4, bottom: 16, left: 4 };
const ZOOM_LABEL_HEIGHT = 24;

// ─────────────────────────────────────────────────────────────────────────────
// Style helpers
// ─────────────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: '#0a0a0f',
    color: '#e2e8f0',
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
    overflow: 'hidden',
    userSelect: 'none',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    height: HEADER_HEIGHT,
    minHeight: HEADER_HEIGHT,
    padding: '0 16px',
    backgroundColor: '#0d0d14',
    borderBottom: '1px solid #1a1a2e',
    gap: 12,
  },
  headerTitle: {
    fontSize: 13,
    fontWeight: 700,
    color: '#00d4aa',
    letterSpacing: '0.05em',
  },
  headerBadge: {
    fontSize: 9,
    fontWeight: 600,
    color: '#d4af37',
    backgroundColor: 'rgba(212, 175, 55, 0.1)',
    border: '1px solid rgba(212, 175, 55, 0.2)',
    borderRadius: 4,
    padding: '2px 8px',
    letterSpacing: '0.08em',
  },
  headerSep: {
    width: 1,
    height: 20,
    backgroundColor: '#1a1a2e',
  },
  headerInfo: {
    fontSize: 10,
    color: '#64748b',
  },
  scrollArea: {
    flex: 1,
    overflowX: 'auto',
    overflowY: 'hidden',
    position: 'relative' as const,
  },
  wellsRow: {
    display: 'flex',
    alignItems: 'stretch',
    height: TRACK_HEIGHT + WELL_NAME_HEIGHT + ZOOM_LABEL_HEIGHT + MARGIN.top + MARGIN.bottom,
    minHeight: TRACK_HEIGHT + WELL_NAME_HEIGHT + ZOOM_LABEL_HEIGHT + MARGIN.top + MARGIN.bottom,
    padding: `${MARGIN.top}px ${MARGIN.right}px ${MARGIN.bottom}px ${MARGIN.left}px`,
  },
  wellColumn: {
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
    position: 'relative',
  },
  wellNameBar: {
    height: WELL_NAME_HEIGHT,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0d0d14',
    borderBottom: '1px solid #1a1a2e',
    borderTop: '1px solid #1a1a2e',
    fontSize: 11,
    fontWeight: 700,
    color: '#00d4aa',
    letterSpacing: '0.04em',
  },
  correlationGap: {
    width: CORRELATION_GAP,
    flexShrink: 0,
    position: 'relative' as const,
  },
  loadingOverlay: {
    position: 'absolute' as const,
    inset: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(10, 10, 15, 0.85)',
    zIndex: 10,
    gap: 8,
  },
  loadingSpinner: {
    width: 24,
    height: 24,
    border: '2px solid #1a1a2e',
    borderTop: '2px solid #00d4aa',
    borderRadius: '50%',
    animation: 'geox-spin 1s linear infinite',
  },
  loadingText: {
    fontSize: 10,
    color: '#64748b',
    letterSpacing: '0.05em',
  },
  errorOverlay: {
    position: 'absolute' as const,
    inset: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(10, 10, 15, 0.85)',
    zIndex: 10,
    gap: 6,
  },
  errorText: {
    fontSize: 10,
    color: '#ef4444',
    textAlign: 'center',
    maxWidth: TRACK_WIDTH + DEPTH_AXIS_WIDTH,
    padding: '0 8px',
  },
  statusBar: {
    height: 28,
    minHeight: 28,
    display: 'flex',
    alignItems: 'center',
    padding: '0 16px',
    backgroundColor: '#0a0a0f',
    borderTop: '1px solid #1a1a2e',
    fontSize: 9,
    color: '#475569',
    gap: 16,
    fontFamily: "'JetBrains Mono', monospace",
  },
  zoomLabel: {
    fontSize: 9,
    color: '#64748b',
    textAlign: 'center' as const,
    height: ZOOM_LABEL_HEIGHT,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Single Well Column — renders 4 curve tracks on a shared canvas
// ─────────────────────────────────────────────────────────────────────────────

interface WellCanvasProps {
  column: WellColumn;
  depthRange: [number, number];
  height: number;
  onCursorMove: (depth: number | null) => void;
}

const WellCanvas: React.FC<WellCanvasProps> = ({
  column, depthRange, height, onCursorMove,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const trackHeight = height - MARGIN.top - MARGIN.bottom;
  const totalWidth = DEPTH_AXIS_WIDTH + TRACK_WIDTH * TRACKS_PER_WELL;

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = totalWidth * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${totalWidth}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, totalWidth, height);

    // Background
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(0, 0, totalWidth, height);

    const yScale = d3.scaleLinear()
      .domain(depthRange)
      .range([MARGIN.top, MARGIN.top + trackHeight]);

    // ─── Depth axis ──────────────────────────────────────────────────
    ctx.strokeStyle = '#1a1a2e';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, MARGIN.top, DEPTH_AXIS_WIDTH, trackHeight);

    // Depth grid lines
    const depthStep = 50;
    ctx.fillStyle = '#64748b';
    ctx.font = '9px monospace';
    ctx.textAlign = 'right';
    for (let d = Math.ceil(depthRange[0] / depthStep) * depthStep; d <= depthRange[1]; d += depthStep) {
      const y = yScale(d);
      ctx.strokeStyle = '#1a1a2e';
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      ctx.moveTo(DEPTH_AXIS_WIDTH, y);
      ctx.lineTo(totalWidth, y);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.fillText(d.toString(), DEPTH_AXIS_WIDTH - 4, y + 3);
    }

    // Minor grid lines
    const minorStep = 10;
    for (let d = Math.ceil(depthRange[0] / minorStep) * minorStep; d <= depthRange[1]; d += minorStep) {
      if (d % depthStep === 0) continue;
      const y = yScale(d);
      ctx.strokeStyle = '#111119';
      ctx.lineWidth = 0.3;
      ctx.beginPath();
      ctx.moveTo(DEPTH_AXIS_WIDTH, y);
      ctx.lineTo(totalWidth, y);
      ctx.stroke();
    }

    // ─── Draw 4 curve tracks ────────────────────────────────────────
    if (!column.curves) return;

    CURVE_CONFIGS.forEach((cfg, trackIdx) => {
      const trackX = DEPTH_AXIS_WIDTH + trackIdx * TRACK_WIDTH;
      const trackLeft = trackX + 4;
      const trackRight = trackX + TRACK_WIDTH - 4;
      const plotWidth = trackRight - trackLeft;

      // Track border
      ctx.strokeStyle = '#1a1a2e';
      ctx.lineWidth = 0.5;
      ctx.strokeRect(trackX, MARGIN.top, TRACK_WIDTH, trackHeight);

      // Track header
      ctx.fillStyle = cfg.color;
      ctx.font = 'bold 9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(cfg.label, trackX + TRACK_WIDTH / 2, MARGIN.top - 2);

      // X scale
      const xScale = d3.scaleLinear()
        .domain([cfg.min, cfg.max])
        .range([trackLeft, trackRight]);

      // Fill scale lines (min/max labels)
      ctx.fillStyle = cfg.color;
      ctx.font = '7px monospace';
      ctx.globalAlpha = 0.5;
      ctx.textAlign = 'left';
      ctx.fillText(cfg.min.toString(), trackLeft, MARGIN.top + 10);
      ctx.textAlign = 'right';
      ctx.fillText(cfg.max.toString(), trackRight, MARGIN.top + 10);
      ctx.globalAlpha = 1;

      // Draw curve line
      const curves = column.curves;
      if (!curves) return;
      const curveData = curves[cfg.key];
      const depths = curves.depth;
      if (!curveData || !depths || depths.length === 0) return;

      ctx.beginPath();
      ctx.strokeStyle = cfg.color;
      ctx.lineWidth = 1.2;
      let started = false;

      for (let i = 0; i < depths.length; i++) {
        const d = depths[i];
        if (d < depthRange[0] || d > depthRange[1]) continue;
        const val = curveData[i];
        if (val == null || isNaN(val)) {
          started = false;
          continue;
        }
        const y = yScale(d);
        const x = xScale(val);
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    });
  }, [column, depthRange, height, trackHeight, totalWidth]);

  useEffect(() => {
    draw();
  }, [draw]);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const yScale = d3.scaleLinear()
      .domain([MARGIN.top, MARGIN.top + trackHeight])
      .range(depthRange);
    const depth = yScale(y) as number;
    if (depth >= depthRange[0] && depth <= depthRange[1]) {
      onCursorMove(depth);
    }
  };

  return (
    <div
      ref={containerRef}
      style={{ position: 'relative', width: totalWidth, height }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => onCursorMove(null)}
    >
      <canvas
        ref={canvasRef}
        style={{ width: totalWidth, height, cursor: 'crosshair' }}
      />
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Correlation Gap Canvas — draws correlation lines and facies between wells
// ─────────────────────────────────────────────────────────────────────────────

interface CorrelationGapProps {
  leftColumn: WellColumn;
  rightColumn: WellColumn;
  depthRange: [number, number];
  height: number;
}

const CorrelationGap: React.FC<CorrelationGapProps> = ({
  leftColumn, rightColumn, depthRange, height,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const trackHeight = height - MARGIN.top - MARGIN.bottom;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = CORRELATION_GAP * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${CORRELATION_GAP}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, CORRELATION_GAP, height);

    // Background
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(0, 0, CORRELATION_GAP, height);

    const yScale = d3.scaleLinear()
      .domain(depthRange)
      .range([MARGIN.top, MARGIN.top + trackHeight]);

    // ─── Facies zone bands between wells ────────────────────────────
    // Use tops from either well that have facies info
    const leftTops = leftColumn.tops ?? [];
    const rightTops = rightColumn.tops ?? [];
    const allTops = [...leftTops, ...rightTops]
      .filter(t => t.facies)
      .sort((a, b) => a.depth - b.depth);

    if (allTops.length > 0) {
      // Draw facies zones between consecutive tops
      for (let i = 0; i < allTops.length - 1; i++) {
        const topD = allTops[i].depth;
        const baseD = allTops[i + 1].depth;
        const y1 = Math.max(MARGIN.top, yScale(topD));
        const y2 = Math.min(MARGIN.top + trackHeight, yScale(baseD));
        if (y2 > y1) {
          const color = getFaciesColor(allTops[i].facies);
          ctx.fillStyle = color;
          ctx.fillRect(0, y1, CORRELATION_GAP, y2 - y1);
        }
      }
    }

    // ─── Correlation lines (stratigraphic tops) ─────────────────────
    // Merge tops from both wells by name
    const leftTopMap = new Map(leftTops.map(t => [t.name, t.depth]));
    const rightTopMap = new Map(rightTops.map(t => [t.name, t.depth]));

    const correlatedNames = new Set([
      ...leftTopMap.keys(),
      ...rightTopMap.keys(),
    ]);

    ctx.setLineDash([4, 3]);
    correlatedNames.forEach((name) => {
      const leftDepth = leftTopMap.get(name);
      const rightDepth = rightTopMap.get(name);

      if (leftDepth != null && rightDepth != null) {
        // Both wells have this top — draw a connecting line
        ctx.strokeStyle = '#d4af37';
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        ctx.moveTo(0, yScale(leftDepth));
        ctx.lineTo(CORRELATION_GAP, yScale(rightDepth));
        ctx.stroke();
        ctx.globalAlpha = 1;
      } else if (leftDepth != null) {
        // Only left well — draw tick from left edge
        ctx.strokeStyle = '#d4af37';
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.5;
        ctx.beginPath();
        ctx.moveTo(0, yScale(leftDepth));
        ctx.lineTo(CORRELATION_GAP * 0.4, yScale(leftDepth));
        ctx.stroke();
        ctx.globalAlpha = 1;
      } else if (rightDepth != null) {
        // Only right well — draw tick from right edge
        ctx.strokeStyle = '#d4af37';
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.5;
        ctx.beginPath();
        ctx.moveTo(CORRELATION_GAP * 0.6, yScale(rightDepth));
        ctx.lineTo(CORRELATION_GAP, yScale(rightDepth));
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    });
    ctx.setLineDash([]);
  }, [leftColumn, rightColumn, depthRange, height, trackHeight]);

  return (
    <div
      style={{
        width: CORRELATION_GAP,
        height,
        flexShrink: 0,
        position: 'relative',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: CORRELATION_GAP, height }}
      />
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Top Labels Overlay — draws stratigraphic top labels along the top of the panel
// ─────────────────────────────────────────────────────────────────────────────

interface TopLabelsProps {
  columns: WellColumn[];
  depthRange: [number, number];
  height: number;
}

const TopLabelsOverlay: React.FC<TopLabelsProps> = ({
  columns, depthRange, height,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const trackHeight = height - MARGIN.top - MARGIN.bottom;

  const totalWidth = useMemo(() => {
    return columns.length * WELL_TOTAL_WIDTH + (columns.length - 1) * CORRELATION_GAP;
  }, [columns.length]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = totalWidth * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${totalWidth}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, totalWidth, height);

    const yScale = d3.scaleLinear()
      .domain(depthRange)
      .range([MARGIN.top, MARGIN.top + trackHeight]);

    // Collect all unique top names across all wells
    const topNameSet = new Set<string>();
    columns.forEach((col) => {
      col.tops?.forEach((t) => topNameSet.add(t.name));
    });

    // For each top, find the average y across all wells where it appears
    // and draw a horizontal dashed line across the entire width
    topNameSet.forEach((topName) => {
      const depths: number[] = [];
      columns.forEach((col) => {
        const top = col.tops?.find(t => t.name === topName);
        if (top) depths.push(top.depth);
      });
      if (depths.length === 0) return;

      const avgDepth = depths.reduce((a, b) => a + b, 0) / depths.length;
      const y = yScale(avgDepth);
      if (y < MARGIN.top || y > MARGIN.top + trackHeight) return;

      // Full-width dashed line
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = 'rgba(212, 175, 55, 0.35)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(totalWidth, y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Label
      ctx.fillStyle = '#d4af37';
      ctx.font = 'bold 8px sans-serif';
      ctx.textAlign = 'left';
      const labelText = `${topName} (${avgDepth.toFixed(0)}m)`;
      ctx.fillText(labelText, 4, y - 4);
    });
  }, [columns, depthRange, height, totalWidth, trackHeight]);

  return (
    <div
      style={{
        position: 'absolute',
        top: WELL_NAME_HEIGHT,
        left: 0,
        pointerEvents: 'none',
        zIndex: 5,
      }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: totalWidth, height }}
      />
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// WellColumnData — per-well data loading via MCP
// ─────────────────────────────────────────────────────────────────────────────

function useWellData(wellId: string) {
  const ingestTool = useMcpTool<
    { well_id: string; mode: string },
    WellIngestResult
  >('geox_well_ingest');

  const petroTool = useMcpTool<
    { well_id: string; mode: string },
    WellPetroResult
  >('geox_petrophysics');

  const [column, setColumn] = useState<WellColumn>({
    wellId,
    curves: null,
    tops: null,
    facies: null,
    loading: true,
    error: null,
  });

  const loadData = useCallback(async () => {
    setColumn(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Step 1: Ingest well data
      const ingestResult = await ingestTool.call({ well_id: wellId, mode: 'auto' });

      if (!ingestResult) {
        throw new Error(`No data returned from geox_well_ingest for ${wellId}`);
      }

      // Extract curves
      const curves = ingestResult.curves ?? null;
      const tops = ingestResult.tops ?? null;

      // Step 2: Run petrophysics for facies
      let facies: string[] | null = null;
      try {
        const petroResult = await petroTool.call({ well_id: wellId, mode: 'generate' });
        if (petroResult?.facies) {
          facies = petroResult.facies;
        } else if (petroResult?.litho_class) {
          // Single litho class — replicate across depths
          const depthLen = curves?.depth?.length ?? 0;
          facies = Array(depthLen).fill(petroResult.litho_class.toLowerCase());
        }
      } catch {
        // Petrophysics failure is non-fatal — we still have the raw curves
        console.warn(`[WellCorrelation] Petrophysics failed for ${wellId}, proceeding without facies`);
      }

      setColumn({
        wellId,
        curves: curves ? {
          depth: curves.depth ?? [],
          gr: curves.gr ?? [],
          rhob: curves.rhob ?? [],
          nphi: curves.nphi ?? [],
          dt: curves.dt ?? [],
        } : null,
        tops,
        facies,
        loading: false,
        error: null,
      });
    } catch (err) {
      setColumn(prev => ({
        ...prev,
        loading: false,
        error: String(err),
      }));
    }
  }, [wellId, ingestTool, petroTool]);

  // Load on mount
  useEffect(() => {
    loadData();
  }, [loadData]);

  return { column, reload: loadData };
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export interface WellCorrelationPanelProps {
  wells: WellInput[];
}

export const WellCorrelationPanel: React.FC<WellCorrelationPanelProps> = ({ wells }) => {
  const [cursorDepth, setCursorDepth] = useState<number | null>(null);
  const [showDetails, setShowDetails] = useState(true);

  // ─── Load data for each well via MCP ──────────────────────────────
  const wellHooks = wells.map(w => useWellData(w.wellId));
  const columns: WellColumn[] = wellHooks.map((h, i) => ({
    ...h.column,
    wellId: wells[i].wellId,
  }));

  // ─── Compute shared depth range ───────────────────────────────────
  const depthRange = useMemo<[number, number]>(() => {
    let min = Infinity;
    let max = -Infinity;

    columns.forEach((col, i) => {
      const w = wells[i];
      if (w.depthTop != null) min = Math.min(min, w.depthTop);
      if (w.depthBase != null) max = Math.max(max, w.depthBase);

      if (col.curves?.depth && col.curves.depth.length > 0) {
        const dMin = col.curves.depth[0];
        const dMax = col.curves.depth[col.curves.depth.length - 1];
        if (w.depthTop == null) min = Math.min(min, dMin);
        if (w.depthBase == null) max = Math.max(max, dMax);
      }
    });

    if (!isFinite(min) || !isFinite(max)) {
      return [0, 2000];
    }
    return [min, max];
  }, [columns, wells]);

  // ─── d3.zoom for depth axis pan/zoom ──────────────────────────────
  const [zoomState, setZoomState] = useState<[number, number]>(depthRange);
  const zoomContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setZoomState(depthRange);
  }, [depthRange]);

  useEffect(() => {
    const el = zoomContainerRef.current;
    if (!el) return;

    const totalHeight = TRACK_HEIGHT + MARGIN.top + MARGIN.bottom;

    const zoomBehavior = d3.zoom<HTMLDivElement, unknown>()
      .scaleExtent([0.2, 10])
      .translateExtent([[0, 0], [0, totalHeight]])
      .extent([[0, 0], [0, totalHeight]])
      .on('zoom', (event) => {
        const t = event.transform;
        const [dMin, dMax] = depthRange;
        const span = dMax - dMin;
        const newCenter = dMin + span / 2 - (t.y / totalHeight) * span;
        const newSpan = span / t.k;
        const newMin = newCenter - newSpan / 2;
        const newMax = newCenter + newSpan / 2;
        setZoomState([
          Math.max(depthRange[0] - span * 0.1, newMin),
          Math.min(depthRange[1] + span * 0.1, newMax),
        ]);
      });

    const selection = d3.select(el);
    selection.call(zoomBehavior);

    return () => {
      selection.on('.zoom', null);
    };
  }, [depthRange]);

  const resetZoom = useCallback(() => {
    setZoomState(depthRange);
  }, [depthRange]);

  const zoomIn = useCallback(() => {
    const mid = (zoomState[0] + zoomState[1]) / 2;
    const half = (zoomState[1] - zoomState[0]) / 2;
    setZoomState([mid - half * 0.6, mid + half * 0.6]);
  }, [zoomState]);

  const zoomOut = useCallback(() => {
    const mid = (zoomState[0] + zoomState[1]) / 2;
    const half = (zoomState[1] - zoomState[0]) / 2;
    setZoomState([mid - half * 1.7, mid + half * 1.7]);
  }, [zoomState]);

  // ─── Stats ────────────────────────────────────────────────────────
  const loadedCount = columns.filter(c => !c.loading && !c.error).length;
  const allLoaded = columns.every(c => !c.loading);
  const totalTopCount = columns.reduce((n, c) => n + (c.tops?.length ?? 0), 0);

  const canvasHeight = TRACK_HEIGHT + WELL_NAME_HEIGHT + ZOOM_LABEL_HEIGHT + MARGIN.top + MARGIN.bottom;

  return (
    <div style={styles.container}>
      {/* Inject keyframe animation */}
      <style>{`
        @keyframes geox-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* ─── Header ──────────────────────────────────────────────── */}
      <div style={styles.header}>
        <GitMerge size={14} color="#00d4aa" />
        <span style={styles.headerTitle}>Multi-Well Correlation</span>
        <span style={styles.headerBadge}>
          {columns.length} WELLS
        </span>
        <div style={styles.headerSep} />
        <span style={styles.headerInfo}>
          {totalTopCount} tops identified
        </span>
        <div style={{ flex: 1 }} />

        <button
          onClick={zoomIn}
          style={{
            background: 'none', border: 'none', color: '#64748b', cursor: 'pointer',
            padding: 4, borderRadius: 4,
          }}
          title="Zoom In"
        >
          <ZoomIn size={14} />
        </button>
        <button
          onClick={zoomOut}
          style={{
            background: 'none', border: 'none', color: '#64748b', cursor: 'pointer',
            padding: 4, borderRadius: 4,
          }}
          title="Zoom Out"
        >
          <ZoomOut size={14} />
        </button>
        <button
          onClick={resetZoom}
          style={{
            background: 'none', border: 'none', color: '#64748b', cursor: 'pointer',
            padding: 4, borderRadius: 4,
          }}
          title="Reset Zoom"
        >
          <RefreshCw size={14} />
        </button>

        <div style={styles.headerSep} />
        <button
          onClick={() => setShowDetails(!showDetails)}
          style={{
            background: 'none', border: 'none', color: '#64748b', cursor: 'pointer',
            padding: 4, borderRadius: 4,
          }}
          title="Toggle Details"
        >
          {showDetails ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>

      {/* ─── Curve Legend Bar (when details expanded) ────────────── */}
      {showDetails && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            padding: '4px 16px',
            backgroundColor: '#0d0d14',
            borderBottom: '1px solid #1a1a2e',
            fontSize: 9,
            color: '#64748b',
          }}
        >
          {CURVE_CONFIGS.map((cfg) => (
            <div key={cfg.key} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div
                style={{
                  width: 12,
                  height: 2,
                  backgroundColor: cfg.color,
                  borderRadius: 1,
                }}
              />
              <span style={{ color: cfg.color, fontWeight: 600 }}>{cfg.label}</span>
              <span>({cfg.unit})</span>
            </div>
          ))}
          <div style={{ flex: 1 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 12,
                height: 2,
                backgroundColor: '#d4af37',
                borderRadius: 1,
                borderStyle: 'dashed',
              }}
            />
            <span style={{ color: '#d4af37' }}>Correlation</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 10,
                height: 10,
                backgroundColor: 'rgba(250, 204, 21, 0.3)',
                borderRadius: 2,
              }}
            />
            <span>Sand</span>
            <div
              style={{
                width: 10,
                height: 10,
                backgroundColor: 'rgba(148, 163, 184, 0.3)',
                borderRadius: 2,
                marginLeft: 4,
              }}
            />
            <span>Shale</span>
            <div
              style={{
                width: 10,
                height: 10,
                backgroundColor: 'rgba(59, 130, 246, 0.3)',
                borderRadius: 2,
                marginLeft: 4,
              }}
            />
            <span>Carbonate</span>
          </div>
        </div>
      )}

      {/* ─── Zoom depth indicator ────────────────────────────────── */}
      <div style={styles.zoomLabel}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          {zoomState[0].toFixed(0)}m — {zoomState[1].toFixed(0)}m
          {cursorDepth != null && (
            <span style={{ color: '#d4af37', marginLeft: 12 }}>
              cursor: {cursorDepth.toFixed(1)}m
            </span>
          )}
        </span>
      </div>

      {/* ─── Scrollable well columns ──────────────────────────────── */}
      <div ref={zoomContainerRef} style={styles.scrollArea}>
        <div style={styles.wellsRow}>
          {columns.map((col, idx) => (
            <React.Fragment key={col.wellId}>
              {/* Well column */}
              <div style={styles.wellColumn}>
                {/* Well name */}
                <div style={styles.wellNameBar}>
                  {col.wellId}
                  {col.loading && (
                    <Loader2
                      size={11}
                      color="#00d4aa"
                      style={{ marginLeft: 6, animation: 'geox-spin 1s linear infinite' }}
                    />
                  )}
                  {!col.loading && !col.error && (
                    <CheckCircle size={10} color="#22c55e" style={{ marginLeft: 6 }} />
                  )}
                  {!col.loading && col.error && (
                    <AlertTriangle size={10} color="#ef4444" style={{ marginLeft: 6 }} />
                  )}
                </div>

                {/* Canvas area */}
                <div style={{ position: 'relative' }}>
                  <WellCanvas
                    column={col}
                    depthRange={zoomState}
                    height={TRACK_HEIGHT}
                    onCursorMove={setCursorDepth}
                  />

                  {/* Loading overlay */}
                  {col.loading && (
                    <div style={styles.loadingOverlay}>
                      <div style={styles.loadingSpinner} />
                      <span style={styles.loadingText}>Loading {col.wellId}…</span>
                    </div>
                  )}

                  {/* Error overlay */}
                  {!col.loading && col.error && (
                    <div style={styles.errorOverlay}>
                      <AlertTriangle size={18} color="#ef4444" />
                      <span style={styles.errorText}>{col.error}</span>
                      <button
                        onClick={() => wellHooks[idx].reload()}
                        style={{
                          marginTop: 4,
                          padding: '3px 10px',
                          fontSize: 9,
                          color: '#00d4aa',
                          background: 'rgba(0, 212, 170, 0.1)',
                          border: '1px solid rgba(0, 212, 170, 0.3)',
                          borderRadius: 4,
                          cursor: 'pointer',
                          fontFamily: 'inherit',
                        }}
                      >
                        Retry
                      </button>
                    </div>
                  )}
                </div>

                {/* Zoom label for this well */}
                <div style={styles.zoomLabel}>
                  <span>
                    {col.tops && col.tops.length > 0
                      ? `${col.tops.length} tops`
                      : col.loading ? '…' : 'no tops'}
                  </span>
                </div>
              </div>

              {/* Correlation gap between wells */}
              {idx < columns.length - 1 && (
                <CorrelationGap
                  leftColumn={col}
                  rightColumn={columns[idx + 1]}
                  depthRange={zoomState}
                  height={TRACK_HEIGHT}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Top labels overlay spanning entire width */}
        {allLoaded && columns.some(c => c.tops && c.tops.length > 0) && (
          <TopLabelsOverlay
            columns={columns}
            depthRange={zoomState}
            height={canvasHeight}
          />
        )}
      </div>

      {/* ─── Status bar ──────────────────────────────────────────── */}
      <div style={styles.statusBar}>
        <span>
          {allLoaded ? (
            <span style={{ color: '#22c55e' }}>●</span>
          ) : (
            <span style={{ color: '#d4af37' }}>●</span>
          )}{' '}
          {loadedCount}/{columns.length} wells loaded
        </span>
        <span>|</span>
        <span>Depth: {zoomState[0].toFixed(0)}–{zoomState[1].toFixed(0)}m</span>
        {totalTopCount > 0 && (
          <>
            <span>|</span>
            <span style={{ color: '#d4af37' }}>Tops: {totalTopCount}</span>
          </>
        )}
        {cursorDepth != null && (
          <>
            <span>|</span>
            <span style={{ color: '#00d4aa' }}>
              Cursor: {cursorDepth.toFixed(1)}m
            </span>
          </>
        )}
        <div style={{ flex: 1 }} />
        <span style={{ color: '#d4af37', opacity: 0.5 }}>DITEMPA BUKAN DIBERI</span>
      </div>
    </div>
  );
};
