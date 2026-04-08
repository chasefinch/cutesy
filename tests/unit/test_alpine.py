"""Tests for the Alpine.js attribute processor."""

from cutesy.attribute_processors.alpine import AttributeProcessor

MAX_CHARS_PER_LINE = 80


class TestAlpineCodeContent:
    """Alpine directives are processed as code content."""

    def test_x_data_whitespace_collapse(self) -> None:
        """X-data gets whitespace collapse."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="x-data",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character="'",
            preprocessor=None,
            attr_body="{  open:    false  }",
        )
        assert result == "{ open: false }"
        assert errors == []

    def test_x_show_processed(self) -> None:
        """X-show gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="x-show",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  open  ",
        )
        assert result == "open"

    def test_x_on_click_processed(self) -> None:
        """X-on:click gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="x-on:click",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="open   =   !open",
        )
        assert result == "open = !open"

    def test_at_click_shorthand(self) -> None:
        """@click shorthand gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="@click",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="open   =   true",
        )
        assert result == "open = true"

    def test_colon_class_shorthand(self) -> None:
        """:class shorthand gets code-content processing."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name=":class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="open   &&   isActive",
        )
        assert result == "open && isActive"

    def test_x_init_multiline_reindent(self) -> None:
        """Multiline x-init gets reindented."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="x-init",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="\nconsole.log(1)\nconsole.log(2)\n",
        )
        assert result is not None
        assert "\n" in result
        lines = result.split("\n")
        assert "console.log(1)" in lines[1]


class TestAlpinePassthrough:
    """Non-Alpine attributes pass through unchanged."""

    def test_class_passes_through(self) -> None:
        """Class is not Alpine's domain — passes through for base."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  foo   bar  ",
        )
        assert result == "  foo   bar  "

    def test_unknown_attr_left_alone(self) -> None:
        """Non-Alpine attributes pass through unchanged."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="title",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="Hello   world",
        )
        assert result == "Hello   world"
