"""Tests for class ordering types functionality."""

from cutesy.attribute_processors.class_ordering.types import (
    DYNAMIC_LIST_ITEM_SENTINEL,
    BaseClassOrderingAttributeProcessor,
    expand_class_names,
)

# Constants to avoid magic numbers
EXPECTED_LIST_LENGTH = 3
EXPECTED_MAX_LENGTH = 72
MAX_CHARS_PER_LINE = 80


class MockClassOrderingProcessor(BaseClassOrderingAttributeProcessor):
    """Mock implementation for testing base functionality."""

    def sort(
        self,
        class_names: list[str],
        *,
        grouped: bool = False,
    ) -> list[str] | list[list[str]]:
        """Sort class names for testing purposes."""
        if grouped:
            return [sorted(class_names)]
        return sorted(class_names)


class MockPreprocessor:
    """Mock implementation for testing base functionality."""

    delimiters = ("«", "»")


class TestConstants:
    """Test module constants."""

    def test_dynamic_list_item_sentinel_is_string(self) -> None:
        """Test DYNAMIC_LIST_ITEM_SENTINEL is a string constant."""
        assert isinstance(DYNAMIC_LIST_ITEM_SENTINEL, str)
        assert len(DYNAMIC_LIST_ITEM_SENTINEL) > 0
        assert "SENTINEL" in DYNAMIC_LIST_ITEM_SENTINEL


class TestExpandClassNames:
    """Test expand_class_names helper function."""

    def test_expand_simple_class_names(self) -> None:
        """Test expanding simple class names without delimiters."""
        class_names = ["btn", "btn-lg", "shadow"]
        result = expand_class_names(class_names, "{", "}")

        assert result == ["btn", "btn-lg", "shadow"]

    def test_expand_class_names_with_delimiters(self) -> None:
        """Test expanding class names with template delimiters."""
        class_names = ["{% if condition %}btn-lg{% else %}btn-sm{% endif %}", "shadow"]
        result = expand_class_names(class_names, "{", "}")

        expected = [
            "{% if condition %}",
            "btn-lg",
            "{% else %}",
            "btn-sm",
            "{% endif %}",
            "shadow",
        ]
        assert result == expected

    def test_expand_class_names_multiple_delimited_sections(self) -> None:
        """Test expanding class names with multiple delimited sections."""
        class_names = ["{{ class1 }} middle {{ class2 }}", "static"]
        result = expand_class_names(class_names, "{{", "}}")

        expected = ["{{ class1 }}", "middle", "{{ class2 }}", "static"]
        assert result == expected

    def test_expand_class_names_no_delimiters(self) -> None:
        """Test expanding class names when no delimiters are found."""
        class_names = ["btn-primary", "shadow-lg"]
        result = expand_class_names(class_names, "{%", "%}")

        assert result == ["btn-primary", "shadow-lg"]

    def test_expand_class_names_keep_empty_false(self) -> None:
        """Test expanding class names with keep_empty=False (default)."""
        class_names = ["{% if test %}{% endif %}btn"]
        result = expand_class_names(class_names, "{", "}", keep_empty=False)

        # Empty parts should be filtered out
        expected = ["{% if test %}", "{% endif %}", "btn"]
        assert result == expected

    def test_expand_class_names_keep_empty_true(self) -> None:
        """Test expanding class names with keep_empty=True."""
        class_names = ["{% if test %}{% endif %}btn"]
        result = expand_class_names(class_names, "{", "}", keep_empty=True)

        # Empty parts should be kept
        expected = ["{% if test %}", "", "{% endif %}", "btn"]
        assert result == expected

    def test_expand_class_names_unmatched_delimiters(self) -> None:
        """Test expanding class names with unmatched delimiters."""
        class_names = ["{% if test btn-lg", "shadow"]
        result = expand_class_names(class_names, "{%", "%}")

        # Unmatched delimiters should leave string as-is
        assert result == ["{% if test btn-lg", "shadow"]

    def test_expand_class_names_empty_input(self) -> None:
        """Test expanding empty class names list."""
        result = expand_class_names([], "{", "}")
        assert result == []

    def test_expand_class_names_complex_template(self) -> None:
        """Test expanding complex template expressions."""
        class_names = [
            "btn {% if large %}btn-lg{% elif small %}btn-sm{% else %}btn-md{% endif %} primary",
        ]
        result = expand_class_names(class_names, "{", "}")

        expected = [
            "btn",
            "{% if large %}",
            "btn-lg",
            "{% elif small %}",
            "btn-sm",
            "{% else %}",
            "btn-md",
            "{% endif %}",
            "primary",
        ]
        assert result == expected


class TestBaseClassOrderingAttributeProcessor:
    """Test BaseClassOrderingAttributeProcessor functionality."""

    def test_processor_initialization(self) -> None:
        """Test processor can be instantiated."""
        processor = MockClassOrderingProcessor()
        assert hasattr(processor, "sort")
        assert hasattr(processor, "process")

    def test_process_non_class_attribute(self) -> None:
        """Test processing non-class attribute returns unchanged."""
        processor = MockClassOrderingProcessor()

        result, errors = processor.process(
            attr_name="id",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="my-id",
        )

        assert result == "my-id"
        assert errors == []

    def test_process_class_attribute_simple(self) -> None:
        """Test processing simple class attribute."""
        processor = MockClassOrderingProcessor()

        result, errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="btn shadow primary",
        )

        # Classes should be sorted
        assert "btn" in result
        assert "shadow" in result
        assert "primary" in result
        assert errors == []

    def test_process_class_attribute_with_whitespace(self) -> None:
        """Test processing class attribute with extra whitespace."""
        processor = MockClassOrderingProcessor()

        result, errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="  btn   shadow   primary  ",
        )

        # Should handle extra whitespace
        assert isinstance(result, str)
        assert errors == []

    def test_process_empty_class_attribute(self) -> None:
        """Test processing empty class attribute."""
        processor = MockClassOrderingProcessor()

        result, errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="",
        )

        assert result == ""
        assert errors == []

    def test_process_sets_internal_state(self) -> None:
        """Test that process method sets internal processor state."""
        processor = MockClassOrderingProcessor()

        processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="    ",
            current_indentation_level=2,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=3,
            bounding_character='"',
            preprocessor=None,
            attr_body="btn primary",
        )

        # Check internal state was set
        assert processor.indentation == "    "
        assert processor.max_items_per_line == EXPECTED_LIST_LENGTH
        assert hasattr(processor, "stashed_class_names")
        assert isinstance(processor.stashed_class_names, list)

    def test_process_calculates_max_length(self) -> None:
        """Test that process method calculates max length correctly."""
        processor = MockClassOrderingProcessor()

        processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="btn",
        )

        # max_length = max_chars_per_line - ((current_indentation_level + 1) * tab_width)
        # max_length = 80 - ((1 + 1) * 4) = 80 - 8 = 72
        expected_max_length = MAX_CHARS_PER_LINE - ((1 + 1) * 4)
        assert processor.max_length == expected_max_length

    def test_sort_method_is_abstract(self) -> None:
        """Test that sort method must be implemented by subclasses."""
        # This is tested by the fact that MockClassOrderingProcessor
        # provides an implementation and can be instantiated
        processor = MockClassOrderingProcessor()
        result = processor.sort(["c", "a", "b"])
        assert result == ["a", "b", "c"]

    def test_sort_method_grouped_option(self) -> None:
        """Test sort method with grouped option."""
        processor = MockClassOrderingProcessor()
        result = processor.sort(["c", "a", "b"], grouped=True)
        assert result == [["a", "b", "c"]]

    def test_process_with_mock_preprocessor(self) -> None:
        """Test processing with a mock preprocessor."""
        processor = MockClassOrderingProcessor()

        result, errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="  ",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=MockPreprocessor(),
            attr_body="btn primary",
        )

        # Should process without error
        assert isinstance(result, str)
        assert isinstance(errors, list)
        assert processor.preprocessor is not None
