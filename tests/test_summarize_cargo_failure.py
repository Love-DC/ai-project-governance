import tempfile
import unittest
from pathlib import Path

from scripts.summarize_cargo_failure import summarize_files, summarize_text


class CargoFailureSummaryTests(unittest.TestCase):
    def test_reports_allowlisted_error_code_without_private_source_details(self):
        source = (
            "error[E0432]: unresolved import private_internal_module\n"
            " --> C:\\agent\\_work\\source\\native\\secret.rs:14:5\n"
            "  |\n"
            "14 | use private_internal_module::secret_symbol;\n"
            "   |     private_internal_module"
        )
        summary = summarize_text(source)
        self.assertIn("E0432", summary)
        self.assertIn("import/module resolution", summary)
        self.assertNotIn("private_internal_module", summary)
        self.assertNotIn("secret_symbol", summary)
        self.assertNotIn("C:\\agent", summary)

    def test_classifies_linker_without_symbol_or_command(self):
        summary = summarize_text(
            "error: linking with cc failed: undefined symbol _private_secret_symbol"
        )
        self.assertIn("linker", summary)
        self.assertNotIn("_private_secret_symbol", summary)

    def test_classifies_format_failure(self):
        summary = summarize_text("Diff in C:\\runner\\source\\native\\lib.rs:10")
        self.assertIn("format check", summary)

    def test_classifies_test_failure(self):
        summary = summarize_text("test result: FAILED. 2 passed; 1 failed")
        self.assertIn("test", summary)

    def test_unknown_failure_stays_generic(self):
        summary = summarize_text("error: opaque private diagnostic text")
        self.assertEqual(summary, "Cargo/native build failure (unclassified)")
        self.assertNotIn("opaque private diagnostic text", summary)

    def test_missing_logs_are_reported_without_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            summary = summarize_files([Path(directory) / "missing-private.log"])
        self.assertEqual(summary, "native build failure (diagnostic log unavailable)")


if __name__ == "__main__":
    unittest.main()
