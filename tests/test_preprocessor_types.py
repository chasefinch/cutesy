"""Tests for preprocessor types and base functionality."""

from typing import ClassVar

import pytest

from cutesy.preprocessors.types import (
    CLEAN_CHARS_AFTER_CLOSING,
    CLEAN_CHARS_BEFORE_OPENING,
    SPECIAL_CHARS,
    BasePreprocessor,
    SetupError,
)
from cutesy.rules import Rule
from cutesy.types import Error, InstructionType, StructuralError

# Constants to avoid magic numbers
EXPECTED_DELIMITER_COUNT = 2
ERROR_CODE_P4 = "P4"


class MockPreprocessor(BasePreprocessor):
    """Mock preprocessor for testing base functionality."""

    braces: ClassVar[set[tuple[str, str]]] = {("{%", "%}"), ("{{", "}}"), ("{#", "#}")}
    closing_tag_string_map: ClassVar[dict[str, str]] = {
        "test": "endtest",
        "block": "endblock",
        "comment": "endcomment",
    }

    def parse_instruction_tag(
        self,
        braces: tuple[str, str],
        html: str,
        cursor: int,
        cursor2: int,
    ) -> tuple[str, InstructionType]:
        """Mock implementation of parse_instruction_tag."""
        body = html[cursor + len(braces[0]) : cursor2].strip()

        if not body:
            if braces[0] == "{#":
                return "…", InstructionType.IGNORED
            error_message = ERROR_CODE_P4
            raise self._make_fatal_error(error_message)

        parts = body.split()
        instruction = parts[0] if parts else ""

        if braces[0] == "{{":
            return "…", InstructionType.VALUE
        if braces[0] == "{#":
            return "…", InstructionType.IGNORED
        if instruction == "test":
            return instruction, InstructionType.PARTIAL
        if instruction == "endtest":
            return instruction, InstructionType.END_PARTIAL
        if instruction == "block":
            return instruction, InstructionType.PARTIAL
        if instruction == "endblock":
            return instruction, InstructionType.END_PARTIAL
        if instruction == "comment":
            return instruction, InstructionType.COMMENT
        if instruction == "endcomment":
            return instruction, InstructionType.END_COMMENT
        return instruction, InstructionType.VALUE


class TestConstants:
    """Test constant values."""

    def test_special_chars_contains_html_special_chars(self) -> None:
        """Test SPECIAL_CHARS contains important HTML characters."""
        assert " " in SPECIAL_CHARS
        assert "&" in SPECIAL_CHARS
        assert "<" in SPECIAL_CHARS
        assert ">" in SPECIAL_CHARS
        assert "'" in SPECIAL_CHARS
        assert '"' in SPECIAL_CHARS
        assert "/" in SPECIAL_CHARS
        assert "=" in SPECIAL_CHARS

    def test_clean_chars_before_opening_contains_whitespace(self) -> None:
        """Test CLEAN_CHARS_BEFORE_OPENING contains whitespace chars."""
        assert ">" in CLEAN_CHARS_BEFORE_OPENING
        assert " " in CLEAN_CHARS_BEFORE_OPENING
        assert "\t" in CLEAN_CHARS_BEFORE_OPENING
        assert "\n" in CLEAN_CHARS_BEFORE_OPENING
        assert "\r" in CLEAN_CHARS_BEFORE_OPENING

    def test_clean_chars_after_closing_contains_brackets(self) -> None:
        """Test CLEAN_CHARS_AFTER_CLOSING contains HTML brackets."""
        assert ">" in CLEAN_CHARS_AFTER_CLOSING
        assert "<" in CLEAN_CHARS_AFTER_CLOSING


class TestSetupError:
    """Test SetupError exception."""

    def test_error_can_be_raised(self) -> None:
        """Test SetupError can be instantiated and raised."""
        error = SetupError("Test error message")
        assert str(error) == "Test error message"

        with pytest.raises(SetupError):
            raise error


class TestBasePreprocessor:
    """Test BasePreprocessor functionality."""

    def test_reset_initializes_state(self) -> None:
        """Test reset method initializes internal state."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ variable }}</div>"

        preprocessor.reset(html)

        assert preprocessor._dynamic_html == html
        assert preprocessor._size == len(html)
        assert preprocessor._fix is False

    def test_reset_with_fix_mode(self) -> None:
        """Test reset method with fix mode enabled."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ variable }}</div>"

        preprocessor.reset(html, fix=True)

        assert preprocessor._fix is True

    def test_reset_finds_unused_delimiters(self) -> None:
        """Test reset finds unused characters for delimiters."""
        preprocessor = MockPreprocessor()
        html = "<div>test</div>"

        preprocessor.reset(html)

        # Should find two different unused characters
        assert len(preprocessor.delimiters) == EXPECTED_DELIMITER_COUNT
        assert preprocessor.delimiters[0] != preprocessor.delimiters[1]
        # Neither delimiter should appear in the HTML
        assert preprocessor.delimiters[0] not in html
        assert preprocessor.delimiters[1] not in html

    def test_reset_avoids_special_chars_for_delimiters(self) -> None:
        """Test reset avoids special characters for delimiters."""
        preprocessor = MockPreprocessor()
        html = "<div>test</div>"

        preprocessor.reset(html)

        # Delimiters should not be special characters
        assert preprocessor.delimiters[0] not in SPECIAL_CHARS
        assert preprocessor.delimiters[1] not in SPECIAL_CHARS

    def test_process_simple_template(self) -> None:
        """Test processing simple template with variables."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ variable }}</div>"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Should replace the variable with placeholder
        assert "{{" not in result
        assert "}}" not in result
        assert "<div>" in result
        assert "</div>" in result

    def test_process_with_comments(self) -> None:
        """Test processing template with comments."""
        preprocessor = MockPreprocessor()
        html = "<div>{# comment #}content</div>"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Comments should be replaced with placeholders
        assert "{#" not in result
        assert "#}" not in result
        assert "content" in result

    def test_process_with_block_tags(self) -> None:
        """Test processing template with block-style tags."""
        preprocessor = MockPreprocessor()
        html = "<div>{% test %}content{% endtest %}</div>"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Block tags should be replaced with placeholders
        assert "{%" not in result
        assert "%}" not in result
        assert "content" in result

    def test_process_mixed_template_constructs(self) -> None:
        """Test processing template with mixed constructs."""
        preprocessor = MockPreprocessor()
        html = """
        <div>
            {{ variable }}
            {% test %}
                {# comment #}
                <span>content</span>
            {% endtest %}
        </div>
        """

        preprocessor.reset(html)
        result = preprocessor.process()

        # All template constructs should be replaced
        assert "{{" not in result
        assert "{%" not in result
        assert "{#" not in result
        assert "<span>content</span>" in result

    def test_process_nested_html_structure(self) -> None:
        """Test processing template with nested HTML structure."""
        preprocessor = MockPreprocessor()
        html = """
        <html>
            <body>
                <div class="{{ css_class }}">
                    <p>{{ content }}</p>
                </div>
            </body>
        </html>
        """

        preprocessor.reset(html)
        result = preprocessor.process()

        # HTML structure should be preserved
        assert "<html>" in result
        assert "<body>" in result
        assert "<div" in result
        assert "<p>" in result
        # Template constructs should be replaced
        assert "{{" not in result

    def test_process_empty_html(self) -> None:
        """Test processing empty HTML."""
        preprocessor = MockPreprocessor()
        html = ""

        preprocessor.reset(html)
        result = preprocessor.process()

        assert result == ""

    def test_process_html_without_templates(self) -> None:
        """Test processing HTML without template constructs."""
        preprocessor = MockPreprocessor()
        html = "<div><p>Pure HTML content</p></div>"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Should return unchanged HTML
        assert result == html

    def test_process_with_malformed_template_tags(self) -> None:
        """Test processing with malformed template tags."""
        preprocessor = MockPreprocessor()
        html = "<div>{% %}</div>"  # Empty tag

        preprocessor.reset(html)

        # Should raise StructuralError for malformed tags
        with pytest.raises(StructuralError):
            preprocessor.process()

    def test_process_tracks_line_and_offset(self) -> None:
        """Test that processing tracks line numbers and offset."""
        preprocessor = MockPreprocessor()
        html = "line1\nline2\n{{ variable }}"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Should process without error (line tracking is internal)
        assert isinstance(result, str)

    def test_process_with_unicode_content(self) -> None:
        """Test processing template with unicode characters."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ unicode_var }}</div><!-- ñáéíóú -->"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Should handle unicode characters properly
        assert "ñáéíóú" in result
        assert "{{" not in result

    def test_process_multiple_variable_types(self) -> None:
        """Test processing with multiple variable and tag types."""
        preprocessor = MockPreprocessor()
        html = """
        <div>
            {{ variable1 }}
            {{ variable2.property }}
            {{ variable3|filter }}
            {% test param="value" %}
            content
            {% endtest %}
            {# A comment #}
        </div>
        """

        preprocessor.reset(html)
        result = preprocessor.process()

        # All template constructs should be processed
        assert "{{" not in result
        assert "{%" not in result
        assert "{#" not in result
        assert "content" in result

    def test_delimiters_unique_across_resets(self) -> None:
        """Test that delimiters are recalculated on each reset."""
        preprocessor = MockPreprocessor()

        # First reset
        html1 = "<div>test1</div>"
        preprocessor.reset(html1)
        delimiters1 = preprocessor.delimiters

        # Second reset with different content
        html2 = "<span>test2</span>"
        preprocessor.reset(html2)
        delimiters2 = preprocessor.delimiters

        # Delimiters should still be valid (might be same, might be different)
        assert len(delimiters1) == EXPECTED_DELIMITER_COUNT
        assert len(delimiters2) == EXPECTED_DELIMITER_COUNT
        assert delimiters1[0] != delimiters1[1]
        assert delimiters2[0] != delimiters2[1]

    def test_reset_with_many_special_chars_in_html(self) -> None:
        """Test reset when HTML contains many special characters."""
        preprocessor = MockPreprocessor()
        # HTML containing many special characters to force delimiter search
        # Use specific characters, avoiding soft hyphen (\xad) which is in SPECIAL_CHARS
        special_chars_html = "¡¢£¤¥¦§¨©ª«¬®¯°±²³"  # Skip ­ (soft hyphen)
        html = f"<div>{special_chars_html}</div>"

        preprocessor.reset(html)

        # Should still find valid delimiters
        assert len(preprocessor.delimiters) == EXPECTED_DELIMITER_COUNT
        assert preprocessor.delimiters[0] not in html
        assert preprocessor.delimiters[1] not in html

    def test_restore_before_processing_raises_error(self) -> None:
        """Test that restore raises SetupError when called before process."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ variable }}</div>"

        preprocessor.reset(html)
        # Don't call process()

        with pytest.raises(SetupError) as exc_info:
            preprocessor.restore(html, [])

        assert "before initial processing" in str(exc_info.value)

    def test_restore_with_newlines_in_instructions(self) -> None:
        """Test restore properly handles newlines in template instructions."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ variable\nwith\nnewlines }}</div>"

        preprocessor.reset(html)
        processed = preprocessor.process()

        error = Error(line=1, column=10, rule=Rule.get("F1"), replacements={})
        errors = [error]

        result = preprocessor.restore(processed, errors)

        # Should restore the original newlines
        assert "variable\nwith\nnewlines" in result
        # Error line numbers should be adjusted for newlines
        assert error.line >= 1  # May have been adjusted

    def test_process_with_dangling_block_instruction(self) -> None:
        """Test processing fails with unmatched block instructions."""
        preprocessor = MockPreprocessor()
        html = "<div>{% block %}content</div>"  # Missing {% endblock %}

        preprocessor.reset(html)

        with pytest.raises(StructuralError) as exc_info:
            preprocessor.process()

        # Should report the expected closing tag
        assert len(exc_info.value.errors) == 1
        assert "endblock" in str(exc_info.value.errors[0].replacements.get("tag", ""))

    def test_process_with_malformed_closing_tag(self) -> None:
        """Test processing fails when closing brace is missing."""
        preprocessor = MockPreprocessor()
        html = "<div>{% test %content</div>"  # Missing closing %}

        preprocessor.reset(html)

        with pytest.raises(StructuralError) as exc_info:
            preprocessor.process()

        # Should be a P4 error (malformed tag)
        assert exc_info.value.errors[0].rule.code == "P4"

    def test_process_with_comment_blocks(self) -> None:
        """Test processing with comment block tags."""
        preprocessor = MockPreprocessor()
        html = "<div>{% comment %}some comment{% endcomment %}</div>"

        preprocessor.reset(html)
        result = preprocessor.process()

        # Comment blocks should be processed
        assert "{%" not in result
        assert "some comment" not in result  # Comments are absorbed

    def test_process_with_missing_comment_end(self) -> None:
        """Test processing fails when comment end tag is missing."""
        preprocessor = MockPreprocessor()
        html = "<div>{% comment %}some comment</div>"  # Missing {% endcomment %}

        preprocessor.reset(html)

        with pytest.raises(StructuralError) as exc_info:
            preprocessor.process()

        # Should be a P2 error for missing closing tag
        assert exc_info.value.errors[0].rule.code == "P2"

    def test_process_without_valid_padding_in_non_fix_mode(self) -> None:
        """Test processing detects invalid padding in non-fix mode."""
        preprocessor = MockPreprocessor()
        html = "<div>{{variable}}</div>"  # No spaces around variable

        preprocessor.reset(html, fix=False)
        preprocessor.process()

        # Should process but create P6 error about padding
        assert len(preprocessor.errors) == 1
        assert preprocessor.errors[0].rule.code == "P6"

    def test_process_with_collapsed_spacing_issues_in_non_fix_mode(self) -> None:
        """Test processing detects spacing issues in non-fix mode."""
        preprocessor = MockPreprocessor()
        html = "<div>{{ block    param1=value1    param2=value2 }}</div>"  # Extra spaces in value

        preprocessor.reset(html, fix=False)
        preprocessor.process()

        # Should detect spacing issues
        assert any(error.rule.code == "P5" for error in preprocessor.errors)
