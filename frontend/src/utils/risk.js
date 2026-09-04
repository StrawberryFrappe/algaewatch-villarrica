// Risk scale 0-100, exclusive to risk (see design tokens). The backend
// returns the level label already computed (MUY_BAJO/BAJO/MEDIO/ALTO);
// this file owns the label/color presentation, matching design tokens.
export const RISK_LEVELS = {
  MUY_BAJO: { label: 'Muy bajo', color: 'var(--risk-muy-bajo)', hex: '#64D2FF' },
  BAJO: { label: 'Bajo', color: 'var(--risk-bajo)', hex: '#30D158' },
  MEDIO: { label: 'Medio', color: 'var(--risk-medio)', hex: '#FF9F0A' },
  ALTO: { label: 'Alto', color: 'var(--risk-alto)', hex: '#FF453A' },
};

export function riskPresentation(level) {
  return RISK_LEVELS[level] ?? RISK_LEVELS.MUY_BAJO;
}
