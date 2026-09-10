# ADR-sf-0006: English is canonical; Spanish siblings for entry documents

## Status

Accepted 2026-09-09.

## Context

The project is Spanish-facing. The root `README.md`, the design handoff, and
every string in the dashboard are Spanish. The harness under `agents/` is
entirely English, because one person wrote it and that is the language they wrote
it in — never a decision, just a default.

With `lq` joining (ADR-sf-0005), that default becomes a real question. He is a
Spanish speaker, and the harness is a substantial part of what is being handed
over: the audit findings, the redesign, and the gates that stop the audited
defects returning. A harness he cannot read comfortably is a harness he will not
use, and the gates then protect nothing.

Kernel `e22f283` added a translation protocol and `GATE-I18N` for exactly this.
The question it forces is which language is canonical — because canonical is
where decisions are made, and a translation is never that.

## Decision

### English is canonical

Every translatable document has one canonical file, `FOO.md`, in English. Where a
translation and its source disagree, the source wins until the translation is
brought current.

Spanish was considered and rejected on cost, not on principle. Making Spanish
canonical is the more honest fit for a Spanish-speaking team working on a
Spanish-facing product — but it means re-authoring roughly twenty existing
documents, including four ADRs and an audit, in the day before a pitch. A
canonical language that is aspirational is worse than one that is merely
inherited: the documents would drift into the language they were actually
maintained in, and the ADR would be quietly false.

Revisit this after the pitch. If `lq` ends up maintaining the harness, the
canonical language should follow him. **Changing the canonical language is an
ADR, not an edit.**

### Scope: entry documents only

Translated, as `FOO.es.md` beside the source:

| File | Why |
|---|---|
| `AGENTS.md` | The operating rules both contributors are held to |
| `agents/README.md` | The map into everything else |
| `agents/RUN_STATE.md` | Where the project actually is |
| `agents/LOCAL_SETUP.md` | He cannot start without building his local half |
| `agents/execution/HANDOFF.md` | Written to him; the single most important one |

Not translated, and this is a decision rather than an omission:

- **ADRs, the brief, the profile, the gates, the source manifest.** Read once,
  deeply, by someone who has already decided to engage. Translating them doubles
  a maintenance surface that GATE-I18N will then hold us to on every edit.
- **Dated records** — reviews, evidence entries, logbook notes. Read rarely, by
  whoever went looking. The protocol says as much.
- **Source material from outside the harness.** The design handoff and the root
  README are already Spanish and are `lq`'s own words in places. Retranslating
  someone else's document to make it consistent with the harness replaces their
  words with the agent's.

If `lq` needs a document that is not translated, translate it then and add it to
the table. The scope is a starting point, not a boundary.

### Line endings are pinned

`.gitattributes` pins `AGENTS.md`, `AGENTS.es.md` and `agents/**/*.md` to LF.

This is not tidiness. `GATE-I18N` compares `git hash-object --no-filters`, which
hashes the bytes on disk. The owner's machine has `core.autocrlf=true` and the
harness files were CRLF; a contributor checking out LF would see mismatches on
files nobody edited, and the gate would report drift that does not exist — worse
than reporting none, because a checker that cries wolf gets ignored.

Scoped to the harness deliberately. A repo-wide `*.md text eol=lf` would
renormalize `lq`'s own README files into a large diff in the same commit that
hands him the repository.

### The gate has an artifact

`agents/check_translations.py` walks the translations, hashes each declared
source, and compares. `agents/harness_doctor.py` does **not** check this — the
kernel ships no i18n check — and `GATES.md` requires that a gate whose evidence
is a claim rather than an artifact has not been passed.

## Consequences

- **Translate on touch.** Whoever edits a canonical file with a Spanish sibling
  updates the sibling in the same change, or leaves it stale deliberately and
  says so. Silent drift is the failure this exists to prevent; visible, dated,
  explained drift is an acceptable interim state.
- Refreshing a translation means re-reading the source in full. A diff is a hint
  about where to look, not the work.
- Five files now cost double to edit. That is the price of the gate, and it is
  why the scope stops where it does.
- Terminology binds to `agents/i18n/GLOSSARY.md`. A term with no agreed
  translation goes in the glossary before it appears in prose.
- The canonical/translated distinction is not a status ranking. It is a
  tie-breaking rule, and its only job is to make disagreement resolvable.

## Sources

- Owner decision, 2026-09-09
- Kernel `e22f283`, `5dee2cf` — the protocol and the line-ending caveat
- `agents/i18n/TRANSLATION_PROTOCOL.md`
- ADR-sf-0005 — the second contributor this is for
