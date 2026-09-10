import { formatDateEs } from './format';

// The FAI series is a ~5-day-revisit satellite feed forward-filled onto a daily
// grid (see src/features/build_dataset.py). Any selected date after the last real
// Sentinel-2 pass shows the last known value held constant. BL-013: that must be
// disclosed everywhere a value is read, not only in the header.

export const STALE_DAYS_THRESHOLD = 6;

export function daysBetween(fromIso, toIso) {
  if (!fromIso || !toIso) return null;
  return Math.round((new Date(toIso) - new Date(fromIso)) / 86400000);
}

// Age of the last real pass relative to today, e.g. "22 ago 2026 · hace 19 d".
export function passAgeLabel(lastPassIso) {
  if (!lastPassIso) return '—';
  const age = daysBetween(lastPassIso, new Date().toISOString().slice(0, 10));
  const since = age == null ? '' : ` · hace ${age} d`;
  return `${formatDateEs(lastPassIso)}${since}`;
}

// How far the selected slider date is projected past the last real pass.
// Returns null when the selected date is on or before the last pass.
export function projectionGapDays(lastPassIso, selectedIso) {
  if (!lastPassIso || !selectedIso || selectedIso <= lastPassIso) return null;
  return daysBetween(lastPassIso, selectedIso);
}
