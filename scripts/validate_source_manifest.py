#!/usr/bin/env python3
"""Validate Colony Sim's repository-local governance contract in the public CI runner."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROTOCOL = "rae.repository-governance"
EXPECTED_PROJECT = "colony-sim"
EXPECTED_CI_REPOSITORY = "Love-DC/ai-project-governance"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ManifestError(ValueError):
    pass


def _file(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ManifestError(f"{label} must be a non-empty relative path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ManifestError(f"Unsafe {label} path: {relative}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ManifestError(f"{label} escapes repository root: {relative}") from exc
    if not resolved.is_file():
        raise ManifestError(f"Missing {label} file: {relative}")
    return resolved


def validate_manifest(source_root: str | Path, runner_root: str | Path, expected_sha: str) -> dict[str, Any]:
    source = Path(source_root).resolve()
    runner = Path(runner_root).resolve()
    if not SHA_RE.fullmatch(expected_sha or ""):
        raise ManifestError("Expected source revision must be a full lowercase 40-character SHA")
    path = source / "rae-governance.json"
    if not path.is_file():
        raise ManifestError("Missing source rae-governance.json")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Cannot parse source governance manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("protocol") != PROTOCOL:
        raise ManifestError(f"Expected protocol {PROTOCOL}")
    version = manifest.get("protocol_version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version) or version.split(".")[0] != "1":
        raise ManifestError("Unsupported governance protocol version")
    if manifest.get("project") != EXPECTED_PROJECT:
        raise ManifestError(f"Expected project {EXPECTED_PROJECT}")
    if manifest.get("conflicts"):
        raise ManifestError("Source manifest declares unresolved governance conflicts")

    governance = manifest.get("governance")
    if not isinstance(governance, dict):
        raise ManifestError("Missing governance object")
    paths = [governance.get("agent_instructions")]
    for key in ("entrypoints", "required"):
        values = governance.get(key, [])
        if not isinstance(values, list):
            raise ManifestError(f"governance.{key} must be an array")
        paths.extend(values)
    rules = governance.get("rule_sets", [])
    if not isinstance(rules, list):
        raise ManifestError("governance.rule_sets must be an array")
    seen: dict[str, tuple[str, int]] = {}
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str):
            raise ManifestError("Invalid governance rule declaration")
        signature = (rule.get("path"), rule.get("priority", 0))
        if not isinstance(signature[1], int):
            raise ManifestError("Governance rule priority must be an integer")
        if rule["id"] in seen and seen[rule["id"]] != signature:
            raise ManifestError(f"Conflicting governance rule ID: {rule['id']}")
        seen[rule["id"]] = signature
        paths.append(rule["path"])
    for relative in paths:
        _file(source, relative, "governance")

    validation = manifest.get("validation")
    if not isinstance(validation, dict):
        raise ManifestError("Missing validation object")
    if validation.get("repository") != EXPECTED_CI_REPOSITORY:
        raise ManifestError(f"Expected validation repository {EXPECTED_CI_REPOSITORY}")
    trigger = validation.get("trigger")
    if not isinstance(trigger, dict) or trigger.get("exact_head_sha_required") is not True:
        raise ManifestError("Exact PR HEAD SHA validation is required")
    workflow = validation.get("workflow")
    _file(runner, workflow, "external CI workflow")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runner-root", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    try:
        manifest = validate_manifest(args.source_root, args.runner_root, args.expected_sha)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Validated {manifest['project']} governance manifest at {args.expected_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
