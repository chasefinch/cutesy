"""Class sorting to accommodate the Tailwind CSS framework."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, NamedTuple, TypeAlias

from more_itertools import collapse

from ..types import InstructionType, Rule
from . import BaseAttributeProcessor

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ..preprocessors import BasePreprocessor


DYNAMIC_LIST_ITEM_SENTINEL = "__LIST_ITEM_SENTINEL_A3VJ3FL__"


Rule("TW1", "Control instruction overlaps class names")


StashItem: TypeAlias = "str | list[StashItem]"

StackNode: TypeAlias = list["int | StackNode"]

IndexRangeNode: TypeAlias = list["int | IndexRangeNode"]


class TailwindClass(NamedTuple):
    """Class representation for Tailwind CSS."""

    class_name: str
    modifiers: list[str]
    full_string: str


class AttributeProcessor(BaseAttributeProcessor):
    """Sort classes according to the Tailwind style."""

    stashed_class_names: list[StashItem]

    def process(
        self,
        attr_name: str,
        position: tuple[int, int],
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        max_chars_per_line: int,
        max_items_per_line: int,
        bounding_character: str,
        preprocessor: BasePreprocessor | None,
        attr_body: str,
    ) -> str:
        """Update the class attribute body with sorted classes."""
        if attr_name != "class":
            return attr_body

        self.indentation = indentation

        self.max_length = max_chars_per_line - ((current_indentation_level + 1) * tab_width)
        self.max_items_per_line = max_items_per_line

        self.stashed_class_names = []

        adjusted_attr_body = attr_body.strip()
        class_names = adjusted_attr_body.split()
        preprocessed_index_ranges: list[IndexRangeNode] = []

        if preprocessor:
            left, right = preprocessor.delimiters
            line, column = position

            # Ensure that there aren't mid-class instructions
            esc = re.escape
            block_starts = InstructionType.block_starts | InstructionType.block_continuations
            block_ends = InstructionType.block_ends
            start_set = "".join(esc(type_.value) for type_ in block_starts)
            end_set = "".join(esc(type_.value) for type_ in block_ends)

            # "Bad left": a LEFT that is not at start and not immediately after RIGHT,
            # *and* whose next char is in starting_chars.
            bad_left = rf"(?<!{esc(right)}){esc(left)}(?=[{start_set}])"

            # Bad RIGHT: in a segment that started with LEFT+ending_char,
            # and this RIGHT is not followed by LEFT and not at end of string
            bad_right = (
                rf"{esc(left)}[{end_set}][^{esc(right)}]*?"
                rf"{esc(right)}(?!{esc(left)}|$)"
            )

            raise_tw1 = any(
                re.search(bad_left, class_name[1:]) or re.search(bad_right, class_name)
                for class_name in class_names
            )

            class_names = expand_class_names(class_names, left, right, keep_empty=False)
            stack: list[StackNode] = []

            for index, class_name in enumerate(class_names):
                if class_name.startswith(left):
                    min_instruction_string_length = 4
                    assert len(class_name) >= min_instruction_string_length
                    instruction_type = InstructionType(class_name[1])

                    if instruction_type.starts_block:
                        node: list = [index]  # start index
                        if stack:
                            stack[-1].append(node)  # nest under current open node
                        else:
                            preprocessed_index_ranges.append(node)  # top-level
                        stack.append(node)

                    elif instruction_type.continues_block:
                        if not stack:
                            error_message = f"Continuation outside a block at index {index}"
                            raise ValueError(error_message)
                        stack[-1].append(index)  # continuation marker

                    elif instruction_type.ends_block:
                        if not stack:
                            error_message = f"Unbalanced block ending at index {index}"
                            raise ValueError(error_message)
                        stack[-1].append(index + 1)  # end index (exclusive)
                        stack.pop()

            if stack:
                raise_tw1 = True

            if raise_tw1:
                error_code = "TW1"
                raise preprocessor.make_fatal_error(
                    error_code,
                    line=line,
                    column=column,
                    tag="Instruction",
                )

            for index, index_range in enumerate(reversed(preprocessed_index_ranges)):
                sentinel = f"{DYNAMIC_LIST_ITEM_SENTINEL}_{index}"
                class_names, stash = extract_with_sentinel(class_names, index_range, sentinel)
                self.stashed_class_names.append(stash)

        classes = []
        for class_name in class_names:
            tailwind_class = parse_tailwind_class(class_name)
            classes.append(tailwind_class)

        # Single-line mode
        sorted_class_groups = group_and_sort_tailwind(classes)
        sorted_class_groups = self._hydrate_class_groups(sorted_class_groups)
        all_class_names = list(collapse(sorted_class_groups, base_type=str))
        all_class_names_on_one_line = " ".join(all_class_names)

        max_attr_chars_per_line = self.max_length - len('class=""')
        single_line_mode = (
            len(all_class_names) <= max_items_per_line
            and len(all_class_names_on_one_line) <= max_attr_chars_per_line
        )

        if single_line_mode:
            return all_class_names_on_one_line

        # Multi-line modes...
        attribute_lines = [""]
        line_indentation = (current_indentation_level + 1) * indentation

        # ...#1: One group, but long enough to merit multiple lines.
        if len(sorted_class_groups) == 1:
            # Only one group, but long enough to merit multiple lines.
            for group_entry in sorted_class_groups[0]:
                lines = self._extract_columns_and_lines(group_entry)
                for column_index, line_value in lines:
                    extra_indentation: str = indentation * column_index
                    attribute_lines.append(f"{line_indentation}{extra_indentation}{line_value}")

        else:
            for group in sorted_class_groups:
                multiple_lines = any(isinstance(item, list) for item in group)
                if multiple_lines:
                    for multi_group_entry in group:
                        lines = self._extract_columns_and_lines(multi_group_entry)
                        for column_index, line_value in lines:
                            extra_indentation = indentation * column_index
                            attribute_lines.append(
                                f"{line_indentation}{extra_indentation}{line_value}",
                            )
                else:
                    attribute_lines.append(" ".join(group))

        # Add the final line
        attribute_lines.append(current_indentation_level * indentation)
        return "\n".join(attribute_lines)

    def _flatten_stash(self, stash: str | Sequence[StashItem]) -> str | list[str]:
        """Recursively flatten `stash`.

        - Nested lists are flattened
        - Any list that becomes a single string returns that string directly
        - If a list can be compacted within limits, it joins into a single
          string with special spacing rules:
            * No space between first & second items
            * No space between second-to-last & last items
            * Single space between everything else
        - Otherwise return a list[str].
        """
        if isinstance(stash, str):
            return stash

        flat_parts: list[str] = []

        for item in stash:
            if isinstance(item, str):
                flat_parts.append(item)
            else:
                collapsed = self._flatten_stash(item)
                if isinstance(collapsed, str):
                    flat_parts.append(collapsed)
                else:
                    flat_parts.extend(collapsed)  # collapsed is list[str]

        # If it collapsed to a single string, return that directly
        if len(flat_parts) == 1:
            return flat_parts[0]

        # If it fits on one line, compact it
        if len(flat_parts) <= self.max_items_per_line:
            # Strip leading & trailing spaces from this one-liner
            pieces: list[str] = []
            for index, part in enumerate(flat_parts):
                if index == 0:
                    pieces.append(part)
                elif index == 1 or index == len(flat_parts) - 1:
                    pieces[-1] += part
                else:
                    pieces.append(part)
            candidate = " ".join(pieces)
            if len(candidate) <= self.max_length:
                return candidate

        # Otherwise, return the list of strings
        return flat_parts

    def _hydrate_class_groups(self, class_groups: list[list[str]]) -> list[list[str]]:
        """Hydrate a stash into a list of class groups."""
        if not class_groups:
            return []

        hydrated_class_groups = class_groups[:-1]
        flat_class_entries: list[str] = []
        for user_defined_item in class_groups[-1]:
            if user_defined_item.startswith(DYNAMIC_LIST_ITEM_SENTINEL):
                index = int(user_defined_item.split("_")[-1])
                flattened = self._flatten_stash(self.stashed_class_names.pop(index))
                if isinstance(flattened, str):
                    flat_class_entries.append(flattened)
                else:
                    flat_class_entries.extend(flattened)  # list[str]
            else:
                flat_class_entries.append(user_defined_item)
        hydrated_class_groups.append(flat_class_entries)
        return hydrated_class_groups

    def _extract_columns_and_lines(
        self,
        item: StashItem,
        column: int = 0,
    ) -> list[tuple[int, str]]:
        if isinstance(item, list):
            min_wrapped_instruction_length = 2
            assert len(item) >= min_wrapped_instruction_length
            # First and last entries of a wrapped block are always strings
            assert isinstance(item[0], str)
            assert isinstance(item[-1], str)

            columns_and_lines: list[tuple[int, str]] = [(column, item[0])]
            for subitem in item[1:-1]:
                columns_and_lines.extend(self._extract_columns_and_lines(subitem, column + 1))
            columns_and_lines.append((column, item[-1]))
            return columns_and_lines

        # Base case: item must be a string here
        assert isinstance(item, str)
        return [(column, item)]


def expand_class_names(
    class_names: Iterable[str],
    left: str,
    right: str,
    *,
    keep_empty: bool = False,
) -> list[str]:
    """Break up delimited strings in a list of class names.

    For each string in `class_names`, find every occurrence of text delimited by
    `left` ... `right`, and expand that string into a sequence of alternating
    outside-text and delimited-chunk entries. Returns the flattened list.

    Example:
        class_names = ["btn{primary}--lg{x}-shadow", "card"]
        left, right = "{", "}"
        -> ["btn", "{primary}", "--lg", "{x}", "-shadow", "card"]

    Notes:
      - Uses a non-greedy match; supports multiple delimited sections per string.
      - Unmatched delimiters leave the string as-is (no split).
      - Set keep_empty=True to retain empty outside pieces (default drops them).
      - Does not attempt to handle nested delimiters (e.g., “{ a { b } }”).

    """
    pattern = re.compile(f"({re.escape(left)}.*?{re.escape(right)})")
    out: list[str] = []

    for class_name in class_names:
        # If there are no delimited chunks, keep the string as-is.
        if not pattern.search(class_name):
            out.append(class_name)
            continue

        parts = pattern.split(class_name)  # keeps the delimited chunks in the result
        if not keep_empty:
            parts = [part for part in parts if part != ""]

        out.extend(parts)

    return out


def extract_with_sentinel(
    class_names: list[str],
    index_tree: IndexRangeNode,
    sentinel: str,
) -> tuple[list[str], StashItem]:
    """Extract a span of class names and replace it with a sentinel.

    Returns (new_class_names, stash), where new_class_names has
    class_names[start:end] replaced by the sentinel, and stash is a nested
    structure of the removed items.

    In the stash, plain strings are class names, and lists represent nested
    blocks.
    """
    start = index_tree[0]
    end = index_tree[-1]

    assert isinstance(start, int)
    assert isinstance(end, int)

    stash = _build_stash(class_names, index_tree)
    new_class_names = [*class_names[:start], sentinel, *class_names[end:]]
    return new_class_names, stash


def parse_tailwind_class(full: str) -> TailwindClass:
    """Parse a Tailwind class string into a TailwindClass object."""
    parts = []
    buffer = []
    in_brackets = False
    escape = False

    for char in full:
        if escape:
            buffer.append(char)
            escape = False
            continue

        if char == "\\":
            buffer.append(char)  # keep backslash for fidelity
            escape = True
            continue

        if char == ":" and not in_brackets:
            parts.append("".join(buffer))
            buffer = []
        else:
            if char == "[":
                in_brackets = True
            elif char == "]":
                in_brackets = False
            buffer.append(char)

    parts.append("".join(buffer))

    modifiers, base = parts[:-1], parts[-1]

    return TailwindClass(
        class_name=base,
        modifiers=modifiers,
        full_string=full,
    )


GROUPS_IN_ORDER: Sequence[tuple[str, Sequence[str]]] = (
    (
        "display/position",
        (
            r"(?:container|block|inline|inline-block|inline-flex|flex|grid|contents|hidden)",
            r"(?:static|fixed|absolute|relative|sticky)",
            r"(?:float-|clear-)",
            r"(?:z-|isolation|inset-|top-|right-|bottom-|left-)",
        ),
    ),
    (
        "flex/grid core",
        (
            r"(?:order-)",
            r"(?:flex-|grow|shrink|basis-)",
            r"(?:grid-cols-|grid-rows-|col-span-|row-span-|col-start-|col-end-|row-start-|row-end-)",
        ),
    ),
    (
        "flex/grid alignment",
        (
            r"(?:place-content-|place-items-|place-self-)",
            r"(?:justify-|content-)",
            r"(?:items-|self-)",
        ),
    ),
    (
        "columns/gap",
        (
            r"(?:columns-)",
            r"(?:gap-|space-[xy]-)",
        ),
    ),
    (
        "spacing (margin/padding)",
        (
            r"(?:m[trblxy]?-\S+)",
            r"(?:p[trblxy]?-\S+)",
        ),
    ),
    ("sizing", (r"(?:w-|min-w-|max-w-|h-|min-h-|max-h-|aspect-)",)),
    (
        "typography",
        (
            r"(?:font-|text-|leading-|tracking-|list-|placeholder-|whitespace-|break-|hyphens-)",
            r"(?:align-)",
            r"(?:content-)",
        ),
    ),
    (
        "backgrounds/gradients",
        (
            r"(?:bg-)",
            r"(?:from-|via-|to-|gradient-)",
        ),
    ),
    ("borders/outline/radius/divide", (r"(?:border-|rounded-|divide-|outline-)",)),
    ("effects", (r"(?:shadow-|opacity-|mix-blend-|backdrop-)",)),
    ("transforms", (r"(?:transform|scale-|rotate-|translate-|skew-)",)),
    ("transitions/animation", (r"(?:transition|duration-|ease-|delay-|animate-)",)),
    (
        "interactivity/behavior",
        (r"(?:cursor-|select-|pointer-events-|touch-|scroll-|overscroll-|snap-)",),
    ),
    (
        "object/overflow",
        (
            r"(?:object-)",
            r"(?:overflow-)",
        ),
    ),
    ("svg", (r"(?:fill-|stroke-)",)),
    ("accessibility", (r"(?:sr-only|not-sr-only)",)),
)

_COMPILED: Final[tuple[tuple[str, list[re.Pattern[str]]], ...]] = tuple(
    (name, [re.compile(rf"^{pattern}") for pattern in patterns])
    for name, patterns in GROUPS_IN_ORDER
)

# Full group order we will emit
REAL_GROUPS_ORDER: Final[tuple[str, ...]] = tuple(name for name, _ in GROUPS_IN_ORDER)

# Modifier ordering (relative lists) ------------------------------------------

RESPONSIVE_ORDER = ("xs", "sm", "md", "lg", "xl", "2xl")

STATE_ORDER = (
    # group/peer first (gatekeepers)
    "group-hover",
    "group-focus",
    "group-active",
    "group-visited",
    "peer-checked",
    "peer-invalid",
    "peer-focus",
    "peer-hover",
    # element states
    "focus-within",
    "focus-visible",
    "focus",
    "hover",
    "active",
    "visited",
    "checked",
    "disabled",
    "required",
    "invalid",
    "read-only",
    "open",
    # theme/dir toggles
    "dark",
    "rtl",
    "ltr",
)

# Group finder & user-class placement -----------------------------------------


def group_and_sort_tailwind(
    classes: list[TailwindClass],
) -> list[list[str]]:
    """Return groups of tailwind class strings in fixed order.

    All user- defined classes will be collected into one final bucket at the
    bottom (preserving original order).

    Real Tailwind groups appear in REAL_GROUPS_ORDER, then "other (tailwind)",
    sorted by _intragroup_sort_key.

    User-defined classes (not recognized as Tailwind) are not mixed into
    groups; they are emitted as one final list at the end, in original order.
    """
    # Buckets for real groups (track original index for stable sort)
    group_items: dict[str, list[tuple[int, TailwindClass]]] = {
        group: [] for group in REAL_GROUPS_ORDER
    }
    group_items["other (tailwind)"] = []

    # Single bucket for all user-defined classes (preserve original order)
    user_defined: list[str] = []

    # Partition into Tailwind groups vs user-defined
    for index, tailwind_class in enumerate(classes):
        group = _find_group(tailwind_class.class_name)  # returns a group name or None
        if group is None:
            user_defined.append(tailwind_class.full_string)
        else:
            group_items[group].append((index, tailwind_class))

    # Emit results as a list of lists (group contents only)
    out: list[list[str]] = []

    # Real groups in fixed order, then "other (tailwind)"
    for group_name in (*REAL_GROUPS_ORDER, "other (tailwind)"):  # noqa: WPS426
        if not group_items[group_name]:
            continue
        sorted_group = sorted(
            group_items[group_name],
            key=lambda pair: _intragroup_sort_key(group_name, pair[1], pair[0]),
        )
        out.append([item.full_string for _, item in sorted_group])

    # Finally, all user-defined classes at the bottom (original order)
    if user_defined:
        out.append(user_defined)

    return out


# Loop, sort, and parse helpers -----------------------------------------------


def _build_stash(class_names: list[str], tree: list) -> list[StashItem]:
    start = tree[0]
    end = tree[-1]
    interior = tree[1:-1]

    stash: list = []
    cursor = start

    for child in interior:
        if isinstance(child, int):
            # Copy items before the scalar, then include the scalar item itself
            stash.extend(class_names[cursor:child])
            stash.append(class_names[child])
            cursor = child + 1
        else:
            # Nested block: child is a list like [start, ..., end]
            child_start = child[0]
            child_end = child[-1]
            # Copy items before the child block
            stash.extend(class_names[cursor:child_start])
            # Recurse for the nested block
            stash.append(_build_stash(class_names, child))
            cursor = child_end

    # Tail after last interior element up to (but not including) end
    stash.extend(class_names[cursor:end])
    return stash


RESPONSIVE_ORDER_INDEX: Final = MappingProxyType(
    {modifier: index for index, modifier in enumerate(RESPONSIVE_ORDER)},
)
STATE_ORDER_INDEX: Final = MappingProxyType(
    {modifier: index for index, modifier in enumerate(STATE_ORDER)},
)


def _modifier_key(
    modifiers: list[str],
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[str, ...]]:
    """Sort by responsive order, then state order, then literal (stable)."""
    responsive = tuple(
        RESPONSIVE_ORDER_INDEX[modifier]
        for modifier in modifiers
        if modifier in RESPONSIVE_ORDER_INDEX
    )
    state = tuple(
        STATE_ORDER_INDEX[modifier] for modifier in modifiers if modifier in STATE_ORDER_INDEX
    )
    other = tuple(
        modifier
        for modifier in modifiers
        if modifier not in RESPONSIVE_ORDER_INDEX and modifier not in STATE_ORDER_INDEX
    )
    return (responsive, state, other)


_SPACING_AXIS = ("x", "y")
_SPACING_SIDES = ("t", "b", "r", "l", "s", "e")


def _spacing_specificity(name: str) -> int:
    # p- / m- < px-/py-/mx-/my- < pt-/pr-/.../ml-
    if name.startswith(("p-", "m-")):
        return 0
    if any(name.startswith((f"p{axis}-", f"m{axis}-")) for axis in _SPACING_AXIS):
        return 1
    if any(name.startswith((f"p{side}-", f"m{side}-")) for side in _SPACING_SIDES):
        return 2
    return 0


def _border_specificity(name: str) -> int:
    # border-* < border-x/y-* < border-t/r/b/l-* ; for rounded: rough by hyphen count
    if name.startswith("border-"):
        if any(name.startswith(f"border-{axis}-") for axis in _SPACING_AXIS):
            return 1
        if any(name.startswith(f"border-{side}-") for side in _SPACING_SIDES):
            return 2
        return 0
    if name.startswith("rounded-"):
        return name.count("-")
    return 0


def _family_key(group_name: str, class_name: str) -> tuple:
    """Cluster similar utilities inside a group."""
    head = class_name.split("-", 1)[0]  # e.g., 'bg', 'text', 'p', 'border'
    if group_name == "spacing (margin/padding)":
        return (head, _spacing_specificity(class_name))
    if group_name == "borders/outline/radius/divide":
        return (head, _border_specificity(class_name))
    # generic: more segments → consider more specific
    return (head, class_name.count("-"))


def _intragroup_sort_key(group_name: str, item: TailwindClass, original_index: int) -> tuple:
    """Sort within a group.

    Unmodified first, then modifiers in consistent order, then name, then
    stable index.
    """
    has_mods = 1 if item.modifiers else 0
    base = item.class_name
    return (
        _family_key(group_name, base),
        has_mods,  # 0 (no mods) before 1 (has mods)
        _modifier_key(item.modifiers),
        base,
        original_index,
    )


def _find_group(class_name: str) -> str | None:
    unwanted_keys = ("--", "__")
    if any(key in class_name for key in unwanted_keys):
        return None
    for group_name, compiled_list in _COMPILED:
        if any(pat.match(class_name) for pat in compiled_list):
            return group_name
    # “Looks Tailwind-y”? (one of the core bare words)
    if class_name in {"container", "flex", "grid", "contents", "hidden"}:
        return "other (tailwind)"
    return None  # None means: user-defined
