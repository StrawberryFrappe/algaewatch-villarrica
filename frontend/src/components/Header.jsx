import { formatDateEs } from '../utils/format';

const TABS = [
  ['mapa', 'Mapa'],
  ['estaciones', 'Estaciones'],
  ['tendencias', 'Tendencias'],
  ['modelo', 'Modelo'],
];

const STALE_DAYS_THRESHOLD = 6;

function Logo() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
      <circle cx="15" cy="15" r="13.2" fill="none" stroke="#0A84FF" strokeWidth="1.3" opacity="0.5" />
      <circle cx="15" cy="15" r="7.6" fill="none" stroke="#30D158" strokeWidth="1.3" />
      <path d="M4 18.4c2.6-2.1 4.6-2.1 7.2 0s4.6 2.1 7.2 0 4.6-2.1 7.2 0" fill="none" stroke="#0A84FF" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="15" cy="15" r="2.1" fill="#FF9F0A" />
    </svg>
  );
}

export function Header({ view, setView, dates, day, setDay, overlayUpdatedAt }) {
  const selectedDate = dates[day];
  // The real date of the last Sentinel-2 pass used (not dates[last], which is
  // forward-filled up to "today" for the slider range and is not a real pass).
  const lastPassDate = overlayUpdatedAt ?? dates[dates.length - 1];
  const staleDays = lastPassDate ? Math.round((new Date() - new Date(lastPassDate)) / 86400000) : 0;
  const isStale = staleDays > STALE_DAYS_THRESHOLD;

  return (
    <header className="header glass-panel">
      <div className="header-row1">
        <div className="brand">
          <Logo />
          <div className="brand-text">
            <div className="brand-title">AlgaeWatch <span>Villarrica</span></div>
            <div className="brand-sub">MONITOREO Y PREDICCIÓN DE FLORACIONES · TRL 2</div>
          </div>
        </div>

        <div className="tabs" role="tablist">
          {TABS.map(([id, label]) => (
            <button
              key={id}
              role="tab"
              aria-selected={view === id}
              className="tab-btn"
              onClick={() => setView(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="spacer" />

        <div className="live-indicator">
          <span className={`live-dot${isStale ? ' live-dot--stale' : ''}`} />
          <div className="live-meta">
            <span className="label">{isStale ? 'DATO DESACTUALIZADO' : 'ÚLTIMA ACTUALIZACIÓN'}</span>
            <span className="value">{lastPassDate ? formatDateEs(lastPassDate) : '—'}</span>
            <span className="source">Sentinel-2 L2A · 4 estaciones IoT</span>
          </div>
        </div>
      </div>

      <div className="header-row2">
        <div className="time-window">
          <span className="label">VENTANA TEMPORAL</span>
          <input
            type="range"
            min={0}
            max={Math.max(0, dates.length - 1)}
            step={1}
            value={day}
            onChange={(e) => setDay(Number(e.target.value))}
            style={{ '--range-pct': `${(day / Math.max(1, dates.length - 1)) * 100}%` }}
          />
        </div>
        <div className="selected-date">
          <span className="label">FECHA SELECCIONADA</span>
          <span className="value">{selectedDate ? formatDateEs(selectedDate) : '—'}</span>
        </div>
      </div>
    </header>
  );
}
