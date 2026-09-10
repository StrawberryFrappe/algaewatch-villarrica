import { LeafletMap } from './LeafletMap';
import { AnalyticsPanel } from './AnalyticsPanel';
import { RISK_PIN_RAMP, RISK_LEVELS } from '../../utils/risk';
import { passAgeLabel, projectionGapDays } from '../../utils/staleness';

export function MapView({
  stationRows, hover, pinned, setHover, setPinned,
  open, setOpen, forecast, trendSeries, hasInSitu, riskGrid, day, selectedDate,
  lastPassDate, selectedIsProjected,
  forecastModel, setForecastModel, candidate, candidateError,
}) {
  const gap = projectionGapDays(lastPassDate, selectedDate);
  return (
    <div className="map-layout">
      <section className="map-shell glass-content">
        <LeafletMap
          stations={stationRows}
          riskGrid={riskGrid}
          hover={hover}
          pinned={pinned}
          onEnter={setHover}
          onLeave={() => setHover(null)}
          onClick={(id) => setPinned(pinned === id ? null : id)}
          lastPassDate={lastPassDate}
          projectionGap={selectedIsProjected ? gap : null}
        />

        <div className="map-annot">
          <span className="map-annot-title">Lago Villarrica · 39°17′S 72°05′O</span>
          <span>Superficie 176 km² · Prof. máx. 165 m · Cuenca Toltén</span>
          <span>Grilla FAI · pasada {passAgeLabel(lastPassDate)}</span>
          {selectedIsProjected && (
            <span className="map-annot-warn">
              Riesgo proyectado {gap != null ? `+${gap} d` : ''} sobre la última pasada
            </span>
          )}
        </div>

        <div className="legend-card">
          <span style={{ fontSize: 9, letterSpacing: 0.6, color: 'var(--color-text-label)', textTransform: 'uppercase' }}>Índice de riesgo de floración</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 190, height: 8, borderRadius: 999, background: `linear-gradient(90deg,${RISK_PIN_RAMP.join(',')})` }} />
            <span style={{ fontSize: 10, color: 'var(--color-text-tertiary)' }}>0 → 100</span>
          </div>
          <div style={{ display: 'flex', gap: 14, fontSize: 10, color: 'var(--color-text-tertiary)' }}>
            <span>Muy bajo</span><span>Bajo</span><span>Medio</span><span style={{ color: RISK_LEVELS.ALTO.pin, fontWeight: 600 }}>Alto</span>
          </div>
        </div>
      </section>

      <AnalyticsPanel
        open={open}
        setOpen={setOpen}
        forecast={forecast}
        trendSeries={trendSeries}
        hasInSitu={hasInSitu}
        dayIndex={day}
        stationRows={stationRows}
        hover={hover}
        pinned={pinned}
        setHover={setHover}
        setPinned={setPinned}
        selectedDate={selectedDate}
        forecastModel={forecastModel}
        setForecastModel={setForecastModel}
        candidate={candidate}
        candidateError={candidateError}
      />
    </div>
  );
}
