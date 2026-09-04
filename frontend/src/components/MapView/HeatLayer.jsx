import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

// Real heatmap: points are sampled from the actual Sentinel-2 FAI raster
// (GET /risk/grid, ~1800 water pixels from the most recent clear pass — see
// src/features/fai.py's sample_grid() and scripts/collect_fai_grid.py), not
// an interpolation between the 4 station markers.
export function HeatLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points.length) return undefined;
    const heat = L.heatLayer(
      points.map((p) => [p.lat, p.lng, p.risk / 100]),
      { radius: 22, blur: 20, maxZoom: 16, max: 1, minOpacity: 0.3,
        gradient: { 0.0: '#64D2FF', 0.35: '#30D158', 0.6: '#FF9F0A', 1.0: '#FF453A' } }
    );
    heat.addTo(map);
    return () => heat.remove();
  }, [map, points]);

  return null;
}
