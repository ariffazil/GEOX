/**
 * RiskDashboard — Prospect Risk Gauges with MCP-wired Prospect Evaluation
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Wires useMcpTool to geox_prospect (mode=evaluate):
 *  - Volumetrics (STOIIP / GIIP)
 *  - Probability of Success (POS)
 *  - Expected Value of Information (EVOI)
 *  - Risk matrix for reservoir / seal / trap / charge / timing
 *
 * Renders:
 *  - Risk gauge dials (canvas-based)
 *  - POS pie chart
 *  - EVOI bar
 *  - Risk matrix heatmap
 *  - Falsification gate status
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import {
  Target, Shield, TrendingUp, PieChart, AlertTriangle,
  CheckCircle, RefreshCw, Loader2, Activity, Gauge
} from 'lucide-react';
import { useMcpTool } from '../../hooks/useMcpTool';
import { useGEOXStore } from '../../store/geoxStore';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface ProspectResult {
  prospect_id?: string;
  verdict?: string;
  gross_rock_volume?: number;
  net_to_gross?: number;
  porosity?: number;
  oil_saturation?: number;
  formation_volume_factor?: number;
  recovery_factor?: number;
  stoip_mmstb?: number;
  pos_geological?: number;
  pos_charge?: number;
  pos_trap?: number;
  pos_seal?: number;
  pos_reservoir?: number;
  pos_timing?: number;
  pos_overall?: number;
  evoi_usd?: number;
  well_cost_usd?: number;
  p50_value_usd?: number;
  risk_matrix?: Record<string, string>;
  missing_constraints?: string[];
  receipt_hash?: string;
}

interface RiskGaugeProps {
  label: string;
  value: number;
  color: string;
  max: number;
  unit: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Risk Gauge Canvas
// ─────────────────────────────────────────────────────────────────────────────

const RiskGauge: React.FC<RiskGaugeProps> = ({ label, value, color, max, unit }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const size = 100;

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
    const cx = size / 2; const cy = size / 2 + 5; const r = 35;

    // Background arc
    ctx.beginPath(); ctx.arc(cx, cy, r, Math.PI * 0.75, Math.PI * 2.25);
    ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 8; ctx.stroke();

    // Value arc
    const ratio = Math.min(value / max, 1);
    const startAngle = Math.PI * 0.75;
    const endAngle = startAngle + ratio * Math.PI * 1.5;
    ctx.beginPath(); ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.strokeStyle = color; ctx.lineWidth = 8; ctx.stroke();

    // Value text
    ctx.fillStyle = '#e2e8f0'; ctx.font = 'bold 16px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(value > 0 ? value.toFixed(value >= 10 ? 0 : 1) : '—', cx, cy);
    ctx.font = '8px sans-serif'; ctx.fillStyle = '#94a3b8';
    ctx.fillText(unit, cx, cy + 14);
    ctx.font = '9px sans-serif'; ctx.fillStyle = '#64748b';
    ctx.fillText(label, cx, size - 4);
  }, [value, color, max, unit, label]);

  return <canvas ref={canvasRef} style={{ width: `${size}px`, height: `${size}px` }} />;
};

// ─────────────────────────────────────────────────────────────────────────────
// POS Bar
// ─────────────────────────────────────────────────────────────────────────────

const POSBar: React.FC<{
  components: Array<{ name: string; value: number; color: string }>;
}> = ({ components }) => (
  <div className="space-y-2">
    <h4 className="text-xs font-bold text-slate-500 uppercase">Probability of Success (POS)</h4>
    {components.map((c) => (
      <div key={c.name} className="flex items-center gap-2">
        <span className="text-xs text-slate-400 w-20">{c.name}</span>
        <div className="flex-1 h-2.5 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-500"
            style={{ width: `${c.value * 100}%`, backgroundColor: c.color }} />
        </div>
        <span className="text-xs font-mono text-slate-300 w-10 text-right">{(c.value * 100).toFixed(0)}%</span>
      </div>
    ))}
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Risk Matrix Heatmap
// ─────────────────────────────────────────────────────────────────────────────

const RiskHeatmap: React.FC<{
  matrix: Record<string, string>;
}> = ({ matrix }) => {
  const entries = Object.entries(matrix);
  if (entries.length === 0) return null;

  const riskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return '#22c55e';
      case 'moderate': return '#3b82f6';
      case 'high': return '#f59e0b';
      case 'critical': case 'very high': return '#ef4444';
      default: return '#64748b';
    }
  };

  return (
    <div>
      <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Risk Matrix</h4>
      <div className="grid grid-cols-2 gap-1.5">
        {entries.map(([key, level]) => (
          <div key={key} className="bg-slate-900 border border-slate-800 rounded p-2 flex justify-between items-center">
            <span className="text-xs text-slate-400 capitalize">{key}</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded" style={{
              backgroundColor: riskColor(level) + '20',
              color: riskColor(level),
            }}>{level}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export const RiskDashboard: React.FC = () => {
  const { selectedProspect, updateFloorStatus } = useGEOXStore();
  const [lastReceipt, setLastReceipt] = useState<string | null>(null);

  const prospectTool = useMcpTool<{
    mode: string;
    prospect_ref: string;
    evidence_refs: string[];
  }, ProspectResult>('geox_prospect');

  const computeProspect = useCallback(async () => {
    try {
      updateFloorStatus('F3', 'amber', 'Evaluating prospect risk via MCP…');
      const result = await prospectTool.call({
        mode: 'evaluate',
        prospect_ref: selectedProspect ?? 'PROSPECT_ALPHA',
        evidence_refs: [],
      });
      updateFloorStatus('F3', 'green', `Prospect evaluated: ${result.verdict || 'SEAL'}`);
      if (result.receipt_hash) setLastReceipt(result.receipt_hash);
    } catch (err) {
      updateFloorStatus('F3', 'red', `Prospect evaluation failed: ${String(err)}`);
    }
  }, [selectedProspect, prospectTool, updateFloorStatus]);

  useEffect(() => { computeProspect(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const data = prospectTool.data;
  const isLoading = prospectTool.status === 'loading';
  const hasError = prospectTool.status === 'error';

  const posComponents = [
    { name: 'Reservoir', value: data?.pos_reservoir ?? 0, color: '#22c55e' },
    { name: 'Seal', value: data?.pos_seal ?? 0, color: '#3b82f6' },
    { name: 'Trap', value: data?.pos_trap ?? 0, color: '#f59e0b' },
    { name: 'Charge', value: data?.pos_charge ?? 0, color: '#ef4444' },
    { name: 'Timing', value: data?.pos_timing ?? 0, color: '#a855f7' },
    { name: 'Overall', value: data?.pos_overall ?? 0, color: '#06b6d4' },
  ];

  const riskMatrix = data?.risk_matrix ?? {};

  return (
    <div className="h-full flex flex-col bg-slate-950 text-slate-200 overflow-y-auto">
      {/* Toolbar */}
      <div className="h-12 border-b border-slate-800 bg-slate-900/50 flex items-center px-4 gap-4 flex-shrink-0">
        <Target className="w-5 h-5 text-red-500" />
        <h2 className="text-sm font-black tracking-widest uppercase italic">Risk Dashboard</h2>

        <div className="flex-1" />

        <button
          onClick={computeProspect}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Evaluating…' : 'Run Evaluation'}
        </button>

        <span className="text-[10px] font-mono text-slate-500">
          Prospect: {selectedProspect ?? 'PROSPECT_ALPHA'}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 space-y-6">
        {/* Status bar */}
        {isLoading && (
          <div className="bg-amber-900/20 border border-amber-900/50 rounded-lg p-3 flex items-center gap-2 text-amber-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Evaluating prospect via MCP: geox_prospect (mode=evaluate)…
          </div>
        )}
        {hasError && (
          <div className="bg-red-900/20 border border-red-900/50 rounded-lg p-3 flex items-center gap-2 text-red-400 text-sm">
            <AlertTriangle className="w-4 h-4" />
            {prospectTool.error}
          </div>
        )}
        {prospectTool.status === 'success' && lastReceipt && (
          <div className="bg-green-900/20 border border-green-900/50 rounded-lg p-3 flex items-center gap-2 text-green-400 text-sm">
            <CheckCircle className="w-4 h-4" />
            Evaluation complete · Receipt: {lastReceipt.slice(0, 14)}…
          </div>
        )}

        {/* Gauges Row */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col items-center">
            <RiskGauge label="POS Overall" value={data?.pos_overall ?? 0} color="#06b6d4" max={1} unit="prob" />
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col items-center">
            <RiskGauge label="STOIIP" value={data?.stoip_mmstb ?? 0} color="#f59e0b" max={data?.stoip_mmstb ? data.stoip_mmstb * 2 : 500} unit="MMstb" />
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col items-center">
            <RiskGauge label="EVOI" value={(data?.evoi_usd ?? 0) / 1e6} color="#22c55e" max={100} unit="$M" />
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col items-center justify-center text-center">
            <Shield className="w-8 h-8 mb-2" style={{
              color: data?.verdict === 'SEAL' ? '#22c55e'
                : data?.verdict === 'PARTIAL' ? '#3b82f6'
                : data?.verdict === 'HOLD' ? '#f59e0b'
                : data?.verdict === 'VOID' ? '#ef4444'
                : '#64748b'
            }} />
            <span className="text-lg font-black uppercase">{data?.verdict ?? '—'}</span>
            <span className="text-[10px] text-slate-500">Verdict</span>
          </div>
        </div>

        {/* POS Bars + Risk Matrix */}
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            <POSBar components={posComponents} />
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
            {Object.keys(riskMatrix).length > 0 ? (
              <RiskHeatmap matrix={riskMatrix} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-xs text-slate-600">Risk matrix not yet evaluated. Run evaluation.</p>
              </div>
            )}
          </div>
        </div>

        {/* Economics */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
          <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Economics Summary</h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="text-[10px] text-slate-500 uppercase">Well Cost</span>
              <div className="text-lg font-mono font-bold text-slate-200">
                ${data?.well_cost_usd != null ? `${(data.well_cost_usd / 1e6).toFixed(1)}M` : '—'}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase">P50 Value</span>
              <div className="text-lg font-mono font-bold text-slate-200">
                ${data?.p50_value_usd != null ? `${(data.p50_value_usd / 1e6).toFixed(1)}M` : '—'}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase">EVOI</span>
              <div className="text-lg font-mono font-bold text-green-400">
                ${data?.evoi_usd != null ? `${(data.evoi_usd / 1e6).toFixed(1)}M` : '—'}
              </div>
            </div>
          </div>

          {data?.recovery_factor != null && (
            <div className="mt-3 pt-3 border-t border-slate-800 grid grid-cols-3 gap-4">
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Net/Gross</span>
                <div className="font-mono text-sm text-slate-300">{data?.net_to_gross?.toFixed(2) ?? '—'}</div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Porosity</span>
                <div className="font-mono text-sm text-slate-300">{data?.porosity != null ? `${(data.porosity * 100).toFixed(1)}%` : '—'}</div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Recovery Factor</span>
                <div className="font-mono text-sm text-slate-300">{data?.recovery_factor != null ? `${(data.recovery_factor * 100).toFixed(1)}%` : '—'}</div>
              </div>
            </div>
          )}
        </div>

        {/* Missing constraints */}
        {data?.missing_constraints && data.missing_constraints.length > 0 && (
          <div className="bg-red-900/20 border border-red-900/50 rounded-lg p-4">
            <h4 className="text-xs font-bold text-red-400 uppercase mb-2 flex items-center gap-2">
              <AlertTriangle className="w-3 h-3" /> Missing Constraints
            </h4>
            <ul className="space-y-1">
              {data.missing_constraints.map((c, i) => (
                <li key={i} className="text-xs text-red-300/80 font-mono">• {c}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="h-8 bg-slate-950 border-t border-slate-800 flex items-center px-4 gap-4 text-[10px] uppercase font-black text-slate-600 flex-shrink-0">
        <span>MCP: geox_prospect</span>
        <span>|</span>
        <span>Prospect: {selectedProspect ?? 'PROSPECT_ALPHA'}</span>
        <span>|</span>
        <span>Gate: F3 TRI-WITNESS · F1 AMANAH</span>
        <div className="flex-1" />
        <span className="text-amber-500/70">DITEMPA BUKAN DIBERI</span>
      </div>
    </div>
  );
};

export default RiskDashboard;
