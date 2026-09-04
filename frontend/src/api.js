const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
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
  getForecast: (date) => get(`/forecast?date=${date}`),
  getModelMetrics: () => get('/model/metrics'),
};
