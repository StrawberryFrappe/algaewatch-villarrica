import { formatDateEs, numEs } from '../utils/format';
import { riskPresentation } from '../utils/risk';

export function StationsView({ stationRows, selectedDate, hover, setHover }) {
  return (
    <div className="view-panel glass-content">
      <div className="view-eyebrow">ESTACIONES DE MONITOREO · {selectedDate ? formatDateEs(selectedDate) : ''}</div>
      <div className="view-title">Mediciones in situ y riesgo por estación</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12, marginTop: 16 }}>
        {stationRows.map((s) => {
          const { hex } = riskPresentation(s.level);
          return (
            <div
              key={s.id}
              className="station-card"
              style={hover === s.id ? { background: 'rgba(10,132,255,0.10)' } : undefined}
              onMouseEnter={() => setHover(s.id)}
              onMouseLeave={() => setHover(null)}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
                <span style={{ fontSize: 15, fontWeight: 600, color: '#FFFFFF', letterSpacing: -0.3 }}>{s.name}</span>
                <span style={{ fontSize: 13, color: hex }}>{s.risk}/100</span>
              </div>
              <div style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)', marginTop: 3 }}>
                {s.code} · {s.sector.toUpperCase()}
              </div>
              <div style={{ height: 6, borderRadius: 999, background: 'var(--progress-track)', marginTop: 11, overflow: 'hidden' }}>
                <div style={{ height: 6, borderRadius: 999, width: `${s.risk}%`, background: hex }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 14px', marginTop: 13 }}>
                <Field label="TEMP. AGUA" value={s.water_temp_c != null ? `${numEs(s.water_temp_c, 1)} °C` : '—'} />
                <Field label="pH" value={s.ph != null ? numEs(s.ph, 2) : '—'} />
                <Field label="OXÍGENO DISUELTO" value={s.dissolved_oxygen_mgl != null ? `${numEs(s.dissolved_oxygen_mgl, 1)} mg/L` : '—'} />
                <Field label="FAI / CLOROFILA" value={s.fai != null ? numEs(s.fai, 3) : '—'} />
                <Field label="VIENTO MEDIO" value={s.wind_speed_kmh != null ? `${numEs(s.wind_speed_kmh, 1)} km/h` : '—'} />
                <Field label="ÚLTIMA MEDICIÓN" value={s.date ? formatDateEs(s.date) : '—'} small />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Field({ label, value, small }) {
  return (
    <div>
      <div style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>{label}</div>
      <div style={{ fontSize: small ? 13 : 16, color: small ? 'var(--color-text-secondary)' : '#FFFFFF', paddingTop: small ? 3 : 0 }}>{value}</div>
    </div>
  );
}
