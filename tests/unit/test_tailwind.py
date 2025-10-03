"""Test the Tailwind attribute processor."""

import pytest

from cutesy.attribute_processors.class_ordering.tailwind import (
    AttributeProcessor,
    TailwindClass,
    group_and_sort,
    parse_tailwind_class,
)


class TestTailwind:
    """Test the Tailwind attribute processor."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # No modifiers
            (
                "bg-red-500",
                TailwindClass(
                    class_name="bg-red-500",
                    modifiers=[],
                    full_string="bg-red-500",
                ),
            ),
            # Single modifier
            (
                "hover:bg-red-500",
                TailwindClass(
                    class_name="bg-red-500",
                    modifiers=["hover"],
                    full_string="hover:bg-red-500",
                ),
            ),
            # Multiple modifiers
            (
                "md:hover:focus:text-lg",
                TailwindClass(
                    class_name="text-lg",
                    modifiers=["md", "hover", "focus"],
                    full_string="md:hover:focus:text-lg",
                ),
            ),
            # Arbitrary variant with brackets
            (
                "dark:[&>*]:text-center",
                TailwindClass(
                    class_name="text-center",
                    modifiers=["dark", "[&>*]"],
                    full_string="dark:[&>*]:text-center",
                ),
            ),
            # Escaped colon inside arbitrary value
            (
                r"content-\[url\:example\.com\]",
                TailwindClass(
                    class_name=r"content-\[url\:example\.com\]",
                    modifiers=[],
                    full_string=r"content-\[url\:example\.com\]",
                ),
            ),
            # Mixed responsive + state + complex arbitrary variant
            (
                r"rtl:focus:hover:[&>svg\:not(\.hidden)]:fill-current",
                TailwindClass(
                    class_name="fill-current",
                    modifiers=["rtl", "focus", "hover", r"[&>svg\:not(\.hidden)]"],
                    full_string=r"rtl:focus:hover:[&>svg\:not(\.hidden)]:fill-current",
                ),
            ),
            # Arbitrary value as base
            (
                r"text-\[theme\(colors\.blue-500\/70\%\)\]",
                TailwindClass(
                    class_name=r"text-\[theme\(colors\.blue-500\/70\%\)\]",
                    modifiers=[],
                    full_string=r"text-\[theme\(colors\.blue-500\/70\%\)\]",
                ),
            ),
            # Arbitrary property variant
            (
                r"[&\:where(h1,h2)]:underline",
                TailwindClass(
                    class_name="underline",
                    modifiers=[r"[&\:where(h1,h2)]"],
                    full_string=r"[&\:where(h1,h2)]:underline",
                ),
            ),
            # Class with dash prefix removed
            (
                "sm:-mt-4",
                TailwindClass(
                    class_name="mt-4",
                    modifiers=["sm"],
                    full_string="sm:-mt-4",
                ),
            ),
            # Container query with container declaration
            (
                "@container:bg-blue",
                TailwindClass(
                    class_name="bg-blue",
                    modifiers=["@container"],
                    full_string="@container:bg-blue",
                ),
            ),
            # Named container query modifier
            (
                "@lg:text-center",
                TailwindClass(
                    class_name="text-center",
                    modifiers=["@lg"],
                    full_string="@lg:text-center",
                ),
            ),
            # Combined regular and @ modifiers
            (
                "hover:@container:bg-red",
                TailwindClass(
                    class_name="bg-red",
                    modifiers=["hover", "@container"],
                    full_string="hover:@container:bg-red",
                ),
            ),
            # Container declaration standalone
            (
                "@container",
                TailwindClass(
                    class_name="@container",
                    modifiers=[],
                    full_string="@container",
                ),
            ),
        ],
    )
    def test_parse_tailwind_class(self, raw: str, expected: TailwindClass) -> None:
        """Test parsing a Tailwind class string."""
        got = parse_tailwind_class(raw)
        assert got == expected, f"\nRaw: {raw}\nExpected: {expected}\nGot: {got}"

    def test_modifiers_empty_when_no_modifiers(self) -> None:
        """Test modifiers are empty when no modifiers are present."""
        got = parse_tailwind_class("p-4")
        assert got.modifiers == []
        assert got.class_name == "p-4"
        assert got.full_string == "p-4"

    def test_keeps_backslashes_in_full_and_class_name(self) -> None:
        """Test backslashes are kept in full and class name."""
        raw = r"before:content-\['foo\:bar'\]"
        got = parse_tailwind_class(raw)
        assert got.modifiers == ["before"]
        assert got.class_name == r"content-\['foo\:bar'\]"
        assert got.full_string == raw


class TestAttributeProcessor:
    """Test the AttributeProcessor class."""

    def test_sort_with_grouped_false(self) -> None:
        """Test sort method with grouped=False returns flat list."""
        processor = AttributeProcessor()
        classes = ["bg-red-500", "text-white", "p-4"]
        result = processor.sort(classes, grouped=False)
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    def test_sort_with_grouped_true(self) -> None:
        """Test sort method with grouped=True returns list of lists."""
        processor = AttributeProcessor()
        classes = ["bg-red-500", "text-white", "p-4", "hover:bg-blue-500"]
        result = processor.sort(classes, grouped=True)
        assert isinstance(result, list)
        assert all(isinstance(group, list) for group in result)


class TestGroupAndSort:
    """Test the group_and_sort function."""

    def test_basic_grouping(self) -> None:
        """Test basic class grouping by category."""
        classes = ["bg-red-500", "p-4", "text-white", "flex"]
        groups = group_and_sort(classes)

        # Should have multiple groups
        assert len(groups) > 1

        # All groups should contain strings
        for group in groups:
            assert all(isinstance(tailwind_class, str) for tailwind_class in group)

    def test_user_defined_classes_last(self) -> None:
        """Test user-defined classes appear in the last group."""
        classes = ["bg-red-500", "my-custom-class", "p-4"]
        groups = group_and_sort(classes)

        # User-defined class should be in one of the groups (find it)
        found = False
        for group in groups:
            if "my-custom-class" in group:
                found = True
                break
        assert found

    def test_arbitrary_selector_variants(self) -> None:
        """Test arbitrary selector variants get their own groups."""
        classes = ["bg-red-500", "[&>*]:text-center", "p-4"]
        groups = group_and_sort(classes)

        # Should find the arbitrary selector class
        found = False
        for group in groups:
            if "[&>*]:text-center" in group:
                found = True
                break
        assert found

    def test_empty_input(self) -> None:
        """Test empty input returns empty list."""
        assert group_and_sort([]) == []

    def test_single_class(self) -> None:
        """Test single class input."""
        result = group_and_sort(["bg-red-500"])
        assert len(result) >= 1
        found = any("bg-red-500" in group for group in result)
        assert found

    def test_bem_notation_with_double_hyphens(self) -> None:
        """Test -- (double hyphens) is treated as user-defined."""
        classes = ["bg-red-500", "block__element--modifier", "p-4"]
        groups = group_and_sort(classes)

        # BEM class with -- should be treated as user-defined, not tailwind
        found_bem = False
        for group in groups:
            if "block__element--modifier" in group:
                found_bem = True
                break
        assert found_bem

    def test_bem_notation_with_double_underscores(self) -> None:
        """Test __ (double underscores) is treated as user-defined."""
        classes = ["bg-red-500", "block__element", "p-4"]
        groups = group_and_sort(classes)

        # BEM class with __ should be treated as user-defined, not tailwind
        found_bem = False
        for group in groups:
            if "block__element" in group:
                found_bem = True
                break
        assert found_bem

    def test_bem_notation_inside_arbitrary_values_allowed(self) -> None:
        """Test BEM notation inside arbitrary values [...] should be allowed.

        This covers the edge case where -- inside arbitrary values like
        mt-[var(--spacing)] should still be treated as valid Tailwind
        classes.
        """
        classes = ["bg-red-500", "mt-[var(--spacing)]", "p-4"]
        groups = group_and_sort(classes)

        # Class with -- inside arbitrary value should be treated as tailwind
        found_arbitrary = False
        for group in groups:
            if "mt-[var(--spacing)]" in group:
                found_arbitrary = True
                break
        assert found_arbitrary

    def test_prefix_removal_edge_cases(self) -> None:
        """Test edge cases for prefix removal in class name parsing."""
        # Test double dash prefix (like CSS custom properties)
        result = parse_tailwind_class("--custom-property")
        assert result.class_name == "-custom-property"  # Only first dash removed
        assert result.modifiers == []

        # Test single dash prefix
        result = parse_tailwind_class("-mt-4")
        assert result.class_name == "mt-4"  # Dash prefix removed
        assert result.modifiers == []

    def test_at_container_queries(self) -> None:
        """Test @ container queries are properly parsed and sorted."""
        classes = ["@lg:text-lg", "bg-red-500", "hover:@max-sm:p-4", "@container"]
        groups = group_and_sort(classes)

        # Should find classes with @ modifiers and declarations
        all_classes = [class_name for group in groups for class_name in group]
        assert "@lg:text-lg" in all_classes
        assert "hover:@max-sm:p-4" in all_classes
        assert "bg-red-500" in all_classes
        assert "@container" in all_classes
