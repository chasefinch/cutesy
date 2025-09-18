# Installation Guide

This guide covers all the ways to install and set up Cutesy for your HTML linting and formatting needs.

## Quick Start

The fastest way to get started with Cutesy:

```bash
pip install cutesy
cutesy "*.html" --fix
```

## Requirements

- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows
- **Dependencies**: Automatically installed with pip

## Installation Methods

### 1. Install from PyPI (Recommended)

Install the latest stable version from the Python Package Index:

```bash
pip install cutesy
```

### 2. Install from Source

For the latest development version or to contribute:

```bash
git clone https://github.com/chasefinch/cutesy.git
cd cutesy
pip install -e .
```

### 3. Install in a Virtual Environment

Recommended for project-specific installations:

```bash
# Create virtual environment
python -m venv cutesy-env

# Activate (Linux/macOS)
source cutesy-env/bin/activate

# Activate (Windows)
cutesy-env\Scripts\activate

# Install Cutesy
pip install cutesy
```

### 4. Install with pipx

For system-wide CLI tool installation without affecting other Python packages:

```bash
pipx install cutesy
```

## Verify Installation

Test that Cutesy is installed correctly:

```bash
cutesy --version
```

You should see output like:
```
cutesy, version X.X.X
```

Test basic functionality:
```bash
cutesy --help
```

## Extensions

### Django Templates

Django template support is built into Cutesy:

```bash
cutesy "templates/*.html" --fix --extras=django
```

### TailwindCSS

TailwindCSS class sorting is built-in:

```bash
cutesy "*.html" --fix --extras=tailwind
```

### Using Both

Use multiple extras together:

```bash
cutesy "*.html" --fix --extras=[django,tailwind]
```

## Editor Integration

### VS Code

Add Cutesy as a formatter in your VS Code settings:

1. Install the Python extension if not already installed
2. Add to your `settings.json`:

```json
{
    "python.formatting.provider": "none",
    "[html]": {
        "editor.defaultFormatter": "ms-python.python",
        "editor.formatOnSave": true
    }
}
```

3. Create a `.vscode/tasks.json` file:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Format with Cutesy",
            "type": "shell",
            "command": "cutesy",
            "args": ["${file}", "--fix"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "silent",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

### Vim/Neovim

Add to your vim configuration:

```vim
" Format current file with Cutesy
nnoremap <leader>cf :!cutesy % --fix<CR>

" Format all HTML files in current directory
nnoremap <leader>ca :!cutesy "*.html" --fix<CR>
```

### Sublime Text

1. Install the "External Command" package
2. Add a new command:
   - Command: `cutesy`
   - Arguments: `["$file", "--fix"]`

## Pre-commit Hook

Add Cutesy to your pre-commit hooks for automatic formatting:

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Create `.pre-commit-config.yaml`:
```yaml
repos:
-   repo: local
    hooks:
    -   id: cutesy
        name: Format HTML with Cutesy
        entry: cutesy
        language: system
        files: \.(html|htm)$
        args: ['--fix']
```

3. Install the hook:
```bash
pre-commit install
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/lint.yml`:

```yaml
name: Lint HTML

on: [push, pull_request]

jobs:
  lint-html:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Cutesy
      run: pip install cutesy

    - name: Check HTML formatting
      run: cutesy "**/*.html" --extras=[django,tailwind]

    - name: Verify no changes needed
      run: |
        if ! git diff --quiet; then
          echo "HTML files need formatting. Run 'cutesy \"**/*.html\" --fix --extras=[django,tailwind]'"
          exit 1
        fi
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
lint-html:
  image: python:3.11
  script:
    - pip install cutesy
    - cutesy "**/*.html" --extras=[django,tailwind]
    - |
      if ! git diff --quiet; then
        echo "HTML files need formatting"
        exit 1
      fi
  only:
    - merge_requests
    - main
```

## Next Steps

After installation:

1. **Configuration**: Read the [Configuration Guide](configuration.md) to customize Cutesy for your project
2. **Rules**: Review the [Rules Reference](rules.md) to understand what Cutesy checks
3. **Integration**: Set up editor integration and pre-commit hooks for your workflow

Now you're ready to start ~~working for~~ using Cutesy! 🥰
