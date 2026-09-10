import { useState } from 'react';
import { formatDateEs } from '../utils/format';

const TABS = [
  ['mapa', 'Mapa'],
  ['estaciones', 'Estaciones'],
  ['tendencias', 'Tendencias'],
  ['modelo', 'Modelo'],
];

const STALE_DAYS_THRESHOLD = 6;

// Fallback mark if /logo.png is not present yet (see public/README).
function LogoFallback() {
  return (
    <svg className="brand-logo" viewBox="0 0 32 32" aria-hidden="true" style={{ background: '#EAF1F7', padding: 3 }}>
      <circle cx="16" cy="16" r="13" fill="none" stroke="#5B77C2" strokeWidth="1.4" opacity="0.55" />
      <circle cx="16" cy="16" r="7.5" fill="none" stroke="#5FA980" strokeWidth="1.4" />
      <path d="M5 19c2.6-2 4.6-2 7.2 0s4.6 2 7.2 0 4.6-2 7.2 0" fill="none" stroke="#5B77C2" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="16" cy="16" r="2.2" fill="#D19A5C" />
    </svg>
  );
}

function BrandLogo() {
  const [failed, setFailed] = useState(false);
  if (failed) return <LogoFallback />;
  return (
    <img
      className="brand-logo"
      src="/logo.png"
      alt=""
      onError={() => setFailed(true)}
    />
  );
}

export function Header({ view, setView, dates, day, setDay, overlayUpdatedAt, selectedIsProjected }) {
  const selectedDate = dates[day];
  const lastPassDate = overlayUpdatedAt ?? dates[dates.length - 1];
  const staleDays = lastPassDate ? Math.round((new Date() - new Date(lastPassDate)) / 86400000) : 0;
  const isStale = staleDays > STALE_DAYS_THRESHOLD;

  return (
    <header className="header">
      <div className="container header-bar">
        <div className="brand">
          <BrandLogo />
          <div className="brand-text">
            <div className="brand-title">AlgaeWatch <span>Villarrica</span></div>
            <div className="brand-sub">Monitoreo y predicción de floraciones · TRL 2</div>
          </div>
        </div>

        <nav className="tabs" role="tablist" aria-label="Vistas">
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
        </nav>

        <div className="live-indicator">
          <span className={`live-dot${isStale ? ' live-dot--stale' : ''}`} />
          <div className="live-meta">
            <span className="label">{isStale ? 'Dato desactualizado' : 'Última actualización'}</span>
            <span className="value">{lastPassDate ? formatDateEs(lastPassDate) : '—'}</span>
            <span className="source">Sentinel-2 L2A · 4 estaciones IoT</span>
          </div>
        </div>
      </div>

      <div className="container header-tools">
        <div className="time-window">
          <span className="label">Ventana temporal</span>
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
          <span className="label">
            Fecha seleccionada
            {selectedIsProjected && <span className="projected-tag">· PROYECCIÓN</span>}
          </span>
          <span className="value">{selectedDate ? formatDateEs(selectedDate) : '—'}</span>
          {selectedIsProjected && (
            <span className="projected-note">Sin pasada satelital · valor arrastrado desde la última</span>
          )}
        </div>
      </div>
    </header>
  );
}
