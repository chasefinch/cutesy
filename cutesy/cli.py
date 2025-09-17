"""Expose Cutesy via CLI.

Cutesy 🥰 — Lint (and optionally fix & format) HTML files.

USAGE
-----
  cutesy [OPTIONS] PATTERN
  cutesy --code [OPTIONS] "<html>…</html>"

CONFIGURATION
-------------
  You can configure Cutesy via (in priority order):
    1) cutesy.toml
    2) [tool.cutesy] in pyproject.toml (or top-level "cutesy")
    3) setup.cfg  (section [cutesy])

  Supported keys (overridable by CLI):
    fix = true|false
    return_zero = true|false
    quiet = true|false
    check_doctype = true|false
    code = true|false
    extra = ["django", "tailwind", ...]  # OPTIONAL
      - NOTE: The internal attribute processors "whitespace" and "reindent" are
        always enabled by default (in that order). Disable both with
        --preserve-attr-whitespace.

CLI HIGHLIGHTS
--------------
    --extra "<list>"
        Provide one or more extras to enable.
        --extra=django
        --extra=django,tailwind
        --extra="[django, tailwind]"
        To override config with an empty list, pass:
        --extra=[]

  --preserve-attr-whitespace
      Disables the built-in 'whitespace' and 'reindent' processors.

Examples
--------
  # Lint all HTML files using defaults + tailwind attribute processor
  cutesy --fix --attribute-processors=tailwind "**/*.html"

  # Run on a string of HTML passed on the command line
  cutesy --code --fix --attribute-processors=[tailwind,alpine] "<div class='...'>…</div>"

  # Disable built-ins that touch attribute whitespace/reindent
  cutesy --preserve-attr-whitespace --attribute-processors=tailwind "**/*.html"

"""  # noqa: D205, D400, D415

import configparser
import contextlib
import json
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
    """Parse config/CLI lists.

    Accepts JSON arrays, comma/space separated strings, or sequences.
    """
    if item is None:
        return None
    if isinstance(item, (list, tuple)):
        return [str(entry).strip() for entry in item if str(entry).strip()]
    if isinstance(item, str):
        string = item.strip()
        if string == "":
            return []
        # Try JSON first (to allow explicit [] override)
        with contextlib.suppress(Exception):
            parsed = json.loads(string)
            if isinstance(parsed, list):
                return [str(entry).strip() for entry in parsed if str(entry).strip()]
        # Fallback: comma/space separated tokens
        parts = [part.strip() for part in string.replace(",", " ").split()]
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


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
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
    "--extra",
    metavar="<list>",
    help=(
        "Extra processors to enable. Accepts a JSON array.Examples: [django], [django, tailwind]."
    ),
)
@click.option(
    "--preserve-attr-whitespace",
    is_flag=True,
    help="Disable the default 'whitespace' and 'reindent' attribute processors.",
)
@click.version_option()
@click.argument("pattern")
@click.pass_context
def main(
    context: click.Context,
    code: bool,  # noqa: FBT001
    fix: bool,  # noqa: FBT001
    return_zero: bool,  # noqa: FBT001
    quiet: bool,  # noqa: FBT001
    check_doctype: bool,  # noqa: FBT001
    extra: str | None,
    preserve_attr_whitespace: bool,  # noqa: FBT001
    pattern: str,
) -> None:
    """Cutesy 🥰.

    Lint (and optionally, fix & format) all files matching PATTERN.
    """
    config = _load_config(Path.cwd())

    # Boolean flags
    for attr_name in ("fix", "return_zero", "quiet", "check_doctype", "code"):
        if not _from_cli(context, attr_name):
            value = _parse_bool(config.get(attr_name))
            if value is not None:
                locals()[attr_name] = value  # type: ignore[misc]  # noqa: WPS421

    # Parse extras (from CLI or config)
    extras = _parse_list(extra)
    if extras is None:
        extras = None if _from_cli(context, "extra") else _parse_list(config.get("extra"))

    preprocessors: dict[str, type[BasePreprocessor]] = {
        "django": django.Preprocessor,
    }
    attr_processor_map: dict[str, type[BaseAttributeProcessor]] = {
        "tailwind": tailwind.AttributeProcessor,
        "reindent": reindent.AttributeProcessor,
        "whitespace": whitespace.AttributeProcessor,
    }

    # Build preprocessor instance (only one supported for now)
    preprocessor_instance = None
    extras = extras or []
    if "django" in extras:
        preprocessor_instance = preprocessors["django"]()

    # Compose attribute processor order
    final_attr_processor_names: list[str] = []
    default_attr_processors = ["whitespace", "reindent"]
    if not preserve_attr_whitespace:
        final_attr_processor_names.extend(default_attr_processors)
    final_attr_processor_names.extend(
        [
            attr_processor_name
            for attr_processor_name in extras
            if attr_processor_name in attr_processor_map
            and attr_processor_name not in default_attr_processors
        ],
    )

    unknown = [
        name for name in extras if name not in preprocessors and name not in attr_processor_map
    ]
    if unknown:
        error_message = f"Unknown extra(s): {', '.join(unknown)}"
        raise click.BadParameter(error_message, param_hint="--extra")

    attr_processor_instances = [attr_processor_map[name]() for name in final_attr_processor_names]

    linter = HTMLLinter(
        fix=fix,
        check_doctype=check_doctype,
        preprocessor=preprocessor_instance,
        attribute_processors=attr_processor_instances,
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
            # Ignore this file due to non-HTML5 doctype, when this feature has been enabled
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
