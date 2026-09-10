# Handoff

Written 2026-09-09, for **Luchosqi** (`lq`), original author of `4b37bea`.

A Spanish translation is at `agents/execution/HANDOFF.es.md`. English is
canonical (ADR-sf-0006), so where the two disagree, this file wins.

## What This Is

You wrote AlgaeWatch Villarrica. It was forked, audited, and fitted with an agent
harness under `agents/`. The repository is being handed back, and this document
is the handover: what was found, what is being rebuilt, what is yours, and what
is still open.

**No application code has been changed.** Everything under `src/`, `backend/`,
`frontend/`, `scripts/` and `data/` is exactly as you left it at `4b37bea`. The
only additions are `AGENTS.md`, the `agents/` tree, `.gitattributes`, and this.

## The Short Version

The satellite pipeline you built is **correct** and is being kept. The FAI
formula matches Hu (2009), the SCL water masking is right, and the rasters are
co-registered by a fixed bbox and resolution. It was checked specifically so it
would not be rewritten alongside everything else.

The **model layer does not predict**, and the metrics in
`src/model/artifacts/metrics.json` are not performance figures. Six findings,
below, all reproducible from CSVs already in the repository. Every one has a
command so you can check it yourself rather than take it on trust.

## The Six Findings

Reproduction commands are in `agents/validation/EVIDENCE_INDEX.md` (EV-001 to
EV-013). Every figure quoted anywhere in the harness has one; that is a rule,
adopted after two figures without commands turned out to have drifted.

| # | Finding | The number |
|---|---|---|
| 1 | **The label encodes location, not blooms.** Under the single pooled threshold of 0.0259, per-station bloom rates are sur 0.98, pucon 0.50, norte 0.00, tolten 0.00 | A rule reading only the station name scores P 0.97 / R 0.74 / F1 0.84 — beating the trained classifier's 0.84 / 0.47 / 0.60 on every metric |
| 2 | **Training rows were fabricated.** 218 real readings (56 pass dates × 4 stations, less 6 cells with no water pixel) were forward-filled into 1,356 daily rows | Only 363 unique (station, fai_now, fai_future) combinations exist; 85% of rows have `fai_now` identical to `fai_lag_1d` |
| 3 | **Cross-validation leaked.** `StratifiedKFold(shuffle=True)` over those duplicated rows put copies of the same observation in both train and validation folds | CV AUC 0.99 vs temporal holdout AUC 0.90 — that gap is the signature |
| 4 | **The holdout leaks at the seam.** Train and holdout share the boundary date 2026-06-09 with no embargo | The last training rows' 7-day targets fall inside the holdout window |
| 5 | **The regressor loses to persistence.** "Predict the same as today" gives MAE 0.00603 | The trained regressor gives 0.00865 — 43% worse |
| 6 | **The classifier re-reads the present.** Thresholding `fai_now` directly reproduces the `bloom_7d` label on 90% of rows | It is not forecasting; it is restating today |

These are findings about a pipeline, not a verdict on you. Every one of them is a
mistake that ships in production ML regularly, and finding number 2 is what makes
the other five almost inevitable — forward-fill first, and shuffled CV cannot
help but leak afterwards.

Three root causes: the target is binarised against a pooled absolute constant,
which encodes place; rows were fabricated by forward-fill; validation shuffled
time-ordered duplicate rows.

## What Is Being Rebuilt, And Why

`agents/adrs/0004-per-pixel-anomaly-redesign.md`. Four changes, adopted together
because adopting a subset reintroduces the defect the others fix:

- **D1** — predict a continuous quantity, apply thresholds at serving time.
- **D2** — express the target as an anomaly against a *local* baseline, not a
  lake-pooled constant.
- **D3** — train on lake pixels rather than four placeholder stations. Your
  `FaiRaster.sample_grid` already produces ~1,860 water pixels per pass and is
  currently used only to draw the heatmap. Training on it takes the honest sample
  count from ~140 to ~65,000 across 35 usable date pairs, using data already
  downloaded.
- **D4** — chronological splits with an embargo of at least the forecast horizon.

Reported metrics **will fall**, and that is the intended outcome. The supervisor
asked for training to be improved and for the team to understand the numbers it
is juggling (SRC-002). A low honest number with correct methodology passes; a
high number produced by leakage does not.

One thing worth saying plainly: beating persistence will probably require
change-drivers the project does not have — wind, temperature, radiation, runoff.
That reframes the missing ERA5-Land backfill from an unfinished chore into the
principal *explanation* for the persistence failure.

## Your Half

Agreed split (ADR-sf-0005). By subsystem, so the two halves share no files.

**You take the frontend.** Full detail in `agents/planning/BACKLOG.md`.

| Item | What |
|---|---|
| BL-009 | Replace the 4-stop risk palette in `frontend/src/utils/risk.js`. Blue/green/orange/red is not perceptually uniform, and green/orange/red is the confusable set for the commonest colour vision deficiencies — on what is nominally a public-health signal |
| BL-010 | Clip the risk overlay to the lake surface. Risk is currently painted over land |
| BL-013 | Extend staleness disclosure beyond the header. `Header.jsx` already flags a stale last pass correctly via `overlay.updated_at`; the date slider, map overlay and station cards do not |
| BL-019 | Render the mandated `TRL 2 · resultados no validados en campo` seal in the Modelo view. It is currently unreachable: `backend/app/routers/model_metrics.py` supplies it only as a default to `m.get("caveats", ...)`, and `metrics.json` always populates `caveats` |
| BL-021 | Reduce the generated-default visual excess — the two blurred colour halos in `app.css`, and the blanket `backdrop-filter: blur(18px) saturate(140%)` on every panel. Full restyle if time allows; removing the decorative excess is the floor |

**`sf` keeps the model layer**: WI-004 (make the persistence and trivial-rule
baselines permanent, re-runnable checks) then WI-005 (the honest retrain). The
audit context lives there, and handing it over would mean transferring the whole
audit session first.

## What Is Yours To Decide

**ADR 0003 — the map library.** The design handoff
(`design_handoff_algaewatch_villarrica/README.md`) mandates Mapbox GL JS; the
code ships Leaflet with Esri satellite tiles. That deviation was recorded as
**provisional specifically pending your opinion**, and it is now your call
because the frontend is yours. Leaflet stands until you answer. Frontend work
should not start before you do — a late reversal costs hours.

## Before You Start

**Build your local half.** `agents/` is committed and shared; `agents/local/` is
never committed and arrives empty. Copy
`agents/templates/capability-scan-template.md` to `agents/local/CAPABILITIES.md`
and fill it in for *your* machine. `agents/LOCAL_SETUP.md` explains why, and
GATE-LOCAL blocks implementation work until it exists.

This is not bureaucracy. Do not read the committed scan at
`agents/reviews/20260909/capability_scan.md` as current — it describes one
Windows machine on one day, and an agent that believes it will plan delegated
reviews it may be unable to run, then report them as done.

**Run the checks.** Both live inside the harness, so they travel with it:

```bash
python agents/harness_doctor.py --root . --strict
python agents/check_translations.py
```

**Conventions that will bite otherwise.** ADR and review filenames carry an
author slug — yours is `lq`, so your next ADR is `lq-0007-name.md`. Append new
rows at the *end* of index tables so concurrent edits conflict visibly instead of
interleaving silently. Never share a working tree with a concurrent agent
session.

## What Is Still Blocked

| Blocker | Effect |
|---|---|
| Copernicus Data Space Ecosystem credentials (WI-002) | Blocks BL-007 and BL-008, therefore milestone M3, the per-pixel redesign. Does **not** block M2, the credential-free honest retrain, which is the guaranteed deliverable |
| PyTorch not installed | ADR 0002 makes it binding from the supervisor. Found during the 2026-09-09 scan; blocks BL-008 independently of the credentials. M2 is unaffected — it deliberately stays scikit-learn |
| Harness acceptance (GATE-HM) | No application code starts until the owner accepts the mounted harness |
| No test suite | GATE-TEST has nothing to run until BL-002 lands |

## Things That Will Not Be Obvious From The Code

- The pitch is roughly 2026-09-10 (ASM-001). Confirm before planning around it.
- `src/model/artifacts/metrics.json` is retained **for provenance only**. Its own
  `caveats` field is honest; the surrounding README prose is not.
- `data/processed/training_dataset.csv` must never train a shipped model. It is
  kept as evidence of the audited defect.
- The four station coordinates are **placeholders**. They carry no scientific
  meaning, and one of them originally fell on dry land — a real bug, found and
  fixed, in `at_latlon`'s search radius.
- The root `README.md` overstates what runs on real data. "Sin mocks, todo el
  backend corre sobre datos reales" is true of the FAI half only: ERA5 was never
  collected, in-situ is a stub, and the station coordinates are placeholders.
  Tracked as BL-011, unassigned.
- The project runs the backend and dashboard with **zero credentials** against
  committed data. That is deliberate. Protect it.
- A green `harness_doctor.py` run is a structural check, not a truth check. It
  once reported zero blockers while `RUN_STATE.md` asserted a review document
  that did not exist.
- Any figure quoted in a harness document must carry a reproduction command in
  `EVIDENCE_INDEX.md`. Every figure that had one stayed accurate; both figures
  that lacked one had drifted by the time they were reviewed.

## Required Reads

1. `AGENTS.md` — the operating rules, including your project's own PR-1…PR-4 and
   the model-integrity rules MI-1…MI-3
2. `agents/RUN_STATE.md` — where the project actually is
3. `agents/LOCAL_SETUP.md` — then build your local half
4. `agents/planning/BACKLOG.md` — your five items in full
5. `agents/adrs/0003-map-library-leaflet-provisional.md` — your decision

Before touching `src/model/` at all: ADR 0004,
`agents/validation/EVIDENCE_INDEX.md`, `agents/validation/TEST_STRATEGY.md`.
