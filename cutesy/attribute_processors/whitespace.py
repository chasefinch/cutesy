"""Trim whitespace inside of attributes where possible."""

import re

from . import BaseAttributeProcessor

# Match "..." or '...' with escapes (no multiline strings)
STRING_RE = re.compile(
    r"""(?sx)
    ("(?:\\.|[^"\\])*")     # double-quoted string
  | ('(?:\\.|[^'\\])*')     # single-quoted string
""",
)

# 2+ horizontal whitespace, not touching \n, between non-whitespace chars
MIDDLE_WS_RUN = re.compile(r"(?<=\S)[^\S\n]{2,}(?=\S)")


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
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        bounding_character: str,
        attr_body: str,
    ) -> str:
        """Trim excess whitespace, and adjust starting & ending whitespace."""
        adjusted_body = attr_body

        if "\n" in attr_body.strip():
            if re.match(r"^[^\S\n]*\S", attr_body):
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

            # Finally: collapse 2+ middle-of-line spaces/tabs *outside* strings
            adjusted_body = collapse_whitespace_outside_strings(adjusted_body)
        else:
            # The only newlines were before or after all of the content. Trim
            # them off.
            adjusted_body = re.sub(r"^\s*\n\s*", " ", adjusted_body)
            adjusted_body = re.sub(r"\s*\n\s*$", " ", adjusted_body)
            adjusted_body = adjusted_body.strip()
        return adjusted_body
