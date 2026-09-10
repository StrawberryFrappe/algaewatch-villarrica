# Glossary — English / Spanish

Terms bind here. A translation must never invent its own rendering of a term this
file already defines, and a term with no agreed translation belongs here before
it appears in prose.

English is canonical (ADR-sf-0006). Language pair: `en` → `es`.

## Domain

| English | Spanish | Note |
|---|---|---|
| bloom | floración | Cyanobacteria bloom. `floración de algas` in full where context needs it |
| Floating Algae Index (FAI) | Índice de Algas Flotantes (FAI) | **Keep the acronym FAI** — it is the column name, the API field, and what the team says out loud |
| lake pixel | píxel de lago | The training unit after ADR 0004 |
| pass / satellite pass | pasada | A Sentinel-2 acquisition date. `fecha de pasada` for the date itself |
| water mask | máscara de agua | Via the Sentinel-2 SCL band |
| in-situ | in situ | Latin in both; unitalicised, no hyphen in Spanish |
| station | estación | The four monitoring points. Coordinates are placeholders |
| risk score | puntaje de riesgo | The 0–100 value `/risk` serves |
| staleness | antigüedad del dato | How old the underlying pass is. Not `obsolescencia`, which reads as decay |

## Modelling

| English | Spanish | Note |
|---|---|---|
| baseline | línea base | A comparison model. Distinct from the next row |
| local baseline | línea base local | ADR 0004 D2 — a location's own reference level, not a pooled constant |
| persistence baseline | línea base de persistencia | "Predict the same as today" |
| trivial-rule baseline | línea base de regla trivial | E.g. predict by station name alone |
| leakage | filtración | Of information between train and validation. Not `fuga` |
| embargo | embargo | Same word. The gap between train end and validation start |
| forward-fill | relleno hacia adelante | The fabrication PR-3 prohibits |
| holdout | conjunto de validación temporal | No good short Spanish equivalent; say it in full |
| target / label | variable objetivo / etiqueta | ADR 0004 replaces the label with a continuous target |
| threshold | umbral | MI-3 places it at serving time, never in the label |
| horizon | horizonte | Seven days here |

## Harness

These stay **untranslated**, because they are what the team says out loud and a
Spanish rendering would be a word nobody uses:

`harness`, `gate`, `backlog`, `ADR`, `handoff`, `commit`, `merge`, `fork`,
`upstream`, `worktree`, `stub`, `mock`, `slug`.

Gate identifiers — `GATE-HM`, `GATE-LOCAL`, `GATE-DR`, `GATE-TEST`, `GATE-PQ`,
`GATE-MODEL`, `GATE-I18N` — and rule identifiers — `PR-1`…`PR-4`, `MI-1`…`MI-3`,
`D1`…`D4` — are opaque tokens. Never translate, never renumber.

| English | Spanish | Note |
|---|---|---|
| evidence | evidencia | An artifact, not an assertion |
| finding | hallazgo | From a review or an audit |
| blocker | bloqueante | A finding that stops forward work |
| work item | ítem de trabajo | The `WI-` table |
| canonical file | archivo canónico | Where a decision is made |
| capability scan | capability scan | Untranslated; it names a specific file |

## Required Texts

Two Spanish strings are mandated by the design handoff (PR-4) and are **source
text, not translations**. Reproduce them exactly, and never round-trip them
through English:

- `TRL 2 · resultados no validados en campo`
- The AI-panel disclaimer hardcoded in `backend/app/routers/forecast.py`

## Rules

- A term that appears in a translated document and is not here should be added
  here in the same change.
- Where the English term is what the team actually says, keep it and say so
  above. Translating a word nobody uses is worse than leaving it alone.
- Product-facing Spanish copy — dashboard strings, the README, the design
  handoff — is not governed by this file. That is source material, and it is
  already Spanish.
