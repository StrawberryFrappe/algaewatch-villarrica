// Shared segmented control. Used by the Modelo view and by the map's analytics
// panel, which drive the *same* app-level forecast model state — the switch has
// to be reachable from the screen where its effect is visible, not only from the
// screen that explains it.
export function Segmented({ value, onChange, options, disabledReason = {}, size }) {
  return (
    <div className={size === 'sm' ? 'seg seg--sm' : 'seg'} role="tablist" aria-label="Modelo a mostrar">
      {options.map((o) => {
        const disabled = Boolean(disabledReason[o.id]);
        return (
          <button
            key={o.id}
            type="button"
            role="tab"
            aria-selected={value === o.id}
            className="seg-btn"
            disabled={disabled}
            aria-disabled={disabled || undefined}
            title={disabled ? disabledReason[o.id] : undefined}
            onClick={() => !disabled && onChange(o.id)}
          >
            {size === 'sm' && o.shortLabel ? o.shortLabel : o.label}
          </button>
        );
      })}
    </div>
  );
}

// Ids match the backend's `model` query parameter on /forecast: this switch does
// not only change what is on screen, it changes which model produces the live
// projection.
export const MODELS = [
  { id: 'legacy', label: 'Producción (GB)', shortLabel: 'Producción' },
  { id: 'candidate', label: 'Candidato (per-píxel)', shortLabel: 'Candidato' },
];
