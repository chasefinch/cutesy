"""Attribute processor for Alpine.js directives.

Runs after the default "attributes" processor in the chain, handling
only Alpine.js-specific attributes (the base processor leaves them
alone since they're unknown to standard HTML).

Alpine.js directives processed as code content (JS expressions):
- x-data, x-init, x-show, x-bind, x-on, x-text, x-html, x-model,
  x-modelable, x-for, x-if, x-effect, x-id, x-intersect, x-trap,
  x-anchor, x-resize, x-sort, x-mask:dynamic, etc.
- @event shorthands (x-on:event)
- :attr shorthands (x-bind:attr)

Non-expression directives (x-ref, x-cloak, x-ignore, x-teleport,
x-transition, x-mask, x-collapse) either have no value (presence-only,
so the processor is never called) or contain simple strings where
whitespace collapsing is harmless.
"""

from ..preprocessors import BasePreprocessor
from ..types import Error
from .attributes import AttributeProcessor as _Base
from .whitespace import has_inner_raw_bounding_quote

_CODE_PREFIXES = ("x-", "@", ":")


class AttributeProcessor(_Base):
    """Process Alpine.js directive attributes.

    Handles x-*, @*, and :* attributes with code-content processing
    (whitespace collapse + reindent). All other attributes pass through
    unchanged for the base "attributes" processor to handle.
    """

    def process(
        self,
        attr_name: str,
        position: tuple[int, int],
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        line_length: int,
        max_items_per_line: int,
        bounding_character: str,
        preprocessor: BasePreprocessor | None,
        attr_body: str,
        *,
        solo: bool = False,
    ) -> tuple[str | None, list[Error]]:
        """Process Alpine.js attributes; pass others through."""
        if not any(attr_name.startswith(prefix) for prefix in _CODE_PREFIXES):
            return attr_body, []

        self._errors: list[Error] = []
        self.position = position

        if has_inner_raw_bounding_quote(attr_body, bounding_character):
            self._handle_error("F16", attr=attr_name)
            replacement = {'"': "&quot;", "'": "&apos;"}[bounding_character]
            attr_body = attr_body.replace(bounding_character, replacement)

        return self._process_code(
            attr_name,
            attr_body,
            indentation,
            current_indentation_level,
            tab_width,
            line_length,
            solo=solo,
        )
