import unittest

from scripts.validate_main_ancestor import ValidationError, validate_main_ancestor

SHA = "a" * 40
OTHER = "b" * 40


class MainAncestorValidationTests(unittest.TestCase):
    def response(self, status="ahead", base=SHA, merge_base=SHA):
        return {
            "status": status,
            "base_commit": {"sha": base},
            "merge_base_commit": {"sha": merge_base},
        }

    def test_accepts_commit_ancestor_of_main(self):
        validate_main_ancestor(self.response(status="ahead"), SHA)

    def test_accepts_current_main_commit(self):
        validate_main_ancestor(self.response(status="identical"), SHA)

    def test_rejects_commit_ahead_of_or_diverged_from_main(self):
        for status in ("behind", "diverged", "unknown"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValidationError, "not an ancestor"):
                    validate_main_ancestor(self.response(status=status), SHA)

    def test_rejects_compare_response_for_different_base(self):
        with self.assertRaisesRegex(ValidationError, "base does not match"):
            validate_main_ancestor(self.response(base=OTHER), SHA)

    def test_rejects_non_matching_merge_base(self):
        with self.assertRaisesRegex(ValidationError, "not the merge base"):
            validate_main_ancestor(self.response(merge_base=OTHER), SHA)

    def test_rejects_short_or_malformed_sha(self):
        with self.assertRaisesRegex(ValidationError, "40-character"):
            validate_main_ancestor(self.response(), "abc")


if __name__ == "__main__":
    unittest.main()
