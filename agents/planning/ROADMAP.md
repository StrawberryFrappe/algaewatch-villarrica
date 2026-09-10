# Roadmap

## Current Goal

Convert a prototype whose predictive layer does not predict into one whose claims
are honest, reproducible, and defensible at the workshop pitch (ASM-001:
approximately 2026-09-10).

The target is not a high accuracy number. It is a correct methodology with its
numbers understood — which is precisely what the supervisor asked for (SRC-002).

## Milestones

| Milestone | Outcome | Evidence |
|---|---|---|
| M0 Harness mounted | Operating contract in place; audit findings recorded as durable project documents | `agents/reviews/20260909/harness_mount_review.md`, doctor run recorded in `agents/validation/DOCTOR.md` |
| M1 Baselines made permanent | Persistence and trivial-rule baselines exist as re-runnable checks rather than ad-hoc analysis; rule MI-1 becomes enforceable | Test output recorded in `agents/validation/EVIDENCE_INDEX.md` |
| M2 Honest retrain, no credentials | D1, D2 and D4 applied to existing station data. Continuous target, local-baseline anomaly, chronological splits with embargo, zero forward-filled training rows | Metrics reported beside both baselines; sample count stated as real pairs, not derived rows |
| M3 Per-pixel redesign | D3 applied: grid backfilled across all 56 passes, model trained on lake pixels | Recorded sample counts and chronological validation results |
| M4 Frontend credibility pass | Colourblind-safe risk scale (BL-009), risk overlay clipped to the lake (BL-010), staleness disclosure extended beyond the header (BL-013), the mandated TRL-2 seal rendered (BL-019), and the generated-default visual excess reduced (BL-021) — the full WI-009 set | Screenshots of the running app, plus a colourblind simulation check for BL-009 |
| M5 Pitch narrative | The audit, the redesign, and the honest numbers assembled into a defensible account | Pitch material, with claims traceable to `EVIDENCE_INDEX.md` |

M2 is credential-free and is the guaranteed deliverable. M3 depends on the P0
external dependency and is the upgrade, not the floor.

## Ownership

Since 2026-09-09 the project has two contributors (ADR-sf-0005). M1, M2 and M3
are `sf`'s; **M4 is `lq`'s**; M5 is joint. The split is by subsystem, so the two
tracks share no files and can run concurrently — which is the point, with the
pitch roughly one day out.

M3 carries a second blocker beyond the Copernicus credentials: PyTorch is binding
from the supervisor (ADR 0002) and is not installed on the owner's machine. See
WI-010.

## Sequencing Rationale

M1 precedes M2 deliberately. Making the baselines executable before retraining
means the new model is measured against them from its first run, rather than
being compared retrospectively and flattered.

M4 was originally sequenced after M2 because ADR 0003 asked that Leaflet-specific
work be deferred while the map decision remained provisional. **That sequencing
is now moot**: M4 belongs to `lq`, who is the person ADR 0003 was waiting on, so
he settles it (WI-008) and then proceeds. The two original M4 items are
library-independent and safe under either outcome; BL-010, overlay clipping, is
the one that is not, so it follows his decision.

ERA5-Land backfill is deliberately **not** a milestone. It is the most commonly
assumed next step, and it is genuinely valuable as the only available source of
change-drivers, but it cannot be completed and validated before the pitch. It
belongs to the roadmap beyond it, recorded in `BACKLOG.md` as BL-012.

## Stop Conditions

- Harness not accepted.
- Source authority unclear.
- Product goal unclear.
- Validation gate cannot be satisfied.
- Agent capability downgrade blocks required review or verification.

Project-specific additions:

- A metric is about to be reported without its persistence and trivial-rule
  baselines. Stop and add them (rule MI-1).
- A training path is about to consume forward-filled rows. Stop; this is
  prohibited by rule PR-3.
- A validation split is about to shuffle time-ordered rows, or to omit the
  horizon-length embargo. Stop (rule MI-2).
