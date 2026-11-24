import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_source_manifest import ManifestError, validate_manifest

SHA = "a" * 40


class SourceManifestTests(unittest.TestCase):
    def make_roots(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        source = base / "source"
        runner = base / "runner"
        for name in ("AGENTS.md", "docs/START.md", "docs/WORKFLOW.md"):
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("rule", encoding="utf-8")
        workflow = runner / ".github/workflows/validate-private-pr.yml"
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text("name: runner", encoding="utf-8")
        manifest = {
            "protocol": "rae.repository-governance",
            "protocol_version": "1.0.0",
            "project": "colony-sim",
            "governance": {
                "agent_instructions": "AGENTS.md",
                "entrypoints": ["docs/START.md"],
                "required": ["docs/WORKFLOW.md"],
                "rule_sets": [{"id": "owner", "path": "AGENTS.md", "priority": 100}],
            },
            "validation": {
                "repository": "Love-DC/ai-project-governance",
                "workflow": ".github/workflows/validate-private-pr.yml",
                "trigger": {"exact_head_sha_required": True},
            },
            "conflicts": [],
        }
        (source / "rae-governance.json").write_text(json.dumps(manifest), encoding="utf-8")
        return source, runner, manifest

    def test_validates_manifest_and_external_workflow(self):
        source, runner, manifest = self.make_roots()
        self.assertEqual(validate_manifest(source, runner, SHA)["project"], "colony-sim")

    def test_rejects_stale_or_short_sha(self):
        source, runner, _ = self.make_roots()
        with self.assertRaisesRegex(ManifestError, "40-character SHA"):
            validate_manifest(source, runner, "abc")

    def test_rejects_missing_governance_file(self):
        source, runner, _ = self.make_roots()
        (source / "docs/WORKFLOW.md").unlink()
        with self.assertRaisesRegex(ManifestError, "Missing governance"):
            validate_manifest(source, runner, SHA)

    def test_rejects_unsafe_path(self):
        source, runner, manifest = self.make_roots()
        manifest["governance"]["required"] = ["../outside.md"]
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "Unsafe governance"):
            validate_manifest(source, runner, SHA)

    def test_rejects_unresolved_conflicts(self):
        source, runner, manifest = self.make_roots()
        manifest["conflicts"] = [{"rule": "owner"}]
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "unresolved"):
            validate_manifest(source, runner, SHA)

    def test_rejects_wrong_ci_repository(self):
        source, runner, manifest = self.make_roots()
        manifest["validation"]["repository"] = "other/ci"
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "Expected validation repository"):
            validate_manifest(source, runner, SHA)

    def test_rejects_missing_external_workflow(self):
        source, runner, manifest = self.make_roots()
        manifest["validation"]["workflow"] = ".github/workflows/missing.yml"
        (source / "rae-governance.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ManifestError, "Missing external CI workflow"):
            validate_manifest(source, runner, SHA)


if __name__ == "__main__":
    unittest.main()
