# Tech Stack

## Existing Stack

| Layer | Technology | Status |
|---|---|---|
| Satellite ingestion | `sentinelhub-py` against Copernicus Data Space Ecosystem, Sentinel-2 L2A | Keep. Audited and correct |
| Weather ingestion | `cdsapi` against ERA5-Land | Keep, unused. Licence accepted, backfill never run (BL-012) |
| In-situ ingestion | Explicit stub | Keep as a stub. SNIA CSVs never arrived |
| Raster handling | `numpy`, `rasterio`, `xarray` | Keep |
| Feature table | `pandas` | Keep |
| Model | scikit-learn Gradient Boosting | **Replace** with PyTorch, per ADR 0002 |
| Model persistence | `joblib` | Revisit under PyTorch; a state-dict checkpoint is the natural replacement |
| API | FastAPI with `uvicorn`, read-only, five routers | Keep |
| Frontend | React 18, Vite 5 | Keep |
| Map | Leaflet, `react-leaflet`, `leaflet.heat`, Esri World Imagery tiles | Keep provisionally, per ADR 0003 |
| AI prose | Gemini 2.5 Flash via `httpx`, server-side, deterministic fallback | Keep. Must never compute a number |

## Proposed / Accepted Stack

The only accepted stack change is the modelling layer.

**Accepted:** PyTorch replaces scikit-learn as the shipped model, adopted
together with the per-pixel redesign rather than independently. See ADR 0002 for
why the two are coupled, and ADR 0004 for the redesign itself.

Near-term target: a multilayer perceptron over per-pixel features with three
quantile output heads trained under pinball loss, producing pessimistic,
expected and optimistic trajectories from a single model. Longer-term, and
explicitly out of scope before the pitch: a convolutional recurrent model over
the raster sequence, currently blocked by timestep depth, irregular sampling
intervals, and cloud dropout.

scikit-learn is retained for data preparation, metrics, and baseline
computation. It stops being the shipped model.

`xgboost` appears in `requirements.txt` and is imported nowhere. It should be
removed (BL-018, ASM-011).

## Stack Decision Rules

- If the project already has a mature stack, respect it.
- If the project is immature, suggest improvements and ask for approval.
- If the project has no stack, propose context-fit options and ask.
- Record major stack decisions in ADRs.

### Project addendum

- The ingestion layer passed audit and is not a candidate for replacement. The
  temptation to rewrite working satellite code alongside the broken model layer
  should be resisted.
- Any dependency added must preserve the property that the backend and dashboard
  run with **zero credentials** against the committed CSVs and artifacts. This is
  what makes the project demonstrable without network access, and it is worth
  protecting.
- Frontend dependencies should not deepen Leaflet coupling while ADR 0003 stays
  provisional.

## Deployment Target

Deferred. GATE-DEPLOY is inactive.

Local run only:

```bash
uvicorn backend.app.main:app --reload
```

```bash
npm --prefix frontend run dev
```

No hosting target, container, or CI has been selected, and none is in scope
before the pitch.
