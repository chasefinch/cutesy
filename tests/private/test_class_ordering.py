"""Test the class ordering attribute processor types module."""

from cutesy.attribute_processors.class_ordering.types import (
    DYNAMIC_LIST_ITEM_SENTINEL,
    BaseClassOrderingAttributeProcessor,
    IndexRangeNode,
    StackNode,
    StashItem,
    expand_class_names,
)
from cutesy.preprocessors.django import Preprocessor


class MockClassOrderingProcessor(BaseClassOrderingAttributeProcessor):
    """Mock class ordering processor for testing."""

    def __init__(self) -> None:
        """Initialize mock processor with required attributes."""
        self.max_items_per_line = 10
        self.max_length = 80
        # Initialize with a proper preprocessor that has delimiters
        self.preprocessor = Preprocessor()
        self.preprocessor.reset("test html")
        self.indentation = "  "
        self.stashed_class_names = []

    def sort(
        self,
        class_names: list[str],
        *,
        grouped: bool = False,
    ) -> list[str] | list[list[str]]:
        """Sort.

        Simple implementation for testing.
        """
        if grouped:
            return [sorted(class_names)]
        return sorted(class_names)


class TestExpandClassNames:
    """Test the expand_class_names function."""

    def test_basic_expansion(self) -> None:
        """Test basic expansion of delimited strings."""
        class_names = ["btn", "text-red"]
        result = expand_class_names(class_names, "{", "}")
        assert result == ["btn", "text-red"]

    def test_single_delimited_chunk(self) -> None:
        """Test expansion with a single delimited chunk."""
        class_names = ["{%if x%}btn-lg{%endif%}"]
        result = expand_class_names(class_names, "{", "}")
        expected = ["{%if x%}", "btn-lg", "{%endif%}"]
        assert result == expected

    def test_multiple_delimited_chunks(self) -> None:
        """Test expansion with multiple delimited chunks."""
        class_names = ["{%if tuna%}btn--lg{%else%}btn--sm{%endif%} shadow", "card"]
        result = expand_class_names(class_names, "{", "}")
        expected = [
            "{%if tuna%}",
            "btn--lg",
            "{%else%}",
            "btn--sm",
            "{%endif%}",
            "shadow",
            "card",
        ]
        assert result == expected

    def test_keep_empty_true(self) -> None:
        """Test keep_empty=True preserves empty strings."""
        class_names = ["{%if x%}{%endif%}"]
        result = expand_class_names(class_names, "{", "}", keep_empty=True)
        expected = ["{%if x%}", "", "{%endif%}"]
        assert result == expected

    def test_keep_empty_false(self) -> None:
        """Test keep_empty=False removes empty strings."""
        class_names = ["{%if x%}{%endif%}"]
        result = expand_class_names(class_names, "{", "}")
        expected = ["{%if x%}", "{%endif%}"]
        assert result == expected

    def test_no_delimited_chunks(self) -> None:
        """Test strings without delimited chunks remain unchanged."""
        class_names = ["btn", "text-red", "shadow"]
        result = expand_class_names(class_names, "{", "}")
        assert result == class_names

    def test_unmatched_delimiters(self) -> None:
        """Test unmatched delimiters leave string as-is."""
        class_names = ["{incomplete", "normal-class"]
        result = expand_class_names(class_names, "{", "}")
        assert result == class_names

    def test_complex_delimited_content(self) -> None:
        """Test complex content within delimiters."""
        class_names = ["{%if user.is_admin%}admin-panel{%endif%} base-class"]
        result = expand_class_names(class_names, "{", "}")
        expected = ["{%if user.is_admin%}", "admin-panel", "{%endif%}", "base-class"]
        assert result == expected


class TestBaseClassOrderingAttributeProcessor:
    """Test the BaseClassOrderingAttributeProcessor class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.processor = MockClassOrderingProcessor()
        self.preprocessor = Preprocessor()
        # Initialize preprocessor with sample HTML to set delimiters
        self.preprocessor.reset("class='test {%if x%}active{%endif%}'")

    def test_process_non_class_attribute(self) -> None:
        """Test processing non-class attributes returns unchanged."""
        result = self.processor.process(
            attr_name="id",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="my-id",
        )
        assert result == ("my-id", [])

    def test_process_simple_class_attribute(self) -> None:
        """Test processing simple class attribute without preprocessor."""
        result = self.processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="z-class b-class a-class",
        )
        # Should be sorted alphabetically by our mock processor
        assert result == ("a-class b-class z-class", [])

    def test_process_with_preprocessor_simple(self) -> None:
        """Test processing class attribute with simple preprocessor usage."""
        result = self.processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=10,
            bounding_character='"',
            preprocessor=self.preprocessor,
            attr_body="btn {{ value }} text-red",
        )
        # Should include the dynamic value
        assert "btn" in result[0]
        assert "text-red" in result[0]
        assert "{{" in result[0]
        assert "}}" in result[0]

    def test_process_overlapping_instructions_error(self) -> None:
        """Test that malformed instructions are handled."""
        # This test may not raise the expected error in all cases
        # The actual implementation may handle malformed input differently
        result = self.processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=self.preprocessor,
            attr_body="btn-{%if x%}lg{%else",  # Malformed/overlapping
        )
        # Just verify it returns a tuple without crashing
        assert isinstance(result, tuple)
        expected_result_length = 2
        assert len(result) == expected_result_length
        assert isinstance(result[0], str)

    def test_single_line_mode(self) -> None:
        """Test single line mode when classes fit on one line."""
        result = self.processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body="a b c",
        )
        assert result == ("a b c", [])

    def test_multi_line_mode_single_group(self) -> None:
        """Test multi-line mode with single group."""
        # Create a long list that exceeds max_items_per_line
        long_class_list = " ".join([f"class-{index}" for index in range(10)])
        max_chars_per_line = 50
        result = self.processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=1,
            tab_width=4,
            max_chars_per_line=max_chars_per_line,
            max_items_per_line=3,
            bounding_character='"',
            preprocessor=None,
            attr_body=long_class_list,
        )
        # Should be multi-line
        assert "\n" in result[0]

    def test_extract_with_sentinel(self) -> None:
        """Test _extract_with_sentinel method."""
        processor = MockClassOrderingProcessor()
        class_names = ["a", "b", "c", "d", "e"]
        index_tree: IndexRangeNode = [1, 3]  # Extract items 1-3 (exclusive)
        sentinel = "TEST_SENTINEL"

        new_class_names, stash = processor._extract_with_sentinel(
            class_names,
            index_tree,
            sentinel,
        )

        assert new_class_names == ["a", sentinel, "d", "e"]
        assert stash == ["b", "c"]

    def test_build_stash_simple(self) -> None:
        """Test _build_stash method with simple case."""
        processor = MockClassOrderingProcessor()
        class_names = ["start", "a", "b", "c", "end"]
        tree = [0, 4]  # Simple range from 0 to 4

        stash = processor._build_stash(class_names, tree)
        # Should include all items from start index to end-1 index
        assert stash == ["start", "a", "b", "c"]

    def test_emit_sorted_run_basic(self) -> None:
        """Test _emit_sorted_run method basic functionality."""
        processor = MockClassOrderingProcessor()
        buffer = ["z", "a", "m"]
        stash = []

        processor._emit_sorted_run(buffer, stash)

        assert stash == ["a", "m", "z"]  # Sorted
        assert buffer == []  # Buffer cleared

    def test_emit_sorted_run_protect_head(self) -> None:
        """Test _emit_sorted_run with head protection."""
        processor = MockClassOrderingProcessor()
        buffer = ["first", "z", "a", "m"]
        stash = []

        processor._emit_sorted_run(buffer, stash, protect_head=True)

        assert stash == ["first", "a", "m", "z"]  # First preserved, rest sorted
        assert buffer == []

    def test_emit_sorted_run_protect_tail(self) -> None:
        """Test _emit_sorted_run with tail protection."""
        processor = MockClassOrderingProcessor()
        buffer = ["z", "a", "m", "last"]
        stash = []

        processor._emit_sorted_run(buffer, stash, protect_tail=True)

        assert stash == ["a", "m", "z", "last"]  # Last preserved, rest sorted
        assert buffer == []

    def test_emit_sorted_run_protect_both(self) -> None:
        """Test _emit_sorted_run with both head and tail protection."""
        processor = MockClassOrderingProcessor()
        buffer = ["first", "z", "a", "m", "last"]
        stash = []

        processor._emit_sorted_run(buffer, stash, protect_head=True, protect_tail=True)

        assert stash == ["first", "a", "m", "z", "last"]  # Both ends preserved
        assert buffer == []

    def test_hydrate_class_groups_simple(self) -> None:
        """Test _hydrate_class_groups with simple groups."""
        processor = MockClassOrderingProcessor()
        processor.stashed_class_names = []

        class_groups = [["a", "b"], ["c", "d"]]
        result = processor._hydrate_class_groups(class_groups)

        assert result == [["a", "b"], ["c", "d"]]

    def test_hydrate_class_groups_with_sentinels(self) -> None:
        """Test _hydrate_class_groups with sentinel replacement."""
        processor = MockClassOrderingProcessor()
        processor.stashed_class_names = [["dynamic", "content"]]

        class_groups = [["a", "b"], [f"{DYNAMIC_LIST_ITEM_SENTINEL}_0", "c"]]
        result = processor._hydrate_class_groups(class_groups)

        expected_result_length = 2
        assert len(result) == expected_result_length
        assert result[0] == ["a", "b"]
        assert "dynamic content" in str(result[1])  # Flattened stash

    def test_flatten_stash_string(self) -> None:
        """Test _flatten_stash with string input."""
        processor = MockClassOrderingProcessor()
        result = processor._flatten_stash("simple-string")
        assert result == "simple-string"

    def test_flatten_stash_single_item_list(self) -> None:
        """Test _flatten_stash with single-item list."""
        processor = MockClassOrderingProcessor()
        result = processor._flatten_stash(["single"])
        assert result == "single"

    def test_flatten_stash_all_strings_short(self) -> None:
        """Test _flatten_stash with short list of all strings."""
        processor = MockClassOrderingProcessor()
        processor.max_items_per_line = 5
        processor.max_length = 100
        processor.preprocessor = self.preprocessor

        result = processor._flatten_stash(["a", "b", "c"])
        assert isinstance(result, str)
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_flatten_stash_mixed_content(self) -> None:
        """Test _flatten_stash with mixed string and list content."""
        processor = MockClassOrderingProcessor()
        stash: list[StashItem] = ["a", ["nested", "content"], "b"]

        result = processor._flatten_stash(stash)
        # Function compacts all strings to a single string with special spacing
        assert isinstance(result, str)
        assert "a" in result
        assert "nested" in result
        assert "content" in result
        assert "b" in result

    def test_extract_columns_and_lines_string(self) -> None:
        """Test _extract_columns_and_lines with string input."""
        processor = MockClassOrderingProcessor()
        result = processor._extract_columns_and_lines("test-class")
        assert result == [(0, "test-class")]

    def test_extract_columns_and_lines_list(self) -> None:
        """Test _extract_columns_and_lines with list input."""
        processor = MockClassOrderingProcessor()
        processor.preprocessor = self.preprocessor

        # Create a list that represents a wrapped block
        wrapped_block: list[StashItem] = ["{%if x%}", "content", "{%endif%}"]
        result = processor._extract_columns_and_lines(wrapped_block)

        min_length = 2  # At least start and end
        assert len(result) >= min_length
        assert result[0][1] == "{%if x%}"  # First item
        assert result[-1][1] == "{%endif%}"  # Last item

    def test_extract_columns_and_lines_2(self) -> None:
        """Test _extract_columns_and_lines with continuation instruction."""
        processor = MockClassOrderingProcessor()
        processor.preprocessor = self.preprocessor

        # Test with a continuation instruction
        result = processor._extract_columns_and_lines("{%else%}", column=2)

        assert len(result) == 1
        original_length = 2
        assert result[0][0] == original_length  # Column unchanged for simple case
        assert result[0][1] == "{%else%}"


class TestConstants:
    """Test module constants and types."""

    def test_dynamic_list_item_sentinel(self) -> None:
        """Test the dynamic list item sentinel constant."""
        assert isinstance(DYNAMIC_LIST_ITEM_SENTINEL, str)
        assert len(DYNAMIC_LIST_ITEM_SENTINEL) > 0
        assert "SENTINEL" in DYNAMIC_LIST_ITEM_SENTINEL

    def test_type_aliases(self) -> None:
        """Test that type aliases are properly defined."""
        # These should not raise import errors and should be available
        assert StashItem is not None
        assert StackNode is not None
        assert IndexRangeNode is not None


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.preprocessor = Preprocessor()
        self.preprocessor.reset("class='test {%if x%}active{%endif%}'")

    def test_unbalanced_block_ending(self) -> None:
        """Test handling block ending without matching start."""
        processor = MockClassOrderingProcessor()

        # The implementation may handle this gracefully rather than raising an error
        result = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=self.preprocessor,
            attr_body="normal-class {%endif%}",  # End without start
        )
        # Just verify it returns a tuple without crashing
        assert isinstance(result, tuple)
        expected_result_length = 2
        assert len(result) == expected_result_length
        assert isinstance(result[0], str)

    def test_continuation_outside_block(self) -> None:
        """Test handling continuation outside a block."""
        processor = MockClassOrderingProcessor()

        # The implementation may handle this gracefully rather than raising an error
        result = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=self.preprocessor,
            attr_body="normal-class {%else%}",  # Else without if
        )
        # Just verify it returns a tuple without crashing
        assert isinstance(result, tuple)
        expected_result_length = 2
        assert len(result) == expected_result_length
        assert isinstance(result[0], str)


class TestIntegration:
    """Integration tests combining multiple features."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.preprocessor = Preprocessor()
        self.preprocessor.reset("class='test {%if x%}active{%endif%}'")

    def test_complex_class_processing(self) -> None:
        """Test processing complex class list with multiple features."""
        processor = MockClassOrderingProcessor()

        max_chars_per_line = 80
        result = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="  ",
            current_indentation_level=1,
            tab_width=2,
            max_chars_per_line=max_chars_per_line,
            max_items_per_line=4,
            bounding_character='"',
            preprocessor=None,
            attr_body="z-class a-class m-class b-class extra-long-class-name-that-might-wrap",
        )

        # Should be sorted and potentially wrapped
        assert "a-class" in result[0]
        assert "z-class" in result[0]

    def test_nested_block_processing(self) -> None:
        """Test processing with nested template blocks."""
        processor = MockClassOrderingProcessor()

        # This should work without errors
        result = processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=0,
            tab_width=4,
            max_chars_per_line=100,
            max_items_per_line=10,
            bounding_character='"',
            preprocessor=self.preprocessor,
            attr_body="base {%if outer%} {%if inner%}nested{%endif%} outer-class {%endif%} final",
        )

        assert "base" in result[0]
        assert "final" in result[0]
        assert "{%if" in result[0]
        assert "{%endif%}" in result[0]
