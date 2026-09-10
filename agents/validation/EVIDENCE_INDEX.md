# Evidence Index

Every figure quoted in `PROJECT_BRIEF.md`, ADR 0004, and the pitch narrative is
reproducible from committed data. The commands below are the reproduction path.
All run from the repository root and require no credentials.

| ID | Date | Evidence | Proves | Location |
|---|---|---|---|---|
| EV-001 | 2026-09-09 | Bloom rate by station: sur 0.979, pucon 0.501, norte 0.000, tolten 0.000 | The label encodes location, not blooms (ADR 0004 D2) | `data/processed/training_dataset.csv` |
| EV-002 | 2026-09-09 | Station-name rule scores precision 0.97 / recall 0.74 / F1 0.84 against the model's 0.84 / 0.47 / 0.60 | A rule using no satellite data beats the trained classifier (rule MI-1) | Same, holdout partition |
| EV-003 | 2026-09-09 | Persistence MAE 0.00603 against the regressor's 0.00865 | The regressor is 43% worse than predicting no change | Same, holdout partition |
| EV-004 | 2026-09-09 | 1,356 rows resolve to 363 unique (station, fai_now, fai_future) combinations; 85.3% of rows have `fai_now` equal to `fai_lag_1d` | Training rows were fabricated by forward-fill (rule PR-3) | Same |
| EV-005 | 2026-09-09 | Last training date and first holdout date are both 2026-06-09 | The temporal holdout leaks at the seam; no embargo (rule MI-2) | Same |
| EV-006 | 2026-09-09 | No tracked secrets; no secret-shaped strings across all commits | Credential hygiene is clean (rule PR-2) | Git history |
| EV-007 | 2026-09-09 | 56 real pass dates, 2025-09-04 to 2026-08-22; median gap 3 days, maximum 32; 11 exact seven-day pairs, 35 within a 5-to-9-day window | Honest sample size is 44 to 140 at station granularity, motivating ADR 0004 D3 | `data/processed/fai_series_raw.csv` |
| EV-008 | 2026-09-09 | 1,860 water pixels in a single pass; 35 usable date pairs implies roughly 65,000 per-pixel samples | The per-pixel redesign resolves the sample-size wall | `data/processed/fai_grid_latest.csv` |
| EV-009 | 2026-09-09 | Thresholding `fai_now` reproduces the `bloom_7d` label on 90.0% of rows; correlation between `fai_now` and `fai_future` is 0.758 | The classifier re-reads the present rather than forecasting | `data/processed/training_dataset.csv` |
| EV-010 | 2026-09-09 | Harness kernel cloned from branch `testing`, commit `a5f428d`, byte-identical to the copies installed in two other local projects | The mounted harness derives from the intended kernel version | `agents/reviews/20260909/capability_scan.md` |
| EV-011 | 2026-09-09 | 218 non-null station readings, not 224: pucon 54, norte 56, tolten 54, sur 54. Six cells are null where no water pixel was found | Corrects a figure that had been stated as 56 x 4 assuming no gaps | `data/processed/fai_series_raw.csv` |
| EV-012 | 2026-09-09 | 2,479 lines of Python, JavaScript and JSX (1,503 Python); 2,924 including CSS | Corrects an unsourced size figure | Working tree |
| EV-014 | 2026-09-10 | Distance from each station coordinate to the nearest sampled water pixel: tolten 0.07 km, norte 0.15 km, **pucon 0.77 km, sur 0.98 km**. `sur` lies south of the lake's southernmost water pixel. On the 2026-08-22 scene the lake mean FAI is 0.000267 and 0.38% of 1,860 water pixels clear the bloom threshold, while `fai_pucon` reads 0.0585 and `fai_sur` 0.0567 — both above that same scene's p99 of 0.0019 | Two of the four station sample points are not on the lake, and their readings are shoreline vegetation. This is upstream of EV-001: the label is close to "is this station sur or pucon", and the pooled threshold is calibrated on the contamination | `data/processed/fai_grid_latest.csv`, `data/processed/fai_series_raw.csv`, `src/features/stations.py` |
| EV-015 | 2026-09-10 | The CDSE token endpoint returns HTTP 200 with an `access_token` for the credentials in `.env` | Copernicus Data Space access is available. The WI-002 credential blocker recorded in `RUN_STATE.md` was stale | `.env`, one directory above the repository root |
| EV-016 | 2026-09-10 | `python -m pytest -q` reports 36 passed, 7 xfailed | The baseline and integrity checks are permanent and re-runnable, satisfying BL-002. The seven xfails are the GATE-MODEL checks the legacy dataset does not pass; they are `strict`, so a fix reports XPASS as a failure | `tests/` |
| EV-017 | 2026-09-10 | `torch 2.14.0+cu126`, `torch.cuda.is_available()` true, GeForce GTX 1650 (sm_75, 4.3 GB), GPU matmul executed | PyTorch is installed with working CUDA, clearing WI-010 / BL-024 on the owner's machine | Local environment; recorded in `agents/local/CAPABILITIES.md` |
| EV-018 | 2026-09-10 | `agents/RUN_STATE.es.md` recorded `source_sha` `28592ee…`, which is the blob sha of `agents/RUN_STATE.md` with **CRLF** line endings; the LF sha, and the committed blob, is `ef31b0a…`. `git cat-file -t 28592ee…` fails — it names no object in the repository. The Spanish text itself is a complete and current translation of that source: the section structure matches 1:1 and the paragraph added in `c3beadf` is present | GATE-I18N failed on a translation that was not stale. `--no-filters` hashes the bytes on disk, so the recorded hash depends on how the file was written, not on the commit — the previous session's working copy was CRLF, every checkout since is LF under `.gitattributes`. `check_translations.py` now normalizes line endings before hashing, and the protocol says so. The gate was fixed before the hash was re-recorded, per the rule in `GATES.md` | `agents/check_translations.py`, `agents/i18n/TRANSLATION_PROTOCOL.md`, `.gitattributes` |
| EV-019 | 2026-09-10 | Pairing each of the 56 real pass dates in `fai_series_raw.csv` with a later date 5 to 9 days out, nearest to 7, yields **35 honest pairs** (horizons 5d×10, 6d×1, 7d×11, 8d×13). On those pairs, persistence MAE is **0.001333** and a causal expanding-mean climatology MAE is **0.000945** | The lake-wide signal admits an honest retrain without station coordinates, at 35 rows. And climatology **beats** persistence here — the reverse of the station table, where the trivial rule was the leak. Any lake-wide model must clear 0.000945, not 0.001333, so `check_beats_persistence` alone is too weak a bar (BL-029 sequence, ADR-sf-0008). 18 of the 35 dates serve as both a target and a feature anchor, which is BL-033 | `data/processed/fai_series_raw.csv` |
| EV-020 | 2026-09-10 | `lake_mean_fai` over all 56 dates spans **−0.008248 to +0.001999**, median 0.000162. The bloom threshold recorded in `src/model/artifacts/metrics.json` is **0.025916** | The threshold sits an order of magnitude above the lake-wide maximum, because it was calibrated on the contaminated station series (ADR-sf-0007). Applied to lake-wide data it labels every row negative, so `bloom_7d` is constant and the whole classification surface — two of the seven gate checks and four of five `ValidationMetrics` fields — becomes vacuous. A lake-wide retrain must recalibrate or report those figures as `null` under PR-3, never compute them from a constant label | `data/processed/fai_series_raw.csv`, `src/model/artifacts/metrics.json` |
| EV-021 | 2026-09-10 | WI-005 built (ADR-lq-0009). `build_pairs` reproduces EV-019's 35 pairs; `min_prior` from 0 to 7 all keep **34** pairs (only the 2025-09-06 anchor drops — one prior pass, below the floor of 2), so the choice is insensitive — set to 5. The interim Ridge retrain scores **`mae_fai` 0.003919 ± 0.002135 (4-fold expanding CV)** against **persistence 0.001362** and **climatology 0.000775** on the same folds: `beats_baselines` is `{persistence: false, climatology: false}`. Every alpha (0.1–100) and feature subset tried loses to both. `precision/recall/F1/AUC` are `null` (EV-020). Pointing GATE-MODEL at the candidate table → **11 passed, 1 skipped, 4 xfailed**: passes `no_fabricated_rows` (PR-3) and `label_not_a_proxy` (inapplicable, one unit) | The lake-mean retrain is honest and does not beat its baselines, exactly as ADR 0004 anticipated. It fixes fabrication and the location-proxy label; it is not a shippable model. Climatology is the binding bar (ADR-sf-0008 D2) | `data/processed/lake_anomaly_dataset.csv`, `src/model/artifacts/lake_anomaly/metrics.json`, `src/features/lake_anomaly.py`, `src/model/lake_anomaly.py` |

| EV-022 | 2026-09-10 | Scanning the main checkout and all five worktrees found **no `.venv`, no `data/raw/era5/`, and no `frontend/node_modules`** anywhere, contrary to `PARA_JUN.md` §1 and §2. The same handoff's test claim reproduced exactly: `pytest -q` → 78 passed, 8 xfailed once an environment was built. A plain `pip install -r requirements.txt` yields `torch 2.14.0+cpu`, not the `+cu126` of EV-017 nor the `+cu130` of `PARA_JUN.md` | Third recorded instance of a harness claim outrunning reality, and the first about local rather than repository state. A claim no committed artifact can witness must be written as a command to re-run, not as a fact. EV-017's CUDA figure describes a deliberate non-default install and does not reproduce from the documented command | `agents/local/CAPABILITIES.md`, `requirements.txt` |
| EV-023 | 2026-09-10 | The per-pixel retrain (ADR-sf-0010), first model here trained on fully real inputs: 56 Sentinel-2 passes + 13 months of ERA5-Land, **56,668 honest pairs / 1,866 pixels / 34 anchors**, spatial blocks {0: 3625, 1: 11932, 2: 9977, 3: 31134}. **MAE 0.001999 ± 0.001501 vs persistence 0.001402 and climatology 0.001296 — `beats_baselines` {persistence: false, climatology: false}.** Per fold: 0.001444/0.004568/0.001192/0.000792 against climatology 0.001543/0.001882/0.000929/0.000828, so folds 1 and 4 **do** beat climatology. Fold 2 (2026-02-13..2026-03-08) carries target std **2.35** against ~0.7 elsewhere. q10–q90 coverage **0.8135** against nominal 0.80 | The retrain is honest and loses on the mean, but not uniformly: it beats climatology on two of four folds and fails hardest in the most volatile window, which is bloom season and the case that matters operationally. BL-016 is satisfied — all four regions have enough pixels. The interval calibration is a genuine positive result independent of the point forecast | `data/processed/per_pixel_anomaly_dataset.csv`, `src/model/artifacts/per_pixel/metrics.json` |
| EV-024 | 2026-09-10 | Three defects found by running the runbook end to end. (a) `collect_era5.py` **could never complete**: `era5.py` assembly called `.drop(columns='month')` on a frame whose projection had already removed it, raising KeyError after all 13 months downloaded. (b) `baselines.trivial_rule` ran an unguarded `groupby(group_col)['bloom_7d']`, so a continuous-target table crashed the entire gate before any check reported. (c) `check_no_fabricated_rows` fails on the per-pixel table at inflation 1.011 — **false positive**: 562 duplicate groups, none sharing a date, on a `fai_now` with only **1,996 distinct values across 56,668 rows** because FAI is quantised to 5 decimals | (a) and (b) are fixed; (b) is the BL-030/BL-031 shape again — the `applicable=False` guard existed one layer above the code that actually ran. (c) is left unfixed on purpose: adding `date` to the key would make the candidate pass and would also destroy the forward-fill detection the check exists for, and a candidate must not be judged by checks rewritten to suit it | `src/features/era5.py`, `src/model/baselines.py`, `src/model/integrity.py` |
| EV-025 | 2026-09-10 | The per-pixel artifact is served end to end (branch `demoday`). `src/model/per_pixel_infer.py` is its **first** load path — before it, `train_per_pixel.py` wrote `quantile_mlp.pt` and no code ever read it back. The artifact format changed to store the scaler as tensors so `torch.load(..., weights_only=True)` (torch's safe default since 2.6) suffices; **retraining reproduced MAE 0.001999 ± 0.001501 bit-for-bit**, so no recorded figure moved. `GET /model/candidate` returns the candidate with both baselines, all 4 folds and `serving: false`. Three defects fixed on the way: `infer.py` read `metrics.json` with the platform codec (cp1252 on Windows), rendering the Spanish caveats as `tamaÃ±o` on the dashboard; `leaflet.heat` called `getImageData` on a zero-width canvas and, with no error boundary, unmounted the **entire** React tree (reproduced by resizing the viewport to 500x400 and back — `root.children.length` went to 0); no error boundary existed anywhere | The trained model is loadable, verifiably identical to the evaluated one, and reachable from the UI without implying it drives `/risk`. The encoding and crash defects were both latent and both user-visible: one silently corrupts any non-ASCII artifact string, the other blanks the dashboard on a window resize. Tests 92 passed / 8 xfailed, up from 80/8 | `src/model/per_pixel_infer.py`, `backend/app/routers/model_metrics.py`, `frontend/src/components/ModelView.jsx`, `frontend/src/components/ErrorBoundary.jsx`, `frontend/src/components/MapView/HeatLayer.jsx` |
## Reproduction

EV-001, EV-002, EV-003, EV-004, EV-005, EV-009 — audit of the training table:

```bash
python - <<'PY'
import pandas as pd
from sklearn.metrics import mean_absolute_error
T = 0.025916439519215278
d = pd.read_csv('data/processed/training_dataset.csv').sort_values('date').reset_index(drop=True)
hold = d.iloc[len(d) - int(len(d) * 0.2):]

print('EV-001 bloom rate by station')
print(d.groupby('station_id').bloom_7d.mean().round(3).to_string())

print('\nEV-002 station-name rule on holdout')
y, pred = hold.bloom_7d, (hold.station_id == 'sur').astype(int)
tp = ((pred == 1) & (y == 1)).sum(); fp = ((pred == 1) & (y == 0)).sum(); fn = ((pred == 0) & (y == 1)).sum()
p, r = tp / (tp + fp), tp / (tp + fn)
print(f'  precision={p:.2f} recall={r:.2f} f1={2*p*r/(p+r):.2f}  (model: 0.84 / 0.47 / 0.60)')

print('\nEV-003 persistence baseline')
print(f'  persistence MAE={mean_absolute_error(hold.fai_future, hold.fai_now):.5f}  (model: 0.00865)')

print('\nEV-004 fabricated rows')
print(f'  rows={len(d)} unique={len(d.drop_duplicates(["station_id","fai_now","fai_future"]))}')
print(f'  fai_now == fai_lag_1d on {(d.fai_now == d.fai_lag_1d).mean():.1%} of rows')

print('\nEV-005 seam')
print(f'  last train={d.iloc[len(d)-int(len(d)*0.2)-1].date}  first holdout={hold.date.min()}')

print('\nEV-009 present-reading')
print(f'  threshold(fai_now) matches label on {((d.fai_now >= T).astype(int) == d.bloom_7d).mean():.1%} of rows')
print(f'  corr(fai_now, fai_future) = {d.fai_now.corr(d.fai_future):.3f}')
PY
```

EV-007, EV-008 — real observation coverage:

```bash
python - <<'PY'
import datetime as dt, pandas as pd
r = pd.read_csv('data/processed/fai_series_raw.csv')
dates = set(pd.to_datetime(r.date).dt.date)
gaps = pd.to_datetime(r.date).diff().dt.days.dropna()
exact = sum(1 for x in dates if x + dt.timedelta(days=7) in dates)
relaxed = sum(1 for x in dates if any(x + dt.timedelta(days=k) in dates for k in range(5, 10)))
print(f'EV-007 dates={len(dates)} span={r.date.min()}..{r.date.max()}')
print(f'  gap median={gaps.median()} max={gaps.max()}  exact 7d pairs={exact}  relaxed 5-9d pairs={relaxed}')
g = pd.read_csv('data/processed/fai_grid_latest.csv')
print(f'EV-008 grid points per pass={len(g)}  implied per-pixel samples={len(g) * relaxed}')
PY
```

EV-011, EV-012 — corrected figures. Both were originally stated without a
reproduction command, and both drifted. They are recorded here so the same
failure does not recur:

```bash
python -c "
import pandas as pd
r = pd.read_csv('data/processed/fai_series_raw.csv')
cols = ['fai_pucon','fai_norte','fai_tolten','fai_sur']
print('non-null per station:', {c: int(r[c].notna().sum()) for c in cols})
print('total real readings:', int(r[cols].notna().sum().sum()))
"
```

```bash
find src backend scripts frontend/src -name '*.py' -o -name '*.js' -o -name '*.jsx' | xargs wc -l | tail -1
```

EV-006 — credential hygiene:

```bash
git ls-files | grep -iE '\.env$|secret|credential|\.pem$|\.key$' ; git log --all -p | grep -inE '(CDSE_CLIENT_SECRET|GEMINI_API_KEY|CDS_TOKEN|AIza)[=:][^ ]'
```

EV-013 — the leakage signature: cross-validation AUC against temporal holdout
AUC. This is finding 3's headline figure and was quoted in
`PROJECT_BRIEF.md` and `HANDOFF.md` without a command until the 2026-09-09
upgrade review caught it — precisely the omission the rule below exists to
prevent.

```bash
python -c "
import sys; sys.path.insert(0, '.')
from src.model import train
out = train.train()
print(out)
"
```

Expect mean CV AUC ≈ 0.99 against temporal holdout AUC ≈ 0.90. Reproduced
2026-09-09 as 0.9925 and 0.9003. The gap is the leakage, not the model: the CV
figure is inflated by shuffled folds over forward-filled duplicate rows (EV-004,
EV-005). Both numbers come from the audited pipeline and neither is a
performance claim.

EV-014, EV-016, and every check behind EV-001 to EV-005 and EV-009 now also run
as a test suite, which is the shortest reproduction path for all of them:

```bash
python -m pytest -q
```

EV-014 — station provenance, standalone:

```bash
python -c "
import sys, math; sys.path.insert(0, '.')
import numpy as np, pandas as pd
from src.features.stations import STATIONS
from src.model.integrity import _haversine_km
g = pd.read_csv('data/processed/fai_grid_latest.csv')
r = pd.read_csv('data/processed/fai_series_raw.csv')
for s in STATIONS:
    d = min(_haversine_km(s.lat, s.lng, la, lo) for la, lo in zip(g.lat, g.lng))
    print('%-7s %.3f km' % (s.id, d))
date = g.date.iloc[0]
row = r[r.date == date].iloc[0]
print('scene', date, 'lake_mean', round(row.lake_mean_fai, 6), 'p99', round(float(np.percentile(g.fai, 99)), 5))
print('fai_sur', round(row.fai_sur, 4), 'fai_pucon', round(row.fai_pucon, 4))
"
```

EV-015 — Copernicus credentials. Prints only the status code, never a secret:

```bash
python -c "
import httpx
from dotenv import find_dotenv, dotenv_values
v = dotenv_values(find_dotenv())
r = httpx.post('https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
               data={'grant_type': 'client_credentials', 'client_id': v['CDSE_CLIENT_ID'],
                     'client_secret': v['CDSE_CLIENT_SECRET']}, timeout=30)
print(r.status_code, 'access_token' in r.text)
"
```

EV-017 — PyTorch and CUDA:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

EV-018 — the CRLF hash. Shows that the sha the translation recorded is the same
file's, with the other line endings, and that it is no object in the repository:

```bash
python -c "
import hashlib
d = open('agents/RUN_STATE.md','rb').read().replace(b'\r\n', b'\n')
for name, b in (('LF', d), ('CRLF', d.replace(b'\n', b'\r\n'))):
    print(name, hashlib.sha1(b'blob %d\x00' % len(b) + b).hexdigest())
"
git cat-file -t 28592eefe840875435c8b510b447d3c0b299b3c6   # fatal: could not get object info
```

EV-019 and EV-020 — the lake-wide signal. Runs from a clean clone, no
credentials, no model:

```bash
python -c "
import json, numpy as np, pandas as pd
s = pd.read_csv('data/processed/fai_series_raw.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
dts = s.date.values
rows = []
for i, t in enumerate(dts):
    lag = (dts - t).astype('timedelta64[D]').astype(int)
    cand = np.where((lag >= 5) & (lag <= 9))[0]
    if len(cand):
        j = cand[np.argmin(np.abs(lag[cand] - 7))]
        rows.append((i, j, int(lag[j])))
p = pd.DataFrame(rows, columns=['i', 'j', 'h'])
now, fut = s.lake_mean_fai[p.i].values, s.lake_mean_fai[p.j].values
clim = s.lake_mean_fai.expanding().mean().values[p.i]
print('pairs', len(p), '| horizons', dict(sorted(p.h.value_counts().items())))
print('persistence MAE %.6f' % np.abs(fut - now).mean())
print('climatology MAE %.6f' % np.abs(fut - clim).mean())
print('shared dates (target and anchor)', len(set(p.i) & set(p.j)))
print('lake_mean_fai %.6f .. %.6f median %.6f' % (s.lake_mean_fai.min(), s.lake_mean_fai.max(), s.lake_mean_fai.median()))
print('recorded threshold', json.load(open('src/model/artifacts/metrics.json'))['fai_alert_threshold'])
"
```

EV-021 — the WI-005 retrain and the `min_prior` curve. No credentials:

```bash
python - <<'PY'
import pandas as pd
from src.features.lake_anomaly import build_pairs, build_anomaly_pairs
from src.model.lake_anomaly import fit_and_evaluate
s = pd.read_csv('data/processed/fai_series_raw.csv')
print('raw pairs (EV-019):', len(build_pairs(s)))
for mp in (0, 2, 4, 5, 7, 8):
    print(f'  min_prior={mp}: {len(build_anomaly_pairs(s, min_prior=mp))} pairs')
m = fit_and_evaluate(build_anomaly_pairs(s, min_prior=5))['metrics']
print('mae_fai %.6f +/- %.6f' % (m['metrics']['mae_fai'], m['metrics']['mae_fai_cv_std']))
print('persistence %.6f  climatology %.6f' % (
    m['baselines']['persistence']['mae_fai'], m['baselines']['climatology']['mae_fai']))
print('beats_baselines', m['beats_baselines'])
PY
# and the gate's verdict on the candidate table:
ALGAEWATCH_DATASET=data/processed/lake_anomaly_dataset.csv \
ALGAEWATCH_METRICS=src/model/artifacts/lake_anomaly/metrics.json \
python -m pytest -q tests/test_model_integrity.py   # 11 passed, 1 skipped, 4 xfailed
```

### Figure drift recorded 2026-09-10

Regenerating `src/model/artifacts/metrics.json` from the committed
`training_dataset.csv` reproduces precision, recall, F1, AUC and the confusion
matrix exactly, and moves two figures:

| Figure | Committed 2026-09-04 | Reproduced 2026-09-10 |
|---|---|---|
| `mae_fai` (EV-003's comparison target) | 0.00865 | **0.00867** |
| mean CV AUC (EV-013) | 0.9922 | **0.9925** |

The committed artifact already disagreed with this index before the change:
EV-013 records the audit's own 2026-09-09 reproduction as 0.9925, which is the
new number, not the old one. The most likely cause is a scikit-learn version
difference between the original 2026-09-04 run and the current environment
(1.7.2). Neither figure changes any conclusion — the regressor still loses to
persistence at 0.00603, by a wider margin — but both are recorded here rather
than silently superseded, per the rule below.


EV-022, EV-023, EV-024 — the per-pixel retrain. EV-022's ERA5 step needs
`CDS_TOKEN`; everything after it runs from committed data with no credentials:

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -c "import torch; print(torch.__version__)"   # EV-022

.venv/Scripts/python scripts/collect_era5.py            # ~50 min of CDS queue
.venv/Scripts/python scripts/build_per_pixel_dataset.py # ~30s, no API
.venv/Scripts/python scripts/train_per_pixel.py         # EV-023, the verdict

ALGAEWATCH_DATASET=data/processed/per_pixel_anomaly_dataset.csv \
ALGAEWATCH_METRICS=src/model/artifacts/per_pixel/metrics.json \
.venv/Scripts/python -m pytest -q tests/test_model_integrity.py
```

EV-024(c) — the quantisation that makes `no_fabricated_rows` misfire:

```python
import pandas as pd
df = pd.read_csv('data/processed/per_pixel_anomaly_dataset.csv')
key = ['station_id', 'fai_now', 'fai_future']
dup = df[df.duplicated(key, keep=False)]
g = dup.groupby(key)
print('rows', len(df), 'unique on key', len(df.drop_duplicates(key)))
print('dup groups sharing a date:', sum(1 for _, x in g if x['date'].nunique() == 1))
print('dup groups spanning dates:', sum(1 for _, x in g if x['date'].nunique() > 1))
print('distinct fai_now values:', df.fai_now.nunique(), 'of', len(df))
print('unique on date+horizon:', len(df.drop_duplicates(['station_id','date','horizon_days'])))
```


EV-025 — the served candidate. Needs the committed artifact:

```bash
.venv/Scripts/python -c "import torch; a=torch.load('src/model/artifacts/per_pixel/quantile_mlp.pt', map_location='cpu', weights_only=True); print(sorted(a))"
.venv/Scripts/python -m pytest -q tests/test_per_pixel_infer.py tests/test_model_metrics_api.py

# and against a running backend:
.venv/Scripts/python -m uvicorn backend.app.main:app --port 8000 &
curl -s http://localhost:8000/model/candidate -o /tmp/c.json
.venv/Scripts/python -c "import json,pathlib; d=json.loads(pathlib.Path('/tmp/c.json').read_bytes().decode('utf-8')); print(d['serving'], d['metrics']['mae_fai'], len(d['folds'])); print([hex(ord(c)) for c in d['classification_reason'] if ord(c)>127])"
```

## Rules

- Evidence should be easy to inspect when it matters to the user.
- Agent-only details can live in obscure docs, but important claims need clear
  references.
- Deployment evidence is required when deployment applies.
- Screenshots or visual review are required when user-facing quality matters.
- A model metric recorded without its persistence and trivial-rule baselines is
  not evidence under rule MI-1, and must not be entered in this index.
- Any figure quoted in a harness document must have a reproduction command here.
  The 2026-09-09 mount review found that every figure carried in this index
  reproduced exactly, while the two figures quoted without one had both drifted.
  Unsourced numbers are the ones that rot.
