/**
 * EarthVisionPanel — Layered Earth Observation Intelligence
 * ═══════════════════════════════════════════════════════════════════════════════
 * DITEMPA BUKAN DIBERI
 *
 * Multi-layer EO panel for GEOX:
 * - 2D map (MapLibre GL JS) with layered EO visualization
 * - STAC API search for satellite imagery
 * - DEM hillshade / terrain
 * - Macrostrat geological context overlay
 * - Layer governance tags (OBSERVED / DERIVED / INTERPRETED / PROCESS_HYPOTHESIS)
 * - ACRisk traffic-light overlay per layer
 *
 * References:
 * - STAC: https://stacspec.org/ | Earth Search: https://earth-search.aws.element84.com/v1/
 * - MapLibre raster: https://maplibre.org/maplibre-gl-js/docs/API/classes/RasterTileSource/
 * - Macrostrat API: https://dev.macrostrat.org/api/v2/
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  Layers, Search, Satellite, MapPin, AlertTriangle, CheckCircle2,
  ChevronDown, ChevronUp, Cloud, Eye, EyeOff, RefreshCw, X,
  Globe, Mountain, Map as MapIcon, Info, ExternalLink, Gauge
} from 'lucide-react';

// ─── Governance Types ──────────────────────────────────────────────────────────

export type GovernanceTag = 'OBSERVED' | 'DERIVED' | 'INTERPRETED_LOCAL' | 'PROCESS_HYPOTHESIS';

export type ACRiskLevel = 'SEAL' | 'QUALIFY' | 'PARTIAL' | 'HOLD' | 'VOID';

export interface EOLayer {
  id: string;
  name: string;
  type: 'raster' | 'raster-dem' | 'geojson' | 'wms';
  source?: string;
  tiles?: string[];
  url?: string;
  data?: string;
  attribution: string;
  governanceTag: GovernanceTag;
  acriskMax: number; // 0.0–1.0
  visible: boolean;
  opacity: number;
  legendColor?: string;
  description: string;
}

// ─── ACRisk helpers ────────────────────────────────────────────────────────────

function acRiskLevel(acriskMax: number): ACRiskLevel {
  if (acriskMax <= 0.30) return 'SEAL';
  if (acriskMax <= 0.50) return 'QUALIFY';
  if (acriskMax <= 0.60) return 'PARTIAL';
  if (acriskMax <= 0.75) return 'HOLD';
  return 'VOID';
}

function acRiskColor(level: ACRiskLevel): string {
  switch (level) {
    case 'SEAL': return 'text-green-400 bg-green-500/20 border-green-500/50';
    case 'QUALIFY': return 'text-blue-400 bg-blue-500/20 border-blue-500/50';
    case 'PARTIAL': return 'text-amber-400 bg-amber-500/20 border-amber-500/50';
    case 'HOLD': return 'text-red-400 bg-red-500/20 border-red-500/50 animate-pulse';
    case 'VOID': return 'text-slate-400 bg-slate-500/20 border-slate-500/50';
  }
}

function acRiskBg(level: ACRiskLevel): string {
  switch (level) {
    case 'SEAL': return 'bg-green-500';
    case 'QUALIFY': return 'bg-blue-500';
    case 'PARTIAL': return 'bg-amber-500';
    case 'HOLD': return 'bg-red-500';
    case 'VOID': return 'bg-slate-500';
  }
}

// ─── Layer Registry ───────────────────────────────────────────────────────────

const EO_LAYERS: EOLayer[] = [
  {
    id: 'osm-basemap',
    name: 'OpenStreetMap',
    type: 'raster',
    tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
    attribution: '© OpenStreetMap Contributors',
    governanceTag: 'OBSERVED',
    acriskMax: 0.10,
    visible: true,
    opacity: 1.0,
    description: 'Base vector map — roads, rivers, boundaries'
  },
  {
    id: 'google-satellite',
    name: 'Google Satellite',
    type: 'raster',
    tiles: [
      'https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
      'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
      'https://mt2.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
      'https://mt3.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    ],
    attribution: '© Google',
    governanceTag: 'OBSERVED',
    acriskMax: 0.20,
    visible: false,
    opacity: 1.0,
    description: 'High-resolution satellite imagery (verify ToS for commercial use)'
  },
  {
    id: 'esri-satellite',
    name: 'ESRI World Imagery',
    type: 'raster',
    tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
    attribution: '© ESRI',
    governanceTag: 'OBSERVED',
    acriskMax: 0.20,
    visible: false,
    opacity: 1.0,
    description: 'ESRI satellite imagery — free for non-commercial use'
  },
  {
    id: 'dem-hillshade',
    name: 'DEM Hillshade (SRTM)',
    type: 'raster-dem',
    url: 'https://demotiles.maplibre.org/terrain-tiles/tiles.json',
    attribution: 'MapLibre Terrain Tiles / SRTM',
    governanceTag: 'OBSERVED',
    acriskMax: 0.20,
    visible: false,
    opacity: 0.7,
    description: 'Shaded relief from SRTM 30m DEM — elevation context for structure'
  },
  {
    id: 'sentinel-2',
    name: 'Sentinel-2 (STAC)',
    type: 'raster',
    tiles: [], // Populated dynamically from STAC search
    attribution: 'ESA Sentinel-2 via STAC',
    governanceTag: 'OBSERVED',
    acriskMax: 0.30,
    visible: false,
    opacity: 0.8,
    legendColor: 'rgb(0, 100, 0)',
    description: 'Sentinel-2 multispectral — requires STAC search to activate tiles'
  },
  {
    id: 'macrostrat-geology',
    name: 'Macrostrat Geology',
    type: 'geojson',
    data: '',
    attribution: '© Macrostrat / USGS',
    governanceTag: 'PROCESS_HYPOTHESIS',
    acriskMax: 0.55,
    visible: false,
    opacity: 0.6,
    legendColor: '#8B4513',
    description: 'Surface geology units from Macrostrat — PROCESS_HYPOTHESIS not hard truth'
  },
  {
    id: 'opentopomap',
    name: 'OpenTopoMap',
    type: 'raster',
    tiles: ['https://tile.opentopomap.org/{z}/{x}/{y}.png'],
    attribution: '© OpenTopoMap contributors',
    governanceTag: 'OBSERVED',
    acriskMax: 0.15,
    visible: false,
    opacity: 1.0,
    description: 'Topographic map with contours — good for structural interpretation'
  },
];

// ─── STAC Search ─────────────────────────────────────────────────────────────

interface STACSearchResult {
  id: string;
  date: string;
  cloud_cover: number;
  bbox: [number, number, number, number];
  thumbnail: string;
  assets: Record<string, { href: string; type: string }>;
}

async function searchSTAC(
  bbox: [number, number, number, number],
  collection: string = 'sentinel-2-l2a',
  maxCloud: number = 20
): Promise<STACSearchResult[]> {
  try {
    const url = new URL('https://earth-search.aws.element84.com/v1/search');
    url.searchParams.set('bbox', bbox.join(','));
    url.searchParams.set('collections', collection);
    url.searchParams.set('limit', '10');
    url.searchParams.set('datetime', '2023-01-01/2026-01-01');
    if (maxCloud < 100) {
      url.searchParams.set('query', `eo:cloud_cover<${maxCloud}`);
    }
    const res = await fetch(url.toString());
    if (!res.ok) return [];
    const data = await res.json();
    return (data.features || []).map((f: any) => ({
      id: f.id,
      date: f.properties.datetime?.split('T')[0] || 'unknown',
      cloud_cover: f.properties['eo:cloud_cover'] ?? 99,
      bbox: f.bbox,
      thumbnail: f.assets?.thumbnail?.href || f.assets?.preview?.href || '',
      assets: f.assets || {},
    }));
  } catch {
    return [];
  }
}

// ─── ACRisk Legend ───────────────────────────────────────────────────────────

const ACRiskLegend: React.FC = () => (
  <div className="flex items-center gap-1 text-[9px] font-mono">
    {(['SEAL', 'QUALIFY', 'PARTIAL', 'HOLD'] as ACRiskLevel[]).map((level) => (
      <div key={level} className="flex items-center gap-0.5">
        <div className={`w-2 h-2 rounded-full ${acRiskBg(level)}`} />
        <span className="text-slate-400">{level}</span>
      </div>
    ))}
  </div>
);

// ─── Layer Control Row ────────────────────────────────────────────────────────

const LayerRow: React.FC<{
  layer: EOLayer;
  onToggle: (id: string) => void;
  onOpacity: (id: string, opacity: number) => void;
}> = ({ layer, onToggle, onOpacity }) => {
  const level = acRiskLevel(layer.acriskMax);
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-slate-700/50 rounded-lg overflow-hidden">
      <div
        className={`flex items-center gap-2 px-2 py-1.5 cursor-pointer hover:bg-slate-800/50 ${layer.visible ? 'bg-slate-800/30' : ''}`}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Visibility toggle */}
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(layer.id); }}
          className="flex-shrink-0"
        >
          {layer.visible
            ? <Eye className="w-3.5 h-3.5 text-blue-400" />
            : <EyeOff className="w-3.5 h-3.5 text-slate-600" />
          }
        </button>

        {/* Layer name + governance tag */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className={`text-[10px] font-bold px-1 py-0.5 rounded border ${acRiskColor(level)}`}>
              {level}
            </span>
            <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${layer.governanceTag === 'OBSERVED' ? 'text-green-400 bg-green-500/10 border-green-500/30' : layer.governanceTag === 'PROCESS_HYPOTHESIS' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' : 'text-slate-400 bg-slate-500/10 border-slate-500/30'}`}>
              {layer.governanceTag}
            </span>
          </div>
          <div className="text-[10px] text-slate-300 truncate mt-0.5">{layer.name}</div>
        </div>

        {/* Layer color swatch */}
        {layer.legendColor && (
          <div
            className="w-3 h-3 rounded border border-slate-600 flex-shrink-0"
            style={{ backgroundColor: layer.legendColor }}
          />
        )}

        {expanded ? <ChevronUp className="w-3 h-3 text-slate-500" /> : <ChevronDown className="w-3 h-3 text-slate-500" />}
      </div>

      {expanded && (
        <div className="px-2 py-1.5 bg-slate-900/50 border-t border-slate-700/30 space-y-1.5">
          <p className="text-[9px] text-slate-500 leading-relaxed">{layer.description}</p>
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-slate-500 font-mono">Opacity</span>
            <input
              type="range"
              min={0.1}
              max={1.0}
              step={0.1}
              value={layer.opacity}
              onChange={(e) => onOpacity(layer.id, Number(e.target.value))}
              className="flex-1"
              onClick={(e) => e.stopPropagation()}
            />
            <span className="text-[9px] font-mono text-slate-400 w-8 text-right">{layer.opacity.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-2 text-[9px] text-slate-500">
            <span>ACRisk ≤ {layer.acriskMax.toFixed(2)}</span>
            <span>·</span>
            <span>{layer.attribution}</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── STAC Search Panel ─────────────────────────────────────────────────────────

const STACSearchPanel: React.FC<{
  bbox: [number, number, number, number] | null;
  onActivate: (tiles: string[], name: string) => void;
}> = ({ bbox, onActivate }) => {
  const [query, setQuery] = useState({ collection: 'sentinel-2-l2a', maxCloud: 20 });
  const [results, setResults] = useState<STACSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const handleSearch = useCallback(async () => {
    if (!bbox) return;
    setLoading(true);
    const items = await searchSTAC(bbox, query.collection, query.maxCloud);
    setResults(items);
    setLoading(false);
  }, [bbox, query.collection, query.maxCloud]);

  const handleActivate = (item: STACSearchResult) => {
    // Try to extract a tile URL from the STAC item
    // Sentinel-2 L2A assets often have a tile URL or COG
    const visualAsset = item.assets?.visual;
    const tcisAsset = item.assets?.tcis;
    const assetHref = visualAsset?.href || tcisAsset?.href || '';

    if (assetHref) {
      // Convert to tile URL pattern if possible
      // For now, activate with the raw asset URL
      onActivate([assetHref], `${item.id} (${item.date})`);
      setSelected(item.id);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Cloud className="w-3 h-3 text-slate-500" />
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">STAC Search</span>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        <select
          value={query.collection}
          onChange={(e) => setQuery(q => ({ ...q, collection: e.target.value }))}
          className="geox-input text-[10px] py-1"
        >
          <option value="sentinel-2-l2a">Sentinel-2 L2A</option>
          <option value="sentinel-1-grd">Sentinel-1 SAR</option>
          <option value="landsat-c2-l2">Landsat C2 L2</option>
        </select>
        <div className="flex items-center gap-1">
          <span className="text-[9px] text-slate-500">CC≤</span>
          <input
            type="number"
            min={5}
            max={100}
            value={query.maxCloud}
            onChange={(e) => setQuery(q => ({ ...q, maxCloud: Number(e.target.value) }))}
            className="geox-input text-[10px] py-1 w-12"
          />
          <span className="text-[9px] text-slate-500">%</span>
        </div>
      </div>

      <button
        onClick={handleSearch}
        disabled={!bbox || loading}
        className="geox-btn geox-btn--ghost text-[10px] w-full py-1.5 flex items-center justify-center gap-1"
      >
        {loading
          ? <><RefreshCw className="w-3 h-3 animate-spin" /> Searching...</>
          : <><Search className="w-3 h-3" /> Search {bbox ? 'AOI' : '(pan map first)'}</>
        }
      </button>

      {results.length > 0 && (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {results.map((item) => (
            <div
              key={item.id}
              onClick={() => handleActivate(item)}
              className={`p-1.5 rounded border cursor-pointer text-[9px] ${selected === item.id ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-600 bg-slate-800/30'}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-slate-300 truncate">{item.id.split('—')[0]}</span>
                <span className={`font-mono flex-shrink-0 ml-1 ${item.cloud_cover <= 10 ? 'text-green-400' : item.cloud_cover <= 30 ? 'text-amber-400' : 'text-red-400'}`}>
                  {item.cloud_cover}%
                </span>
              </div>
              <div className="text-slate-500 font-mono mt-0.5">{item.date}</div>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && (
        <p className="text-[9px] text-slate-600 text-center py-2">
          Search to discover EO scenes for current AOI
        </p>
      )}
    </div>
  );
};

// ─── Coordinate HUD ────────────────────────────────────────────────────────────

const CoordHUD: React.FC<{ map: maplibregl.Map | null }> = ({ map }) => {
  const [coords, setCoords] = useState<{ lat: number; lon: number; zoom: number } | null>(null);

  useEffect(() => {
    if (!map) return;
    const update = () => {
      const c = map.getCenter();
      setCoords({ lat: c.lat, lon: c.lng, zoom: map.getZoom() });
    };
    map.on('move', update);
    update();
    return () => { map.off('move', update); };
  }, [map]);

  if (!coords) return null;

  return (
    <div className="absolute bottom-4 left-4 z-10 bg-slate-900/85 backdrop-blur px-3 py-1.5 rounded border border-slate-700 font-mono text-[10px] text-slate-300 flex gap-3">
      <span>LAT: {coords.lat.toFixed(4)}</span>
      <span>LON: {coords.lon.toFixed(4)}</span>
      <span>Z: {coords.zoom.toFixed(1)}</span>
      <span className="text-slate-600">WGS84</span>
    </div>
  );
};

// ─── Main EarthVisionPanel ─────────────────────────────────────────────────────

export const EarthVisionPanel: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [layers, setLayers] = useState<EOLayer[]>(EO_LAYERS);
  const [mapCenter] = useState({ lng: 114.2, lat: 4.5, zoom: 6 });
  const [activeBaseLayer, setActiveBaseLayer] = useState<string>('osm-basemap');
  const [bbox, setBbox] = useState<[number, number, number, number] | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Initialize MapLibre map
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8 as const,
        sources: {
          osm: {
            type: 'raster' as const,
            tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap Contributors',
          },
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster' as const,
            source: 'osm',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [mapCenter.lng, mapCenter.lat],
      zoom: mapCenter.zoom,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.current.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right');

    map.current.on('load', () => {
      if (!map.current) return;
      setMapReady(true);
      const b = map.current.getBounds();
      setBbox([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
    });

    map.current.on('move', () => {
      if (!map.current) return;
      const b = map.current.getBounds();
      setBbox([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  // Sync layer visibility with MapLibre sources
  useEffect(() => {
    if (!map.current || !mapReady) return;

    layers.forEach((layer) => {
      const sourceId = `source-${layer.id}`;
      const hasSource = !!map.current?.getSource(sourceId);

      if (layer.visible && !hasSource) {
        // Add source if visible and not yet added
        if (layer.type === 'raster' && layer.tiles && layer.tiles.length > 0) {
          try {
            map.current?.addSource(sourceId, {
              type: 'raster',
              tiles: layer.tiles,
              tileSize: 256,
              attribution: layer.attribution,
            });
            map.current?.addLayer({
              id: `layer-${layer.id}`,
              type: 'raster',
              source: sourceId,
              paint: { 'raster-opacity': layer.opacity },
            });
          } catch {
            // Source may already exist or be invalid
          }
        } else if (layer.type === 'raster-dem' && layer.url) {
          try {
            map.current?.addSource(sourceId, {
              type: 'raster-dem',
              url: layer.url,
              tileSize: 256,
            });
            map.current?.addLayer({
              id: `layer-${layer.id}`,
              type: 'hillshade',
              source: sourceId,
              paint: { 'hillshade-shadow-color': '#000', 'hillshade-illumination-anchor': 'map' },
            });
          } catch {
            // Ignore
          }
        } else if (layer.type === 'geojson' && layer.data) {
          fetch(layer.data)
            .then(r => r.json())
            .then(geojson => {
              if (map.current?.getSource(sourceId)) return;
              map.current?.addSource(sourceId, { type: 'geojson', data: geojson });
              map.current?.addLayer({
                id: `layer-${layer.id}`,
                type: 'fill',
                source: sourceId,
                paint: {
                  'fill-color': '#8B4513',
                  'fill-opacity': layer.opacity * 0.5,
                },
              });
              map.current?.addLayer({
                id: `layer-${layer.id}-outline`,
                type: 'line',
                source: sourceId,
                paint: {
                  'line-color': '#A0522D',
                  'line-width': 1,
                },
              });
            })
            .catch(() => {});
        }
      } else if (!layer.visible && hasSource) {
        // Remove source if hidden
        try {
          if (map.current?.getLayer(`layer-${layer.id}`)) map.current?.removeLayer(`layer-${layer.id}`);
          if (map.current?.getLayer(`layer-${layer.id}-outline`)) map.current?.removeLayer(`layer-${layer.id}-outline`);
          if (map.current?.getSource(sourceId)) map.current?.removeSource(sourceId);
        } catch {
          // Ignore
        }
      } else if (layer.visible && hasSource) {
        // Update opacity
        try {
          if (layer.type === 'raster' || layer.type === 'geojson') {
            map.current?.setPaintProperty(`layer-${layer.id}`, 'raster-opacity', layer.opacity);
            if (layer.type === 'geojson') {
              map.current?.setPaintProperty(`layer-${layer.id}`, 'fill-opacity', layer.opacity * 0.5);
            }
          }
        } catch {
          // Ignore
        }
      }
    });
  }, [layers, mapReady]);

  // Toggle base layer (only one at a time for raster basemaps)
  const handleToggleBase = (id: string) => {
    const target = layers.find(l => l.id === id);
    if (!target) return;

    if (['osm-basemap', 'google-satellite', 'esri-satellite', 'opentopomap'].includes(id)) {
      // Switch base layer
      setActiveBaseLayer(id);
      if (map.current) {
        // Remove all basemap sources and add the new one
        ['osm-basemap', 'google-satellite', 'esri-satellite', 'opentopomap'].forEach(baseId => {
          const sourceId = `source-${baseId}`;
          if (map.current?.getLayer(`layer-${baseId}`)) map.current?.removeLayer(`layer-${baseId}`);
          if (map.current?.getSource(sourceId)) map.current?.removeSource(sourceId);
        });
        // Add new base
        const newBase = layers.find(l => l.id === id)!;
        if (newBase.tiles && newBase.tiles.length > 0) {
          map.current?.addSource(`source-${id}`, { type: 'raster', tiles: newBase.tiles, tileSize: 256, attribution: newBase.attribution });
          map.current?.addLayer({ id: `layer-${id}`, type: 'raster', source: `source-${id}` });
        }
      }
    } else {
      // Toggle overlay layer
      setLayers(prev => prev.map(l => l.id === id ? { ...l, visible: !l.visible } : l));
    }
  };

  const handleToggleOverlay = (id: string) => {
    setLayers(prev => prev.map(l => l.id === id ? { ...l, visible: !l.visible } : l));
  };

  const handleOpacity = (id: string, opacity: number) => {
    setLayers(prev => prev.map(l => l.id === id ? { ...l, opacity } : l));
  };

  const handleSTACActivate = (tiles: string[], name: string) => {
    // Add Sentinel-2 layer as overlay
    const s2Layer: EOLayer = {
      id: 'sentinel-2-active',
      name: `Sentinel-2: ${name}`,
      type: 'raster',
      tiles,
      attribution: 'ESA Sentinel-2',
      governanceTag: 'OBSERVED',
      acriskMax: 0.30,
      visible: true,
      opacity: 0.8,
      legendColor: 'rgb(34, 197, 94)',
      description: 'Active Sentinel-2 scene from STAC search'
    };
    setLayers(prev => {
      const filtered = prev.filter(l => l.id !== 'sentinel-2-active');
      return [...filtered, s2Layer];
    });
  };

  const handleMacrostratToggle = () => {
    if (!map.current) return;
    const bbox = map.current.getBounds();
    const lat = bbox.getCenter().lat;
    const lng = bbox.getCenter().lng;
    const buffer = Math.max(bbox.getEast() - bbox.getWest(), bbox.getNorth() - bbox.getSouth()) / 2;
    const url = `https://dev.macrostrat.org/api/v2/units/geojson?lat=${lat}&lng=${lng}&buffer=${buffer}`;

    const macroLayer: EOLayer = {
      id: 'macrostrat-geology',
      name: 'Macrostrat Geology',
      type: 'geojson',
      data: url,
      attribution: '© Macrostrat / USGS',
      governanceTag: 'PROCESS_HYPOTHESIS',
      acriskMax: 0.55,
      visible: true,
      opacity: 0.6,
      legendColor: '#8B4513',
      description: 'Surface geology units — PROCESS_HYPOTHESIS not hard truth'
    };

    // Remove existing if any
    if (map.current.getLayer('layer-macrostrat-geology')) map.current.removeLayer('layer-macrostrat-geology');
    if (map.current.getLayer('layer-macrostrat-geology-outline')) map.current.removeLayer('layer-macrostrat-geology-outline');
    if (map.current.getSource('source-macrostrat-geology')) map.current.removeSource('source-macrostrat-geology');

    fetch(url)
      .then(r => r.json())
      .then(geojson => {
        if (!map.current) return;
        map.current.addSource('source-macrostrat-geology', { type: 'geojson', data: geojson });
        map.current.addLayer({
          id: 'layer-macrostrat-geology',
          type: 'fill',
          source: 'source-macrostrat-geology',
          paint: {
            'fill-color': [
              'match', ['get', 'lith'],
              'shale', '#7B8794',
              'sandstone', '#D4A574',
              'limestone', '#B8C4AE',
              'granite', '#C9725A',
              'basalt', '#5A5A5A',
              '#8B7355' // default
            ],
            'fill-opacity': 0.55,
          },
        });
        map.current.addLayer({
          id: 'layer-macrostrat-geology-outline',
          type: 'line',
          source: 'source-macrostrat-geology',
          paint: { 'line-color': '#A0522D', 'line-width': 0.5 },
        });
      })
      .catch(() => {});
  };

  const baseLayers = layers.filter(l => ['osm-basemap', 'google-satellite', 'esri-satellite', 'opentopomap'].includes(l.id));
  const overlayLayers = layers.filter(l => !['osm-basemap', 'google-satellite', 'esri-satellite', 'opentopomap'].includes(l.id));

  const overallACRisk = Math.max(...layers.filter(l => l.visible).map(l => l.acriskMax));
  const overallLevel = acRiskLevel(overallACRisk);

  return (
    <div className="h-full flex flex-col bg-[#0A0C0E] text-slate-300">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <Globe className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-bold text-white">EarthVision</span>
          <span className="text-xs font-mono text-blue-400">Layered EO Intelligence</span>
        </div>
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded border text-[10px] font-bold ${acRiskColor(overallLevel)}`}>
            <Gauge className="w-3 h-3" />
            ACRisk: {overallLevel}
          </div>
          <span className="text-[10px] font-mono text-slate-500">{layers.filter(l => l.visible).length} layers active</span>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 flex overflow-hidden">

        {/* Left: Layer controls */}
        <div className="w-72 border-r border-slate-800 bg-slate-900/30 overflow-y-auto geox-scroll p-3 space-y-4">

          {/* Base layers */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <MapIcon className="w-3 h-3 text-slate-500" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Base Map</span>
            </div>
            <div className="space-y-1">
              {baseLayers.map(layer => (
                <LayerRow
                  key={layer.id}
                  layer={{ ...layer, visible: activeBaseLayer === layer.id }}
                  onToggle={handleToggleBase}
                  onOpacity={handleOpacity}
                />
              ))}
            </div>
          </div>

          {/* DEM + Terrain */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Mountain className="w-3 h-3 text-slate-500" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Terrain</span>
            </div>
            <div className="space-y-1">
              {layers.filter(l => l.id === 'dem-hillshade').map(layer => (
                <LayerRow
                  key={layer.id}
                  layer={layer}
                  onToggle={handleToggleOverlay}
                  onOpacity={handleOpacity}
                />
              ))}
            </div>
          </div>

          {/* Geology */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Layers className="w-3 h-3 text-slate-500" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Geology</span>
            </div>
            <button
              onClick={handleMacrostratToggle}
              className="geox-btn geox-btn--ghost text-[10px] w-full py-1.5 flex items-center justify-center gap-1"
            >
              <ExternalLink className="w-3 h-3" />
              Load Macrostrat at center
            </button>
            <p className="text-[9px] text-slate-600 mt-1 px-1">
              Fetches geology within current map view. PROCESS_HYPOTHESIS — not hard truth.
            </p>
          </div>

          {/* STAC Search */}
          <div className="border-t border-slate-800 pt-3">
            <STACSearchPanel bbox={bbox} onActivate={handleSTACActivate} />
          </div>

          {/* Overlay layers */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Eye className="w-3 h-3 text-slate-500" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">EO Overlays</span>
            </div>
            <div className="space-y-1">
              {overlayLayers.filter(l => l.id !== 'dem-hillshade').map(layer => (
                <LayerRow
                  key={layer.id}
                  layer={layer}
                  onToggle={handleToggleOverlay}
                  onOpacity={handleOpacity}
                />
              ))}
            </div>
          </div>

          {/* Governance note */}
          <div className="border-t border-slate-800 pt-3">
            <div className="bg-slate-800/40 rounded p-2">
              <div className="flex items-center gap-1.5 mb-1.5">
                <AlertTriangle className="w-3 h-3 text-amber-500" />
                <span className="text-[10px] font-bold text-amber-500 uppercase tracking-widest">Governance</span>
              </div>
              <p className="text-[9px] text-slate-500 leading-relaxed">
                Every layer carries a claim tag. OBSERVED = direct sensor output. DERIVED = processed. PROCESS_HYPOTHESIS = regional model, not subsurface truth.
              </p>
              <div className="mt-2">
                <ACRiskLegend />
              </div>
            </div>
          </div>

        </div>

        {/* Right: Map viewport */}
        <div className="flex-1 relative">
          <div ref={mapContainer} className="absolute inset-0" />

          {/* Coordinate HUD */}
          <CoordHUD map={map.current} />

          {/* Active layers legend */}
          {layers.filter(l => l.visible && l.legendColor).length > 0 && (
            <div className="absolute top-4 right-4 z-10 bg-slate-900/85 backdrop-blur border border-slate-700 rounded-lg p-2">
              <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Active Legend</div>
              {layers.filter(l => l.visible && l.legendColor).map(l => (
                <div key={l.id} className="flex items-center gap-1.5 mb-1">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: l.legendColor }} />
                  <span className="text-[9px] text-slate-300">{l.name}</span>
                </div>
              ))}
            </div>
          )}

          {/* Claim tag overlay */}
          <div className="absolute top-4 left-4 z-10">
            <div className="bg-slate-900/85 backdrop-blur border border-slate-700 rounded-lg px-2.5 py-1.5">
              <div className="flex items-center gap-2 text-[9px]">
                <CheckCircle2 className="w-3 h-3 text-green-500" />
                <span className="text-slate-300 font-mono">EO layers governed by ToAC v1</span>
              </div>
              <p className="text-[8px] text-slate-600 mt-0.5">
                Map tiles: not verified physical truth — always tag with OBSERVED/DERIVED/INTERPRETED
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EarthVisionPanel;
