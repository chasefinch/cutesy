"""Attribute processor for AMP HTML.

Runs after the default "attributes" processor in the chain, handling
only AMP-specific attributes (the base processor leaves them alone
since they're unknown to standard HTML).

AMP binding attributes (code content):
- [attr]="expression" syntax (e.g. [class], [src], [hidden], [text])
- data-amp-bind-attr="expression" (XHTML-compatible alternative)
  Values are AMP bind expressions.

AMP action attribute:
- on="tap:target.method" — uses AMP's action/event micro-syntax.
  Already handled by the base "attributes" processor via the "on"
  prefix in JS_ATTRIBUTE_PREFIXES.

AMP layout attribute:
- layout="responsive|fill|fixed|..." — enumerated, safe to strip.

AMP presence-only attributes (fallback, placeholder, noloading) have
no value, so the processor is never called for them.
"""

from ..preprocessors import BasePreprocessor
from ..types import Error
from .attributes import AttributeProcessor as _Base
from .whitespace import has_inner_raw_bounding_quote

_CODE_PREFIXES = ("[", "data-amp-bind-")
_STRIP_NAMES = frozenset(("layout",))


class AttributeProcessor(_Base):
    """Process AMP-specific attributes.

    Handles [*] and data-amp-bind-* attributes with code-content
    processing, and layout with strip processing. All other attributes
    pass through unchanged.
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
        """Process AMP attributes; pass others through."""
        is_code = any(attr_name.startswith(prefix) for prefix in _CODE_PREFIXES)
        is_strip = attr_name in _STRIP_NAMES

        if not is_code and not is_strip:
            return attr_body, []

        self._errors: list[Error] = []
        self.position = position

        if has_inner_raw_bounding_quote(attr_body, bounding_character):
            self._handle_error("F16", attr=attr_name)
            replacement = {'"': "&quot;", "'": "&apos;"}[bounding_character]
            attr_body = attr_body.replace(bounding_character, replacement)

        if is_strip:
            return attr_body.strip(), self._errors

        return self._process_code(
            attr_name,
            attr_body,
            indentation,
            current_indentation_level,
            tab_width,
            line_length,
            solo=solo,
        )
