# ADR-lq-0007: Frontend credibility pass — deviations from the design handoff

## Status

Accepted 2026-09-10 by `lq` (owns the frontend half, ADR-sf-0005).

## Context

WI-009 / GATE-PQ required a frontend credibility pass: BL-009 (risk palette),
BL-010 (overlay clipping), BL-013 (staleness disclosure), BL-019 (TRL-2 seal),
BL-021 (visual excess). PR-4 makes
`design_handoff_algaewatch_villarrica/README.md` the frontend source of truth
and requires that deviations from it be recorded as ADRs. Three of the five
items deviate from the handoff; this ADR records them. ADR 0003 (Leaflet over
the mandated Mapbox) was settled first and is unaffected.

## Decision

### D1 — Risk scale: magma-family sequential ramp (BL-009)

The handoff specifies a four-stop qualitative scale — `#64D2FF` blue, `#30D158`
green, `#FF9F0A` orange, `#FF453A` red — and calls the risk colour scale
normative. It is replaced with four stops sampled from the `magma`
perceptually-uniform sequential ramp:

| Level | Was | Now |
|---|---|---|
| MUY_BAJO | `#64D2FF` | `#93318A` |
| BAJO | `#30D158` | `#D0466B` |
| MEDIO | `#FF9F0A` | `#F47355` |
| ALTO | `#FF453A` | `#FCAC3D` |

Why the old scale fails: it is not perceptually uniform (OKLCH lightness runs
0.82 → 0.76 → 0.78 → 0.66, non-monotonic), and BAJO→MEDIO differ in lightness by
only 0.027 — green / orange / red are the confusable set for the commonest
colour-vision deficiencies, on what is nominally a public-health signal.

Why the new one holds: single hue family (~36° spread), OKLCH lightness strictly
monotonic (0.48 → 0.59 → 0.70 → 0.80), every adjacent pair ≥ 9.2 ΔE (OKLab ×100)
under normal, protanopia, deuteranopia and tritanopia simulation (Machado 2009).
Validated with the dataviz skill's `validate_palette.js --ordinal` against the
app surface `#0a0a0d` — all four ordinal checks pass. ALTO is the brightest stop,
so it is the most prominent mark on the dark map; urgency that the old red
carried by hue is now also carried by the existing ALTO pulse-ring and the
stations-in-alert count, not by colour alone.

Corollary: the header liveness dot was reading the risk tokens
(`--risk-bajo` / `--risk-medio`). It now has its own `--status-live` /
`--status-stale` tokens, so the risk scale is genuinely reserved for risk as the
handoff's own token comment already claimed.

Corollary: risk *values* ("98/100") are rendered in text ink with a coloured dot
beside them, not in the ramp colour — the darkest ramp stop is 2.9:1 on the
surface, fine for a mark, low for small text.

### D2 — Panel treatment: near-opaque surfaces, minimal blur (BL-021)

The handoff's glass surface (`backdrop-filter: blur(18px) saturate(140%)` on
every top-level panel) plus two `filter: blur(10px)` accent halo `<div>`s is the
generated-default idiom GATE-PQ flags. The halos are removed; the shell keeps one
restrained radial accent in its background gradient. Panels move to
`rgba(24,24,27,0.80-0.82)` with `blur(6px)`. The AI panel loses its blue→green
gradient fill and 30px outer glow for a flat tint with a single accent edge. The
"remove the decorative excess" floor from BL-021, not a full restyle.

### D3 — Additions that are not deviations

- **BL-010** clips the risk overlay to a Lago Villarrica polygon (OSM relation
  1922935, simplified to 133 vertices) via an inverse land mask. The handoff
  explicitly asks for this ("recortar el overlay a la superficie del lago … una
  capa `fill` inversa sobre tierra"); it was simply unimplemented.
- **BL-013** adds pass-age disclosure to the slider, map, station cards and the
  station popup. Additive to the handoff, which only specifies the header's
  "última actualización".
- **BL-019** renders the mandated `TRL 2 · resultados no validados en campo`
  seal, which PR-4 requires and which was unreachable dead code. The seal text
  is a fixed literal in `ModelView.jsx`, mirroring how the AI-panel disclaimer
  lives as a literal in `backend/app/routers/forecast.py`. The run-specific
  `caveats` string still renders alongside it — different texts, both kept.

## Consequences

- The handoff and the code now disagree on the risk palette and the panel
  treatment in a documented way. Anyone re-checking fidelity against the handoff
  should read this ADR first.
- `frontend/src/utils/risk.js` gains `RISK_RAMP` (ordered low→high) so the
  heatmap gradient and legend bar derive from the same four tokens.
- The backend is untouched. `backend/app/routers/model_metrics.py` still carries
  the misleading `m.get("caveats", "<seal>")` default; it is now confirmed dead
  (metrics.json always populates `caveats`) and `sf` may simplify it when next in
  that file. Left alone here to keep the two halves' files disjoint (ADR-sf-0005).
- If the original design intent for a *qualitative* risk scale is reasserted, D1
  is a pure token change and this ADR is the place to revisit it.

## Evidence

- `agents/reviews/20260910/frontend_credibility_pass.lq.md` — the pass, item by
  item, with before/after description and screenshots.
- `agents/reviews/20260910/frontend_credibility_pass_screens/` — screenshots of
  the running app (backend + frontend, real data, slider at a projected date).
- Palette validation: `validate_palette.js --ordinal` output reproduced in the
  review document.

## Sources

- SRC-004 — `design_handoff_algaewatch_villarrica/README.md` (risk scale §Fidelity,
  glass surface §Cabecera, map overlay §"Vista 1 — Mapa", seal §"los datos
  provienen de satélite")
- PR-4 — deviations recorded as ADRs
- ADR 0003 — map library (settled separately)
- ADR-sf-0005 — the frontend/model split and the disjoint-files rule
- `agents/planning/BACKLOG.md` — BL-009, BL-010, BL-013, BL-019, BL-021
- dataviz skill — its `color-formula` reference and its `validate_palette`
  script (bundled with the skill, not part of this repository)
