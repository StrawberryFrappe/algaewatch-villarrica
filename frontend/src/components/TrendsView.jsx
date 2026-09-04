import { Sparkline, sparklineNow, sparklineRange } from './Sparkline';
import { formatDateEs } from '../utils/format';

const CHART_DEFS = [
  { key: 'water_temp_c', label: 'Temperatura superficial', decimals: 1, unit: ' °C', color: '#0A84FF', fill: 'rgba(10,132,255,0.2)' },
  { key: 'ph', label: 'pH', decimals: 2, unit: '', color: '#30D158', fill: 'rgba(48,209,88,0.16)' },
  { key: 'fai', label: 'Índice FAI (clorofila-a)', decimals: 3, unit: '', color: '#FF9F0A', fill: 'rgba(255,159,10,0.16)' },
];

export function TrendsView({ trendSeries, day, hasInSitu }) {
  const charts = hasInSitu ? CHART_DEFS : CHART_DEFS.filter((c) => c.key === 'fai');
  const firstDate = trendSeries[0]?.date;
  const lastDate = trendSeries[trendSeries.length - 1]?.date;
  return (
    <div className="view-panel glass-content">
      <div className="view-eyebrow">
        TENDENCIAS · PROMEDIO LAGO{firstDate && lastDate ? ` · ${formatDateEs(firstDate).toUpperCase()} – ${formatDateEs(lastDate).toUpperCase()}` : ''}
      </div>
      <div className="view-title">Variables clave del modelo</div>
      {!hasInSitu && (
        <p style={{ color: 'var(--color-text-dim)', fontSize: 12, marginTop: 8 }}>
          Temperatura y pH aparecerán aquí cuando se conecten los datos in situ (SNIA). Por ahora, solo el índice FAI (Sentinel-2) es real.
        </p>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
        {charts.map((c) => (
          <div key={c.key} className="trend-card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 14.5, fontWeight: 600, color: '#FFFFFF', letterSpacing: -0.3 }}>{c.label}</span>
              <span style={{ fontSize: 17, color: c.color }}>{sparklineNow(trendSeries, c.key, day, c.decimals, c.unit)}</span>
            </div>
            <div style={{ marginTop: 8 }}>
              <Sparkline series={trendSeries} valueKey={c.key} color={c.color} fill={c.fill} decimals={c.decimals} selectedIndex={day} height={118} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)', marginTop: 4 }}>
              <span>{firstDate ? formatDateEs(firstDate).toUpperCase() : ''}</span>
              <span>Rango {sparklineRange(trendSeries, c.key, c.decimals, c.unit)}</span>
              <span>{lastDate ? formatDateEs(lastDate).toUpperCase() : ''}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
