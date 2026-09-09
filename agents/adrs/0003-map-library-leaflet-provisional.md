# ADR 0003: Keep Leaflet as the map library (provisional)

## Status

Accepted — provisional. Deliberately reversible pending consultation with the
original author.

## Context

The design handoff (SRC-004) specifies Mapbox GL JS, style
`satellite-streets-v12`, a `heatmap` layer coloured by risk, and a
`MAPBOX_ACCESS_TOKEN` supplied from the environment.

The implementation instead uses Leaflet with `react-leaflet` and `leaflet.heat`.
The code carries a one-line rationale at `frontend/src/components/MapView/LeafletMap.jsx:9`
describing a "free Leaflet + raster-tile stack (no token required)", but the
deviation was never recorded as a decision.

Inspection shows the deviation is better reasoned than the bare library swap
suggests. The basemap is Esri World Imagery satellite tiles with an Esri
boundaries and places overlay — satellite imagery with labels, which is the same
visual outcome the handoff specified Mapbox for, obtained without an account,
token, or request quota.

What Mapbox would still add: vector tiles with smoother zoom behaviour, and
easier clipping of the risk overlay to the lake polygon.

What it would cost: a new credential, a rewrite of the MapView components, and
hours competing directly with the model work before the pitch.

## Decision

Keep Leaflet. Record the deviation from SRC-004 rather than silently continuing it.

Hold this decision **provisional** and avoid work that would make a later
migration to Mapbox expensive. The original author has not yet been consulted,
and the owner has asked to keep the Mapbox option open for as long as practical.

Practically, until the decision is confirmed:

- Do not spread Leaflet-specific assumptions beyond the MapView components.
- Keep the risk-overlay data contract library-agnostic — a list of
  latitude/longitude/risk points, which both `leaflet.heat` and a Mapbox
  `heatmap` layer can consume unchanged.
- Treat the colour ramp and the lake-clipping fix as library-independent work,
  because both are required under either choice.

## Consequences

- No new credential is introduced, and the project's credential-free local run is
  preserved.
- The frontend keeps working against the real FAI grid with no migration.
- The handoff and the code now disagree in a documented way rather than an
  invisible one.
- A late reversal to Mapbox remains possible at bounded cost, because the
  constraints above deliberately limit Leaflet's blast radius.
- Two genuine handoff requirements remain unmet and are independent of this
  decision, so they are filed as backlog rather than resolved here: clipping the
  risk overlay to the lake surface, and replacing the risk colour ramp.

## Revisit Trigger

Revisit when the original author responds, or before any substantial frontend
work begins — whichever comes first.

## Sources

- SRC-004 — `design_handoff_algaewatch_villarrica/README.md`, map implementation section
- CONF-003 — recorded conflict in `agents/intake/SOURCE_MANIFEST.md`
- `frontend/src/components/MapView/LeafletMap.jsx` — Esri tile layers
- `frontend/src/components/MapView/HeatLayer.jsx` — `leaflet.heat` configuration
