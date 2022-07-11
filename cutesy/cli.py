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
    num_errors = 0
    num_files_modified = 0
    num_files_failed = 0

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
            num_files_failed += 1
            errors = preprocessing_error.errors
        else:
            if fix and html != result:
                with open(path, mode="w") as html_file:
                    html_file.write(result)
                    print(f"Fixed {path}")  # noqa: T201 (CLI output)
                num_files_modified += 1

        if errors:
            errors_by_file[str(path)] = errors
            num_errors += len(errors)

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

    if errors_by_file:
        maybe_s_1 = "" if num_errors == 1 else "s"
        maybe_s_2 = "" if len(errors_by_file) == 1 else "s"

        if fix:
            if num_files_modified:
                maybe_s_3 = "" if num_files_modified == 1 else "s"
                print(  # noqa: T201 (CLI output)
                    f"\033[1mFixed {num_files_modified} file{maybe_s_3}, "
                    + f"\033[91m\033[1m{num_errors} problḙ̴͈͝m{maybe_s_1} le̴ft\033[0m in "
                    + f"{len(errors_by_file)} file{maybe_s_2}",
                )
            else:
                print(  # noqa: T201 (CLI output)
                    f"🔪 \033[91m\033[1m{num_errors} pro̵ble̴m{maybe_s_1} lef̴̥͆t\033[0m in "
                    + f"{len(errors_by_file)} file{maybe_s_2}",
                )

        else:
            print(  # noqa: T201 (CLI output)
                f"🔪 \033[91m\033[1m{num_errors} proble̴m{maybe_s_1}\033[0m fo̵͖̔u̷nd in "
                + f"{len(errors_by_file)} file{maybe_s_2}",
            )

        if return_zero:
            exit(0)
        exit(1)

    if fix:
        if num_files_modified:
            maybe_s = "" if num_files_modified == 1 else "s"
            print(  # noqa: T201 (CLI output)
                f"\033[1mFixed {num_files_modified} file{maybe_s}, no problems left\033[0m 🥰",
            )
        else:
            print("\033[1mNothing to fix\033[0m 🥰")  # noqa: T201 (CLI output)

    else:
        print("\033[1mNo problems found\033[0m 🥰")  # noqa: T201 (CLI output)

    exit(0)
