# Work Items

Use this file for current, actionable work. Keep the larger backlog stable.

Owner column uses author slugs (ADR-sf-0005): `sf` StrawberryFrappe,
`lq` Luchosqi, `user` either contributor acting as themselves rather than through
an agent.

| ID | Status | Task | Owner | Evidence |
|---|---|---|---|---|
| WI-001 | in_progress | Mount harness and obtain user acceptance | `sf` | `agents/reviews/20260909/harness_mount_review.md` |
| WI-002 | blocked | Obtain Copernicus Data Space Ecosystem credentials | user | Successful authenticated call against CDSE |
| WI-003 | done | Notify the original author that the modelling layer is being rebuilt, and raise the map-library question (ADR 0003) | `sf` | Absorbed into `agents/execution/HANDOFF.md`, which states both. Superseded as a separate errand by ADR-sf-0005 |
| WI-004 | pending | Make persistence and trivial-rule baselines permanent, re-runnable checks (BL-002) | `sf` | Recorded test output |
| WI-005 | pending | Honest retrain on station data: continuous target, local-baseline anomaly, chronological splits with embargo (BL-003 to BL-006) | `sf` | Metrics reported beside both baselines |
| WI-006 | done | Upgrade the mounted harness to the revised kernel (BL-020) | `sf` | Kernel `5dee2cf` recorded in `RUN_STATE.md`; doctor run in `agents/validation/DOCTOR.md`; review in `agents/reviews/20260909/harness_upgrade_review.sf.md` |
| WI-007 | pending | Hand the repository back: deliver `agents/execution/HANDOFF.md`, confirm `lq` can build his local half and run both checks | `sf` | `lq` confirms receipt and a passing `harness_doctor.py` run on his machine |
| WI-008 | pending | Settle ADR 0003 — Leaflet stands, or Mapbox returns | `lq` | ADR 0003 status moves from provisional to accepted or superseded |
| WI-009 | pending | Frontend credibility pass: BL-009, BL-010, BL-013, BL-019, BL-021 | `lq` | Screenshots of the running app, plus a colourblind simulation check for BL-009 |
| WI-010 | blocked | Install PyTorch, or record that BL-008 cannot proceed | user | `python -c "import torch"` succeeds on the machine that will run BL-008 |

## Dependencies

- WI-002 blocks BL-007 and BL-008, therefore milestone M3. It does **not** block
  M2, which is the guaranteed deliverable.
- WI-010 blocks BL-008 independently of WI-002. PyTorch is binding from the
  supervisor (SRC-003, ADR 0002) and is **not installed** on the owner's machine,
  found during the 2026-09-09 local capability scan. M2 is unaffected — it
  deliberately stays scikit-learn.
- WI-008 gates WI-009. Frontend work starting before the map library is settled
  risks doing Leaflet work twice.
- WI-004 gates WI-005 by sequencing choice, not by technical necessity. Making
  the baselines executable first means the new model is measured against them
  from its first run rather than compared retrospectively and flattered.

## Status Values

- pending
- in_progress
- blocked
- done

## Rules

- Do not mark a work item done until verification evidence is recorded.
- Append new rows at the end, so concurrent additions by two contributors
  conflict visibly rather than interleaving silently.
