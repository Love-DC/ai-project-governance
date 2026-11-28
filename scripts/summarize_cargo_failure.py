#!/usr/bin/env python3
"""Emit a deliberately redacted, allow-listed summary of private Cargo failures."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ERROR_CODE_RE = re.compile(r"\berror\[(E\d{4})\]\s*:", re.IGNORECASE)
RUSTFMT_DIFF_RE = re.compile(
    r"^Diff in .*[\\/](?P<filename>[A-Za-z0-9_.-]+\.rs):(?P<line>\d+):?\s*$",
    re.MULTILINE,
)

CODE_GROUPS = {
    "import/module resolution": {"E0432", "E0433"},
    "name/type resolution": {"E0412", "E0425", "E0463"},
    "type/trait mismatch": {"E0277", "E0308"},
    "missing member": {"E0599", "E0609"},
    "ownership/borrow": {"E0382", "E0499", "E0502", "E0507"},
    "call/field shape": {"E0061", "E0063"},
    "unstable feature": {"E0554", "E0658"},
}

# Compiler diagnostics are scanned for known standard trait families, but
# the diagnostic itself is never emitted. Only one of these generic labels
# can cross the private commit-status boundary.
TRAIT_FAMILY_PATTERNS = (
    ("GDExtension binding/conversion bound", re.compile(r"\b(?:GodotConvert|ToGodot|FromGodot|GodotFfi|GodotClass|Exportable)\b")),
    ("thread-safety bound", re.compile(r"\b(?:Send|Sync)\b")),
    ("serialization bound", re.compile(r"\b(?:Serialize|Deserialize)\b")),
    ("formatting bound", re.compile(r"\b(?:Debug|Display)\b")),
    ("error-conversion bound", re.compile(r"\b(?:std::error::Error|Error)\b")),
    ("iterator/future bound", re.compile(r"\b(?:Iterator|IntoIterator|Future|IntoFuture)\b")),
    ("conversion bound", re.compile(r"\b(?:From|Into|TryFrom|TryInto|AsRef|AsMut|Borrow)\b")),
    ("comparison/hash bound", re.compile(r"\b(?:Eq|PartialEq|Ord|PartialOrd|Hash)\b")),
)


def classify_trait_family(text: str) -> str | None:
    """Map known trait spellings to generic labels without returning identifiers."""
    for label, pattern in TRAIT_FAMILY_PATTERNS:
        if pattern.search(text):
            return label
    return None


def summarize_text(text: str) -> str:
    """Return only compiler codes and broad categories, never source text."""
    normalized = ANSI_RE.sub("", text)
    codes = sorted({code.upper() for code in ERROR_CODE_RE.findall(normalized)})
    categories: set[str] = set()

    for label, members in CODE_GROUPS.items():
        if set(codes) & members:
            categories.add(label)

    if set(codes) & {"E0277"}:
        trait_family = classify_trait_family(normalized)
        if trait_family:
            categories.add(trait_family)

    lowered = normalized.lower()
    if re.search(r"\bdiff in\b|rustfmt.*(format|diff)|not formatted", lowered):
        categories.add("format check")
    if re.search(r"linking with .* failed|linker command failed|undefined symbols? for architecture", lowered):
        categories.add("linker")
    if "failed to run custom build command" in lowered:
        categories.add("build script")
    if re.search(r"test result: failed|test failed|failures:", lowered):
        categories.add("test")
    if re.search(r"could not compile|aborting due to \d+ previous error", lowered) and not codes:
        categories.add("compiler")

    if codes:
        code_text = "/".join(codes[:4])
        if len(codes) > 4:
            code_text += "/…"
        if not categories:
            categories.add("compiler")
        category_text = ", ".join(sorted(categories)[:2])
        return f"Rust {code_text} ({category_text})"[:120]

    if categories:
        return f"Cargo {', '.join(sorted(categories)[:2])} failure"[:120]
    if re.search(r"error:|fatal error|process didn't exit successfully", lowered):
        return "Cargo/native build failure (unclassified)"
    return "native build or validation failure (details withheld)"


def summarize_rustfmt_locations(text: str) -> str:
    """Return only bounded Rust source basenames and line numbers, never paths or diff text."""
    normalized = ANSI_RE.sub("", text)
    locations = list(dict.fromkeys(
        f"{match.group('filename')}:{match.group('line')}"
        for match in RUSTFMT_DIFF_RE.finditer(normalized)
    ))[:20]
    if not locations:
        return "Rustfmt check failed; no safe source locations were emitted."
    return "Rustfmt mismatch locations (source omitted): " + ", ".join(locations)


def summarize_rustfmt_files(paths: Iterable[Path]) -> str:
    texts: list[str] = []
    for path in paths:
        try:
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return summarize_rustfmt_locations("\n".join(texts))


def summarize_files(paths: Iterable[Path]) -> str:
    texts: list[str] = []
    for path in paths:
        try:
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    if not texts:
        return "native build failure (diagnostic log unavailable)"
    return summarize_text("\n".join(texts))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", action="append", type=Path, default=[])
    parser.add_argument("--rustfmt-log", action="append", type=Path, default=[])
    args = parser.parse_args()
    if not args.log and not args.rustfmt_log:
        parser.error("provide --log and/or --rustfmt-log")
    if args.log:
        print(summarize_files(args.log))
    if args.rustfmt_log:
        print(summarize_rustfmt_files(args.rustfmt_log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
