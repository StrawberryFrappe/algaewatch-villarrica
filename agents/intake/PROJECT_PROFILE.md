# Project Profile

This profile keeps the harness granular. Do not stop at broad labels like
"web app" or "CLI"; record the project-specific shape that should drive the
harness.

## Project Category

**Remote-sensing data/ML project with a thin web presentation layer.**

More precisely, four coupled subsystems with different risk profiles:

| Subsystem | Path | Nature | Audit standing |
|---|---|---|---|
| Satellite feature extraction | `src/features/` | Deterministic math over Sentinel-2 L2A bands | Sound. FAI matches Hu (2009); SCL water masking correct |
| Predictive model | `src/model/` | Supervised learning, 7-day horizon | Broken. Leakage, fabricated rows, loses to trivial baselines |
| API | `backend/app/` | FastAPI read-only, five routers | Structurally clean; serves whatever the model produces |
| Dashboard | `frontend/src/` | React + Vite + Leaflet, four views | Functional; visual style and colour semantics are liabilities |

The centre of gravity is the model layer. The web layer exists to make the model
legible, not the other way round.

## Maturity

**Prototype.** TRL 2 by the project's own declaration, and the label is honestly
earned rather than aspirational — a concept has been formulated and analytically
explored, with no experimental proof and no field validation.

Qualifiers:

- One commit of history. No tests, no CI, no deployment.
- The ingestion half is more mature than the modelling half. Real Sentinel-2
  scenes are fetched and processed correctly; the learning built on top does not
  yet learn.
- Broad architectural change is **permitted** by the owner. The satellite
  pipeline is nonetheless to be preserved, because it was audited and passed.

## Primary Quality Risks

Ordered by severity for this project specifically.

| Risk | Manifestation here | Status |
|---|---|---|
| **Model leakage** | Shuffled k-fold over forward-filled duplicate rows; no embargo at the train/holdout seam | Confirmed, quantified |
| **Data fabrication** | 218 real readings inflated to 1,356 training rows by forward-fill | Confirmed |
| **Target mis-specification** | Absolute pooled threshold makes the label a proxy for location | Confirmed |
| **Insufficient sample** | 44 honest (t, t+7) pairs across 4 stations; 140 with a relaxed window | Confirmed; remedy identified |
| **Unearned credibility** | Metrics presented without baseline comparison | Being addressed by MI-1 |
| **Fake-looking UI** | Generated-default visual idiom; risk palette is Apple system colours | Open, GATE-PQ applies |
| **Accessibility** | 4-stop risk palette whose green/orange/red stops are the confusable set for common colour vision deficiencies | Open, backlog |
| **Visual correctness** | Heat overlay not clipped to the lake polygon; risk painted on land | Open, backlog |
| Weak tests | No test surface at all | Open, GATE-TEST applies |
| Placeholder geography | Station coordinates are admitted placeholders inside the lake bbox | Open; per-pixel redesign removes the dependency |

Deliberately **not** a listed risk: satellite ingestion correctness, credential
hygiene. Both were checked and passed.

## Active Gates

| Gate | Active | Reason |
|---|---|---|
| GATE-HM Harness Mounted | yes | Always required |
| GATE-DR Doctor | yes | Always required |
| GATE-TEST Tests | yes | Data/ML project with a confirmed leakage history. Baseline-comparison checks (MI-1) must be executable and re-runnable, not ad-hoc |
| GATE-DEPLOY Deployment | no | Deployment is explicitly out of scope; local evidence only |
| GATE-PQ Portfolio Quality | yes | Owner intends this as a portfolio piece and has flagged the current visual quality as unacceptable |
| GATE-MODEL Model Integrity | yes | Project-specific gate added after the 2026-09-09 audit. Encodes rules MI-1 to MI-3 so the leakage found cannot silently return. Defined in `agents/validation/GATES.md` |

## Evidence Bar

- **Model claims**: a reproducible script plus its recorded output. Every headline
  metric must appear next to the persistence and trivial-rule baselines it is
  being compared against. A metric without its baselines is not evidence.
- **Data claims**: the exact command and the CSV it read. Row counts must
  distinguish real observations from derived rows.
- **UI claims**: a screenshot of the running app showing the real state, not a
  mock.
- **Pipeline claims**: the satellite pass dates actually used, not a
  forward-filled range presented as coverage.

## Deployment Posture

Deferred. The system runs locally: FastAPI via `uvicorn`, frontend via `vite`.
No hosting target, no domain, no container, and no CI have been selected, and
none are in scope before the pitch.

The committed `data/processed/*.csv` and `src/model/artifacts/` mean the backend
and dashboard run with **zero credentials**. Credentials are required only to
re-collect satellite data. This is a deliberate property and should be preserved.

## Collaboration Posture

**Solo-first, upstream-compatible.** Development proceeds on the owner's fork
(`origin` → `StrawberryFrappe/algaewatch-villarrica`) with the original author's
repository retained as `upstream` (`Luchosqi/algaewatch-villarrica`).

- The original author is not expected to contribute further development time,
  but the door to merging back upstream is deliberately kept open.
- Therefore: avoid gratuitous restructuring, keep commits reviewable by someone
  who did not attend the audit session, and preserve the original commit history
  and authorship.
- Decisions that would be hard to reverse — notably the map library — are
  recorded as provisional pending consultation with the original author.
