import { Header } from './components/Header';
import { MapView } from './components/MapView/MapView';
import { StationsView } from './components/StationsView';
import { TrendsView } from './components/TrendsView';
import { ModelView, ModelFooter } from './components/ModelView';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useAppData } from './hooks/useAppData';

export default function App() {
  const data = useAppData();
  const {
    view, setView, day, setDay, hover, setHover, pinned, setPinned, open, setOpen,
    dates, selectedDate, stationRows, trendSeries, hasInSitu, riskGrid, risk, forecast, metrics, candidate, candidateError,
    forecastModel, setForecastModel, forecastModelError,
    lastPassDate, selectedIsProjected,
    loadError, isReady,
  } = data;

  return (
    <div className="shell">
      <Header
        view={view} setView={setView} dates={dates} day={day} setDay={setDay}
        overlayUpdatedAt={risk?.overlay?.updated_at}
        selectedIsProjected={selectedIsProjected}
      />

      <main className="main container">
        {loadError && (
          <div className="view-panel glass-content">
            <div className="view-title" style={{ color: 'var(--risk-alto-ink)' }}>No se pudo cargar la API</div>
            <p style={{ color: 'var(--color-text-tertiary)' }}>
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
          <ErrorBoundary label="El mapa">
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
            lastPassDate={lastPassDate}
            selectedIsProjected={selectedIsProjected}
            forecastModel={forecastModel}
            setForecastModel={setForecastModel}
            candidate={candidate}
            candidateError={candidateError}
          />
          </ErrorBoundary>
        )}

        {!loadError && isReady && view === 'estaciones' && (
          <ErrorBoundary label="La vista Estaciones">
            <StationsView
              stationRows={stationRows}
              selectedDate={selectedDate}
              hover={hover}
              setHover={setHover}
              lastPassDate={lastPassDate}
              selectedIsProjected={selectedIsProjected}
            />
          </ErrorBoundary>
        )}

        {!loadError && isReady && view === 'tendencias' && (
          <ErrorBoundary label="La vista Tendencias">
            <TrendsView trendSeries={trendSeries} day={day} hasInSitu={hasInSitu} />
          </ErrorBoundary>
        )}

        {!loadError && isReady && view === 'modelo' && (
          <ErrorBoundary label="La vista Modelo">
            <ModelView
              metrics={metrics}
              candidate={candidate}
              candidateError={candidateError}
              forecastModel={forecastModel}
              setForecastModel={setForecastModel}
              forecastModelError={forecastModelError}
            />
            <ModelFooter metrics={metrics} />
          </ErrorBoundary>
        )}
      </main>
    </div>
  );
}
