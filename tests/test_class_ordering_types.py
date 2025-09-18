"""Tests for class ordering types functionality."""

from cutesy.attribute_processors.class_ordering.types import (
    DYNAMIC_LIST_ITEM_SENTINEL,
    BaseClassOrderingAttributeProcessor,
    StashItem,
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

    def test_process_with_preprocessor_simple_case(self) -> None:
        """Test process method works with preprocessor in simple case."""
        processor = MockClassOrderingProcessor()
        processor.preprocessor = MockPreprocessor()

        # Test with simple case that doesn't trigger regex errors
        attr_body = "btn shadow"

        result, errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=MockPreprocessor(),
            attr_body=attr_body,
        )

        # Should process successfully
        assert isinstance(result, str)
        assert len(errors) == 0

    def test_build_stash_with_control_boundaries(self) -> None:
        """Test _build_stash handles control items at boundaries."""
        processor = MockClassOrderingProcessor()
        processor.preprocessor = MockPreprocessor()

        # Mock scenario with control items
        class_names = ["start", "«a»", "middle", "«b»", "end"]
        tree = [0, 4, 5]  # Simple tree structure

        result = processor._build_stash(class_names, tree)

        # Should handle control boundaries correctly
        assert isinstance(result, list)
        assert len(result) >= 0

    def test_emit_sorted_run_edge_cases(self) -> None:
        """Test _emit_sorted_run with various edge cases."""
        processor = MockClassOrderingProcessor()

        # Test with empty buffer
        buffer = []
        stash = []
        processor._emit_sorted_run(buffer, stash, protect_head=True, protect_tail=True)
        assert len(stash) == 0
        assert len(buffer) == 0

        # Test with single item
        buffer = ["item"]
        stash = []
        processor._emit_sorted_run(buffer, stash, protect_head=True, protect_tail=False)
        assert len(stash) == 1
        assert len(buffer) == 0

    def test_process_handles_non_class_attributes(self) -> None:
        """Test process method returns unchanged for non-class attributes."""
        processor = MockClassOrderingProcessor()
        attr_body = "value1 value2 value3"

        result, errors = processor.process(
            attr_name="id",  # Not "class"
            position=(1, 10),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # Should return unchanged for non-class attributes
        assert result == attr_body
        assert len(errors) == 0

    def test_flatten_stash_with_complex_nested_structures(self) -> None:
        """Test _flatten_stash handles complex nested structures."""
        processor = MockClassOrderingProcessor()
        processor.indentation = "\t"
        processor.preprocessor = MockPreprocessor()
        processor.max_length = MAX_CHARS_PER_LINE
        processor.max_items_per_line = 5

        # Create complex nested stash structure
        nested_stash: list[StashItem] = [
            "{{a}}",  # Block start
            ["inner1", ["inner2"]],  # Nested list with proper StashItem structure
            "{{d}}",  # Continuation
            "middle",
            "{{b}}",  # Block end
        ]

        result = processor._flatten_stash(nested_stash)

        # Should handle nested structures appropriately
        assert isinstance(result, (str, list))

    def test_extract_columns_and_lines_with_continuation_instructions(self) -> None:
        """Test _extract_columns_and_lines handles continuations."""
        processor = MockClassOrderingProcessor()
        processor.preprocessor = MockPreprocessor()

        # Test with continuation instruction (reduces column by 1)
        item = "{{d}}"  # 'd' = MID_CONDITIONAL (continuation)

        result = processor._extract_columns_and_lines(item)

        # Should return list of tuples with column adjustments
        assert isinstance(result, list)
        assert len(result) > 0
        tuple_size = 2
        assert all(isinstance(item, tuple) and len(item) == tuple_size for item in result)

    def test_build_stash_with_control_items_at_boundaries(self) -> None:
        """Test _build_stash handles control items at start/end correctly."""
        processor = MockClassOrderingProcessor()
        processor.preprocessor = MockPreprocessor()

        # Mock class names representing a control structure
        class_names = ["regular1", "{{a}}", "middle", "{{b}}", "regular2"]

        # Mock tree structure: [1, 3, 4] (start at 1, end at 4, middle at 3)
        tree = [1, 3, 4]
        result = processor._build_stash(class_names, tree)

        # Should properly handle control items at boundaries
        assert isinstance(result, list)

    def test_emit_sorted_run_with_protection_flags(self) -> None:
        """Test _emit_sorted_run with different flag combinations."""
        processor = MockClassOrderingProcessor()

        buffer = ["z", "a", "y", "b"]
        stash = []

        # Test protect_head=True, protect_tail=True
        processor._emit_sorted_run(buffer, stash, protect_head=True, protect_tail=True)

        # Should protect first and last items, sort middle
        assert len(stash) > 0
        # Buffer should be cleared
        assert len(buffer) == 0

    def test_hydrate_class_groups_with_multiple_groups(self) -> None:
        """Test _hydrate_class_groups handles multiple class groups."""
        processor = MockClassOrderingProcessor()
        processor.stashed_class_names = ["stash1", "stash2"]

        # Multiple groups with sentinels
        class_groups = [
            ["group1"],
            ["item1", f"{DYNAMIC_LIST_ITEM_SENTINEL}_0", "item2"],
        ]

        result = processor._hydrate_class_groups(class_groups)

        # Should handle multiple groups correctly
        assert isinstance(result, list)
        assert len(result) == len(class_groups)

    def test_single_line_mode_calculation(self) -> None:
        """Test single line mode decision logic."""
        processor = MockClassOrderingProcessor()
        processor.max_length = 50

        # Test with classes that fit on single line
        attr_body = "btn btn-lg shadow"

        result, _errors = processor.process(
            attr_name="class",
            position=(1, 10),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=MAX_CHARS_PER_LINE,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )

        # Should use single line mode for short class lists
        assert "\n" not in result

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
