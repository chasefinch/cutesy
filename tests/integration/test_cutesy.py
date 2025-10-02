"""Test against spec files."""

from pathlib import Path
from types import MappingProxyType

import pytest

from cutesy import HTMLLinter
from cutesy.attribute_processors import reindent, whitespace
from cutesy.attribute_processors.class_ordering import tailwind
from cutesy.preprocessors import django


class TestSpec:
    """Test the linter against the spec files."""

    tests = MappingProxyType(
        {
            "0000_blank": ([], []),
            "0001_basic": ([], []),
            "0002_indentation": (["F3", "F3", "F3", "F2", "F3"], []),
            "0003_whitespace": (["F13", "F5", "F4", "D9"], []),
            "0004_dynamic": (
                ["F4", "F3", "F3", "F3", "F3", "F3", "F3", "F3", "F14", "F3", "F3"],
                [],
            ),
            "0005_attributes": (["F6", "F14", "F15", "F17", "F17", "F17", "F13"], []),
        },
    )

    @pytest.mark.parametrize("spec", tests)
    def test_files(self, spec: str) -> None:
        """Run the test for all spec files."""
        self._run_test(spec)

    def _run_test(self, spec: str) -> None:
        current_file_path = Path(__file__)
        local_path = current_file_path.parent
        input_path_string = f"{local_path}/spec/cutesy/{spec}/input.html"
        output_path_string = f"{local_path}/spec/cutesy/{spec}/expected_output.html"

        input_path = Path(input_path_string)
        with input_path.open() as html_file:
            html = html_file.read()

        output_path = Path(output_path_string)
        with output_path.open() as html_file:
            expected = html_file.read()

        preprocessor = django.Preprocessor()
        attribute_processors = [
            whitespace.AttributeProcessor(),
            reindent.AttributeProcessor(),
            tailwind.AttributeProcessor(),
        ]

        checking_linter = HTMLLinter(
            check_doctype=True,
            preprocessor=preprocessor,
            attribute_processors=attribute_processors,
        )
        result, errors = checking_linter.lint(html)

        assert result == html
        assert self.tests[spec][0] == [error.rule.code for error in errors]

        fixing_linter = HTMLLinter(
            check_doctype=True,
            fix=True,
            preprocessor=preprocessor,
            attribute_processors=attribute_processors,
        )
        result, errors = fixing_linter.lint(html)

        assert result == expected
        assert self.tests[spec][1] == [error.rule.code for error in errors]
