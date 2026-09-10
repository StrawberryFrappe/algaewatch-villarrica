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
