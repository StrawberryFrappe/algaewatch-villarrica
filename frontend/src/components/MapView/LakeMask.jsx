import { Polygon } from 'react-leaflet';
import { LAKE_POLYGON, WORLD_RING } from '../../data/lakePolygon';

// Clips the FAI risk heat overlay to the lake surface (BL-010).
//
// The /risk/grid points are already water-only pixels, but leaflet.heat draws
// each one with a radius/blur in screen pixels, so the gradient bleeds past the
// shoreline onto land. Rather than fight the heat renderer, we lay an inverse
// mask over it: one polygon whose outer ring covers the whole map and whose
// hole is the lake, filled with the map's dark base colour. Heat that spilled
// onto land is painted over; the water surface shows through the hole.
//
// This matches the design handoff's own suggestion ("una capa fill inversa
// sobre tierra") and stays library-agnostic per ADR 0003 — the same polygon
// would drive a Mapbox fill layer unchanged.
export function LakeMask() {
  return (
    <>
      {/* Inverse land mask: [outerRing, lakeHole]. */}
      <Polygon
        positions={[WORLD_RING, LAKE_POLYGON]}
        pathOptions={{
          stroke: false,
          fill: true,
          fillColor: '#EDF1F6',
          fillOpacity: 0.6,
          fillRule: 'evenodd',
          interactive: false,
        }}
      />
      {/* Thin shoreline so the clipped edge reads as a deliberate boundary. */}
      <Polygon
        positions={LAKE_POLYGON}
        pathOptions={{
          stroke: true,
          color: 'rgba(91, 119, 194, 0.45)',
          weight: 1,
          fill: false,
          interactive: false,
        }}
      />
    </>
  );
}
