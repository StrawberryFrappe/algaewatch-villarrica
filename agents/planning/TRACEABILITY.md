# Traceability

Traceability links sources, user decisions, ADRs, work items, tests, evidence,
and final behavior.

| Trace ID | Source / Decision | Work Item | Verification | Evidence |
|---|---|---|---|---|
| TR-001 | Kernel mount requested | WI-001 | Harness mount review | `agents/reviews/20260909/` |
| TR-002 | SRC-002 supervisor: improve training | ADR 0004 D1, D2, D4 → WI-005 | Retrain with chronological splits and no fabricated rows | `EVIDENCE_INDEX.md` EV-007 onward |
| TR-003 | SRC-002 supervisor: understand the numbers | Audit findings → `PROJECT_BRIEF.md` | Every figure reproducible from committed CSVs | `EVIDENCE_INDEX.md` EV-001 to EV-009 |
| TR-004 | SRC-003 supervisor: use PyTorch | ADR 0002 → BL-008 only | Model trains under PyTorch with quantile heads | Pending. WI-005 (M2) deliberately does **not** use PyTorch: ADR 0002 rejects it on the four-station framing, so the honest retrain stays scikit-learn |
| TR-005 | SRC-004 handoff mandates Mapbox; code ships Leaflet (CONF-003) | ADR 0003 provisional → WI-003 | Original author consulted; decision confirmed or reversed | Pending |
| TR-006 | Audit: trivial station rule beats the classifier | Rule MI-1 → BL-002 | Baseline comparison is a permanent, re-runnable check | EV-002 |
| TR-007 | Audit: shuffled cross-validation over duplicated rows | Rule MI-2 → BL-005, BL-006 | No shuffled splits; embargo present at the seam | EV-004, EV-005 |
| TR-008 | Audit: absolute pooled threshold encodes location | Rule MI-3, ADR 0004 D2 → BL-004 | Bloom rates no longer stratify by station | EV-001 |
| TR-009 | Audit: regressor loses to persistence | ADR 0004 → BL-002, BL-012 | Any shipped model reported beside persistence | EV-003 |
| TR-010 | Owner decision: GATE-PQ active | BL-009, BL-010, BL-013 | Screenshots of the running app | Pending |
| TR-011 | Root README overstates real-data coverage (CONF-001) | BL-011 | README consistent with the audit record | Pending |
| TR-012 | PR-2 credential hygiene, verified clean | Preserved rule in `AGENTS.md` | No tracked secrets; none in git history | EV-006 |

## Rules

- Traceability should grow as the project evolves.
- For requirements-heavy projects, preserve source-backed IDs.
- For lightweight projects, trace decisions and outcomes instead of inventing
  artificial requirements.
- Do not expose internal trace IDs in user-facing products unless the product
  itself is an admin/audit tool and the user approves it.
