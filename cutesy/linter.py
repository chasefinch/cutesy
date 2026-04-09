"""Lint & format an HTML document in Python."""

import re
import string
from collections.abc import Sequence
from enum import Enum, auto
from html.parser import HTMLParser
from typing import Any, Final, Literal, NamedTuple, Never, TypeGuard

from .attribute_processors import BaseAttributeProcessor
from .foreign_content import (
    FOREIGN_CONTENT_ELEMENTS,
    get_correct_attr_name,
    get_correct_tag_name,
)
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
    original_text: str = ""  # original template instruction text (instructions only)


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
        self._result = []  # Accumulator for fixed output (fix mode only)

        self._did_report_expected_doctype = False
        self._freeform_level = 0  # >0 inside {% verbatim %} blocks
        self._indentation_level = 0  # Current nesting depth

        # Tags and template instructions share one stack so nesting
        # mismatches (e.g. <div>{% endif %}) are caught
        self._tag_stack: list[StackItem] = []

        # Deferred indentation: set by handle_data when it strips trailing
        # whitespace before a newline. Resolved by _reconcile_indentation
        # when the next element begins.
        #   None  = no pending indentation
        #   True  = pending (fix mode, exact string not yet known)
        #   str   = pending (lint mode, original whitespace to compare)
        self._expected_indentation: str | Literal[True] | None = ""

        # Pre-scanned minimum whitespace prefix for CDATA (script/style)
        # content. Computed once when entering CDATA mode so that all
        # handle_data chunks (split by template tags) share the same base.
        self._cdata_common_prefix: str | None = None

        # For detecting blank lines adjacent to opening/closing tags
        self._last_data: str | None = None
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
        """Process a self-closing tag (e.g. <br/>, <path d="..."/>).

        After handle_starttag, the tag is on the stack (if non-void).
        We then either: silently close it (foreign), warn about unnecessary
        self-close (void), or warn about invalid self-close (non-void).
        """
        # Opens the tag normally — pushes onto stack, emits output
        self.handle_starttag(tag, attrs)

        tag_lower = tag.lower()
        foreign_context = self._get_foreign_content_context()

        if foreign_context or tag_lower in FOREIGN_CONTENT_ELEMENTS:
            # SVG/MathML: self-closing is valid XML syntax, just close it
            correct_tag = get_correct_tag_name(tag_lower, foreign_context or tag_lower)
            self.handle_endtag(correct_tag)
        elif tag_lower in VOID_ELEMENTS:
            # Void elements (br, img, etc.): self-close is unnecessary
            if not self.fix:
                self._handle_error("D5", tag=f"<{tag_lower}>")
        else:
            # Non-void HTML elements: self-closing is invalid (e.g. <div/>)
            if not self.fix:
                self._handle_error("D6", tag=f"<{tag_lower}>")

            self.handle_endtag(tag_lower)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Process a start tag.

        State at entry: tag/attrs are raw from the parser (original casing).
        State at exit: tag is on _tag_stack (if non-void), _indentation_level
        is incremented, and the formatted tag is appended to _result (if fix).
        """
        self._handle_encountered_data()
        self._last_data = None
        self._prev_indentation_level = self._indentation_level

        is_new_line = self._expected_indentation is not None

        # --- Normalize tag casing ---
        # HTML → lowercase. SVG/MathML → spec-correct (e.g. clipPath).
        # When tag_lower is "svg"/"math", we're entering foreign content
        # but the tag itself isn't on the stack yet, so we check both.
        tag_lower = tag.lower()
        foreign_context = self._get_foreign_content_context()

        if foreign_context or tag_lower in FOREIGN_CONTENT_ELEMENTS:
            effective_context = foreign_context or tag_lower
            correct_tag = get_correct_tag_name(tag_lower, effective_context)
            if not self.fix and tag != correct_tag:
                self._handle_error("F7", tag=f"<{tag}>")
            tag = correct_tag
        else:
            if not self.fix and tag != tag_lower:
                self._handle_error("F7", tag=f"<{tag}>")
            tag = tag_lower

        # Attributes on <svg>/<math> itself also need foreign-context casing,
        # even though the tag hasn't been pushed onto the stack yet
        if foreign_context:
            attr_foreign_context: str | None = foreign_context
        elif tag_lower in FOREIGN_CONTENT_ELEMENTS:
            attr_foreign_context = tag_lower
        else:
            attr_foreign_context = None

        num_attrs = len(attrs)
        solo = num_attrs == 1

        # --- Two-pass attribute processing ---
        # Pass 1 (final_pass=False): measure attr lengths without reporting
        # errors, to decide whether attributes should wrap to multiple lines.
        _, attr_strings = self._make_attr_strings(
            attrs,
            solo=solo,
            final_pass=False,
            foreign_context=attr_foreign_context,
        )

        # Determine if any attribute contains a line break (e.g. multi-line
        # class lists, code content, template conditionals)
        has_breaking_attr = any(
            char in attr_string for attr_string in attr_strings for char in ("\n", "\t")
        )

        # Estimate total line length to decide if we need to wrap
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

        # Edge case: a single attribute has a line break (e.g. a long class
        # list). We temporarily step back one indentation level so the
        # attribute's internal content gets the right indentation depth.
        single_attribute_wrap = has_breaking_attr and not wrap
        if single_attribute_wrap:
            self._indentation_level -= 1

        # Pass 2 (final_pass=True): re-render attrs at the resolved
        # indentation level, and report any errors (F8, F17, etc.)
        _, attr_strings = self._make_attr_strings(
            attrs,
            solo=solo,
            foreign_context=attr_foreign_context,
        )

        if single_attribute_wrap:
            # Restore indentation level after re-rendering
            self._indentation_level += 1

            # Re-check: the attr may no longer break at the new depth
            has_breaking_attr = any(
                char in attr_string for attr_string in attr_strings for char in ("\n", "\t")
            )
            if not has_breaking_attr:
                wrap = False

        # If wrapping is needed but we're inline, try to insert a line break
        if wrap and not is_new_line:
            fix_f12 = self.fix and not self.is_rule_ignored("F12")
            if fix_f12 and self._break_for_inline_tag():
                self._process("\n")
                self._expected_indentation = True
                is_new_line = True
            else:
                self._handle_error("F12", tag=f"<{tag}>")

        # Emit any pending indentation before the tag
        self._reconcile_indentation()

        # Only wrap if we're actually at the start of a line
        wrap = wrap and is_new_line

        # --- Format the final tag string ---
        if wrap:
            # Each attr on its own line, indented one level deeper than the tag
            indentation_level = self._indentation_level + 1
            indentation = self.indentation * indentation_level
            attrs_string = f"\n{indentation}".join(attr_strings)

            end_char = self.indentation * (indentation_level - 1)
            attrs_string = f"\n{indentation}{attrs_string}\n{end_char}"
        elif attr_strings:
            attrs_string = " ".join(attr_strings)
            attrs_string = f" {attrs_string}"
        else:
            attrs_string = ""

        # Collapse blank lines within the attribute block
        attrs_string = re.sub(rf"\n({self.indentation})+\n", "\n\n", attrs_string)

        # In lint mode, compare whitespace layout to detect formatting errors
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

        # --- Update the tag stack ---
        # Non-void tags get pushed so handle_endtag can match them later.
        # The stored name uses correct casing (e.g. "clipPath" not "clippath").
        if tag not in VOID_ELEMENTS:
            self._tag_stack.append(
                StackItem(StackItemType.TAG, tag, self._indentation_level, self.getpos()[0]),
            )

            if tag != "html":
                self._indentation_level += 1

        if self.fix:
            self._process(f"<{tag}{attrs_string}>")

    def handle_endtag(self, tag: str) -> None:
        """Process a closing tag.

        State at entry: tag is raw from the parser (original casing).
        State at exit: matching StackItem is popped from _tag_stack,
        _indentation_level is restored to the opening tag's level, and
        the formatted closing tag is appended to _result (if fix).
        """
        # --- Normalize tag casing (same logic as handle_starttag) ---
        tag_lower = tag.lower()
        foreign_context = self._get_foreign_content_context()

        if foreign_context:
            correct_tag = get_correct_tag_name(tag_lower, foreign_context)
            if not self.fix and tag != correct_tag:
                self._handle_error("F7", tag=f"</{tag}>")
            tag = correct_tag
        else:
            if not self.fix and tag != tag_lower:
                self._handle_error("F7", tag=f"</{tag}>")
            tag = tag_lower

        # --- Void element closing tag check ---
        # Void elements (br, img, etc.) cannot have closing tags.
        if tag in VOID_ELEMENTS and not foreign_context:
            if not self.fix:
                self._handle_error("D10", tag=f"<{tag}>")
            return

        # Snapshot indentation before popping, so we can detect blank-line
        # issues between the last content and this closing tag
        old_indentation_level = self._indentation_level
        opening_line = None

        # --- Pop the stack to find the matching opening tag ---
        # Stack names use correct casing (e.g. "clipPath"), so end-tag must
        # match. Any intervening items are reported as unclosed.
        if tag in {item.name for item in self._tag_stack if item.item_type == StackItemType.TAG}:
            while self._tag_stack:
                stack_item = self._tag_stack.pop()

                if stack_item.item_type == StackItemType.TAG and stack_item.name == tag:
                    # Found the match — restore indentation to opening level
                    self._indentation_level = stack_item.indentation
                    opening_line = stack_item.line
                    break
                if stack_item.item_type == StackItemType.TAG:
                    # Skipped over an unclosed tag
                    self._handle_error("D3", tag=f"</{stack_item.name}>")
                else:
                    # Skipped over an unclosed template instruction
                    original = stack_item.original_text or str(stack_item.name)
                    self._handle_error("D3", tag=f"closing instruction for {original}")
        else:
            # No matching opener on the stack at all
            self._handle_error("D4", tag=f"</{tag}>")
            if self._indentation_level > 0:
                self._indentation_level -= 1

        # --- Blank-line cleanup before closing tags ---
        # If indentation decreased (i.e. we actually closed something) and
        # there's trailing whitespace before this tag, clean it up
        if (
            self._indentation_level < old_indentation_level
            and self._last_data
            and opening_line != self.getpos()[0]
        ):
            match = re.search(r"\n\s*\n\s*$", self._last_data)
            if match:
                if self.fix:
                    if self._result:
                        last_chunk = self._result[-1]
                        self._result[-1] = re.sub(r"\n\s*\n\s*$", r"\n", last_chunk)
                else:
                    line_offset = self._last_data[: match.start()].count("\n")
                    self._handle_error("F4", line_offset=line_offset, column=0)

        self._reconcile_indentation()

        if self.fix:
            self._process(f"</{tag}>")

    def handle_data(self, html_data: str) -> None:
        """Process raw text content between tags.

        Applies multiple passes over the text:
        1. Blank-line cleanup after opening tags
        2. Trailing whitespace removal (F2)
        3. Indentation normalization (F3)
        4. Consecutive blank line collapse (F4)
        5. Horizontal whitespace collapse (F5)
        """
        # Stash for handle_endtag's blank-line-before-close check
        self._last_data = html_data

        self._handle_encountered_data()
        self._reconcile_indentation()

        # Inside freeform template blocks: emit verbatim
        if self._freeform_level:
            if self.fix:
                self._process(html_data)
            return

        # Inside <script>/<style>: rebase indentation, skip other passes
        if self.cdata_elem:
            self._process_cdata_content(html_data)
            return

        # --- Pass 1: blank lines after opening tags ---
        # If we just increased indentation (an opening tag was processed),
        # strip leading blank lines from the content that follows it
        if self._indentation_level > self._prev_indentation_level:
            # Match: newline followed by any blank lines at the start
            match = re.search(r"^\n[ \t]*\n", html_data)
            if match:
                if self.fix:
                    # Remove ALL leading blank lines, keeping just one newline
                    html_data = re.sub(r"^(\n[ \t]*)+\n", "\n", html_data)
                # Only report if there's NOT 3+ consecutive newlines (that's
                # reported elsewhere)
                elif not re.search(r"\n{3,}", html_data):
                    # Report F4 error for extra vertical whitespace
                    self._handle_error("F4", line_offset=0, column=0)

        indentation = self.indentation * self._indentation_level

        # --- Pass 2: trailing whitespace (F2) ---
        trailing_whitespace = r"[ \t]+\n"
        if self.fix:
            html_data = re.sub(trailing_whitespace, "\n", html_data)

        else:
            for match in re.finditer(trailing_whitespace, html_data):
                start = match.start()
                line_offset = html_data.count("\n", 0, start)
                column = html_data.rfind("\n", 0, start) - 1
                self._handle_error("F2", line_offset=line_offset, column=column)

        # --- Pass 3: indentation normalization (F3) ---
        # Replace all existing indentation with the expected amount.
        # new_html_data is the "ideal" version; we compare against it to
        # find errors, or use it directly in fix mode.
        some_indentation = r"\n[ \t]*"
        new_html_data = re.sub(some_indentation, f"\n{indentation}", html_data)

        # Don't indent blank lines — keep them truly empty
        if indentation:
            blank_line = f"\n{indentation}\n"

            while blank_line in new_html_data:
                new_html_data = new_html_data.replace(blank_line, "\n\n")

        if new_html_data.endswith(f"\n{indentation}"):
            # Strip trailing indentation — the next tag/data will emit its
            # own via _reconcile_indentation. Store a flag so reconcile knows
            # indentation is pending.
            if indentation:
                new_html_data = new_html_data[: -1 * len(indentation)]

            self._expected_indentation = True

        if self.fix:
            html_data = new_html_data
        else:
            # In lint mode, diff line-by-line against the ideal version
            html_lines = html_data.split("\n")
            new_html_lines = new_html_data.split("\n")
            for i, line in enumerate(new_html_lines):
                if i == len(new_html_lines) - 1 and not line:
                    # Last line is blank — we don't know the next element's
                    # indentation yet. Stash the original for reconcile to
                    # compare against later.
                    if not self.fix:
                        self._expected_indentation = html_lines[i]
                    break

                original_line = html_lines[i]
                if line != original_line:
                    self._handle_error("F3", line_offset=i, column=0)

        # --- Pass 4: consecutive blank lines (F4) ---
        extra_vertical_lines = r"\n{3,}"
        if self.fix:
            html_data = re.sub(extra_vertical_lines, "\n\n", html_data)
        else:
            for match in re.finditer(extra_vertical_lines, html_data):
                line_offset = html_data.count("\n", 0, match.start())
                self._handle_error("F4", line_offset=line_offset, column=0)

        # --- Pass 5: horizontal whitespace collapse (F5) ---
        # Collapse runs of spaces/tabs within each line's content, preserving
        # leading/trailing single spaces (which may be significant).
        lines = []
        for i, line in enumerate(html_data.split("\n")):
            original_line = line
            line_contents = line
            line_start = ""

            # Separate indentation from content (only for continuation lines;
            # line 0 may start mid-tag so its leading space is content)
            if i > 0:
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

                self._handle_error("F5", line_offset=i, column=len(line_start) + column)

            lines.append(original_line)

        if self.fix:
            self._process("\n".join(lines))

    def handle_instruction(self, instruction_text: str) -> None:
        """Process a dynamic template instruction placeholder.

        Template instructions ({% if %}, {% for %}, etc.) are managed on
        _tag_stack alongside HTML tags. Block-start instructions push,
        block-end instructions pop, and continuations ({% else %}) pop
        then re-push. This mirrors how handle_starttag/handle_endtag
        manage indentation for HTML elements.
        """
        instruction_type = InstructionType(instruction_text[0])

        # Freeform blocks (e.g. {% verbatim %}) suppress all formatting
        if instruction_type == InstructionType.FREEFORM:
            self._freeform_level += 1
        elif instruction_type == InstructionType.END_FREEFORM:
            self._freeform_level -= 1

        old_indentation_level = self._indentation_level
        opening_line = None

        # --- Pop the stack for block-end / continuation instructions ---
        # Mirrors handle_endtag: walk the stack to find the matching opener,
        # restoring its indentation level. Any intervening items are unclosed.
        if instruction_type.ends_block or instruction_type.continues_block:
            found_match = False
            while self._tag_stack:
                stack_item = self._tag_stack.pop()

                if stack_item.item_type == StackItemType.INSTRUCTION:
                    self._indentation_level = stack_item.indentation
                    opening_line = stack_item.line

                    if instruction_type.continues_block:
                        # {% else %} / {% elif %} must follow a block-start
                        # or another continuation
                        assert isinstance(stack_item.name, InstructionType)
                        if not (stack_item.name.starts_block or stack_item.name.continues_block):
                            original = self._restore_instruction(instruction_text)
                            self._handle_error("D3", tag=original)

                    found_match = True
                    break
                # Skipped an unclosed HTML tag while searching
                self._handle_error("D3", tag=f"</{stack_item.name}>")

            if not found_match:
                # No matching opening instruction found
                original = self._restore_instruction(instruction_text)
                self._handle_error("D4", tag=original)
                # Decrement anyway to try to recover
                if self._indentation_level > 0:
                    self._indentation_level -= 1

        # Check for blank lines before instruction that decreases indentation
        # Skip this check if the closing instruction is on the same line as
        # the opening instruction
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
                        # Replace multiple trailing newlines with single
                        # newline + indentation
                        self._result[-1] = re.sub(r"\n\s*\n\s*$", r"\n", last_chunk)
                else:
                    # Report F4 error for extra vertical whitespace
                    line_offset = self._last_data[: match.start()].count("\n")
                    self._handle_error("F4", line_offset=line_offset, column=0)

        # Emit indentation at the now-restored level (between pop and push)
        self._reconcile_indentation()

        self._prev_indentation_level = self._indentation_level

        # --- Push onto stack for block-start / continuation instructions ---
        # Block-start ({% if %}, {% for %}): push and indent children.
        # Continuation ({% else %}): was popped above, now re-push so the
        # next {% endif %} / {% else %} can find it.
        if instruction_type.starts_block or instruction_type.continues_block:
            original_text = ""
            if self.preprocessor:
                original_text = self.preprocessor.restore_instruction(instruction_text)
            self._tag_stack.append(
                StackItem(
                    StackItemType.INSTRUCTION,
                    instruction_type,
                    self._indentation_level,
                    self.getpos()[0],
                    original_text=original_text,
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
            # Inside <script>/<style>: skip straight to the closing tag,
            # emitting the entire content (including any preprocessor
            # placeholders) as one handle_data call so indentation
            # rebasing sees complete lines.
            if self.cdata_elem:
                # Use a case-insensitive regex instead of rawdata.lower()
                # because str.lower() can change string length with certain
                # Unicode characters (e.g. İ → i̇), corrupting positions.
                close_match = re.search(
                    rf"</{re.escape(self.cdata_elem)}\s*>",
                    rawdata[cursor:],
                    re.IGNORECASE,
                )
                close_pos = cursor + close_match.start() if close_match else -1
                if close_pos < 0:
                    self.handle_data(rawdata[cursor:size])
                    cursor = self.updatepos(cursor, size)
                    break
                if cursor < close_pos:
                    self.handle_data(rawdata[cursor:close_pos])
                cursor = self.updatepos(cursor, close_pos)
                cursor2 = self.parse_endtag(cursor)
                cursor = self.updatepos(cursor, cursor2)
                continue

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
                self._scan_cdata_min_prefix(end_cursor)

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

    def _get_foreign_content_context(self) -> str | None:
        """Return the foreign content context type, or None if in normal HTML.

        Scans the tag stack for the innermost <svg> or <math> ancestor.
        """
        for stack_item in reversed(self._tag_stack):
            if (
                stack_item.item_type == StackItemType.TAG
                and stack_item.name in FOREIGN_CONTENT_ELEMENTS
            ):
                return stack_item.name
        return None

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

    def _scan_cdata_min_prefix(self, start_pos: int) -> None:
        """Pre-scan CDATA content to find the minimum whitespace prefix.

        Called once when entering CDATA mode so that every handle_data
        chunk (which may be split by template-tag placeholders) shares
        the same base indentation for rebasing.
        """
        rawdata = self.rawdata
        tag = self.cdata_elem
        assert tag is not None

        # Find the closing tag using a case-insensitive regex instead
        # of rawdata.lower() — str.lower() can change string length with
        # certain Unicode characters (e.g. İ → i̇), corrupting positions.
        close_match = re.search(
            rf"</{re.escape(tag)}\s*>",
            rawdata[start_pos:],
            re.IGNORECASE,
        )
        if not close_match:
            self._cdata_common_prefix = None
            return

        cdata_content = rawdata[start_pos : start_pos + close_match.start()]

        min_prefix: str | None = None
        for line in cdata_content.split("\n")[1:]:
            stripped = line.lstrip(" \t")
            if not stripped:
                continue
            prefix = line[: len(line) - len(stripped)]
            if min_prefix is None or len(prefix) < len(min_prefix):
                min_prefix = prefix

        self._cdata_common_prefix = min_prefix

    def _process_cdata_content(self, html_data: str) -> None:
        """Process content inside <script>/<style> elements.

        Rebases indentation to match the HTML hierarchy while preserving
        the relative indentation structure of the CSS/JS content. Uses
        the pre-scanned _cdata_common_prefix so all chunks agree on the
        same base indentation.
        """
        indentation = self.indentation * self._indentation_level
        common = self._cdata_common_prefix

        # --- Indentation rebasing (F3) ---
        lines = html_data.split("\n")

        if common is None:
            new_html_data = html_data
        else:
            # Rebuild with rebased indentation
            new_lines = [lines[0]]
            for line in lines[1:]:
                if line.strip() and line.startswith(common):
                    new_lines.append(f"{indentation}{line[len(common) :]}")
                elif line.strip():
                    new_lines.append(f"{indentation}{line.lstrip()}")
                else:
                    new_lines.append("")

            new_html_data = "\n".join(new_lines)

        # Don't indent blank lines
        if indentation:
            blank_line = f"\n{indentation}\n"
            while blank_line in new_html_data:
                new_html_data = new_html_data.replace(blank_line, "\n\n")

        # Handle trailing indentation — strip it and mark as pending so
        # _reconcile_indentation can emit the correct level for the
        # closing tag
        if new_html_data.endswith(f"\n{indentation}"):
            if indentation:
                new_html_data = new_html_data[: -len(indentation)]
            self._expected_indentation = True
        elif new_html_data.endswith("\n"):
            self._expected_indentation = True

        if self.fix:
            self._process(new_html_data)
        else:
            # In lint mode, diff line-by-line against the ideal version
            html_lines = html_data.split("\n")
            new_html_lines = new_html_data.split("\n")
            for i, line in enumerate(new_html_lines):
                if i == len(new_html_lines) - 1 and not line:
                    # Last line is blank — stash original for reconcile
                    if i < len(html_lines):
                        self._expected_indentation = html_lines[i]
                    break

                if i < len(html_lines) and line != html_lines[i]:
                    self._handle_error("F3", line_offset=i, column=0)

    def _reconcile_indentation(self, adjustment: int = 0) -> None:
        """Emit or check pending indentation.

        Called before any output that follows a newline.
        _expected_indentation is set to True (fix mode) or the original
        whitespace string (lint mode) by handle_data when it strips
        trailing indentation from content. This method resolves that
        pending state by emitting the correct indentation or comparing
        against what was in the source.
        """
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
        foreign_context: str | None = None,
    ) -> tuple[str | None, Sequence[str]]:
        """Build formatted attribute strings for a single tag.

        Returns (sort_key, attr_strings) where sort_key is the first
        attribute name (for F6 ordering) and attr_strings is a list of
        formatted 'name="value"' strings ready to be joined into a tag.

        Called twice per tag in handle_starttag:
          - Pass 1 (final_pass=False): measure only, no error reporting
          - Pass 2 (final_pass=True): report F8/F17/F6 errors

        For template preprocessors, attributes may contain instruction
        delimiters (e.g. {% if %}class="x"{% endif %}). These are split
        into separate pieces and grouped for conditional rendering.
        """
        # --- Phase 1: Normalize attribute names and split template parts ---
        # Produces (name, value, quote_char) tuples with correct casing.
        all_attrs = []
        for incoming_attr in attrs:
            name, value = incoming_attr

            # Template preprocessor: an attr name may contain instruction
            # delimiters interleaved with real attr names. Split them apart
            # so each piece can be processed independently.
            if self.preprocessor:
                wraps = self.preprocessor.delimiters
                while wraps[0] in name:
                    start_index = name.index(wraps[0])
                    end_index = name.index(wraps[1]) + 1

                    # Text before the delimiter is a real attribute name
                    if start_index > 0:
                        split_name = name[:start_index]
                        split_name_lower = split_name.lower()
                        if foreign_context:
                            correct_name = get_correct_attr_name(
                                split_name_lower,
                                foreign_context,
                            )
                            if not self.fix and split_name != correct_name and final_pass:
                                self._handle_error("F8", attr=correct_name)
                            processed_name = correct_name
                        else:
                            if not self.fix and split_name != split_name_lower and final_pass:
                                self._handle_error("F8", attr=split_name_lower)
                            processed_name = split_name_lower

                        quote_char = "'" if '"' in processed_name else '"'
                        all_attrs.append((processed_name, value, quote_char))

                    # The delimiter itself is kept as-is (template instruction)
                    split_name = name[start_index:end_index]

                    quote_char = "'" if '"' in split_name else '"'
                    all_attrs.append((split_name, None, quote_char))

                    name = name[end_index:]

            # Remaining text (or the whole name if no preprocessor)
            if name:
                name_lower = name.lower()
                # Apply correct casing: spec-correct for SVG/MathML, lowercase
                # for HTML
                if foreign_context:
                    correct_name = get_correct_attr_name(name_lower, foreign_context)
                    if not self.fix and name != correct_name and final_pass:
                        self._handle_error("F8", attr=correct_name)
                    processed_name = correct_name
                else:
                    if not self.fix and name != name_lower and final_pass:
                        self._handle_error("F8", attr=name_lower)
                    processed_name = name_lower

                quote_char = "'" if '"' in (value or "") else '"'
                all_attrs.append((processed_name, value, quote_char))

        # --- Phase 2: Group attributes and process values ---
        # Template conditionals ({% if %}/{% endif %}) create groups of
        # attrs that are rendered together. group_level tracks nesting
        # depth of these conditional blocks.
        attr_keys_and_groups = []

        group_level = 0
        # Buffer top-level comments so they move with the next attribute
        # during F6 sorting (e.g. {# description #} before class="...")
        pending_comments: list[str] = []

        group = []
        for name, value, quote_char in all_attrs:
            attr = name, value

            instruction_type = None
            if self.preprocessor and name.startswith(self.preprocessor.delimiters[0]):
                instruction_type = InstructionType(name[1])

            if instruction_type == InstructionType.IGNORED and not group_level:
                pending_comments.append(name)
                continue

            if instruction_type and instruction_type.is_group_start:
                # Entering a conditional block (e.g. {% if %})
                group_level += 1
                if group_level == 1:
                    group = [name]
                    group_key: str | None = None
                    subgroup_attrs = []
                else:
                    # Nested conditional — collect into parent's subgroup
                    subgroup_attrs.append(attr)
            elif instruction_type and instruction_type.is_group_middle:
                # Continuation (e.g. {% else %}) — finalize current subgroup
                if group_level == 1:
                    subgroup_key, subgroup = self._make_attr_strings(
                        subgroup_attrs,
                        final_pass=False,
                        foreign_context=foreign_context,
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
                # Closing a conditional block (e.g. {% endif %})
                if group_level == 1:
                    subgroup_key, subgroup = self._make_attr_strings(
                        subgroup_attrs,
                        final_pass=False,
                        foreign_context=foreign_context,
                    )
                    if group_key and subgroup_key:
                        group_key = min(group_key, subgroup_key)
                    else:
                        group_key = group_key or subgroup_key
                    group += [f"{self.indentation}{attr_string}" for attr_string in subgroup]
                    group.append(name)
                    attr_keys_and_groups.append((group_key, [*pending_comments, *group]))
                    pending_comments = []
                else:
                    subgroup_attrs.append(attr)
                group_level -= 1
            elif group_level:
                # Inside a conditional block — accumulate for subgroup
                subgroup_attrs.append(attr)
            else:
                # Regular attribute (not inside a template conditional)
                attr_string = name
                if value is not None:
                    # Run each attribute processor (whitespace, reindent,
                    # tailwind, etc.) to normalize the value
                    processed_value = value
                    fix_f17 = self.fix and not self.is_rule_ignored("F17")
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
                        if processing_errors:
                            for processing_error in processing_errors:
                                self._handle_error(error=processing_error)
                        elif processed_value is None:
                            # Processor says this attr value should be removed
                            if not fix_f17 and final_pass:
                                self._handle_error("F17", attr=name)
                            break
                    # Compare against the original value after ALL processors
                    # have run. Checking inside the loop caused false positives
                    # when an earlier processor changed the value but a later
                    # one (e.g. Tailwind) normalized it back to the original.
                    if (
                        processed_value is not None
                        and not fix_f17
                        and value != processed_value
                        and final_pass
                    ):
                        self._handle_error("F17", attr=name)
                    if processed_value is None and self.fix:
                        continue
                    if processed_value is None:
                        processed_value = value
                    attr_string = f"{attr_string}={quote_char}{processed_value}{quote_char}"
                attr_keys_and_groups.append((name, [*pending_comments, attr_string]))
                pending_comments = []

        # Flush any trailing comments (attach to last group)
        if pending_comments and attr_keys_and_groups:
            last_key, last_group = attr_keys_and_groups[-1]
            attr_keys_and_groups[-1] = (last_key, [*last_group, *pending_comments])

        # --- Phase 3: Sort attributes (F6) ---
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

        # --- Phase 4: Flatten template conditional groups ---
        # Groups from template conditionals ({% if %}...{% endif %}) are
        # rendered as multi-line blocks. Short ones that fit on one line
        # get flattened for readability.
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
                inner_items = [item.removeprefix(self.indentation) for item in group[1:-1]]
                flat = f"{group[0]}{' '.join(inner_items)}{group[-1]}"
                attr_strings.append(flat)

            elif (
                len(group) == num_empty_dyamic_context_attrs
                and self.preprocessor
                and all(item.startswith(self.preprocessor.delimiters[0]) for item in group)
            ):
                # Empty conditional (e.g. {% if x %}{% endif %}) — no content
                attr_strings.append("".join(group))
            else:
                attr_strings.extend(group)

        return sort_key, attr_strings

    def _restore_instruction(self, placeholder_content: str) -> str:
        """Restore a placeholder's original instruction text for errors."""
        if self.preprocessor:
            return self.preprocessor.restore_instruction(placeholder_content)
        return f"{{{placeholder_content}}}"

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
