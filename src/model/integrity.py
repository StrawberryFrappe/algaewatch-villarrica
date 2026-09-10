"""Model-integrity checks — GATE-MODEL, rules MI-1 to MI-3 and PR-3.

These encode the defects the 2026-09-09 audit actually found, so that they
cannot be reintroduced silently. `agents/validation/TEST_STRATEGY.md` lists them;
this module is their executable form, and `tests/` is what runs them.

Each check returns a `CheckResult` carrying the measured numbers rather than a
bare boolean. A check that says only "failed" cannot be argued with, and cannot
show that the situation improved without yet passing — which is exactly the
state the legacy dataset is in.

PR-1: this consumes an already-built feature table and never imports from
`src/features/`. `check_station_points_on_water` therefore takes the station
catalogue as **data**, supplied by the caller; the test that runs it is free to
read `src.features.stations`, because a test is not `src/model/`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .baselines import HORIZON_DAYS, Split, compute as compute_baselines

#: A pair of real observations differs in the continuous FAI value. Rows where
#: the current value equals its own 1-day lag are the forward-fill signature
#: (EV-004 measured 85.3%). Some coincidence is possible; a tenth of the table
#: is not.
MAX_DUPLICATE_LAG_FRACTION = 0.10

#: Positive-rate spread across locations. A target that fires at one station and
#: never at another is measuring place, not blooms (EV-001 measured 0.979).
MAX_STATION_POSITIVE_RATE_SPREAD = 0.50

#: How often thresholding the *present* reading may reproduce the label before
#: the "forecast" is just a re-reading of today (EV-009 measured 90.0%).
MAX_PRESENT_READING_AGREEMENT = 0.80

#: Distance from a station's declared coordinate to the nearest water pixel.
#: The reference grid is sampled every 15 pixels at 20 m, so ~300 m spacing
#: already costs up to ~0.2 km before any real error; 0.35 km leaves room for
#: that and no more.
MAX_STATION_WATER_DISTANCE_KM = 0.35

#: A station reading drawn from a raster should sit inside that raster's own
#: distribution. Above this percentile it is an outlier against the very water
#: it claims to sample.
STATION_PERCENTILE_CEILING = 99.0


@dataclass(frozen=True)
class CheckResult:
    """One check's verdict, with the numbers that produced it."""

    name: str
    passed: bool
    rule: str
    detail: str
    measured: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.passed


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(a))


def check_beats_persistence(model_metrics: Mapping, split: Split) -> CheckResult:
    """MI-1. The regressor is reported beside "the future equals the present"."""
    baselines = compute_baselines(split)
    baseline_mae = baselines["persistence"].get("mae_fai")
    model_mae = model_metrics.get("mae_fai")
    measured = {"model_mae_fai": model_mae, "persistence_mae_fai": baseline_mae}

    if model_mae is None or baseline_mae is None:
        return CheckResult(
            "beats_persistence", False, "MI-1",
            "One side of the comparison is missing, so MI-1 cannot be satisfied.",
            measured,
        )
    passed = model_mae < baseline_mae
    ratio = model_mae / baseline_mae if baseline_mae else float("inf")
    return CheckResult(
        "beats_persistence", passed, "MI-1",
        "Model MAE {:.5f} vs persistence {:.5f} ({:.0f}% of baseline error).".format(
            model_mae, baseline_mae, ratio * 100
        ),
        {**measured, "ratio": round(float(ratio), 4)},
    )


def check_beats_trivial_rule(model_metrics: Mapping, split: Split) -> CheckResult:
    """MI-1. The classifier is reported beside a rule that reads only location."""
    baselines = compute_baselines(split)
    trivial = baselines["trivial_rule"]
    baseline_f1 = trivial.get("f1_score")
    model_f1 = model_metrics.get("f1_score")
    measured = {
        "model_f1": model_f1,
        "trivial_rule_f1": baseline_f1,
        "trivial_rule": trivial.get("rule"),
    }

    if model_f1 is None or baseline_f1 is None:
        return CheckResult(
            "beats_trivial_rule", False, "MI-1",
            "One side of the comparison is missing, so MI-1 cannot be satisfied.",
            measured,
        )
    passed = model_f1 > baseline_f1
    return CheckResult(
        "beats_trivial_rule", passed, "MI-1",
        "Model F1 {:.4f} vs {} at F1 {:.4f}.".format(model_f1, trivial.get("rule"), baseline_f1),
        measured,
    )


def check_no_fabricated_rows(
    df: pd.DataFrame,
    key_cols: Sequence[str] = ("station_id", "fai_now", "fai_future"),
    lag_col: str = "fai_lag_1d",
    now_col: str = "fai_now",
) -> CheckResult:
    """PR-3 / EV-004. Every training row is a real observation pair.

    Two assertions, because either alone is evadable. Row count must equal the
    number of distinct real combinations — forward-filling a sparse series onto
    a daily grid multiplies rows without adding observations. And `fai_now` must
    not equal its own 1-day lag across the table: two genuinely different passes
    do not produce the same float, so agreement at scale means the value was
    held, not measured.
    """
    n_rows = len(df)
    n_unique = len(df.drop_duplicates(list(key_cols)))
    duplicate_lag = (
        float((df[now_col] == df[lag_col]).mean())
        if lag_col in df.columns and now_col in df.columns
        else float("nan")
    )
    measured = {
        "n_rows": n_rows,
        "n_unique_observations": n_unique,
        "inflation_factor": round(n_rows / n_unique, 3) if n_unique else None,
        "duplicate_lag_fraction": round(duplicate_lag, 4) if duplicate_lag == duplicate_lag else None,
    }

    rows_ok = n_rows == n_unique
    lag_ok = duplicate_lag != duplicate_lag or duplicate_lag <= MAX_DUPLICATE_LAG_FRACTION
    passed = rows_ok and lag_ok
    return CheckResult(
        "no_fabricated_rows", passed, "PR-3",
        "{} rows from {} real combinations; fai_now == fai_lag_1d on {:.1%} of rows "
        "(ceiling {:.0%}).".format(n_rows, n_unique, duplicate_lag, MAX_DUPLICATE_LAG_FRACTION),
        measured,
    )


def check_chronological_split(split: Split, horizon_days: int = HORIZON_DAYS) -> CheckResult:
    """MI-2 / EV-005. Validation follows training, with a horizon-length embargo.

    The audited pipeline sliced the sorted frame and stopped, leaving the last
    training date equal to the first holdout date: a training row's target then
    reaches seven days into the validation window.
    """
    gap = split.gap_days
    measured = split.summary()
    if gap is None:
        return CheckResult(
            "chronological_split", False, "MI-2",
            "No boundary could be computed — a partition is empty.", measured,
        )
    passed = gap >= horizon_days
    return CheckResult(
        "chronological_split", passed, "MI-2",
        "Last train {} -> first holdout {}: gap {} day(s), required {}.".format(
            split.last_train_date, split.first_holdout_date, gap, horizon_days
        ),
        measured,
    )


def check_label_not_stratified_by_station(
    df: pd.DataFrame, label_col: str = "bloom_7d", group_col: str = "station_id"
) -> CheckResult:
    """ADR 0004 D2 / EV-001. The label must not resolve to location.

    A pooled absolute threshold over stations with different local baselines
    produces exactly this: the station that always sits above it is labelled
    permanently blooming, the ones below it never.
    """
    rates = df.groupby(group_col)[label_col].mean()
    spread = float(rates.max() - rates.min()) if len(rates) else float("nan")
    measured = {
        "positive_rate_by_group": {str(k): round(float(v), 4) for k, v in rates.items()},
        "spread": round(spread, 4) if spread == spread else None,
    }
    passed = spread == spread and spread <= MAX_STATION_POSITIVE_RATE_SPREAD
    return CheckResult(
        "label_not_stratified_by_station", passed, "ADR 0004 D2",
        "Positive-rate spread across {} is {:.3f} (ceiling {:.2f}).".format(
            group_col, spread, MAX_STATION_POSITIVE_RATE_SPREAD
        ),
        measured,
    )


def check_no_present_reading_shortcut(
    df: pd.DataFrame,
    threshold: float,
    now_col: str = "fai_now",
    label_col: str = "bloom_7d",
) -> CheckResult:
    """EV-009. Thresholding today must not reproduce the label.

    Where it does, the "seven-day forecast" is a re-reading of the present, and
    the classifier's apparent skill is the autocorrelation of a slow index.
    """
    agreement = float(((df[now_col] >= threshold).astype(int) == df[label_col]).mean())
    measured = {"threshold": threshold, "agreement": round(agreement, 4)}
    passed = agreement <= MAX_PRESENT_READING_AGREEMENT
    return CheckResult(
        "no_present_reading_shortcut", passed, "EV-009",
        "Thresholding {} at {:.4f} reproduces the label on {:.1%} of rows "
        "(ceiling {:.0%}).".format(now_col, threshold, agreement, MAX_PRESENT_READING_AGREEMENT),
        measured,
    )


def check_station_points_on_water(
    stations: Iterable[Mapping],
    water_points: pd.DataFrame,
    station_series: pd.DataFrame | None = None,
) -> CheckResult:
    """Provenance: a station's sample point must actually be on the lake.

    Found 2026-09-10, and upstream of every modelling defect above. Two of the
    four placeholder coordinates in the station catalogue lie off the water;
    `src/features/fai.py::at_latlon` then expands its search window up to 1.2 km
    and averages the water pixels it eventually reaches, which for an off-lake
    point are shoreline mixed pixels. Vegetation reads strongly positive in FAI,
    so those stations return values in the extreme tail of the very raster they
    were drawn from, and the pooled bloom threshold is calibrated on that tail.

    `stations` is passed as data, not imported, to keep PR-1 intact. Each entry
    needs `id`, `lat`, `lng`. `water_points` needs `lat`, `lng`, `fai`, `date`.
    `station_series` is the wide per-date table (`fai_<station_id>` columns);
    when it shares a date with `water_points`, each station's reading is also
    compared against that scene's own distribution.
    """
    grid_dates = set(water_points["date"].unique()) if "date" in water_points.columns else set()
    shared_date = None
    percentile_value = None
    if station_series is not None and grid_dates:
        shared = set(station_series["date"].unique()) & grid_dates
        if shared:
            shared_date = sorted(shared)[-1]
            scene = water_points[water_points["date"] == shared_date]
            percentile_value = float(np.percentile(scene["fai"], STATION_PERCENTILE_CEILING))

    per_station: dict[str, dict] = {}
    failures: list[str] = []
    for station in stations:
        sid = str(station["id"])
        distance_km = min(
            _haversine_km(float(station["lat"]), float(station["lng"]), lat, lng)
            for lat, lng in zip(water_points["lat"], water_points["lng"])
        )
        entry: dict = {"distance_km": round(distance_km, 3)}
        on_water = distance_km <= MAX_STATION_WATER_DISTANCE_KM
        if not on_water:
            failures.append("{} is {:.2f} km from the nearest water pixel".format(sid, distance_km))

        if shared_date is not None:
            column = "fai_{}".format(sid)
            if column in station_series.columns:
                row = station_series.loc[station_series["date"] == shared_date, column]
                reading = float(row.iloc[0]) if len(row) and pd.notna(row.iloc[0]) else None
                entry["reading_on_shared_date"] = reading
                if reading is not None and percentile_value is not None and reading > percentile_value:
                    entry["above_scene_percentile"] = True
                    failures.append(
                        "{} reads {:.4f} on {}, above the p{:.0f} of that scene ({:.4f})".format(
                            sid, reading, shared_date, STATION_PERCENTILE_CEILING, percentile_value
                        )
                    )
                else:
                    entry["above_scene_percentile"] = False
        per_station[sid] = entry

    measured = {
        "max_distance_km": MAX_STATION_WATER_DISTANCE_KM,
        "shared_date": shared_date,
        "scene_percentile_value": None if percentile_value is None else round(percentile_value, 5),
        "stations": per_station,
    }
    passed = not failures
    detail = (
        "All station points sit on water and read inside their scene's distribution."
        if passed
        else "; ".join(failures)
    )
    return CheckResult("station_points_on_water", passed, "PR-3 / provenance", detail, measured)


def run_all(
    df: pd.DataFrame,
    split: Split,
    model_metrics: Mapping,
    threshold: float,
    stations: Iterable[Mapping] | None = None,
    water_points: pd.DataFrame | None = None,
    station_series: pd.DataFrame | None = None,
) -> list[CheckResult]:
    """Every check that the supplied inputs make answerable.

    A check whose inputs are missing is omitted rather than reported as a pass.
    """
    results = [
        check_beats_persistence(model_metrics, split),
        check_beats_trivial_rule(model_metrics, split),
        check_no_fabricated_rows(df),
        check_chronological_split(split),
        check_label_not_stratified_by_station(df),
        check_no_present_reading_shortcut(df, threshold),
    ]
    if stations is not None and water_points is not None:
        results.append(check_station_points_on_water(stations, water_points, station_series))
    return results
