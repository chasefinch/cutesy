"""Class sorting to accommodate the Tailwind CSS framework."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from typing import NamedTuple
from ..preprocessors import BasePreprocessor
from ..types import InstructionType, PreprocessingError, Rule

from . import BaseAttributeProcessor


DYNAMIC_LIST_ITEM_SENTINEL = "__LIST_ITEM_SENTINEL_A3VJ3FL__"


Rule("TW1", "Control instruction overlaps class names")


class TailwindClass(NamedTuple):
    """Class representation for Tailwind CSS."""

    class_name: str
    modifiers: list[str]
    full_string: str


class AttributeProcessor(BaseAttributeProcessor):
    """Sort classes according to the Tailwind style."""

    def process(
        self,
        attr_name: str,
        position: (int, int),
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        bounding_character: str,
        preprocessor: BasePreprocessor | None,
        attr_body: str,
    ) -> str:
        """Update the class attribute body with sorted classes."""
        if attr_name != "class":
            return attr_body

        adjusted_attr_body = attr_body.strip()
        class_names = adjusted_attr_body.split()
        stashed_class_names: list[list[str]] = []
        preprocessed_index_ranges: list[tuple(int, int)] = []
        current_preprocessed_index_range: tuple(int, int) = None
        if preprocessor:
            left, right = preprocessor.delimiters
            line, column = position

            # Ensure that there aren't mid-class instructions
            esc = re.escape
            start_set = "".join(esc(type_.value) for type_ in InstructionType.block_starts)
            end_set = "".join(esc(type_.value) for type_ in InstructionType.block_ends)

            # "Bad left": a LEFT that is not at start and not immediately after RIGHT,
            # *and* whose next char is in starting_chars.
            bad_left = rf'(?<!{esc(right)}){esc(left)}(?=[{start_set}])'

            # Bad RIGHT: in a segment that started with LEFT+ending_char,
            # and this RIGHT is not followed by LEFT and not at end of string
            bad_right = (
                rf'{esc(left)}[{end_set}][^{esc(right)}]*?'
                rf'{esc(right)}(?!{esc(left)}|$)'
            )

            raise_tw1 = any(
                re.search(bad_left, class_name[1:]) or re.search(bad_right, class_name)
                for class_name in class_names
            )

            class_names = expand_class_names(class_names, left, right, keep_empty=False)
            start_block_count = 0
            for index, class_name in enumerate(class_names):
                if class_name.startswith(left):
                    min_instruction_string_length = 4
                    assert(len(class_name) >= min_instruction_string_length)
                    instruction_type = InstructionType(class_name[1])
                    if instruction_type.starts_block:
                        start_block_count += 1
                    elif instruction_type.ends_block:
                        start_block_count -= 1

                if start_block_count < 0:
                    raise_tw1 - True

                if current_preprocessed_index_range:
                    current_preprocessed_index_range = (current_preprocessed_index_range[0], index + 1)
                    if not start_block_count:
                        preprocessed_index_ranges.append(current_preprocessed_index_range)
                        current_preprocessed_index_range = None
                elif start_block_count:
                    current_preprocessed_index_range = (index, index + 1)

            if current_preprocessed_index_range:
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
                # Do this after & in reverse order, b/c editing class_names
                stashed_class_names.append(class_names[index_range[0]:index_range[1]])
                class_names[index_range[0]:index_range[1]] = [f"{DYNAMIC_LIST_ITEM_SENTINEL}_{index}"]

            if preprocessed_index_ranges:
                print(class_names)

        max_single_line_classes = 5
        max_single_line_characters = 40
        single_line_mode = len(class_names) <= max_single_line_classes and len(adjusted_attr_body) <= max_single_line_characters

        classes = []
        for class_name in class_names:
            tailwind_class = parse_tailwind_class(class_name)
            classes.append(tailwind_class)

        sorted_classes = group_and_sort_tailwind(classes)
        if single_line_mode:
            all_class_names = []
            for class_list in sorted_classes:
                for tailwind_class in class_list:
                    line = tailwind_class.full_string
                    if line.startswith(DYNAMIC_LIST_ITEM_SENTINEL):
                        index = int(line.split('_')[-1])
                        all_class_names.extend(stashed_class_names.pop(index))
                    else:
                        all_class_names.append(line)

            return ' '.join(all_class_names)

        attribute_lines = [""]
        line_indentation = (current_indentation_level + 1) * indentation
        if len(sorted_classes) == 1:
            # Only one group, but long enough to merit multiple lines.
            for tailwind_class in sorted_classes[0]:
                line = tailwind_class.full_string
                if line.startswith(DYNAMIC_LIST_ITEM_SENTINEL):
                    index = int(line.split('_')[-1])
                    original_class_names = stashed_class_names.pop(index)
                    for class_name in original_class_names:
                        attribute_lines.append(f'{line_indentation}{class_name}')
                else:
                    attribute_lines.append(f'{line_indentation}{line}')
        else:
            for group in sorted_classes:
                class_names = []
                for tailwind_class in group:
                    line = tailwind_class.full_string
                    if line.startswith(DYNAMIC_LIST_ITEM_SENTINEL):
                        index = int(line.split('_')[-1])
                        original_class_names = stashed_class_names.pop(index)
                        for class_name in original_class_names:
                            class_names.append(f'{class_name}')
                    else:
                        class_names.append(line)
                joined_line = ' '.join(class_names)
                attribute_lines.append(f'{line_indentation}{joined_line}')

        attribute_lines.append(current_indentation_level * indentation)
        return '\n'.join(attribute_lines)


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
    out: List[str] = []

    for s in class_names:
        # If there are no delimited chunks, keep the string as-is.
        if not pattern.search(s):
            out.append(s)
            continue

        parts = pattern.split(s)  # keeps the delimited chunks in the result
        if not keep_empty:
            parts = [p for p in parts if p != ""]

        out.extend(parts)

    return out

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


# -------------------- Group definitions (order matters) -----------------------

GROUPS_IN_ORDER: list[tuple[str, Iterable[str]]] = [
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
]

_COMPILED: list[tuple[str, list[re.Pattern[str]]]] = [
    (name, [re.compile(rf"^{p}") for p in patterns]) for name, patterns in GROUPS_IN_ORDER
]

# Full group order we will emit
REAL_GROUPS_ORDER: tuple[str, ...] = tuple(name for name, _ in GROUPS_IN_ORDER)

# -------------------- Modifier ordering (relative lists) ----------------------

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


def _index_in(seq: tuple[str, ...], val: str, default: int) -> int:
    try:
        return seq.index(val)
    except ValueError:
        return default


def _modifier_key(mods: list[str]) -> tuple:
    """Build a tuple that sorts by the following criteria.

    - unmodified first (handled outside by flag),
    - then by responsive in RESP_ORDER sequence (left to right),
    - then by states in STATE_ORDER (left to right),
    - then arbitrary/unknown (kept in written order, used as tiebreak).
    """
    resp = tuple(_index_in(RESPONSIVE_ORDER, m, 999) for m in mods if m in RESPONSIVE_ORDER)
    state = tuple(_index_in(STATE_ORDER, m, 999) for m in mods if m in STATE_ORDER)
    # Anything not caught above: keep literal for stable compare
    other = tuple(m for m in mods if (m not in RESPONSIVE_ORDER and m not in STATE_ORDER))
    return (resp, state, other)


# -------------------- Intra-group ordering (simple, stable) -------------------

_SPACING_AXIS = ("x", "y")
_SPACING_SIDES = ("t", "r", "b", "l")


def _spacing_specificity(name: str) -> int:
    # p- / m- < px-/py-/mx-/my- < pt-/pr-/.../ml-
    if name.startswith(("p-", "m-")):
        return 0
    if any(name.startswith(f"p{a}-") or name.startswith(f"m{a}-") for a in _SPACING_AXIS):
        return 1
    if any(name.startswith(f"p{s}-") or name.startswith(f"m{s}-") for s in _SPACING_SIDES):
        return 2
    return 0


def _border_specificity(name: str) -> int:
    # border-* < border-x/y-* < border-t/r/b/l-* ; for rounded: rough by hyphen count
    if name.startswith("border-"):
        if any(name.startswith(f"border-{a}-") for a in _SPACING_AXIS):
            return 1
        if any(name.startswith(f"border-{s}-") for s in _SPACING_SIDES):
            return 2
        return 0
    if name.startswith("rounded-"):
        return name.count("-")
    return 0


def _family_key(group_name: str, class_name: str) -> tuple:
    """A cheap key so similar utilities cluster inside a group."""
    head = class_name.split("-", 1)[0]  # e.g., 'bg', 'text', 'p', 'border'
    if group_name == "spacing (margin/padding)":
        return (head, _spacing_specificity(class_name))
    if group_name == "borders/outline/radius/divide":
        return (head, _border_specificity(class_name))
    # generic: more segments → consider more specific
    return (head, class_name.count("-"))


def _intragroup_sort_key(group_name: str, item, original_index: int) -> tuple:
    """Unmodified first, then modifiers in consistent order, then name, then
    stable index.
    """
    base = item.class_name
    has_mods = 1 if item.modifiers else 0
    return (
        _family_key(group_name, base),
        has_mods,  # 0 (no mods) before 1 (has mods)
        _modifier_key(item.modifiers),
        base,
        original_index,
    )


# -------------------- Group finder & user-class placement ---------------------


def _find_group(class_name: str) -> str | None:
    for group_name, compiled_list in _COMPILED:
        if any(pat.match(class_name) for pat in compiled_list):
            return group_name
    # “Looks Tailwind-y”? (dash or one of the core bare words)
    if "-" in class_name or class_name in {"container", "flex", "grid", "contents", "hidden"}:
        return "other (tailwind)"
    return None  # None means: user-defined


def group_and_sort_tailwind(
    classes: list[TailwindClass],
) -> list[list[TailwindClass]]:
    """Returns a list of (group_name, [TailwindClass...]) where:

    • Real Tailwind groups appear in the fixed order defined above. • Each
    group’s items are sorted (unmodified → modified, then responsive/state
    order). • User classes are *not* mixed into groups; instead they are
    emitted as their own 'user-defined (after <group>)' bucket right *after*
    the preceding non-user group. User classes preserve their original order
    inside that bucket. • Any 'leading' user classes (before the first non-
    user) go to 'user-defined (leading)' at top.
    """
    # Buckets for real groups
    group_items: dict[str, list[tuple[int, object]]] = {g: [] for g in REAL_GROUPS_ORDER}
    group_items["other (tailwind)"] = []

    # Buckets for user classes after a given group, and leading users
    user_after: dict[str, list[object]] = defaultdict(list)
    leading_users: list[object] = []

    last_seen_real_group: str | None = None

    for idx, it in enumerate(classes):
        g = _find_group(it.class_name)
        if g is None:
            # user-defined: attach after last seen group, or to leading if none
            if last_seen_real_group is None:
                leading_users.append(it)
            else:
                user_after[last_seen_real_group].append(it)
        else:
            last_seen_real_group = g
            group_items[g].append((idx, it))  # keep original index for stability

    # Emit results
    out: list[tuple[str, list]] = []

    if leading_users:
        out.append(("user-defined (leading)", leading_users))

    for gname in REAL_GROUPS_ORDER + ("other (tailwind)",):
        if not group_items[gname]:
            # still may have user-after bucket even if empty group; if both empty, skip entirely
            if user_after.get(gname):
                # if the group is empty but users reference it, we still “honor” the place:
                out.append((gname, []))
                out.append((f"user-defined (after {gname})", user_after[gname]))
            continue

        # sort inside group (stable)
        sorted_group = sorted(
            group_items[gname],
            key=lambda pair: _intragroup_sort_key(gname, pair[1], pair[0]),
        )
        out.append((gname, [it for _, it in sorted_group]))

        # then any user classes that should appear after this group
        if user_after.get(gname):
            out.append((f"user-defined (after {gname})", user_after[gname]))

    return [out[1] for out in out]
