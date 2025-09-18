# Configuration Guide

This guide covers all the ways to configure Cutesy for your specific needs, from command-line options to configuration files and project-specific settings.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Command-Line Options](#command-line-options)
- [Configuration Files](#configuration-files)
- [Rule Management](#rule-management)
- [Template Languages](#template-languages)
- [CSS Framework Support](#css-framework-support)
- [Formatting Options](#formatting-options)
- [Project Examples](#project-examples)

## Quick Reference

**Basic usage:**
```bash
cutesy "*.html" --fix
```

**Django templates with TailwindCSS:**
```bash
cutesy "templates/**/*.html" --fix --extras=[django,tailwind]
```

**Custom configuration:**
```bash
cutesy "*.html" --fix --indentation-type=tabs --line-length=120
```

## Command-Line Options

### Basic Operations

#### `PATTERN` (required)
File pattern to match HTML files.

```bash
cutesy "*.html"                    # All HTML files in current directory
cutesy "templates/**/*.html"       # All HTML files in templates/ recursively
cutesy "src/components/*.html"     # Specific directory
```

#### `--code`
Process HTML code directly as a string instead of files.

```bash
cutesy --code '<div>Hello</div>'
```

#### `--fix`
Automatically fix problems when possible. **Highly recommended** for most use cases.

```bash
cutesy "*.html" --fix
```

#### `--quiet`
Suppress individual problem reports, only show summary.

```bash
cutesy "*.html" --quiet
```

#### `--return-zero`
Always exit with code 0, even if problems remain. Useful for CI where you want to report issues but not fail the build.

```bash
cutesy "*.html" --return-zero
```

### Document Processing

#### `--check-doctype`
Process files with non-HTML5 doctypes. By default, Cutesy skips files that don't have `<!doctype html>`.

```bash
cutesy "legacy/*.html" --check-doctype
```

### Extensions

#### `--extras`
Enable support for template languages and CSS frameworks.

**Available extras:**
- `django`: Django Template Language support
- `tailwind`: TailwindCSS class sorting

```bash
# Template language support
cutesy "*.html" --extras=django

# CSS framework support
cutesy "*.html" --extras=tailwind

# Both together
cutesy "*.html" --extras=[django,tailwind]
```

### Formatting Options

#### `--indentation-type`
Choose between spaces or tabs for indentation.

```bash
cutesy "*.html" --indentation-type=spaces  # Default
cutesy "*.html" --indentation-type=tabs
```

#### `--tab-width`
Set tab width for display and line length calculation (default: 4).

```bash
cutesy "*.html" --tab-width=2
cutesy "*.html" --tab-width=8
```

#### `--line-length`
Maximum line length before wrapping tags and attributes (default: 99).

```bash
cutesy "*.html" --line-length=80
cutesy "*.html" --line-length=120
```

#### `--max-items-per-line`
Maximum items (attributes, instructions, etc.) per line before wrapping (default: 5).

```bash
cutesy "*.html" --max-items-per-line=3
cutesy "*.html" --max-items-per-line=10
```

### Attribute Processing

#### `--preserve-attr-whitespace`
Disable the default whitespace normalization and re-indentation of attributes. Use this if you have specific whitespace requirements.

```bash
cutesy "*.html" --preserve-attr-whitespace
```

### Rule Management

#### `--ignore`
Ignore specific rules or entire rule categories.

```bash
# Ignore specific rules
cutesy "*.html" --ignore=F1
cutesy "*.html" --ignore=[F1,D5]

# Ignore entire categories
cutesy "*.html" --ignore=F              # All formatting rules
cutesy "*.html" --ignore=[F,D]          # Formatting and document rules

# Mixed rules and categories
cutesy "*.html" --ignore=[F,D5,E1]
```

**Rule categories:**
- `T`: Temporary preprocessing rules
- `P`: Preprocessing rules (templates)
- `D`: Document structure rules
- `F`: Formatting and style rules
- `E`: Encoding and language rules

See the [Rules Reference](rules.md) for details on individual rules.

## Configuration Files

Cutesy supports multiple configuration file formats to avoid cluttering your command line with options.

### Supported Configuration Files

Cutesy looks for configuration files in this order:
1. `cutesy.toml`
2. `pyproject.toml` (under `[tool.cutesy]`)
3. `setup.cfg` (under `[cutesy]`)

### TOML Configuration

**cutesy.toml:**
```toml
fix = true
check_doctype = true
extras = ["django", "tailwind"]
indentation_type = "spaces"
tab_width = 4
line_length = 99
max_items_per_line = 5
ignore = ["F1", "D5"]
quiet = false
preserve_attr_whitespace = false
```

**pyproject.toml:**
```toml
[tool.cutesy]
fix = true
check_doctype = true
extras = ["django", "tailwind"]
indentation_type = "spaces"
tab_width = 4
line_length = 99
max_items_per_line = 5
ignore = ["F1", "D5"]
quiet = false
preserve_attr_whitespace = false
```

### INI Configuration

**setup.cfg:**
```ini
[cutesy]
fix = true
check_doctype = true
extras = django,tailwind
indentation_type = spaces
tab_width = 4
line_length = 99
max_items_per_line = 5
ignore = F1,D5
quiet = false
preserve_attr_whitespace = false
```

### Configuration Priority

Configuration is loaded in this order (later values override earlier ones):
1. Configuration file
2. Command-line arguments

Example:
```toml
# cutesy.toml
line_length = 120
```

```bash
# Command line overrides config file
cutesy "*.html" --line-length=80  # Uses 80, not 120
```

## Rule Management

### Understanding Rule Categories

**Structural vs. Non-Structural Rules:**
- **Structural rules** must be fixed in `--fix` mode (cannot be ignored)
- **Non-structural rules** are style preferences (can be ignored)

**Fixable vs. Non-Fixable Rules:**
- **Fixable rules** can be automatically corrected
- **Non-fixable rules** require manual intervention

### Ignoring Rules

```bash
# Ignore specific formatting issues
cutesy "*.html" --ignore=F1        # Ignore rule F1

# Ignore all formatting rules
cutesy "*.html" --ignore=F         # Ignore category F

# Ignore multiple specific rules
cutesy "*.html" --ignore=[F1,F8,D5]

# Mixed approach
cutesy "*.html" --ignore=[F,D5,E1] # Ignore all F rules, plus D5 and E1
```

### Common Rule Ignore Patterns

```bash
# For legacy projects with existing style
cutesy "*.html" --ignore=[F1,F2,F3]

# When working with auto-generated HTML
cutesy "*.html" --ignore=D

# For projects with strict whitespace requirements
cutesy "*.html" --ignore=[F6,F7] --preserve-attr-whitespace
```

## Template Languages

### Django Templates

Enable Django template support:

```bash
cutesy "templates/*.html" --extras=django
```

**Configuration file:**
```toml
extras = ["django"]
```

**Features:**
- Understands `{% %}` and `{{ }}` syntax
- Preserves template logic structure
- Handles template inheritance and includes
- Maintains proper indentation around template blocks

**Example:**
```html
<!-- Before -->
{% if user.is_authenticated %}
<div class="welcome">
        <h1>Welcome, {{ user.name }}!</h1>
{% endif %}

<!-- After -->
{% if user.is_authenticated %}
    <div class="welcome">
        <h1>Welcome, {{ user.name }}!</h1>
    </div>
{% endif %}
```

## CSS Framework Support

### TailwindCSS

Enable TailwindCSS class sorting:

```bash
cutesy "*.html" --extras=tailwind
```

**Configuration file:**
```toml
extras = ["tailwind"]
```

**Features:**
- Sorts classes into logical groups
- Maintains responsive prefixes
- Handles pseudo-class modifiers
- Preserves custom classes

**Example:**
```html
<!-- Before -->
<div class="text-red-500 p-4 bg-white hover:bg-gray-100 md:p-8 rounded">

<!-- After -->
<div class="bg-white hover:bg-gray-100 p-4 md:p-8 rounded text-red-500">
```

### Combining Extensions

```bash
cutesy "templates/*.html" --extras=[django,tailwind]
```

This enables Django template processing AND TailwindCSS class sorting.

## Formatting Options

### Indentation

**Spaces (default):**
```bash
cutesy "*.html" --indentation-type=spaces --tab-width=4
```

**Tabs:**
```bash
cutesy "*.html" --indentation-type=tabs --tab-width=4
```

### Line Length and Wrapping

Control how Cutesy wraps long lines:

```bash
# Shorter lines for narrow editors
cutesy "*.html" --line-length=80

# Longer lines for wide screens
cutesy "*.html" --line-length=120

# More attributes per line
cutesy "*.html" --max-items-per-line=8
```

### Attribute Processing

**Default behavior** (recommended):
```bash
cutesy "*.html" --fix
```

**Preserve original attribute whitespace:**
```bash
cutesy "*.html" --fix --preserve-attr-whitespace
```

## Project Examples

### Django Web Application

**Project structure:**
```
myproject/
├── templates/
│   ├── base.html
│   ├── components/
│   └── pages/
├── cutesy.toml
└── manage.py
```

**cutesy.toml:**
```toml
fix = true
extras = ["django", "tailwind"]
indentation_type = "spaces"
tab_width = 4
line_length = 99
ignore = ["F1"]  # Allow some formatting flexibility
```

**Usage:**
```bash
# Format all templates
cutesy "templates/**/*.html"

# Pre-commit hook
cutesy "templates/**/*.html" --quiet
```

### Static Site Generator

**Project structure:**
```
site/
├── src/
│   ├── layouts/
│   ├── partials/
│   └── pages/
├── pyproject.toml
└── build.py
```

**pyproject.toml:**
```toml
[tool.cutesy]
fix = true
extras = ["tailwind"]
indentation_type = "spaces"
line_length = 120
max_items_per_line = 6
```

### Legacy HTML Project

**For projects with existing code style:**

**setup.cfg:**
```ini
[cutesy]
fix = true
ignore = F,D1,D2,D3  # Ignore formatting and some document rules
preserve_attr_whitespace = true
line_length = 80
```

**Usage:**
```bash
# Gradually adopt Cutesy
cutesy "new-pages/*.html"

# Check without fixing
cutesy "legacy/*.html" --no-fix --quiet
```

## Getting Help

- **Rules Reference**: See [rules.md](rules.md) for all available rules
- **Installation Issues**: See [installation.md](installation.md)
- **Bug Reports**: [GitHub Issues](https://github.com/chasefinch/cutesy/issues)

## Next Steps

1. **Start Simple**: Begin with `cutesy "*.html" --fix`
2. **Add Template Support**: Use `--extras` for your template language
3. **Create Config File**: Set up a `cutesy.toml` for your project
4. **Integrate**: Add pre-commit hooks and CI/CD integration
5. **Customize**: Fine-tune rules and formatting options for your team

Happy linting! 🥰
