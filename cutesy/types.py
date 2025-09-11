"""Types to support Cutesy."""

# Standard Library
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto, unique

# Third Party
from data_enum import DataEnum


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
Rule("P5", "Extra whitespace in {tag}")
Rule("P6", "Expected padding in {tag}")

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
Rule("F12", "Long tag {tag} should be on a new line")
Rule("F13", "Nonstandard whitespace in {tag}")
Rule("F14", "Expected {tag} attributes on new lines")
Rule("F15", "Expected {tag} attributes on a single line")

# Encoding & language rules
Rule("E1", "Doctype not “html”")
Rule("E2", "Ampersand not represented as “&amp;”")
Rule("E3", "Left angle bracket not represented as “&lt;”")
Rule("E4", "Right angle bracket not represented as “&gt;”")


class Mode(DataEnum):
    """A state to represent the structure of the HTML."""


Mode.DOCUMENT = Mode()
Mode.UNSTRUCTURED = Mode()


class IndentationType(Enum):
    """An indentation scheme."""

    TAB = auto()  # noqa: WPS115 (Caps preferred for Enums)
    SPACES = auto()  # noqa: WPS115 (Caps preferred for Enums)


@dataclass
class Error:
    """An issue to be reported by the linter."""

    line: int
    column: int
    rule: Rule
    replacements: dict[str, str]


class DoctypeError(Exception):
    """An error that can be raised when encountering a non-HTML5 doctype."""


class PreprocessingError(Exception):
    """An exception that can be thrown when preprocessing fails."""

    def __init__(self, *args: object, errors: Sequence[Error]) -> None:
        """Initialize the error with attached errors."""
        super().__init__(*args)

        self.errors = errors


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
    def regex_range(cls) -> str:
        """Match all (and only) the character values."""
        return "[a-k]"

    @property
    def is_group_start(self) -> bool:
        """Whether this instruction type starts a linked group."""
        return self in {
            InstructionType.PARTIAL,
            InstructionType.CONDITIONAL,
            InstructionType.REPEATABLE,
        }

    @property
    def is_group_middle(self) -> bool:
        """Whether this instruction type continues a linked group."""
        return self in {
            InstructionType.MID_CONDITIONAL,
            InstructionType.LAST_CONDITIONAL,
        }

    @property
    def is_group_end(self) -> bool:
        """Whether this instruction type ends a linked group."""
        return self in {
            InstructionType.END_PARTIAL,
            InstructionType.END_CONDITIONAL,
            InstructionType.END_REPEATABLE,
        }

    @property
    def increase_indentation(self) -> bool:
        """Whether this instruction type causes an increase in indentation."""
        return self in {
            InstructionType.PARTIAL,
            InstructionType.CONDITIONAL,
            InstructionType.MID_CONDITIONAL,
            InstructionType.LAST_CONDITIONAL,
            InstructionType.REPEATABLE,
        }

    @property
    def decrease_indentation(self) -> bool:
        """Whether this instruction type causes a decrease in indentation."""
        return self in {
            InstructionType.END_PARTIAL,
            InstructionType.MID_CONDITIONAL,
            InstructionType.LAST_CONDITIONAL,
            InstructionType.END_CONDITIONAL,
            InstructionType.END_REPEATABLE,
        }
