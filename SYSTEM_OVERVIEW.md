# AlgaeWatch Villarrica — System Overview

What the system is, how the pieces fit, what it can honestly claim, and what it
cannot. Written to be read start to finish by someone who has never opened the
repository — including when the reader is preparing a presentation about it.

Status as of **2026-09-10**. TRL 2: a working end-to-end prototype on real data,
not a validated product.

---

## 1. The problem

Lake Villarrica (176 km², Araucanía, Chile) has recurring cyanobacterial algal
blooms. Blooms are a public-health and tourism problem, and the current
monitoring answer is in-situ sampling: someone takes a boat out, fills bottles,
and a laboratory returns numbers days later. That is accurate, slow, sparse in
space, and expensive.

The question this prototype asks is narrow and testable:

> Can freely available satellite imagery, plus weather, forecast the lake's algal
> index roughly seven days ahead **better than trivially guessing**?

The phrase "better than trivially guessing" is the whole methodological spine of
the project, and section 5 is about it.

---

## 2. What the system actually does

Four stages, each of which can be run and inspected on its own.

```
Sentinel-2 L2A  ──►  FAI per pixel  ──┐
(Copernicus, free)   src/features/    │
                                      ├──►  training table  ──►  model  ──►  API  ──►  dashboard
ERA5-Land       ──►  daily weather  ──┘     data/processed/      src/model/  backend/   frontend/
(Copernicus CDS)     src/features/
```

**Stage 1 — the satellite index.** Sentinel-2 passes over the lake every ~5 days.
For each cloud-free pass we compute the **Floating Algae Index (FAI)**, an
arithmetic combination of near-infrared and red bands that responds to floating
algal biomass. Water is isolated with the scene's own SCL classification band, so
land and cloud never enter the average. This is a published index, not something
invented here; no model is involved at this stage.

**Stage 2 — the weather.** ERA5-Land reanalysis supplies daily mean temperature,
accumulated precipitation and mean wind over the lake's bounding box. These are
the *change drivers*: an algal index tells you where biomass is now, weather is
part of what moves it.

**Stage 3 — the model.** A small PyTorch **quantile** network predicts each
pixel's standardised anomaly at a ~7-day horizon, and reports three quantiles
(10th, 50th, 90th) rather than a single number — so the output is a range with
stated confidence, not a false point certainty.

**Stage 4 — delivery.** A FastAPI backend serves the model and the collected data;
a React + Leaflet dashboard renders four views (Map, Stations, Trends, Model).

---

## 3. Where the numbers come from

Everything below is measured, from committed data, and reproducible by the
commands in `agents/validation/EVIDENCE_INDEX.md`.

| Quantity | Value |
|---|---|
| Cloud-free Sentinel-2 passes | **56** (2025-09-04 → 2026-08-22) |
| Water pixels sampled per pass | ~1,888 |
| ERA5-Land coverage | **13 months**, 56 matching days |
| Honest anchor→target training pairs | **56,668** |
| Distinct pixels / anchor dates | 1,866 / 34 |

"Honest" is load-bearing. **No row is interpolated, forward-filled or otherwise
invented.** If a pixel was clouded out on a date, that date simply has no row for
that pixel. An earlier version of this project inflated 363 real observations
into 1,356 training rows by forward-filling, which made the model look far better
than it was; a permanent automated check now refuses that (rule PR-3).

---

## 4. What is real and what is not

Being precise about this is more useful than overclaiming, especially in a
presentation where someone may ask.

| Component | Status |
|---|---|
| Sentinel-2 imagery and FAI | **Real.** Live scenes, real credentials, real water masking |
| ERA5-Land weather | **Real.** 13 months backfilled from the Copernicus CDS API |
| Model training and evaluation | **Real.** No mock data anywhere in the pipeline |
| Dashboard and API | **Real.** `mock_data.py` was deleted; every endpoint serves collected data |
| In-situ measurements (temp, pH, dissolved O₂) | **Absent.** Deliberate stub — the dashboard shows `—`, never a fabricated number. Blocked on SNIA data (BL-027) |
| The four "monitoring stations" | **Provisional.** Two of the four placeholder coordinates are not on the water (0.77 km and 0.98 km off), so their readings are shoreline vegetation. Real GPS is blocked on SNIA (BL-027) |
| Bloom classification (precision/recall/F1) | **Reported as `null`, with a reason.** See section 6 |

---

## 5. The methodological core: baselines

This is the part worth presenting, because it is what separates a demo from
evidence.

A model that reports "MAE 0.002" tells you nothing. The honest question is: **what
does the same number look like for a method that does no work at all?** Two such
methods are computed on exactly the same rows, in every evaluation:

- **Persistence** — "tomorrow looks like today." Predict the current FAI value.
- **Climatology** — "predict this pixel's own historical average," using only
  observations from *before* the prediction date.

A rule enforced by the test suite (**MI-1**) says a metric recorded without both
baselines beside it is not evidence and may not be entered in the evidence index.
The dashboard's Model view shows the comparison on screen, not just in a file.

Two further rules matter:

- **MI-2 — temporal embargo.** Training data must end before the validation
  target date. Otherwise the model has seen the future.
- **BL-016 — spatial hold-out.** Adjacent lake pixels are highly correlated, so
  random splits leak badly. Each evaluation fold holds out an entire geographic
  quadrant of the lake, and the model is scored on a region it never saw.

These are enforced by ~88 automated tests, not by good intentions.

---

## 6. The result, stated plainly

The per-pixel model, trained on all real inputs and evaluated under temporal
embargo plus spatial hold-out:

| | MAE (FAI units) |
|---|---|
| **Model** | **0.001999** ± 0.001501 |
| Persistence baseline | 0.001402 |
| Climatology baseline | 0.001296 |

**The model does not beat either baseline on the average.** That is the reported
result. It was not tuned toward a better number, and a low honest figure is
treated as a pass by the project's own gate while a high figure from a leaking
pipeline is treated as a failure.

The fold-by-fold detail is more interesting than the average, and is the honest
version of the story:

| Fold | Lake region held out | Model | Climatology | |
|---|---|---|---|---|
| 1 | NW | 0.001444 | 0.001543 | **beats** |
| 2 | NE | 0.004568 | 0.001882 | fails badly |
| 3 | SW | 0.001192 | 0.000929 | loses |
| 4 | SE | 0.000792 | 0.000828 | **beats** |

**Two of four folds beat climatology.** Fold 2 alone drags the unweighted average
past it. Fold 2's validation window is 2026-02-13 → 2026-03-08 — southern-
hemisphere late summer, the most volatile stretch in the whole series (target
standard deviation 2.35 against ~0.7 elsewhere). In other words:

> The model is least reliable exactly when the lake is most variable — which is
> precisely when a bloom forecast would matter.

That is the honest headline, and it is a better thing to say out loud than an
average that hides it.

**One result did work.** The 10th–90th percentile interval achieved **81.35%**
empirical coverage against a nominal 80%. The uncertainty quantification is well
calibrated even though the point forecast adds nothing over climatology at this
sample size. A calibrated "we don't know, and here is how much we don't know" is
a real deliverable.

**Classification is reported as `null`, on purpose.** The bloom threshold
inherited from earlier work (0.025916) is roughly ten times the highest per-pixel
FAI actually observed. Applied to real data it labels every row negative, which
would make precision, recall and F1 vacuously perfect. Rather than bake a wrong
threshold into training labels, the classification surface is reported as `null`
with the reason recorded in the artifact (rule MI-3).

---

## 7. Why it probably underperforms

Honest candidates, in rough order of likelihood:

1. **Sample size in time.** 56 passes over a year is 34 usable anchor dates. The
   56,668 rows are spatially numerous but temporally thin, and pixels within one
   date are far from independent.
2. **The target is hard.** Predicting a *standardised anomaly* means the model
   must beat "predict zero," which is exactly climatology. On a weakly
   autocorrelated signal that is a genuinely high bar.
3. **Weather is coarse.** ERA5-Land is a bounding-box mean. The lake is 176 km²;
   a single daily mean temperature may not resolve what drives local blooms.
4. **No in-situ ground truth.** Nutrients, temperature profile and dissolved
   oxygen are the actual bloom drivers and none are available yet (BL-027).

Note what is *not* on this list: leakage. Earlier versions of this project scored
much better precisely because they leaked, and the current gates exist to keep
that from happening quietly again.

---

## 8. Running it

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt

# Backend (needs data/processed/ and src/model/artifacts/, both committed)
.venv/Scripts/python -m uvicorn backend.app.main:app --port 8000

# Frontend
npm install --prefix frontend
npm run dev --prefix frontend        # http://localhost:5173
```

Credentials live in a `.env` **one directory above the repository**, so the file
with real secrets is structurally outside the Git tree rather than merely
ignored. Only the data collection scripts need them; the dashboard runs from
committed data with no credentials at all.

To reproduce the model from scratch:

```bash
.venv/Scripts/python scripts/collect_era5.py             # ~50 min, CDS queue
.venv/Scripts/python scripts/build_per_pixel_dataset.py  # ~30 s, no API
.venv/Scripts/python scripts/train_per_pixel.py          # the verdict
```

---

## 9. What would make this a product

In dependency order:

1. **Real station coordinates and in-situ data** from SNIA (BL-027). This unblocks
   both ground truth and the four station cards the dashboard currently cannot
   fill.
2. **A longer satellite history.** 2024–2026 rather than one year, which roughly
   triples the anchor dates.
3. **Recalibrate the bloom threshold** on the real per-pixel distribution, so the
   classification surface can be reported at all.
4. **Field validation.** Nothing here has been checked against an observed bloom.
   Until it is, TRL 2 is the correct label.

---

## 10. Where to look in the repository

| Question | File |
|---|---|
| Current state, what to do next | `agents/RUN_STATE.md` |
| Every number, with a command that reproduces it | `agents/validation/EVIDENCE_INDEX.md` |
| Why a decision was made | `agents/adrs/` |
| The satellite index | `src/features/fai.py` |
| Weather | `src/features/era5.py` |
| The model | `src/model/per_pixel.py` |
| The rules that keep it honest | `src/model/integrity.py`, `tests/test_model_integrity.py` |
