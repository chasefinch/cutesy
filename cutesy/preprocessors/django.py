"""Prerendering to accommodate the Django template language."""
# Current App
from .. import InstructionType
from . import BasePreprocessor


class Preprocessor(BasePreprocessor):
    """A preprocessor for Django templates."""

    closing_tag_string_map = {
        "freeform": "endfreeform",
        "comment": "endcomment",
        "spaceless": "endspaceless",
        "spaceless_json": "endspaceless_json",
    }

    def parse_instruction_tag(self, braces, html, cursor, cursor2):
        """Return the appropriate InstructionType."""
        if braces[0] == "{{":
            return "…", InstructionType.VALUE

        parts = html[cursor + len(braces[0]) : cursor2].split()
        try:
            instruction = parts[0]
        except IndexError:
            if braces[0] == "{#":
                return "…", InstructionType.IGNORED
            raise self.make_error("P4")

        if braces[0] == "{#":
            special_comment_instructions = {
                "freeform": InstructionType.FREEFORM,
                "endfreeform": InstructionType.END_FREEFORM,
            }

            try:
                return instruction, special_comment_instructions[instruction]
            except KeyError:
                return "…", InstructionType.IGNORED

        try:
            return (
                instruction,
                {
                    "block": InstructionType.PARTIAL,
                    "endblock": InstructionType.END_PARTIAL,
                    "if": InstructionType.CONDITIONAL,
                    "elif": InstructionType.MID_CONDITIONAL,
                    "else": InstructionType.LAST_CONDITIONAL,
                    "endif": InstructionType.END_CONDITIONAL,
                    "for": InstructionType.REPEATABLE,
                    "endfor": InstructionType.END_REPEATABLE,
                    "while": InstructionType.REPEATABLE,
                    "endwhile": InstructionType.END_REPEATABLE,
                    "with": InstructionType.PARTIAL,
                    "endwith": InstructionType.END_PARTIAL,
                    "blocktrans": InstructionType.CONDITIONAL,
                    "plural": InstructionType.LAST_CONDITIONAL,
                    "endblocktrans": InstructionType.END_CONDITIONAL,
                    "comment": InstructionType.COMMENT,
                    "endcomment": InstructionType.END_COMMENT,
                    "spaceless": InstructionType.FREEFORM,
                    "endspaceless": InstructionType.END_FREEFORM,
                    "spaceless_json": InstructionType.FREEFORM,
                    "endspaceless_json": InstructionType.END_FREEFORM,
                }[instruction],
            )
        except KeyError:
            return instruction, InstructionType.VALUE
