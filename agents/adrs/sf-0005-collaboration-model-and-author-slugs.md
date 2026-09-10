# ADR-sf-0005: Two contributors, author slugs, and handing the repository back

## Status

Accepted 2026-09-09.

## Context

The harness was mounted on the assumption recorded in `PROJECT_PROFILE.md` as
**solo-first, upstream-compatible**: development would proceed alone on the
owner's fork, with the original author's repository retained as `upstream` and
the door to merging back deliberately kept open. WI-003 existed to notify him,
eventually, that the modelling layer was being rebuilt.

That assumption no longer holds. The original author, **Luchosqi** — who wrote
the entirety of commit `4b37bea` — is joining the work, and the repository is
being handed back to him. The door is not being kept open; it is being walked
through.

The kernel upgrade to `5dee2cf` arrived at the same moment and is what makes this
tractable. It carries the multi-contributor machinery the project previously had
no use for: the shared/local split so one machine's capabilities are not shipped
as everyone's, per-developer capability scans, and author slugs for the IDs that
merge badly.

## Decision

### 1. This is a two-contributor project

`PROJECT_PROFILE.md`'s collaboration posture is rewritten. The consequences that
were previously precautionary — "avoid gratuitous restructuring, keep commits
reviewable by someone who did not attend the audit session, preserve the original
commit history and authorship" — are now load-bearing rather than polite.

WI-003 is absorbed into `agents/execution/HANDOFF.md`. Notifying him and handing
him the work are the same act, and splitting them into two would mean writing the
audit findings twice.

### 2. Author slugs

| Slug | Contributor |
|---|---|
| `sf` | StrawberryFrappe — repository owner, `origin` |
| `lq` | Luchosqi — original author, `upstream` |

- ADR filenames carry the slug: `sf-0005-decision-name.md`, referenced in prose
  as ADR-sf-0005.
- Review filenames carry it: `harness_upgrade_review.sf.md`. Review **folders**
  stay `YYYYMMDD/`, because the doctor identifies them by an eight-digit name.
- The slug records **who minted the ID**, not who owns the subject. This ADR is
  `sf` because `sf` wrote it, even though half its content is about `lq`.
- **A slug must not be a real ISO 639-1 language code.** `review.<slug>.md` and
  the translation form `FOO.<lang>.md` are the same shape, so a contributor
  slugged `es` or `en` would have their reviews parsed as translations. This is
  not hypothetical: `agents/check_translations.py` matched *any* letter pair
  until `harness_upgrade_review.sf.md` was read as a translation into the
  language "sf". The checker now matches a declared language list, and slug
  selection avoids the collision rather than relying on that.
- New rows go at the **end** of index tables, so two people adding at once
  produce a merge conflict rather than silently interleaving.

**ADRs 0001 through 0004 keep their bare numbers and belong to `sf`.** They were
minted before the second contributor arrived. Renaming them would break every
citation in the harness to fix a collision that cannot happen retroactively.

Numbering continues from the highest existing number regardless of slug: the next
ADR either contributor writes is `0007`, prefixed with their own slug.

### 3. Capability scans stop being project-wide

`agents/reviews/20260909/capability_scan.md` stays where it is, but it is now a
record of one machine on one day rather than a claim about the environment. Each
contributor keeps a live scan at `agents/local/CAPABILITIES.md`, which is never
committed.

This is not bookkeeping. That committed scan asserts subagents, worktrees, and a
working credential helper. An agent on the other contributor's machine reading it
as current would plan delegated reviews it may be unable to perform, and would
report them as done.

### 4. Concurrent work must not share a working tree

The mechanism is each contributor's own — worktrees, separate clones, containers,
or simply working serially — and belongs in their local scan, because one
person's directory layout means nothing on another's machine. The rule is shared;
the mechanism is not.

Corollary, recorded because it has teeth on the owner's machine, where three
worktrees currently share one repository: never bare `git stash` / `git stash pop`.
The stash stack is shared across trees.

## The Work Split

Agreed 2026-09-09. Recorded here because a split that lives only in a
conversation is not a split.

| Contributor | Scope | Items |
|---|---|---|
| `sf` | The model layer | WI-004 (baselines permanent), WI-005 (honest retrain per ADR 0004) |
| `lq` | The frontend | BL-009 risk palette, BL-010 overlay clipping, BL-013 staleness disclosure, BL-019 TRL-2 seal, BL-021 visual excess |

The split is by subsystem, so the two halves share no files. That is deliberate
with a pitch roughly one day out: a boundary that needs no coordination is worth
more than an optimal allocation that does.

The model half stays with `sf` because the audit context lives there — six
findings, their reproduction commands, and the reasoning in ADR 0004. Handing
that over would mean transferring the whole audit session first. The frontend
half is self-contained, has no dependency on the retrain, and its items are
written against named files.

**ADR 0003 (map library) is `lq`'s to settle.** It was held provisional pending
his opinion, and he now has it in front of him. Frontend work starting before he
answers risks doing Leaflet work twice.

## Consequences

- Everything in `agents/` is read by both contributors, including the audit's
  assessment of the modelling layer `lq` wrote. ADR 0001 records the register
  this demands: findings with reproduction commands, not verdicts.
- The harness gains a second working language. See ADR-sf-0006.
- Two contributors and roughly one day to the pitch means the split must hold.
  Renegotiating it costs more than either half is worth.
- Merge conflicts in index tables are the intended outcome, not a failure. A
  conflict is visible; a silent interleave is not.

## Sources

- Owner decision, 2026-09-09, recorded in `agents/intake/QUESTIONS_SUMMARY.md`
- Kernel `5dee2cf`, `fd122ff` — shared/local split and slug conventions
- ADR 0001 — mounting policy, shared-half choice
- ADR 0003 — map library, provisional pending `lq`
- ADR 0004 — the redesign the model half implements
