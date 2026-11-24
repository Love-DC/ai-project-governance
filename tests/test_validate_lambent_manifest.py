import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_lambent_manifest import ManifestError, validate_manifest

SHA = "a" * 40


class LambentManifestTests(unittest.TestCase):
    def roots(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        source = base / "source"
        runner = base / "runner"
        source.mkdir(parents=True, exist_ok=True)
        for path in ("AGENTS.md", "README.md"):
            (source / path).write_text("governance", encoding="utf-8")
        workflow = runner / ".github/workflows/validate-private-lambent.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: validator", encoding="utf-8")
        manifest = {
            "protocol": "rae.repository-governance",
            "protocol_version": "1.0.0",
            "project": "lambent",
            "governance": {
                "agent_instructions": "AGENTS.md",
                "entrypoints": ["README.md"],
                "required": ["AGENTS.md", "README.md"],
                "rule_sets": [
                    {"id": "owner", "path": "AGENTS.md", "priority": 100},
                    {"id": "entry", "path": "README.md", "priority": 90},
                ],
            },
            "validation": {
                "provider": "github-actions",
                "mode": "external-private-source-runner",
                "repository": "Love-DC/ai-project-governance",
                "workflow": ".github/workflows/validate-private-lambent.yml",
                "trigger": {
                    "type": "issue_comment",
                    "control_issue": 9,
                    "pull_request_command": "/validate-lambent-pr",
                    "post_merge_command": "/validate-lambent-merge",
                    "exact_head_sha_required": True,
                },
                "status_contexts": ["external-ci/lambent-governance"],
            },
            "conflicts": [],
        }
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        return source, runner, manifest

    def test_accepts_valid_exact_sha_manifest(self):
        source, runner, _ = self.roots()
        result = validate_manifest(source, runner, SHA, SHA)
        self.assertEqual(result["project"], "lambent")

    def test_rejects_sha_drift(self):
        source, runner, _ = self.roots()
        with self.assertRaisesRegex(ManifestError, "does not match"):
            validate_manifest(source, runner, SHA, "b" * 40)

    def test_rejects_missing_required_file(self):
        source, runner, _ = self.roots()
        (source / "README.md").unlink()
        with self.assertRaisesRegex(ManifestError, "Missing governance"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_path_traversal(self):
        source, runner, manifest = self.roots()
        manifest["governance"]["required"] = ["../outside.md"]
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "Unsafe"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_wrong_project_key(self):
        source, runner, manifest = self.roots()
        manifest["project"] = "colony-sim"
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "project key"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_unresolved_conflicts(self):
        source, runner, manifest = self.roots()
        manifest["conflicts"] = [{"rule": "owner"}]
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "unresolved"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_wrong_control_issue(self):
        source, runner, manifest = self.roots()
        manifest["validation"]["trigger"]["control_issue"] = 3
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "control issue"):
            validate_manifest(source, runner, SHA, SHA)

    def test_rejects_missing_public_workflow(self):
        source, runner, manifest = self.roots()
        manifest["validation"]["workflow"] = ".github/workflows/missing.yml"
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "Missing external CI workflow"):
            validate_manifest(source, runner, SHA, SHA)


if __name__ == "__main__":
    unittest.main()
