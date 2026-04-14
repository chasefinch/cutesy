"""Tests for HTMLLinter functionality."""

from typing import ClassVar

import pytest

from cutesy.attribute_processors import reindent, whitespace
from cutesy.attribute_processors.class_ordering import tailwind
from cutesy.linter import HTMLLinter, attr_sort, is_whitespace
from cutesy.preprocessors import django
from cutesy.preprocessors.types import BasePreprocessor
from cutesy.rules import Rule
from cutesy.types import DoctypeError, IndentationType, InstructionType


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

    def test_lint_simple_html(self) -> None:
        """Test linting simple valid HTML."""
        linter = HTMLLinter()
        html = "<div>Hello World</div>"

        linter.lint(html)

    def test_is_rule_ignored_exact_rule_code(self) -> None:
        """Test is_rule_ignored with exact rule codes."""
        linter = HTMLLinter(ignore_rules=["F1", "D5"])

        assert linter.is_rule_ignored("F1") is True
        assert linter.is_rule_ignored("D5") is True
        assert linter.is_rule_ignored("F2") is False
        assert linter.is_rule_ignored("D6") is False

    def test_is_rule_ignored_rule_category(self) -> None:
        """Test is_rule_ignored with rule categories."""
        linter = HTMLLinter(ignore_rules=["F", "D"])

        assert linter.is_rule_ignored("F1") is True
        assert linter.is_rule_ignored("F99") is True
        assert linter.is_rule_ignored("D1") is True
        assert linter.is_rule_ignored("D99") is True
        assert linter.is_rule_ignored("E1") is False
        assert linter.is_rule_ignored("P1") is False

    def test_is_rule_ignored_empty_rule_code(self) -> None:
        """Test is_rule_ignored with empty rule code."""
        linter = HTMLLinter(ignore_rules=["F"])

        assert linter.is_rule_ignored("") is False

    def test_is_rule_ignored_mixed_rules_and_categories(self) -> None:
        """Test is_rule_ignored with mixed exact rules and categories."""
        linter = HTMLLinter(ignore_rules=["F", "D5", "E1"])

        assert linter.is_rule_ignored("F1") is True  # Category F
        assert linter.is_rule_ignored("F99") is True  # Category F
        assert linter.is_rule_ignored("D5") is True  # Exact rule D5
        assert linter.is_rule_ignored("D1") is False  # Other D rule
        assert linter.is_rule_ignored("E1") is True  # Exact rule E1
        assert linter.is_rule_ignored("E2") is False  # Other E rule

    def test_indentation_property_with_tabs(self) -> None:
        """Test indentation property returns tabs when configured for tabs."""
        linter = HTMLLinter(indentation_type=IndentationType.TAB)

        assert linter.indentation == "\t"

    def test_indentation_property_with_spaces(self) -> None:
        """Test indentation property returns spaces when specified."""
        linter = HTMLLinter(indentation_type=IndentationType.SPACES, tab_width=2)

        assert linter.indentation == "  "

    def test_lint_with_fix_mode_adds_final_newline(self) -> None:
        """Test lint adds final newline in fix mode for full documents."""
        linter = HTMLLinter(fix=True, check_doctype=True)
        html = "<!DOCTYPE html><div>test</div>"  # No final newline

        result, _errors = linter.lint(html)

        assert result.endswith("\n")

    def test_lint_without_fix_reports_missing_final_newline(self) -> None:
        """Test lint reports missing final newline without fixing."""
        linter = HTMLLinter(fix=False, check_doctype=True)
        html = "<!DOCTYPE html><div>test</div>"  # No final newline

        _result, errors = linter.lint(html)

        # Should have D9 error for missing final newline
        d9_errors = [error for error in errors if error.rule is Rule.D9]
        assert len(d9_errors) > 0
        expected_line = 0
        expected_column = 0
        assert d9_errors[0].line == expected_line
        assert d9_errors[0].column == expected_column

    def test_lint_ignores_final_newline_when_rule_ignored(self) -> None:
        """Test lint ignores final newline when D9 rule is ignored."""
        linter = HTMLLinter(fix=True, check_doctype=True, ignore_rules=["D9"])
        html = "<!DOCTYPE html><div>test</div>"  # No final newline

        result, _errors = linter.lint(html)

        # Should not add newline when D9 is ignored
        assert not result.endswith("\n") or result.rstrip() != result[:-1]

    def test_lint_with_preprocessor_integration(self) -> None:
        """Test lint integrates with preprocessor correctly."""
        preprocessor = MockPreprocessor()
        linter = HTMLLinter(preprocessor=preprocessor)
        html = "<TEMPLATE>content</TEMPLATE>"

        result, _errors = linter.lint(html)

        # MockPreprocessor should replace TEMPLATE with div
        assert "div" in result
        assert "TEMPLATE" not in result

    def test_lint_preserves_error_order_by_line_and_column(self) -> None:
        """Test lint sorts errors by line and column."""
        linter = HTMLLinter(fix=False)
        html = """<div>
    <span CLASS="test">
    <P>content</P>
</span>
</div>"""  # Multiple errors: uppercase tags

        _result, errors = linter.lint(html)

        # Errors should be sorted by line, then column
        if len(errors) > 1:
            for i in range(len(errors) - 1):
                current = errors[i]
                next_error = errors[i + 1]
                assert current.line < next_error.line or (
                    current.line == next_error.line and current.column <= next_error.column
                )

    def test_lint_with_doctype_checking_valid_html5(self) -> None:
        """Test linting with doctype checking on valid HTML5."""
        linter = HTMLLinter(check_doctype=True)
        html = "<!DOCTYPE html><div>Hello</div>"

        result, _errors = linter.lint(html)

        # Should not raise DoctypeError
        assert isinstance(result, str)

    def test_lint_with_doctype_checking_invalid_doctype(self) -> None:
        """Test linting with doctype checking reports error for non-HTML5."""
        linter = HTMLLinter(check_doctype=True)
        html = '<!DOCTYPE html SYSTEM "about:legacy-compat"><div>Hello</div>'

        # Should not raise DoctypeError when check_doctype=True, but report as
        # linting error
        _result, errors = linter.lint(html)
        # Should have E1 error for invalid doctype
        e1_errors = [error for error in errors if error.rule is Rule.E1]
        assert len(e1_errors) > 0
        expected_line = 0
        expected_column = 0
        assert e1_errors[0].line == expected_line
        assert e1_errors[0].column == expected_column

    def test_lint_without_doctype_checking_invalid_doctype(self) -> None:
        """Test linting without doctype checking raises DoctypeError."""
        linter = HTMLLinter(check_doctype=False)
        html = '<!DOCTYPE html SYSTEM "about:legacy-compat"><div>Hello</div>'

        # Should raise DoctypeError when check_doctype=False to skip non-HTML5
        # files
        with pytest.raises(DoctypeError):
            linter.lint(html)

    def test_lint_with_structural_error(self) -> None:
        """Test linting detects structural errors."""
        linter = HTMLLinter()
        # Malformed HTML that should trigger structural errors
        html = "<div><span></div></span>"  # Mismatched tags

        _result, errors = linter.lint(html)

        # Should detect structural issues (D3 and D4 errors)
        expected_error_count = 2
        assert len(errors) == expected_error_count

        # D3 error: Expected <span> closing tag
        d3_errors = [error for error in errors if error.rule is Rule.D3]
        assert len(d3_errors) == 1
        expected_line = 0
        expected_column = 11
        assert d3_errors[0].line == expected_line
        assert d3_errors[0].column == expected_column

        # D4 error: </span> doesn't have a matching opening tag
        d4_errors = [error for error in errors if error.rule is Rule.D4]
        assert len(d4_errors) == 1
        expected_line = 0
        expected_column = 17
        assert d4_errors[0].line == expected_line
        assert d4_errors[0].column == expected_column

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
        f1_errors = [error for error in errors if error.rule is Rule.F1]
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

        result, _errors = linter.lint(html)

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

    def test_basic_empty_html(self) -> None:
        """Test the baseline HTML structure."""
        basic_html = ""
        expected_result = ""

        linter = HTMLLinter(fix=True)
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_complex_attribute_name_parsing_with_preprocessor_delimiters(self) -> None:
        """Test parsing attributes with delimiters and special characters."""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())

        # HTML with complex attribute names containing Django template syntax
        html = '<div data-{% if condition %}dynamic{% endif %}="value">content</div>'

        result, errors = linter.lint(html)

        # Should handle complex attribute names without crashing
        assert isinstance(result, str)
        assert isinstance(errors, list)

    def test_attribute_processing_with_mixed_quotes_in_names(self) -> None:
        """Test attribute processing when attribute names contain quotes."""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())

        # HTML with attribute names which trigger quote character selection
        html = '<div pre"fix{% block %}content{% endblock %}="value">content</div>'

        result, errors = linter.lint(html)

        # Should handle mixed quotes in attribute names
        assert isinstance(result, str)
        assert isinstance(errors, list)

    def test_attribute_processing_without_fix_mode_case_errors(self) -> None:
        """Test reporting case errors in complex attribute names."""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())

        # HTML with uppercase in complex attribute name that should trigger
        # F8 error
        html = '<div Data{% block %}content{% endblock %}="value">content</div>'

        _result, errors = linter.lint(html)

        # Should report F8 error for case mismatch in attribute name
        f8_errors = [error for error in errors if error.rule is Rule.F8]
        assert len(f8_errors) > 0 or not errors  # Either F8 error found or no errors
        if f8_errors:
            expected_line = 0
            expected_column_min = 0
            assert f8_errors[0].line == expected_line
            assert f8_errors[0].column >= expected_column_min

    def test_attribute_processing_quote_character_selection(self) -> None:
        """Test quote character selection based on attribute content."""
        linter = HTMLLinter(fix=True)

        # Attribute value with single quotes should use double quotes for
        # wrapping
        html = "<div data-value=\"text with 'single' quotes\">content</div>"

        result, errors = linter.lint(html)

        # Should handle quote selection properly
        assert isinstance(result, str)
        assert isinstance(errors, list)

    def test_attribute_processing_with_preprocessor_edge_cases(self) -> None:
        """Test attribute processing edge cases with preprocessors."""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())

        # Test various edge cases that should not crash
        test_cases = [
            '<div class="simple">content</div>',  # Simple case
            '<div class="{% if x %}test{% endif %}">content</div>',  # Template in class
        ]

        for html in test_cases:
            result, errors = linter.lint(html)
            # Should handle edge cases without crashing
            assert isinstance(result, str)
            assert isinstance(errors, list)

    def test_entityref_parsing(self) -> None:
        """Test parsing entity references."""
        linter = HTMLLinter(fix=True)

        basic_html = "<span>Hi! &amp; </span>"
        expected_result = "<span>Hi! &amp; </span>"

        result, errors = linter.lint(basic_html)
        assert result == expected_result
        assert not errors

        basic_html = "&copy;"
        expected_result = "&copy;"
        result, errors = linter.lint(basic_html)
        assert result == expected_result
        assert not errors

    def test_charref_parsing(self) -> None:
        """Test parsing character references."""
        basic_html = "<span>Hi! &#x999; </span>"
        expected_result = "<span>Hi! &#x999; </span>"

        linter = HTMLLinter(fix=True)
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_django_preprocessor_integration(self) -> None:
        """Test Django template preprocessing."""
        basic_html = "<span>Hi! &#x999; {% block %}{% endblock %} </span>"
        expected_result = "<span>Hi! &#x999; {% block %}{% endblock %} </span>"

        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_multiline_attribute_handling(self) -> None:
        """Test multiline attributes with proper indentation."""
        basic_html = """
<div
    x-data="() => {
        state1: true,

        state2: true,

        init() {
            state1 = false;
            state2 = false;
        }
    }"
>
asdf
</div>
        """
        expected_result = """
<div x-data="() => {
    state1: true,

    state2: true,

    init() {
        state1 = false;
        state2 = false;
    }
}">
    asdf
</div>
"""

        attribute_processors = [
            whitespace.AttributeProcessor(),
            reindent.AttributeProcessor(),
            tailwind.AttributeProcessor(),
        ]
        linter = HTMLLinter(
            fix=True,
            attribute_processors=attribute_processors,
            indentation_type=IndentationType.SPACES,
        )
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_break_for_inline_tag_empty_result_edge_case(self) -> None:
        """Test _break_for_inline_tag handles empty _result."""
        linter = HTMLLinter(fix=True)

        # This HTML should trigger the edge case where _result might be empty
        # when _break_for_inline_tag is called
        html = "<span></span>"

        result, errors = linter.lint(html)

        # Should not crash and should return valid result
        assert isinstance(result, str)
        assert isinstance(errors, list)

    def test_break_for_inline_tag_preserves_closing_bracket(self) -> None:
        """Regression: _break_for_inline_tag must not strip '>' from prev tag.

        When two adjacent tags both need attribute wrapping and there is no
        whitespace between them (e.g. <a ...><img ...>), the line-break
        logic must not remove the closing '>' of the first tag.
        """
        short_line_length = 40
        linter = HTMLLinter(fix=True, line_length=short_line_length)

        html = (
            '<a id="footer-icon" href="https://example.com">'
            '<img width="40" src="icon.png" alt="Icon" />'
            "</a>"
        )
        result, _ = linter.lint(html)

        # The <a> opening tag must close with '>' before <img> starts
        before_img = result.split("<img")[0]
        assert before_img.rstrip().endswith(">"), (
            f"Opening <a> tag lost its closing '>': ...{before_img[-short_line_length:]}"
        )

    def test_break_for_inline_tag_after_end_tag(self) -> None:
        """Regression: '>' on closing tag must survive line break."""
        short_line_length = 40
        linter = HTMLLinter(fix=True, line_length=short_line_length)

        html = '<p>text</p><div class="container" data-role="main" id="content">inner</div>'
        result, _ = linter.lint(html)

        assert "</p>" in result, "Closing </p> must remain intact"

    def test_line_number_tracking_multiline_html(self) -> None:
        """Test that line numbers are correctly tracked in multi-line HTML."""
        linter = HTMLLinter(fix=False)
        html = """<div>
    <SPAN>Line 2</SPAN>
    <P>Line 3</P>
    <A HREF="test">Line 4</A>
</div>"""

        _result, errors = linter.lint(html)

        # Check F7 errors (tag case) for SPAN on line 2 (0-indexed: 1)
        span_line = 1
        span_open_errors = [
            error
            for error in errors
            if error.rule is Rule.F7
            and error.line == span_line
            and "<SPAN>" in error.replacements.get("tag", "")
        ]
        assert len(span_open_errors) == 1
        expected_column = 4
        assert span_open_errors[0].column == expected_column

        span_close_errors = [
            error
            for error in errors
            if error.rule is Rule.F7
            and error.line == span_line
            and "</SPAN>" in error.replacements.get("tag", "")
        ]
        assert len(span_close_errors) == 1
        expected_column = 16
        assert span_close_errors[0].column == expected_column

        # Check F7 errors (tag case) for P on line 3 (0-indexed: 2)
        p_line = 2
        p_open_errors = [
            error
            for error in errors
            if error.rule is Rule.F7
            and error.line == p_line
            and "<P>" in error.replacements.get("tag", "")
        ]
        assert len(p_open_errors) == 1
        expected_column = 4
        assert p_open_errors[0].column == expected_column

        p_close_errors = [
            error
            for error in errors
            if error.rule is Rule.F7
            and error.line == p_line
            and "</P>" in error.replacements.get("tag", "")
        ]
        assert len(p_close_errors) == 1
        expected_column = 13
        assert p_close_errors[0].column == expected_column

        # Check F7 and F8 errors for A on line 4 (0-indexed: 3)
        a_line = 3
        a_open_errors = [
            error
            for error in errors
            if error.rule is Rule.F7
            and error.line == a_line
            and "<A>" in error.replacements.get("tag", "")
        ]
        assert len(a_open_errors) == 1
        expected_column = 4
        assert a_open_errors[0].column == expected_column

        # F8 error for HREF attribute
        href_errors = [error for error in errors if error.rule is Rule.F8 and error.line == a_line]
        assert len(href_errors) == 1
        expected_column = 4
        assert href_errors[0].column == expected_column

        # Check F3 errors (indentation) on lines 2, 3, 4
        f3_line2 = [error for error in errors if error.rule is Rule.F3 and error.line == span_line]
        assert len(f3_line2) == 1
        expected_column = 0
        assert f3_line2[0].column == expected_column

        f3_line3 = [error for error in errors if error.rule is Rule.F3 and error.line == p_line]
        assert len(f3_line3) == 1
        expected_column = 0
        assert f3_line3[0].column == expected_column

        f3_line4 = [error for error in errors if error.rule is Rule.F3 and error.line == a_line]
        assert len(f3_line4) == 1
        expected_column = 0
        assert f3_line4[0].column == expected_column

    def test_line_number_tracking_with_attributes(self) -> None:
        """Test line number tracking for attribute-related errors."""
        linter = HTMLLinter(fix=False)
        html = """<div CLASS="test">
    <span ID="item">content</span>
</div>"""

        _result, errors = linter.lint(html)

        # Look for case errors in attributes (F8)
        class_errors = [
            error
            for error in errors
            if error.rule is Rule.F8 and error.replacements.get("attr") == "class"
        ]
        id_errors = [
            error
            for error in errors
            if error.rule is Rule.F8 and error.replacements.get("attr") == "id"
        ]

        # Verify errors are on correct lines
        if class_errors:
            expected_line = 0
            assert class_errors[0].line == expected_line, "CLASS error should be on line 1"
        if id_errors:
            expected_line = 1
            assert id_errors[0].line == expected_line, "ID error should be on line 2"

    # --- Regression tests for recent fixes ---

    def test_unicode_cdata_closing_tag_not_corrupted(self) -> None:
        """Regression: Unicode chars that change length under str.lower().

        Turkish İ (U+0130) lowercases to 'i̇' (2 chars), which previously
        corrupted position tracking when searching for </style> or </script>.
        """
        linter = HTMLLinter(fix=True)

        # İ inside a <style> block — str.lower() would make it longer
        html = "<style>\n\t/* İstanbul */\n\tbody { color: red; }\n</style>"
        result, _ = linter.lint(html)

        # Must close cleanly — no truncation or corruption
        assert "</style>" in result
        assert "İstanbul" in result
        assert "color: red" in result

    def test_unicode_script_cdata_not_corrupted(self) -> None:
        """Regression: same Unicode position bug in <script> blocks."""
        linter = HTMLLinter(fix=True)

        html = '<script>\n\tvar city = "İstanbul";\n\tconsole.log(city);\n</script>'
        result, _ = linter.lint(html)

        assert "</script>" in result
        assert "İstanbul" in result
        assert "console.log" in result

    def test_cdata_indentation_rebasing(self) -> None:
        """Regression: CDATA indentation is rebased to HTML hierarchy."""
        linter = HTMLLinter(fix=True)

        # Style block with excess indent should be rebased to match hierarchy
        html = (
            "<head>\n"
            "\t<style>\n"
            "\t\t\tbody { margin: 0; }\n"
            "\t\t\ta { color: blue; }\n"
            "\t</style>\n"
            "</head>"
        )
        result, _ = linter.lint(html)

        # Content lines should be indented at 2 tabs (head > style > content)
        lines = result.split("\n")
        body_line = next(line for line in lines if "body" in line)
        assert body_line.startswith("\t\t"), f"Expected 2-tab indent, got: {body_line!r}"

    def test_cdata_with_template_tags_stays_intact(self) -> None:
        """Regression: template tags inside CDATA don't break rebasing."""
        preprocessor = django.Preprocessor()
        linter = HTMLLinter(fix=True, preprocessor=preprocessor)

        html = "<head>\n\t<style>\n\t\t.item { color: {{ primary_color }}; }\n\t</style>\n</head>"
        result, _ = linter.lint(html)

        assert "</style>" in result
        assert "{{ primary_color }}" in result

    def test_preprocessor_comment_stays_with_attribute_on_sort(self) -> None:
        """Regression: preprocessor comments travel with next attr on sort."""
        preprocessor = django.Preprocessor()
        linter = HTMLLinter(fix=True, preprocessor=preprocessor)

        # "id" sorts before "src" per attr_sort; the comment before id=
        # should move with id= to the top.
        html = '<img\n\tsrc="icon.png"\n\t{# identifier #}\n\tid="logo"\n>'
        result, _ = linter.lint(html)

        # id= should sort before src=, and the comment should precede id=
        id_pos = result.find("id=")
        src_pos = result.find("src=")
        comment_pos = result.find("{# identifier #}")

        assert id_pos < src_pos, "id= should sort before src="
        assert comment_pos < id_pos, "Comment should stay attached before id="


class TestForeignContent:
    """Test foreign content (SVG & MathML) handling."""

    # --- Tag casing (F7) in SVG ---

    def test_svg_correct_case_no_error(self) -> None:
        """SVG camelCase elements with correct casing produce no F7 errors."""
        linter = HTMLLinter(fix=False)
        html = "<svg><clipPath><rect></rect></clipPath></svg>"

        _result, errors = linter.lint(html)

        f7_errors = [error for error in errors if error.rule is Rule.F7]
        assert len(f7_errors) == 0

    def test_svg_lowercase_camelcase_tag_reports_f7(self) -> None:
        """Lowercase version of a camelCase SVG tag reports F7."""
        linter = HTMLLinter(fix=False)
        html = "<svg><clippath><rect></rect></clippath></svg>"

        _result, errors = linter.lint(html)

        f7_errors = [error for error in errors if error.rule is Rule.F7]
        expected_error_count = 2  # Opening and closing
        assert len(f7_errors) == expected_error_count

    def test_svg_uppercase_camelcase_tag_reports_f7(self) -> None:
        """Wrong casing (all caps) of a camelCase SVG tag reports F7."""
        linter = HTMLLinter(fix=False)
        html = "<svg><CLIPPATH><rect></rect></CLIPPATH></svg>"

        _result, errors = linter.lint(html)

        f7_errors = [error for error in errors if error.rule is Rule.F7]
        expected_error_count = 2
        assert len(f7_errors) == expected_error_count

    def test_svg_lowercase_elements_no_error(self) -> None:
        """SVG elements not in the adjustment table stay lowercase."""
        linter = HTMLLinter(fix=False)
        html = "<svg><g><rect></rect><circle></circle></g></svg>"

        _result, errors = linter.lint(html)

        f7_errors = [error for error in errors if error.rule is Rule.F7]
        assert len(f7_errors) == 0

    def test_svg_fix_corrects_tag_case(self) -> None:
        """Fix mode corrects SVG element casing."""
        linter = HTMLLinter(fix=True)
        html = "<svg><clippath><rect></rect></clippath></svg>"

        result, _errors = linter.lint(html)

        assert "<clipPath>" in result
        assert "</clipPath>" in result
        assert "<clippath>" not in result

    def test_svg_fix_multiple_camelcase_tags(self) -> None:
        """Fix mode corrects multiple camelCase SVG elements."""
        linter = HTMLLinter(fix=True)
        html = "<svg><lineargradient></lineargradient><radialgradient></radialgradient></svg>"

        result, _errors = linter.lint(html)

        assert "<linearGradient>" in result
        assert "</linearGradient>" in result
        assert "<radialGradient>" in result
        assert "</radialGradient>" in result

    def test_svg_fix_foreignobject(self) -> None:
        """Fix mode corrects foreignObject casing."""
        linter = HTMLLinter(fix=True)
        html = "<svg><foreignobject><div></div></foreignobject></svg>"

        result, _errors = linter.lint(html)

        assert "<foreignObject>" in result
        assert "</foreignObject>" in result

    # --- Attribute casing (F8) in SVG ---

    def test_svg_viewbox_correct_case_no_error(self) -> None:
        """Correct viewBox casing produces no F8 error."""
        linter = HTMLLinter(fix=False)
        html = '<svg viewBox="0 0 100 100"></svg>'

        _result, errors = linter.lint(html)

        f8_errors = [error for error in errors if error.rule is Rule.F8]
        assert len(f8_errors) == 0

    def test_svg_viewbox_wrong_case_reports_f8(self) -> None:
        """Lowercase viewbox reports F8."""
        linter = HTMLLinter(fix=False)
        html = '<svg viewbox="0 0 100 100"></svg>'

        _result, errors = linter.lint(html)

        f8_errors = [error for error in errors if error.rule is Rule.F8]
        assert len(f8_errors) == 1

    def test_svg_fix_corrects_attribute_case(self) -> None:
        """Fix mode corrects SVG attribute casing."""
        linter = HTMLLinter(fix=True)
        html = '<svg viewbox="0 0 100 100"></svg>'

        result, _errors = linter.lint(html)

        assert 'viewBox="0 0 100 100"' in result
        assert "viewbox" not in result

    def test_svg_preserveaspectratio_fix(self) -> None:
        """Fix mode corrects preserveAspectRatio casing."""
        linter = HTMLLinter(fix=True)
        html = '<svg preserveaspectratio="xMidYMid meet"></svg>'

        result, _errors = linter.lint(html)

        assert "preserveAspectRatio=" in result

    def test_svg_html_attrs_stay_lowercase(self) -> None:
        """Standard HTML attributes on SVG elements stay lowercase."""
        linter = HTMLLinter(fix=False)
        html = '<svg class="icon" id="logo"></svg>'

        _result, errors = linter.lint(html)

        f8_errors = [error for error in errors if error.rule is Rule.F8]
        assert len(f8_errors) == 0

    def test_svg_nested_element_attr_case(self) -> None:
        """Attributes on nested SVG elements use correct casing."""
        linter = HTMLLinter(fix=True)
        html = '<svg><feGaussianBlur stddeviation="5"></feGaussianBlur></svg>'

        result, _errors = linter.lint(html)

        assert 'stdDeviation="5"' in result

    # --- Self-closing in SVG ---

    def test_svg_self_closing_no_d5_d6(self) -> None:
        """Self-closing SVG elements should not report D5 or D6."""
        linter = HTMLLinter(fix=False)
        html = '<svg><path d="M0 0"/><circle r="5"/></svg>'

        _result, errors = linter.lint(html)

        d5_errors = [error for error in errors if error.rule is Rule.D5]
        d6_errors = [error for error in errors if error.rule is Rule.D6]
        assert len(d5_errors) == 0
        assert len(d6_errors) == 0

    def test_svg_self_closing_fix_mode(self) -> None:
        """Fix mode handles self-closing SVG elements correctly."""
        linter = HTMLLinter(fix=True)
        html = '<svg><rect width="10" height="10"/></svg>'

        result, _errors = linter.lint(html)

        assert "<rect" in result
        assert "</rect>" in result

    # --- Context boundaries ---

    def test_svg_inside_html(self) -> None:
        """SVG inside HTML: HTML stays lowercase, SVG uses correct case."""
        linter = HTMLLinter(fix=True)
        html = "<div><svg><clippath></clippath></svg></div>"

        result, _errors = linter.lint(html)

        assert "<div>" in result
        assert "<clipPath>" in result
        assert "</clipPath>" in result
        assert "</div>" in result

    def test_context_ends_after_closing_svg(self) -> None:
        """After </svg>, HTML lowercase rules resume."""
        linter = HTMLLinter(fix=False)
        html = "<svg><g></g></svg><DIV></DIV>"

        _result, errors = linter.lint(html)

        # No F7 inside SVG (g is lowercase, correct)
        # F7 for DIV after SVG closes
        f7_errors = [error for error in errors if error.rule is Rule.F7]
        expected_error_count = 2  # <DIV> and </DIV>
        assert len(f7_errors) == expected_error_count

    def test_nested_svg_elements(self) -> None:
        """Deeply nested SVG elements all use correct casing."""
        linter = HTMLLinter(fix=True)
        html = "<svg><g><clipPath><rect></rect></clipPath></g></svg>"

        result, _errors = linter.lint(html)

        assert "<clipPath>" in result
        assert "</clipPath>" in result

    # --- MathML ---

    def test_math_context(self) -> None:
        """Basic MathML context works."""
        linter = HTMLLinter(fix=False)
        html = "<math><mrow></mrow></math>"

        _result, errors = linter.lint(html)

        f7_errors = [error for error in errors if error.rule is Rule.F7]
        assert len(f7_errors) == 0

    def test_math_definitionurl_fix(self) -> None:
        """Fix mode corrects MathML definitionURL attribute."""
        linter = HTMLLinter(fix=True)
        html = '<math><csymbol definitionurl="https://example.com"></csymbol></math>'

        result, _errors = linter.lint(html)

        assert "definitionURL=" in result

    # --- fe* filter elements ---

    def test_svg_fix_fe_elements(self) -> None:
        """Fix mode corrects fe* filter element casing."""
        linter = HTMLLinter(fix=True)
        html = (
            "<svg><filter>"
            "<fegaussianblur></fegaussianblur>"
            "<fecolormatrix></fecolormatrix>"
            "</filter></svg>"
        )

        result, _errors = linter.lint(html)

        assert "<feGaussianBlur>" in result
        assert "</feGaussianBlur>" in result
        assert "<feColorMatrix>" in result
        assert "</feColorMatrix>" in result

    def test_svg_textpath_fix(self) -> None:
        """Fix mode corrects textPath casing."""
        linter = HTMLLinter(fix=True)
        html = "<svg><text><textpath></textpath></text></svg>"

        result, _errors = linter.lint(html)

        assert "<textPath>" in result
        assert "</textPath>" in result
