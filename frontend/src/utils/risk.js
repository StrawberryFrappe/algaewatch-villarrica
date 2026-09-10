// Risk scale 0-100, exclusive to risk (see design tokens). The backend returns
// the level label already computed (MUY_BAJO/BAJO/MEDIO/ALTO); this file owns the
// label/colour presentation.
//
// Blue (low) → green (high) sequential ramp, per user request 2026-09-10
// (replaces the peach→terracotta magma ramp of BL-009 / ADR-lq-0008; that
// variant is in git history). Kept colour-vision-safe the same way viridis is:
//   - lightness rises strictly and monotonically with risk (≈ blue L48 → green
//     L70), so the order survives full loss of hue discrimination;
//   - the hue walk stays inside the blue→teal→green arc, avoiding the red/green
//     confusion axis entirely.
// Note: green reads as "safe" by convention, so here high risk is the *bright*
// end — the rising lightness is what signals severity, not the hue.
//
// `ink` is a darker step for small text on white. `pin` is the map-surface
// variant (markers, heat, map legend); currently equal to `hex` because the new
// ramp is already mid-toned and reads over satellite imagery, but kept as its
// own field so the map can diverge from chip colours later without a refactor.
export const RISK_LEVELS = {
  MUY_BAJO: { label: 'Muy bajo', color: 'var(--risk-muy-bajo)', hex: '#2E7BB0', ink: '#245E86', pin: '#2E7BB0' },
  BAJO: { label: 'Bajo', color: 'var(--risk-bajo)', hex: '#1C9BA0', ink: '#16777A', pin: '#1C9BA0' },
  MEDIO: { label: 'Medio', color: 'var(--risk-medio)', hex: '#23A96F', ink: '#1A8155', pin: '#23A96F' },
  ALTO: { label: 'Alto', color: 'var(--risk-alto)', hex: '#52C244', ink: '#3C8F33', pin: '#52C244' },
};

// Ordered low → high, for gradients on white surfaces (legend bar, chips).
export const RISK_RAMP = [
  RISK_LEVELS.MUY_BAJO.hex,
  RISK_LEVELS.BAJO.hex,
  RISK_LEVELS.MEDIO.hex,
  RISK_LEVELS.ALTO.hex,
];

// Ordered low → high, for the map surface (heat layer, map legend bar).
export const RISK_PIN_RAMP = [
  RISK_LEVELS.MUY_BAJO.pin,
  RISK_LEVELS.BAJO.pin,
  RISK_LEVELS.MEDIO.pin,
  RISK_LEVELS.ALTO.pin,
];

export function riskPresentation(level) {
  return RISK_LEVELS[level] ?? RISK_LEVELS.MUY_BAJO;
}
