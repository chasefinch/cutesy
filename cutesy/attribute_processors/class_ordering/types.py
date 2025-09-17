"""Class sorting to accommodate the Tailwind CSS framework."""

from __future__ import annotations

import re
from abc import abstractmethod

# add at top with your other imports
from typing import TYPE_CHECKING, TypeAlias, cast

from more_itertools import collapse

from ...rules import Rule
from ...types import Error, InstructionType
from .. import BaseAttributeProcessor

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ..preprocessors import BasePreprocessor


DYNAMIC_LIST_ITEM_SENTINEL = "__LIST_ITEM_SENTINEL_A3VJ3FL__"


Rule("TW1", "Control instruction overlaps class names")


StashItem: TypeAlias = "str | list[StashItem]"

StackNode: TypeAlias = list["int | StackNode"]

IndexRangeNode: TypeAlias = list["int | IndexRangeNode"]


class BaseClassOrderingAttributeProcessor(BaseAttributeProcessor):
    """Sort classes."""

    stashed_class_names: list[StashItem]

    @abstractmethod
    def sort(
        self,
        class_names: list[str],
        *,
        grouped: bool = False,
    ) -> list[str] | list[list[str]]:
        """Sort the given list of class names."""

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
    ) -> tuple[str, list[Error]]:
        """Update the class attribute body with sorted classes."""
        errors: list[Error] = []
        if attr_name != "class":
            return attr_body, errors

        self.indentation = indentation
        self.preprocessor = preprocessor

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
            block_starts = InstructionType.block_starts
            block_ends = InstructionType.block_ends
            start_set = "".join(esc(type_.value) for type_ in block_starts)
            end_set = "".join(esc(type_.value) for type_ in block_ends)

            # "Bad left": a LEFT that is not at start and not immediately after
            # RIGHT or space, *and* whose next char is in starting_chars.
            bad_left = rf"(?<!{esc(right)}| ){esc(left)}(?=[{start_set}])"

            # Bad RIGHT: in a segment that started with LEFT+ending_char,
            # and this RIGHT is not followed by LEFT or a space, and not at end
            # of string
            bad_right = (
                rf"{esc(left)}[{end_set}][^{esc(right)}]*?"
                rf"{esc(right)}(?!{esc(left)}|$| )"
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
                class_names, stash = self._extract_with_sentinel(
                    class_names,
                    index_range,
                    sentinel,
                )
                self.stashed_class_names.append(stash)

        sorted_class_groups = cast("list[list[str]]", self.sort(class_names, grouped=True))
        sorted_class_group_tree = self._hydrate_class_groups(sorted_class_groups)
        all_class_names = list(collapse(sorted_class_group_tree, base_type=str))
        all_class_names_on_one_line = " ".join(all_class_names)

        max_attr_chars_per_line = self.max_length - len('class=""')
        single_line_mode = (
            len(all_class_names) <= max_items_per_line
            and len(all_class_names_on_one_line) <= max_attr_chars_per_line
        )

        if single_line_mode:
            return all_class_names_on_one_line, errors

        # Multi-line modes...
        attribute_lines = [""]
        line_indentation = (current_indentation_level + 1) * indentation

        # ...#1: One group, but long enough to merit multiple lines.
        if len(sorted_class_group_tree) == 1:
            # Only one group, but long enough to merit multiple lines.
            for group_entry in sorted_class_group_tree[0]:
                lines = self._extract_columns_and_lines(group_entry)
                for column_index, line_value in lines:
                    extra_indentation = indentation * column_index
                    attribute_lines.append(f"{line_indentation}{extra_indentation}{line_value}")

        else:
            for group in sorted_class_group_tree:
                if all(isinstance(item, str) for item in group):
                    group_line = " ".join([str(item) for item in group])
                    group_line = f"{line_indentation}{group_line}"
                    if len(group_line) <= self.max_length:
                        attribute_lines.append(group_line)
                    else:
                        group_lines = [f"{line_indentation}{item!s}" for item in group]
                        attribute_lines.extend(group_lines)
                else:
                    for multi_group_entry in group:
                        lines = self._extract_columns_and_lines(multi_group_entry)
                        for column_index, line_value in lines:
                            extra_indentation = indentation * column_index
                            attribute_lines.append(
                                f"{line_indentation}{extra_indentation}{line_value}",
                            )
        # Add the final line
        attribute_lines.append(current_indentation_level * indentation)
        return "\n".join(attribute_lines), errors

    def _extract_with_sentinel(
        self,
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

        stash = self._build_stash(class_names, index_tree)
        new_class_names = [*class_names[:start], sentinel, *class_names[end:]]
        return new_class_names, stash

    def _build_stash(self, class_names: list[str], tree: list) -> list[StashItem]:
        """Build a nested stash.

        Sort each contiguous run of non-control items between control items.
        Controls:
        - nested block (a list like [start, ..., end])
        - scalar index representing a block continuation character

        First and last items at this level must never be sorted.
        """
        start = tree[0]
        end = tree[-1]
        interior = tree[1:-1]

        stash: list[StashItem] = []
        buffer: list[str] = []
        cursor = start

        for child in interior:
            if isinstance(child, int):
                name = class_names[child]
                if self.preprocessor and name.startswith(self.preprocessor.delimiters[0]):
                    min_instruction_string_length = 4
                    assert len(name) >= min_instruction_string_length
                    instruction_type = InstructionType(name[1])

                    # FIX #2: call the predicate
                    if instruction_type.continues_block:
                        # FIX #1: capture the segment BEFORE this scalar control
                        buffer.extend(class_names[cursor:child])

                        # Flush preceding run, protecting head if nothing has been emitted yet
                        self._emit_sorted_run(buffer, stash, protect_head=(len(stash) == 0))

                        # Emit the control itself
                        stash.append(name)
                        cursor = child + 1

                # Non-control scalar: keep accumulating; will be flushed later.
                continue

            # Child is a nested block (control)
            child_start = child[0]
            child_end = child[-1]

            # Capture & flush the segment before the child block
            buffer.extend(class_names[cursor:child_start])
            self._emit_sorted_run(buffer, stash, protect_head=(len(stash) == 0))

            # Recurse; child sorts internally but remains atomic here
            stash.append(self._build_stash(class_names, child))
            cursor = child_end

        # Tail (after last interior up to end). Always protect the tail item.
        buffer.extend(class_names[cursor:end])
        self._emit_sorted_run(
            buffer,
            stash,
            protect_head=(len(stash) == 0),  # no controls at all -> protect both ends
            protect_tail=True,
        )

        return stash

    def _emit_sorted_run(
        self,
        buffer: list[str],
        stash: list[StashItem],
        *,
        protect_head: bool = False,
        protect_tail: bool = False,
    ) -> None:
        """Emit a buffered run into `stash`.

        Keeping optional head/tail items unsorted.
        - If protect_head: keep buffer[0] unsorted as the first emitted item.
        - If protect_tail: keep the last remaining element unsorted as the last
          emitted item.
        - The middle (whatever remains) is sorted via _sort_run.
        """
        if not buffer:
            return

        head_item: str | None = None
        tail_item: str | None = None

        if protect_head and buffer:
            head_item = buffer.pop(0)

        if protect_tail and buffer:
            tail_item = buffer.pop()  # from what remains after head pop

        middle_sorted = cast("list[str]", self.sort(buffer))

        if head_item is not None:
            stash.append(head_item)
        if middle_sorted:
            stash.extend(middle_sorted)
        if tail_item is not None:
            stash.append(tail_item)

        buffer.clear()  # explicit; caller reuses the same list

    def _hydrate_class_groups(self, class_groups: list[list[str]]) -> list[list[StashItem]]:
        """Hydrate a stash into a list of class groups."""
        if not class_groups:
            return []

        hydrated_class_groups: list[list[StashItem]] = [
            [item for item in group] for group in class_groups[:-1]
        ]
        hydrated_class_entries: list[StashItem] = []
        for user_defined_item in class_groups[-1]:
            if user_defined_item.startswith(DYNAMIC_LIST_ITEM_SENTINEL):
                index = int(user_defined_item.split("_")[-1])
                flattened = self._flatten_stash(self.stashed_class_names.pop(index))
                hydrated_class_entries.append(flattened)
            else:
                hydrated_class_entries.append(user_defined_item)
        hydrated_class_groups.append(hydrated_class_entries)
        return hydrated_class_groups

    def _flatten_stash(self, stash: str | Sequence[StashItem]) -> str | list[StashItem]:
        """Normalize `stash` without crossing control boundaries.

        Child lists are atomic at their parent level (controls). We may flatten
        *inside* a child, but we never splice its contents into the parent.

        If (and only if) every item at the current level is a string, we may
        compact to a one-liner with special spacing rules:
        - No space between first & second items
        - No space between second-to-last & last items
        - Single space between everything else
        - Otherwise return a list[StashItem] preserving child lists in place.
        """
        if isinstance(stash, str):
            return stash

        # Recurse into children but keep each child atomic at this level.
        normalized: list[StashItem] = []
        for item in stash:
            if isinstance(item, str):
                normalized.append(item)
            else:
                child = self._flatten_stash(item)
                normalized.append(child)  # keep child as a single token

        # If everything at this level is a string, consider one-line compaction
        all_strings = all(isinstance(normalized_item, str) for normalized_item in normalized)
        if all_strings:
            if len(normalized) == 1:
                return normalized[0]  # single string

            if len(normalized) <= self.max_items_per_line:
                # Join and fix spaces around delimiters
                pieces = [str(normalized_item) for normalized_item in normalized]
                candidate = " ".join(pieces)

                assert self.preprocessor  # required for delimiters
                left_raw, right_raw = self.preprocessor.delimiters
                left, right = re.escape(left_raw), re.escape(right_raw)

                # Remove space immediately after left delimiter and before right delimiter
                candidate = re.sub(rf" {left}", left, candidate)
                candidate = re.sub(rf"{right} ", right, candidate)

                if len(candidate) <= self.max_length:
                    return candidate

        # Could not compact; return the sequence with children preserved in place.
        return normalized

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

        # Reduce effective column by one for "continuation" items
        effective_column = column
        if self.preprocessor and item.startswith(self.preprocessor.delimiters[0]):
            min_instruction_string_length = 4
            assert len(item) >= min_instruction_string_length
            instruction_type = InstructionType(item[1])
            if instruction_type.continues_block:
                effective_column -= 1

        return [(effective_column, item)]


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
        class_names = ["{% if tuna %}btn--lg{% else %}btn--sm{% endif %} shadow", "card"]
        left, right = "{", "}"
        -> ["{% if tuna %}", "btn--lg", "{% else %}", "btn--sm", "{% endif %}", "shadow", "card"]

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
