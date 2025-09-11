"""Expose Cutesy via CLI."""

# Standard Library
import sys
from pathlib import Path

# Third Party
import click

# Current App
from . import HTMLLinter
from .preprocessors import django
from .types import DoctypeError, PreprocessingError


@click.command()
@click.option(
    "--code",
    is_flag=True,
    help="Process the code passed in as a string, instead of searching PATTERN.",
)
@click.option("--fix", is_flag=True, help="Automatically fix problems when possible.")
@click.option(
    "--return-zero",
    is_flag=True,
    help="Always exit with 0, even if unfixed problems remain.",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Don't print individual problems.",
)
@click.option(
    "--check-doctype",
    is_flag=True,
    help="Process files with non-HTML5 doctypes. Without this flag, non-HTML5 files are skipped.",
)
@click.option(
    "--preprocessor",
    metavar="<str>",
    help="Use a preprocessor for dynamic HTML files. Try 'django'.",
)
@click.version_option()
@click.argument("pattern")
def main(
    code: bool,  # noqa: FBT001 (argument pattern)
    fix: bool,  # noqa: FBT001 (argument pattern)
    return_zero: bool,  # noqa: FBT001 (argument pattern)
    quiet: bool,  # noqa: FBT001 (argument pattern)
    check_doctype: bool,  # noqa: FBT001 (argument pattern)
    preprocessor: str,
    pattern: str,
) -> None:
    """Cutesy 🥰

    Lint (and optionally, fix & format) all files matching PATTERN.
    """  # noqa: D209, D400, D415
    preprocessor_instance = {
        None: None,
        "django": django.Preprocessor(),
    }[preprocessor]

    linter = HTMLLinter(fix=fix, check_doctype=check_doctype, preprocessor=preprocessor_instance)
    errors_by_file = {}
    num_errors = 0
    num_files_modified = 0
    num_files_failed = 0

    is_in_modification_block = False  # For printing extra newlines

    html_paths_and_strings: list[tuple[Path | None, str]] = []
    if code:
        html_paths_and_strings = [(None, pattern)]
    else:
        for glob_path in Path().glob(pattern):
            with glob_path.open("r") as html_file:
                html = html_file.read()
                html_paths_and_strings.append((glob_path, html))

    result = None  # For passed-in-code mode
    for path, html in html_paths_and_strings:
        is_preprocessing_error = False  # These are "fatal"

        try:
            result, errors = linter.lint(html)
        except DoctypeError:
            # Ignore this file due to non-HTML5 doctype, when this feature has
            # been enabled
            continue
        except PreprocessingError as preprocessing_error:
            is_preprocessing_error = True
            num_files_failed += 1
            errors = preprocessing_error.errors
        else:
            if fix and html != result and path is not None:
                with path.open("w") as html_file:
                    html_file.write(result)
                    is_in_modification_block = True
                    if not quiet:
                        click.echo(f"Fixed {path}")
                num_files_modified += 1

        if errors:
            errors_by_file[str(path)] = errors
            num_errors += len(errors)

            if is_in_modification_block:
                # Extra newline for spacing
                if not quiet:
                    click.echo()
                is_in_modification_block = False

            if not quiet:
                indentation = ""
                if path is not None:
                    indentation = "  "
                    click.echo(f"\033[1m\033[4m{click.format_filename(path)}\033[0m")

                warning_part = "\x1b[91m\x1b[1mFATAL\x1b[0m  " if is_preprocessing_error else ""

                for error in errors:
                    rule = error.rule

                    len_error_line = len(str(error.line))
                    location_width = 4 + max((len_error_line, 3))
                    location_display = f"{error.line}:{error.column}".ljust(location_width)

                    message = rule.message
                    if error.replacements:
                        message = message.format(**error.replacements)
                    click.echo(
                        f"{indentation}{warning_part}{location_display} "
                        f"{error.rule.code.ljust(4)} {message}",
                    )

                click.echo("")

    # Print closing remarks

    if code:
        if num_errors:
            maybe_s = "" if num_errors == 1 else "s"
            if fix:
                click.echo(f"🔪 \033[91m\033[1m{num_errors} pro̵ble̴m{maybe_s} lef̴̥͆t\033[0m")
            else:
                click.echo(f"🔪 \033[91m\033[1m{num_errors} proble̴m{maybe_s} fo̵͖̔u̷nd\033[0m")

            if return_zero:
                sys.exit(0)
            sys.exit(1)

        if fix:
            if result is not None:
                click.echo(result)
                click.echo()

            if result == pattern:
                click.echo("\033[1mNothing to fix\033[0m 🥰")
            else:
                click.echo("\033[1mAll done\033[0m 🥰")
        else:
            click.echo("\033[1mNo problems found\033[0m 🥰")

        sys.exit(0)

    if errors_by_file:
        maybe_s_1 = "" if num_errors == 1 else "s"
        maybe_s_2 = "" if len(errors_by_file) == 1 else "s"

        if fix:
            if num_files_modified:
                if is_in_modification_block:
                    # Extra newline for spacing
                    click.echo()

                maybe_s_3 = "" if num_files_modified == 1 else "s"
                click.echo(
                    f"\033[1mFixed {num_files_modified} file{maybe_s_3}, "
                    f"\033[91m\033[1m{num_errors} problḙ̴͈͝m{maybe_s_1} le̴ft\033[0m in "
                    f"{len(errors_by_file)} file{maybe_s_2}",
                )
            else:
                click.echo(
                    f"🔪 \033[91m\033[1m{num_errors} pro̵ble̴m{maybe_s_1} lef̴̥͆t\033[0m in "
                    f"{len(errors_by_file)} file{maybe_s_2}",
                )

        else:
            click.echo(
                f"🔪 \033[91m\033[1m{num_errors} proble̴m{maybe_s_1}\033[0m fo̵͖̔u̷nd in "
                f"{len(errors_by_file)} file{maybe_s_2}",
            )

        if return_zero:
            sys.exit(0)
        sys.exit(1)

    if fix:
        if num_files_modified:
            if is_in_modification_block:
                click.echo()

            maybe_s = "" if num_files_modified == 1 else "s"
            click.echo(
                f"\033[1mFixed {num_files_modified} file{maybe_s}, no problems left\033[0m 🥰",
            )
        else:
            click.echo("\033[1mNothing to fix\033[0m 🥰")

    else:
        click.echo("\033[1mNo problems found\033[0m 🥰")

    sys.exit(0)
