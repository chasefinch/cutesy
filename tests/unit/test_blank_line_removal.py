"""Tests for blank line removal functionality."""

from cutesy.linter import HTMLLinter
from cutesy.preprocessors import django


class TestBlankLineRemovalAfterOpeningTags:
    """Test blank line removal after opening tags."""

    def test_single_blank_line_after_opening_tag(self) -> None:
        """Test removal of single blank line after opening tag."""
        html = """<!doctype html>
<div>

\tcontent
</div>
"""
        expected = """<!doctype html>
<div>
\tcontent
</div>
"""
        linter = HTMLLinter(fix=True)
        result, _errors = linter.lint(html)

        assert result == expected

    def test_multiple_blank_lines_after_opening_tag(self) -> None:
        """Test removal of multiple blank lines after opening tag."""
        html = """<!doctype html>
<div>



\tcontent
</div>
"""
        expected = """<!doctype html>
<div>
\tcontent
</div>
"""
        linter = HTMLLinter(fix=True)
        result, _errors = linter.lint(html)

        assert result == expected

    def test_blank_line_detection_without_fix(self) -> None:
        """Test F4 error reported for blank line after opening tag w/o fix."""
        html = """<!doctype html>
<div>

\tcontent
</div>
"""
        linter = HTMLLinter(fix=False)
        _result, errors = linter.lint(html)

        f4_errors = [error for error in errors if error.rule.code == "F4"]
        assert len(f4_errors) >= 1

    def test_nested_tags_with_blank_lines(self) -> None:
        """Test nested tags with blank lines after each opening."""
        html = """<!doctype html>
<div>

\t<span>
\t
\t\tcontent
\t</span>
</div>
"""
        expected = """<!doctype html>
<div>
\t<span>
\t\tcontent
\t</span>
</div>
"""
        linter = HTMLLinter(fix=True)
        result, _errors = linter.lint(html)

        assert result == expected


class TestBlankLineRemovalBeforeClosingTags:
    """Test blank line removal before closing tags."""

    def test_single_blank_line_before_closing_tag(self) -> None:
        """Test removal of single blank line before closing tag."""
        html = """<!doctype html>
<div>
\tcontent

</div>
"""
        expected = """<!doctype html>
<div>
\tcontent
</div>
"""
        linter = HTMLLinter(fix=True)
        result, _errors = linter.lint(html)

        assert result == expected

    def test_multiple_blank_lines_before_closing_tag(self) -> None:
        """Test removal of multiple blank lines before closing tag."""
        html = """<!doctype html>
<div>
\tcontent



</div>
"""
        expected = """<!doctype html>
<div>
\tcontent
</div>
"""
        linter = HTMLLinter(fix=True)
        result, _errors = linter.lint(html)

        assert result == expected

    def test_blank_line_before_closing_detection_without_fix(self) -> None:
        """Test F4 error reported for blank line before closing tag."""
        html = """<!doctype html>
<div>
\tcontent

</div>
"""
        linter = HTMLLinter(fix=False)
        _result, errors = linter.lint(html)

        f4_errors = [error for error in errors if error.rule.code == "F4"]
        assert len(f4_errors) >= 1

    def test_both_opening_and_closing_blank_lines(self) -> None:
        """Test removal of blank lines after opening and before closing."""
        html = """<!doctype html>
<div>

\tcontent
\t
</div>
"""
        expected = """<!doctype html>
<div>
\tcontent
</div>
"""
        linter = HTMLLinter(fix=True)
        result, _errors = linter.lint(html)

        assert result == expected


class TestBlankLineRemovalWithInstructions:
    """Test blank line removal with template instructions."""

    def test_blank_line_after_opening_instruction(self) -> None:
        """Test removal of blank line after opening instruction."""
        html = """<!doctype html>
{% if condition %}

\tcontent
{% endif %}
"""
        expected = """<!doctype html>
{% if condition %}
\tcontent
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected

    def test_blank_line_before_closing_instruction(self) -> None:
        """Test removal of blank line before closing instruction."""
        html = """<!doctype html>
{% if condition %}
\tcontent

{% endif %}
"""
        expected = """<!doctype html>
{% if condition %}
\tcontent
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected

    def test_blank_lines_around_instruction_continuations(self) -> None:
        """Test removal of blank lines around else/elif."""
        html = """<!doctype html>
{% if a %}

\tcontent_a
\t
{% else %}

\tcontent_b
\t
{% endif %}
"""
        expected = """<!doctype html>
{% if a %}
\tcontent_a
{% else %}
\tcontent_b
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected

    def test_elif_with_blank_lines(self) -> None:
        """Test blank line removal around elif."""
        html = """<!doctype html>
{% if a %}
\tA

{% elif b %}

\tB

{% endif %}
"""
        expected = """<!doctype html>
{% if a %}
\tA
{% elif b %}
\tB
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected


class TestMixedTagsAndInstructions:
    """Test blank line removal with mixed tags and instructions."""

    def test_tag_containing_instruction_with_blank_lines(self) -> None:
        """Test blank lines in tag containing instruction."""
        html = """<!doctype html>
<div>

\t{% if x %}
\t
\t\tcontent
\t\t
\t{% endif %}
\t
</div>
"""
        expected = """<!doctype html>
<div>
\t{% if x %}
\t\tcontent
\t{% endif %}
</div>
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected

    def test_instruction_containing_tag_with_blank_lines(self) -> None:
        """Test blank lines in instruction containing tag."""
        html = """<!doctype html>
{% if condition %}

\t<div>
\t
\t\tcontent
\t\t
\t</div>
\t
{% endif %}
"""
        expected = """<!doctype html>
{% if condition %}
\t<div>
\t\tcontent
\t</div>
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected

    def test_complex_interleaving_with_blank_lines(self) -> None:
        """Test complex interleaving of tags and instructions."""
        html = """<!doctype html>
<body>

\t{% if a %}
\t
\t\t<div>
\t\t
\t\t\t{% if b %}
\t\t\t
\t\t\t\tX
\t\t\t\t
\t\t\t{% endif %}
\t\t\t
\t\t</div>
\t\t
\t{% endif %}
\t
</body>
"""
        expected = """<!doctype html>
<body>
\t{% if a %}
\t\t<div>
\t\t\t{% if b %}
\t\t\t\tX
\t\t\t{% endif %}
\t\t</div>
\t{% endif %}
</body>
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        assert result == expected


class TestIndentationReset:
    """Test indentation level reset for block endings."""

    def test_indentation_resets_on_endif(self) -> None:
        """Test indentation resets correctly on endif."""
        html = """<!doctype html>
{% if outer %}
\t{% if inner %}
\t\tcontent
\t{% endif %}
\tmore content
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        # Check that indentation is preserved correctly
        assert "\t{% if inner %}" in result
        assert "\t{% endif %}" in result
        assert "{% endif %}" in result

    def test_indentation_resets_on_else(self) -> None:
        """Test indentation matches between if and else."""
        html = """<!doctype html>
{% if condition %}
\tcontent
{% else %}
\tother
{% endif %}
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        lines = result.split("\n")
        if_line = next(line for line in lines if "{% if condition %}" in line)
        else_line = next(line for line in lines if "{% else %}" in line and "if" not in line)

        # Both should have same indentation
        if_indent = len(if_line) - len(if_line.lstrip("\t"))
        else_indent = len(else_line) - len(else_line.lstrip("\t"))
        assert if_indent == else_indent

    def test_indentation_resets_with_mixed_structures(self) -> None:
        """Test indentation reset with mixed tags and instructions."""
        html = """<!doctype html>
<div>
\t{% if a %}
\t\t<span>content</span>
\t{% endif %}
</div>
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, _errors = linter.lint(html)

        # Verify structure is preserved correctly
        assert "\t{% if a %}" in result
        assert "\t\t<span>" in result
        assert "\t{% endif %}" in result
        assert "</div>" in result


class TestUnbalancedStructures:
    """Test error reporting for unbalanced structures."""

    def test_unclosed_tag_before_endif(self) -> None:
        """Test D3 error for unclosed tag before endif."""
        html = """<!doctype html>
{% if condition %}
\t<div>
{% endif %}
"""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())
        _result, errors = linter.lint(html)

        d3_errors = [error for error in errors if error.rule.code == "D3"]
        assert len(d3_errors) == 1
        # Should NOT have P2 error
        p2_errors = [error for error in errors if error.rule.code == "P2"]
        assert len(p2_errors) == 0

    def test_multiple_unclosed_tags_before_endif(self) -> None:
        """Test D3 errors for multiple unclosed tags."""
        html = """<!doctype html>
{% if condition %}
\t<div>
\t\t<span>
{% endif %}
"""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())
        _result, errors = linter.lint(html)

        d3_errors = [error for error in errors if error.rule.code == "D3"]
        expected_error_count = 2
        assert len(d3_errors) == expected_error_count  # span and div

    def test_balanced_structure_no_errors(self) -> None:
        """Test balanced structure produces no errors."""
        html = """<!doctype html>
{% if condition %}
\t<div>
\t\tcontent
\t</div>
{% endif %}
"""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())
        _result, errors = linter.lint(html)

        assert len(errors) == 0

    def test_unclosed_tag_before_else(self) -> None:
        """Test D3 error for unclosed tag before else."""
        html = """<!doctype html>
{% if condition %}
\t<div>
{% else %}
\tcontent
{% endif %}
"""
        linter = HTMLLinter(fix=False, preprocessor=django.Preprocessor())
        _result, errors = linter.lint(html)

        d3_errors = [error for error in errors if error.rule.code == "D3"]
        assert len(d3_errors) >= 1


class TestIdempotency:
    """Test fix mode idempotence (running twice produces same result)."""

    def test_single_pass_removes_all_blank_lines(self) -> None:
        """Test single pass removes all blank lines."""
        html = """<!doctype html>
{% if True %}





\tasdf!




{% endif %}
</div>
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result1, errors1 = linter.lint(html)

        # Run again on result
        linter2 = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result2, errors2 = linter2.lint(result1)

        # Should be idempotent
        assert result1 == result2
        assert len(errors1) == len(errors2)

    def test_fix_mode_idempotent_on_complex_structure(self) -> None:
        """Test fix mode is idempotent on complex structures."""
        html = """<!doctype html>
<div>

\t{% if x %}
\t
\t\t<span>

\t\t\tcontent
\t\t\t
\t\t</span>
\t\t
\t{% endif %}
\t
</div>
"""
        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result1, _ = linter.lint(html)

        linter2 = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result2, _ = linter2.lint(result1)

        assert result1 == result2
