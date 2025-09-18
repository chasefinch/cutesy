"""Tests for HTMLLinter functionality."""

from typing import ClassVar

import pytest

from cutesy.attribute_processors import whitespace
from cutesy.linter import HTMLLinter, attr_sort, is_whitespace
from cutesy.preprocessors.types import BasePreprocessor
from cutesy.types import DoctypeError, InstructionType, Mode


class MockPreprocessor(BasePreprocessor):
    """Mock preprocessor class for testing."""

    braces: ClassVar[set[tuple[str, str]]] = {("{%", "%}"), ("{{", "}}")}
    closing_tag_string_map: ClassVar[dict[str, str]] = {}

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


class TestHelperFunctions:
    """Test helper functions in linter module."""

    def test_is_whitespace_with_whitespace_chars(self) -> None:
        """Test is_whitespace with actual whitespace characters."""
        assert is_whitespace(" ") is True
        assert is_whitespace("\t") is True
        assert is_whitespace("\n") is True
        assert is_whitespace("\r") is True

    def test_is_whitespace_with_non_whitespace_chars(self) -> None:
        """Test is_whitespace with non-whitespace characters."""
        assert is_whitespace("a") is False
        assert is_whitespace("1") is False
        assert is_whitespace(".") is False

    def test_attr_sort_with_none_attribute(self) -> None:
        """Test attr_sort prioritizes None attributes last."""
        result = attr_sort((None, "value"))
        assert result[0] is True  # None attributes come last

    def test_attr_sort_with_named_attribute(self) -> None:
        """Test attr_sort with named attribute."""
        result = attr_sort(("class", "value"))
        assert result[0] is False  # Named attributes come first


class TestHTMLLinter:
    """Test HTMLLinter class."""

    def test_linter_initialization_defaults(self) -> None:
        """Test HTMLLinter initialization with default values."""
        linter = HTMLLinter()

        assert linter.fix is False
        assert linter.check_doctype is False
        assert linter.preprocessor is None
        assert linter.attribute_processors == []  # noqa: WPS520 (supposed to be OK for asserts)
        assert linter.ignore_rules == ()  # noqa: WPS520 (supposed to be OK for asserts)

    def test_linter_initialization_with_parameters(self) -> None:
        """Test HTMLLinter initialization with custom parameters."""
        linter = HTMLLinter(
            fix=True,
            check_doctype=True,
            ignore_rules=["F1", "F2"],
        )

        assert linter.fix is True
        assert linter.check_doctype is True
        assert linter.ignore_rules == ["F1", "F2"]

    def test_linter_reset_state(self) -> None:
        """Test linter reset clears internal state."""
        linter = HTMLLinter()

        # Simulate some state
        linter._mode = Mode.DOCUMENT
        linter._errors = ["error"]
        linter._result = ["result"]

        linter.reset()

        assert linter._mode is None
        assert linter._errors == []  # noqa: WPS520 (supposed to be OK for asserts)
        assert linter._result == []  # noqa: WPS520 (supposed to be OK for asserts)

    def test_lint_simple_html(self) -> None:
        """Test linting simple valid HTML."""
        linter = HTMLLinter()
        html = "<div>Hello World</div>"

        result, errors = linter.lint(html)

        assert isinstance(result, str)
        assert isinstance(errors, list)

    def test_lint_with_doctype_checking_valid_html5(self) -> None:
        """Test linting with doctype checking on valid HTML5."""
        linter = HTMLLinter(check_doctype=True)
        html = "<!DOCTYPE html><div>Hello</div>"

        result, errors = linter.lint(html)

        # Should not raise DoctypeError
        assert isinstance(result, str)

    def test_lint_with_doctype_checking_invalid_doctype(self) -> None:
        """Test linting with doctype checking reports error for non-HTML5."""
        linter = HTMLLinter(check_doctype=True)
        html = '<!DOCTYPE html SYSTEM "about:legacy-compat"><div>Hello</div>'

        # Should not raise DoctypeError when check_doctype=True, but report as linting error
        result, errors = linter.lint(html)
        # Should have E1 error for invalid doctype
        e1_errors = [error for error in errors if error.rule.code == "E1"]
        assert len(e1_errors) > 0

    def test_lint_without_doctype_checking_invalid_doctype(self) -> None:
        """Test linting without doctype checking raises DoctypeError."""
        linter = HTMLLinter(check_doctype=False)
        html = '<!DOCTYPE html SYSTEM "about:legacy-compat"><div>Hello</div>'

        # Should raise DoctypeError when check_doctype=False to skip non-HTML5 files
        with pytest.raises(DoctypeError):
            linter.lint(html)

    def test_lint_with_structural_error(self) -> None:
        """Test linting detects structural errors."""
        linter = HTMLLinter()
        # Malformed HTML that should trigger structural errors
        html = "<div><span></div></span>"  # Mismatched tags

        result, errors = linter.lint(html)

        # Should detect structural issues
        assert len(errors) > 0

    def test_lint_with_fix_mode(self) -> None:
        """Test linting in fix mode modifies the HTML."""
        linter = HTMLLinter(fix=True)
        html = "<div   >  Hello World  </div>"

        result, _errors = linter.lint(html)

        # In fix mode, should clean up the HTML
        assert result != html  # Should be modified

    def test_lint_with_ignored_rules(self) -> None:
        """Test linting with ignored rules."""
        linter = HTMLLinter(ignore_rules=["F1"])
        # HTML that might trigger F1 rules
        html = "<div>Content</div>"

        _result, errors = linter.lint(html)

        # Should not report F1 errors
        f1_errors = [error for error in errors if error.rule.code == "F1"]
        assert len(f1_errors) == 0

    def test_lint_empty_html(self) -> None:
        """Test linting empty HTML."""
        linter = HTMLLinter()
        html = ""

        result, errors = linter.lint(html)

        assert result == ""
        assert isinstance(errors, list)

    def test_lint_whitespace_only_html(self) -> None:
        """Test linting HTML with only whitespace."""
        linter = HTMLLinter()
        html = "   \n\t  "

        result, errors = linter.lint(html)

        assert isinstance(result, str)
        assert isinstance(errors, list)

    def test_lint_with_preprocessing(self) -> None:
        """Test linting with preprocessor."""
        linter = HTMLLinter(preprocessor=MockPreprocessor())
        html = "<TEMPLATE>Content</TEMPLATE>"

        result, errors = linter.lint(html)

        # Preprocessor should have converted TEMPLATE to div
        assert "TEMPLATE" not in result
        assert "div" in result.lower()

    def test_lint_with_attribute_processors(self) -> None:
        """Test linting with attribute processors."""
        linter = HTMLLinter(attribute_processors=[whitespace.AttributeProcessor()])
        html = '<div class="  spaced   ">Content</div>'

        result, _errors = linter.lint(html)

        # Attribute processor should have cleaned up spacing
        assert isinstance(result, str)

    def test_lint_complex_html_structure(self) -> None:
        """Test linting complex HTML structure."""
        linter = HTMLLinter()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <div class="container">
                <p>Paragraph</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </body>
        </html>
        """

        result, errors = linter.lint(html)

        assert isinstance(result, str)
        assert isinstance(errors, list)
        # Should handle complex structure without crashing

    def test_lint_self_closing_tags(self) -> None:
        """Test linting self-closing tags."""
        linter = HTMLLinter()
        html = '<img src="test.jpg" alt="Test"><br><hr>'

        result, _errors = linter.lint(html)

        assert isinstance(result, str)
        # Should handle self-closing tags properly

    def test_lint_attributes_with_special_characters(self) -> None:
        """Test linting attributes containing special characters."""
        linter = HTMLLinter()
        html = '<div data-test="value with spaces" onclick="alert(\'hello\')">Content</div>'

        result, _errors = linter.lint(html)

        assert isinstance(result, str)
        # Should handle special characters in attributes

    def test_lint_nested_tags(self) -> None:
        """Test linting deeply nested tags."""
        linter = HTMLLinter()
        html = "<div><span><em><strong>Nested</strong></em></span></div>"

        result, _errors = linter.lint(html)

        assert isinstance(result, str)
        # Should handle nested structure
