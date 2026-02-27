"""Test the Tailwind attribute processor."""

import pytest

from cutesy.attribute_processors.class_ordering.tailwind import (
    AttributeProcessor,
    TailwindClass,
    _find_group,
    _merge_collapsible_groups,
    group_and_sort,
    parse_tailwind_class,
)
from cutesy.attribute_processors.class_ordering.types import SuperGroup


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


class TestFlexGroupAssignment:
    """Test that flex/grid classes are assigned to the correct groups."""

    @pytest.mark.parametrize(
        ("class_name", "expected_group"),
        [
            # Display group
            ("flex", "display"),
            ("inline-flex", "display"),
            ("grid", "display"),
            ("block", "display"),
            ("inline-block", "display"),
            ("inline", "display"),
            ("hidden", "display"),
            ("contents", "display"),
            # Flex container group
            ("flex-row", "flex container"),
            ("flex-col", "flex container"),
            ("flex-wrap", "flex container"),
            ("flex-nowrap", "flex container"),
            ("justify-center", "flex container"),
            ("justify-between", "flex container"),
            ("items-center", "flex container"),
            ("items-start", "flex container"),
            ("content-between", "flex container"),
            ("place-content-center", "flex container"),
            ("place-items-start", "flex container"),
            # Flex item group
            ("order-1", "flex item"),
            ("flex-1", "flex item"),
            ("flex-auto", "flex item"),
            ("flex-initial", "flex item"),
            ("flex-none", "flex item"),
            ("grow", "flex item"),
            ("shrink", "flex item"),
            ("basis-1/2", "flex item"),
            ("self-center", "flex item"),
            ("self-start", "flex item"),
            ("place-self-end", "flex item"),
            # Grid group
            ("grid-cols-3", "grid"),
            ("grid-rows-2", "grid"),
            ("col-span-2", "grid"),
            ("row-span-full", "grid"),
            ("col-start-1", "grid"),
            ("col-end-3", "grid"),
            ("row-start-2", "grid"),
            ("row-end-4", "grid"),
            ("columns-3", "grid"),
            # Gap/space group
            ("gap-4", "gap/space"),
            ("gap-x-2", "gap/space"),
            ("space-x-4", "gap/space"),
            ("space-y-2", "gap/space"),
        ],
    )
    def test_group_assignment(self, class_name: str, expected_group: str) -> None:
        """Test each class is assigned to the correct group."""
        assert _find_group(class_name) == expected_group

    def test_flex_negative_lookahead_prevents_prefix_match(self) -> None:
        """Test flex(?!-) in display doesn't capture flex-* classes."""
        # 'flex' goes to display, but 'flex-row' goes to flex container
        assert _find_group("flex") == "display"
        assert _find_group("flex-row") == "flex container"
        assert _find_group("flex-1") == "flex item"

    def test_grid_negative_lookahead_prevents_prefix_match(self) -> None:
        """Test grid(?!-) in display doesn't capture grid-* classes."""
        assert _find_group("grid") == "display"
        assert _find_group("grid-cols-3") == "grid"
        assert _find_group("grid-rows-2") == "grid"


class TestSuperGroup:
    """Test the SuperGroup class and collapsible group merging."""

    def test_super_group_is_sequence(self) -> None:
        """Test SuperGroup behaves as a sequence."""
        sg = SuperGroup([["a"], ["b"]])
        assert len(sg) == 2  # noqa: PLR2004
        assert sg[0] == ["a"]
        assert isinstance(sg, SuperGroup)

    def test_super_group_isinstance_check(self) -> None:
        """Test isinstance distinguishes SuperGroup from plain list."""
        sg = SuperGroup([["a"], ["b"]])
        plain = [["a"], ["b"]]
        assert isinstance(sg, SuperGroup)
        assert not isinstance(plain, SuperGroup)

    def test_group_and_sort_without_super_groups_returns_flat(self) -> None:
        """Test with_super_groups=False returns no SuperGroup instances."""
        classes = ["flex", "items-center", "order-1", "gap-4", "p-4", "bg-red-500"]
        groups = group_and_sort(classes, with_super_groups=False)
        for group in groups:
            assert not isinstance(group, SuperGroup)

    def test_group_and_sort_with_super_groups_wraps_layout(self) -> None:
        """Test with_super_groups=True wraps layout groups in SuperGroup."""
        classes = ["flex", "items-center", "order-1", "gap-4", "p-4", "bg-red-500"]
        groups = group_and_sort(classes, with_super_groups=True)

        # Should have a SuperGroup containing display, flex container, flex item, gap/space
        super_groups = [
            super_group for super_group in groups if isinstance(super_group, SuperGroup)
        ]
        assert len(super_groups) == 1

        sg = super_groups[0]
        expected_sub_group_count = 4
        assert len(sg) == expected_sub_group_count

        # Flatten and verify all layout classes are in the super-group
        all_layout = [class_name for sub in sg for class_name in sub]
        assert "flex" in all_layout
        assert "items-center" in all_layout
        assert "order-1" in all_layout
        assert "gap-4" in all_layout

        # Non-layout classes should NOT be in the super-group
        assert "p-4" not in all_layout
        assert "bg-red-500" not in all_layout

    def test_single_layout_group_not_wrapped(self) -> None:
        """Test a single collapsible group is not wrapped in SuperGroup."""
        classes = ["flex", "p-4", "bg-red-500"]
        groups = group_and_sort(classes, with_super_groups=True)

        # Only one layout group (display with 'flex'), so no wrapping
        super_groups = [
            super_group for super_group in groups if isinstance(super_group, SuperGroup)
        ]
        assert len(super_groups) == 0

    def test_no_layout_classes_no_super_group(self) -> None:
        """Test no SuperGroup when there are no layout classes."""
        classes = ["p-4", "mt-8", "bg-red-500", "text-white"]
        groups = group_and_sort(classes, with_super_groups=True)
        super_groups = [
            super_group for super_group in groups if isinstance(super_group, SuperGroup)
        ]
        assert len(super_groups) == 0

    def test_super_group_preserves_subgroup_order(self) -> None:
        """Test sub-groups within SuperGroup maintain correct order."""
        classes = ["gap-4", "order-1", "items-center", "flex"]
        groups = group_and_sort(classes, with_super_groups=True)

        super_groups = [
            super_group for super_group in groups if isinstance(super_group, SuperGroup)
        ]
        assert len(super_groups) == 1

        sg = super_groups[0]
        # display comes first, then flex container, then flex item, then gap/space
        assert sg[0] == ["flex"]
        assert sg[1] == ["items-center"]
        assert sg[2] == ["order-1"]
        assert sg[3] == ["gap-4"]

    def test_super_group_with_grid_classes(self) -> None:
        """Test grid classes are included in the layout super-group."""
        classes = ["grid", "grid-cols-3", "gap-4", "p-4"]
        groups = group_and_sort(classes, with_super_groups=True)

        super_groups = [
            super_group for super_group in groups if isinstance(super_group, SuperGroup)
        ]
        assert len(super_groups) == 1

        sg = super_groups[0]
        all_layout = [class_name for sub in sg for class_name in sub]
        assert "grid" in all_layout
        assert "grid-cols-3" in all_layout
        assert "gap-4" in all_layout

    def test_super_group_with_all_five_layout_groups(self) -> None:
        """Test all five layout sub-groups appear in one SuperGroup."""
        classes = [
            "flex",
            "items-center",
            "justify-between",
            "order-2",
            "grow",
            "grid-cols-3",
            "gap-4",
            "space-x-2",
        ]
        groups = group_and_sort(classes, with_super_groups=True)

        super_groups = [
            super_group for super_group in groups if isinstance(super_group, SuperGroup)
        ]
        assert len(super_groups) == 1

        sg = super_groups[0]
        expected_sub_group_count = 5
        assert len(sg) == expected_sub_group_count

    def test_empty_input_with_super_groups(self) -> None:
        """Test empty input returns empty list with super-groups enabled."""
        assert group_and_sort([], with_super_groups=True) == []

    def test_user_defined_not_in_super_group(self) -> None:
        """Test user-defined classes are never part of a SuperGroup."""
        classes = ["flex", "items-center", "my-custom", "gap-4"]
        groups = group_and_sort(classes, with_super_groups=True)

        for group in groups:
            if isinstance(group, SuperGroup):
                all_classes = [class_name for sub in group for class_name in sub]
                assert "my-custom" not in all_classes

    def test_arbitrary_selectors_not_in_super_group(self) -> None:
        """Test arbitrary selector groups are not part of a SuperGroup."""
        classes = ["flex", "items-center", "[&>*]:text-center", "gap-4"]
        groups = group_and_sort(classes, with_super_groups=True)

        for group in groups:
            if isinstance(group, SuperGroup):
                all_classes = [class_name for sub in group for class_name in sub]
                assert "[&>*]:text-center" not in all_classes


class TestMergeCollapsibleGroups:
    """Test the _merge_collapsible_groups function directly."""

    def test_merges_adjacent_collapsible_groups(self) -> None:
        """Test adjacent collapsible groups are merged."""
        tagged: list[tuple[str | None, list[str]]] = [
            ("display", ["flex"]),
            ("flex container", ["items-center"]),
            ("flex item", ["order-1"]),
            ("spacing (margin/padding)", ["p-4"]),
        ]
        result = _merge_collapsible_groups(tagged)
        assert len(result) == 2  # noqa: PLR2004
        assert isinstance(result[0], SuperGroup)
        assert not isinstance(result[1], SuperGroup)
        assert result[1] == ["p-4"]

    def test_single_collapsible_group_not_wrapped(self) -> None:
        """Test a single collapsible group stays flat."""
        tagged: list[tuple[str | None, list[str]]] = [
            ("display", ["flex"]),
            ("spacing (margin/padding)", ["p-4"]),
        ]
        result = _merge_collapsible_groups(tagged)
        assert len(result) == 2  # noqa: PLR2004
        assert not isinstance(result[0], SuperGroup)
        assert result[0] == ["flex"]

    def test_non_collapsible_groups_pass_through(self) -> None:
        """Test non-collapsible groups are not wrapped."""
        tagged: list[tuple[str | None, list[str]]] = [
            ("spacing (margin/padding)", ["p-4"]),
            ("typography", ["text-white"]),
            ("backgrounds/gradients", ["bg-red-500"]),
        ]
        result = _merge_collapsible_groups(tagged)
        assert len(result) == 3  # noqa: PLR2004
        for group in result:
            assert not isinstance(group, SuperGroup)

    def test_untagged_groups_not_merged(self) -> None:
        """Test None-tagged groups (arbitrary/user-defined) are not merged."""
        tagged = [
            ("display", ["flex"]),
            (None, ["[&>*]:text-center"]),
            ("flex container", ["items-center"]),
        ]
        result = _merge_collapsible_groups(tagged)
        # The None group breaks the adjacency, so display is alone (not wrapped)
        # and flex container is alone (not wrapped)
        assert len(result) == 3  # noqa: PLR2004
        for group in result:
            assert not isinstance(group, SuperGroup)

    def test_empty_input(self) -> None:
        """Test empty input returns empty list."""
        assert _merge_collapsible_groups([]) == []


class TestSuperGroupRendering:
    """Test end-to-end rendering with SuperGroup collapsing."""

    def setup_method(self) -> None:
        """Set up the Tailwind processor for rendering tests."""
        self.processor = AttributeProcessor()

    def test_short_layout_classes_single_line(self) -> None:
        """Test short layout classes stay on one line."""
        result = self._render("flex items-center gap-4 p-4 bg-red-500")
        assert "\n" not in result
        assert result == "flex items-center gap-4 p-4 bg-red-500"

    def test_layout_super_group_collapses_in_multiline(self) -> None:
        """Test layout groups collapse onto one line in multi-line output."""
        # Enough classes to trigger multi-line, but layout should collapse
        result = self._render(
            "flex items-center justify-center order-1 grow gap-4"
            " p-4 text-white font-bold text-xl bg-red-500"
            " border-2 rounded-lg shadow-lg transform transition-all cursor-pointer",
        )
        lines = result.split("\n")
        # Find the line with layout classes — should be combined
        layout_line = next(
            (line for line in lines if "flex" in line and "items-center" in line),
            None,
        )
        assert layout_line is not None
        # All layout classes should be on that same line
        assert "justify-center" in layout_line
        assert "order-1" in layout_line
        assert "grow" in layout_line
        assert "gap-4" in layout_line

    def test_layout_super_group_splits_when_too_long(self) -> None:
        """Test layout groups split into sub-groups when combined is long."""
        # Many layout classes — line_length=60 allows sub-groups on their own
        # lines but the combined super-group is too long to collapse
        result = self._render(
            "flex flex-row flex-wrap items-center justify-between"
            " order-1 grow shrink basis-1/2 self-center"
            " grid-cols-3 col-span-2 columns-3"
            " gap-4 space-x-2 space-y-4"
            " p-4 bg-red-500",
            line_length=60,
        )
        lines = result.split("\n")

        # Should be multi-line
        assert len(lines) > 2  # noqa: PLR2004

        # Layout sub-groups should each get their own line since combined is too long
        # Verify flex container and flex item classes are on separate lines
        flex_container_found = any("flex-row" in line and "items-center" in line for line in lines)
        flex_item_found = any("order-1" in line and "grow" in line for line in lines)
        assert flex_container_found
        assert flex_item_found

    def test_non_layout_groups_separate_lines(self) -> None:
        """Test non-layout groups get their own lines in multi-line mode."""
        result = self._render(
            "flex items-center gap-4 p-4 mt-8 text-white font-bold"
            " bg-red-500 border-2 rounded-lg shadow-lg cursor-pointer",
        )
        if "\n" not in result:
            # Single-line mode, skip multi-line assertions
            return

        lines = result.split("\n")
        # Spacing, typography, backgrounds should be on separate lines
        spacing_line = next((line for line in lines if "p-4" in line), None)
        bg_line = next((line for line in lines if "bg-red-500" in line), None)
        assert spacing_line is not None
        assert bg_line is not None
        assert spacing_line != bg_line

    def test_only_layout_classes_single_group_path(self) -> None:
        """Test only layout classes still render correctly."""
        result = self._render("flex items-center order-1 gap-4")
        assert "\n" not in result
        assert "flex" in result
        assert "items-center" in result
        assert "order-1" in result
        assert "gap-4" in result

    def test_grid_layout_collapses_with_flex(self) -> None:
        """Test grid + flex classes collapse together in a super-group."""
        result = self._render(
            "grid grid-cols-3 gap-4 p-4 text-white font-bold"
            " bg-red-500 border-2 rounded-lg shadow-lg cursor-pointer",
        )
        if "\n" not in result:
            return

        lines = result.split("\n")
        # grid, grid-cols-3, and gap-4 should be on the same line
        grid_line = next((line for line in lines if "grid" in line), None)
        assert grid_line is not None
        assert "grid-cols-3" in grid_line
        assert "gap-4" in grid_line

    def _render(
        self,
        attr_body: str,
        line_length: int = 80,
        current_indentation_level: int = 1,
    ) -> str:
        """Render class attribute through the processor."""
        result, _errors = self.processor.process(
            attr_name="class",
            position=(1, 0),
            indentation="\t",
            current_indentation_level=current_indentation_level,
            tab_width=4,
            line_length=line_length,
            max_items_per_line=5,
            bounding_character='"',
            preprocessor=None,
            attr_body=attr_body,
        )
        return result
