"""Reindent multiline attributes according to their outer context."""

import re

from . import BaseAttributeProcessor


class AttributeProcessor(BaseAttributeProcessor):
    """Reindent multiline attributes according to their outer context."""

    def process(
        self,
        attr_name: str,
        indentation: str,
        current_indentation_level: int,
        tab_width: int,
        bounding_character: str,
        attr_body: str,
    ) -> str:
        """Reindent multiline attributes."""
        indentation_strings = (" " * tab_width, "\t")

        adjusted_body = attr_body

        # Strip leading whitespace before the first newline
        adjusted_body = re.sub(r"^[^\S\n]*(\S|\n)", r"\1", adjusted_body)
        if "\n" not in adjusted_body:
            return adjusted_body

        lines = adjusted_body.split("\n")

        indentation_and_lines: list[tuple[int, str]] = []
        for line in lines:
            num_indents = 0
            index = 0
            while any(line[index:].startswith(string) for string in indentation_strings):
                num_indents += 1
                if line[index:].startswith(" "):
                    index += tab_width
                else:
                    index += 1
            indentation_and_lines.append((num_indents, line.strip()))

        # Drop the first & last line for this calculation
        lines_with_content = [
            line_info for line_info in indentation_and_lines[1:-1] if line_info[1]
        ]

        if lines_with_content:
            min_indents = min(line_info[0] for line_info in lines_with_content)
        else:
            # The last line was the only line with content; Use it's offset
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
