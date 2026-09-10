import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';

// Lake-wide daily average, used for the historical trend sparklines (Tendencias).
// This is derived purely from observed FAI (+ in-situ once it's wired in) —
// no model output here. Returns null for a series with no real values yet,
// so callers can skip rendering a misleading flat-zero line.
function buildTrendSeries(observations, dates) {
  const byDate = new Map(dates.map((d) => [d, []]));
  observations.forEach((o) => byDate.get(o.date)?.push(o));
  const avg = (rows, key) => {
    const valid = rows.map((r) => r[key]).filter((v) => v != null);
    return valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
  };
  return dates.map((date) => {
    const rows = byDate.get(date) ?? [];
    return {
      date,
      water_temp_c: avg(rows, 'water_temp_c'),
      ph: avg(rows, 'ph'),
      fai: avg(rows, 'fai'),
    };
  });
}

export function useAppData() {
  const [view, setView] = useState('mapa');
  const [day, setDay] = useState(0);
  const [hover, setHover] = useState(null);
  const [pinned, setPinned] = useState(null);
  const [open, setOpen] = useState(true);

  const [stations, setStations] = useState([]);
  const [observations, setObservations] = useState([]);
  const [dates, setDates] = useState([]);
  const [risk, setRisk] = useState(null);
  const [riskGrid, setRiskGrid] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [candidate, setCandidate] = useState(null);
  const [loadError, setLoadError] = useState(null);

  // Initial load: station catalog, full observation window, model metrics,
  // and the real FAI grid (one satellite-pass snapshot, not date-dependent).
  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getStations(), api.getObservations(), api.getModelMetrics(), api.getRiskGrid()])
      .then(([stationsRes, obsRes, metricsRes, gridRes]) => {
        if (cancelled) return;
        const uniqueDates = [...new Set(obsRes.map((o) => o.date))].sort();
        setStations(stationsRes);
        setObservations(obsRes);
        setDates(uniqueDates);
        setMetrics(metricsRes);
        setRiskGrid(gridRes);
        setDay(Math.max(0, uniqueDates.length - 1)); // most recent day, like the design's initial state
      })
      .catch((err) => !cancelled && setLoadError(err.message));
    return () => { cancelled = true; };
  }, []);

  // The per-pixel candidate is fetched on its own and its failure is swallowed
  // on purpose. It is an optional, non-serving model: a checkout that has not
  // trained it must still render the dashboard, so a 404 here must not reach
  // setLoadError and blank the whole app.
  useEffect(() => {
    let cancelled = false;
    api.getModelCandidate()
      .then((c) => !cancelled && setCandidate(c))
      .catch(() => !cancelled && setCandidate(null));
    return () => { cancelled = true; };
  }, []);

  const selectedDate = dates[day] ?? null;

  // Per-date fetches: current risk (present state) and 7-day forecast (model output).
  useEffect(() => {
    if (!selectedDate) return;
    let cancelled = false;
    api.getRisk(selectedDate).then((r) => !cancelled && setRisk(r)).catch((err) => !cancelled && setLoadError(err.message));
    api.getForecast(selectedDate).then((f) => !cancelled && setForecast(f)).catch((err) => !cancelled && setLoadError(err.message));
    return () => { cancelled = true; };
  }, [selectedDate]);

  const observationByStationDate = useMemo(() => {
    const map = new Map();
    observations.forEach((o) => map.set(`${o.station_id}:${o.date}`, o));
    return map;
  }, [observations]);

  const trendSeries = useMemo(() => buildTrendSeries(observations, dates), [observations, dates]);
  const hasInSitu = useMemo(() => observations.some((o) => o.water_temp_c != null), [observations]);

  // Merges catalog + current risk + current observation into one row per station.
  const stationRows = useMemo(() => {
    if (!risk || stations.length === 0) return [];
    const riskByStation = new Map(risk.stations.map((s) => [s.station_id, s]));
    return stations.map((s) => {
      const r = riskByStation.get(s.id);
      const obs = observationByStationDate.get(`${s.id}:${selectedDate}`);
      return {
        ...s,
        risk: r?.risk ?? 0,
        level: r?.level ?? 'MUY_BAJO',
        ...obs,
      };
    });
  }, [stations, risk, observationByStationDate, selectedDate]);

  const activeStationId = hover ?? pinned;
  const activeStation = stationRows.find((s) => s.id === activeStationId) ?? null;

  // Real date of the last Sentinel-2 pass (from the risk overlay / grid), as
  // opposed to selectedDate, which the slider extends up to "today" over
  // forward-filled values. BL-013: surfaced so views can flag projected values.
  const lastPassDate = risk?.overlay?.updated_at ?? riskGrid?.date ?? null;
  const selectedIsProjected = !!(lastPassDate && selectedDate && selectedDate > lastPassDate);

  return {
    view, setView,
    day, setDay,
    hover, setHover,
    pinned, setPinned,
    open, setOpen,
    dates,
    selectedDate,
    stationRows,
    activeStation,
    trendSeries,
    hasInSitu,
    risk,
    candidate,
    riskGrid,
    forecast,
    metrics,
    lastPassDate,
    selectedIsProjected,
    loadError,
    isReady: dates.length > 0 && risk !== null,
  };
}
