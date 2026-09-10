# Doctor Workflow

Doctor is a harness coherence check, not a product runtime.

## Hard Blockers

- Root `AGENTS.md` does not point to `agents/`.
- `agents/RUN_STATE.md` does not show the current phase.
- Implementation is marked ready before harness review and user acceptance.
- Existing project rules were overwritten or ignored without a recorded
  decision.
- Major stack/product/deployment decisions are undocumented.
- Local/raw memory is not gitignored.
- Validation gates do not identify evidence.

## Warnings

- Placeholder sections remain.
- ADRs are missing for medium-impact decisions.
- Review index is stale.
- Traceability is sparse.
- Deployment target is deferred.
- Subagents are unavailable, reducing review strength.

## Doctor Record

| Date | Result | Hard Blockers | Warnings | Next Action |
|---|---|---|---|---|
| 2026-09-09 | fail | 2 | 0 | First run during mounting, before `DOCTOR.md` and `reviews_index.md` existed. Both written; re-run |
| 2026-09-09 | pass | 0 | 0 | Structural pass, but see the note below: the script did not catch the P0 the independent review found |
| 2026-09-09 | pass | 0 | 0 | After resolving all eleven review findings. Present the mounted harness for user acceptance |
| 2026-09-09 | pass | 0 | 0 | Kernel `5dee2cf`, run as `python agents/harness_doctor.py --root . --strict --kernel <clone>`. After resolving all eight upgrade-review findings. `agents/check_translations.py` also passes, 5 of 5 current. Present the upgraded harness for user acceptance |
| 2026-09-10 | **fail** | 1 | 0 | First run of the WI-004 session, in a fresh worktree. `BLOCKER [local-mount]: agents/local/CAPABILITIES.md is missing`. The previous `RUN_STATE.md` asserted that file existed and had cleared GATE-LOCAL; it did not exist in either the worktree or the main checkout. See the note below |
| 2026-09-10 | pass | 0 | 0 | After writing a fresh `agents/local/CAPABILITIES.md` for this machine. Proceeded to WI-004 |
| 2026-09-10 | pass | 0 | 0 | After WI-004 landed: new modules, tests, ADR-sf-0007, evidence rows EV-014 to EV-017, backlog and work-item updates. `agents/check_translations.py` also passes, 5 of 5 current. Next: WI-005 |

### Script Limitation Observed

The 2026-09-09 mount review found a P0 that `harness_doctor.py` reported as
clean: `RUN_STATE.md` asserted the harness review was complete while the review
file it pointed at did not exist. The script's dated-review check requires only
that *some* markdown file exist in a `YYYYMMDD/` folder, and `capability_scan.md`
satisfied that vacuously.

A green doctor run is a structural check, not a truth check. It does not verify
that a document's claims match reality, and it must not be treated as evidence
that they do.

### The Same Failure, Again — 2026-09-10

`RUN_STATE.md` stated: "Local half mounted. `agents/local/CAPABILITIES.md` exists
and is gitignored, clearing GATE-LOCAL." The file did not exist, in the worktree
or in the main checkout, and the first `--strict` run of the next session
reported it as a hard blocker.

This is the second instance of the same class of defect the mount review caught:
a harness document asserting a state that was never verified. Note the
difference in who caught it. The first time it took an independent reviewer;
this time the doctor caught it directly, because kernel `5dee2cf` added the
local-mount check. A gate whose evidence is the artifact itself is worth more
than a gate whose evidence is a sentence.

The general lesson stands and is worth restating: **do not write a state claim
into a harness document at the same moment you intend to make it true.** Write it
after the check passes, or write what you actually observed.

### A Third Instance, With A Twist — 2026-09-10

`RUN_STATE.md` and `SESSION_HANDOFF.sf.md` both recorded
`python agents/check_translations.py` as "5 of 5 current". On the first run of the
next session it reported one stale file. Same class of defect on the surface, and
the same lesson: the claim was written in the session that produced the state, and
was true of that session's working tree only.

The twist is that the claim was true when written and *the artifact it named was
correct too*. What was wrong was the check. `check_translations.py` hashed the
bytes on disk, and the previous session's working copy of `agents/RUN_STATE.md`
had CRLF line endings, so the hash it recorded described that copy rather than the
commit. Every checkout since gets LF under `.gitattributes` and disagrees. The
translation itself was complete and current. EV-018, and the reasoning now sits in
`agents/i18n/TRANSLATION_PROTOCOL.md`.

Worth separating from the first two instances, because the remedy is different. A
state claim that outran reality is fixed by writing claims after checks. A check
that answers differently in two trees of the same commit is fixed by fixing the
check — and until it is, "the gate passed here" is not transferable evidence. The
doctor is not implicated: it ships no i18n check, which is why this one is a
project script.

## Manual Blocker Review

The script checks structure. The blocker list above is judgement, and was
assessed by hand on 2026-09-09:

| Blocker | Status |
|---|---|
| Root `AGENTS.md` points to `agents/` | Satisfied — required read order and core rules present |
| `RUN_STATE.md` shows current phase | Satisfied — "Harness upgraded to kernel `5dee2cf` and split for two contributors; awaiting user acceptance" |
| Implementation marked ready prematurely | Not applicable — implementation explicitly blocked, no application code touched |
| Existing rules overwritten | Not applicable — no `AGENTS.md` or `CLAUDE.md` existed. Rules implicit in the README were preserved as PR-1 to PR-4 rather than discarded |
| Major decisions undocumented | Satisfied — stack in ADR 0002, map library in ADR 0003, modelling redesign in ADR 0004, deployment posture in `PROJECT_PROFILE.md` |
| Local memory not gitignored | Satisfied — `agents/.gitignore` excludes `local/**`; `agents/local/.gitignore` excludes everything but itself |
| Gates do not identify evidence | Satisfied — every gate in `GATES.md` names its evidence, and `EVIDENCE_INDEX.md` carries runnable reproduction commands |

## Known Warnings Carried Forward

These are accepted rather than resolved, and are tracked elsewhere:

- Deployment target deferred — deliberate, GATE-DEPLOY inactive.
- No test surface yet — GATE-TEST cannot pass until BL-002 lands.
- No frontend verification or screenshot evidence — GATE-PQ not yet exercised.
- Architecture documents (C4, 4+1, SRS) not mounted, to avoid shipping
  placeholder-only files. Recorded as a P2 open question.
- Thirteen mounted files are content-identical to the kernel template by design:
  `agents/README.md`, `agents/LOCAL_SETUP.md`, `agents/execution/WORKFLOW.md`,
  `agents/execution/REVIEW_PROTOCOL.md`, `agents/execution/LOGBOOK_POLICY.md`,
  and everything under `agents/templates/`. These describe generic agent process
  rather than anything project-specific, and adapting them would add wording
  without adding meaning. Nineteen files *are* genuinely adapted.
  `agents/i18n/TRANSLATION_PROTOCOL.md` is the one new file that is adapted — it
  carries a project section naming the language pair, the glossary and the
  checker. Project-specific content lives in `AGENTS.md` (rules PR-1 to PR-4,
  MI-1 to MI-3) and across intake, planning and validation. Recorded here so the
  identity is a decision rather than an oversight.

### The `--kernel` Adaptation Check Is Currently Defeated

Verified 2026-09-09, and recorded because a silently useless check is worse than
an absent one.

`--kernel` warns when an active document is byte-identical to its template. This
harness is pinned to LF (`.gitattributes`, ADR-sf-0006), while a fresh kernel
clone on a machine with `core.autocrlf=true` checks out CRLF. **Every** comparison
therefore differs, and the check reports nothing — including for the thirteen
files where it should fire.

The result is a `--kernel` run that reports zero warnings and means nothing by it.
Comparing with line endings normalised gives the real answer: 13 identical, 19
adapted.

Until the kernel pins its own line endings, check adaptation with a normalised
comparison rather than trusting a clean `--kernel` run:

```bash
python -c "
import pathlib, sys
k = pathlib.Path(sys.argv[1]) / 'kernel/templates/agents'
for p in pathlib.Path('agents').rglob('*.md'):
    t = k / p.relative_to('agents')
    if t.is_file() and p.read_bytes().replace(b'
', b'
') == t.read_bytes().replace(b'
', b'
'):
        print('identical:', p)
" <kernel-clone>
```

Carried to the kernel as part of BL-025.

## Script Policy

The doctor is **vendored into the harness** at `agents/harness_doctor.py`, not
kept in the project's `scripts/` and not left in the kernel. A harness is meant
to be copyable into another repository, and one that cannot check itself without
its kernel is not portable. Copying `agents/` carries its own doctor (ADR 0001).

It automates missing-file, placeholder, stale-path, referential-integrity and
contradiction checks. The workflow remains authoritative; the script is a
guardrail against theatrical completion.

```bash
python agents/harness_doctor.py --root . --strict
```

`--strict` promotes placeholder markers, empty dated review folders and a missing
local half from warnings to hard blockers. `--kernel <path>` enables the
template-adaptation check, which needs a fresh kernel clone because no backup is
kept in this repository.

GATE-I18N is **not** checked by the doctor — the kernel ships no i18n check. It
has its own artifact:

```bash
python agents/check_translations.py
```

## Upgrade Record

| Date | From | To | Method |
|---|---|---|---|
| 2026-09-09 | — | `a5f428d` | Initial mount |
| 2026-09-09 | `a5f428d` | `5dee2cf` | Diff-merge. Four files byte-identical to the old templates were replaced wholesale; `AGENTS.md`, `GATES.md` and ADR 0001 were merged by hand because project content lives in them |

The `5dee2cf` doctor's referential-integrity check earned itself immediately: it
caught the two live citations of a doctor script under `scripts/` — a path that
never existed in this repository — which the old doctor had passed, and then
caught two forward references to `agents/check_translations.py` introduced during
the upgrade before that file existed. It went on to catch three more forward
references to this upgrade's own review document. Every one was a claim written
slightly ahead of the artifact it named, which is the failure mode the check
exists for.
