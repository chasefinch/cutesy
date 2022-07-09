"""Expose Cutesy via CLI."""

# Standard Library
from pathlib import Path

# Third Party
import click

# Current App
from . import DoctypeError, HTMLLinter, PreprocessingError
from .preprocessors import django


@click.command()
@click.option("--fix", is_flag=True)
@click.option("--return-zero", is_flag=True)
@click.option("--check-doctype", is_flag=True)
@click.option("--preprocessor")
@click.argument("pattern")
def main(fix, return_zero, check_doctype, preprocessor, pattern):
    """Lint the specified files."""
    preprocessor = {
        None: None,
        "django": django.Preprocessor(),
    }[preprocessor]

    linter = HTMLLinter(fix=fix, check_doctype=check_doctype, preprocessor=preprocessor)
    errors_by_file = {}

    for path in Path(".").glob(pattern):
        is_preprocessing_error = False

        with open(path, mode="r") as html_file:
            html = html_file.read()

        try:
            result, errors = linter.lint(html)
        except DoctypeError:
            continue
        except PreprocessingError as preprocessing_error:
            is_preprocessing_error = True
            errors = preprocessing_error.errors
        else:
            if fix and html != result:
                with open(path, mode="w") as html_file:
                    html_file.write(result)
                    print(f"Modified {path}.")  # noqa: T201 (CLI output)

        if errors:
            errors_by_file[str(path)] = errors

            print(f"\033[1m\033[4m{path}\033[0m")  # noqa: T201 (CLI output)

            if is_preprocessing_error:
                warning_part = "\033[91m\033[1mFATAL\033[0m  "
            else:
                warning_part = ""

            for error in errors:
                rule = error.rule

                len_error_line = len(str(error.line))
                location_width = 4 + max((len_error_line, 3))
                location_display = f"{error.line}:{error.column}".ljust(location_width)

                message = rule.message
                if error.replacements:
                    message = message.format(**error.replacements)
                print(  # noqa: T201 (CLI output)
                    f"  {warning_part}{location_display} {error.rule.code.ljust(3)} {message}",
                )

            print("")  # noqa: T201 (CLI output)

    if return_zero:
        exit(0)

    exit(1 if errors_by_file else 0)
