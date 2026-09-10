import { numEs } from '../utils/format';

// viewBox 0 0 320 78, matching the design handoff's sparkline geometry.
export function Sparkline({ series, valueKey, color, fill, decimals, unit = '', selectedIndex, height = 78 }) {
  const values = series.map((row) => row[valueKey]);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const spread = hi - lo || 1;
  const n = values.length;

  const x = (i) => 4 + (i / (n - 1 || 1)) * 312;
  const y = (v) => 66 - ((v - lo) / spread) * 56;

  const points = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const area = `4,70 ${points} 316,70`;
  const mx = x(selectedIndex).toFixed(1);
  const my = y(values[selectedIndex] ?? lo).toFixed(1);

  return (
    <svg viewBox="0 0 320 78" preserveAspectRatio="none" style={{ width: '100%', height, display: 'block' }}>
      <line x1="0" y1="70" x2="320" y2="70" stroke="rgba(36,48,63,0.14)" strokeWidth="1" />
      <line x1="0" y1="8" x2="320" y2="8" stroke="rgba(36,48,63,0.08)" strokeWidth="1" strokeDasharray="2 4" />
      <polyline points={area} fill={fill} stroke="none" />
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
      <line x1={mx} y1="0" x2={mx} y2="72" stroke="rgba(36,48,63,0.28)" strokeWidth="1" strokeDasharray="2 3" />
      <circle cx={mx} cy={my} r="3.4" fill={color} stroke="#FFFFFF" strokeWidth="1.4" />
    </svg>
  );
}

export function sparklineNow(series, valueKey, selectedIndex, decimals, unit = '') {
  const v = series[selectedIndex]?.[valueKey] ?? 0;
  return `${numEs(v, decimals)}${unit}`;
}

export function sparklineRange(series, valueKey, decimals, unit = '') {
  const values = series.map((row) => row[valueKey]);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  return `${numEs(lo, decimals)} – ${numEs(hi, decimals)}${unit}`;
}
