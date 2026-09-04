import { Header } from './components/Header';
import { MapView } from './components/MapView/MapView';
import { StationsView } from './components/StationsView';
import { TrendsView } from './components/TrendsView';
import { ModelView, ModelFooter } from './components/ModelView';
import { useAppData } from './hooks/useAppData';

export default function App() {
  const data = useAppData();
  const {
    view, setView, day, setDay, hover, setHover, pinned, setPinned, open, setOpen,
    dates, selectedDate, stationRows, trendSeries, hasInSitu, riskGrid, risk, forecast, metrics,
    loadError, isReady,
  } = data;

  return (
    <div className="shell">
      <div className="shell-halo shell-halo--blue" />
      <div className="shell-halo shell-halo--green" />

      <Header
        view={view} setView={setView} dates={dates} day={day} setDay={setDay}
        overlayUpdatedAt={risk?.overlay?.updated_at}
      />

      <main className="main">
        {loadError && (
          <div className="view-panel glass-content">
            <div className="view-title" style={{ color: '#FF453A' }}>No se pudo cargar la API</div>
            <p style={{ color: 'var(--color-text-tertiary-2)' }}>
              {loadError}. Verifica que el backend esté corriendo (ver backend/README.md).
            </p>
          </div>
        )}

        {!loadError && !isReady && (
          <div className="view-panel glass-content">
            <div className="view-title">Cargando datos…</div>
          </div>
        )}

        {!loadError && isReady && view === 'mapa' && (
          <MapView
            stationRows={stationRows}
            hover={hover}
            pinned={pinned}
            setHover={setHover}
            setPinned={setPinned}
            open={open}
            setOpen={setOpen}
            forecast={forecast}
            trendSeries={trendSeries}
            hasInSitu={hasInSitu}
            riskGrid={riskGrid}
            day={day}
            selectedDate={selectedDate}
          />
        )}

        {!loadError && isReady && view === 'estaciones' && (
          <StationsView stationRows={stationRows} selectedDate={selectedDate} hover={hover} setHover={setHover} />
        )}

        {!loadError && isReady && view === 'tendencias' && (
          <TrendsView trendSeries={trendSeries} day={day} hasInSitu={hasInSitu} />
        )}

        {!loadError && isReady && view === 'modelo' && (
          <ModelView metrics={metrics} />
        )}
      </main>

      {!loadError && isReady && view === 'modelo' && <ModelFooter metrics={metrics} />}
    </div>
  );
}
