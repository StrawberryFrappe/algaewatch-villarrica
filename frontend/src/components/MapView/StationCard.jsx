import { formatDateEs, numEs } from '../../utils/format';
import { riskPresentation } from '../../utils/risk';

// Pure content — no absolute positioning. Rendered inside a Leaflet Popup
// (see LeafletMap.jsx), which handles anchoring to the real map projection.
export function StationCardContent({ station, lastPassDate, projectionGap }) {
  if (!station) return null;
  const { label, hex, ink } = riskPresentation(station.level);
  const passDate = lastPassDate ?? station.date;

  return (
    <div className="station-popup-content">
      <div style={{ fontSize: 14.5, fontWeight: 600, color: 'var(--color-text-primary)', lineHeight: 1.25 }}>{station.name}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 4 }}>
        <span style={{ fontSize: 9, letterSpacing: 0.4, color: 'var(--color-text-label)' }}>
          {station.code} · {station.sector.toUpperCase()}
        </span>
        <span style={{ fontSize: 9, color: projectionGap != null ? 'var(--risk-alto-ink)' : 'var(--color-text-dim)', whiteSpace: 'nowrap' }}>
          {passDate ? `PASADA ${formatDateEs(passDate)}` : '—'}
          {projectionGap != null ? ` · PROY. +${projectionGap} d` : ''}
        </span>
      </div>
      <div
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 9, padding: '4px 11px', borderRadius: 999,
          fontSize: 10, fontWeight: 600, letterSpacing: 0.4, border: `1px solid ${hex}`,
          background: `${hex}33`, color: ink,
        }}
      >
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: hex }} />
        RIESGO {label.toUpperCase()} · {station.risk}/100
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 14px', marginTop: 12 }}>
        <Field label="TEMP. AGUA" value={station.water_temp_c != null ? `${numEs(station.water_temp_c, 1)} °C` : '—'} />
        <Field label="pH" value={station.ph != null ? numEs(station.ph, 2) : '—'} />
        <Field label="OXÍGENO DISUELTO" value={station.dissolved_oxygen_mgl != null ? `${numEs(station.dissolved_oxygen_mgl, 1)} mg/L` : '—'} />
        <Field label="FAI / CLOROFILA" value={station.fai != null ? numEs(station.fai, 3) : '—'} />
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: 9, letterSpacing: 0.5, color: 'var(--color-text-label)' }}>{label}</span>
      <span style={{ fontSize: 15, color: 'var(--color-text-primary)' }}>{value}</span>
    </div>
  );
}
