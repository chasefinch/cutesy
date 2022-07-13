"""Test each rule."""

# Cutesy
from cutesy import HTMLLinter, Rule
from cutesy.preprocessors import django


class TestRules:
    """Test that each rule is triggerable."""

    def setup_method(self, test_method):
        """Set up the systems under test."""
        self.preprocessor = django.Preprocessor()
        self.checking_linter = HTMLLinter(check_doctype=True, preprocessor=self.preprocessor)
        self.fixing_linter = HTMLLinter(
            check_doctype=True,
            fix=True,
            preprocessor=self.preprocessor,
        )

    def run_test(self, html, rule_code, is_fixable=True):
        """Run a test which attempts to produce an error once."""
        result, errors = self.checking_linter.lint(html)

        assert result == html
        assert len(errors) == 1
        assert errors[0].rule == Rule.get(rule_code)

        result, errors = self.fixing_linter.lint(html)

        assert result != html
        assert not errors

    def test_f1(self):
        """Test rule F1."""
        self.run_test("<!DOCTYPE HTML>", "F1")
