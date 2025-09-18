"""Test the collections utilities."""

from cutesy.utilities.collections import collapse


class TestCollapse:
    """Test the collapse function."""

    def test_collapse_empty_iterable(self) -> None:
        """Test collapse with empty iterable."""
        result = list(collapse([]))
        assert result == []

    def test_collapse_flat_list(self) -> None:
        """Test collapse with already flat list."""
        result = list(collapse([1, 2, 3]))
        assert result == [1, 2, 3]

    def test_collapse_nested_list(self) -> None:
        """Test collapse with nested lists."""
        result = list(collapse([1, [2, 3], 4]))
        assert result == [1, 2, 3, 4]

    def test_collapse_deeply_nested(self) -> None:
        """Test collapse with deeply nested structures."""
        result = list(collapse([1, [2, [3, [4, 5]]], 6]))
        assert result == [1, 2, 3, 4, 5, 6]

    def test_collapse_mixed_types(self) -> None:
        """Test collapse with mixed data types."""
        result = list(collapse([1, ["a", "b"], [2.5, [True, False]]]))
        assert result == [1, "a", "b", 2.5, True, False]

    def test_collapse_with_strings(self) -> None:
        """Test that strings are not collapsed (treated as atomic)."""
        result = list(collapse(["hello", ["world", "test"], "end"]))
        assert result == ["hello", "world", "test", "end"]

    def test_collapse_with_base_type_str(self) -> None:
        """Test collapse with base_type=str stops at strings."""
        result = list(collapse([["a", "b"], ["c", ["d", "e"]]], base_type=str))
        assert result == ["a", "b", "c", "d", "e"]

    def test_collapse_with_base_type_int(self) -> None:
        """Test collapse with base_type=int stops at integers."""
        nested = [1, [2, [3, "hello"]], 4]
        result = list(collapse(nested, base_type=int))
        assert result == [1, 2, 3, "hello", 4]

    def test_collapse_with_tuples(self) -> None:
        """Test collapse works with tuples."""
        result = list(collapse([1, (2, 3), [4, (5, 6)]]))
        assert result == [1, 2, 3, 4, 5, 6]

    def test_collapse_preserves_order(self) -> None:
        """Test that collapse preserves the original order."""
        result = list(collapse([[1, 2], [3, [4, 5]], 6]))
        assert result == [1, 2, 3, 4, 5, 6]

    def test_collapse_with_bytes(self) -> None:
        """Test that bytes are not collapsed (treated as atomic)."""
        result = list(collapse([b"hello", [b"world", "test"], "end"]))
        assert result == [b"hello", b"world", "test", "end"]

    def test_collapse_empty_nested_lists(self) -> None:
        """Test collapse with empty nested lists."""
        result = list(collapse([1, [], [2, []], 3]))
        assert result == [1, 2, 3]

    def test_collapse_single_deeply_nested_item(self) -> None:
        """Test collapse with a single deeply nested item."""
        result = list(collapse([[[[["deep"]]]]]))
        assert result == ["deep"]

    def test_collapse_generator_input(self) -> None:
        """Test collapse works with generator input."""
        test_data = [1, [2, 3], 4]
        test_generator = (item for item in test_data)
        result = list(collapse(test_generator))
        assert result == [1, 2, 3, 4]

    def test_collapse_with_sets(self) -> None:
        """Test collapse works with sets (order may vary)."""
        expected_length = 4
        expected_values = {1, 2, 3, 4}
        result = list(collapse([1, {2, 3}, 4]))
        # Since set order is not guaranteed, we check for membership
        assert len(result) == expected_length
        for value in expected_values:
            assert value in result
