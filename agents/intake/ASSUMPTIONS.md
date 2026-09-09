# Assumptions

Assumptions are temporary. Prefer asking the user during harness mounting.

Every assumption below was filled in from repository evidence or the 2026-09-09
audit session rather than from an explicit answer. They are listed so the owner
can correct them at the acceptance gate.

| ID | Assumption | Risk | Expiration / Review Trigger |
|---|---|---|---|
| ASM-001 | The pitch is approximately 33 hours from 2026-09-09, i.e. on 2026-09-10 | Medium. Drives every scope decision in `ROADMAP.md` | Correct at the acceptance gate if the date is wrong |
| ASM-002 | The satellite ingestion layer is correct and should be preserved | Low. FAI formula verified against Hu (2009); SCL water masking verified; rasters confirmed co-registered | Revisit if a per-pixel run produces physically implausible values |
| ASM-003 | The 56 collected pass dates are a collection choice, not a data ceiling. Sentinel-2 archive depth and per-pixel sampling can raise the sample count by orders of magnitude | Medium. Underpins the claim that the data problem is solvable | Falsified if Copernicus quota or archive coverage over this bbox proves restrictive |
| ASM-004 | Station coordinates are placeholders and carry no scientific meaning | Low. Stated as a pending item in `src/features/stations.py`; one placeholder demonstrably fell on land | Resolved if real coordinates arrive |
| ASM-005 | SNIA in-situ CSVs will not arrive before the pitch | Medium. If wrong, water temperature, pH and dissolved oxygen become available as features | Revisit immediately if the CSVs arrive |
| ASM-006 | A relaxed pairing window of 5 to 9 days is an acceptable stand-in for an exact 7-day horizon | Medium. Raises usable **date** pairs from 11 to 35 — equivalently 44 to 140 training rows once multiplied across the 4 stations, which is how the same fact is quoted in `PROJECT_BRIEF.md` and `PROJECT_PROFILE.md` — at the cost of a slightly fuzzy horizon | Confirm with the supervisor; state explicitly in any reported metric |
| ASM-007 | Neighbouring lake pixels are spatially autocorrelated, so a per-pixel sample count is not an independent-sample count | Low. Standard for raster data | Governs the validation design; do not report per-pixel counts as independent samples |
| ASM-008 | Purely temporal splitting is sufficient validation before the pitch, with spatial block cross-validation deferred | Medium. A purely temporal split still permits spatial optimism within a date | Must be stated as a limitation wherever metrics are reported |
| ASM-009 | Committed `data/processed/` CSVs and model artifacts should remain committed, so the project runs credential-free | Low. Deliberate choice documented in `.gitignore` | Revisit only if file sizes become unmanageable |
| ASM-010 | Resolved 2026-09-09, no longer an assumption. The owner confirmed the visual idiom is not a deliberate brand: full replacement if time allows, and at minimum removal of the decorative excess | Resolved | Promoted to BL-021 |
| ASM-011 | `xgboost` in `requirements.txt` is vestigial; it is imported nowhere | Low | Remove during dependency cleanup unless a use appears |
| ASM-012 | Gemini-generated prose in the "Análisis IA" panel is optional and must never compute a number | Low. The code already enforces a deterministic fallback | Preserve this property through any refactor |

## Rules

- Do not let assumptions silently become requirements.
- High-impact assumptions need ADRs or user confirmation.
- If a user correction invalidates an assumption, update affected planning,
  architecture, validation, and traceability docs.
