# Traceability

Traceability links sources, user decisions, ADRs, work items, tests, evidence,
and final behavior.

| Trace ID | Source / Decision | Work Item | Verification | Evidence |
|---|---|---|---|---|
| TR-001 | Kernel mount requested | WI-001 | Harness mount review | `agents/reviews/20260909/` |
| TR-002 | SRC-002 supervisor: improve training | ADR 0004 D1, D2, D4 → WI-005 | Retrain with chronological splits and no fabricated rows | `EVIDENCE_INDEX.md` EV-007 onward |
| TR-003 | SRC-002 supervisor: understand the numbers | Audit findings → `PROJECT_BRIEF.md` | Every figure reproducible from committed CSVs | `EVIDENCE_INDEX.md` EV-001 to EV-009 |
| TR-004 | SRC-003 supervisor: use PyTorch | ADR 0002 → BL-008 only | Model trains under PyTorch with quantile heads | Pending. WI-005 (M2) deliberately does **not** use PyTorch: ADR 0002 rejects it on the four-station framing, so the honest retrain stays scikit-learn |
| TR-005 | SRC-004 handoff mandates Mapbox; code ships Leaflet (CONF-003) | ADR 0003 provisional → WI-008 | `lq` settles it; ADR 0003 moves from provisional to accepted or superseded | **Done** 2026-09-10. `lq` confirmed Leaflet; ADR 0003 status now Accepted (provisional hold lifted); WI-008 done |
| TR-006 | Audit: trivial station rule beats the classifier | Rule MI-1 → BL-002 | Baseline comparison is a permanent, re-runnable check | EV-002 |
| TR-007 | Audit: shuffled cross-validation over duplicated rows | Rule MI-2 → BL-005, BL-006 | No shuffled splits; embargo present at the seam | EV-004, EV-005 |
| TR-008 | Audit: absolute pooled threshold encodes location | Rule MI-3, ADR 0004 D2 → BL-004 | Bloom rates no longer stratify by station | EV-001 |
| TR-009 | Audit: regressor loses to persistence | ADR 0004 → BL-002, BL-012 | Any shipped model reported beside persistence | EV-003 |
| TR-010 | Owner decision: GATE-PQ active | WI-009 → BL-009, BL-010, BL-013, BL-019, BL-021 | Screenshots of the running app; palette CVD validation | **Done** 2026-09-10. `agents/reviews/20260910/frontend_credibility_pass.lq.md` + `frontend_credibility_pass_screens/`; handoff deviations in ADR-lq-0007 |
| TR-011 | Root README overstates real-data coverage (CONF-001) | BL-011 | README consistent with the audit record | Pending |
| TR-012 | PR-2 credential hygiene, verified clean | Preserved rule in `AGENTS.md` | No tracked secrets; none in git history | EV-006 |
| TR-013 | Owner decision: Luchosqi joins; repository handed back | ADR-sf-0005 → WI-007, BL-022 | `lq` confirms receipt and runs the doctor on his machine | Pending |
| TR-014 | Owner decision: two working languages, English canonical | ADR-sf-0006 → BL-023 | `python agents/check_translations.py` passes; five translations current | `agents/validation/DOCTOR.md` |
| TR-015 | Kernel `798f1b3`: doctor follows citations | Vendored `agents/harness_doctor.py` | `--strict` run reports zero hard blockers, dangling citations included | `agents/validation/DOCTOR.md` |
| TR-016 | Kernel `fd122ff`: shared/local split | GATE-LOCAL → `agents/local/CAPABILITIES.md` | File exists and `git check-ignore` confirms it is not committed | `agents/validation/DOCTOR.md` |
| TR-017 | 2026-09-09 local scan: PyTorch not installed | ADR 0002 / SRC-003 → BL-008 blocked, BL-024, WI-010 | `python -c "import torch"` succeeds where BL-008 will run | Pending. Blocks BL-008 independently of the Copernicus credentials |
| TR-018 | GATE-PQ: risk palette not colourblind-safe; handoff glass idiom | ADR-lq-0007 → BL-009, BL-021 | Documented deviations from SRC-004; palette passes `validate_palette.js --ordinal` and CVD sim | `agents/adrs/lq-0007-frontend-credibility-pass.md`; review 20260910 |
| TR-019 | Owner redirect 2026-09-10: lighter/pastel theme, topbar nav, contained layout | ADR-lq-0008 → WI-011 | Wholesale visual-layer deviation from SRC-004 recorded; light-mode risk ramp re-validated; four views screenshotted on real data | `agents/adrs/lq-0008-light-pastel-theme-and-topbar.md`; `agents/reviews/20260910/light-theme-pass_screens/` |

## Rules

- Traceability should grow as the project evolves.
- For requirements-heavy projects, preserve source-backed IDs.
- For lightweight projects, trace decisions and outcomes instead of inventing
  artificial requirements.
- Do not expose internal trace IDs in user-facing products unless the product
  itself is an admin/audit tool and the user approves it.
