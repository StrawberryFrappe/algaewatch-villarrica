const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function get(path, { nullOn404 = false } = {}) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    // A 404 on an optional endpoint means "not available in this checkout", not
    // a failure. Anything else (backend down, CORS, 500) is a real fault and
    // must still throw so callers can tell the two apart.
    if (nullOn404 && res.status === 404) return null;
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  getStations: () => get('/stations'),
  getObservations: ({ from, to, station } = {}) => {
    const params = new URLSearchParams();
    if (from) params.set('from', from);
    if (to) params.set('to', to);
    if (station) params.set('station', station);
    const qs = params.toString();
    return get(`/observations${qs ? `?${qs}` : ''}`);
  },
  getRisk: (date) => get(`/risk?date=${date}`),
  getRiskGrid: () => get('/risk/grid'),
  // model: 'legacy' (default, the Gradient Boosting artifact that also drives
  // /risk) or 'candidate' (per-pixel quantile network). The candidate 404s when
  // this checkout has not run scripts/predict_per_pixel_forecast.py, which
  // resolves to null so the caller can fall back instead of blanking the app.
  getForecast: (date, model = 'legacy') =>
    get(`/forecast?date=${date}&model=${model}`, { nullOn404: model === 'candidate' }),
  getModelMetrics: () => get('/model/metrics'),
  // 404s when this checkout has never run scripts/train_per_pixel.py — resolved
  // to null here so callers can hide the panel without a try/catch. A non-404
  // error still rejects, so a transient backend fault is not mistaken for
  // "no candidate".
  getModelCandidate: () => get('/model/candidate', { nullOn404: true }),
};
