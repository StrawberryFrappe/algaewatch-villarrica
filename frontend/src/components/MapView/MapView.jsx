import { LeafletMap } from './LeafletMap';
import { AnalyticsPanel } from './AnalyticsPanel';

export function MapView({
  stationRows, hover, pinned, setHover, setPinned,
  open, setOpen, forecast, trendSeries, hasInSitu, riskGrid, day, selectedDate,
}) {
  return (
    <div style={{ display: 'flex', gap: 12, flex: '1 1 auto', minWidth: 0, minHeight: 0 }}>
      <section
        style={{
          flex: 1, position: 'relative', minWidth: 0, overflow: 'hidden',
          border: '1px solid var(--hairline)', borderRadius: 16,
          boxShadow: 'var(--shadow-content)',
        }}
      >
        <LeafletMap
          stations={stationRows}
          riskGrid={riskGrid}
          hover={hover}
          pinned={pinned}
          onEnter={setHover}
          onLeave={() => setHover(null)}
          onClick={(id) => setPinned(pinned === id ? null : id)}
        />

        <div style={{ position: 'absolute', top: 16, left: 18, zIndex: 500, display: 'flex', flexDirection: 'column', gap: 3, pointerEvents: 'none' }}>
          <span style={{ fontSize: 11, letterSpacing: 0.8, color: 'var(--color-text-tertiary-2)', textShadow: '0 1px 6px rgba(0,0,0,0.9)' }}>LAGO VILLARRICA · 39°17′S 72°05′O</span>
          <span style={{ fontSize: 10, color: 'var(--color-text-dim)', textShadow: '0 1px 6px rgba(0,0,0,0.9)' }}>Superficie 176 km² · Prof. máx. 165 m · Cuenca Toltén</span>
        </div>

        <div className="legend-card" style={{ zIndex: 1000 }}>
          <span style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>ÍNDICE DE RIESGO DE FLORACIÓN</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 206, height: 9, borderRadius: 999, background: 'linear-gradient(90deg,#64D2FF,#30D158,#FF9F0A,#FF453A)' }} />
            <span style={{ fontSize: 10, color: 'var(--color-text-tertiary-2)' }}>0 → 100</span>
          </div>
          <div style={{ display: 'flex', gap: 14, fontSize: 10, color: 'var(--color-text-tertiary)' }}>
            <span>Muy bajo</span><span>Bajo</span><span>Medio</span><span style={{ color: '#FF453A' }}>Alto</span>
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
      />
    </div>
  );
}
