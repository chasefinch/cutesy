"""Tests for types module functionality."""

import pytest

from cutesy.rules import Rule
from cutesy.types import (
    ConfigurationError,
    DoctypeError,
    Error,
    InstructionType,
    StructuralError,
)

# Constants to avoid magic numbers
SAMPLE_LINE_NUMBER = 10
SAMPLE_COLUMN_NUMBER = 5

# Error messages as constants
DOCTYPE_ERROR_MESSAGE = "Non-HTML5 doctype found"
CONFIG_ERROR_MESSAGE = "Invalid configuration"
PARSE_FAILED_MESSAGE = "Parse failed"


class TestError:
    """Test Error dataclass functionality."""

    def test_error_creation(self) -> None:
        """Test Error can be created with required fields."""
        rule = Rule("TEST1", "Test rule", structural=False)
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
        rule = Rule("TEST2", "Another rule", structural=True)
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
        rule = Rule("TEST3", "Structural rule", structural=True)
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
