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

Both commands returning nothing is the pass condition.

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
