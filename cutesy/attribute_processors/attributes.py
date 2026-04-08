"""Attribute processor that dispatches based on attribute type knowledge.

Replaces the separate 'whitespace' and 'reindent' processors with a
single processor that applies type-appropriate handling to each
attribute.
"""

import re
from collections.abc import Iterable
from typing import ClassVar

from ..preprocessors import BasePreprocessor
from ..rules import Rule
from ..types import Error
from . import BaseAttributeProcessor
from .constants import (
    CODE_CONTENT_ATTRIBUTES,
    ENUMERATED_ATTRIBUTES,
    JS_ATTRIBUTE_PREFIXES,
    NUMERIC_ATTRIBUTES,
    PRESENCE_ATTRIBUTES,
    TOKEN_ATTRIBUTES,
)
from .whitespace import (
    collapse_whitespace_outside_strings,
    has_inner_raw_bounding_quote,
)

# Token + code-content attributes are meaningless when empty
_REMOVABLE_WHEN_EMPTY: frozenset[str] = TOKEN_ATTRIBUTES | CODE_CONTENT_ATTRIBUTES


class AttributeProcessor(BaseAttributeProcessor):
    """Process attributes based on their semantic type.

    Attribute types and their processing:
    - Token lists (class, rel, etc.): Normalize whitespace, format/wrap tokens
    - Code content (on*, style): Whitespace collapse + reindent
    - Numeric/enumerated/presence: Strip surrounding whitespace
    - Unknown: Leave completely alone

    Plugins can register additional attributes/prefixes for code-content
    processing via register_code_content_processing().
    """

    _extra_code_names: ClassVar[set[str]] = set()
    _extra_code_prefixes: ClassVar[set[str]] = set()

    @classmethod
    def register_code_content_processing(
        cls,
        *,
        names: Iterable[str] = (),
        prefixes: Iterable[str] = (),
    ) -> None:
        """Register attribute names/prefixes for code-content processing.

        Code-content attributes get whitespace collapsing and
        reindentation, the same treatment as on* event handlers and
        style.
        """
        cls._extra_code_names.update(names)
        cls._extra_code_prefixes.update(prefixes)

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
        """Process an attribute value based on its semantic type."""
        self._errors: list[Error] = []
        self.position = position

        # Classify
        is_token = attr_name in TOKEN_ATTRIBUTES
        is_code = not is_token and self._is_code_content(attr_name)
        is_strip = (
            not is_token
            and not is_code
            and (
                attr_name in NUMERIC_ATTRIBUTES
                or attr_name in ENUMERATED_ATTRIBUTES
                or attr_name in PRESENCE_ATTRIBUTES
            )
        )

        if not is_token and not is_code and not is_strip:
            return attr_body, self._errors

        # Common safety check: raw bounding quote inside value (F16)
        if has_inner_raw_bounding_quote(attr_body, bounding_character):
            self._handle_error("F16", attr=attr_name)
            replacement = {'"': "&quot;", "'": "&apos;"}[bounding_character]
            attr_body = attr_body.replace(bounding_character, replacement)

        if is_token:
            return self._process_token(
                attr_name,
                attr_body,
                indentation,
                current_indentation_level,
                tab_width,
                line_length,
                max_items_per_line,
            )

        if is_code:
            return self._process_code(
                attr_name,
                attr_body,
                indentation,
                current_indentation_level,
                tab_width,
                line_length,
                solo=solo,
            )

        # is_strip
        return attr_body.strip(), self._errors

    def _is_code_content(self, attr_name: str) -> bool:
        """Check if an attribute should get code-content processing."""
        if attr_name in CODE_CONTENT_ATTRIBUTES or attr_name in self._extra_code_names:
            return True
        all_prefixes = (*JS_ATTRIBUTE_PREFIXES, *self._extra_code_prefixes)
        return any(attr_name.startswith(prefix) for prefix in all_prefixes)

    def _process_token(
        self,
        attr_name: str,
        attr_body: str,
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        line_length: int,
        max_items_per_line: int,
    ) -> tuple[str | None, list[Error]]:
        """Process a token-list attribute (class, rel, sizes, etc.).

        Normalizes whitespace between tokens and formats as single-line
        or multiline based on token count and line length (same approach
        as the tailwind class processor).
        """
        tokens = attr_body.split()

        if not tokens:
            return None, self._errors

        one_line = " ".join(tokens)

        # Available width: same calculation as the tailwind class processor
        max_length = line_length - ((current_indentation_level + 1) * tab_width)
        attr_overhead = len(attr_name) + len('=""')
        max_attr_chars = max_length - attr_overhead

        if len(tokens) <= max_items_per_line and len(one_line) <= max_attr_chars:
            return one_line, self._errors

        # Multi-line: each token on its own indented line
        line_indent = indentation * (current_indentation_level + 1)
        lines = [""]  # Empty first line (newline after opening quote)
        lines.extend(f"{line_indent}{token}" for token in tokens)
        lines.append(indentation * current_indentation_level)
        return "\n".join(lines), self._errors

    def _process_code(
        self,
        attr_name: str,
        attr_body: str,
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        line_length: int,
        *,
        solo: bool = False,
    ) -> tuple[str | None, list[Error]]:
        """Process a code-content attribute (on*, style).

        Combines whitespace collapsing with reindentation.
        """
        # --- Whitespace phase ---

        max_first_line_length = 0
        if solo:
            brackets_quotes_and_space_length = 5
            extra_char_length = brackets_quotes_and_space_length
            extra_char_length += len(attr_name)
            extra_char_length += tab_width * current_indentation_level
            max_first_line_length = line_length - extra_char_length

        # Collapse 2+ middle-of-line spaces/tabs outside strings
        adjusted_body = collapse_whitespace_outside_strings(attr_body)

        must_wrap = len(adjusted_body.strip()) > max_first_line_length if solo else False
        multiline = must_wrap or "\n" in adjusted_body.strip()

        if multiline:
            if re.match(r"^[^\S\n]*\S", attr_body):
                adjusted_body = adjusted_body.strip()
                # Trim leading whitespace:
                adjusted_body = re.sub(r"^[^\S\n]*(\S)", r"\1", adjusted_body)
                # Trim trailing whitespace, including newlines:
                adjusted_body = re.sub(r"\s*$", "", adjusted_body)
            else:
                # Replace the end with the proper spaced newline
                end_string = "".join(("\n", indentation * current_indentation_level))
                adjusted_body = re.sub(r"(\S)\s*$", rf"\1{end_string}", adjusted_body)

            # Replace triple-or-more newlines with double newlines
            adjusted_body = re.sub(r"(?:[^\S\n]*\r?\n){2,}", r"\n\n", adjusted_body)

            # Replace first-line and last-line trailing newlines
            adjusted_body = re.sub(r"^(?:\n[^\S\n]*){2,}", r"\n\n", adjusted_body)
            adjusted_body = re.sub(r"(?:[^\S\n]*\n)+([^\S\n]*)$", r"\n\1", adjusted_body)

            # Trim trailing whitespace on each line
            adjusted_body = re.sub(r"[^\S\n]+\n", r"\n", adjusted_body)
        else:
            adjusted_body = re.sub(r"^\s*\n\s*", " ", adjusted_body)
            adjusted_body = re.sub(r"\s*\n\s*$", " ", adjusted_body)
            adjusted_body = adjusted_body.strip()

        # --- Reindent phase ---
        if "\n" in adjusted_body:
            adjusted_body = self._reindent(
                adjusted_body,
                indentation,
                current_indentation_level,
                tab_width,
            )

        # Empty code content → remove the attribute
        if not adjusted_body.strip() and attr_name in _REMOVABLE_WHEN_EMPTY:
            return None, self._errors

        return adjusted_body, self._errors

    def _reindent(
        self,
        body: str,
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
    ) -> str:
        """Reindent multiline content according to outer context."""
        indentation_strings = (" " * tab_width, "\t")

        adjusted_body = re.sub(r"^[^\S\n]*(\S|\n)", r"\1", body)
        if "\n" not in adjusted_body:
            return adjusted_body

        lines = adjusted_body.split("\n")

        indentation_and_lines: list[tuple[int, str]] = []
        for line in lines:
            num_indents = 0
            i = 0
            while any(line[i:].startswith(string) for string in indentation_strings):
                num_indents += 1
                if line[i:].startswith(" "):
                    i += tab_width
                else:
                    i += 1
            indentation_and_lines.append((num_indents, line.strip()))

        # Drop the first & last line for this calculation
        lines_with_content = [
            line_info for line_info in indentation_and_lines[1:-1] if line_info[1]
        ]

        if lines_with_content:
            min_indents = min(line_info[0] for line_info in lines_with_content)
        else:
            # The last line was the only line with content; use its offset
            min_indents = indentation_and_lines[-1][0]

        indented_lines = [indentation_and_lines[0][1]]
        for line_info in indentation_and_lines[1:]:
            line_content = line_info[1]
            if line_content:
                num_relative_indents = line_info[0] - min_indents
                line_indentation = indentation * (
                    current_indentation_level + 1 + num_relative_indents
                )
                indented_lines.append(f"{line_indentation}{line_content}")
            else:
                indented_lines.append("")
        if indented_lines[-1] == "":
            indented_lines[-1] = indentation * current_indentation_level

        return "\n".join(indented_lines)

    def _handle_error(self, rule_code: str, **replacements: str) -> None:
        line, column = self.position
        self._errors.append(
            Error(
                line=line,
                column=column,
                rule=Rule.get(rule_code),
                replacements=replacements,
            ),
        )
