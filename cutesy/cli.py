"""Expose Cutesy via CLI."""

import configparser
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

import click
from click.core import ParameterSource

from . import HTMLLinter
from .attribute_processors import BaseAttributeProcessor, reindent, whitespace
from .attribute_processors.class_ordering import tailwind
from .preprocessors import BasePreprocessor, django
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
@click.option(
    "--attribute-processor",
    metavar="<str>",
    multiple=True,
    help="Use an attribute processor for dynamic HTML files. Try 'tailwind'.",
)
@click.version_option()
@click.argument("pattern")
@click.pass_context
def main(
    context: click.Context,
    code: bool,  # noqa: FBT001 (argument pattern)
    fix: bool,  # noqa: FBT001
    return_zero: bool,  # noqa: FBT001
    quiet: bool,  # noqa: FBT001
    check_doctype: bool,  # noqa: FBT001
    preprocessor: str | None,
    attribute_processor: list[str],
    pattern: str,
) -> None:
    """Cutesy 🥰

    Lint (and optionally, fix & format) all files matching PATTERN.
    """  # noqa: D209, D400, D415
    config = _load_config(Path.cwd())

    if not _from_cli(context, "fix"):
        value = _parse_bool(config.get("fix"))
        if value is not None:
            fix = value

    if not _from_cli(context, "return_zero"):
        value = _parse_bool(config.get("return_zero"))
        if value is not None:
            return_zero = value

    if not _from_cli(context, "quiet"):
        value = _parse_bool(config.get("quiet"))
        if value is not None:
            quiet = value

    if not _from_cli(context, "check_doctype"):
        value = _parse_bool(config.get("check_doctype"))
        if value is not None:
            check_doctype = value

    if not _from_cli(context, "code"):
        value = _parse_bool(config.get("code"))
        if value is not None:
            code = value

    if not _from_cli(context, "preprocessor"):
        value = config.get("preprocessor")
        if isinstance(value, str):
            preprocessor = value

    if not _from_cli(context, "attribute_processor"):
        value_list = _parse_list(config.get("attribute_processor"))
        if value_list is not None:
            attribute_processor = value_list

    preprocessors: dict[str, type[BasePreprocessor]] = {
        "django": django.Preprocessor,
    }
    preprocessor_instance = preprocessors[preprocessor]() if preprocessor else None

    attribute_processors: dict[str, type[BaseAttributeProcessor]] = {
        "tailwind": tailwind.AttributeProcessor,
        "reindent": reindent.AttributeProcessor,
        "whitespace": whitespace.AttributeProcessor,
    }

    attribute_processor_instances = [attribute_processors[name]() for name in attribute_processor]

    linter = HTMLLinter(
        fix=fix,
        check_doctype=check_doctype,
        preprocessor=preprocessor_instance,
        attribute_processors=attribute_processor_instances,
    )
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


def _from_cli(context: click.Context, name: str) -> bool:
    try:
        return context.get_parameter_source(name) == ParameterSource.COMMANDLINE
    except Exception:
        return True  # be conservative


def _find_in_parents(start: Path, names: list[str]) -> Path | None:
    current = start.resolve()
    while True:
        for name in names:
            part = current / name
            if part.is_file():
                return part
        if current.parent == current:
            return None
        current = current.parent


def _parse_bool(item: object) -> bool | None:
    if isinstance(item, bool):
        return item
    if isinstance(item, str):
        value = item.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False
    return None


def _parse_list(item: object) -> list[str] | None:
    if item is None:
        return None
    if isinstance(item, (list, tuple)):
        return [str(entry) for entry in item]
    if isinstance(item, str):
        parts = [part.strip() for part in item.replace(",", " ").split()]
        return [part for part in parts if part]
    return None


def _load_config(start_dir: Path) -> dict:
    """Load config from cutesy.toml, pyproject.toml, or setup.cfg."""
    # 1) cutesy.toml
    path = _find_in_parents(start_dir, ["cutesy.toml"])
    if path:
        with path.open("rb") as toml_file:
            return tomllib.load(toml_file)

    # 2) pyproject.toml
    path = _find_in_parents(start_dir, ["pyproject.toml"])
    if path:
        with path.open("rb") as toml_file:
            toml_data = tomllib.load(toml_file) or {}
        if "cutesy" in toml_data and isinstance(toml_data["cutesy"], dict):
            return toml_data["cutesy"]
        if (
            "tool" in toml_data
            and isinstance(toml_data["tool"], dict)
            and isinstance(toml_data["tool"].get("cutesy"), dict)
        ):
            return toml_data["tool"]["cutesy"]

    # 3) setup.cfg
    path = _find_in_parents(start_dir, ["setup.cfg"])
    if path:
        config = configparser.ConfigParser()
        config.read(path)
        if config.has_section("cutesy"):
            return {key: value for key, value in config.items("cutesy")}

    return {}
