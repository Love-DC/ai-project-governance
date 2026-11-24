#!/usr/bin/env python3
"""Fail-closed exact-SHA validation for the private Lambent RAE onboarding manifest."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROTOCOL = "rae.repository-governance"
PROJECT = "lambent"
RUNNER_REPOSITORY = "Love-DC/colony-sim-ci"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ManifestError(ValueError):
    """The source manifest or required governance files are invalid."""


def required_file(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ManifestError(f"{label} must be a non-empty relative path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ManifestError(f"Unsafe {label} path")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ManifestError(f"{label} path escapes repository root") from exc
    if not resolved.is_file():
        raise ManifestError(f"Missing {label} file")
    return resolved


def validate_manifest(
    source_root: str | Path,
    runner_root: str | Path,
    expected_sha: str,
    actual_sha: str,
) -> dict[str, Any]:
    source = Path(source_root).resolve()
    runner = Path(runner_root).resolve()
    expected = (expected_sha or "").lower()
    actual = (actual_sha or "").lower()
    if not SHA_RE.fullmatch(expected) or not SHA_RE.fullmatch(actual):
        raise ManifestError("Expected and actual revisions must be full 40-character SHAs")
    if expected != actual:
        raise ManifestError("Private checkout SHA does not match the requested exact SHA")

    manifest_path = required_file(source, "rae-governance.json", "manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Cannot parse RAE governance manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("protocol") != PROTOCOL:
        raise ManifestError("Unsupported RAE governance protocol")
    version = manifest.get("protocol_version")
    if not isinstance(version, str) or not re.fullmatch(r"1\.\d+\.\d+", version):
        raise ManifestError("Unsupported RAE governance protocol version")
    if manifest.get("project") != PROJECT:
        raise ManifestError("RAE manifest project key does not match Lambent")
    if manifest.get("conflicts") != []:
        raise ManifestError("RAE manifest has unresolved or missing conflicts declaration")

    governance = manifest.get("governance")
    if not isinstance(governance, dict):
        raise ManifestError("Missing governance declaration")
    paths: list[Any] = [governance.get("agent_instructions")]
    for field in ("entrypoints", "required"):
        value = governance.get(field)
        if not isinstance(value, list):
            raise ManifestError(f"governance.{field} must be an array")
        paths.extend(value)

    rule_sets = governance.get("rule_sets")
    if not isinstance(rule_sets, list) or not rule_sets:
        raise ManifestError("At least one governance rule set is required")
    seen: dict[str, tuple[str, int]] = {}
    for rule in rule_sets:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or not rule["id"]:
            raise ManifestError("Invalid governance rule declaration")
        relative = rule.get("path")
        priority = rule.get("priority")
        if not isinstance(priority, int):
            raise ManifestError("Governance rule priority must be an integer")
        signature = (relative, priority)
        previous = seen.get(rule["id"])
        if previous is not None and previous != signature:
            raise ManifestError("Conflicting governance rule ID")
        seen[rule["id"]] = signature
        paths.append(relative)

    for relative in paths:
        required_file(source, relative, "governance")

    validation = manifest.get("validation")
    if not isinstance(validation, dict):
        raise ManifestError("Missing validation declaration")
    if validation.get("provider") != "github-actions":
        raise ManifestError("Unsupported validation provider")
    if validation.get("mode") != "external-private-source-runner":
        raise ManifestError("Lambent validation must use the external private-source runner")
    if validation.get("repository") != RUNNER_REPOSITORY:
        raise ManifestError("Wrong public validation repository")
    workflow = validation.get("workflow")
    required_file(runner, workflow, "external CI workflow")

    trigger = validation.get("trigger")
    if not isinstance(trigger, dict) or trigger.get("type") != "issue_comment":
        raise ManifestError("Missing public CI control-issue trigger")
    if trigger.get("control_issue") != 9:
        raise ManifestError("Wrong public CI control issue")
    if trigger.get("pull_request_command") != "/validate-lambent-pr":
        raise ManifestError("Wrong pull-request validation command")
    if trigger.get("post_merge_command") != "/validate-lambent-merge":
        raise ManifestError("Wrong post-merge validation command")
    if trigger.get("exact_head_sha_required") is not True:
        raise ManifestError("Exact-head SHA validation must be required")
    contexts = validation.get("status_contexts")
    if not isinstance(contexts, list) or "external-ci/lambent-governance" not in contexts:
        raise ManifestError("Missing Lambent external CI status context")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runner-root", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--actual-sha", required=True)
    args = parser.parse_args()
    try:
        manifest = validate_manifest(
            args.source_root, args.runner_root, args.expected_sha, args.actual_sha
        )
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Validated {manifest['project']} manifest and required files at the exact source SHA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
