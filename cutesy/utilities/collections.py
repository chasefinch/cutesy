"""Collection utilities for Cutesy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


def collapse(iterable: Iterable[Any], base_type: type | None = None) -> Generator[Any, None, None]:
    """Flatten nested iterables, similar to more_itertools.collapse."""
    for item in iterable:
        if base_type and isinstance(item, base_type):
            yield item
        elif hasattr(item, "__iter__") and not isinstance(item, (str, bytes)):
            yield from collapse(item, base_type)
        else:
            yield item
