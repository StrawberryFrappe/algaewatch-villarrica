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

const RAMP = [
  RISK_LEVELS.MUY_BAJO.pin,
  RISK_LEVELS.BAJO.pin,
  RISK_LEVELS.MEDIO.pin,
  RISK_LEVELS.ALTO.pin,
];

// `fai_to_risk` is a sigmoid centred on the alert threshold, so on a typical
// pass almost every water pixel lands within a point or two of the same low
// value. Mapping that straight onto the ramp paints a flat, dead wash and
// throws away real variation the sensor did measure.
//
// GAMMA < 1 stretches the low end of the scale across more of the ramp, so
// neighbouring pixels at risk 4 and 7 become distinguishable. It is a *display*
// transform only: it changes nothing about the underlying value, the legend
// still shows the true 0-100 scale, and the ordering is preserved exactly, so a
// hotter cell can never render cooler than a calmer one.
const GAMMA = 0.6;

function lerpChannel(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function lerpHex(from, to, t) {
  const a = [1, 3, 5].map((i) => parseInt(from.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(to.slice(i, i + 2), 16));
  const c = a.map((v, i) => lerpChannel(v, b[i], t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// Continuous colour across the ramp rather than four hard bands.
function cellColor(risk) {
  const clamped = Math.min(1, Math.max(0, risk / 100));
  const t = Math.pow(clamped, GAMMA) * (RAMP.length - 1);
  const i = Math.min(RAMP.length - 2, Math.floor(t));
  return lerpHex(RAMP[i], RAMP[i + 1], t - i);
}

// Low risk is the overwhelming majority of any pass, so painting it at full
// strength would hide the lake under a flat wash. Opacity rises with risk: calm
// water stays a tint you can see the water through, hot cells read solid.
function cellOpacity(risk) {
  const clamped = Math.min(1, Math.max(0, risk / 100));
  return 0.3 + 0.55 * Math.pow(clamped, GAMMA);
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
