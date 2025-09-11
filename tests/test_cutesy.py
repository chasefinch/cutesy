"""Tests for HTMLLinter and related functionality."""

# Cutesy
from cutesy import HTMLLinter
from cutesy.preprocessors import django
from cutesy.types import IndentationType


class TestLinter:
    """Test the HTMLLinter class."""

    def test_basic(self) -> None:
        """Test the baseline HTML structure."""
        basic_html = ""
        expected_result = ""

        linter = HTMLLinter(fix=True)
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_entityref(self) -> None:
        """Test parsing charrefs."""
        linter = HTMLLinter(fix=True)

        basic_html = "<span>Hi! &amp; </span>"
        expected_result = "<span>Hi! &amp; </span>"

        result, errors = linter.lint(basic_html)
        assert result == expected_result
        assert not errors

        basic_html = "&copy;"
        expected_result = "&copy;"
        result, errors = linter.lint(basic_html)
        assert result == expected_result
        assert not errors

    def test_charref(self) -> None:
        """Test parsing charrefs."""
        basic_html = "<span>Hi! &#x999; </span>"
        expected_result = "<span>Hi! &#x999; </span>"

        linter = HTMLLinter(fix=True)
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_preprocessor(self) -> None:
        """Test preprocessing."""
        basic_html = "<span>Hi! &#x999; {% block %}{% endblock %} </span>"
        expected_result = "<span>Hi! &#x999; {% block %}{% endblock %} </span>"

        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_multiline_attr(self) -> None:
        """Test multiline attributes."""
        basic_html = """
<div
    x-data="() => {
        state1: true,

        state2: true,

        init() {
            state1 = false;
            state2 = false;
        }
    }"
>
asdf
</div>
        """
        expected_result = """
<div
    x-data="
        () => {
            state1: true,

            state2: true,

            init() {
                state1 = false;
                state2 = false;
            }
        }
    "
>
    asdf
</div>
"""

        linter = HTMLLinter(fix=True)
        linter.indentation_type = IndentationType.SPACES
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors
