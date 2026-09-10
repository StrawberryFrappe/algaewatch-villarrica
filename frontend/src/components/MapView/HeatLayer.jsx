import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import { RISK_PIN_RAMP } from '../../utils/risk';

// Real heatmap: points are sampled from the actual Sentinel-2 FAI raster
// (GET /risk/grid, ~1800 water pixels from the most recent clear pass — see
// src/features/fai.py's sample_grid() and scripts/collect_fai_grid.py), not
// an interpolation between the 4 station markers.
export function HeatLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points.length) return undefined;

    let heat = null;

    // leaflet.heat draws into a canvas sized from the map container and then
    // calls getImageData on it. When the container is still 0 wide -- first
    // paint, a hidden tab, a viewport resize mid-layout -- that throws
    // IndexSizeError, and with no boundary above it React unmounted the entire
    // dashboard. Wait for a real size, and re-try on resize.
    const attach = () => {
      if (heat) return;
      const size = map.getSize();
      if (!size || !size.x || !size.y) return;
      heat = buildHeat();
      heat.addTo(map);
    };

    const buildHeat = () => L.heatLayer(
      points.map((p) => [p.lat, p.lng, p.risk / 100]),
      // Over Esri satellite imagery the previous near-transparent config
      // (minOpacity 0.04 / max 2.6) was invisible. Raise the floor and pull
      // `max` down so density actually colours, widen radius/blur for a smoother
      // field, and run the gradient through the map-surface `pin` ramp
      // (blue → green). Calm water reads as a faint blue tint; real clusters
      // clearly saturate toward green.
      { radius: 18, blur: 14, maxZoom: 16, max: 1.5, minOpacity: 0.22,
        gradient: {
          0.0: RISK_PIN_RAMP[0], 0.4: RISK_PIN_RAMP[1],
          0.7: RISK_PIN_RAMP[2], 1.0: RISK_PIN_RAMP[3],
        } }
    );

    attach();
    map.on('resize', attach);
    return () => {
      map.off('resize', attach);
      if (heat) heat.remove();
    };
  }, [map, points]);

  return null;
}
