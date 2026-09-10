import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import { RISK_RAMP } from '../../utils/risk';

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
      // Light theme (ADR-lq-0008): ~1800 grid points stack additively, so on a
      // light surface a normal heat config turns the whole lake into one wash.
      // Keep the floor near zero, push `max` up so density rarely saturates, and
      // anchor the gradient's low end at a barely-there tint — calm water then
      // reads as the lake showing through, and only real hot clusters colour up.
      { radius: 15, blur: 16, maxZoom: 16, max: 2.6, minOpacity: 0.04,
        gradient: { 0.0: 'rgba(240,228,208,0.35)', 0.3: RISK_RAMP[1], 0.62: RISK_RAMP[2], 1.0: RISK_RAMP[3] } }
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
