"""Trim whitespace inside of attributes where possible."""

import re

from ..preprocessors import BasePreprocessor
from ..rules import Rule
from ..types import Error
from . import BaseAttributeProcessor

# Match "..." or '...' with backslash escapes (no multiline strings)
STRING_RE = re.compile(
    r"""(?sx)
    ("(?:\\.|[^"\\])*")     # double-quoted string
  | ('(?:\\.|[^'\\])*')     # single-quoted string
""",
)

# 2+ horizontal whitespace, not touching \n, between non-whitespace chars
MIDDLE_WS_RUN = re.compile(r"(?<=\S)[^\S\n]{2,}(?=\S)")

# --- Encoded/escaped quote detection ----------------------------------------

# Safe encodings for a double quote (") that should NOT trigger a bail:
DOUBLE_QUOTE_SAFE_RE = re.compile(r"&quot;;?|&#34;;?|&#x22;;?|%22|\\u0022|\\x22", re.IGNORECASE)

# Safe encodings for a single quote / apostrophe (') that should NOT trigger a bail:
SINGLE_QUOTE_SAFE_RE = re.compile(r"&apos;;?|&#39;;?|&#x27;;?|%27|\\u0027|\\x27", re.IGNORECASE)


def has_inner_raw_bounding_quote(attr_body: str, bounding_character: str) -> bool:
    r"""Return True if attr_body contains a quote matching bounding_character.

    We first remove known *safe* encodings of that quote (entities, %XX,
    \uXXXX, \xXX) and then look for the literal quote. Backslash-escape
    (e.g. \") is NOT considered safe in HTML and will still contain a
    raw quote, so it will trigger a bail.
    """
    if bounding_character == '"':
        # Strip safe representations of double quotes so they don't confuse the check.
        stripped = DOUBLE_QUOTE_SAFE_RE.sub("", attr_body)
        return '"' in stripped
    if bounding_character == "'":
        stripped = SINGLE_QUOTE_SAFE_RE.sub("", attr_body)
        return "'" in stripped
    # Unexpected bounding char; be conservative.
    return True


def collapse_whitespace_outside_strings(string: str) -> str:
    """Collapse runs of 2+ horizontal whitespace to single spaces.

    Preserve whitespace inside string literals.
    """
    out = []
    pos = 0
    for match in STRING_RE.finditer(string):
        # process the gap before the string
        chunk = string[pos : match.start()]
        chunk = MIDDLE_WS_RUN.sub(" ", chunk)  # collapse to a single space
        out.append(chunk)

        # keep the string literal untouched
        out.append(match.group(0))
        pos = match.end()

    # tail after the last string
    tail = string[pos:]
    tail = MIDDLE_WS_RUN.sub(" ", tail)
    out.append(tail)

    return "".join(out)


class AttributeProcessor(BaseAttributeProcessor):
    """Trim whitespace inside of attributes where possible."""

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
    ) -> tuple[str, list[Error]]:
        """Trim excess whitespace, and adjust starting & ending whitespace.

        If we detect a raw inner quote that matches the
        bounding_character, we bail (return the original body unchanged)
        to avoid breaking the HTML.
        """
        self._errors: list[Error] = []
        self.position = position

        if solo:
            brackets_quotes_and_space_length = 5
            extra_char_length = brackets_quotes_and_space_length
            extra_char_length += len(attr_name)
            extra_char_length += tab_width * current_indentation_level
            max_first_line_length = line_length - extra_char_length

        # --- Safety check: bail if an inner raw quote matches the bounding char
        if has_inner_raw_bounding_quote(attr_body, bounding_character):
            rule_code = "F16"
            error = Error(
                line=position[0],
                column=position[1],
                rule=Rule.get(rule_code),
                replacements={"attr": attr_name},
            )
            self._errors.append(error)

            replacement = {'"': "&quot;", "'": "&apos;"}[bounding_character]
            attr_body = attr_body.replace(bounding_character, replacement)

        # Collapse 2+ middle-of-line spaces/tabs *outside* strings
        adjusted_body = collapse_whitespace_outside_strings(attr_body)

        must_wrap = len(adjusted_body.strip()) > max_first_line_length if solo else False
        multiline = must_wrap or "\n" in adjusted_body.strip()

        if multiline:
            if re.match(r"^[^\S\n]*\S", attr_body):
                adjusted_body = adjusted_body.strip()
                # The first line is on the same line as the opening quotes.
                # Trim the leading whitespace:
                adjusted_body = re.sub(r"^[^\S\n]*(\S)", r"\1", adjusted_body)

                # Trim the trailing whitespace, including newlines:
                adjusted_body = re.sub(r"\s*$", "", adjusted_body)

            else:
                # Replace the end string with the proper spaced newline
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
            # The only newlines were before or after all of the content. Trim them off.
            adjusted_body = re.sub(r"^\s*\n\s*", " ", adjusted_body)
            adjusted_body = re.sub(r"\s*\n\s*$", " ", adjusted_body)
            adjusted_body = adjusted_body.strip()

        return adjusted_body, self._errors

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
