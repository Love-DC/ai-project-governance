#!/usr/bin/env python3
"""Fail closed unless a commit is an ancestor of the private source main branch."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ValidationError(ValueError):
    """The supplied commit cannot be proven to be reachable from main."""


def validate_main_ancestor(compare: dict[str, Any], expected_sha: str) -> None:
    expected = (expected_sha or "").lower()
    if not SHA_RE.fullmatch(expected):
        raise ValidationError("Expected a full 40-character commit SHA")

    base_sha = str(compare.get("base_commit", {}).get("sha", "")).lower()
    merge_base_sha = str(compare.get("merge_base_commit", {}).get("sha", "")).lower()
    status = compare.get("status")

    if base_sha != expected:
        raise ValidationError("GitHub compare response base does not match requested SHA")
    if status not in {"ahead", "identical"}:
        raise ValidationError("Requested commit is not an ancestor of the current main branch")
    if merge_base_sha != expected:
        raise ValidationError("Requested commit is not the merge base with current main")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare-response", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.compare_response.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValidationError("GitHub compare response must be a JSON object")
        validate_main_ancestor(payload, args.expected_sha)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Verified {args.expected_sha.lower()} is reachable from colony-sim main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
