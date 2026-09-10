import { formatDateEs, numEs } from '../utils/format';
import { MODELS, Segmented } from './Segmented';

// Research-prototype notice. Replaces the former "TRL 2 · resultados no validados
// en campo" seal, removed from the UI per ADR-lq-0010 (the user found the seal
// unprofessional and over-self-aware). This keeps the one point that still
// matters to a viewer: the output is not an operational alert.
const PROTOTYPE_NOTE =
  'Prototipo de investigación. Las salidas no son alertas sanitarias ni operacionales.';

// The backend `caveats` strings still open with the old seal sentence
// ("TRL 2 — no validado en campo."). Strip just that clause on render so the
// substantive caveats (sample size, MI-1, spatial autocorrelation) survive.
// The model artifacts themselves are left byte-unchanged.
//
// Tolerates the separator variants actually seen in the artifacts and the design
// handoff (em dash, en dash, hyphen, middot) and a clause that runs to the end of
// the string with no trailing period.
function stripSeal(text) {
  if (!text) return text;
  return text.replace(/\s*TRL\s*2\s*[—–·-]\s*[^.]*(?:\.|$)\s*/i, ' ').trim();
}

// Muted confusion-matrix accents for the light theme (ADR-lq-0008). Not the risk
// ramp — these label matrix cells. Paired with the text label, never colour alone.
const CM_ROWS = [
  { key: 'true_positives', label: 'Verdaderos positivos', tone: '#3F7E5C' },
  { key: 'false_positives', label: 'Falsos positivos', tone: '#B07A2E' },
  { key: 'false_negatives', label: 'Falsos negativos', tone: '#9A4F3B' },
  { key: 'true_negatives', label: 'Verdaderos negativos', tone: '#43589A' },
];

// The legacy Gradient Boosting model — the one that actually drives /risk and
// /forecast. Rendered when the Modelo switch is on "Producción".
function LegacyModelCards({ metrics }) {
  const cm = metrics.confusion_matrix;
  const persistence = metrics.baselines?.persistence;
  const trivial = metrics.baselines?.trivial_rule;
  const verdict = metrics.beats_baselines ?? {};

  return (
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
          La validación es temporal: se entrena con las fechas más antiguas y se
          evalúa con las siguientes, sin mezclarlas, para medir predicción y no
          memoria.
        </div>
        <div style={{ fontSize: 11.5, lineHeight: 1.5, color: 'var(--color-text-dim)', marginTop: 8 }}>
          {stripSeal(metrics.disclaimer)}
        </div>
      </div>

      <div className="model-card">
        <div className="model-card-eyebrow">COMPARACIÓN CON BASELINES</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 11, fontSize: 12.5 }}>
          <div>
            <div style={{ color: 'var(--color-text-secondary)' }}>MAE del modelo: {numEs(metrics.metrics.mae_fai, 5)}</div>
            <div style={{ color: 'var(--color-text-dim)' }}>
              Persistencia: {numEs(persistence?.mae_fai, 5)} · {verdict.persistence ? 'superada' : 'no superada'}
            </div>
          </div>
          <div>
            <div style={{ color: 'var(--color-text-secondary)' }}>F1 del modelo: {numEs(metrics.metrics.f1_score, 4)}</div>
            <div style={{ color: 'var(--color-text-dim)' }}>
              Regla trivial: {numEs(trivial?.f1_score, 4)} · {verdict.trivial_rule ? 'superada' : 'no superada'}
            </div>
          </div>
          <div style={{ color: 'var(--color-text-dim)', lineHeight: 1.45 }}>
            Una métrica solo es evidencia cuando aparece junto a una referencia calculada sobre las mismas filas.
          </div>
        </div>
      </div>
    </div>
  );
}

// The per-pixel candidate. Evaluated but not deployed: /risk and /forecast still
// run the legacy artifacts. Rendered when the Modelo switch is on "Candidato".
function CandidatePanel({ candidate }) {
  if (!candidate) return null;

  const c = candidate;
  const persistence = c.baselines?.persistence?.mae_fai;
  const climatology = c.baselines?.climatology?.mae_fai;
  const beatsAny = Object.values(c.beats_baselines ?? {}).some(Boolean);
  const foldsBeating = c.folds.filter((f) => f.mae_fai < f.climatology_mae_fai).length;

  return (
    <section style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <div className="view-eyebrow" style={{ margin: 0 }}>CANDIDATO · {c.version}</div>
        <span
          style={{
            fontSize: 9.5,
            letterSpacing: 0.5,
            padding: '2px 7px',
            borderRadius: 999,
            border: '1px solid var(--hairline)',
            color: 'var(--color-text-tertiary-2)',
          }}
        >
          {c.serving ? 'EN PRODUCCIÓN' : 'NO ALIMENTA EL MAPA'}
        </span>
      </div>
      <div className="view-title" style={{ marginTop: 4 }}>Red cuantílica per-píxel + ERA5-Land</div>
      <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', marginTop: 6, lineHeight: 1.55 }}>
        {c.n_pairs.toLocaleString('es-CL')} pares honestos · {c.n_pixels.toLocaleString('es-CL')} píxeles ·{' '}
        {c.n_anchor_dates} fechas ancla · {c.date_range.start} a {c.date_range.end}. Sin filas rellenadas.
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 16 }}>
        <div className="model-card">
          <div className="model-card-eyebrow">VEREDICTO CONTRA BASELINES</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 11, fontSize: 12.5 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>MAE del modelo</span>
              <span style={{ fontSize: 15, color: 'var(--color-text-primary)' }}>{numEs(c.metrics.mae_fai, 6)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, color: 'var(--color-text-dim)' }}>
              <span>Persistencia</span>
              <span>{numEs(persistence, 6)} · {c.beats_baselines?.persistence ? 'superada' : 'no superada'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, color: 'var(--color-text-dim)' }}>
              <span>Climatología</span>
              <span>{numEs(climatology, 6)} · {c.beats_baselines?.climatology ? 'superada' : 'no superada'}</span>
            </div>
            <div style={{ color: 'var(--color-text-dim)', lineHeight: 1.45, marginTop: 2 }}>
              {beatsAny
                ? 'Supera al menos una línea base en el promedio.'
                : `No supera a ninguna en el promedio — pero gana en ${foldsBeating} de ${c.folds.length} folds. Ver el detalle.`}
            </div>
          </div>
        </div>

        <div className="model-card">
          <div className="model-card-eyebrow">CALIBRACIÓN DEL INTERVALO</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 11, fontSize: 12.5 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Cobertura q10–q90</span>
              <span style={{ fontSize: 15, color: '#3F7E5C' }}>{numEs(c.metrics.q10_q90_coverage * 100, 2)}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, color: 'var(--color-text-dim)' }}>
              <span>Nominal</span><span>80,00%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, color: 'var(--color-text-dim)' }}>
              <span>Ancho medio</span><span>{numEs(c.metrics.mean_interval_width_fai, 6)}</span>
            </div>
            <div style={{ color: 'var(--color-text-dim)', lineHeight: 1.45, marginTop: 2 }}>
              El modelo no acierta el valor puntual mejor que la climatología, pero su declaración de
              incertidumbre es honesta: el intervalo contiene al valor real con la frecuencia que promete.
            </div>
          </div>
        </div>

        <div className="model-card">
          <div className="model-card-eyebrow">CLASIFICACIÓN DE FLORACIÓN</div>
          <div style={{ marginTop: 11, fontSize: 12.5 }}>
            <div style={{ fontSize: 15, color: 'var(--color-text-tertiary-2)' }}>No reportada</div>
            <div style={{ color: 'var(--color-text-dim)', lineHeight: 1.5, marginTop: 7 }}>
              {c.classification_reason}
            </div>
          </div>
        </div>
      </div>

      <div className="model-card" style={{ marginTop: 12 }}>
        <div className="model-card-eyebrow">VALIDACIÓN POR FOLD · {c.cv_scheme}</div>
        <div style={{ fontSize: 11.5, lineHeight: 1.5, color: 'var(--color-text-dim)', marginTop: 8 }}>
          Cada fold entrena hasta una fecha y evalúa la ventana siguiente (ventana
          expansiva), con un embargo del horizonte de pronóstico entre ambas y un
          bloque 2×2 del lago dejado afuera.
        </div>
        <div style={{ overflowX: 'auto', marginTop: 11 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ color: 'var(--color-text-label)', textAlign: 'right' }}>
                <th style={{ textAlign: 'left', fontWeight: 500, padding: '4px 8px 6px 0' }}>Fold</th>
                <th style={{ textAlign: 'left', fontWeight: 500, padding: '4px 8px 6px 0' }}>Ventana de validación</th>
                <th style={{ fontWeight: 500, padding: '4px 0 6px 8px' }}>Región excl.</th>
                <th style={{ fontWeight: 500, padding: '4px 0 6px 8px' }}>Modelo</th>
                <th style={{ fontWeight: 500, padding: '4px 0 6px 8px' }}>Climatología</th>
                <th style={{ fontWeight: 500, padding: '4px 0 6px 8px' }}>Cobertura</th>
              </tr>
            </thead>
            <tbody>
              {c.folds.map((f) => {
                const wins = f.mae_fai < f.climatology_mae_fai;
                return (
                  <tr key={f.fold} style={{ borderTop: '1px solid var(--hairline)', textAlign: 'right' }}>
                    <td style={{ textAlign: 'left', padding: '6px 8px 6px 0', color: 'var(--color-text-secondary)' }}>{f.fold}</td>
                    <td style={{ textAlign: 'left', padding: '6px 8px 6px 0', color: 'var(--color-text-dim)', whiteSpace: 'nowrap' }}>
                      {f.first_validation_date} → {f.last_validation_date}
                    </td>
                    <td style={{ padding: '6px 0 6px 8px', color: 'var(--color-text-dim)' }}>{f.held_spatial_block}</td>
                    <td style={{ padding: '6px 0 6px 8px', color: wins ? '#3F7E5C' : 'var(--color-text-primary)' }}>
                      {numEs(f.mae_fai, 6)}{wins ? ' ✓' : ''}
                    </td>
                    <td style={{ padding: '6px 0 6px 8px', color: 'var(--color-text-dim)' }}>{numEs(f.climatology_mae_fai, 6)}</td>
                    <td style={{ padding: '6px 0 6px 8px', color: 'var(--color-text-dim)' }}>{numEs(f.q10_q90_coverage * 100, 1)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ fontSize: 11.5, lineHeight: 1.5, color: 'var(--color-text-dim)', marginTop: 11 }}>
          {stripSeal(c.disclaimer)}
        </div>
      </div>
    </section>
  );
}

export function ModelView({
  metrics, candidate, candidateError,
  forecastModel, setForecastModel, forecastModelError,
}) {
  if (!metrics) {
    return (
      <div className="view-panel glass-content">
        <div className="view-eyebrow">MODELO PREDICTIVO</div>
        <div className="view-title">Cargando métricas…</div>
      </div>
    );
  }

  let candidateDisabled = '';
  if (!candidate) {
    candidateDisabled = candidateError
      ? 'No se pudo cargar el candidato (ver consola del navegador).'
      : 'El candidato per-píxel no se ha entrenado en este checkout.';
  }
  const showing = forecastModel === 'candidate' && candidate ? 'candidate' : 'legacy';

  return (
    <div className="view-panel glass-content">
      <div className="view-eyebrow">MODELO PREDICTIVO</div>
      <div className="view-title">Dos modelos, ninguno listo para producción</div>
      <p className="model-lede">
        El modelo de <strong>producción</strong> (Gradient Boosting + FAI) no supera
        a sus líneas base y lee coordenadas de estación que caen fuera del agua. El{' '}
        <strong>candidato</strong> per-píxel + ERA5-Land es la iteración pensada para
        reemplazarlo: entrenado sobre datos reales sin relleno, tampoco las supera
        en promedio, pero gana en los folds más volátiles y declara su
        incertidumbre de forma calibrada.
      </p>
      <p className="model-lede" style={{ marginTop: 8 }}>
        Este selector <strong>cambia el modelo que produce el pronóstico</strong> del
        panel analítico, no solo las métricas de abajo.
      </p>
      <p className="model-lede" style={{ marginTop: 8 }}>
        El mapa todavía <strong>no usa ningún modelo entrenado</strong>. En las 56
        fechas con pasada Sentinel-2 muestra la lectura real; en las otras 316 del
        deslizador arrastra el último valor conocido, que es exactamente la línea
        base de <em>persistencia</em>. Es decir: el 85% de las fechas del mapa ya
        están siendo «predichas», y por el método más tonto posible. Ahí es donde
        un modelo tiene que aportar, y todavía no lo hace.
      </p>

      <Segmented
        value={forecastModel}
        onChange={setForecastModel}
        options={MODELS}
        disabledReason={{ candidate: candidateDisabled }}
      />

      {forecastModelError && (
        <p className="model-note" style={{ marginTop: 10, color: 'var(--status-stale)' }}>
          {forecastModelError}
        </p>
      )}

      {showing === 'legacy'
        ? <LegacyModelCards metrics={metrics} />
        : <CandidatePanel candidate={candidate} />}

      <p className="model-note">{PROTOTYPE_NOTE}</p>
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
    { label: 'F1-SCORE', value: fmt(m.f1_score, 2), pct: pct(m.f1_score), note: `base ${fmt(metrics.baselines?.trivial_rule?.f1_score, 2)}` },
    { label: 'AUC-ROC', value: fmt(m.auc_roc, 2), pct: pct(m.auc_roc), note: 'hold-out' },
    { label: 'MAE FAI', value: fmt(m.mae_fai, 3), pct: m.mae_fai == null ? 0 : (1 - m.mae_fai) * 100, note: `persist. ${fmt(metrics.baselines?.persistence?.mae_fai, 3)}` },
  ];

  return (
    <footer className="footer glass-panel">
      <div style={{ flex: '0 0 auto', whiteSpace: 'nowrap', display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span style={{ fontSize: 9.5, letterSpacing: 0.6, color: 'var(--color-text-label)' }}>MODELO EN PRODUCCIÓN</span>
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
        <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{metrics.validation.n_observations.toLocaleString('es-CL')} obs · CV temporal</span>
        <span style={{ fontSize: 9.5, color: 'var(--color-text-dim)' }}>Umbral de alerta: FAI ≥ {numEs(metrics.fai_alert_threshold, 4)}</span>
      </div>
    </footer>
  );
}
