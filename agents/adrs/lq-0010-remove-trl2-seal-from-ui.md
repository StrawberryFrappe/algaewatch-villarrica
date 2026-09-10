# ADR lq-0010: Remove the "TRL 2" seal from the UI

## Status

Accepted (owner decision, 2026-09-10). Deviates from PR-4 and the project-specific
GATE-PQ criterion; see Consequences.

## Context

`AGENTS.md` PR-4 and the design handoff (§"Datos", §"VALIDACIÓN", and the explicit
line "Conservar esos textos") require the maturity seal
**"TRL 2 · resultados no validados en campo"** to be preserved and visible. BL-019
tracked getting it actually rendered, and it was: on the Modelo view three times
(a stamp under the title, and prepended to both the VALIDACIÓN and the candidate
fold-table disclaimers) plus the header subtitle "· TRL 2".

During a demo-polish pass the owner reviewed the running dashboard and judged the
seal "unprofessional and weirdly self-aware" — it repeats, it leads with a
negative, and prepending "TRL 2 — no validado en campo." to every caveat reads as
the product apologising for itself. They asked for it removed from the UI.

The seal exists for a real reason: this prototype must not be mistaken for an
operational or sanitary alert system, and both models currently lose to their
baselines. That function has to be kept even if the specific wording goes.

## Decision

Remove the "TRL 2" seal wording from the **UI only**:

- Delete the `TRL_SEAL` constant and its three uses in
  `frontend/src/components/ModelView.jsx`; delete `.trl-seal` / `.trl-seal-dot`
  from `frontend/src/styles/views.css`.
- Drop "· TRL 2" from the header subtitle (`frontend/src/components/Header.jsx`).
- The backend `caveats` strings in both `metrics.json` files still open with
  "TRL 2 — no validado en campo."; strip that one sentence **on render** with a
  small `stripSeal()` helper in `ModelView.jsx`. The model artifacts are left
  byte-unchanged, so GATE-MODEL and the "artifacts unchanged" invariant in
  `RUN_STATE.md` are untouched.

What is kept, so the honesty function survives:

- One neutral line on the Modelo view: **"Prototipo de investigación. Las salidas
  no son alertas sanitarias ni operacionales."**
- The README's top-of-file TRL-2 block and `AGENTS.md` PR-4 itself are **not**
  changed here — that is a separate call for the owner.
- The **AI-panel disclaimer** ("ALGAEWATCH-LM · SÍNTESIS SOBRE LA SALIDA DEL
  MODELO, NO VALIDADA EN CAMPO", `backend/app/routers/forecast.py`) — the other
  text PR-4 mandates — is **untouched**.
- The substantive run caveats (sample size, MI-1 baseline losses, spatial
  autocorrelation) still render; only the seal sentence is stripped.

## Consequences

- **PR-4 is knowingly deviated** for the seal text. This ADR is the record PR-4
  asks for ("Deviations from it are allowed but must be recorded as ADRs").
- **GATE-PQ**: the project-specific criteria in `agents/validation/GATES.md` do
  not list the seal, so this does not by itself fail GATE-PQ; but PR-4 compliance
  was previously cited as "partial, the seal now rendered" and that citation is
  now out of date. `AGENTS.md` PR-4 and `GATES.md` should be updated by the owner
  to reference this ADR.
- If a reviewer or supervisor requires the seal back, reverting is a small,
  localised change (this ADR lists every touch point).
- The header subtitle change is cosmetic and carries no rule weight.

## Sources

- Owner decision, 2026-09-10 (demo-polish session), recorded via the planning
  flow in `/home/strawberry/.claude/plans/`.
- `AGENTS.md` PR-4; design handoff `design_handoff_algaewatch_villarrica/README.md`
  line 47.
- BL-019 (seal previously unrendered, then fixed).
- Touch points: `frontend/src/components/ModelView.jsx`,
  `frontend/src/components/Header.jsx`, `frontend/src/styles/views.css`.
