// Risk scale 0-100, exclusive to risk (see design tokens). The backend returns
// the level label already computed (MUY_BAJO/BAJO/MEDIO/ALTO); this file owns the
// label/colour presentation.
//
// BL-009 + ADR-lq-0008: light-theme pastel sequential ramp, sampled from
// matplotlib `magma` warm-end (peach → dusty terracotta). Colourblind-safe:
//   - OKLCH lightness strictly monotonic decreasing (0.84 → 0.76 → 0.65 → 0.53),
//     so the order survives loss of hue discrimination;
//   - single hue family (~36° spread), the CVD-safety mechanism for an ordered
//     ramp;
//   - every adjacent pair keeps ΔE ≥ 8.5 (OKLab ×100) under normal, protanopia,
//     deuteranopia and tritanopia (Machado 2009).
// Validated with the dataviz skill's validate_palette (`--ordinal`, surface
// #F6F8FA) — see ADR-lq-0008 and agents/local/logbook. The dark magma variant
// it replaces is in git history.
//
// `ink` is a darker step for small text on white (the ramp fill itself is a
// mark colour, tuned for chips/markers/gradients not body text).
export const RISK_LEVELS = {
  MUY_BAJO: { label: 'Muy bajo', color: 'var(--risk-muy-bajo)', hex: '#EAC49B', ink: '#8A6A45' },
  BAJO: { label: 'Bajo', color: 'var(--risk-bajo)', hex: '#E0A074', ink: '#8A5A38' },
  MEDIO: { label: 'Medio', color: 'var(--risk-medio)', hex: '#C9765A', ink: '#9A4F3B' },
  ALTO: { label: 'Alto', color: 'var(--risk-alto)', hex: '#A05445', ink: '#8A463B' },
};

// Ordered low → high, for gradients (heatmap, legend bar).
export const RISK_RAMP = [
  RISK_LEVELS.MUY_BAJO.hex,
  RISK_LEVELS.BAJO.hex,
  RISK_LEVELS.MEDIO.hex,
  RISK_LEVELS.ALTO.hex,
];

export function riskPresentation(level) {
  return RISK_LEVELS[level] ?? RISK_LEVELS.MUY_BAJO;
}
