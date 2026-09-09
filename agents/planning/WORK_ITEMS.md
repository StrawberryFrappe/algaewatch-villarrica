# Work Items

Use this file for current, actionable work. Keep the larger backlog stable.

| ID | Status | Task | Owner | Evidence |
|---|---|---|---|---|
| WI-001 | in_progress | Mount harness and obtain user acceptance | agent | `agents/reviews/20260909/harness_mount_review.md` |
| WI-002 | blocked | Obtain Copernicus Data Space Ecosystem credentials. Owner will do this when development starts, approximately 11 hours from 2026-09-09 | user | Successful authenticated call against CDSE |
| WI-003 | pending | Notify the original author that the modelling layer is being rebuilt, and raise the map-library question (ADR 0003). Owner will do this approximately 8 hours from 2026-09-09, i.e. before WI-002 unblocks | user | Confirmation that the message was sent |
| WI-004 | pending | Make persistence and trivial-rule baselines permanent, re-runnable checks (BL-002) | agent | Recorded test output |
| WI-005 | pending | Honest retrain on station data: continuous target, local-baseline anomaly, chronological splits with embargo (BL-003 to BL-006) | agent | Metrics reported beside both baselines |
| WI-006 | pending | Upgrade the mounted harness to the revised kernel (BL-020) | agent | Doctor passes; new kernel commit recorded in `RUN_STATE.md` |

WI-002 blocks BL-007 and BL-008, and therefore milestone M3. It does not block
M2, which is the guaranteed deliverable.

Both owner-held items have committed timings as of 2026-09-09: WI-003 in roughly
8 hours, WI-002 in roughly 11 hours. WI-003 therefore resolves before WI-002
unblocks, so ADR 0003 should be settled before any frontend work begins.

WI-003 is not a technical blocker but is time-sensitive: ADR 0003 is held
provisional pending the original author's response, and frontend work should not
begin until it resolves.

## Status Values

- pending
- in_progress
- blocked
- done

## Rule

Do not mark a work item done until verification evidence is recorded.
