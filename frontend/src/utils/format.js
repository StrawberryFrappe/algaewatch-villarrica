const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// Parses a 'YYYY-MM-DD' string as a local calendar date (avoids UTC-shift
// off-by-one when the browser's timezone is behind UTC).
export function parseIsoDate(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function formatDateEs(isoDate) {
  const d = parseIsoDate(isoDate);
  return `${String(d.getDate()).padStart(2, '0')} ${MESES[d.getMonth()]} ${d.getFullYear()}`;
}

export function numEs(value, decimals) {
  return value.toFixed(decimals).replace('.', ',');
}
