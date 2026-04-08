"""Tests for Django preprocessor functionality."""

import pytest

from cutesy.preprocessors.django import Preprocessor
from cutesy.types import ConfigurationError, InstructionType, StructuralError


class TestDjangoPreprocessor:
    """Test Django template preprocessor."""

    def test_initialization(self) -> None:
        """Test Django preprocessor initialization."""
        preprocessor = Preprocessor()

        # Check class variables are set correctly
        assert ("{%", "%}") in preprocessor.braces
        assert ("{{", "}}") in preprocessor.braces
        assert ("{#", "#}") in preprocessor.braces

        assert "freeform" in preprocessor.closing_tag_string_map
        assert "comment" in preprocessor.closing_tag_string_map

    def test_parse_instruction_tag_value_type(self) -> None:
        """Test parsing Django variable tags (value type)."""
        preprocessor = Preprocessor()
        html = "{{ variable }}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{{", "}}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "…"
        assert instruction_type == InstructionType.VALUE

    def test_parse_instruction_tag_if_conditional(self) -> None:
        """Test parsing Django if tag."""
        preprocessor = Preprocessor()
        html = "{% if condition %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "if"
        assert instruction_type == InstructionType.CONDITIONAL

    def test_parse_instruction_tag_endif_conditional(self) -> None:
        """Test parsing Django endif tag."""
        preprocessor = Preprocessor()
        html = "{% endif %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endif"
        assert instruction_type == InstructionType.END_CONDITIONAL

    def test_parse_instruction_tag_elif_conditional(self) -> None:
        """Test parsing Django elif tag."""
        preprocessor = Preprocessor()
        html = "{% elif condition %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "elif"
        assert instruction_type == InstructionType.MID_CONDITIONAL

    def test_parse_instruction_tag_else_conditional(self) -> None:
        """Test parsing Django else tag."""
        preprocessor = Preprocessor()
        html = "{% else %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "else"
        assert instruction_type == InstructionType.LAST_CONDITIONAL

    def test_parse_instruction_tag_for_repeatable(self) -> None:
        """Test parsing Django for tag."""
        preprocessor = Preprocessor()
        html = "{% for item in items %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "for"
        assert instruction_type == InstructionType.REPEATABLE

    def test_parse_instruction_tag_endfor_repeatable(self) -> None:
        """Test parsing Django endfor tag."""
        preprocessor = Preprocessor()
        html = "{% endfor %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endfor"
        assert instruction_type == InstructionType.END_REPEATABLE

    def test_parse_instruction_tag_empty_for(self) -> None:
        """Test parsing Django empty tag in for loops."""
        preprocessor = Preprocessor()
        html = "{% empty %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "empty"
        assert instruction_type == InstructionType.MID_CONDITIONAL

    def test_parse_instruction_tag_block_partial(self) -> None:
        """Test parsing Django block tag."""
        preprocessor = Preprocessor()
        html = "{% block content %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "block"
        assert instruction_type == InstructionType.PARTIAL

    def test_parse_instruction_tag_endblock_partial(self) -> None:
        """Test parsing Django endblock tag."""
        preprocessor = Preprocessor()
        html = "{% endblock %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endblock"
        assert instruction_type == InstructionType.END_PARTIAL

    def test_parse_instruction_tag_with_partial(self) -> None:
        """Test parsing Django with tag."""
        preprocessor = Preprocessor()
        html = "{% with value=variable %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "with"
        assert instruction_type == InstructionType.PARTIAL

    def test_parse_instruction_tag_endwith_partial(self) -> None:
        """Test parsing Django endwith tag."""
        preprocessor = Preprocessor()
        html = "{% endwith %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endwith"
        assert instruction_type == InstructionType.END_PARTIAL

    def test_parse_instruction_tag_comment_freeform(self) -> None:
        """Test parsing Django comment tag."""
        preprocessor = Preprocessor()
        html = "{% comment %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "comment"
        assert instruction_type == InstructionType.COMMENT

    def test_parse_instruction_tag_endcomment_freeform(self) -> None:
        """Test parsing Django endcomment tag."""
        preprocessor = Preprocessor()
        html = "{% endcomment %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endcomment"
        assert instruction_type == InstructionType.END_COMMENT

    def test_parse_instruction_tag_spaceless_freeform(self) -> None:
        """Test parsing Django spaceless tag."""
        preprocessor = Preprocessor()
        html = "{% spaceless %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "spaceless"
        assert instruction_type == InstructionType.FREEFORM

    def test_parse_instruction_tag_endspaceless_freeform(self) -> None:
        """Test parsing Django endspaceless tag."""
        preprocessor = Preprocessor()
        html = "{% endspaceless %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endspaceless"
        assert instruction_type == InstructionType.END_FREEFORM

    def test_parse_instruction_tag_blocktrans_conditional(self) -> None:
        """Test parsing Django blocktrans tag."""
        preprocessor = Preprocessor()
        html = "{% blocktrans %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "blocktrans"
        assert instruction_type == InstructionType.CONDITIONAL

    def test_parse_instruction_tag_plural_conditional(self) -> None:
        """Test parsing Django plural tag."""
        preprocessor = Preprocessor()
        html = "{% plural %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "plural"
        assert instruction_type == InstructionType.LAST_CONDITIONAL

    def test_parse_instruction_tag_endblocktrans_conditional(self) -> None:
        """Test parsing Django endblocktrans tag."""
        preprocessor = Preprocessor()
        html = "{% endblocktrans %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endblocktrans"
        assert instruction_type == InstructionType.END_CONDITIONAL

    def test_parse_instruction_tag_while_repeatable(self) -> None:
        """Test parsing Django while tag."""
        preprocessor = Preprocessor()
        html = "{% while condition %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "while"
        assert instruction_type == InstructionType.REPEATABLE

    def test_parse_instruction_tag_endwhile_repeatable(self) -> None:
        """Test parsing Django endwhile tag."""
        preprocessor = Preprocessor()
        html = "{% endwhile %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endwhile"
        assert instruction_type == InstructionType.END_REPEATABLE

    def test_parse_instruction_tag_comment_ignored(self) -> None:
        """Test parsing Django comment tags."""
        preprocessor = Preprocessor()
        html = "{# This is a comment #}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{#", "#}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "…"
        assert instruction_type == InstructionType.IGNORED

    def test_parse_instruction_tag_freeform_special_comment(self) -> None:
        """Test parsing special freeform comment directive."""
        preprocessor = Preprocessor()
        html = "{# freeform #}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{#", "#}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "freeform"
        assert instruction_type == InstructionType.FREEFORM

    def test_parse_instruction_tag_endfreeform_special_comment(self) -> None:
        """Test parsing special endfreeform comment directive."""
        preprocessor = Preprocessor()
        html = "{# endfreeform #}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{#", "#}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "endfreeform"
        assert instruction_type == InstructionType.END_FREEFORM

    def test_parse_instruction_tag_empty_comment(self) -> None:
        """Test parsing empty Django comment."""
        preprocessor = Preprocessor()
        html = "{# #}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{#", "#}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "…"
        assert instruction_type == InstructionType.IGNORED

    def test_parse_instruction_tag_unknown_tag_as_value(self) -> None:
        """Test parsing unknown Django tag defaults to value type."""
        preprocessor = Preprocessor()
        html = "{% unknown_tag %}"

        instruction, instruction_type = preprocessor.parse_instruction_tag(
            ("{%", "%}"),
            html,
            0,
            len(html) - 2,
        )

        assert instruction == "unknown_tag"
        assert instruction_type == InstructionType.VALUE

    def test_parse_instruction_tag_empty_tag_raises_error(self) -> None:
        """Test parsing empty Django tag raises error."""
        preprocessor = Preprocessor()
        html = "{% %}"

        # Initialize the attributes that make_fatal_error expects
        preprocessor.line = 1
        preprocessor.offset = 0

        # This should raise a StructuralError for P4 code
        with pytest.raises(StructuralError) as exc_info:
            preprocessor.parse_instruction_tag(("{%", "%}"), html, 0, len(html) - 2)

        assert exc_info.value.errors[0].rule.code == "P4"


class TestCustomTags:
    """Test custom_tags configuration for the Django preprocessor."""

    def test_custom_partial_tag(self) -> None:
        """Custom partial tag is recognized as PARTIAL/END_PARTIAL."""
        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})

        braces = ("{%", "%}")
        html_open = "{% macro my_macro %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html_open, 0, len(html_open) - 2,
        )
        assert instruction == "macro"
        assert itype == InstructionType.PARTIAL

        html_close = "{% endmacro %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html_close, 0, len(html_close) - 2,
        )
        assert instruction == "endmacro"
        assert itype == InstructionType.END_PARTIAL

    def test_custom_conditional_tag(self) -> None:
        """Custom conditional tag is recognized."""
        preprocessor = Preprocessor(custom_tags={"conditional": [["switch", "endswitch"]]})

        braces = ("{%", "%}")
        html_open = "{% switch value %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html_open, 0, len(html_open) - 2,
        )
        assert itype == InstructionType.CONDITIONAL

        html_close = "{% endswitch %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html_close, 0, len(html_close) - 2,
        )
        assert itype == InstructionType.END_CONDITIONAL

    def test_custom_repeatable_tag(self) -> None:
        """Custom repeatable tag is recognized."""
        preprocessor = Preprocessor(custom_tags={"repeatable": [["each", "endeach"]]})

        braces = ("{%", "%}")
        html_open = "{% each items %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html_open, 0, len(html_open) - 2,
        )
        assert itype == InstructionType.REPEATABLE

        html_close = "{% endeach %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html_close, 0, len(html_close) - 2,
        )
        assert itype == InstructionType.END_REPEATABLE

    def test_non_end_prefix_closing_tag(self) -> None:
        """Custom pair with a closing tag that doesn't start with 'end'."""
        preprocessor = Preprocessor(
            custom_tags={"partial": [["call", "caller"]]},
        )

        braces = ("{%", "%}")
        html_open = "{% call my_func %}"
        _, itype = preprocessor.parse_instruction_tag(
            braces, html_open, 0, len(html_open) - 2,
        )
        assert itype == InstructionType.PARTIAL

        html_close = "{% caller %}"
        _, itype = preprocessor.parse_instruction_tag(
            braces, html_close, 0, len(html_close) - 2,
        )
        assert itype == InstructionType.END_PARTIAL

    def test_builtin_tags_still_work(self) -> None:
        """Adding custom tags does not break built-in tags."""
        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})

        braces = ("{%", "%}")
        html = "{% block content %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html, 0, len(html) - 2,
        )
        assert instruction == "block"
        assert itype == InstructionType.PARTIAL

    def test_unknown_tag_still_value(self) -> None:
        """Unrecognized tags still fall through to VALUE."""
        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})

        braces = ("{%", "%}")
        html = "{% load static %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html, 0, len(html) - 2,
        )
        assert itype == InstructionType.VALUE

    def test_unknown_category_raises(self) -> None:
        """Invalid category name raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Unknown custom_tags category"):
            Preprocessor(custom_tags={"bogus": [["foo", "endfoo"]]})

    def test_collision_with_builtin_raises(self) -> None:
        """Custom tag that conflicts with a built-in tag raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="conflicts with built-in"):
            Preprocessor(custom_tags={"partial": [["block", "endblock"]]})

    def test_non_list_value_raises(self) -> None:
        """Non-list value for a category raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must be a list"):
            Preprocessor(custom_tags={"partial": "macro"})  # type: ignore[dict-item]

    def test_bad_pair_raises(self) -> None:
        """Entry that isn't a [start, end] pair raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="\\[start, end\\] pairs"):
            Preprocessor(custom_tags={"partial": [["macro"]]})

        with pytest.raises(ConfigurationError, match="\\[start, end\\] pairs"):
            Preprocessor(custom_tags={"partial": ["macro"]})  # type: ignore[list-item]

    def test_no_custom_tags_backward_compatible(self) -> None:
        """Preprocessor() without custom_tags works identically to before."""
        preprocessor = Preprocessor()

        braces = ("{%", "%}")
        html = "{% macro %}"
        instruction, itype = preprocessor.parse_instruction_tag(
            braces, html, 0, len(html) - 2,
        )
        assert itype == InstructionType.VALUE

    def test_expected_closing_instructions_updated(self) -> None:
        """Custom tags are added to expected_closing_instructions."""
        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})
        assert preprocessor.expected_closing_instructions["macro"] == "endmacro"
        # Built-in entries still present
        assert preprocessor.expected_closing_instructions["block"] == "endblock"

    def test_end_to_end_macro_indentation(self) -> None:
        """Full lint pipeline indents content inside {% macro %}...{% endmacro %}."""
        from cutesy.linter import HTMLLinter

        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})
        html = (
            "{% macro my_macro %}\n"
            "<div>\n"
            "</div>\n"
            "{% endmacro %}\n"
        )
        expected = (
            "{% macro my_macro %}\n"
            "\t<div>\n"
            "\t</div>\n"
            "{% endmacro %}\n"
        )
        linter = HTMLLinter(fix=True, preprocessor=preprocessor)
        result, errors = linter.lint(html)
        assert result == expected

    def test_dangling_custom_tag_raises(self) -> None:
        """Unclosed custom block tag raises StructuralError."""
        from cutesy.linter import HTMLLinter

        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})
        html = "{% macro my_macro %}\n<div></div>\n"
        linter = HTMLLinter(fix=False, preprocessor=preprocessor)
        with pytest.raises(StructuralError):
            linter.lint(html)

    def test_unmatched_end_tag_raises(self) -> None:
        """{% endmacro %} without opening {% macro %} raises StructuralError."""
        from cutesy.linter import HTMLLinter

        preprocessor = Preprocessor(custom_tags={"partial": [["macro", "endmacro"]]})
        html = "<div></div>\n{% endmacro %}\n"
        linter = HTMLLinter(fix=False, preprocessor=preprocessor)
        with pytest.raises(StructuralError):
            linter.lint(html)
