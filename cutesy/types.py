"""Types to support Cutesy."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto, unique
from typing import cast

from classproperties import classproperty
from data_enum import DataEnum

from .rules import Rule


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


class ConfigurationError(Exception):
    """An exception that can be thrown when the config is misconfigured."""


class StructuralError(Exception):
    """An exception that can be thrown when a required parse or fix fails."""

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

    @classproperty
    def block_starts(cls) -> set["InstructionType"]:  # noqa: N805 (Classproperty convention)
        """Return a set of instruction types which start a block."""
        starts: set[InstructionType] = {
            cast("InstructionType", cls.PARTIAL),
            cast("InstructionType", cls.CONDITIONAL),
            cast("InstructionType", cls.REPEATABLE),
        }
        return starts

    @classproperty
    def block_continuations(cls) -> set["InstructionType"]:  # noqa: N805
        """Return a set of instruction types which continue a block."""
        continuations: set[InstructionType] = {
            cast("InstructionType", cls.MID_CONDITIONAL),
            cast("InstructionType", cls.LAST_CONDITIONAL),
        }
        return continuations

    @classproperty
    def block_ends(cls) -> set["InstructionType"]:  # noqa: N805
        """Return a set of instruction types which end a block."""
        ends: set[InstructionType] = {
            cast("InstructionType", cls.END_PARTIAL),
            cast("InstructionType", cls.END_CONDITIONAL),
            cast("InstructionType", cls.END_REPEATABLE),
        }
        return ends

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
    def starts_block(self) -> bool:
        """Whether this instruction type causes an increase in indentation."""
        return self in self.block_starts

    @property
    def continues_block(self) -> bool:
        """Whether this instruction type continues a block."""
        return self in self.block_continuations

    @property
    def ends_block(self) -> bool:
        """Whether this instruction type causes a decrease in indentation."""
        return self in self.block_ends
