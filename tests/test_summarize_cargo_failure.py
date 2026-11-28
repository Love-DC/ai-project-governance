import tempfile
import unittest
from pathlib import Path

from scripts.summarize_cargo_failure import (
    summarize_files,
    summarize_rustfmt_locations,
    summarize_text,
)


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

    def test_classifies_thread_safety_trait_without_returning_identifier(self):
        summary = summarize_text(
            "error[E0277]: the trait bound PrivateKernelType: Send is not satisfied"
        )
        self.assertIn("thread-safety bound", summary)
        self.assertNotIn("PrivateKernelType", summary)
        self.assertNotIn("Send", summary)

    def test_classifies_gdextension_binding_trait_without_returning_identifier(self):
        summary = summarize_text(
            "error[E0277]: the trait bound InternalGodotValue: GodotConvert is not satisfied"
        )
        self.assertIn("GDExtension binding/conversion bound", summary)
        self.assertNotIn("InternalGodotValue", summary)
        self.assertNotIn("GodotConvert", summary)

    def test_unknown_trait_family_falls_back_to_generic_category(self):
        summary = summarize_text(
            "error[E0277]: the trait bound InternalThing: UnlistedTrait is not satisfied"
        )
        self.assertIn("type/trait mismatch", summary)
        self.assertNotIn("UnlistedTrait", summary)


    def test_rustfmt_locations_expose_only_basename_and_line_number(self):
        private_log = (
            r"Diff in C:\agent\_work\private\source\native\src\tests.rs:42:" + "\n"
            "  |\n"
            "42 | fn private_internal_symbol() {\n"
            "   |    ^^^^^^^^^^^^^^^^^^^^^^^"
        )
        summary = summarize_rustfmt_locations(private_log)
        self.assertEqual(
            summary,
            "Rustfmt mismatch locations (source omitted): tests.rs:42",
        )
        self.assertNotIn("C:", summary)
        self.assertNotIn("private", summary)
        self.assertNotIn("private_internal_symbol", summary)

    def test_rustfmt_locations_are_bounded_and_deduplicated(self):
        private_log = "\n".join(
            f"Diff in /runner/source/native/src/file{index}.rs:{index}:"
            for index in range(30)
        )
        summary = summarize_rustfmt_locations(private_log)
        self.assertEqual(summary.count(".rs:"), 20)
        self.assertNotIn("/runner/", summary)
        self.assertNotIn("file20.rs", summary)

    def test_rustfmt_unknown_log_does_not_echo_private_content(self):
        summary = summarize_rustfmt_locations(
            "private source contents and no recognized Diff header"
        )
        self.assertEqual(
            summary,
            "Rustfmt check failed; no safe source locations were emitted.",
        )
        self.assertNotIn("private source", summary)


if __name__ == "__main__":
    unittest.main()
