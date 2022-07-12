"""Prerendering to accommodate template languages."""

# Standard Library
import re
import unicodedata
from abc import ABC

# Cutesy
from utilities.base36 import base36_encode

# Current App
from .. import Error, InstructionType, PreprocessingError, Rule

SPECIAL_CHARS = frozenset(
    (
        " ",
        "&",
        "<",
        ">",
        "'",
        '"',
        "/",
        "#",
        "=",
        ".",
        "?",
        "!",
        " ",
        " ",  # Non-breaking space
        "­",  # Soft hyphen
        "​",  # Zero-width space
    ),
)


CLEAN_CHARS_BEFORE_OPENING = frozenset(
    (
        ">",
        " ",
        "\t",
        "\n",
        "\r",
    ),
)

CLEAN_CHARS_AFTER_CLOSING = frozenset(
    (
        ">",
        "<",
        " ",
        "\t",
        "\n",
        "\r",
    ),
)


class SetupError(Exception):
    """An error that can be thrown when the preprocessor isn’t ready."""


class BasePreprocessor(ABC):
    """A base class for preprocessors.

    Preprocessors should choose placeholders that would trigger a dynamic
    instruction in the associated template language, so that they don’t
    inadvertently get tripped up by static parts of the HTML.
    """

    # Must not start with < or &
    braces = {
        ("{%", "%}"),
        ("{{", "}}"),
        ("{#", "#}"),
    }

    def reset(self, dynamic_html, fix=False):
        """Prepare the preprocessor for processing."""
        self._dynamic_html = dynamic_html
        self._size = len(self._dynamic_html)
        self._fix = fix

        # Choose start and end delimiters for placeholers which do not appear
        # in the HTML string
        unused_char_num = 161
        while all(  # noqa: WPS352 (dynamic condition body)
            (
                chr(unused_char_num) in dynamic_html,
                chr(unused_char_num) not in SPECIAL_CHARS,
                not unicodedata.combining(chr(unused_char_num)),
            ),
        ):
            unused_char_num += 1

        unused_char_2_num = unused_char_num + 1
        while all(  # noqa: WPS352 (dynamic condition body)
            (
                chr(unused_char_2_num) in dynamic_html,
                chr(unused_char_2_num) not in SPECIAL_CHARS,
                not unicodedata.combining(chr(unused_char_2_num)),
            ),
        ):
            unused_char_2_num += 1

        self.delimiters = chr(unused_char_num), chr(unused_char_2_num)

    def process(self):
        """Replace the dynamic parts of some dynamic HTML with placeholders."""
        self.line = 1
        self.offset = 0

        self._instructions = []
        self._modified_html_parts = []

        opening_braces = (re.escape(braces[0]) for braces in self.braces)
        pattern = "|".join((f"(?:{brace})" for brace in opening_braces))
        interesting = re.compile(pattern)

        self._placeholder_id_num = 0

        html = self._dynamic_html
        size = self._size

        self._block_instruction_stack = []

        self._cursor = 0
        while self._cursor < size:
            cursor = self._cursor
            match = interesting.search(html, cursor)
            if match:
                cursor2 = match.start()
            else:
                cursor2 = size
            if cursor < cursor2:
                self._modified_html_parts.append(html[cursor:cursor2])

            self._cursor = self._update_position(cursor, cursor2)
            if self._cursor == size:
                break

            cursor = self._cursor

            startswith = html.startswith

            for braces in self.braces:
                if startswith(braces[0], cursor) and self._handle_match(braces):
                    break

        # end while
        cursor = self._cursor
        if cursor < size:
            self._modified_html_parts.append(html[cursor:size])

        if self._block_instruction_stack:
            _, last_instruction, braces = self._block_instruction_stack.pop()
            expected_instruction = {
                "block": "endblock",
                "if": "endif",
                "for": "endfor",
                "while": "endwhile",
                "with": "endwith",
                "blocktrans": "endblocktrans",
                "freeform": "endfreeform",
                "spaceless": "endspaceless",
                "spaceless_json": "endspaceless_json",
            }[last_instruction]
            tag_string = f"{braces[0]} {expected_instruction} {braces[1]}"
            raise self.make_error("P2", tag=tag_string)

        return "".join(self._modified_html_parts)

    def restore(self, modified_html, errors):
        """Restore the original dynamic parts to the modified HTML."""
        if not hasattr(self, "_instructions"):
            raise SetupError("Error: Attempting to restore before initial processing.")

        inserted_newline_locations = []

        for replacement, instruction in self._instructions:
            if "\n" in instruction:
                instruction_index = modified_html.find(replacement)
                for newline_match in re.finditer(r"\n", instruction):
                    inserted_newline_locations.append(instruction_index + newline_match.start())

            modified_html = modified_html.replace(replacement, instruction, 1)

        cursor = 0
        line = 0
        column = 0
        size = len(modified_html)
        while cursor < size:
            if modified_html[cursor] == "\n":
                if cursor in inserted_newline_locations:
                    for error in errors:
                        if error.line > line:
                            error.line += 1
                        elif error.line == line and error.column >= column:
                            error.line += 1
                            error.column -= column
                line += 1
                column = 0
            cursor += 1
            column += 1

        return modified_html

    def make_error(self, rule_code, line=None, column=None, **kwargs):
        """Create a PreprocessingError based on the given details."""
        if line is None:
            line = self.line
        if column is None:
            column = self.offset

        replacements = {}
        for keyword, value in kwargs.items():
            replacements[keyword] = value

        error = Error(
            line=line,
            column=column,
            rule=Rule.get(rule_code),
            replacements=replacements,
        )

        return PreprocessingError(errors=[error])

    def _handle_match(self, braces):
        """Replace a matched instruction with a placeholder."""
        should_collapse = True

        wraps = self.delimiters
        cursor = self._cursor
        html = self._dynamic_html
        dynamic_html_lower = html.lower()

        len_start = len(braces[0])
        len_end = len(braces[1])

        cursor2 = html.find(braces[1], cursor + len_start)
        if cursor2 < 0:
            raise self.make_error("P4")

        instruction_string, instruction_type = self.parse_instruction_tag(
            braces,
            html,
            cursor,
            cursor2,
        )

        end_cursor = cursor2 + len_end

        # Ensure balanced tags
        tag_string = f"{braces[0]} {instruction_string} {braces[1]}"
        hanging_closing_tag_error = self.make_error("P3", tag=tag_string)

        # Handle comment instructions
        if instruction_type == InstructionType.END_COMMENT:
            # We absorb these when we encounter the opening comment tag.
            raise hanging_closing_tag_error

        if instruction_type == InstructionType.COMMENT:
            should_collapse = False

            closing_tag_string = self.closing_tag_string_map[instruction_string]
            search_string = f"{braces[0]} {closing_tag_string} {braces[1]}"
            tag_string = f"{tag_string} … {search_string}"

            search_regex = re.compile(
                rf"{re.escape(braces[0])}[ \t]*"
                + rf"{re.escape(closing_tag_string)}[ \t]*"
                + f"{re.escape(braces[1])}",
            )

            match = search_regex.search(dynamic_html_lower, end_cursor)
            if not match:
                raise self.make_error("P2", tag=search_string)

            end_cursor = match.end()

        if instruction_type.is_group_start:
            self._block_instruction_stack.append((instruction_type, instruction_string, braces))

        if instruction_type.is_group_middle:
            if not self._block_instruction_stack:
                raise hanging_closing_tag_error
            last_instruction_type = self._block_instruction_stack[-1][0]

            expected_openings = {
                InstructionType.MID_CONDITIONAL: InstructionType.CONDITIONAL,
                InstructionType.LAST_CONDITIONAL: InstructionType.CONDITIONAL,
            }

            if last_instruction_type != expected_openings[instruction_type]:
                raise hanging_closing_tag_error

        if instruction_type.is_group_end:
            try:
                last_instruction_info = self._block_instruction_stack.pop()
            except IndexError:
                raise hanging_closing_tag_error

            last_instruction_type = last_instruction_info[0]

            expected_openings = {
                InstructionType.END_PARTIAL: InstructionType.PARTIAL,
                InstructionType.END_CONDITIONAL: InstructionType.CONDITIONAL,
                InstructionType.END_REPEATABLE: InstructionType.REPEATABLE,
                InstructionType.END_FREEFORM: InstructionType.FREEFORM,
            }

            if last_instruction_type != expected_openings[instruction_type]:
                raise hanging_closing_tag_error

        # Handle ignored instructions
        if instruction_type == InstructionType.IGNORED:
            should_collapse = False

        part = html[cursor:end_cursor]

        # Keep the length of the replacement the same for
        # line/column counting, but don't include any spaces so
        # it'll be handled appropriately by the HTML parser
        necessary_length = 3  # one opening, one closing, one type
        type_id_char = instruction_type.value
        id_value = base36_encode(self._placeholder_id_num)

        raw_instruction = part
        formatted_instruction_parts = [part[:len_start]]

        middle_part = part[len_start : -1 * len_end]

        if should_collapse:
            current_string_char = None
            part_cursor = 0
            part_size = len(middle_part)

            middle_parts = []
            current_part = ""
            is_escape = False
            while part_cursor < part_size:
                was_escape = is_escape
                is_escape = False

                char = middle_part[part_cursor]
                if char == " " and not current_string_char:
                    middle_parts.append(current_part)
                    current_part = ""
                    part_cursor += 1
                    continue

                if current_string_char and char == "\\":
                    is_escape = True
                    current_part = f"{current_part}{char}"
                    part_cursor += 1
                    continue

                for test_char in ("'", '"'):
                    if char != test_char:
                        continue

                    if not current_string_char:
                        current_string_char = char
                        break

                    if not was_escape and char == current_string_char:
                        current_string_char = None

                current_part = f"{current_part}{char}"
                part_cursor += 1

            middle_parts.append(current_part)
            for middle_part in middle_parts:
                if middle_part:
                    formatted_instruction_parts.append(middle_part)
        else:
            formatted_instruction_parts.append(middle_part.strip())

        formatted_instruction_parts.append(part[-1 * len_end :])

        formatted_instruction = " ".join(formatted_instruction_parts)
        if not self._fix and raw_instruction != formatted_instruction:
            raise self.make_error("P5", tag=tag_string)
        raw_instruction = formatted_instruction

        padding_length = len(raw_instruction) - necessary_length - len(id_value)
        if padding_length < 0:
            raise self.make_error("T1")

        padding = "-" * padding_length
        replacement = f"{wraps[0]}{type_id_char}{id_value}{padding}{wraps[1]}"

        self._modified_html_parts.append(replacement)
        self._instructions.append((replacement, raw_instruction))
        self._cursor = self._update_position(cursor, end_cursor)
        self._placeholder_id_num += 1

        return True

    def _update_position(self, cursor, end_cursor):
        len_chunk = end_cursor - cursor
        if len_chunk <= 0:
            return end_cursor

        html = self._dynamic_html
        num_lines = html.count("\n", cursor, end_cursor)
        self.line += num_lines
        if num_lines:
            self.offset = len_chunk - html[cursor:end_cursor].rindex("\n") - 1
        else:
            self.offset += len_chunk
        return end_cursor
