"""Tests for types module functionality."""

import pytest

from cutesy.rules import Rule
from cutesy.types import (
    ConfigurationError,
    DoctypeError,
    Error,
    IndentationType,
    InstructionType,
    Mode,
    StructuralError,
)

# Constants to avoid magic numbers
SAMPLE_LINE_NUMBER = 10
SAMPLE_COLUMN_NUMBER = 5
EXPECTED_BLOCK_STARTS_COUNT = 3
EXPECTED_BLOCK_CONTINUATIONS_COUNT = 2
EXPECTED_BLOCK_ENDS_COUNT = 3

# Error messages as constants
DOCTYPE_ERROR_MESSAGE = "Non-HTML5 doctype found"
CONFIG_ERROR_MESSAGE = "Invalid configuration"
PARSE_FAILED_MESSAGE = "Parse failed"


class TestMode:
    """Test Mode enum functionality."""

    def test_mode_has_document_and_unstructured(self) -> None:
        """Test Mode has DOCUMENT and UNSTRUCTURED values."""
        assert hasattr(Mode, "DOCUMENT")
        assert hasattr(Mode, "UNSTRUCTURED")
        assert Mode.DOCUMENT is not None
        assert Mode.UNSTRUCTURED is not None

    def test_mode_values_are_different(self) -> None:
        """Test Mode values are distinct."""
        assert Mode.DOCUMENT != Mode.UNSTRUCTURED


class TestIndentationType:
    """Test IndentationType enum functionality."""

    def test_indentation_types(self) -> None:
        """Test IndentationType has TAB and SPACES values."""
        assert IndentationType.TAB is not None
        assert IndentationType.SPACES is not None
        assert IndentationType.TAB != IndentationType.SPACES


class TestError:
    """Test Error dataclass functionality."""

    def test_error_creation(self) -> None:
        """Test Error can be created with required fields."""
        rule = Rule("TEST1", "Test rule", fixable=True, structural=False)
        error = Error(
            line=SAMPLE_LINE_NUMBER,
            column=SAMPLE_COLUMN_NUMBER,
            rule=rule,
            replacements={"old": "new"},
        )

        assert error.line == SAMPLE_LINE_NUMBER
        assert error.column == SAMPLE_COLUMN_NUMBER
        assert error.rule == rule
        assert error.replacements == {"old": "new"}

    def test_error_with_empty_replacements(self) -> None:
        """Test Error with empty replacements dict."""
        rule = Rule("TEST2", "Another rule", fixable=False, structural=True)
        error = Error(line=1, column=1, rule=rule, replacements={})

        assert error.replacements == {}


class TestExceptions:
    """Test custom exception classes."""

    def test_doctype_error(self) -> None:
        """Test DoctypeError can be raised and caught."""
        with pytest.raises(DoctypeError):
            raise DoctypeError(DOCTYPE_ERROR_MESSAGE)

    def test_configuration_error(self) -> None:
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError(CONFIG_ERROR_MESSAGE)

    def test_structural_error_with_errors(self) -> None:
        """Test StructuralError with attached errors."""
        rule = Rule("TEST3", "Structural rule", fixable=False, structural=True)
        error = Error(line=1, column=1, rule=rule, replacements={})

        structural_error = StructuralError(PARSE_FAILED_MESSAGE, errors=[error])

        assert structural_error.errors == [error]
        assert len(structural_error.errors) == 1

    def test_structural_error_empty_errors(self) -> None:
        """Test StructuralError with empty errors list."""
        structural_error = StructuralError(PARSE_FAILED_MESSAGE, errors=[])
        assert structural_error.errors == []


class TestInstructionType:
    """Test InstructionType enum functionality."""

    def test_instruction_type_values(self) -> None:
        """Test InstructionType has all expected values."""
        assert InstructionType.PARTIAL.value == "a"
        assert InstructionType.END_PARTIAL.value == "b"
        assert InstructionType.CONDITIONAL.value == "c"
        assert InstructionType.MID_CONDITIONAL.value == "d"
        assert InstructionType.LAST_CONDITIONAL.value == "e"
        assert InstructionType.END_CONDITIONAL.value == "f"
        assert InstructionType.REPEATABLE.value == "g"
        assert InstructionType.END_REPEATABLE.value == "h"
        assert InstructionType.VALUE.value == "i"
        assert InstructionType.FREEFORM.value == "j"
        assert InstructionType.END_FREEFORM.value == "k"
        assert InstructionType.COMMENT.value == "l"
        assert InstructionType.END_COMMENT.value == "m"
        assert InstructionType.IGNORED.value == "n"

    def test_block_starts_classproperty(self) -> None:
        """Test block_starts returns correct instruction types."""
        starts = InstructionType.block_starts

        assert InstructionType.PARTIAL in starts
        assert InstructionType.CONDITIONAL in starts
        assert InstructionType.REPEATABLE in starts
        assert len(starts) == EXPECTED_BLOCK_STARTS_COUNT

    def test_block_continuations_classproperty(self) -> None:
        """Test block_continuations returns correct instruction types."""
        continuations = InstructionType.block_continuations

        assert InstructionType.MID_CONDITIONAL in continuations
        assert InstructionType.LAST_CONDITIONAL in continuations
        assert len(continuations) == EXPECTED_BLOCK_CONTINUATIONS_COUNT

    def test_block_ends_classproperty(self) -> None:
        """Test block_ends returns correct instruction types."""
        ends = InstructionType.block_ends

        assert InstructionType.END_PARTIAL in ends
        assert InstructionType.END_CONDITIONAL in ends
        assert InstructionType.END_REPEATABLE in ends
        assert len(ends) == EXPECTED_BLOCK_ENDS_COUNT

    def test_regex_range_classmethod(self) -> None:
        """Test regex_range returns correct character range."""
        range_str = InstructionType.regex_range()
        assert range_str == "[a-k]"

    def test_is_group_start_property(self) -> None:
        """Test is_group_start property for various instruction types."""
        assert InstructionType.PARTIAL.is_group_start is True
        assert InstructionType.CONDITIONAL.is_group_start is True
        assert InstructionType.REPEATABLE.is_group_start is True

        assert InstructionType.END_PARTIAL.is_group_start is False
        assert InstructionType.VALUE.is_group_start is False
        assert InstructionType.FREEFORM.is_group_start is False

    def test_is_group_middle_property(self) -> None:
        """Test is_group_middle property for various instruction types."""
        assert InstructionType.MID_CONDITIONAL.is_group_middle is True
        assert InstructionType.LAST_CONDITIONAL.is_group_middle is True

        assert InstructionType.PARTIAL.is_group_middle is False
        assert InstructionType.END_PARTIAL.is_group_middle is False
        assert InstructionType.VALUE.is_group_middle is False

    def test_all_instruction_types_have_unique_values(self) -> None:
        """Test all instruction types have unique character values."""
        values = [instruction_type.value for instruction_type in InstructionType]
        assert len(values) == len(set(values))  # No duplicates

    def test_instruction_types_form_continuous_range(self) -> None:
        """Test instruction types form a continuous character range."""
        values = sorted([instruction_type.value for instruction_type in InstructionType])

        # Should be continuous from 'a' to some letter
        expected = [chr(ord("a") + index) for index in range(len(values))]
        assert values == expected

    def test_starts_block_property(self) -> None:
        """Test starts_block property (if it exists)."""
        # Test that block-starting types have this property
        assert hasattr(InstructionType.PARTIAL, "starts_block")

    def test_continues_block_property(self) -> None:
        """Test continues_block property (if it exists)."""
        # Test that block-continuing types work correctly
        mid_types = InstructionType.block_continuations
        for instruction_type in mid_types:
            assert hasattr(instruction_type, "continues_block")

    def test_ends_block_property(self) -> None:
        """Test ends_block property (if it exists)."""
        # Test that block-ending types work correctly
        end_types = InstructionType.block_ends
        for instruction_type in end_types:
            assert hasattr(instruction_type, "ends_block")


class TestInstructionTypeProperties:
    """Test InstructionType instance properties to achieve 100% coverage."""

    def test_is_group_start_all_types(self) -> None:
        """Test is_group_start property for all instruction types."""
        # Test all types to ensure we hit line 138 (the missing coverage)
        group_start_types = {
            InstructionType.PARTIAL,
            InstructionType.CONDITIONAL,
            InstructionType.REPEATABLE,
        }

        for instruction_type in InstructionType:
            expected = instruction_type in group_start_types
            assert instruction_type.is_group_start == expected

    def test_is_group_middle_all_types(self) -> None:
        """Test is_group_middle property for all instruction types."""
        group_middle_types = {InstructionType.MID_CONDITIONAL, InstructionType.LAST_CONDITIONAL}

        for instruction_type in InstructionType:
            expected = instruction_type in group_middle_types
            assert instruction_type.is_group_middle == expected

    def test_instruction_type_edge_cases(self) -> None:
        """Test edge cases for instruction type properties."""
        # Test specific types that might not be covered elsewhere
        assert InstructionType.COMMENT.is_group_start is False
        assert InstructionType.END_COMMENT.is_group_start is False
        assert InstructionType.IGNORED.is_group_start is False

        assert InstructionType.COMMENT.is_group_middle is False
        assert InstructionType.END_COMMENT.is_group_middle is False
        assert InstructionType.IGNORED.is_group_middle is False
