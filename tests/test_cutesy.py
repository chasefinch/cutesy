"""Tests for HTMLLinter and related functionality."""

# Cutesy
from cutesy import HTMLLinter
from cutesy.preprocessors import django


class TestLinter:
    """Test the HTMLLinter class."""

    def test_basic(self):
        """Test the baseline HTML structure."""
        basic_html = ""
        expected_result = ""

        linter = HTMLLinter(fix=True)
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_entityref(self):
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

    def test_charref(self):
        """Test parsing charrefs."""
        basic_html = "<span>Hi! &#x999; </span>"
        expected_result = "<span>Hi! &#x999; </span>"

        linter = HTMLLinter(fix=True)
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors

    def test_preprocessor(self):
        """Test preprocessing."""
        basic_html = "<span>Hi! &#x999; {% block %}{% endblock %} </span>"
        expected_result = "<span>Hi! &#x999; {% block %}{% endblock %} </span>"

        linter = HTMLLinter(fix=True, preprocessor=django.Preprocessor())
        result, errors = linter.lint(basic_html)

        assert result == expected_result
        assert not errors
