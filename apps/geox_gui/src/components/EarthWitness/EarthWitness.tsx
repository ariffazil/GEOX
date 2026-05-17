import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { GroundedBadge } from '../WitnessBadges/WitnessBadges';
import { useActiveTab, useToACReport, useGEOXStore } from '../../store/geoxStore';
import { PERCEPTION_CLASS_META, CANON9_META } from '../../types';
import type { Canon9 } from '../../types';

/**
 * EarthWitness Component
 * 
 * The primary 2D geospatial grounding layer for GEOX.
 * Uses MapLibre GL JS for GPU-accelerated Earth visualization.
 * 
 * DITEMPA BUKAN DIBERI
 */
export const EarthWitness: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [lng] = useState(114.2); // Default to SE Asia / Brunei area
  const [lat] = useState(4.5);
  const [zoom] = useState(9);
  
  const activeTab = useActiveTab();

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm': {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap Contributors'
          }
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [lng, lat],
      zoom: zoom
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    const pilotData = {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "id": "basin_boundary",
          "properties": {"name": "Malay Basin Boundary", "type": "Basin"},
          "geometry": {
            "type": "Polygon",
            "coordinates": [[
              [102.0, 5.0], [105.0, 7.5], [107.0, 5.0], [105.0, 3.0], [102.0, 5.0]
            ]]
          }
        },
        {
          "type": "Feature",
          "id": "p1_zone",
          "properties": {"name": "P1: Basin-centre Anticline", "play": "P1", "fill": "#ff4444"},
          "geometry": {
            "type": "Polygon",
            "coordinates": [[
              [103.5, 5.5], [105.0, 6.0], [105.5, 5.5], [104.5, 4.5], [103.5, 5.5]
            ]]
          }
        }
      ]
    };

    map.current.on('load', () => {
      if (!map.current) return;

      map.current.addSource('malay_basin_pilot', {
        type: 'geojson',
        data: pilotData as any
      });

      map.current.addLayer({
        id: 'malay_basin_fill',
        type: 'fill',
        source: 'malay_basin_pilot',
        paint: {
          'fill-color': ['coalesce', ['get', 'fill'], '#3b82f6'],
          'fill-opacity': 0.2
        }
      });

      map.current.addLayer({
        id: 'malay_basin_outline',
        type: 'line',
        source: 'malay_basin_pilot',
        paint: {
          'line-color': ['coalesce', ['get', 'fill'], '#3b82f6'],
          'line-width': 2
        }
      });

      if (activeTab === 'pilot') {
        map.current.flyTo({
          center: [104.5, 5.5],
          zoom: 6.5,
          duration: 2000
        });
      }
    });

    return () => {
      map.current?.remove();
    };
  }, [lng, lat, zoom, activeTab]);

  return (
    <div className="relative w-full h-full min-h-[400px] border border-slate-800 rounded-lg overflow-hidden">
      {/* Map Container */}
      <div ref={mapContainer} className="absolute inset-0" />

      {/* Floating Governance Layer */}
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <GroundedBadge 
          confidence={0.92} 
          status="GROUNDED"
          source="OpenStreetMap / Protomaps"
        />
      </div>

      {/* ToAC Perception HUD */}
      <ToACHud />

      {/* Coordinate HUD */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-900/80 backdrop-blur px-3 py-1.5 rounded border border-slate-700 font-mono text-[10px] text-slate-300">
        LAT: {lat.toFixed(4)} | LON: {lng.toFixed(4)} | WGS84
      </div>

      {/* Vertical Trend Overlay */}
      <VerticalTrendOverlay />

      {/* ToAC Warning Overlay */}
      {activeTab === 'seismic' && (
        <div className="absolute inset-0 bg-red-500/5 pointer-events-none border-2 border-red-500/20 animate-pulse" />
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// ToAC Perception HUD — Overlay on map showing current perception state
// ─────────────────────────────────────────────────────────────────────────────

const ToACHud: React.FC = () => {
  const report = useToACReport();
  if (!report) return null;

  const meta = PERCEPTION_CLASS_META[report.perception_class as keyof typeof PERCEPTION_CLASS_META] || PERCEPTION_CLASS_META.HYPOTHESIS;
  const trendSymbol = report.vertical_trend === 'DEEPENING_UPWARD' ? '↘' :
    report.vertical_trend === 'SHALLOWING_UPWARD' ? '↗' : '→';

  return (
    <div className="absolute top-14 left-4 z-10 bg-slate-900/85 backdrop-blur border border-slate-700 rounded-lg p-3 shadow-xl min-w-[200px]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">ToAC v1</span>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${meta.bg} ${meta.color}`}>
          {meta.label}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-300 mb-1">
        <span className="text-slate-500">Evidence:</span>
        <span className="font-mono font-bold">{report.evidence_tag}</span>
      </div>
      {report.canon_9_touched.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-1">
          {report.canon_9_touched.map((q: Canon9) => {
            const c9 = CANON9_META[q];
            return (
              <span key={q} className="text-[9px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 border border-slate-700" title={`${c9.name} (${c9.unit})`}>
                {c9.symbol}
              </span>
            );
          })}
        </div>
      )}
      {(report.vertical_trend !== 'UNKNOWN' || report.litho_class !== 'UNKNOWN') && (
        <div className="flex items-center gap-2 text-[10px] text-slate-400 border-t border-slate-800 pt-1 mt-1">
          {report.vertical_trend !== 'UNKNOWN' && <span>{trendSymbol} {report.vertical_trend}</span>}
          {report.litho_class !== 'UNKNOWN' && <span>◆ {report.litho_class}</span>}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Vertical Trend Overlay — Arrow indicators on map for GDE trends
// ─────────────────────────────────────────────────────────────────────────────

const VerticalTrendOverlay: React.FC = () => {
  const report = useToACReport();
  const activeTabLocal = useActiveTab();
  if (!report || activeTabLocal !== 'section') return null;

  const trendArrows: Record<string, { symbol: string; color: string }> = {
    DEEPENING_UPWARD: { symbol: '▼', color: 'text-blue-400' },
    SHALLOWING_UPWARD: { symbol: '▲', color: 'text-amber-400' },
    STABLE_OR_AMBIGUOUS: { symbol: '◆', color: 'text-slate-400' },
  };
  const arrow = trendArrows[report.vertical_trend] || { symbol: '?', color: 'text-slate-500' };

  return (
    <div className="absolute bottom-14 right-4 z-10 flex items-center gap-2 bg-slate-900/80 backdrop-blur px-3 py-1.5 rounded border border-slate-700">
      <span className={`text-lg font-bold ${arrow.color}`}>{arrow.symbol}</span>
      <span className="text-[10px] text-slate-300 font-mono">{report.vertical_trend}</span>
    </div>
  );
};
