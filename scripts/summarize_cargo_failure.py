#!/usr/bin/env python3
"""Emit a deliberately redacted, allow-listed summary of private Cargo failures."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ERROR_CODE_RE = re.compile(r"\berror\[(E\d{4})\]\s*:", re.IGNORECASE)

CODE_GROUPS = {
    "import/module resolution": {"E0432", "E0433"},
    "name/type resolution": {"E0412", "E0425", "E0463"},
    "type/trait mismatch": {"E0277", "E0308"},
    "missing member": {"E0599", "E0609"},
    "ownership/borrow": {"E0382", "E0499", "E0502", "E0507"},
    "call/field shape": {"E0061", "E0063"},
    "unstable feature": {"E0554", "E0658"},
}


def summarize_text(text: str) -> str:
    """Return only compiler codes and broad categories, never source text."""
    normalized = ANSI_RE.sub("", text)
    codes = sorted({code.upper() for code in ERROR_CODE_RE.findall(normalized)})
    categories: set[str] = set()

    for label, members in CODE_GROUPS.items():
        if set(codes) & members:
            categories.add(label)

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
    parser.add_argument("--log", action="append", type=Path, required=True)
    args = parser.parse_args()
    print(summarize_files(args.log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
