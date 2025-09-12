"""Test the Tailwind attribute processor."""

import pytest

from cutesy.attribute_processors.tailwind import TailwindClass, parse_tailwind_class


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
