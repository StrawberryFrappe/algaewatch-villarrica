"""WI-005 / ADR-sf-0008 / ADR-lq-0009 — lake-mean FAI anomaly pairs.

Turns the raw pass-date FAI series into honest observation pairs for the
interim retrain, in two steps that are kept separate on purpose:

- `build_pairs` — one row per anchor date, paired with the nearest later pass
  5 to 9 days out. This is pure pairing and reproduces EV-019 (35 pairs,
  `persistence_mae` 0.001333) exactly, so it stays checkable against the
  recorded evidence.
- `add_causal_baseline` — attaches a local baseline computed only from passes
  strictly *before* each anchor, then drops anchors without enough history for
  the baseline `std` to mean anything.

`build_anomaly_pairs` composes the two and is what training calls.

Constraints this module keeps:

- **PR-3 / no fabrication.** One row per real anchor, no forward-fill.
  `fai_now` / `fai_future` are raw FAI values from the source series.
- **ADR-sf-0007.** The signal is `lake_mean_fai` — the SCL water-mask mean, no
  station coordinate in its derivation — not `fai_<station_id>`.
- **BL-028.** Pure pandas/numpy; no `sentinelhub` import.
- **PR-1.** `src/features/` never imports from `src/model/`.
- **ADR 0004 D3.** Parameterised on a spatial-unit column: pass
  `unit_col="pixel_id"` and the per-pixel table flows through unchanged. The
  lake-wide series has one unit, recorded as `station_id="lake"` so the model
  gate's single-group guards (BL-030, BL-031) engage.
- **ADR 0004 D2.** The target is a *standardised* anomaly against the local
  causal baseline, `(value - baseline_mean) / baseline_std`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LAKE_UNIT = "lake"

#: Minimum causal observations before an anchor for its baseline `std` to mean
#: something. ADR-lq-0009: on the 56-date series the pair count is flat at 34
#: for any value from 2 to 6 (only the zero-history 2025-09-06 anchor is ever
#: dropped) and `baseline_std` barely moves across that range, so the choice is
#: insensitive; 5 sits clear of the sample-std floor of 2 with every kept pair
#: backed by at least 7 real prior passes.
DEFAULT_MIN_PRIOR = 5

PAIR_COLUMNS = ["date", "station_id", "horizon_days", "fai_now", "fai_future"]
BASELINE_COLUMNS = ["baseline_mean", "baseline_std", "n_prior", "anomaly_now", "anomaly_future"]


def build_pairs(
    series: pd.DataFrame,
    *,
    value_col: str = "lake_mean_fai",
    unit_col: str | None = None,
    date_col: str = "date",
    min_lag: int = 5,
    max_lag: int = 9,
    target_lag: int = 7,
) -> pd.DataFrame:
    """One pair per anchor: the nearest later pass 5-9 days out, ties toward 7.

    Reproduces EV-019 on `fai_series_raw.csv`: 35 pairs, horizons 5d x10, 6d x1,
    7d x11, 8d x13. Columns: ``date`` (anchor), ``station_id`` (the spatial
    unit), ``horizon_days``, ``fai_now``, ``fai_future`` — all raw FAI units.
    """
    src = series.copy()
    src[date_col] = pd.to_datetime(src[date_col])
    if unit_col is None:
        unit_col = "__unit__"
        src[unit_col] = LAKE_UNIT

    rows: list[dict] = []
    for unit, group in src.groupby(unit_col, sort=False):
        g = group.sort_values(date_col).reset_index(drop=True)
        vals = g[value_col].to_numpy(dtype=float)
        day_index = (g[date_col] - g[date_col].iloc[0]).dt.days.to_numpy()

        for i in range(len(g)):
            lag = day_index - day_index[i]
            candidates = np.where((lag >= min_lag) & (lag <= max_lag))[0]
            if candidates.size == 0:
                continue
            j = int(candidates[np.argmin(np.abs(lag[candidates] - target_lag))])
            fai_now, fai_future = float(vals[i]), float(vals[j])
            if not (np.isfinite(fai_now) and np.isfinite(fai_future)):
                continue
            rows.append(
                {
                    "date": g[date_col].iloc[i].date().isoformat(),
                    "station_id": str(unit),
                    "horizon_days": int(lag[j]),
                    "fai_now": fai_now,
                    "fai_future": fai_future,
                }
            )
    return pd.DataFrame(rows, columns=PAIR_COLUMNS).sort_values(
        ["station_id", "date"]
    ).reset_index(drop=True)


def add_causal_baseline(
    pairs: pd.DataFrame,
    series: pd.DataFrame,
    *,
    value_col: str = "lake_mean_fai",
    unit_col: str | None = None,
    date_col: str = "date",
    min_prior: int = DEFAULT_MIN_PRIOR,
) -> pd.DataFrame:
    """Attach a local baseline from passes strictly before each anchor.

    `baseline_mean` / `baseline_std` are the mean and sample std of `value_col`
    over that unit's passes with date < the anchor date. Anchors with fewer
    than ``max(min_prior, 2)`` such passes, or a zero / non-finite std, are
    dropped — a one-point window gives no spread, and the anomaly it produces
    is meaningless.
    """
    floor = max(int(min_prior), 2)
    src = series.copy()
    src[date_col] = pd.to_datetime(src[date_col])
    if unit_col is None:
        unit_col = "__unit__"
        src[unit_col] = LAKE_UNIT

    history: dict[str, pd.DataFrame] = {
        str(unit): g.sort_values(date_col).reset_index(drop=True)
        for unit, g in src.groupby(unit_col, sort=False)
    }

    kept: list[dict] = []
    for row in pairs.to_dict("records"):
        g = history.get(str(row["station_id"]))
        if g is None:
            continue
        anchor = pd.Timestamp(row[date_col])
        prior = g.loc[g[date_col] < anchor, value_col].to_numpy(dtype=float)
        prior = prior[np.isfinite(prior)]
        if prior.size < floor:
            continue
        baseline_mean = float(prior.mean())
        baseline_std = float(prior.std(ddof=1))
        if not np.isfinite(baseline_std) or baseline_std == 0.0:
            continue
        kept.append(
            {
                **row,
                "baseline_mean": baseline_mean,
                "baseline_std": baseline_std,
                "n_prior": int(prior.size),
                "anomaly_now": (row["fai_now"] - baseline_mean) / baseline_std,
                "anomaly_future": (row["fai_future"] - baseline_mean) / baseline_std,
            }
        )

    return pd.DataFrame(kept, columns=list(pairs.columns) + BASELINE_COLUMNS).reset_index(
        drop=True
    )


def build_anomaly_pairs(
    series: pd.DataFrame,
    *,
    value_col: str = "lake_mean_fai",
    unit_col: str | None = None,
    date_col: str = "date",
    min_lag: int = 5,
    max_lag: int = 9,
    target_lag: int = 7,
    min_prior: int = DEFAULT_MIN_PRIOR,
    bloom_threshold: float | None = None,
) -> pd.DataFrame:
    """`build_pairs` then `add_causal_baseline` — the training entry point.

    When ``bloom_threshold`` is given, a ``bloom_7d`` column is added as
    ``fai_future >= bloom_threshold``. Under the uncalibrated station threshold
    it is constant (EV-020); ADR-sf-0008 D4 keeps the classification metrics
    ``null`` because of that, and the column is present only so the gate's
    table-shape checks have something to read.
    """
    pairs = build_pairs(
        series,
        value_col=value_col,
        unit_col=unit_col,
        date_col=date_col,
        min_lag=min_lag,
        max_lag=max_lag,
        target_lag=target_lag,
    )
    out = add_causal_baseline(
        pairs,
        series,
        value_col=value_col,
        unit_col=unit_col,
        date_col=date_col,
        min_prior=min_prior,
    )
    if bloom_threshold is not None:
        out["bloom_7d"] = (out["fai_future"] >= bloom_threshold).astype(int)
    return out
