import React, { useCallback } from 'react';
import { Box, Globe, BarChart3, AlertTriangle, MapPin } from 'lucide-react';
import { useMcpTool } from '../hooks/useMcpTool';

interface BasinGeoJSON {
  type: string;
  features: Array<{
    type: string;
    geometry: { type: string; coordinates: number[][][] };
    properties: Record<string, unknown>;
  }>;
  metadata?: {
    bbox?: number[];
    maruah_flag?: {
      maruah_flag: string;
      territory_risk: string;
      intersected_basins: string[];
      floors_triggered: string[];
    };
    acrisk?: number;
    artifact_ref?: string;
    tool_name?: string;
    verdict?: string;
  };
}

interface MapSceneResult {
  primary_artifact?: {
    geojson?: BasinGeoJSON;
    bbox?: number[];
    mode?: string;
  };
  claim_tag?: string;
  governance_status?: string;
  acrisk?: number;
  artifact_ref?: string;
  tool_name?: string;
  verdict?: string;
}

const Badge: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = "emerald" }) => {
  const colors: Record<string, string> = {
    cyan: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
    emerald: "border-emerald-500/30 text-emerald-500 bg-emerald-500/10",
    purple: "border-purple-500/30 text-purple-400 bg-purple-500/10",
    red: "border-red-500/30 text-red-500 bg-red-500/10",
    amber: "border-amber-500/30 text-amber-400 bg-amber-500/10",
  };
  return (
    <span className={`px-1.5 py-0.5 text-[10px] font-mono border rounded uppercase tracking-wider ${colors[color]}`}>
      {children}
    </span>
  );
};

export const Domain3D: React.FC = () => {
  const basinTool = useMcpTool<{ bbox: number[]; mode: string }, MapSceneResult>('geox_map_context_scene');
  const basinResolveTool = useMcpTool<{ name: string }, { primary_artifact?: { bbox?: number[] } }>('geox_basin_resolve');

  const MALAY_BASIN_BBOX = [102.0, 4.0, 106.5, 8.5];

  const handleBasinSynthesis = useCallback(async () => {
    // Step 1: Resolve basin to get canonical bbox
    await basinResolveTool.call({ name: 'Malay Basin' });
    const bbox = basinResolveTool.data?.primary_artifact?.bbox ?? MALAY_BASIN_BBOX;
    // Step 2: Render basin map scene with GeoJSON
    await basinTool.call({ bbox, mode: 'render_geojson' });
  }, [basinTool, basinResolveTool]);

  const geojsonData = basinTool.data?.primary_artifact?.geojson;
  const mapMetadata = basinTool.data?.primary_artifact;
  const featureCount = geojsonData?.features?.length ?? 0;
  const maruahFlag = geojsonData?.metadata?.maruah_flag;
  const acrisk = basinTool.data?.acrisk ?? 0.3;
  const verdict = basinTool.data?.verdict ?? 'QUALIFY';
  const governanceStatus = basinTool.data?.governance_status ?? '';
  const claimTag = basinTool.data?.claim_tag ?? '';

  return (
    <div className="flex flex-col h-full gap-4 p-4">
      <div className="flex justify-between items-end mb-2 border-b border-gray-800 pb-2">
        <div>
          <h2 className="text-xl font-bold tracking-widest flex items-center gap-2">
            <Box className="w-5 h-5 text-purple-500" /> SOVEREIGN BASIN ENGINE
          </h2>
          <p className="text-xs text-gray-500 font-mono">▸ GEOX:MAP_CONTEXT_SCENE ▸ render_geojson</p>
        </div>
        <div className="flex gap-2">
          <Badge color="cyan">EARTH TRUE SCALE</Badge>
          <Badge color={acrisk <= 0.30 ? 'emerald' : acrisk <= 0.60 ? 'amber' : 'red'}>
            ACRisk: {acrisk.toFixed(2)}
          </Badge>
          <Badge color={basinTool.status === 'loading' ? 'amber' : 'purple'}>
            {basinTool.status === 'loading' ? 'FETCHING...' : 'ONLINE'}
          </Badge>
        </div>
      </div>

      <div className="flex-1 flex gap-4 overflow-hidden relative">
        <div className="flex-1 glass-panel relative overflow-hidden bg-[#050608]">
          {/* MARUAH overlay indicator */}
          {maruahFlag && (
            <div className={`absolute top-2 left-2 z-20 flex items-center gap-2 px-3 py-1.5 bg-black/80 border ${maruahFlag.maruah_flag === 'MARUAH_REQUIRED' ? 'border-amber-500/50 text-amber-400' : 'border-green-500/50 text-green-400'} text-[10px] font-mono shadow-lg backdrop-blur-md rounded-sm`}>
              <AlertTriangle className="w-3 h-3" />
              {maruahFlag.maruah_flag} — {maruahFlag.intersected_basins.join(', ')}
            </div>
          )}
          {/* ACRisk + Floors overlay */}
          {mapMetadata && (
            <div className="absolute top-2 right-2 z-20 flex flex-col gap-1 px-3 py-1.5 bg-black/80 border border-purple-500/30 text-purple-400 text-[10px] font-mono shadow-lg backdrop-blur-md rounded-sm">
              <span>ACRisk: {acrisk.toFixed(2)}</span>
              <span>Verdict: {verdict}</span>
              {maruahFlag?.floors_triggered && (
                <span>Floors: {maruahFlag.floors_triggered.join(', ')}</span>
              )}
              <span>Features: {featureCount}</span>
            </div>
          )}

          {/* Map placeholder — renders the basin data structure */}
          {!geojsonData && basinTool.status !== 'loading' && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <Globe className="w-16 h-16 text-purple-500/30 mx-auto mb-4" />
                <p className="text-sm text-gray-600 font-mono">GENERATE BASIN MAP</p>
                <p className="text-[10px] text-gray-700 font-mono mt-1">Click "Render Basin Map" to fetch Malay Basin GeoJSON from GEOX MCP</p>
              </div>
            </div>
          )}
          {basinTool.status === 'loading' && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
                <p className="text-sm text-purple-400 font-mono animate-pulse">FETCHING BASIN DATA VIA GEOX MCP...</p>
              </div>
            </div>
          )}
          {geojsonData && (
            <div className="absolute inset-0 overflow-auto p-4">
              {/* Visual GeoJSON representation */}
              <div className="space-y-2">
                {geojsonData.features.map((feature, i) => (
                  <div key={i} className="bg-black/60 border border-purple-500/20 rounded p-3 font-mono text-[11px]">
                    <div className="flex items-center gap-2 text-purple-400 mb-1">
                      <MapPin className="w-3 h-3" />
                      <span className="font-bold uppercase">{String(feature.properties.type)}</span>
                      <span className="text-gray-600">—</span>
                      <span className="text-gray-400">{String(feature.properties.label)}</span>
                    </div>
                    <div className="text-gray-500 ml-5">
                      <span>Geometry: {feature.geometry.type}</span>
                      <span className="ml-3">
                        Coords: {JSON.stringify(feature.geometry.coordinates).slice(0, 80)}...
                      </span>
                    </div>
                  </div>
                ))}
                {/* MARUAH zone overlay card */}
                {maruahFlag && maruahFlag.maruah_flag === 'MARUAH_REQUIRED' && (
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded p-3 font-mono text-[11px]">
                    <div className="flex items-center gap-2 text-amber-400 mb-1">
                      <AlertTriangle className="w-3 h-3" />
                      <span className="font-bold uppercase">MARUAH ZONE</span>
                    </div>
                    <p className="text-amber-300/70 ml-5">
                      Territory: {maruahFlag.intersected_basins.join(', ')} · 
                      Risk: {maruahFlag.territory_risk} ·
                      Action: F6 MARUAH — FPIC required before proceeding
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="w-64 glass-panel p-4 flex flex-col gap-4 z-20">
          <div className="text-xs font-mono text-gray-500 border-b border-gray-800 pb-2 flex justify-between items-center">
            BASIN INTELLIGENCE <Globe className="w-4 h-4 text-purple-500" />
          </div>
          <button 
            onClick={handleBasinSynthesis} 
            disabled={basinTool.status === 'loading' || basinResolveTool.status === 'loading'} 
            className="w-full py-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 text-[10px] font-mono uppercase hover:bg-purple-500/20 transition-colors flex justify-center items-center gap-2"
          >
            {(basinTool.status === 'loading' || basinResolveTool.status === 'loading')
              ? 'FETCHING...' 
              : '🗺️ RENDER BASIN MAP'}
          </button>

          {/* Governance details panel */}
          {basinTool.data && (
            <div className="mt-2 space-y-2">
              <div className="p-2 border border-purple-500/20 rounded font-mono text-[10px]">
                <div className="text-purple-400 font-bold mb-1 uppercase tracking-wider">Governance</div>
                <div className="text-gray-500 space-y-0.5">
                  <div>Status: <span className="text-gray-300">{governanceStatus}</span></div>
                  <div>Claim: <span className="text-gray-300">{claimTag}</span></div>
                  <div>ACRisk: <span className={acrisk <= 0.30 ? 'text-green-400' : acrisk <= 0.60 ? 'text-amber-400' : 'text-red-400'}>{acrisk.toFixed(2)}</span></div>
                  <div>Features: <span className="text-gray-300">{featureCount}</span></div>
                </div>
              </div>

              <div className="p-2 border border-purple-500/20 rounded font-mono text-[10px]">
                <div className="text-purple-400 font-bold mb-1 uppercase tracking-wider">Provenance</div>
                <div className="text-gray-500 space-y-0.5">
                  <div>Tool: <span className="text-gray-300">geox_map_context_scene</span></div>
                  <div>Mode: <span className="text-gray-300">render_geojson</span></div>
                  <div>Bbox: <span className="text-gray-300">{JSON.stringify(mapMetadata?.bbox ?? MALAY_BASIN_BBOX)}</span></div>
                </div>
              </div>
            </div>
          )}

          {basinTool.error && (
            <div className="mt-2 p-3 border border-red-500/30 bg-red-500/5 text-red-200 font-mono text-[11px] rounded">
              <div className="flex items-center gap-2 text-red-400 text-[9px] mb-1">
                <AlertTriangle size={12} /> ERROR
              </div>
              <pre className="whitespace-pre-wrap">{basinTool.error}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Domain3D;
