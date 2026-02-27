"""Lint & format an HTML document in Python."""

import re
import string
from collections.abc import Sequence
from enum import Enum, auto
from html.parser import HTMLParser
from typing import Any, Final, Literal, NamedTuple, Never, TypeGuard

from .attribute_processors import BaseAttributeProcessor
from .preprocessors import BasePreprocessor
from .rules import Rule
from .types import (
    ConfigurationError,
    DoctypeError,
    Error,
    IndentationType,
    InstructionType,
    Mode,
    StructuralError,
)


class StackItemType(Enum):
    """Type of item on the tag/instruction stack."""

    TAG = auto()  # noqa: WPS115 (Enum caps)
    INSTRUCTION = auto()  # noqa: WPS115 (Enum caps)


class StackItem(NamedTuple):
    """An item on the tag/instruction stack."""

    item_type: StackItemType
    name: str | InstructionType  # tag name or instruction type
    indentation: int
    line: int  # line number where this item was opened


def is_whitespace(char: str) -> TypeGuard[Never]:
    """Return whether char is a whitespace character."""
    return char in string.whitespace


def attr_sort(attr: tuple[str | None, Any]) -> tuple[Any, ...]:
    """Return a sort tuple for attributes by priority."""
    return (
        attr[0] is None,
        attr[0] != "⚡",
        attr[0] != "amp",
        attr[0] != "lang",
        attr[0] != "rel",
        attr[0] != "as",
        attr[0] != "for",
        attr[0] != "type",
        attr[0] != "id",
        attr[0] != "class",
        "class" not in (attr[0] or ""),
        attr[0] != "name",
        "href" not in (attr[0] or ""),
        attr[0] != "itemid",
        attr[0] != "itemscope",
        attr[0] != "itemtype",
        attr[0] != "itemprop",
        attr[0] != "property",
        attr[0] != "content",
        attr[0] != "value",
        "value" not in (attr[0] or ""),
        attr[0] != "placeholder",
        attr[0] != "checked",
        "checked" not in (attr[0] or ""),
        attr[0] != "href",
        attr[0] != "src",
        "src" not in (attr[0] or ""),
        attr[0] != "multiple",
        attr[0] != "size",
        attr[0] != "step",
        attr[0] != "sizes",
        attr[0] != "width",
        attr[0] != "height",
        attr[0] != "alt",
        attr[0] != "title",
        attr[0] != "pattern",
        attr[0] != "maxlength",
        attr[0] != "disabled",
        attr[0] != "hidden",
        "hidden" not in (attr[0] or ""),
        attr[0] != "readonly",
        attr[0] != "required",
        attr[0] != "autocomplete",
        attr[0] != "autofocus",
        attr[0] != "tabindex",
        not (attr[0] or "").startswith("form"),
        attr[0] != "itemid",
        attr[0] != "itemscope",
        attr[0] != "itemtype",
        attr[0] != "itemprop",
        attr[0] != "style",
        # Push these keys to the end (in reverse order)
        (attr[0] or "").startswith("on"),
        (attr[0] or "").startswith("@"),
        (attr[0] or "").startswith("x-"),
        (attr[0] or "").startswith("data-"),
        attr[0],
    )


# https://www.w3.org/TR/2011/WD-html-markup-20110113/syntax.html#void-elements
VOID_ELEMENTS = frozenset(
    (
        "area",
        "base",
        "br",
        "col",
        "command",
        "embed",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ),
)


class HTMLLinter(HTMLParser):
    """A parser to ingest HTML and lint it."""

    fix: Final[bool]
    check_doctype: Final[bool]
    preprocessor: Final[BasePreprocessor | None]
    attribute_processors: Final[Sequence[BaseAttributeProcessor]]
    indentation_type: Final[IndentationType]
    tab_width: Final[int]
    max_items_per_line: Final[int]
    line_length: Final[int]

    _mode: Mode | None
    _errors: list[Error]
    _result: list[str]

    def __init__(
        self,
        *,
        fix: bool = False,
        check_doctype: bool = False,
        preprocessor: BasePreprocessor | None = None,
        attribute_processors: Sequence[BaseAttributeProcessor] | None = None,
        ignore_rules: Sequence[str] = (),
        indentation_type: IndentationType = IndentationType.TAB,
        tab_width: int = 4,
        max_items_per_line: int = 5,
        line_length: int = 99,
        convert_charrefs: bool = True,  # ignore
    ) -> None:
        """Initialize HTMLLinter."""
        super().__init__(convert_charrefs=False)
        self.fix = fix  # Whether we're fixing the files
        # If true, assume all files are HTML5 files, and complain when they
        # aren't. Otherwise, skip any files without an HTML5 doctype.
        self.check_doctype = check_doctype
        # A preprocessor for handling dynamic templating languages
        self.preprocessor = preprocessor
        self.attribute_processors = attribute_processors or []
        self.ignore_rules = ignore_rules
        self.convert_charrefs = False
        self.indentation_type = indentation_type
        # This applies even if indentation == TABS, to best infer what spaces
        # mean in the incoming HTML document
        self.tab_width = tab_width
        # Tuners for attribute wrapping logic
        self.max_items_per_line = max_items_per_line
        self.line_length = line_length

    def reset(self) -> None:
        """Reset the state of the linter so that it can be run again."""
        super().reset()
        self._mode = None  # Full document or arbitrary HTML
        self._errors = []
        self._result = []
        # Parsing state
        self._did_report_expected_doctype = False
        self._freeform_level = 0
        self._indentation_level = 0
        # Stack of StackItem for tracking tags and instructions
        self._tag_stack: list[StackItem] = []
        # Possible values: {None, True} if self.fix else {None, str}
        self._expected_indentation: str | Literal[True] | None = ""
        # Track last data to detect blank lines before closing
        # tags/instructions
        self._last_data: str | None = None
        # Track indentation level before last tag/instruction (for detecting
        # blank lines after opening)
        self._prev_indentation_level = 0
        # Line & column numbers in the modified HTML
        self._line = 0
        self._column = 0

    def lint(self, html: str) -> tuple[str, Sequence[Error]]:
        """Run the linting routine."""
        self.reset()

        html_data = html

        preprocessor = self.preprocessor
        if preprocessor:
            # Replace the dynamic template language instructions with
            # placeholders that our parser can handle
            preprocessor.reset(html_data, fix=self.fix)
            html_data = preprocessor.process()

        try:
            self.feed(html_data)
        except StructuralError as structural_error:
            # Update the line & column numbers for the errors.
            if preprocessor:
                preprocessor.restore(html_data, structural_error.errors)
            raise

        self.close()

        result = "".join(self._result) if self.fix else html_data
        errors = self._errors

        # Enforce a final blank line for full HTML documents.
        if self._mode == Mode.DOCUMENT and not result.endswith("\n"):
            if self.fix and not self.is_rule_ignored("D9"):
                # Normalize to exactly one blank line at EOF.
                result = "".join((result.rstrip("\n"), "\n"))
            else:
                self._handle_error("D9", column=0)

        if preprocessor:
            # Restore the instructions into the placeholder slots
            result = preprocessor.restore(result, errors)  # modifies "errors"

            # Add in any errors from the preprocessor which weren't fatal
            errors.extend(preprocessor.errors)

        errors.sort(key=lambda error: (error.line, error.column))

        return result, errors

    @property
    def indentation(self) -> str:
        """Return a string to indent a line one level."""
        if self.indentation_type == IndentationType.TAB:
            return "\t"

        if self.indentation_type == IndentationType.SPACES:
            return " " * self.tab_width

        return "\t"

    def is_rule_ignored(self, rule_code: str) -> bool:
        """Check if a rule should be ignored based on ignore_rules."""
        # Check if the exact rule code is ignored (e.g., "F1", "D5")
        if rule_code in self.ignore_rules:
            return True

        # Check if the rule category is ignored (e.g., "F" ignores all F-rules)
        rule_category = rule_code[0] if rule_code else ""
        return rule_category in self.ignore_rules

    def handle_decl(self, decl: str) -> None:
        """Process a declaration string."""
        self._reconcile_indentation()

        # We only want "doctype" declarations, and only at the beginning. The
        # presence of a doctype declaration determines whether this is an HTML
        # document, or just loose HTML.
        if self._mode:
            mode_code = {
                Mode.DOCUMENT: "D2",
                Mode.UNSTRUCTURED: "D1",
            }[self._mode]
            self._handle_error(mode_code)
            if self.fix:
                self._process(f"<!{decl}>")
            return

        decl_lower = decl.lower()
        fix_f1 = self.fix and not self.is_rule_ignored("F1")
        if fix_f1:
            decl = decl_lower
        elif decl_lower != decl:
            self._handle_error("F1")

        decl_lower_joined = " ".join(decl_lower.split())
        fix_f13 = self.fix and not self.is_rule_ignored("F13")
        if fix_f13:
            decl = decl_lower_joined
        elif decl_lower != decl_lower_joined:
            self._handle_error("F13", tag=f"<!{decl_lower_joined}>")

        if decl_lower_joined != "doctype html":
            if not self.check_doctype:
                # Punt; This is not an HTML5 document.
                raise DoctypeError

            self._handle_error("E1")

        self._mode = Mode.DOCUMENT

        if self.fix:
            self._process(f"<!{decl}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Process a self-closing tag."""
        self.handle_starttag(tag, attrs)

        tag = tag.lower()
        if tag in VOID_ELEMENTS:
            if not self.fix:
                self._handle_error("D5", tag=f"<{tag}>")

        else:
            if not self.fix:
                self._handle_error("D6", tag=f"<{tag}>")

            self.handle_endtag(tag)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Process a start tag."""
        self._handle_encountered_data()
        self._last_data = None  # Clear last data when we encounter a tag
        self._prev_indentation_level = self._indentation_level  # Track indentation before tag

        is_new_line = self._expected_indentation is not None

        if not self.fix and tag != tag.lower():
            # Tag isn't lowercase
            self._handle_error("F7", tag=f"<{tag}>")

        tag = tag.lower()

        num_attrs = len(attrs)
        solo = num_attrs == 1

        _, attr_strings = self._make_attr_strings(attrs, solo=solo, final_pass=False)

        # Decide whether this should be kept on one line or should wrap

        has_breaking_attr = any(
            char in attr_string for attr_string in attr_strings for char in ("\n", "\t")
        )

        len_angle_brackets = 2
        len_attrs = sum(len(attr_string) for attr_string in attr_strings)
        num_spaces = num_attrs
        num_chars = (
            len_angle_brackets
            + len_attrs
            + num_spaces
            + len(tag)
            + self.tab_width * self._indentation_level
        )
        wrap = num_attrs > 1 and any(
            (
                num_attrs > self.max_items_per_line,
                num_chars > self.line_length,
                has_breaking_attr,
            ),
        )

        single_attribute_wrap = has_breaking_attr and not wrap
        if single_attribute_wrap:
            self._indentation_level -= 1

        # Recalculate attr_stings at the new indentation level (the final pass)
        _, attr_strings = self._make_attr_strings(attrs, solo=solo)

        if single_attribute_wrap:
            self._indentation_level += 1

            has_breaking_attr = any(
                char in attr_string for attr_string in attr_strings for char in ("\n", "\t")
            )
            if not has_breaking_attr:
                wrap = False

        if wrap and not is_new_line:
            fix_f12 = self.fix and not self.is_rule_ignored("F12")
            if fix_f12 and self._break_for_inline_tag():
                self._process("\n")
                self._expected_indentation = True
                is_new_line = True
            else:
                self._handle_error("F12", tag=f"<{tag}>")

        self._reconcile_indentation()

        wrap = wrap and is_new_line

        if wrap:
            indentation_level = self._indentation_level + 1
            indentation = self.indentation * indentation_level
            attrs_string = f"\n{indentation}".join(attr_strings)

            end_char = self.indentation * (indentation_level - 1)
            attrs_string = f"\n{indentation}{attrs_string}\n{end_char}"
        elif attr_strings:
            # Don't wrap; Just separate all by a space
            attrs_string = " ".join(attr_strings)
            attrs_string = f" {attrs_string}"
        else:
            # No attributes
            attrs_string = ""

        attrs_string = re.sub(rf"\n({self.indentation})+\n", "\n\n", attrs_string)

        if not self.fix:
            new_whitespace = list(filter(is_whitespace, list(attrs_string)))
            old_whitespace = list(filter(is_whitespace, list(self.__starttag_text or "")))

            if new_whitespace != old_whitespace:
                if "\n" in new_whitespace and "\n" not in old_whitespace and wrap:
                    error_code = "F14"
                elif "\n" not in new_whitespace and "\n" in old_whitespace and not wrap:
                    error_code = "F15"
                else:
                    error_code = "F13"

                self._handle_error(error_code, tag=f"<{tag}>")

        if tag not in VOID_ELEMENTS:
            # Tag should be closed, add it to the stack.
            self._tag_stack.append(
                StackItem(StackItemType.TAG, tag, self._indentation_level, self.getpos()[0]),
            )

            if tag != "html":
                # All non-void elements increase the expected indentation level
                # except <html>
                self._indentation_level += 1

        if self.fix:
            self._process(f"<{tag}{attrs_string}>")

    def handle_endtag(self, tag: str) -> None:
        """Process a closing tag."""
        if not self.fix and tag != tag.lower():
            self._handle_error("F7", tag=f"</{tag}>")

        tag = tag.lower()

        # Store the current indentation level before we pop the stack
        old_indentation_level = self._indentation_level
        opening_line = None  # Track line where opening tag was found

        if tag in {item.name for item in self._tag_stack if item.item_type == StackItemType.TAG}:
            # Pop self._tag_stack until we find the matching opening tag
            while self._tag_stack:
                stack_item = self._tag_stack.pop()

                if stack_item.item_type == StackItemType.TAG and stack_item.name == tag:
                    self._indentation_level = stack_item.indentation
                    opening_line = stack_item.line
                    break
                if stack_item.item_type == StackItemType.TAG:
                    self._handle_error("D3", tag=f"</{stack_item.name}>")
                else:
                    # Found an unclosed instruction before the matching tag
                    self._handle_error("P2", tag=f"{{{stack_item.name}}}")
        else:
            self._handle_error("D4", tag=f"</{tag}>")
            # Decrement anyway to try to recover
            if self._indentation_level > 0:
                self._indentation_level -= 1

        # Check for blank lines before closing tag that decreases indentation
        # Skip this check if the closing tag is on the same line as the opening tag
        if (
            self._indentation_level < old_indentation_level
            and self._last_data
            and opening_line != self.getpos()[0]
        ):
            match = re.search(r"\n\s*\n\s*$", self._last_data)
            if match:
                if self.fix:
                    # Remove blank lines from the end of the result buffer
                    if self._result:
                        last_chunk = self._result[-1]
                        # Replace multiple trailing newlines with single newline + indentation
                        self._result[-1] = re.sub(r"\n\s*\n\s*$", r"\n", last_chunk)
                else:
                    # Report F4 error for extra vertical whitespace
                    line_offset = self._last_data[: match.start()].count("\n")
                    self._handle_error("F4", line_offset=line_offset, column=0)

        if tag != self.cdata_elem:
            self._reconcile_indentation()

        if self.fix:
            self._process(f"</{tag}>")

    def handle_data(self, html_data: str) -> None:
        """Process HTML data."""
        # Store the raw data for checking in handle_endtag
        self._last_data = html_data

        self._handle_encountered_data()
        self._reconcile_indentation()

        if self.cdata_elem or self._freeform_level:
            if self.fix:
                self._process(html_data)
            return

        # Check for blank lines after opening tag/instruction that increased indentation
        if self._indentation_level > self._prev_indentation_level:
            # Match: newline followed by any blank lines at the start
            match = re.search(r"^\n[ \t]*\n", html_data)
            if match:
                if self.fix:
                    # Remove ALL leading blank lines, keeping just one newline
                    html_data = re.sub(r"^(\n[ \t]*)+\n", "\n", html_data)
                # Only report if there's NOT 3+ consecutive newlines (that's reported elsewhere)
                elif not re.search(r"\n{3,}", html_data):
                    # Report F4 error for extra vertical whitespace
                    self._handle_error("F4", line_offset=0, column=0)

        indentation = self.indentation * self._indentation_level

        # Check for & fix trailing whitespace
        trailing_whitespace = r"[ \t]+\n"
        if self.fix:
            html_data = re.sub(trailing_whitespace, "\n", html_data)

        else:
            for match in re.finditer(trailing_whitespace, html_data):
                start = match.start()
                line_offset = html_data.count("\n", 0, start)
                column = html_data.rfind("\n", 0, start) - 1
                self._handle_error("F2", line_offset=line_offset, column=column)

        # Check for & fix inappropriate indentation
        some_indentation = r"\n[ \t]*"
        new_html_data = re.sub(some_indentation, f"\n{indentation}", html_data)

        if indentation:
            blank_line = f"\n{indentation}\n"

            while blank_line in new_html_data:
                new_html_data = new_html_data.replace(blank_line, "\n\n")

        if new_html_data.endswith(f"\n{indentation}"):
            if indentation:
                new_html_data = new_html_data[: -1 * len(indentation)]

            # We should add indentation once we know how deep to indent.
            self._expected_indentation = True

        if self.fix:
            html_data = new_html_data
        else:
            html_lines = html_data.split("\n")
            new_html_lines = new_html_data.split("\n")
            for index, line in enumerate(new_html_lines):
                if index == len(new_html_lines) - 1 and not line:
                    # This is the last line; We don't know what's coming next
                    if not self.fix:
                        # We should confirm the indentation once we know it.
                        self._expected_indentation = html_lines[index]
                    break

                # This isn't the last line
                original_line = html_lines[index]
                if line != original_line:
                    self._handle_error("F3", line_offset=index, column=0)

        # Check for & fix too many consecutive empty lines
        extra_vertical_lines = r"\n{3,}"
        if self.fix:
            html_data = re.sub(extra_vertical_lines, "\n\n", html_data)
        else:
            for match in re.finditer(extra_vertical_lines, html_data):
                line_offset = html_data.count("\n", 0, match.start())
                self._handle_error("F4", line_offset=line_offset, column=0)

        lines = []
        for index, line in enumerate(html_data.split("\n")):
            original_line = line
            line_contents = line
            line_start = ""

            # We don't assume that the lines have been indented, or have had
            # trailing whitespace removed, since we might not be in "fix" mode
            if index > 0:
                line_contents = line_contents.lstrip()
                line_start = original_line[: len(original_line) - len(line_contents)]

            trimmed_line_contents = line_contents.lstrip()
            leading_space = " " if 0 < len(trimmed_line_contents) < len(line_contents) else ""

            trimmed_line_contents = line_contents.rstrip()
            trailing_space = " " if len(trimmed_line_contents) < len(line_contents) else ""

            new_line_contents = " ".join(line_contents.split())
            new_line_contents = f"{leading_space}{new_line_contents}{trailing_space}"
            if self.fix:
                original_line = f"{line_start}{new_line_contents}"
            elif line_contents.rstrip() != new_line_contents.rstrip():
                # Find first character where the differ
                len_line = min(len(line_contents.rstrip()), len(new_line_contents.rstrip()))
                column = next(
                    (
                        column
                        for column in range(len_line)
                        if line_contents[column] != new_line_contents[column]
                    ),
                    len_line,
                )

                self._handle_error("F5", line_offset=index, column=len(line_start) + column)

            lines.append(original_line)

        if self.fix:
            self._process("\n".join(lines))

    def handle_instruction(self, instruction_text: str) -> None:
        """Process a dynamic template instruction placeholder."""
        instruction_type = InstructionType(instruction_text[0])

        if instruction_type == InstructionType.FREEFORM:
            self._freeform_level += 1
        elif instruction_type == InstructionType.END_FREEFORM:
            self._freeform_level -= 1

        # Store the current indentation level before we change it
        old_indentation_level = self._indentation_level
        opening_line = None  # Track line where opening instruction was found

        # Handle block ending/continuation - restore correct indentation from stack
        if instruction_type.ends_block or instruction_type.continues_block:
            found_match = False
            while self._tag_stack:
                # Pop to find the matching opening instruction
                stack_item = self._tag_stack.pop()

                if stack_item.item_type == StackItemType.INSTRUCTION:
                    self._indentation_level = stack_item.indentation
                    opening_line = stack_item.line

                    # For continuations (else, elif), validate the match
                    if instruction_type.continues_block:
                        # Continuation should match a block start or another continuation
                        # stack_item.name is an InstructionType
                        assert isinstance(stack_item.name, InstructionType)
                        if not (stack_item.name.starts_block or stack_item.name.continues_block):
                            self._handle_error("P2", tag=f"{{{instruction_text}}}")

                    found_match = True
                    break
                # Found an unclosed tag before the matching instruction
                self._handle_error("D3", tag=f"</{stack_item.name}>")

            if not found_match:
                # No matching opening instruction found
                self._handle_error("P3", tag=f"{{{instruction_text}}}")
                # Decrement anyway to try to recover
                if self._indentation_level > 0:
                    self._indentation_level -= 1

        # Check for blank lines before instruction that decreases indentation
        # Skip this check if the closing instruction is on the same line as the opening instruction
        if (
            self._indentation_level < old_indentation_level
            and self._last_data
            and opening_line != self.getpos()[0]
        ):
            match = re.search(r"\n\s*\n\s*$", self._last_data)
            if match:
                if self.fix:
                    # Remove blank lines from the end of the result buffer
                    if self._result:
                        last_chunk = self._result[-1]
                        # Replace multiple trailing newlines with single newline + indentation
                        self._result[-1] = re.sub(r"\n\s*\n\s*$", r"\n", last_chunk)
                else:
                    # Report F4 error for extra vertical whitespace
                    line_offset = self._last_data[: match.start()].count("\n")
                    self._handle_error("F4", line_offset=line_offset, column=0)

        self._reconcile_indentation()  # Between the indentation change

        # Track indentation before we change it (for detecting blank lines after opening)
        self._prev_indentation_level = self._indentation_level

        # Handle block starting/continuation - push onto stack and increase indentation
        if instruction_type.starts_block:
            # Push the opening instruction type and current indentation level
            self._tag_stack.append(
                StackItem(
                    StackItemType.INSTRUCTION,
                    instruction_type,
                    self._indentation_level,
                    self.getpos()[0],
                ),
            )
            self._indentation_level += 1
        elif instruction_type.continues_block:
            # For continuations, push back with the continuation type
            self._tag_stack.append(
                StackItem(
                    StackItemType.INSTRUCTION,
                    instruction_type,
                    self._indentation_level,
                    self.getpos()[0],
                ),
            )
            self._indentation_level += 1

        if self.fix:
            processing_text = instruction_text
            if self.preprocessor:
                wraps = self.preprocessor.delimiters
                processing_text = f"{wraps[0]}{instruction_text}{wraps[1]}"
            self._process(processing_text)

    def handle_entityref(self, name: str) -> None:
        """Process an HTML entity."""
        self._handle_encountered_data()
        self._reconcile_indentation()

        if self.fix:
            self._process(f"&{name};")

    def handle_charref(self, name: str) -> None:
        """Process a numbered HTML entity."""
        self._handle_encountered_data()
        self._reconcile_indentation()

        if self.fix:
            self._process(f"&#{name};")

    def handle_comment(self, comment: str) -> None:
        """Process an HTML comment."""
        self._reconcile_indentation()

        if self.fix:
            self._process(f"<!--{comment}-->")

    def goahead(self, end: int) -> None:
        """Handle data as far as reasonably possible.

        Adapted from:
        https://github.com/python/cpython/blob/3.10/Lib/html/parser.py

        This modified version doesn't support multiple calls to "feed" or
        convert_charrefs mode.
        """
        interesting_regex = r"&|<"
        if self.preprocessor:
            wraps = self.preprocessor.delimiters
            opening_regex_part = re.escape(wraps[0])
            interesting_regex = f"{interesting_regex}|(?:{opening_regex_part})"

        interesting = re.compile(interesting_regex)
        entityref = re.compile("&([a-zA-Z][-.a-zA-Z0-9]*);")
        charref = re.compile("&#(?:[0-9]+|[xX][0-9a-fA-F]+);")
        starttagopen = re.compile("<[a-zA-Z]")
        endtagopen = re.compile("</[a-zA-Z]")

        rawdata = self.rawdata
        cursor = 0
        size = len(rawdata)
        while cursor < size:
            match = interesting.search(rawdata, cursor)  # < or &, or a dynamic tag
            cursor2 = match.start() if match else size
            if cursor < cursor2:
                self.handle_data(rawdata[cursor:cursor2])
            cursor = self.updatepos(cursor, cursor2)
            if cursor == size:
                break

            startswith = rawdata.startswith

            if self.preprocessor:
                # Check for the opening of a dynamic tag
                prefix, postfix = self.preprocessor.delimiters
                if startswith(prefix, cursor):
                    cursor2 = rawdata.find(postfix, cursor + 1)  # Should always be >= 0
                    instruction_text = rawdata[cursor + 1 : cursor2]
                    self.handle_instruction(instruction_text)
                    cursor = self.updatepos(cursor, cursor2 + 1)
                    continue

            if self._freeform_level:
                # We're in a freeform tag; Everything other than the dynamic
                # tags should just be reproduced as-is
                self.handle_data(rawdata[cursor : cursor + 1])
                cursor = self.updatepos(cursor, cursor + 1)
                continue

            if startswith("<", cursor):
                if starttagopen.match(rawdata, cursor):  # < + letter
                    cursor2 = self.parse_starttag(cursor)
                elif endtagopen.match(rawdata, cursor):
                    cursor2 = self.parse_endtag(cursor)
                elif startswith("<!--", cursor):
                    cursor2 = self.parse_comment(cursor)
                elif startswith("<!", cursor):
                    cursor2 = self.parse_html_declaration(cursor)
                else:
                    self._handle_error("E3")
                    self.handle_data("<")
                    cursor2 = cursor + 1

                if cursor2 < 0:
                    cursor2 = rawdata.find(">", cursor + 1)
                    if cursor2 < 0:
                        cursor2 = rawdata.find("<", cursor + 1)
                        if cursor2 < 0:
                            cursor2 = cursor + 1
                    else:
                        cursor2 += 1
                    self.handle_data(rawdata[cursor:cursor2])
                cursor = self.updatepos(cursor, cursor2)
                continue

            if startswith("&#", cursor):
                match = charref.match(rawdata, cursor)
                if match:
                    name = match.group()[2:-1]
                    cursor2 = match.end()
                    self.handle_charref(name)
                    cursor = self.updatepos(cursor, cursor2)
                    continue

                # bail by consuming &#
                if self.cdata_elem is not None:
                    self._handle_error("E2")

                self.handle_data(rawdata[cursor : cursor + 2])
                cursor = self.updatepos(cursor, cursor + 2)
                continue

            if startswith("&", cursor):
                match = entityref.match(rawdata, cursor)
                if match:
                    name = match.group(1)
                    cursor2 = match.end()
                    self.handle_entityref(name)
                    cursor = self.updatepos(cursor, cursor2)
                    continue

                if self.cdata_elem is not None:
                    self.handle_data("&")
                    cursor = self.updatepos(cursor, cursor + 1)
                    continue

                # can't be confused with some other construct
                ref_data = "&amp;"
                fix_e2 = self.fix and not self.is_rule_ignored("E2")
                if fix_e2:
                    ref_data = "&amp;"
                else:
                    ref_data = "&"
                    self._handle_error("E2")

                self.handle_data(ref_data)
                cursor = self.updatepos(cursor, cursor + 1)

        # end while
        if cursor < size:
            self.handle_data(rawdata[cursor:size])
            cursor = self.updatepos(cursor, size)
        self.rawdata = rawdata[cursor:]

    def parse_starttag(self, cursor: int) -> int:
        """Parse a start tag.

        Adapted from:
        https://github.com/python/cpython/blob/3.10/Lib/html/parser.py
        """
        attrfind_tolerant = re.compile(
            r'((?<=[\'"\s/])[^\s/>][^\s/=>]*)(\s*=+\s*'
            r'(\'[^\']*\'|"[^"]*"|(?![\'"])[^>\s]*))?(?:\s|/(?!>))*',
        )

        tagfind_tolerant = re.compile(r"([a-zA-Z][^\t\n\r\f />\x00]*)(?:\s|/(?!>))*")
        rawdata = self.rawdata

        self.__starttag_text = None  # noqa: WPS112 (copied)
        if self.preprocessor:
            wraps = self.preprocessor.delimiters
            wrap_regex = re.escape(wraps[0])
            overlap = re.compile(
                rf"<([a-zA-Z][-.a-zA-Z0-9:_]*){wrap_regex}",
            )
            match = overlap.match(rawdata, cursor)
            if match:
                error_code = "P1"
                raise self._make_fatal_error(
                    error_code,
                    tag="Instruction",
                )

        end_cursor = self.check_for_whole_start_tag(cursor)
        if end_cursor < 0:
            self._handle_error("D7")
            return end_cursor

        self.__starttag_text = rawdata[cursor:end_cursor]  # noqa: WPS112 (copied)

        attrs = []
        match = tagfind_tolerant.match(rawdata, cursor + 1)
        if not match:
            raise NotImplementedError

        cursor2 = match.end()

        tag = match.group(1)
        self.lasttag = tag.lower()
        while cursor2 < end_cursor:
            match = attrfind_tolerant.match(rawdata, cursor2)
            if not match:
                break

            attrname, rest, attrvalue = match.group(1, 2, 3)
            if not rest or attrvalue is None:
                attrvalue = None
            elif attrvalue[:1] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
            elif attrvalue[:1] == "'" == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
                if '"' not in attrvalue and not self.fix:
                    self._handle_error("F10", attr=attrname)
            elif not self.fix:
                self._handle_error("F9", attr=attrname)

            attrs.append((attrname, attrvalue))
            cursor2 = match.end()

        end = rawdata[cursor2:end_cursor].strip()
        if end not in {">", "/>"}:
            lineno, offset = self.getpos()
            if "\n" in self.__starttag_text:
                lineno = lineno + self.__starttag_text.count("\n")
                offset = len(self.__starttag_text) - self.__starttag_text.rfind("\n")
            else:
                offset = offset + len(self.__starttag_text)
            self.handle_data(rawdata[cursor:end_cursor])

            return end_cursor

        if end.endswith("/>"):
            # XHTML-style empty tag: <span attr="value" />
            self.handle_startendtag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            tag = tag.lower()
            if tag in self.CDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag)

        return end_cursor

    def parse_endtag(self, cursor: int) -> int:
        """Parse an end tag.

        Adapted from:
        https://github.com/python/cpython/blob/3.10/Lib/html/parser.py
        """
        rawdata = self.rawdata

        endtagfind = re.compile(r"</([a-zA-Z][-.a-zA-Z0-9:_]*)\s*>")
        match = endtagfind.match(rawdata, cursor)  # </ + tag + >
        if not match:
            if self.preprocessor:
                wraps = self.preprocessor.delimiters
                wrap_regex = re.escape(wraps[0])
                overlap = re.compile(
                    rf"</[a-zA-Z][-.a-zA-Z0-9:_]*\s*{wrap_regex}",
                )
                match = overlap.match(rawdata, cursor)
                if match:
                    error_code = "P1"
                    raise self._make_fatal_error(
                        error_code,
                        tag="Instruction",
                    )

            self._handle_error("D8")
            return -1

        end_cursor = match.end()
        tag = match.group(1)

        parsed_data = rawdata[cursor:end_cursor]
        if any(char in string.whitespace for char in rawdata[cursor:end_cursor]):
            if self.fix:
                parsed_data = re.sub(r"\s", "", parsed_data)
            else:
                self._handle_error("F11", tag=f"</{tag}>")

        if self.cdata_elem is not None and tag.lower() != self.cdata_elem:
            # script or style
            self.handle_data(parsed_data)
            return end_cursor

        self.handle_endtag(tag)
        self.clear_cdata_mode()

        return end_cursor

    def _process(self, html_chunk: str) -> None:
        """Process the HTML chunk."""
        self._result.append(html_chunk)

        len_chunk = len(html_chunk)
        num_lines = html_chunk.count("\n")
        self._line += num_lines
        if num_lines:
            self._column = len_chunk - html_chunk.rfind("\n") - 1
        else:
            self._column += len_chunk

    def _break_for_inline_tag(self) -> bool:
        """Remove the most recent space in preparation for a line break."""
        if not self._result or not self._result[-1].endswith((" ", ">")):
            return False

        self._result[-1] = self._result[-1][:-1]
        self._column -= 1
        return True

    def _handle_encountered_data(self) -> None:
        """Handle encountered data."""
        self._mode = self._mode or Mode.UNSTRUCTURED

    def _reconcile_indentation(self, adjustment: int = 0) -> None:
        """Return indentation properly."""
        if self._expected_indentation is None:
            return

        indentation = self.indentation * (self._indentation_level + adjustment)
        if self.fix:
            self._process(indentation)
        elif self._expected_indentation != indentation:
            self._handle_error("F3", column=0)

        self._expected_indentation = None

    def _make_attr_strings(
        self,
        attrs: Sequence[tuple[str, Any]],
        *,
        solo: bool = False,
        final_pass: bool = True,
    ) -> tuple[str | None, Sequence[str]]:
        """Return the prepared attribute strings.

        Recursively handles dynamic attributes, prepending them with the
        indentation characters.

        The first return value is a key for sorting the whole set in a
        higher- level set. The second is a list of attribute strings.
        """
        all_attrs = []
        for incoming_attr in attrs:
            name, value = incoming_attr

            if self.preprocessor:
                wraps = self.preprocessor.delimiters
                while wraps[0] in name:
                    start_index = name.index(wraps[0])
                    end_index = name.index(wraps[1]) + 1

                    if start_index > 0:
                        split_name = name[:start_index]
                        split_name_lower = split_name.lower()
                        if not self.fix and split_name != split_name_lower and final_pass:
                            self._handle_error("F8", attr=split_name_lower)

                        quote_char = "'" if '"' in split_name_lower else '"'
                        all_attrs.append((split_name_lower, value, quote_char))

                    split_name = name[start_index:end_index]

                    quote_char = "'" if '"' in split_name else '"'
                    all_attrs.append((split_name, None, quote_char))

                    name = name[end_index:]
            if name:
                name_lower = name.lower()
                if not self.fix and name != name_lower and final_pass:
                    self._handle_error("F8", attr=name_lower)

                quote_char = "'" if '"' in (value or "") else '"'
                all_attrs.append((name_lower, value, quote_char))

        attr_keys_and_groups = []

        group_level = 0

        group = []
        for name, value, quote_char in all_attrs:
            attr = name, value

            instruction_type = None
            if self.preprocessor and name.startswith(self.preprocessor.delimiters[0]):
                instruction_type = InstructionType(name[1])

            if instruction_type and instruction_type.is_group_start:
                group_level += 1
                if group_level == 1:
                    group = [name]
                    group_key: str | None = None
                    subgroup_attrs = []
                else:
                    subgroup_attrs.append(attr)
            elif instruction_type and instruction_type.is_group_middle:
                if group_level == 1:
                    subgroup_key, subgroup = self._make_attr_strings(
                        subgroup_attrs,
                        final_pass=False,
                    )
                    if group_key and subgroup_key:
                        group_key = min(group_key, subgroup_key)
                    else:
                        group_key = group_key or subgroup_key
                    group += [f"{self.indentation}{attr_string}" for attr_string in subgroup]
                    group.append(name)
                    subgroup_attrs = []
                else:
                    subgroup_attrs.append(attr)
            elif instruction_type and instruction_type.is_group_end:
                if group_level == 1:
                    subgroup_key, subgroup = self._make_attr_strings(
                        subgroup_attrs,
                        final_pass=False,
                    )
                    if group_key and subgroup_key:
                        group_key = min(group_key, subgroup_key)
                    else:
                        group_key = group_key or subgroup_key
                    group += [f"{self.indentation}{attr_string}" for attr_string in subgroup]
                    group.append(name)
                    attr_keys_and_groups.append((group_key, group))
                else:
                    subgroup_attrs.append(attr)
                group_level -= 1
            elif group_level:
                subgroup_attrs.append(attr)
            else:
                attr_string = name
                if value is not None:
                    processed_value = value
                    for processor in self.attribute_processors:
                        processed_value, processing_errors = processor.process(
                            attr_name=name,
                            indentation=self.indentation,
                            position=(self.getpos()[0] - 1, self.getpos()[1]),
                            current_indentation_level=self._indentation_level + 1,
                            tab_width=self.tab_width,
                            line_length=self.line_length,
                            max_items_per_line=self.max_items_per_line,
                            bounding_character=quote_char,
                            preprocessor=self.preprocessor,
                            attr_body=processed_value,
                            solo=solo,
                        )
                        fix_f17 = self.fix and not self.is_rule_ignored("F17")
                        if processing_errors:
                            for processing_error in processing_errors:
                                self._handle_error(error=processing_error)
                        elif not fix_f17 and value != processed_value and final_pass:
                            self._handle_error("F17", attr=name)
                    attr_string = f"{attr_string}={quote_char}{processed_value}{quote_char}"
                attr_keys_and_groups.append((name, [attr_string]))

        if self.fix:
            attr_keys_and_groups.sort(key=attr_sort)
        else:
            sorted_groups = sorted(attr_keys_and_groups, key=attr_sort)
            if attr_keys_and_groups != sorted_groups and final_pass:
                self._handle_error("F6")

        try:
            sort_key = attr_keys_and_groups[0][0]
        except IndexError:
            sort_key = None

        attr_strings = []
        for _, group in attr_keys_and_groups:
            num_dynamic_tag_parts = 3
            num_empty_dyamic_context_attrs = 2

            is_flattenable = (
                num_dynamic_tag_parts <= len(group) <= self.max_items_per_line
                and not any("\n" in item for item in group)
                and sum(len(item) for item in group)
                + self.tab_width * (self._indentation_level + 1)
                <= self.line_length
            )

            if is_flattenable:
                # strip one indent from every inner item, if present
                inner_items = [item.removeprefix(self.indentation) for item in group[1:-1]]
                flat = f"{group[0]}{' '.join(inner_items)}{group[-1]}"
                attr_strings.append(flat)

            elif len(group) == num_empty_dyamic_context_attrs:
                # Nothing between start/end tokens – just glue them together
                attr_strings.append("".join(group))
            else:
                attr_strings.extend(group)

        return sort_key, attr_strings

    def _handle_error(
        self,
        rule_code: str | None = None,
        line_offset: int = 0,
        column: int | None = None,
        *,
        error: Error | None = None,
        **replacements: str,
    ) -> None:
        if error:
            rule_code = error.rule.code
        else:
            assert rule_code is not None
            error = self._make_error(
                rule_code=rule_code,
                line_offset=line_offset,
                column=column,
                **replacements,
            )

        is_rule_ignored = self.is_rule_ignored(rule_code)

        if self.fix and Rule.get(rule_code).structural:
            exception: Exception
            if is_rule_ignored:
                message = f"Can’t run --fix with structural rule {rule_code} ignored"
                exception = ConfigurationError(message)
            else:
                exception = self._make_fatal_error(error=error)
            raise exception

        if is_rule_ignored:
            return

        self._errors.append(error)

    def _make_fatal_error(
        self,
        rule_code: str | None = None,
        line_offset: int = 0,
        column: int | None = None,
        *,
        error: Error | None = None,
        **replacements: str,
    ) -> StructuralError:
        if not error:
            assert rule_code is not None
            error = self._make_error(
                rule_code=rule_code,
                line_offset=line_offset,
                column=column,
                **replacements,
            )

        assert error.rule.structural

        # Return a StructuralError which wraps the associated error; These
        # errors are fatal, and handled specially.
        return StructuralError(errors=[error])

    def _make_error(
        self,
        rule_code: str,
        line_offset: int = 0,
        column: int | None = None,
        **replacements: str,
    ) -> Error:
        if self.fix:
            line, current_column = self._line, self._column
        else:
            line, current_column = self.getpos()
            line -= 1  # Convert from HTMLParser's 1-based to 0-based
        line += line_offset
        if column is None:
            column = current_column

        return Error(
            line=line,
            column=column,
            rule=Rule.get(rule_code),
            replacements=replacements,
        )
