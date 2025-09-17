"""Test against Cutesy Tailwind spec files."""

# Standard Library
from pathlib import Path

# Third Party
from types import MappingProxyType

import pytest

# Cutesy
from cutesy import HTMLLinter
from cutesy.attribute_processors import reindent, whitespace
from cutesy.attribute_processors.class_ordering import tailwind
from cutesy.preprocessors import django


class TestCutesySpec:
    """Test the linter against the Cutesy Tailwind spec files."""

    tests = MappingProxyType(
        {
            "0001_basic_tailwind": (
                ["F1", "F3", "F3", "F3", "F3", "F14", "F3", "F3", "F3", "F3", "F14", "F3", "D9"],
                [],
            ),
            "0002_responsive_and_states": (
                [
                    "F1",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "D9",
                ],
                [],
            ),
            "0003_arbitrary_values_and_variants": (
                [
                    "F1",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "D9",
                ],
                [],
            ),
            "0004_complex_modifiers_and_custom": (
                [
                    "F1",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "D9",
                ],
                [],
            ),
            "0005_negative_values_and_edge_cases": (
                [
                    "F1",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F14",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "F3",
                    "D9",
                ],
                [],
            ),
        },
    )

    @pytest.mark.parametrize("spec", tests)
    def test_cutesy_files(self, spec: str) -> None:
        """Run the test for all Cutesy Tailwind spec files."""
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

        # Should not modify on check
        assert result == html
        assert self.tests[spec][0] == [error.rule.code for error in errors]

        fixing_linter = HTMLLinter(
            check_doctype=True,
            fix=True,
            preprocessor=preprocessor,
            attribute_processors=attribute_processors,
        )
        result, errors = fixing_linter.lint(html)

        # Should format classes correctly
        assert result == expected
        assert self.tests[spec][1] == [error.rule.code for error in errors]
