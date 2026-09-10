import { formatDateEs, numEs } from '../utils/format';

// Mandated maturity seal (design handoff §"Datos", §"VALIDACIÓN"). PR-4 requires
// this exact text to be preserved and visible. It is fixed UI chrome, not run
// data — kept here as a literal, the same way the AI-panel disclaimer lives in
// backend/app/routers/forecast.py. `metrics.disclaimer` carries the extra,
// run-specific caveats (BL-019: the seal and the caveats are different texts and
// both belong).
const TRL_SEAL = 'TRL 2 · resultados no validados en campo';

// Muted confusion-matrix accents for the light theme (ADR-lq-0008). Not the risk
// ramp — these label matrix cells. Paired with the text label, never colour alone.
const CM_ROWS = [
  { key: 'true_positives', label: 'Verdaderos positivos', tone: '#3F7E5C' },
  { key: 'false_positives', label: 'Falsos positivos', tone: '#B07A2E' },
  { key: 'false_negatives', label: 'Falsos negativos', tone: '#9A4F3B' },
  { key: 'true_negatives', label: 'Verdaderos negativos', tone: '#43589A' },
];

export function ModelView({ metrics }) {
  if (!metrics) {
    return (
      <div className="view-panel glass-content">
        <div className="view-eyebrow">MODELO PREDICTIVO</div>
        <div className="view-title">Cargando métricas…</div>
      </div>
    );
  }

  const cm = metrics.confusion_matrix;

  return (
    <div className="view-panel glass-content">
      <div className="view-eyebrow">MODELO PREDICTIVO · {metrics.version}</div>
      <div className="view-title">Gradient Boosting + índice FAI Sentinel-2</div>
      <div className="trl-seal" role="note">
        <span className="trl-seal-dot" aria-hidden="true" />
        {TRL_SEAL}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 16 }}>
        <div className="model-card">
          <div className="model-card-eyebrow">MATRIZ DE CONFUSIÓN · UMBRAL FAI ≥ {numEs(metrics.fai_alert_threshold, 4)}</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 11 }}>
            {CM_ROWS.map((r) => (
              <div key={r.key} style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
                <span style={{ fontSize: 12.5, color: 'var(--color-text-tertiary-2)' }}>{r.label}</span>
                <span style={{ fontSize: 16, color: r.tone }}>{cm[r.key].toLocaleString('es-CL')}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="model-card">
          <div className="model-card-eyebrow">IMPORTANCIA DE VARIABLES</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 11 }}>
            {metrics.feature_importance.map((v) => (
              <div key={v.feature}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 12.5, color: 'var(--color-text-secondary)' }}>
                  <span>{v.feature}</span><span style={{ color: 'var(--color-text-tertiary-2)' }}>{v.importance_pct}%</span>
                </div>
                <div style={{ height: 5, borderRadius: 999, background: 'var(--progress-track)', marginTop: 5, overflow: 'hidden' }}>
                  <div style={{ height: 5, borderRadius: 999, width: `${v.importance_pct}%`, background: 'var(--color-accent)' }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="model-card">
          <div className="model-card-eyebrow">VALIDACIÓN</div>
          <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--color-text-secondary)', marginTop: 10 }}>
            {metrics.validation.n_observations.toLocaleString('es-CL')} observaciones · {metrics.validation.period}<br />
            {metrics.validation.method}<br />
            Reentrenado el {formatDateEs(metrics.validation.retrained_at)}<br />
            Horizonte de predicción: {metrics.validation.horizon_days} días
          </div>
          <div style={{ fontSize: 11.5, lineHeight: 1.5, color: 'var(--color-text-dim)', marginTop: 10 }}>
            <strong style={{ color: 'var(--color-text-tertiary-2)', fontWeight: 600 }}>{TRL_SEAL}.</strong>{' '}
            {metrics.disclaimer}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ModelFooter({ metrics }) {
  if (!metrics) return null;
  const m = metrics.metrics;

  const fmt = (v, d) => (v == null ? '—' : numEs(v, d));
  const pct = (v) => (v == null ? 0 : v * 100);

  const CHIPS = [
    { label: 'PRECISIÓN', value: fmt(m.precision, 2), pct: pct(m.precision), note: `VP ${metrics.confusion_matrix.true_positives}/FP ${metrics.confusion_matrix.false_positives}` },
    { label: 'RECALL', value: fmt(m.recall, 2), pct: pct(m.recall), note: `FN ${metrics.confusion_matrix.false_negatives}` },
    { label: 'F1-SCORE', value: fmt(m.f1_score, 2), pct: pct(m.f1_score), note: 'floración' },
    { label: 'AUC-ROC', value: fmt(m.auc_roc, 2), pct: pct(m.auc_roc), note: 'hold-out' },
    { label: 'MAE FAI', value: fmt(m.mae_fai, 3), pct: m.mae_fai == null ? 0 : (1 - m.mae_fai) * 100, note: 'error medio' },
  ];

  return (
    <footer className="footer glass-panel">
      <div style={{ flex: '0 0 auto', whiteSpace: 'nowrap', display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>MODELO PREDICTIVO</span>
        <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-text)' }}>Gradient Boosting + FAI</span>
        <span style={{ fontSize: 9.5, color: 'var(--color-text-dim)' }}>{metrics.version} · reentrenado {formatDateEs(metrics.validation.retrained_at)}</span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'nowrap', gap: 8, flex: '1 1 auto', minWidth: 0 }}>
        {CHIPS.map((c) => (
          <div key={c.label} className="metric-chip">
            <span style={{ fontSize: 8.5, letterSpacing: 0.4, color: 'var(--color-text-label)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.label}</span>
            <span style={{ fontSize: 17, lineHeight: 1, fontWeight: 600, color: 'var(--color-text-primary)' }}>{c.value}</span>
            <div style={{ height: 4, borderRadius: 999, background: 'var(--progress-track)', overflow: 'hidden' }}>
              <div style={{ height: 4, borderRadius: 999, width: `${c.pct}%`, background: 'var(--color-accent)' }} />
            </div>
            <span style={{ fontSize: 8.5, lineHeight: 1.3, color: 'var(--color-text-dim)' }}>{c.note}</span>
          </div>
        ))}
      </div>

      <div style={{ flex: '0 0 auto', whiteSpace: 'nowrap', display: 'flex', flexDirection: 'column', gap: 2, textAlign: 'right', paddingLeft: 14, borderLeft: '1px solid var(--hairline)' }}>
        <span style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>VALIDACIÓN</span>
        <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{metrics.validation.n_observations.toLocaleString('es-CL')} obs · CV 5-fold</span>
        <span style={{ fontSize: 9.5, color: 'var(--color-text-dim)' }}>Umbral de alerta: FAI ≥ {numEs(metrics.fai_alert_threshold, 4)}</span>
      </div>
    </footer>
  );
}
