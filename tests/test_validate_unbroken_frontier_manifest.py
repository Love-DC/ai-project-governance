import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_unbroken_frontier_manifest import ManifestError, validate_manifest

SHA = "a" * 40
OTHER_SHA = "b" * 40


class UnbrokenFrontierManifestTests(unittest.TestCase):
    def make_roots(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        source = base / "source"
        runner = base / "runner"
        for name in (
            "AGENTS.md",
            "README.md",
            "docs/GAME_DESIGN.md",
            "native/Cargo.toml",
            "godot/project.godot",
            "godot/scenes/bridge_check.tscn",
            "godot/scripts/bridge_check.gd",
            "android-plugin/plugin/build.gradle.kts",
        ):
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture", encoding="utf-8")
        workflow = runner / ".github/workflows/validate-private-unbroken-frontier.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text("name: runner", encoding="utf-8")
        manifest = {
            "protocol": "rae.repository-governance",
            "protocol_version": "1.0.0",
            "project": "unbroken-frontier",
            "governance": {
                "agent_instructions": "AGENTS.md",
                "entrypoints": ["README.md", "docs/GAME_DESIGN.md"],
                "required": [
                    "native/Cargo.toml",
                    "godot/project.godot",
                    "godot/scenes/bridge_check.tscn",
                    "godot/scripts/bridge_check.gd",
                    "android-plugin/plugin/build.gradle.kts",
                ],
                "rule_sets": [
                    {"id": "gameplay", "path": "docs/GAME_DESIGN.md", "priority": 100},
                    {"id": "agent", "path": "AGENTS.md", "priority": 100},
                ],
            },
            "validation": {
                "provider": "github-actions",
                "mode": "external-private-source-runner",
                "repository": "Love-DC/ai-project-governance",
                "source_repository": "Love-DC/Unbroken-Frontier",
                "workflow": ".github/workflows/validate-private-unbroken-frontier.yml",
                "trigger": {
                    "type": "issue_comment",
                    "control_issue": 15,
                    "pull_request_command": "/validate-unbroken-frontier-pr",
                    "post_merge_command": "/validate-unbroken-frontier-merge",
                    "exact_head_sha_required": True,
                },
                "status_contexts": [
                    "external-ci/unbroken-frontier-windows",
                    "external-ci/unbroken-frontier-android",
                    "external-ci/unbroken-frontier-ios",
                ],
            },
            "conflicts": [],
        }
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        return source, runner, manifest

    def test_validates_exact_sha_and_manifest(self):
        source, runner, _ = self.make_roots()
        self.assertEqual(
            validate_manifest(source, runner, SHA, SHA)["project"],
            "unbroken-frontier",
        )

    def test_rejects_stale_checkout_sha(self):
        source, runner, _ = self.make_roots()
        with self.assertRaisesRegex(ManifestError, "does not match"):
            validate_manifest(source, runner, SHA, OTHER_SHA)

    def test_rejects_short_sha(self):
        source, runner, _ = self.make_roots()
        with self.assertRaisesRegex(ManifestError, "40-character"):
            validate_manifest(source, runner, "abc", "abc")

    def test_rejects_wrong_source_repository(self):
        source, runner, manifest = self.make_roots()
        manifest["validation"]["source_repository"] = "Love-DC/colony-sim"
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "Wrong private source"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_wrong_control_issue(self):
        source, runner, manifest = self.make_roots()
        manifest["validation"]["trigger"]["control_issue"] = 9
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "Wrong public CI control issue"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_missing_platform_status(self):
        source, runner, manifest = self.make_roots()
        manifest["validation"]["status_contexts"].pop()
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "status contexts"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_unsafe_paths(self):
        source, runner, manifest = self.make_roots()
        manifest["governance"]["required"] = ["../outside"]
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "Unsafe governance"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_missing_workflow_file(self):
        source, runner, manifest = self.make_roots()
        manifest["validation"]["workflow"] = ".github/workflows/missing.yml"
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "Wrong external validation workflow"):
            validate_manifest(source, runner, SHA, SHA)


if __name__ == "__main__":
    unittest.main()
