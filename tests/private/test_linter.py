"""Tests for HTMLLinter functionality."""

from typing import ClassVar

from cutesy.linter import HTMLLinter
from cutesy.preprocessors.types import BasePreprocessor
from cutesy.rules import Rule
from cutesy.types import Error, InstructionType, Mode


class MockPreprocessor(BasePreprocessor):
    """Mock preprocessor class for testing."""

    braces: ClassVar[set[tuple[str, str]]] = {("{%", "%}"), ("{{", "}}")}
    closing_tag_string_map: ClassVar[dict[str, str]] = {}
    expected_closing_instructions: ClassVar[dict[str, str]] = {}

    def parse_instruction_tag(
        self,
        braces: tuple[str, str],
        html: str,
        cursor: int,
        cursor2: int,
    ) -> tuple[str, InstructionType]:
        """Parse instruction tag - mock implementation."""
        return "", InstructionType.VALUE

    def process(self) -> str:
        """Mock process by replacing 'TEMPLATE' with 'div'."""
        # First call the parent process to set up the internal state
        result = super().process()
        # Then apply our simple transformation
        return result.replace("TEMPLATE", "div")


class TestHTMLLinter:
    """Test HTMLLinter class."""

    def test_linter_reset_state(self) -> None:
        """Test linter reset clears internal state."""
        linter = HTMLLinter()

        # Simulate some state
        linter._mode = Mode.DOCUMENT
        linter._errors = [Error(line=1, column=0, rule=Rule.get("D1"))]
        linter._result = ["result"]

        linter.reset()

        assert linter._mode is None
        assert linter._errors == []  # noqa: WPS520 (supposed to be OK for asserts)
        assert linter._result == []  # noqa: WPS520 (supposed to be OK for asserts)

    def test_handle_decl_with_mode_already_set_document(self) -> None:
        """Test handle_decl when mode is already DOCUMENT."""
        linter = HTMLLinter(fix=False)
        linter._mode = Mode.DOCUMENT

        # Should generate D2 error when trying to add another doctype in document mode
        linter.handle_decl("doctype html")

        d2_errors = [error for error in linter._errors if error.rule.code == "D2"]
        assert len(d2_errors) > 0

    def test_handle_decl_with_mode_already_set_unstructured(self) -> None:
        """Test handle_decl when mode is already UNSTRUCTURED."""
        linter = HTMLLinter(fix=False)
        linter._mode = Mode.UNSTRUCTURED

        # Should generate D1 error when trying to add doctype in unstructured mode
        linter.handle_decl("doctype html")

        d1_errors = [error for error in linter._errors if error.rule.code == "D1"]
        assert len(d1_errors) > 0
