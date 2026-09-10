# Frontend Credibility Pass — WI-009

Author: `lq` · 2026-09-10 · Verdict: **done, GATE-PQ evidence attached**

Covers BL-009, BL-010, BL-013, BL-019, BL-021. All changes are under
`frontend/`; no backend file was touched (ADR-sf-0005 disjoint-files rule).
Design-handoff deviations are recorded in ADR-lq-0007.

## Environment

- Backend: `.venv/bin/python -m uvicorn backend.app.main:app --port 8000`, real
  data (`data/processed/fai_series_raw.csv`, `src/model/artifacts/`), zero
  credentials.
- Frontend: `npm --prefix frontend run dev` (Vite 5, port 5173).
- Screenshots taken with the slider at 10 sep 2026 — 19 days past the last real
  Sentinel-2 pass (22 ago 2026), i.e. the forward-filled / projected case, so the
  BL-013 disclosures are all visible.
- `npm --prefix frontend run build` passes (95 modules, no warnings).
- Browser console: no errors or warnings across all four views.

## BL-010 — risk overlay clipped to the lake  ✔

**Before:** `leaflet.heat` rendered `/risk/grid` points with a screen-space
radius/blur that bled well past the shoreline; risk was painted as a rectangular
blob over land.

**Change:** `frontend/src/data/lakePolygon.js` (Lago Villarrica shoreline, OSM
relation 1922935, stitched + Douglas–Peucker to 133 vertices) and
`frontend/src/components/MapView/LakeMask.jsx` — an inverse land mask
(`[worldRing, lakeHole]`, `fillRule: evenodd`, `#0a0a0d` at 0.74) laid over the
heat layer, plus a 1px shoreline stroke. Heat radius/blur trimmed 22/20 → 20/18,
`minOpacity` 0.30 → 0.25. Library-agnostic: the same polygon drives a Mapbox fill
layer unchanged (ADR 0003).

**Evidence:** `frontend_credibility_pass_screens/01-bl010-overlay-clipped-to-lake.jpg`,
`02-bl009-magma-ramp-map.jpg`, `07-bl021-reduced-glass-halos.jpg`.

## BL-009 — colourblind-safe sequential risk scale  ✔

**Before:** `#64D2FF / #30D158 / #FF9F0A / #FF453A`. Ran the dataviz validator on
it (`--ordinal`, surface `#0a0a0d`): FAIL on lightness monotonicity
(`[0.817, 0.756, 0.782, 0.663]`), FAIL on adjacent ΔL (BAJO→MEDIO 0.027), FAIL on
single hue (161° spread).

**Change:** four stops from `magma` (t ≈ 0.44 / 0.57 / 0.69 / 0.82) —
`#93318A / #D0466B / #F47355 / #FCAC3D` — in `utils/risk.js` (+ new `RISK_RAMP`),
`styles/tokens.css`, and the heat gradient / legend bar which now derive from
`RISK_RAMP`. Liveness dot moved to its own `--status-live` / `--status-stale`
tokens. Risk numbers now render in text ink with a coloured dot, not in the ramp
colour (`AnalyticsPanel`, `StationsView`).

Validator on the new scale:

```
$ node scripts/validate_palette.js "#93318A,#D0466B,#F47355,#FCAC3D" \
    --mode dark --surface "#0a0a0d" --ordinal
  [PASS] Lightness monotone     steps read light→dark
  [PASS] Adjacent ΔL            all gaps >= 0.06
  [PASS] Light-end contrast     #93318A at 2.87:1 vs surface
  [PASS] Single hue             hue spread 36°
  → ALL CHECKS PASS
```

CVD simulation, adjacent-pair ΔE (OKLab ×100, Machado 2009, severity 1.0):

| pair | normal | protan | deutan | tritan |
|---|---|---|---|---|
| MUY_BAJO→BAJO | 15.1 | 12.4 | 16.0 | 14.3 |
| BAJO→MEDIO | 13.3 | 14.0 | 12.8 | 9.2 |
| MEDIO→ALTO | 14.2 | 14.9 | 10.8 | 12.2 |

Worst pair 9.2, above the ΔE ≥ 8 target. OKLCH L strictly monotonic
(0.48 → 0.59 → 0.70 → 0.80), chroma ≥ 0.156.

**Evidence:** `02-bl009-magma-ramp-map.jpg`, `03-bl009-estaciones.jpg`.

## BL-013 — staleness disclosure beyond the header  ✔

**Before:** only the header flagged a stale last pass. The slider, map, station
cards and station popup presented forward-filled values as current — the station
cards even labelled the slider date "ÚLTIMA MEDICIÓN".

**Change:** `utils/staleness.js` (`passAgeLabel`, `projectionGapDays`);
`useAppData` exposes `lastPassDate` and `selectedIsProjected`.

- Slider: "FECHA SELECCIONADA · PROYECCIÓN" + "Sin pasada satelital · valor
  arrastrado desde la última".
- Map: persistent "Grilla FAI · pasada 22 ago 2026 · hace 19 d" and, when
  projected, "Riesgo proyectado +19 d sobre la última pasada".
- Stations view: sub-header spelling out the projection, and the per-card field
  relabelled "ÚLTIMA PASADA" showing the real pass date + "proyección +19 d".
- Station popup: "PASADA 22 ago 2026 · PROY. +19 d".

**Evidence:** `05-bl013-staleness-map-popup.jpg`, `06-bl013-staleness-estaciones.jpg`.

## BL-019 — mandated TRL-2 seal rendered  ✔

**Before:** `TRL 2 · resultados no validados en campo` existed only as the default
arg to `m.get("caveats", …)` in `backend/app/routers/model_metrics.py`;
`metrics.json` always populates `caveats`, so the seal never rendered.

**Change:** `ModelView.jsx` renders the seal as (a) an amber pill badge under the
view title and (b) a bold prefix on the VALIDACIÓN card's disclaimer line,
followed by the run-specific `caveats` — matching the handoff's line shape
("`TRL 2 · resultados no validados en campo; …`"). Fixed literal, like the
AI-panel disclaimer in `forecast.py`. Backend untouched; its dead default noted
in ADR-lq-0007 for `sf`.

**Evidence:** `04-bl019-trl2-seal-modelo.jpg`.

## BL-021 — reduce generated-default visual excess  ✔ (floor)

**Change:** removed the two `filter: blur(10px)` halo `<div>`s (`App.jsx`,
`app.css`); shell keeps one restrained radial accent. `.glass-panel` /
`.glass-content` blur 18px+saturate → 6px, panel surfaces raised to
`rgba(24,24,27,0.78–0.82)`. AI panel: dropped the blue→green gradient and 30px
glow for a flat tint + accent edge. "Remove the excess" floor, not a full
restyle.

**Evidence:** `07-bl021-reduced-glass-halos.jpg`.

## Superseded by the light-theme pass (same day)

Later on 2026-09-10 the owner redirected the frontend to a **light pastel theme**
(ADR-lq-0008, WI-011). That pass replaces the dark magma ramp above with a
light-surface pastel ramp:

| Level | dark (this pass) | light (ADR-lq-0008) |
|---|---|---|
| MUY_BAJO | `#93318A` | `#EAC49B` |
| BAJO | `#D0466B` | `#E0A074` |
| MEDIO | `#F47355` | `#C9765A` |
| ALTO | `#FCAC3D` | `#A05445` |

```
$ node scripts/validate_palette.js "#EAC49B,#E0A074,#C9765A,#A05445" \
    --mode light --surface "#F6F8FA" --ordinal
  [PASS] Lightness monotone   [PASS] Adjacent ΔL   [PASS] Single hue (36°)
  (light-end contrast is a WARN by the ordinal rule — the pale low stop is a
   sequential "near-zero" anchor, not a text colour; a darker `ink` step per
   level covers small text on white)
```
CVD adjacent ΔE (Machado 2009): worst 8.5 (deutan MUY_BAJO→BAJO); all others ≥ 9.
BL-010 clipping, BL-013 disclosures and the BL-019 seal carry over unchanged;
BL-021 is subsumed (all glass/halos removed, not just trimmed).

## Known follow-ups (out of scope here)

- `numEs` renders near-zero negatives as "-0,000" (Toltén FAI). Cosmetic,
  `utils/format.js`, touches many call sites.
- `ModelView` confusion-matrix cell colours still use the old
  green/amber/red/blue. They encode matrix categories (TP/FP/FN/TN), not the risk
  scale, so out of BL-009 scope — but the green/red pair has the same CVD issue
  and could move to the dataviz status palette later.
- `agents/RUN_STATE.md` (and its `.es.md` sibling) still say "awaiting user
  acceptance" / ADR 0003 pending / WI-009 not started. `sf` to refresh on the
  next harness pass: harness accepted 2026-09-10, local half mounted, ADR 0003
  Accepted, WI-008 and WI-009 done.
