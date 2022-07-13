"""Test against spec files."""

# Standard Library
import os

# Third Party
import pytest

# Cutesy
from cutesy import HTMLLinter
from cutesy.preprocessors import django


class TestSpec:
    """Test the linter against the spec files."""

    tests = {
        "0000_blank": ([], []),
        "0001_basic": ([], []),
        "0002_indentation": (["F3", "F2", "F3", "F3", "F3"], []),
        "0003_whitespace": (["F13", "F5", "F4"], []),
        "0004_dynamic": (["F3", "F3", "F3", "F3", "F3", "F3", "F3", "F14", "F3", "F3"], []),
        "0005_attributes": (["F6", "F14", "F15", "F13"], []),
    }

    @pytest.mark.parametrize("spec", tests)
    def test_files(self, spec):
        """Run the test for all spec files."""
        self._run_test(spec)

    def _run_test(self, spec):
        local_path = os.path.dirname(__file__)
        input_path = "{}/spec/{}/input.html".format(local_path, spec)
        output_path = "{}/spec/{}/expected_output.html".format(local_path, spec)

        with open(input_path, mode="r") as html_file:
            html = html_file.read()

        with open(output_path, mode="r") as html_file:
            expected = html_file.read()

        preprocessor = django.Preprocessor()

        checking_linter = HTMLLinter(check_doctype=True, preprocessor=preprocessor)
        result, errors = checking_linter.lint(html)

        assert result == html
        assert self.tests[spec][0] == [error.rule.code for error in errors]

        fixing_linter = HTMLLinter(check_doctype=True, fix=True, preprocessor=preprocessor)
        result, errors = fixing_linter.lint(html)

        assert result == expected
        assert self.tests[spec][1] == [error.rule.code for error in errors]
