# Project Agent Instructions — AlgaeWatch Villarrica

This project uses a mounted Agent Harness Kernel under `agents/`.

## Required Read Order

1. `agents/README.md`
2. `agents/RUN_STATE.md`
3. `agents/LOCAL_SETUP.md`
4. `agents/intake/PROJECT_BRIEF.md`
5. `agents/intake/PROJECT_PROFILE.md`
6. `agents/intake/SOURCE_MANIFEST.md`
7. `agents/validation/GATES.md`
8. `agents/execution/WORKFLOW.md`
9. `agents/i18n/TRANSLATION_PROTOCOL.md` — this project carries two working
   languages
10. Latest relevant review under `agents/reviews/`

Before touching anything under `src/model/`, also read
`agents/adrs/0004-per-pixel-anomaly-redesign.md`,
`agents/validation/EVIDENCE_INDEX.md` and `agents/validation/TEST_STRATEGY.md`.

## The Local Half

`agents/` is project truth and is committed. What your agent can do, where your
checkout lives, and which binaries you invoke are **environment truth**, and
live in `agents/local/`, which is never committed.

A fresh clone therefore arrives incomplete on purpose. Build the local half
before implementation work — `agents/LOCAL_SETUP.md` says how, and GATE-LOCAL
enforces it.

## Languages

English is canonical. Spanish translations live beside their sources as
`FOO.es.md` and track them by hash. See `agents/i18n/TRANSLATION_PROTOCOL.md`
and ADR-sf-0006. Where a translation and its source disagree, the source wins.

## Core Rules

- Do not implement application code until the mounted harness is accepted,
  unless the user explicitly overrides after risk disclosure. This gate is
  unconditional — it is not waived by small scope, high confidence, or complete
  context. Assumptions filled from context, even "safe" ones, must be surfaced
  for the user to double-check before proceeding.
- Do not implement application code until `agents/local/CAPABILITIES.md` exists.
- Preserve existing project rules and fuse them into this file and `agents/`.
- Ask the user when product, stack, deployment, evidence, or quality decisions
  are unclear.
- Decide review strength from your own capability scan. Do not assume a
  capability because a committed document mentions it.
- Keep environment truth, raw memory and task logs under `agents/local/`; never
  commit them.
- Promote durable decisions into ADRs, planning docs, architecture docs,
  validation docs, or review summaries.
- This project has two contributors. ADR and review filenames carry an author
  slug — `sf` and `lq`, see ADR-sf-0005 and the naming rules in
  `agents/execution/WORKFLOW.md`.
- Cite artifacts rather than asserting them. A citation is checkable, and the
  doctor checks that cited paths exist.
- If you detect drift from the harness, stop forward work and produce a handoff.

## Preserved Project Rules

These rules predate the harness. They come from the root `README.md` and the
existing code layout, and they remain binding.

### PR-1 — Strict feature/model separation

`src/features/` must never import from `src/model/`, and `src/model/` must never
import from `src/features/` or call the Sentinel-2 / CDS APIs directly.

- `src/features/` computes FAI and derived variables only. No training.
- `src/model/` trains and infers only. It consumes an already-built table.
- `backend/app/data_source.py` is the single bridge between the backend and the
  pipeline. Routers call `data_source`, never `src/` directly.

### PR-2 — Credentials live outside the repository tree

Real credentials go in a `.env` **one directory above the repository root**, not
inside it. The code resolves it with `python-dotenv`'s `find_dotenv()`, which
walks upward, so no absolute paths are hardcoded and the file is structurally
outside the git tree rather than merely gitignored.

Verified on 2026-09-09: no secrets are tracked and none appear in git history.
Do not add credentials to the repo, and do not weaken this convention.

### PR-3 — Never fabricate measurements

Where real data is unavailable, return `null` / `NaN` and mark the source as a
stub. `src/features/insitu.py` is an explicit stub because the SNIA CSVs have not
arrived; `/observations` therefore returns `null` for temperature, pH, dissolved
oxygen, and wind. Do not replace absent data with invented values.

This rule now extends to training data — see ADR 0004. Forward-filling sparse
satellite observations onto a daily grid and training on the result counts as
fabrication and is prohibited.

### PR-4 — Design handoff governs the frontend

`design_handoff_algaewatch_villarrica/README.md` is the frontend source of
truth for layout, view structure, and interaction. Deviations from it are
allowed but must be recorded as ADRs. One such deviation is already recorded
(ADR 0003, map library).

Two texts in that handoff are explicitly required to be preserved: the
"TRL 2 · resultados no validados en campo" seal and the AI-panel disclaimer.

Current compliance is partial, verified 2026-09-09. The AI-panel disclaimer is
hardcoded correctly in `backend/app/routers/forecast.py`. The TRL-2 seal is
**not** rendered: `backend/app/routers/model_metrics.py` supplies it only as a
default argument to `m.get("caveats", ...)`, and `metrics.json` always populates
`caveats`, so the mandated Spanish text is unreachable dead code. Tracked as
BL-019. Do not treat this rule as currently satisfied.

## Model Integrity Rules

These are project-specific and were added after the 2026-09-09 audit.

### MI-1 — No model ships without baseline comparison

Any bloom model must be reported alongside, at minimum:

- a **persistence** baseline (predict "same as today"), and
- a **trivial-rule** baseline (e.g. predict by location alone).

A model that does not beat both is reported as not beating them. See
`agents/validation/TEST_STRATEGY.md`.

### MI-2 — Temporal validation only

Splits must be chronological. Random or shuffled k-fold over time-ordered rows
is prohibited. Leave an embargo gap of at least the forecast horizon between the
end of training and the start of validation.

### MI-3 — Thresholds are policy, not labels

Do not bake an absolute alert threshold into training labels. Predict a
continuous quantity; apply thresholds downstream where they can be changed
without retraining.
