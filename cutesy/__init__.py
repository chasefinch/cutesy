"""Lint & autoformat an HTML document in Python."""
# Standard Library
import re
import string
from dataclasses import dataclass
from enum import Enum, unique
from html.parser import HTMLParser

# Third Party
from data_enum import DataEnum


def is_whitespace(char):
    """Return whether char is a whitespace character."""
    return char in string.whitespace


class DoctypeError(Exception):
    """An error that can be raised when encountering a non-HTML5 doctype."""


class PreprocessingError(Exception):
    """An exception that can be thrown when preprocessing fails."""

    def __init__(self, *args, errors, **kwargs):
        """Initialize the error with attached errors."""
        super().__init__(*args, **kwargs)

        self.errors = errors


class Rule(DataEnum):
    """A rule to lint against."""

    primary_attribute = "code"
    data_attributes = ("message",)


# Temporary preprocessing rules
Rule("T1", "Instruction not long enough to generate a placeholder")

# Preprocessing rules
Rule("P1", "{tag} overlaps HTML elements or attributes")
Rule("P2", "Expected {tag}")  # Expected closing instruction
Rule("P3", "{tag} doesn’t have a matching opening instruction")
Rule("P4", "Malformed processing instruction")
Rule("P5", "Nonstandard whitespace in {tag}")

# Document structure rules
Rule("D1", "Expected doctype before other HTML elements")
Rule("D2", "Second declaration found; “doctype” should be the only declaration")
Rule("D3", "Expected {tag}")  # Expected closing tag
Rule("D4", "{tag} doesn’t have a matching opening tag")
Rule("D5", "Unnecessary self-closing of {tag}")
Rule("D6", "Self-closing of non-void element {tag}")
Rule("D7", "Malformed tag")
Rule("D8", "Malformed closing tag")

# Formatting rules
Rule("F1", "Doctype not lowercase")
Rule("F2", "Trailing whitespace")
Rule("F3", "Incorrect indentation")
Rule("F4", "Extra vertical whitespace")
Rule("F5", "Extra horizontal whitespace")
Rule("F6", "Incorrect attribute order")
Rule("F7", "{tag} not lowercase")
Rule("F8", "Attribute “{attr}” not lowercase")
Rule("F9", "Attribute “{attr}” missing quotes")
Rule("F10", "Attribute “{attr}” using wrong quotes")
Rule("F11", "{tag} contains whitespace")
Rule("F12", "Nonstandard whitespace in {tag}")

# Encoding & language rules
Rule("E1", "Doctype not “html”")
Rule("E2", "Ampersand not represented as “&amp;”")
Rule("E3", "Left angle bracket not represented as “&lt;”")
Rule("E4", "Right angle bracket not represented as “&gt;”")


class Mode(DataEnum):
    """A state to represent the structure of the HTML."""


Mode.DOCUMENT = Mode()
Mode.UNSTRUCTURED = Mode()


@dataclass
class Error:
    """An issue to be reported by the linter."""

    line: int
    column: int
    rule: Rule
    replacements: dict


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


@unique
class InstructionType(Enum):
    """A single letter to represent each type of dynamic instruction.

    For regex performance reasons, these characters form a complete character
    range, [a-k].
    """

    # Increase indentation
    PARTIAL = "a"  # noqa: WPS115 (Caps preferred for Enums)

    # Decrease indentation, reset HTML indentation
    END_PARTIAL = "b"  # noqa: WPS115 (Caps preferred for Enums)

    # Conditional: Increase indentation
    CONDITIONAL = "c"  # noqa: WPS115 (Caps preferred for Enums)

    # Decrease & increase indentation
    MID_CONDITIONAL = "d"  # noqa: WPS115 (Caps preferred for Enums)

    # Decrease & increase indentation
    LAST_CONDITIONAL = "e"  # noqa: WPS115 (Caps preferred for Enums)

    # Decrease indentation, ensure consistent HTML tag use
    END_CONDITIONAL = "f"  # noqa: WPS115 (Caps preferred for Enums)

    # Increase indentation
    REPEATABLE = "g"  # noqa: WPS115 (Caps preferred for Enums)

    END_REPEATABLE = "h"  # noqa: WPS115 (Caps preferred for Enums)

    # Decrease indentation, ensure repeatable HTML tag use
    VALUE = "i"  # noqa: WPS115 (Caps preferred for Enums)

    # Stop processing
    FREEFORM = "j"  # noqa: WPS115 (Caps preferred for Enums)

    # Resume processing
    END_FREEFORM = "k"  # noqa: WPS115 (Caps preferred for Enums)

    # Stop processing, treat contents as string
    COMMENT = "l"  # noqa: WPS115 (Caps preferred for Enums)

    # Resume processing
    END_COMMENT = "m"  # noqa: WPS115 (Caps preferred for Enums)

    # Ignore for processing
    IGNORED = "n"  # noqa: WPS115 (Caps preferred for Enums)

    @classmethod
    def regex_range(cls):
        """Match all (and only) the character values."""
        return "[a-k]"

    @property
    def is_group_start(self):
        """Whether this instruction type starts a linked group."""
        return self in {
            InstructionType.PARTIAL,
            InstructionType.CONDITIONAL,
            InstructionType.REPEATABLE,
        }

    @property
    def is_group_middle(self):
        """Whether this instruction type continues a linked group."""
        return self in {
            InstructionType.MID_CONDITIONAL,
            InstructionType.LAST_CONDITIONAL,
        }

    @property
    def is_group_end(self):
        """Whether this instruction type ends a linked group."""
        return self in {
            InstructionType.END_PARTIAL,
            InstructionType.END_CONDITIONAL,
            InstructionType.END_REPEATABLE,
        }

    @property
    def should_increase_indentation(self):
        """Whether this instruction type causes an increase in indentation."""
        return self in {
            InstructionType.PARTIAL,
            InstructionType.CONDITIONAL,
            InstructionType.MID_CONDITIONAL,
            InstructionType.LAST_CONDITIONAL,
            InstructionType.REPEATABLE,
        }

    @property
    def should_decrease_indentation(self):
        """Whether this instruction type causes a decrease in indentation."""
        return self in {
            InstructionType.END_PARTIAL,
            InstructionType.MID_CONDITIONAL,
            InstructionType.LAST_CONDITIONAL,
            InstructionType.END_CONDITIONAL,
            InstructionType.END_REPEATABLE,
        }


class HTMLLinter(HTMLParser):
    """A parser to ingest HTML and lint it."""

    def __init__(self, fix=False, check_doctype=False, preprocessor=None, *args, **kwargs):
        """Initialize HTMLLinter."""
        super().__init__(*args, **kwargs)

        self.fix = fix
        self.check_doctype = check_doctype
        self.preprocessor = preprocessor

        self.convert_charrefs = False
        self.indentation = "\t"
        self.tab_width = 4
        self.long_attr_value_length = 10
        self.xlong_attr_value_length = 28
        self.xxlong_attr_value_length = 60

        self.attr_sort = lambda attr: (
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
            # Push these keys to the end
            (attr[0] or "").startswith("on"),
            (attr[0] or "").startswith("data-"),
            attr[0],
        )

    def reset(self):
        """Reset the state of the linter so that it can be run again."""
        super().reset()

        self._mode = None
        self._errors = []
        self._result = []

        self._did_report_expected_doctype = False
        self._freeform_level = 0
        self._indentation_level = 0
        self._tag_stack = []

        # Possible values: {None, True} if self.fix else {None, str}
        self._expected_indentation = None

        self._line = 0
        self._column = 0

    def lint(self, html):
        """Run the server-side-rendering routine."""
        self.reset()

        html_data = html

        if self.preprocessor:
            self.preprocessor.reset(html_data, self.fix)
            html_data = self.preprocessor.process()

        try:
            self.feed(html_data)
        except PreprocessingError as preprocessing_error:
            # Update the line & column numbers for the errors.
            self.preprocessor.restore(html_data, preprocessing_error.errors)
            raise preprocessing_error

        self.close()

        result = "".join(self._result) if self.fix else html_data
        errors = self._errors

        if self.preprocessor:
            result = self.preprocessor.restore(result, errors)  # modifies "errors"

        return result, errors

    def handle_decl(self, decl):
        """Process a declaration string."""
        self._reconcile_indentation()

        if self._mode:
            self._log_error(
                {
                    Mode.DOCUMENT: "D2",
                    Mode.UNSTRUCTURED: "D1",
                }[self._mode],
            )
            if self.fix:
                self._process(f"<!{decl}>")
            return

        decl_lower = decl.lower()
        if decl_lower != "doctype html":
            if not self.check_doctype:
                raise DoctypeError

            self._log_error("E1")

        self._mode = Mode.DOCUMENT

        if self.fix:
            self._process(f"<!{decl_lower}>")
        elif decl != decl_lower:
            self._log_error("F1")

    def handle_startendtag(self, tag, attrs):
        """Process a self-closing tag."""
        self.handle_starttag(tag, attrs)

        tag = tag.lower()
        if tag in VOID_ELEMENTS:
            if not self.fix:
                self._log_error("D5", tag=f"<{tag}>")

        else:
            if not self.fix:
                self._log_error("D6", tag=f"<{tag}>")

            self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs):
        """Process a start tag."""
        self._did_encounter_data()
        self._reconcile_indentation()

        if not self.fix and tag != tag.lower():
            self._log_error("F7", tag=f"<{tag}>")

        tag = tag.lower()

        if not self.fix:
            for attr in attrs:
                if attr[0] != attr[0].lower():
                    self._log_error("F8", attr=attr[0])

        num_long_attrs = 0
        num_xlong_attrs = 0
        num_xxlong_attrs = 0
        num_breaking_attrs = 0
        for attr in attrs:
            value_length = max(len(attr[0]), len(attr[1] or ""))
            if value_length >= self.long_attr_value_length:
                num_long_attrs += 1
            if value_length >= self.xlong_attr_value_length:
                num_xlong_attrs += 1
            if value_length >= self.xxlong_attr_value_length:
                num_xxlong_attrs += 1
            if attr[1] and any((char in attr[1] for char in ("\n", "\t"))):
                num_breaking_attrs += 1

        _, attr_strings = self._make_attr_strings(attrs)

        should_wrap = any(
            (
                len(attr_strings) > 5,
                num_long_attrs > 2,
                num_xlong_attrs > 0 and num_long_attrs > 1,
                num_xxlong_attrs > 0 and len(attr_strings) > 1,
                num_breaking_attrs > 0,
            ),
        )
        if should_wrap:
            indentation = self.indentation * (self._indentation_level + 1)
            value_indentation = f"{indentation}{self.indentation}"
            end_char = self.indentation * self._indentation_level

            adjusted_attr_strings = []
            indentations = (" " * self.tab_width, "\t")
            for attr_string in attr_strings:
                adjusted_attr_string = attr_string
                if "\n" in adjusted_attr_string:
                    name_etc, value = adjusted_attr_string.split('"', 1)
                    value = value[:-1]  # Strip trailing quote
                    lines = value.rstrip().split("\n")

                    if len(lines) == 1:
                        adjusted_attr_string = lines[0].strip()
                    else:
                        special_first_line = None
                        indentation_and_lines = []

                        if not lines[0].startswith("\n"):
                            special_first_line = lines.pop(0).strip()

                        for line in lines:
                            num_indents = 0
                            index = 0
                            while any((line[index:].startswith(char) for char in indentations)):
                                num_indents += 1
                                if line[index:].startswith(" "):
                                    index += self.tab_width
                                else:
                                    index += 1

                            indentation_and_lines.append((num_indents, line.strip()))

                        min_indents = min(line_info[0] for line_info in indentation_and_lines)
                        if special_first_line:
                            indentation_and_lines.insert(0, (min_indents, special_first_line))

                        indented_lines = []
                        for line_info in indentation_and_lines:
                            line_indentation = self.indentation * (line_info[0] - min_indents)
                            indented_lines.append(f"{line_indentation}{line_info[1]}")

                        value = f"\n{value_indentation}".join(indented_lines)
                        adjusted_attr_string = (
                            f'{name_etc}"\n{value_indentation}{value}\n{indentation}"'
                        )
                adjusted_attr_strings.append(adjusted_attr_string)

            attrs_string = f"\n{indentation}".join(adjusted_attr_strings)
            attrs_string = f"\n{indentation}{attrs_string}\n{end_char}"
        elif attr_strings:
            attrs_string = " ".join(attr_strings)
            attrs_string = f" {attrs_string}"
        else:
            attrs_string = ""

        if not self.fix:
            new_whitespace = list(filter(is_whitespace, list(attrs_string)))
            old_whitespace = list(filter(is_whitespace, list(self.__starttag_text)))

            if new_whitespace != old_whitespace:
                self._log_error("P5", tag=f"<{tag}>")

        if tag not in VOID_ELEMENTS:
            self._tag_stack.append((tag, self._indentation_level))

            if tag != "html":
                self._indentation_level += 1

        if self.fix:
            self._process(f"<{tag}{attrs_string}>")

    def handle_endtag(self, tag):
        """Process a closing tag."""
        if not self.fix and tag != tag.lower():
            self._log_error("F7", tag=f"</{tag}>")

        tag = tag.lower()

        if tag in {tag_info[0] for tag_info in self._tag_stack}:
            while self._tag_stack:
                expected_tag = self._tag_stack.pop()
                if expected_tag[0] == tag:
                    self._indentation_level = expected_tag[1]
                    break
                self._log_error("D3", tag=f"</{expected_tag[0]}>")
        else:
            self._log_error("D4", tag=f"</{tag}>")

        if tag != self.cdata_elem:
            self._reconcile_indentation()

        if self.fix:
            self._process(f"</{tag}>")

    def handle_data(self, html_data):
        """Process HTML data."""
        self._did_encounter_data()
        self._reconcile_indentation()

        if self.cdata_elem or self._freeform_level:
            if self.fix:
                self._process(html_data)
            return

        indentation = self.indentation * self._indentation_level

        trailing_whitespace = r"[ \t]+\n"
        if self.fix:
            html_data = re.sub(trailing_whitespace, "\n", html_data)

        else:
            for match in re.finditer(trailing_whitespace, html_data):
                start = match.start()
                line_offset = html_data.count("\n", 0, start)
                column = html_data.rfind("\n", 0, start) - 1
                self._log_error("F2", line_offset=line_offset, column=column)

        some_indentation = r"\n[ \t]*"
        new_html_data = re.sub(some_indentation, f"\n{indentation}", html_data)

        if indentation:
            blank_line = f"\n{indentation}\n"

            while blank_line in new_html_data:
                new_html_data = new_html_data.replace(blank_line, "\n\n")

            if new_html_data.endswith(f"\n{indentation}"):
                new_html_data = new_html_data[: -1 * len(indentation)]
                self._expected_indentation = True

        if self.fix:
            html_data = new_html_data
        else:
            html_lines = html_data.split("\n")
            new_html_lines = new_html_data.split("\n")
            for index, line in enumerate(new_html_lines):
                if index == len(new_html_lines) - 1 and not line:
                    if not self.fix:
                        self._expected_indentation = html_lines[index]
                    break

                original_line = html_lines[index]
                if line != original_line:
                    self._log_error("F3", line_offset=index, column=0)

        extra_vertical_lines = r"\n{3,}"
        if self.fix:
            html_data = re.sub(extra_vertical_lines, "\n\n", html_data)
        else:
            for match in re.finditer(extra_vertical_lines, html_data):
                line_offset = html_data.count("\n", 0, match.start())
                self._log_error("F4", line_offset=line_offset, column=0)

        lines = []
        for index, line in enumerate(html_data.split("\n")):
            line_contents = line
            line_start = ""
            if index > 0:
                line_contents = line_contents.lstrip()
                line_start = line[: len(line) - len(line_contents)]

            trimmed_line_contents = line_contents.lstrip()
            leading_space = " " if 0 < len(trimmed_line_contents) < len(line_contents) else ""

            trimmed_line_contents = line_contents.rstrip()
            trailing_space = " " if len(trimmed_line_contents) < len(line_contents) else ""

            new_line_contents = " ".join(line_contents.split())
            new_line_contents = f"{leading_space}{new_line_contents}{trailing_space}"
            if self.fix:
                line = f"{line_start}{new_line_contents}"
            elif line_contents != new_line_contents:
                # Find first character where the differ
                column = next(
                    (
                        column
                        for column in range(min(len(line_contents), len(new_line_contents)))
                        if line_contents[column] != new_line_contents[column]
                    ),
                    None,
                )

                self._log_error("F5", line_offset=index, column=len(line_start) + column)

            lines.append(line)

        if self.fix:
            self._process("\n".join(lines))

    def handle_instruction(self, instruction_text):
        """Process a dynamic template instruction placeholder."""
        instruction_type = InstructionType(instruction_text[0])

        if instruction_type == InstructionType.FREEFORM:
            self._freeform_level += 1
        elif instruction_type == InstructionType.END_FREEFORM:
            self._freeform_level -= 1

        if instruction_type.should_decrease_indentation:
            self._indentation_level -= 1

        self._reconcile_indentation()

        if instruction_type.should_increase_indentation:
            self._indentation_level += 1

        if self.fix:
            wraps = self.preprocessor.delimiters
            self._process(f"{wraps[0]}{instruction_text}{wraps[1]}")

    def handle_entityref(self, name):
        """Process an HTML entity."""
        self._did_encounter_data()
        self._reconcile_indentation()

        if self.fix:
            self._process(f"&{name};")

    def handle_charref(self, name):
        """Process a numbered HTML entity."""
        self._did_encounter_data()
        self._reconcile_indentation()

        if self.fix:
            self._process(f"&#{name};")

    def handle_comment(self, comment):
        """Process an HTML comment."""
        self._reconcile_indentation()

        if self.fix:
            self._process(f"<!--{comment}-->")

    def goahead(self, end):
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
            if match:
                cursor2 = match.start()
            else:
                cursor2 = size
            if cursor < cursor2:
                self.handle_data(rawdata[cursor:cursor2])
            cursor = self.updatepos(cursor, cursor2)
            if cursor == size:
                break

            startswith = rawdata.startswith

            if self.preprocessor:
                prefix, postfix = self.preprocessor.delimiters
                if startswith(prefix, cursor):
                    cursor2 = rawdata.find(postfix, cursor + 1)  # Should always be >= 0
                    instruction_text = rawdata[cursor + 1 : cursor2]
                    self.handle_instruction(instruction_text)
                    cursor = self.updatepos(cursor, cursor2 + 1)
                    continue

            if self._freeform_level:
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
                    self._log_error("E3")
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
                    self._log_error("E2")

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
                if self.fix:
                    ref_data = "&amp;"
                else:
                    ref_data = "&"
                    self._log_error("E2")

                self.handle_data(ref_data)
                cursor = self.updatepos(cursor, cursor + 1)

        # end while
        if cursor < size:
            self.handle_data(rawdata[cursor:size])
            cursor = self.updatepos(cursor, size)
        self.rawdata = rawdata[cursor:]

    def parse_starttag(self, cursor):
        """Parse a start tag.

        Adapted from:
        https://github.com/python/cpython/blob/3.10/Lib/html/parser.py
        """
        attrfind_tolerant = re.compile(
            r'((?<=[\'"\s/])[^\s/>][^\s/=>]*)(\s*=+\s*'
            + r'(\'[^\']*\'|"[^"]*"|(?![\'"])[^>\s]*))?(?:\s|/(?!>))*',
        )

        tagfind_tolerant = re.compile(r"([a-zA-Z][^\t\n\r\f />\x00]*)(?:\s|/(?!>))*")
        rawdata = self.rawdata

        self.__starttag_text = None  # noqa: WPS112 (copied)
        end_cursor = self.check_for_whole_start_tag(cursor)
        if end_cursor < 0:
            if self.preprocessor:
                wraps = self.preprocessor.delimiters
                wrap_regex = re.escape(wraps[0])
                overlap = re.compile(
                    rf"<([a-zA-Z][-.a-zA-Z0-9:_]*){wrap_regex}",
                )
                match = overlap.match(rawdata, cursor)
                if match:
                    line, column = self.getpos()
                    raise self.preprocessor.make_error(
                        "P1",
                        line=line,
                        column=column,
                        tag="Instruction",
                    )

            self._log_error("D7")
            return end_cursor

        self.__starttag_text = rawdata[cursor:end_cursor]  # noqa: WPS112 (copied)

        attrs = []
        match = tagfind_tolerant.match(rawdata, cursor + 1)
        cursor2 = match.end()

        tag = match.group(1)
        self.lasttag = tag.lower()
        while cursor2 < end_cursor:
            match = attrfind_tolerant.match(rawdata, cursor2)
            if not match:
                break

            attrname, rest, attrvalue = match.group(1, 2, 3)
            if not rest:
                attrvalue = None
            elif attrvalue[:1] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
            elif attrvalue[:1] == "'" == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
                if '"' not in attrvalue:
                    self._log_error("F10", attr=attrname)
            elif not self.fix:
                self._log_error("F9", attr=attrname)

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

    def parse_endtag(self, cursor):
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
                    line, column = self.getpos()
                    raise self.preprocessor.make_error(
                        "P1",
                        line=line,
                        column=column,
                        tag="Instruction",
                    )

            self._log_error("D8")
            return -1

        end_cursor = match.end()
        tag = match.group(1)

        parsed_data = rawdata[cursor:end_cursor]
        if any((char in string.whitespace for char in rawdata[cursor:end_cursor])):
            if self.fix:
                parsed_data = re.sub(r"\s", "", parsed_data)
            else:
                self._log_error("F11", tag=f"</{tag}>")

        if self.cdata_elem is not None and tag.lower() != self.cdata_elem:
            # script or style
            self.handle_data(parsed_data)
            return end_cursor

        self.handle_endtag(tag)
        self.clear_cdata_mode()

        return end_cursor

    def _process(self, html_chunk):
        self._result.append(html_chunk)

        len_chunk = len(html_chunk)
        num_lines = html_chunk.count("\n")
        self._line += num_lines
        if num_lines:
            self._column = len_chunk - html_chunk.rfind("\n") - 1
        else:
            self._column += len_chunk

    def _did_encounter_data(self):
        self._mode = self._mode or Mode.UNSTRUCTURED

    def _reconcile_indentation(self, adjustment=0):
        if self._expected_indentation is None:
            return

        indentation = self.indentation * (self._indentation_level + adjustment)
        if self.fix:
            self._process(indentation)
        elif self._expected_indentation != indentation:
            self._log_error("F3", column=0)

        self._expected_indentation = None

    def _make_attr_strings(self, attrs):
        """Return the prepared attribute strings.

        Recursively handles dynamic attributes, prepending them with the
        indentation characters.

        The first return value is a key for sorting the whole set in a higher-
        level set. The second is a list of attribute strings.
        """
        all_attrs = []
        for attr in attrs:
            name, value = attr
            name = name.lower()

            if self.preprocessor:
                wraps = self.preprocessor.delimiters
                while wraps[0] in name:
                    start_index = name.index(wraps[0])
                    end_index = name.index(wraps[1]) + 1

                    if start_index > 0:
                        split_name = name[:start_index]
                        quote_char = "'" if '"' in split_name else '"'
                        all_attrs.append((split_name, value, quote_char))

                    split_name = name[start_index:end_index]
                    quote_char = "'" if '"' in split_name else '"'
                    all_attrs.append((split_name, None, quote_char))

                    name = name[end_index:]
            if name:
                quote_char = "'" if '"' in (value or "") else '"'
                all_attrs.append((name, value, quote_char))

        attr_groups_by_key = []

        index = 0
        group_level = 0

        group = []
        while index < len(all_attrs):
            name, value, quote_char = all_attrs[index]
            attr = name, value

            instruction_type = None
            if self.preprocessor and name.startswith(self.preprocessor.delimiters[0]):
                instruction_type = InstructionType(name[1])

            if instruction_type and instruction_type.is_group_start:
                group_level += 1
                if group_level == 1:
                    group.append(name)
                    group_key = None
                    subgroup_attrs = []
                else:
                    subgroup_attrs.append(attr)
            elif instruction_type and instruction_type.is_group_middle:
                if group_level == 1:
                    subgroup_key, subgroup = self._make_attr_strings(subgroup_attrs)
                    group_key = min((group_key, subgroup_key)) if group_key else subgroup_key
                    group += [f"{self.indentation}{attr_string}" for attr_string in subgroup]
                    group.append(name)
                    subgroup_attrs = []
                else:
                    subgroup_attrs.append(attr)
            elif instruction_type and instruction_type.is_group_end:
                if group_level == 1:
                    subgroup_key, subgroup = self._make_attr_strings(subgroup_attrs)
                    group_key = min((group_key, subgroup_key)) if group_key else subgroup_key
                    group += [f"{self.indentation}{attr_string}" for attr_string in subgroup]
                    group.append(name)
                    attr_groups_by_key.append((group_key, group))
                else:
                    subgroup_attrs.append(attr)
                group_level -= 1
            elif group_level:
                subgroup_attrs.append(attr)
            else:
                attr_string = name
                if value is not None:
                    attr_string = f"{attr_string}={quote_char}{value}{quote_char}"
                attr_groups_by_key.append((name, [attr_string]))

            index += 1

        if self.fix:
            attr_groups_by_key.sort(key=self.attr_sort)
        else:
            sorted_groups = sorted(attr_groups_by_key, key=self.attr_sort)
            if attr_groups_by_key != sorted_groups:
                self._log_error("F6")

        try:
            sort_key = attr_groups_by_key[0][0]
        except IndexError:
            sort_key = None

        attr_strings = []
        for _, group in attr_groups_by_key:
            if (  # noqa: WPS337 (Dynamic loop condition)
                len(group) == 3
                and "\n" not in group[1]
                and len(group[1][len(self.indentation)]) <= self.long_attr_value_length
            ):
                group[1] = group[1][len(self.indentation) :]  # Strip leading indentation
                attr_strings.append("".join(group))
            elif len(group) == 2:
                attr_strings.append("".join(group))
            else:
                attr_strings.extend(group)

        return sort_key, attr_strings

    def _log_error(self, rule_code, line_offset=0, column=None, **kwargs):
        line, current_column = (self._line, self._column) if self.fix else self.getpos()
        line += line_offset
        if column is None:
            column = current_column

        replacements = {}
        for keyword, value in kwargs.items():
            replacements[keyword] = value

        self._errors.append(
            Error(
                line=line,
                column=column,
                rule=Rule.get(rule_code),
                replacements=replacements,
            ),
        )
