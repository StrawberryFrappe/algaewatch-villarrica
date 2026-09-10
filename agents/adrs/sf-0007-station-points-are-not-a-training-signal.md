# ADR-sf-0007: Station-point FAI is not an admissible training signal

## Status

Accepted

## Context

ADR 0004 moved modelling to per-pixel FAI anomalies, and its stated reason was
sample size: honest pairing at station granularity yields 44 to 140 rows
(EV-007), which is not enough to train on. That argument is about *quantity*.

Investigating the training data on 2026-09-10 produced a second and independent
reason, about *validity*. Two of the four station sample points are not on the
lake (EV-014):

| Station | Distance to nearest sampled water pixel |
|---|---|
| tolten | 0.07 km |
| norte | 0.15 km |
| pucon | **0.77 km** |
| sur | **0.98 km** |

`sur` at -39.3100 lies south of the lake's southernmost water pixel, -39.30701.
`src/features/stations.py` says the coordinates are placeholders pending the GPS
that arrives with the SNIA CSVs; nothing downstream refused to train on them.

`at_latlon` in `src/features/fai.py` expands its search window up to
`max_radius_px=60` — 1.2 km at 20 m resolution — and averages every pixel the
SCL mask calls water inside it. For an off-lake point those are shoreline mixed
pixels, and terrestrial vegetation reads strongly positive in FAI. The result is
measurable on a single scene: on 2026-08-22 the lake mean FAI is 0.000267 and
0.38% of 1,860 water pixels clear the bloom threshold, while `fai_pucon` reads
0.0585 and `fai_sur` 0.0567 — both above that same raster's 99th percentile.

This is upstream of the audit's first finding rather than beside it. Ranking the
stations by distance from the water reproduces the ranking by bloom rate exactly:
the two off-lake stations are the two that "bloom" (0.979 and 0.501), the two on
the water never do (0.000). The Gaussian-mixture threshold of 0.0259 is
calibrated on a bimodal distribution whose upper mode *is* the contamination, so
the threshold is an artifact of the defect it is used to detect.

The consequence is that the redesign in ADR 0004 is necessary but not
sufficient. A continuous target, a local-baseline anomaly, real observation
pairs and chronological splits would all be correct changes, and a model trained
on these four points would still be learning shoreline vegetation.

## Decision

Station-point FAI is disqualified as a training signal until the real station
coordinates arrive.

1. No training path may consume `fai_<station_id>` columns as its measurement of
   lake condition. This holds regardless of how the target is expressed.
2. `check_station_points_on_water`, in `src/model/integrity.py`, enforces it: each
   declared coordinate must sit within 0.35 km of a water pixel, and its reading
   must fall inside the distribution of the scene it was drawn from. The
   tolerance accounts for the reference grid's ~300 m sampling stride and no
   more.
3. Per-pixel sampling over the water mask, per ADR 0004 D3, is the path forward.
   It does not depend on the station catalogue at all, which is why the defect
   does not follow it.
4. The station catalogue remains correct for **display**. The four stations are
   real physical installations and the dashboard should keep naming them; what
   is disqualified is treating a placeholder coordinate as a measurement site.
5. When the SNIA coordinates arrive, the check is what decides whether station
   sampling is readmitted. Passing it is the condition, not an argument that the
   new coordinates look better.

## Consequences

**Improves.** The label defect gains a root cause rather than a description, so
fixing the target alone can no longer be mistaken for fixing the problem. The
per-pixel decision in ADR 0004 gains a second justification that survives even
if the sample-size argument is one day resolved by a longer history. And the
check is executable, so the disqualification cannot lapse quietly.

**Gets harder.** The four station cards in the dashboard cannot show a
measurement traceable to their own coordinates until either the real GPS lands
or the per-pixel field is queried at each station's true position. Whichever
arrives first, that is a visible product gap in the meantime, and PR-3 requires
it be shown as absent rather than filled in.

**Must be revisited** when the SNIA CSVs arrive with real coordinates (BL-027),
and if `at_latlon` is kept for any purpose: silently averaging whatever water it
can find up to 1.2 km away is a reasonable fallback for a map query and a bad
one for a training feature, and the two uses should not share a function without
saying which is which.

## Sources

- EV-014, `agents/validation/EVIDENCE_INDEX.md` — the measurements above
- EV-001, EV-007 — the bloom-rate stratification and the honest pair count
- ADR 0004 — the per-pixel anomaly redesign this reinforces
- `src/features/stations.py` — placeholder coordinates, stated in the file
- `src/features/fai.py` — `at_latlon` search and averaging behaviour
- `tests/test_station_provenance.py` — the checks that keep this decision honest
