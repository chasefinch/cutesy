"""Test each rule."""

# Cutesy
from cutesy import HTMLLinter
from cutesy.attribute_processors import reindent, tailwind, whitespace
from cutesy.preprocessors import django
from cutesy.types import Rule


class TestRules:
    """Test that each rule is triggerable."""

    def setup_method(self, test_method: str) -> None:
        """Set up the systems under test."""
        self.preprocessor = django.Preprocessor()
        attribute_processors = [
            whitespace.AttributeProcessor(),
            reindent.AttributeProcessor(),
            tailwind.AttributeProcessor(),
        ]

        self.checking_linter = HTMLLinter(
            check_doctype=True,
            preprocessor=self.preprocessor,
            attribute_processors=attribute_processors,
        )
        self.fixing_linter = HTMLLinter(
            check_doctype=True,
            fix=True,
            preprocessor=self.preprocessor,
            attribute_processors=attribute_processors,
        )

    def run_test(self, html: str, rule_code: str, *, is_fixable: bool = True) -> None:
        """Run a test which attempts to produce an error once."""
        result, errors = self.checking_linter.lint(html)

        assert result == html
        assert len(errors) == 1
        assert errors[0].rule == Rule.get(rule_code)

        result, errors = self.fixing_linter.lint(html)

        assert result != html
        assert not errors

    def test_f1(self) -> None:
        """Test rule F1."""
        self.run_test("<!DOCTYPE HTML>\n", "F1")
