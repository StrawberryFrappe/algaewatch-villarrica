#!/usr/bin/env python3
"""Check GATE-I18N: is every translation current with the source it names?

Project-specific. Unlike `agents/harness_doctor.py`, this is not vendored from
the kernel -- the kernel ships no i18n check, and `agents/validation/GATES.md`
requires a gate's evidence to be an artifact rather than a claim.

It answers exactly one question per translated file, the one in
`agents/i18n/TRANSLATION_PROTOCOL.md`:

    does this translation's recorded source_sha still match the hash of the
    canonical file it names?

A match means the translation was written against the source as it now stands.
It does not mean the translation is good. A mismatch is a fact, not a verdict:
the source moved, and nothing here knows whether the change mattered.

Usage:
    python agents/check_translations.py [--root .] [--lang es]

Exit status is 0 when every translation is current, 1 otherwise, so it can gate
a commit or a CI step.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Languages this project actually carries. Declared explicitly rather than
# inferred from the filename, because `FOO.<lang>.md` and the author-slug form
# `review.<slug>.md` are the same shape: `harness_upgrade_review.sf.md` was
# parsed as a translation into the language "sf" until this list existed. Add a
# code here when the project adds a language -- and never pick an author slug
# that is a real ISO 639-1 code (ADR-sf-0005).
LANGUAGES = {"es"}

# FOO.<lang>.md, where <lang> is a lowercase ISO 639-1 code.
TRANSLATION_RE = re.compile(r"^(?P<stem>.+)\.(?P<lang>[a-z]{2})\.md$")

FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---\r?\n", re.DOTALL)

REQUIRED_FIELDS = ("source", "source_sha", "source_sha_algo")

# Directories that never carry translations and would only slow the walk.
SKIP_DIRS = {".git", "node_modules", "__pycache__", "data", "dist", "build"}


def blob_sha(path: Path) -> str:
    """Hash a file the way the protocol specifies.

    `--no-filters` is load-bearing. Without it git applies whatever line-ending
    conversion the local `core.autocrlf` happens to be set to, so two
    contributors hashing the same unchanged file get different answers, and the
    gate reports drift that does not exist.
    """
    result = subprocess.run(
        ["git", "hash-object", "--no-filters", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def parse_frontmatter(text: str) -> dict[str, str] | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def find_translations(root: Path, lang: str | None) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        match = TRANSLATION_RE.match(path.name)
        if not match:
            continue
        code = match.group("lang")
        if code not in LANGUAGES:
            continue
        if lang is None or code == lang:
            found.append(path)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that every translation is current with its source."
    )
    parser.add_argument("--root", default=".", help="Project root to check.")
    parser.add_argument(
        "--lang",
        default=None,
        help="Only check this language code. Default: every language found.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    translations = find_translations(root, args.lang)

    print("Translation Currency Check (GATE-I18N)")
    print(f"root: {root}")

    if not translations:
        print("no translations found - nothing to check")
        return 0

    problems: list[str] = []

    for path in translations:
        rel = path.relative_to(root).as_posix()
        fields = parse_frontmatter(path.read_text(encoding="utf-8"))

        if fields is None:
            problems.append(f"{rel}: no frontmatter block")
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in fields]
        if missing:
            problems.append(f"{rel}: frontmatter missing {', '.join(missing)}")
            continue

        algo = fields["source_sha_algo"]
        if algo != "git-blob-sha1":
            problems.append(
                f"{rel}: source_sha_algo is '{algo}', which this checker cannot verify"
            )
            continue

        source = root / fields["source"]
        if not source.is_file():
            problems.append(f"{rel}: source does not exist: {fields['source']}")
            continue

        actual = blob_sha(source)
        recorded = fields["source_sha"]

        if actual == recorded:
            print(f"  current  {rel}  <- {fields['source']}")
        else:
            problems.append(
                f"{rel}: STALE - {fields['source']} is now {actual}, "
                f"translation recorded {recorded}"
            )

    print(f"checked: {len(translations)}   problems: {len(problems)}")
    for problem in problems:
        print(f"PROBLEM: {problem}")

    if problems:
        print(
            "\nA stale translation is not a failure to fix by editing the hash. "
            "Re-read the source in full, bring the translation current, then "
            "record the new hash."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
