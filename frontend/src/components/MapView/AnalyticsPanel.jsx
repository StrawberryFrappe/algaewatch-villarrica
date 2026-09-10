import { Sparkline, sparklineNow, sparklineRange } from '../Sparkline';
import { formatDateEs } from '../../utils/format';
import { riskPresentation } from '../../utils/risk';

// Muted chart series colours for the light theme (ADR-lq-0008) — not the risk
// ramp, these encode different measures.
const CHART_DEFS = [
  { key: 'water_temp_c', label: 'Temperatura superficial', decimals: 1, unit: ' °C', color: '#5B77C2', fill: 'rgba(91,119,194,0.14)' },
  { key: 'ph', label: 'pH', decimals: 2, unit: '', color: '#5FA980', fill: 'rgba(95,169,128,0.14)' },
  { key: 'fai', label: 'Índice FAI (clorofila-a)', decimals: 3, unit: '', color: '#C9765A', fill: 'rgba(201,118,90,0.14)' },
];

function SparkFlash() {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" aria-hidden="true">
      <path d="M9 1.5l1.5 4.1 4.1 1.5-4.1 1.5L9 12.7 7.5 8.6 3.4 7.1l4.1-1.5L9 1.5z" fill="#5B77C2" />
      <circle cx="14.2" cy="13.6" r="2.2" fill="#5FA980" />
    </svg>
  );
}

export function AnalyticsPanel({ open, setOpen, forecast, trendSeries, dayIndex, hasInSitu, stationRows, hover, pinned, setHover, setPinned, selectedDate }) {
  const charts = hasInSitu ? CHART_DEFS : CHART_DEFS.filter((c) => c.key === 'fai');
  const firstDate = trendSeries[0]?.date;
  const lastDate = trendSeries[trendSeries.length - 1]?.date;
  if (!open) {
    return (
      <aside className="glass-content" style={{ flex: '0 0 48px', width: 48, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, paddingTop: 14 }}>
        <button className="collapse-btn" onClick={() => setOpen(true)}>‹</button>
        <span style={{ writingMode: 'vertical-rl', fontSize: 9.5, letterSpacing: 0.8, color: 'var(--color-text-label)' }}>
          PANEL ANALÍTICO · ANÁLISIS IA
        </span>
      </aside>
    );
  }

  return (
    <aside className="glass-content analytics-panel" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, overflowY: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '13px 16px', borderBottom: '1px solid var(--hairline-soft)' }}>
        <span style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>PANEL ANALÍTICO</span>
        <button className="collapse-btn" onClick={() => setOpen(false)}>COLAPSAR ›</button>
      </div>

      <div className="ai-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 10 }}>
          <SparkFlash />
          <span style={{ fontSize: 10, letterSpacing: 0.7, color: 'var(--color-accent-ink)', fontWeight: 600 }}>ANÁLISIS IA</span>
          <span style={{ marginLeft: 'auto', fontSize: 9.5, color: 'var(--color-text-label)' }}>
            {forecast ? `CONFIANZA ${forecast.confidence_pct}%` : '—'}
          </span>
        </div>
        <p style={{ margin: '0 0 10px', fontSize: 13.5, lineHeight: 1.55, color: 'var(--color-text)' }}>
          {forecast?.summary ?? 'Calculando proyección…'}
        </p>
        <p style={{ margin: '0 0 12px', fontSize: 12.5, lineHeight: 1.5, color: 'var(--color-text-tertiary-2)' }}>
          {forecast?.recommendation ?? ''}
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <MiniStat label="RIESGO MEDIO LAGO (7D)" value={forecast ? `${forecast.lake_mean_risk_7d}/100` : '—'} color={forecast ? riskPresentation(levelFor(forecast.lake_mean_risk_7d)).hex : 'var(--color-text-tertiary)'} />
          <MiniStat label="ESTACIONES EN ALERTA" value={forecast ? `${forecast.stations_in_alert} / 4` : '—'} color={forecast && forecast.stations_in_alert > 1 ? 'var(--status-stale)' : 'var(--status-live)'} />
          <MiniStat label="HORIZONTE" value={forecast ? `${forecast.horizon_days} d` : '—'} color="var(--color-text-tertiary)" />
        </div>
        <div style={{ marginTop: 11, paddingTop: 9, borderTop: '1px solid var(--hairline-soft)', fontSize: 9, letterSpacing: 0.6, color: 'var(--color-text-dim)' }}>
          {forecast?.disclaimer ?? 'ALGAEWATCH-LM · SÍNTESIS SOBRE LA SALIDA DEL MODELO, NO VALIDADA EN CAMPO'}
        </div>
      </div>

      <div style={{ padding: '16px 14px 4px', fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>
        TENDENCIAS · PROMEDIO LAGO
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '8px 14px 14px' }}>
        {charts.map((c) => (
          <div key={c.key} className="trend-card">
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-text-secondary)' }}>{c.label}</span>
              <span style={{ fontSize: 14, color: c.color }}>{sparklineNow(trendSeries, c.key, dayIndex, c.decimals, c.unit)}</span>
            </div>
            <Sparkline series={trendSeries} valueKey={c.key} color={c.color} fill={c.fill} decimals={c.decimals} selectedIndex={dayIndex} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'var(--color-text-dim)', marginTop: 3 }}>
              <span>{firstDate ? formatDateEs(firstDate).toUpperCase() : ''}</span>
              <span>{sparklineRange(trendSeries, c.key, c.decimals, c.unit)}</span>
              <span>{lastDate ? formatDateEs(lastDate).toUpperCase() : ''}</span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding: '0 14px 18px' }}>
        <div style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)', marginBottom: 8 }}>
          ESTACIONES · {selectedDate ? formatDateEs(selectedDate) : ''}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {stationRows.map((s) => {
            const { hex } = riskPresentation(s.level);
            const isActive = hover === s.id || pinned === s.id;
            return (
              <div
                key={s.id}
                className="station-row"
                style={isActive ? { background: 'var(--surface-tint)', borderColor: 'var(--color-accent-light)' } : undefined}
                onMouseEnter={() => setHover(s.id)}
                onMouseLeave={() => setHover(null)}
                onClick={() => setPinned(pinned === s.id ? null : s.id)}
              >
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: hex, flex: '0 0 auto' }} />
                <span style={{ flex: 1, fontSize: 12.5, color: 'var(--color-text-secondary)' }}>{s.name}</span>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontVariantNumeric: 'tabular-nums' }}>{s.risk}/100</span>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

function levelFor(risk) {
  if (risk < 25) return 'MUY_BAJO';
  if (risk < 45) return 'BAJO';
  if (risk < 68) return 'MEDIO';
  return 'ALTO';
}

function MiniStat({ label, value, color }) {
  return (
    <div style={{ flex: 1, padding: '8px 9px', border: '1px solid var(--hairline)', borderRadius: 10, background: 'var(--surface-panel)', display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span style={{ fontSize: 8.5, letterSpacing: 0.4, color: 'var(--color-text-label)', textTransform: 'uppercase' }}>{label}</span>
      <span style={{ fontSize: 15, fontWeight: 600, color }}>{value}</span>
    </div>
  );
}
