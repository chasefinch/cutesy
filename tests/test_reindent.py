"""Tests for reindent attribute processor."""

from cutesy.attribute_processors.reindent import AttributeProcessor

MAX_CHARS_PER_LINE = 80


class TestAttributeProcessor:
    """Test AttributeProcessor class."""

    def test_process_single_line_attribute(self) -> None:
        """Test processing single line attribute returns unchanged."""
        processor = AttributeProcessor()

        result, errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="hello world",
        )

        assert result == "hello world"
        assert errors == []

    def test_process_multiline_attribute_basic(self) -> None:
        """Test processing basic multiline attribute."""
        processor = AttributeProcessor()

        attr_body = """first line
  second line
    third line"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        expected_lines = [
            "first line",
            "    second line",  # 1 base + 1 relative = 2 levels * 2 spaces
            "      third line",  # 1 base + 2 relative = 3 levels * 2 spaces
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_strips_leading_whitespace(self) -> None:
        """Test processing strips leading whitespace before first newline."""
        processor = AttributeProcessor()

        attr_body = "  first line\n  second line"

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="    ",  # 4 spaces
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        expected_lines = [
            "first line",
            "        second line",  # 1 base + 0 relative = 1 level * 4 spaces + 4 for content
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_with_tab_indentation(self) -> None:
        """Test processing with tab-based indentation."""
        processor = AttributeProcessor()

        attr_body = """first line
\tsecond line
\t\tthird line"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,  # Tabs count as 4 spaces for calculation
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        expected_lines = [
            "first line",
            "\t\tsecond line",  # 1 base + 1 relative = 2 levels
            "\t\t\tthird line",  # 1 base + 2 relative = 3 levels
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_mixed_space_and_tab_indentation(self) -> None:
        """Test processing with mixed space and tab indentation."""
        processor = AttributeProcessor()

        # Mix of spaces (2) and tab (counts as 1 indent unit)
        attr_body = """first line
  second line
\tthird line"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # Both second and third line should be at same relative level
        expected_lines = [
            "first line",
            "    second line",  # 1 base + 1 relative = 2 levels * 2 spaces
            "    third line",  # 1 base + 1 relative = 2 levels * 2 spaces
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_empty_lines_preserved(self) -> None:
        """Test processing preserves empty lines."""
        processor = AttributeProcessor()

        attr_body = """first line
  second line

  fourth line"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        expected_lines = [
            "first line",
            "    second line",
            "",  # Empty line preserved
            "    fourth line",
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_determines_minimum_indentation(self) -> None:
        """Test processing correctly determines minimum indentation level."""
        processor = AttributeProcessor()

        attr_body = """first line
    heavily indented
  less indented
      most indented"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=0,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # Min indentation is 1 level (less indented line), so relative:
        # heavily = 2-1 = 1 relative, most = 3-1 = 2 relative
        expected_lines = [
            "first line",
            "    heavily indented",  # 0 base + 1 + 1 relative = 2 levels
            "  less indented",  # 0 base + 1 + 0 relative = 1 level
            "      most indented",  # 0 base + 1 + 2 relative = 3 levels
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_only_last_line_has_content(self) -> None:
        """Test processing when only the last line has meaningful content."""
        processor = AttributeProcessor()

        attr_body = """first line


      last line"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # When only the last line has content, use its offset as minimum
        expected_lines = [
            "first line",
            "",
            "",
            "    last line",  # 1 base + 0 relative (since it's the min) = 1 level
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_last_empty_line_gets_proper_indentation(self) -> None:
        """Test processing sets proper indentation for last empty line."""
        processor = AttributeProcessor()

        attr_body = """first line
  second line
"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=2,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        expected_lines = [
            "first line",
            "      second line",  # 2 base + 1 + 0 relative = 3 levels
            "    ",  # Last empty line gets base indentation (2 levels)
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_empty_lines_between_first_and_last(self) -> None:
        """Test processing with no content lines between first and last."""
        processor = AttributeProcessor()

        attr_body = """first line


"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # Should use the last line's indentation (which is 0 in this case)
        expected_lines = [
            "first line",
            "",
            "",
            "  ",  # Last line gets current_indentation_level (1 * 2 spaces)
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_large_tab_width(self) -> None:
        """Test processing with larger tab width."""
        processor = AttributeProcessor()

        attr_body = """first line
        second line
                third line"""

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="    ",  # 4 spaces
            current_indentation_level=1,
            tab_width=8,  # Large tab width
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # With tab_width=8: second line = 1 indent, third line = 2 indents
        # Min is 1, so relative: second = 0, third = 1
        expected_lines = [
            "first line",
            "        second line",  # 1 base + 1 + 0 relative = 2 levels * 4 spaces
            "            third line",  # 1 base + 1 + 1 relative = 3 levels * 4 spaces
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []

    def test_process_single_newline_only(self) -> None:
        """Test processing attribute that is just a single newline.

        This tests the case where the attribute contains only a single newline
        character.
        """
        processor = AttributeProcessor()

        attr_body = "first\n"

        result, errors = processor.process(
            attr_name="data-content",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        expected_lines = [
            "first",
            "  ",  # Empty last line gets current indentation level
        ]
        expected = "\n".join(expected_lines)

        assert result == expected
        assert errors == []
