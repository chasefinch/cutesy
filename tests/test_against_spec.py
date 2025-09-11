"""Test against spec files."""

# Standard Library
from pathlib import Path

# Third Party
from types import MappingProxyType

import pytest

# Cutesy
from cutesy import HTMLLinter
from cutesy.preprocessors import django


class TestSpec:
    """Test the linter against the spec files."""

    tests = MappingProxyType(
        {
            "0000_blank": ([], []),
            "0001_basic": ([], []),
            "0002_indentation": (["F3", "F2", "F3", "F3", "F3"], []),
            "0003_whitespace": (["F13", "F5", "F4"], []),
            "0004_dynamic": (["F3", "F3", "F3", "F3", "F3", "F3", "F3", "F14", "F3", "F3"], []),
            "0005_attributes": (["F6", "F14", "F15", "F13"], []),
        },
    )

    @pytest.mark.parametrize("spec", tests)
    def test_files(self, spec: str) -> None:
        """Run the test for all spec files."""
        self._run_test(spec)

    def _run_test(self, spec: str) -> None:
        current_file_path = Path(__file__)
        local_path = current_file_path.parent
        input_path_string = f"{local_path}/spec/{spec}/input.html"
        output_path_string = f"{local_path}/spec/{spec}/expected_output.html"

        input_path = Path(input_path_string)
        with input_path.open() as html_file:
            html = html_file.read()

        output_path = Path(output_path_string)
        with output_path.open() as html_file:
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
