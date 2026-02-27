"""Prerendering to accommodate template languages."""

import re
import unicodedata
from abc import ABC
from collections.abc import Iterable
from typing import ClassVar

# Cutesy
from utilities.base36 import base36_encode

# Current App
from ..rules import Rule
from ..types import Error, InstructionType, StructuralError

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
        " ",  # noqa: RUF001 (Non-breaking space)
        "­",  # noqa: RUF001 (Soft hyphen)
        "\u200b",  # Zero-width space
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

    A preprocessor will replace dynamic instructions that it recognizes
    with placeholder stubs that can later be understood correctly by the
    HTML parser.
    """

    braces: ClassVar[set[tuple[str, str]]]
    closing_tag_string_map: ClassVar[dict[str, str]]
    expected_closing_instructions: ClassVar[dict[str, str]]

    def reset(self, dynamic_html: str, *, fix: bool = False) -> None:
        """Prepare the preprocessor for processing."""
        self._dynamic_html = dynamic_html
        self._size = len(self._dynamic_html)
        self.fix = fix

        # Choose start and end delimiters for placeholders which do not appear
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

    def process(self) -> str:
        """Replace the dynamic parts of some dynamic HTML with placeholders."""
        self.line = 1
        self.offset = 0

        # Dynamic instructions which have been replaced
        self._instructions = []
        self.errors = []

        # Modified HTML parts, including placeholders for instructions
        self._modified_html_parts = []

        opening_braces = (re.escape(possible_opening[0]) for possible_opening in self.braces)
        pattern = "|".join(f"(?:{brace})" for brace in opening_braces)
        interesting = re.compile(pattern)

        # Each placeholder includes an ID
        self._placeholder_id_num = 0

        html = self._dynamic_html
        size = self._size

        # Keep track of which instructions haven't been closed
        self._block_instruction_stack = []

        self._cursor = 0
        while self._cursor < size:
            cursor = self._cursor

            # Search for an opening brace
            match = interesting.search(html, cursor)
            cursor2 = match.start() if match else size

            if cursor < cursor2:
                # Consume HTML up to the opening brace
                self._modified_html_parts.append(html[cursor:cursor2])

            # Skip ahead to the opening brace or the end of the HTML
            self._cursor = self._update_position(cursor, cursor2)
            if self._cursor == size:
                break

            cursor = self._cursor

            startswith = html.startswith
            for possible_matching_braces in self.braces:
                if startswith(possible_matching_braces[0], cursor):
                    # Process & consume the match
                    self._handle_match(possible_matching_braces)
                    break

        # end while
        if self._cursor < size:
            self._modified_html_parts.append(html[self._cursor : size])

        if self._block_instruction_stack:
            # Handle dangling open instructions
            _, last_instruction, braces = self._block_instruction_stack.pop()
            expected_instruction = self.expected_closing_instructions[last_instruction]
            tag_string = f"{braces[0]} {expected_instruction} {braces[1]}"
            error_code = "P2"
            raise self.make_fatal_error(error_code, tag=tag_string)

        return "".join(self._modified_html_parts)

    def restore(self, modified_html: str, errors: Iterable[Error]) -> str:
        """Restore the original dynamic parts to the modified HTML."""
        if not hasattr(self, "_instructions"):
            error_message = "Error: Attempting to restore before initial processing."
            raise SetupError(error_message)

        # Insert the instructions back into the string in place of the
        # placeholders. Keep track of which instructions contained newlines and
        # where they were found, since the errors were not aware of those
        # newlines when they were generated.
        inserted_newline_locations = []
        for replacement, instruction in self._instructions:
            if "\n" in instruction:
                instruction_index = modified_html.find(replacement)
                for newline_match in re.finditer(r"\n", instruction):
                    inserted_newline_locations.append(instruction_index + newline_match.start())  # noqa: PERF401 (kept for clarity)

            modified_html = modified_html.replace(replacement, instruction, 1)

        # Adjust the line & column numbers according to the newlines found in
        # the now-restored instructions
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

    def parse_instruction_tag(
        self,
        braces: tuple[str, str],
        html: str,
        cursor: int,
        cursor2: int,
    ) -> tuple[str, InstructionType]:
        """Return the appropriate instruction text and InstructionType."""
        raise NotImplementedError

    def make_fatal_error(
        self,
        rule_code: str,
        line: int | None = None,
        column: int | None = None,
        **replacements: str,
    ) -> StructuralError:
        """Create a StructuralError based on the given details."""
        rule = Rule.get(rule_code)
        assert rule.structural

        if line is None:
            line = self.line
        if column is None:
            column = self.offset

        error = Error(
            line=line,
            column=column,
            rule=rule,
            replacements=replacements,
        )

        # Return a StructuralError which wraps the associated error; These
        # errors are fatal, and handled specially.
        return StructuralError(errors=[error])

    def _handle_match(self, braces: tuple[str, str]) -> None:
        """Replace a matched instruction with a placeholder."""
        # The instruction can be collapsed to contain only single spaces
        collapse = True

        wraps = self.delimiters
        cursor = self._cursor
        html = self._dynamic_html
        dynamic_html_lower = html.lower()

        len_start = len(braces[0])
        len_end = len(braces[1])

        cursor2 = html.find(braces[1], cursor + len_start)
        if cursor2 < 0:
            # Malformed tag
            error_code = "P4"
            raise self.make_fatal_error(error_code)

        # This is implemented by individual processors.
        instruction_string, instruction_type = self.parse_instruction_tag(
            braces,
            html,
            cursor,
            cursor2,
        )

        end_cursor = cursor2 + len_end

        # Ensure balanced tags
        tag_string = f"{braces[0]} {instruction_string} {braces[1]}"
        hanging_closing_tag_error = self.make_fatal_error("P3", tag=tag_string)

        # Handle comment instructions
        if instruction_type == InstructionType.END_COMMENT:
            # We absorb these when we encounter the opening comment tag.
            raise hanging_closing_tag_error

        if instruction_type == InstructionType.COMMENT:
            collapse = False

            closing_tag_string = self.closing_tag_string_map[instruction_string]
            search_string = f"{braces[0]} {closing_tag_string} {braces[1]}"
            tag_string = f"{tag_string} … {search_string}"

            search_regex = re.compile(
                rf"{re.escape(braces[0])}[ \t]*"
                rf"{re.escape(closing_tag_string)}[ \t]*"
                f"{re.escape(braces[1])}",
            )

            match = search_regex.search(dynamic_html_lower, end_cursor)
            if not match:
                error_code = "P2"
                raise self.make_fatal_error(error_code, tag=search_string)

            end_cursor = match.end()

        # Stack block-type instructions
        if instruction_type.is_group_start:
            self._block_instruction_stack.append((instruction_type, instruction_string, braces))

        # Handle chained blocks
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

        # End block-type instructions
        if instruction_type.is_group_end:
            try:
                last_instruction_info = self._block_instruction_stack.pop()
            except IndexError as error:
                raise hanging_closing_tag_error from error

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
            collapse = False

        part = html[cursor:end_cursor]

        # Keep the length of the replacement the same for
        # line/column counting, but don't include any spaces so
        # it'll be handled appropriately by the HTML parser
        necessary_length = 3  # one opening, one closing, one type
        type_id_char = instruction_type.value
        id_value = base36_encode(self._placeholder_id_num)

        raw_instruction = part
        if not self.fix:
            has_valid_padding = all(
                (
                    raw_instruction[len_start:].startswith(" "),
                    raw_instruction[: -1 * len_end].endswith(" "),
                ),
            )

            if not has_valid_padding:
                self._handle_error("P6", tag=tag_string)

        # Start with the opening brace
        formatted_instruction_parts = [part[:len_start]]

        middle_part = part[len_start : -1 * len_end]

        if collapse:
            # Collapse the instruction, except the part inside of strings.
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
            for possible_middle_part in middle_parts:
                if possible_middle_part:  # Skip blank strings, we allowed those
                    formatted_instruction_parts.append(possible_middle_part)  # noqa: PERF401
        else:
            formatted_instruction_parts.append(middle_part.strip())

        # Add the closing brace
        formatted_instruction_parts.append(part[-1 * len_end :])

        # Collapse
        formatted_instruction = " ".join(formatted_instruction_parts)
        if not self.fix:
            # Check if collapsing changed anything
            stripped_raw_instruction = raw_instruction[len_start : -1 * len_end]
            stripped_formatted_instruction = formatted_instruction[len_start : -1 * len_end]

            # Remove the case we checked for already
            stripped_raw_instruction = stripped_raw_instruction.removeprefix(" ")
            stripped_raw_instruction = stripped_raw_instruction.removesuffix(" ")

            stripped_formatted_instruction = stripped_formatted_instruction[1:-1]

            if stripped_raw_instruction != stripped_formatted_instruction:
                # This wasn't collapsed before
                self._handle_error("P5", tag=tag_string)

        raw_instruction = formatted_instruction

        padding_length = len(raw_instruction) - necessary_length - len(id_value)
        if padding_length < 0:
            error_code = "T1"
            raise self.make_fatal_error(error_code)

        padding = "-" * padding_length

        # Put together the replacement string, consisting of:
        #  (1) An opening delimeter
        #  (2) A character representing what type of instruction this is
        #  (3) A base36 integer specifying which instruction this is exactly
        #  (4) Possible padding to make this replacement the same length as the
        #      original instruction, so that the line/column position will be
        #      correct
        #  (5) A closing delimeter
        replacement = f"{wraps[0]}{type_id_char}{id_value}{padding}{wraps[1]}"

        self._modified_html_parts.append(replacement)
        self._instructions.append((replacement, raw_instruction))
        self._cursor = self._update_position(cursor, end_cursor)
        self._placeholder_id_num += 1

    def _update_position(self, cursor: int, end_cursor: int) -> int:
        """Update line & column number, and return the new cursor value."""
        len_chunk = end_cursor - cursor
        if len_chunk <= 0:
            return end_cursor

        html = self._dynamic_html
        num_lines = html.count("\n", cursor, end_cursor)
        self.line += num_lines
        if num_lines:
            # Start the column number over
            self.offset = len_chunk - html[cursor:end_cursor].rindex("\n") - 1
        else:
            # Add the current chunk length to the column number
            self.offset += len_chunk

        return end_cursor

    def _handle_error(self, rule_code: str, **replacements: str) -> None:
        self.errors.append(
            Error(
                line=self.line,
                column=self.offset,
                rule=Rule.get(rule_code),
                replacements=replacements,
            ),
        )
