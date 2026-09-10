# Session Handoff — `demoday` demo-prep pass

Written 2026-09-10 at the end of a demo-preparation session. Everything
described here is **committed and pushed to `origin/demoday`**. Nothing is
merged to `main`.

Four commits, oldest first:

| Commit | What |
|---|---|
| `742cdb6` | Frontend polish, model switch, TRL-2 seal removed, satellite backdrop, error boundaries |
| `60a7d24` | Candidate alert threshold recalibrated to the water scale (BL-039) |
| `1badabc` | FAI grid rendered as a raster instead of a density heatmap |
| `1c9012e` | Continuous colour ramp on that raster |

Gate status at handoff: `pytest -q` **103 passed / 8 xfailed**; GATE-MODEL
**9 passed / 8 xfailed** (unchanged all session); GATE-I18N **0 problems**;
`harness_doctor --strict` **0 blockers**, 4 pre-existing warnings about
`data/raw/era5` which does not exist in a fresh checkout.

## The one thing that matters most

**The dashboard still does not predict anything on the dates where prediction is
the entire point.**

The slider spans 372 days. Only **56** have a real Sentinel-2 pass. On the other
**316 (85%)**, `/risk` carries the last known FAI forward and the header says so
out loud: *"Sin pasada satelital · valor arrastrado desde la última."*

Carrying the last value forward **is the persistence baseline** — the same
baseline both models are measured against and both lose to. So the product
currently ships persistence as its map, on 85% of its dates, while showing a
Modelo view that explains at length why persistence is the thing to beat.

The owner asked the right question and it is still open: *shouldn't at least one
of the models actually predict the number we are showing?*

### What that would take

The candidate is a per-pixel model. Its natural output is a grid, and a grid is
exactly what the map wants. Concretely:

1. Extend `scripts/predict_per_pixel_forecast.py` to also write **per-pixel**
   predictions (it currently aggregates to 4 stations + a lake row before
   writing). Keep `pixel_id`, `lat`, `lng`, `fai_q50` per anchor.
2. Add `/risk/grid?model=candidate&date=…`, serving the predicted grid for the
   anchor covering that date instead of the frozen pass.
3. Add `model` to `/risk` the same way, so markers and the station list follow
   the switch too. `get_candidate_forecast` in `backend/app/data_source.py`
   already shows the shape to copy.
4. Frontend: `RiskGridLayer` already takes a plain `{lat,lng,risk}[]`, so it
   needs no change — only the fetch does.

**Honesty constraint that must not be dropped:** the candidate loses to
persistence (MAE 0.001999 vs 0.001402). A model-driven map will therefore be, on
measured average, *worse* than the forward-fill it replaces. That is still worth
building and showing — it is the honest demonstration of where the project is —
but it must be **labelled**, never silently swapped. Rule MI-1.

## Everything else open, roughly in priority order

1. **BL-038 — the station popup shows three fields it can never fill.**
   `StationCard.jsx` renders TEMP. AGUA, pH and OXÍGENO DISUELTO, all of which
   are `null` until the SNIA CSVs arrive (`src/features/insitu.py` is a stub,
   PR-3). Three of four fields are permanently a dash and it reads as broken.
   The temperature/pH sparklines already solve this correctly by hiding behind
   `hasInSitu` — copy that, or label the fields "pendiente SNIA".
2. **The risk ramp is blue → green, and green is HIGH.** Owner's explicit
   request. It inverts the universal "green means safe" reading and a demo
   audience may misjudge it. It was also hand-picked and **not** re-validated
   with the dataviz `validate_palette` tool the previous magma ramp was checked
   against. Both caveats are written into `GATES.md` under GATE-PQ; neither is
   resolved. Colours live in `frontend/src/utils/risk.js` and
   `frontend/src/styles/tokens.css` (`pin` is the map-surface variant).
3. **`AGENTS.md` PR-4 was amended to withdraw the TRL-2 seal requirement**
   (ADR-lq-0010, owner decision). The AI-panel disclaimer requirement stands and
   is untouched. If anyone wants the seal back, that ADR lists every touch point.
4. **BL-027 still poisons the legacy model.** Two of four station coordinates
   sit off the water on shoreline vegetation, which is why pucón and sur read
   ALTO permanently while norte and toltén read MUY_BAJO permanently. The legacy
   threshold is measuring *whether a coordinate landed on a plant*. Blocked on
   real GPS from SNIA.
5. Deferred and previously noted: no URL state for view/date, no prefetch of
   adjacent dates, the analytics panel does not auto-collapse below ~1100px.

## Traps this session hit, so you do not hit them again

- **`station_id` in `per_pixel_anomaly_dataset.csv` is NOT a dashboard station.**
  Under ADR 0004 D3 it is the per-pixel training unit and equals `pixel_id`.
  Aggregating on it silently produces 1,860 one-pixel "stations". Assign to
  dashboard stations from coordinates against `src/features/stations.py`.
- **Do not reuse `fai_alert_threshold` (0.025916) for per-pixel values.** It was
  calibrated on vegetation-contaminated station points and is ~6.6× the p99 of
  real water FAI, so it flattens every prediction to the bottom of the scale.
  ADR-sf-0008 warned about this and it was implemented wrong anyway. The
  candidate's water-scale threshold is computed in
  `scripts/predict_per_pixel_forecast.py` (`ALERT_PERCENTILE`).
- **`leaflet.heat` renders point *density*, not values.** On a regular grid the
  intensities of overlapping points sum and saturate the gradient, painting the
  whole lake at max risk regardless of the data. It has been replaced by
  `RiskGridLayer.jsx` (one canvas-rendered cell per pixel). Do not reintroduce a
  heatmap for a scalar field.
- **Leaflet caches container size and only recomputes on *window* resize.**
  Collapsing the analytics panel resizes the container without touching the
  window, so the map kept drawing at the old width. `AutoResize` in
  `LeafletMap.jsx` fixes it with a `ResizeObserver`; keep it.
- **A `z-index: -1` pseudo-element cannot sit behind an opaque ancestor
  background.** Negative-z-index children paint *before* block-level descendants'
  backgrounds, so `#root`'s solid colour covered the lake backdrop entirely. It
  now lives on `body` itself with `#root` transparent (`tokens.css`).
- **Editing `AGENTS.md` or `agents/RUN_STATE.md` stales their Spanish siblings**
  and fails GATE-I18N. Translate the changed section and re-record `source_sha`
  (LF-folded git blob sha; `agents/check_translations.py` explains the hashing).
- **Routers are called directly from tests**, so a `= Query(...)` default arrives
  as the sentinel object. Use `Annotated[T, Query(...)] = default` instead — see
  `backend/app/routers/forecast.py`.

## Running it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm --prefix frontend install

.venv/bin/uvicorn backend.app.main:app --reload --port 8000
npm --prefix frontend run dev            # http://localhost:5173
```

`agents/local/CAPABILITIES.md` is gitignored and every fresh checkout must
re-create it (GATE-LOCAL) — copy `agents/templates/capability-scan-template.md`.

Regenerating the candidate's predictions after a retrain:

```bash
.venv/bin/python scripts/predict_per_pixel_forecast.py
```

## Verify

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q tests/test_model_integrity.py   # GATE-MODEL
.venv/bin/python agents/check_translations.py                 # GATE-I18N
.venv/bin/python agents/harness_doctor.py --root . --strict
npm --prefix frontend run build
```

Both models, side by side, at the same date:

```bash
curl -s "localhost:8000/forecast?date=2026-01-18&model=legacy"
curl -s "localhost:8000/forecast?date=2026-01-18&model=candidate"
```

The divergence is the demo: legacy reports pucón 81 / sur 69 ALTO from shoreline
vegetation; the candidate reports sur 33 in summer and single digits in winter,
from water pixels only.
