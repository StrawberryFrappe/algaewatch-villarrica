# Source Manifest

Record the source materials that govern this project.

| ID | Source | Type | Authority | Notes |
|---|---|---|---|---|
| SRC-001 | Workshop assignment: predict algae appearance on a specific lake using freely available satellite data and any obtainable sources | Verbal brief | Highest — defines the deliverable | Not held as a document in this repo. Recorded from the owner's account on 2026-09-09 |
| SRC-002 | Supervisor feedback: training must be improved; the team must understand the numbers it is juggling | Verbal review | Highest — overrides prior implementation choices | Directly motivates ADR 0004 and the MI-1..MI-3 rules in `AGENTS.md` |
| SRC-003 | Supervisor direction: use PyTorch | Verbal review | Binding — see ADR 0002 | Accepted as a hard constraint by the owner |
| SRC-004 | `design_handoff_algaewatch_villarrica/README.md` | Design specification | Governs frontend layout, views, and interaction | Itself a generated artifact adopted as spec. Deviations permitted but must be recorded as ADRs |
| SRC-005 | Root `README.md` | Project documentation | Governs pipeline intent and layout rules | Source of preserved rules PR-1 through PR-4. Its status claims are partly overstated — see SRC-009 |
| SRC-006 | `data/processed/fai_series_raw.csv` | Primary data | Authoritative record of real satellite observations | 56 real Sentinel-2 pass dates, 2025-09-04 to 2026-08-22. Median gap 3 days, maximum 32 |
| SRC-007 | `data/processed/fai_grid_latest.csv` | Primary data | Authoritative FAI raster sample | 1,860 water pixels, single date only. Must be extended across dates for the per-pixel redesign |
| SRC-008 | `src/model/artifacts/metrics.json` | Model record | Superseded as a performance claim | Its own `caveats` field is honest; the surrounding README prose is not. Retained for provenance |
| SRC-009 | Audit session, 2026-09-09 | Analysis | Supersedes SRC-005 and SRC-008 on model performance | Findings recorded in `agents/intake/PROJECT_BRIEF.md`; reproduction commands in `agents/validation/EVIDENCE_INDEX.md` |
| SRC-010 | Hu, C. (2009), Floating Algae Index | Literature | Governs the FAI formula | Implemented in `src/features/fai.py`; implementation verified to match |
| SRC-011 | `data/processed/training_dataset.csv` | Derived data | Not authoritative | Contains forward-filled rows. Retained as evidence of the audited defect; must not be used to train a shipped model |

## Authority Order

1. **SRC-001 / SRC-002 / SRC-003** — the workshop brief and supervisor direction.
   These define what the project is for and override any implementation already
   in the repository.
2. **SRC-009** — the 2026-09-09 audit, where it contradicts earlier project
   claims about model performance. It is reproducible from committed data; the
   earlier claims are not.
3. **SRC-006 / SRC-007 / SRC-010** — real observational data and the published
   index definition. Facts, not opinions.
4. **SRC-004** — the design handoff, for frontend questions.
5. **SRC-005** — the root README, for pipeline intent and layout rules, except
   where superseded by SRC-009.
6. **SRC-008 / SRC-011** — historical artifacts, retained for provenance only.

## Recorded Source Conflicts

| ID | Conflict | Resolution |
|---|---|---|
| CONF-001 | SRC-005 states "sin mocks, todo el backend corre sobre datos reales", but ERA5 weather was never collected, in-situ is a stub, and station coordinates are placeholders | SRC-009 wins. The FAI half of the claim is true; the rest is not. The README will be corrected as backlog item BL-011 |
| CONF-002 | SRC-008 reports precision 0.84 / recall 0.47 / AUC 0.90 as model performance | SRC-009 wins. Those figures came from a leaking pipeline and are beaten by trivial baselines. The file is retained but is no longer a performance claim |
| CONF-003 | SRC-004 mandates Mapbox GL JS; the code ships Leaflet with Esri satellite tiles | Recorded in ADR 0003 as a provisional deviation. Kept open pending consultation with the original author |
| CONF-004 | SRC-003 requires PyTorch; the repository ships scikit-learn and lists `xgboost` in `requirements.txt` | SRC-003 wins. See ADR 0002. `xgboost` is listed as a dependency but is not imported anywhere in the codebase |

## Source Handling Rules

- Do not rewrite original source documents unless explicitly asked.
- If extracted or summarized requirements conflict with original sources, record
  the conflict and ask for a decision.
- Preserve source-backed IDs when they exist.
- Derived requirements must be labeled and traceable to source/user decisions.
- SRC-001 through SRC-003 are verbal and held only in this manifest. If the
  supervisor issues written direction, add it as a new source and raise its
  authority above this record.
