"""Class sorting to accommodate the Tailwind CSS framework."""

from __future__ import annotations

import re

# add at top with your other imports
from collections import OrderedDict
from functools import partial
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, NamedTuple, TypeAlias

from .types import BaseClassOrderingAttributeProcessor

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


StashItem: TypeAlias = "str | list[StashItem]"

StackNode: TypeAlias = list["int | StackNode"]

IndexRangeNode: TypeAlias = list["int | IndexRangeNode"]


class TailwindClass(NamedTuple):
    """Class representation for Tailwind CSS."""

    class_name: str
    modifiers: list[str]
    full_string: str


class AttributeProcessor(BaseClassOrderingAttributeProcessor):
    """Sort classes according to the Tailwind style."""

    def sort(
        self,
        class_names: list[str],
        *,
        grouped: bool = False,
    ) -> list[str] | list[list[str]]:
        """Sort the given list of class names."""
        groups = group_and_sort(class_names)
        if grouped:
            return groups
        return [class_name for group in groups for class_name in group]


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

    modifiers, base = parts[:-1], parts[-1].removeprefix("-")

    return TailwindClass(
        class_name=base,
        modifiers=modifiers,
        full_string=full,
    )


GROUPS_IN_ORDER: Sequence[tuple[str, Sequence[str]]] = (
    (
        "position/float",
        (
            r"(?:static|fixed|absolute|relative|sticky)",
            r"(?:float-|clear-)",
            r"(?:z-|isolation|inset-|top-|right-|bottom-|left-)",
        ),
    ),
    (
        "flex/grid core",
        (
            r"(?:container|block|inline|inline-block|inline-flex|flex|grid|contents|hidden)",
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
            r"(?:columns-)",
            r"(?:gap-|space-[xy]-)",
        ),
    ),
    (
        "spacing (margin/padding)",
        (
            r"(?:m[trblxyse]?-\S+)",
            r"(?:p[trblxyse]?-\S+)",
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
        "object/overflow",
        (
            r"(?:object-)",
            r"(?:overflow-)",
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
    ("svg", (r"(?:fill-|stroke-)",)),
    ("transforms", (r"(?:transform|scale-|rotate-|translate-|skew-)",)),
    ("transitions/animation", (r"(?:transition|duration-|ease-|delay-|animate-)",)),
    (
        "interactivity/behavior",
        (r"(?:cursor-|select-|pointer-events-|touch-|scroll-|overscroll-|snap-)",),
    ),
    ("accessibility", (r"(?:sr-only|not-sr-only)",)),
)

_COMPILED: Final[tuple[tuple[str, list[re.Pattern[str]]], ...]] = tuple(
    (name, [re.compile(rf"^{pattern}") for pattern in patterns])
    for name, patterns in GROUPS_IN_ORDER
)

# Helper to find arbitrary descendant/sibling selectors
_ARBITRARY_SELECTOR_RE = re.compile(r"^\[(?P<inner>[^]]+)\]$", re.VERBOSE)

# Full group order we will emit
REAL_GROUPS_ORDER: Final[tuple[str, ...]] = tuple(name for name, _ in GROUPS_IN_ORDER)

_group_rank_dict: dict[str, int] = {name: rank for rank, name in enumerate(REAL_GROUPS_ORDER)}
_group_rank_dict["other (tailwind)"] = len(REAL_GROUPS_ORDER)
_GROUP_RANK: Final[Mapping[str, int]] = MappingProxyType(_group_rank_dict)

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


def group_and_sort(class_names: list[str]) -> list[list[str]]:
    """Return groups of tailwind class strings in fixed order.

    All user-defined classes will be collected into one final bucket at the
    bottom (preserving original order).

    Real Tailwind groups appear in REAL_GROUPS_ORDER, then "other (tailwind)",
    sorted by _intragroup_sort_key.

    Arbitrary selector variants (e.g., "[&>*]") each get their own bucket,
    keyed by the exact modifier string, and are emitted after the above groups.

    Arbitrary selectors that still target the same element (e.g., "[&]" with
    any underscores) are treated normally (not split out).

    User-defined classes (not recognized as Tailwind) are not mixed into
    groups; they are emitted as one final list at the end, in original order.
    """
    # Buckets for real groups (track original index for stable sort)
    group_items: dict[str, list[tuple[int, TailwindClass]]] = {
        group: [] for group in REAL_GROUPS_ORDER
    }
    group_items["other (tailwind)"] = []

    # One bucket per arbitrary selector modifier; preserve first-seen order
    arbitrary_selector_groups: OrderedDict[str, list[tuple[int, TailwindClass]]] = OrderedDict()

    # Single bucket for all user-defined classes (preserve original order)
    user_defined: list[str] = []

    # Create TailwindClass instances
    classes = []
    for class_name in class_names:
        tailwind_class = parse_tailwind_class(class_name)
        classes.append(tailwind_class)

    # Partition
    for index, tailwind_class in enumerate(classes):
        arbitrary_modifier = next(
            (
                modifier
                for modifier in tailwind_class.modifiers
                if _is_arbitrary_selector_variant(modifier)
            ),
            None,
        )
        if arbitrary_modifier is not None:
            arbitrary_selector_groups.setdefault(arbitrary_modifier, []).append(
                (index, tailwind_class),
            )
            continue

        group = _find_group(tailwind_class.class_name)
        if group is None:
            user_defined.append(tailwind_class.full_string)
        else:
            group_items[group].append((index, tailwind_class))

    # Emit results as a list of lists (group contents only)
    out: list[list[str]] = []

    # Real groups in fixed order, then "other (tailwind)"
    for group_name in (*REAL_GROUPS_ORDER, "other (tailwind)"):
        if not group_items[group_name]:
            continue
        key_function = partial(_group_sort_key, group_name=group_name)
        sorted_group = sorted(group_items[group_name], key=key_function)
        out.append([item[1].full_string for item in sorted_group])

    # Then each arbitrary selector group (in first-seen order)
    for items in arbitrary_selector_groups.values():
        sorted_group = sorted(items, key=_arbitrary_selector_key)
        out.append([item[1].full_string for item in sorted_group])

    # Finally, all user-defined classes at the bottom (original order)
    if user_defined:
        out.append(user_defined)

    return out


# Loop, sort, and parse helpers -----------------------------------------------


_RESPONSIVE_ORDER_INDEX: Final = MappingProxyType(
    {modifier: index for index, modifier in enumerate(RESPONSIVE_ORDER)},
)
_STATE_ORDER_INDEX: Final = MappingProxyType(
    {modifier: index for index, modifier in enumerate(STATE_ORDER)},
)


def _modifier_key(
    modifiers: list[str],
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[str, ...]]:
    """Sort by responsive order, then state order, then literal (stable)."""
    responsive = tuple(
        _RESPONSIVE_ORDER_INDEX[modifier]
        for modifier in modifiers
        if modifier in _RESPONSIVE_ORDER_INDEX
    )
    state = tuple(
        _STATE_ORDER_INDEX[modifier] for modifier in modifiers if modifier in _STATE_ORDER_INDEX
    )
    other = tuple(
        modifier
        for modifier in modifiers
        if modifier not in _RESPONSIVE_ORDER_INDEX and modifier not in _STATE_ORDER_INDEX
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
    # Generic: More segments → consider more specific
    return (head, class_name.count("-"))


def _group_sort_key(pair: tuple[int, TailwindClass], group_name: str) -> tuple:
    original_index, item = pair
    return _intragroup_sort_key(group_name, item, original_index)


def _intragroup_sort_key(group_name: str, item: TailwindClass, original_index: int) -> tuple:
    """Sort within a group.

    Unmodified first, then modifiers in consistent order, then name, then
    stable index.
    """
    has_modifiers = bool(item.modifiers)
    base = item.class_name
    return (
        _family_key(group_name, base),
        has_modifiers,  # False (no modifiers) before True (has modifiers)
        _modifier_key(item.modifiers),
        base,
        original_index,
    )


def _find_group(class_name: str) -> str | None:
    # BEM heuristic, but ignore arbitrary payloads inside [...] or (...)
    # e.g., mt-[var(--x)] should NOT be rejected because of "--" inside brackets.
    outside = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", class_name)
    if "--" in outside or "__" in outside:
        return None  # user-defined
    for group_name, compiled_list in _COMPILED:
        if any(pat.match(class_name) for pat in compiled_list):
            return group_name
    # “Looks Tailwind-y”? (one of the core bare words)
    if class_name in {"container", "flex", "grid", "contents", "hidden"}:
        return "other (tailwind)"
    return None  # None means: user-defined


def _is_arbitrary_selector_variant(modifier: str) -> bool:
    """Return whether a modifier is a descendant selector.

    True if modifier is like "[&...]" (underscores allowed around '&')
    and is NOT the self-selector "[&]" (with any underscore placement).
    """
    match = _ARBITRARY_SELECTOR_RE.match(modifier)
    if not match:
        return False

    inner = match.group("inner")
    stripped = inner.replace("_", "")
    if not stripped.startswith("&"):
        return False

    # exclude the self selector
    return stripped != "&"


_OTHER_GROUP: Final[str] = "other (tailwind)"


def _arbitrary_selector_key(pair: tuple[int, TailwindClass]) -> tuple:
    original_index, tailwind_class = pair
    base_group = _find_group(tailwind_class.class_name) or _OTHER_GROUP
    rank = _GROUP_RANK.get(base_group, _GROUP_RANK[_OTHER_GROUP])
    # Use the base group's name so spacing/border heuristics match normal grouping.
    return (rank, _intragroup_sort_key(base_group, tailwind_class, original_index))
