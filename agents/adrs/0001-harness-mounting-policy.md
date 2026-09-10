# ADR 0001: Harness Mounting Policy

## Status

Accepted. All three choices confirmed on 2026-09-09 and re-confirmed at the
`5dee2cf` kernel upgrade, when the second and third became live rather than
theoretical.

## Context

Agentic coding platforms do not consistently share global rules, memories,
skills, workflows, or subagent capabilities across devices and tools. A
project-local harness makes the operating contract travel with the repository
instead of with one person's tool configuration.

Three choices follow from that, and the kernel default is not right for every
project.

## Decision

### 1. The harness is a project-local `agents/` tree

It is the operating contract. Existing project rules are preserved and fused
rather than overwritten — here, the implicit rules in the root `README.md`
became PR-1 to PR-4 in `AGENTS.md`. The generic kernel does not remain
authoritative after mounting.

**The harness carries its own tooling.** `agents/harness_doctor.py` and
`agents/check_translations.py` live inside the harness tree rather than in the
project's `scripts/`, because a harness that cannot check itself without its
kernel is not portable. Copying `agents/` into another repository carries the
checks with it.

**No kernel backup is kept in this repository.** The kernel was cloned to a
scratch directory, diff-merged, and discarded. Provenance is recorded in
`agents/RUN_STATE.md` and in the vendored script's header, which is enough to
trace the source without carrying a second copy of it — and without publishing
the private kernel's template tree into a repository headed upstream. The cost
is that the doctor's `--kernel` template-adaptation check needs a fresh clone;
every other check runs without one.

### 2. The harness is split into a shared half and a local half

`agents/` is **project truth**: shared, committed, identical for every
contributor. `agents/local/` is **environment truth**: capabilities, machine
paths, tooling, raw session notes. It is never committed.

The test for which half something belongs to: *would another developer's agent
get confused if it had this?*

`agents/local/.gitignore` contains `*` and `!.gitignore`, so the directory
ignores its own contents and arrives empty in a fresh clone. That is the
adaptation mechanism, not a gap — a harness cannot inherit its author's
environment, so each machine is made to describe itself before implementation
work begins (GATE-LOCAL).

This stopped being theoretical when the project gained a second contributor. The
capability scan at `agents/reviews/20260909/capability_scan.md` describes one
Windows machine running Claude Code with subagents and no `gh` CLI. Shipping that
as a project-wide claim would hand the other contributor's agent a list of
capabilities it may not have.

### 3. The shared half is committed by default

The project carries its own operating context, and work stays consistent across
devices and platforms.

**This project is shared, deliberately.** The repository is being handed back to
the original author (`upstream`, `Luchosqi/algaewatch-villarrica`), and the
harness is a substantial part of what is being handed over: the audit findings,
the redesign in ADR 0004, and the gates that stop the audited defects returning
are all in `agents/`. A private mount would hand him the code and withhold the
reasoning.

The consequence is live rather than hypothetical: everything in `agents/` is
readable by him, including the audit's assessment of the modelling layer he
wrote. That is accepted, and it sets the register — the audit is recorded as
findings with reproduction commands, so he can check them, rather than as a
verdict he has to take on trust.

## Consequences

- Work is more consistent across devices and platforms.
- The project carries its own operating context, and the harness is portable
  into another repository without its kernel.
- Every clone requires a local setup step before implementation. Intended.
- The next kernel upgrade must re-clone the kernel to diff against, since no
  backup is kept. `agents/RUN_STATE.md` records the commit to diff from.
- `agents/harness_doctor.py` is vendored. Fix it in the kernel and re-vendor;
  editing it here means the next upgrade silently discards the change.
- Anything written in `agents/` is readable by both contributors. Write
  accordingly — candid, checkable, and addressed to a reader who was not in the
  audit session.

## Sources

- Kernel `agent-harness-kernel` `testing` @ `5dee2cf`, ADR 0001 template
- ADR-sf-0005 — collaboration model and author slugs
- ADR-sf-0006 — canonical language
