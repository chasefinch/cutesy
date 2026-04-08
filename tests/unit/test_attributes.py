"""Tests for the combined attributes processor."""

from cutesy.attribute_processors.attributes import AttributeProcessor

MAX_CHARS_PER_LINE = 80


class TestClassification:
    """Test attribute type classification and dispatch."""

    def test_unknown_attribute_left_alone(self) -> None:
        """Unknown attributes are returned unchanged."""
        processor = AttributeProcessor()
        result, errors = processor.process(
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
        assert errors == []

    def test_data_attribute_left_alone(self) -> None:
        """Data-* attributes are unknown and left alone."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="data-value",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  some   spaced  value  ",
        )
        assert result == "  some   spaced  value  "
        assert errors == []

    def test_uri_attribute_left_alone(self) -> None:
        """URI attributes like href are left alone."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="href",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="/path/to/page",
        )
        assert result == "/path/to/page"
        assert errors == []


class TestTokenAttributes:
    """Test token-list attribute processing (class, rel, etc.)."""

    def test_normalizes_whitespace(self) -> None:
        """Token attributes have whitespace normalized."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  foo   bar   baz  ",
        )
        assert result == "foo bar baz"
        assert errors == []

    def test_empty_token_attribute_returns_none(self) -> None:
        """Empty token attributes signal removal via None."""
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
            attr_body="",
        )
        assert result is None

    def test_whitespace_only_token_attribute_returns_none(self) -> None:
        """Token attributes with only whitespace signal removal."""
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
            attr_body="   \t  ",
        )
        assert result is None

    def test_rel_attribute_normalized(self) -> None:
        """Rel is a token attribute and gets normalized."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="rel",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="noopener   noreferrer",
        )
        assert result == "noopener noreferrer"
        assert errors == []

    def test_single_line_when_fits(self) -> None:
        """Tokens stay on one line when they fit."""
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
            attr_body="a b c d e",
        )
        assert result is not None
        assert result == "a b c d e"
        assert "\n" not in result

    def test_multiline_when_exceeds_max_items(self) -> None:
        """Tokens go multiline when exceeding max_items_per_line."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=3,
            bounding_character='"',
            preprocessor=None,
            attr_body="a b c d",
        )
        assert result is not None
        assert "\n" in result
        lines = result.split("\n")
        assert lines[0] == ""  # Empty first line
        assert lines[1] == "\t\ta"
        assert lines[2] == "\t\tb"
        assert lines[3] == "\t\tc"
        assert lines[4] == "\t\td"
        assert lines[5] == "\t"  # Base indentation

    def test_multiline_when_exceeds_line_length(self) -> None:
        """Tokens go multiline when exceeding line length."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=30,  # noqa: WPS432
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="very-long-class-a very-long-class-b",
        )
        assert result is not None
        assert "\n" in result

    def test_multiline_token_indentation(self) -> None:
        """Multiline tokens indented at indent_level + 1."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="  ",
            current_indentation_level=2,
            tab_width=2,
            line_length=20,  # noqa: WPS432
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="alpha bravo charlie delta echo foxtrot",
        )
        assert result is not None
        lines = result.split("\n")
        assert lines[0] == ""  # Empty first line
        # Each token at indent level 3 (2+1), 2-space indent = 6 spaces
        for line in lines[1:-1]:
            assert line.startswith("      ")
        # Last line at base indentation level 2 = 4 spaces
        assert lines[-1] == "    "

    def test_f16_on_token_attribute(self) -> None:
        """F16 fires on token attributes with raw bounding quotes."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="class",
            position=(1, 5),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body='foo "bar" baz',
        )
        assert len(errors) == 1
        assert errors[0].rule.code == "F16"
        assert result is not None
        assert "&quot;" in result

    def test_newlines_in_tokens_collapsed(self) -> None:
        """Newlines in token values are treated as whitespace."""
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
            attr_body="foo\n  bar\n  baz",
        )
        assert result == "foo bar baz"

    def test_sizes_attribute(self) -> None:
        """Sizes is a token attribute."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="sizes",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="(max-width: 600px) 480px,   800px",
        )
        assert result is not None
        assert "  " not in result


class TestCodeContentAttributes:
    """Test code-content attribute processing (on*, style)."""

    def test_onclick_whitespace_collapse(self) -> None:
        """On* attributes get whitespace collapse."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="onclick",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="doSomething();    return false;",
        )
        assert result == "doSomething(); return false;"
        assert errors == []

    def test_style_is_code_content(self) -> None:
        """Style attribute gets code-content processing."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="style",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="color: red;    margin: 0;",
        )
        assert result == "color: red; margin: 0;"
        assert errors == []

    def test_empty_style_returns_none(self) -> None:
        """Empty style attribute signals removal."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="style",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="   ",
        )
        assert result is None

    def test_multiline_code_reindent(self) -> None:
        """Multiline code content gets reindented."""
        processor = AttributeProcessor()
        attr_body = "\n  line1();\n  line2();\n"
        result, _ = processor.process(
            attr_name="onclick",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )
        assert result is not None
        assert "\n" in result
        lines = result.split("\n")
        # First line should be empty (content starts on next line)
        assert lines[0] == ""
        # Content lines should be at indentation level 2 (1+1)
        assert lines[1].startswith("\t\t")
        assert "line1();" in lines[1]

    def test_f16_on_code_content(self) -> None:
        """F16 fires on code content with raw bounding quotes."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="onclick",
            position=(2, 10),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body='alert("hi")',
        )
        assert len(errors) == 1
        assert errors[0].rule.code == "F16"
        assert result is not None
        assert "&quot;" in result

    def test_triple_newlines_collapsed(self) -> None:
        """Triple newlines in code content collapsed to double."""
        processor = AttributeProcessor()
        attr_body = "\nline1\n\n\nline2\n"
        result, _ = processor.process(
            attr_name="onclick",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )
        assert result is not None
        assert "\n\n\n" not in result
        assert "line1" in result
        assert "line2" in result

    def test_single_line_code_strips(self) -> None:
        """Single-line code with surrounding newlines is stripped."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="onclick",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="\n  doSomething()  \n",
        )
        assert result == "doSomething()"

    def test_code_preserves_string_whitespace(self) -> None:
        """Code content preserves whitespace inside strings."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="onclick",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character="'",
            preprocessor=None,
            attr_body='var x = "hello    world";  return x;',
        )
        assert result is not None
        assert '"hello    world"' in result
        assert "return x;" in result

    def test_onsubmit_is_code_content(self) -> None:
        """Any on* attribute is code content."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="onsubmit",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="validate();    return true;",
        )
        assert result == "validate(); return true;"

    def test_first_line_content_multiline(self) -> None:
        """Multiline code with content on first line."""
        processor = AttributeProcessor()
        attr_body = "  line1();\n  line2();\n  line3();"
        result, _ = processor.process(
            attr_name="onclick",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )
        assert result is not None
        lines = result.split("\n")
        # First line should have content (stripped of leading ws)
        assert lines[0] == "line1();"


class TestStripAttributes:
    """Test strip-safe attribute processing."""

    def test_numeric_attribute_stripped(self) -> None:
        """Numeric attributes get stripped."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="width",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  42  ",
        )
        assert result == "42"
        assert errors == []

    def test_enumerated_attribute_stripped(self) -> None:
        """Enumerated attributes get stripped."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="type",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  text  ",
        )
        assert result == "text"
        assert errors == []

    def test_presence_attribute_stripped(self) -> None:
        """Presence attributes get stripped."""
        processor = AttributeProcessor()
        result, errors = processor.process(
            attr_name="disabled",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  disabled  ",
        )
        assert result == "disabled"
        assert errors == []

    def test_f16_on_strip_attributes(self) -> None:
        """F16 fires on strip attributes with raw bounding quotes."""
        processor = AttributeProcessor()
        _, errors = processor.process(
            attr_name="type",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body='"text"',
        )
        assert len(errors) == 1
        assert errors[0].rule.code == "F16"


class TestPluginExtension:
    """Test plugin extension mechanism."""

    def test_register_code_content_by_name(self) -> None:
        """Plugins can register attribute names as code content."""
        AttributeProcessor.register_code_content_processing(names=["x-data"])
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="x-data",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="foo    bar",
        )
        assert result == "foo bar"
        # Clean up class-level state
        AttributeProcessor._extra_code_names.discard("x-data")  # noqa: SLF001

    def test_register_code_content_by_prefix(self) -> None:
        """Plugins can register attribute prefixes as code content."""
        AttributeProcessor.register_code_content_processing(prefixes=["x-"])
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
            attr_body="count    = 0",
        )
        assert result == "count = 0"
        AttributeProcessor._extra_code_prefixes.discard("x-")  # noqa: SLF001

    def test_unregistered_prefix_left_alone(self) -> None:
        """Unregistered prefixes are left alone."""
        processor = AttributeProcessor()
        result, _ = processor.process(
            attr_name="x-unknown",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            line_length=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="some    value",
        )
        assert result == "some    value"
