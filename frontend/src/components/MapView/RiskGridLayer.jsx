import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { RISK_LEVELS } from '../../utils/risk';

// Real FAI raster: one filled cell per sampled water pixel from
// GET /risk/grid (~1,860 pixels of the most recent clear Sentinel-2 pass, see
// src/features/fai.py sample_grid).
//
// This replaces a leaflet.heat layer, which was the wrong instrument. A heatmap
// renders accumulated point *density*: every pixel contributed risk/100 as an
// intensity, and on a regular grid dozens of them fall inside one blur kernel,
// so their intensities summed and saturated the gradient. The lake painted
// solid at the top of the risk ramp while 1,778 of its 1,860 pixels were
// actually sitting at risk 5. It was drawing "there are samples here", not
// "risk is high here", and no change of model or date could alter that.
//
// A scalar field on a regular grid wants a raster. Each cell is coloured by its
// own value and nothing bleeds into its neighbours, so a calm pixel next to a
// hot one reads as calm.
const LAT_STEP = 0.00289;
const LNG_STEP = 0.00342;

// Risk 0-100 -> ramp colour. Matches the backend's risk_level() cutoffs so the
// raster, the markers and the legend all speak the same scale.
function cellColor(risk) {
  if (risk < 25) return RISK_LEVELS.MUY_BAJO.pin;
  if (risk < 45) return RISK_LEVELS.BAJO.pin;
  if (risk < 68) return RISK_LEVELS.MEDIO.pin;
  return RISK_LEVELS.ALTO.pin;
}

// Low risk is the overwhelming majority of any pass, so painting it at full
// strength would hide the lake under a flat wash. Opacity rises with risk: calm
// water stays a tint you can see the water through, hot cells read solid.
function cellOpacity(risk) {
  if (risk < 25) return 0.28;
  if (risk < 45) return 0.5;
  if (risk < 68) return 0.68;
  return 0.82;
}

export function RiskGridLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length === 0) return undefined;

    // One canvas renderer for the whole grid: ~1,860 individual SVG paths would
    // cost a DOM node each and stutter on pan/zoom.
    const renderer = L.canvas({ padding: 0.3 });
    const group = L.layerGroup([], { renderer });

    const halfLat = LAT_STEP / 2;
    const halfLng = LNG_STEP / 2;

    points.forEach((p) => {
      const color = cellColor(p.risk);
      L.rectangle(
        [
          [p.lat - halfLat, p.lng - halfLng],
          [p.lat + halfLat, p.lng + halfLng],
        ],
        {
          renderer,
          stroke: false,
          fill: true,
          fillColor: color,
          fillOpacity: cellOpacity(p.risk),
          interactive: false,
        },
      ).addTo(group);
    });

    group.addTo(map);
    return () => {
      group.remove();
    };
  }, [map, points]);

  return null;
}
