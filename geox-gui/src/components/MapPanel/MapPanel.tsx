/**
 * MapPanel — 2D MapLibre GL basemap with geospatial verification.
 * ArcGIS-style 2D spatial grounding pane.
 */

import { useEffect, useRef, useState } from "react";
import { useGeoxTool } from "../../hooks/useGeoxTool";
import type { GeospatialResponse } from "../../types/geox";

export function MapPanel() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [verified, setVerified] = useState<GeospatialResponse | null>(null);
  const { call: verifyGeospatial, loading } = useGeoxTool<GeospatialResponse>("geox_verify_geospatial");

  useEffect(() => {
    // MapLibre is loaded on demand to avoid bundle bloat when panel is hidden
    let map: unknown;
    (async () => {
      if (!mapRef.current) return;
      try {
        const maplibregl = await import("maplibre-gl");
        map = new maplibregl.Map({
          container: mapRef.current,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution: "© OpenStreetMap contributors",
              },
            },
            layers: [{ id: "osm", type: "raster", source: "osm" }],
          },
          center: [103.82, 3.14],
          zoom: 5,
        });

        (map as { on: (e: string, cb: (ev: { lngLat: { lat: number; lng: number } }) => void) => void }).on(
          "click",
          async (e) => {
            const { lat, lng } = e.lngLat;
            const result = await verifyGeospatial({ lat, lon: lng, radius_m: 1000 });
            if (result) setVerified(result);
          }
        );
      } catch {
        // MapLibre not available in this environment
      }
    })();
    return () => {
      if (map && typeof (map as { remove?: () => void }).remove === "function") {
        (map as { remove: () => void }).remove();
      }
    };
  }, [verifyGeospatial]);

  return (
    <div className="relative w-full h-full flex flex-col bg-geox-panel">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-geox-border text-xs text-gray-400 font-mono">
        <span>EARTH CANVAS</span>
        {loading && <span className="text-geox-hold">verifying…</span>}
        {verified && (
          <span className="ml-auto text-geox-seal">
            {verified.geological_province} · {verified.verdict}
          </span>
        )}
      </div>
      <div ref={mapRef} className="flex-1" />
    </div>
  );
}
