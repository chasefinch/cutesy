# Cutesy 🥰

A cute little HTML linter, until y̵ou ma̴k̵e i̴͌ͅt̴̖̀ a̵̤̤͕̰͐̅͘͘n̶̦̣͙̑̌̆̄ǵ̷̗̗̀͝r̷̭̈́͂͘ẙ̶͔̟̞̊̈…̴̢͘

**Cutesy reformats & lints HTML documents**, including HTML templates. It ensures consistent indentation, line breaks, and formatting while automatically fixing most issues.

## First-class support for your favorite frameworks

- Full support for Django templates 🐍💕
- Sorts classes for TailwindCSS 💖✨
- Works with AlpineJS and HTMX ⚡💘

## ✨ Features

- **🔧 Auto-Fix**: Automatically corrects most formatting issues
- **📏 Configurable**: Extensive configuration options for your project's needs
- **🏃‍♂️ Fast**: Processes large codebases quickly

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Basic Usage](#-basic-usage)
- [Configuration](#-configuration)
- [Template Languages](#-template-languages)  
- [CSS Framework Support](#-css-framework-support)
- [Examples](#-examples)
- [Documentation](#-documentation)
- [Development](#-development)

## 🚀 Quick Start

**Install:**
```bash
pip install cutesy
```

**Format your HTML files:**
```bash
cutesy "*.html" --fix
```

**For Django projects with TailwindCSS:**
```bash
cutesy "templates/**/*.html" --fix --extras=[django,tailwind]
```

## 💾 Installation

Cutesy requires **Python 3.11+** and works on Linux, macOS, and Windows.

**Basic Installation:**
```bash
pip install cutesy
```

**For system-wide CLI tool:**
```bash
pipx install cutesy
```

**Development Installation:**
```bash
git clone https://github.com/chasefinch/cutesy.git
cd cutesy
pip install -e .
```

> 📚 **Detailed guide**: See [Installation Documentation](docs/installation.md) for editor integration, pre-commit hooks, and CI/CD setup.

## 🎯 Basic Usage

### Command Line

**Check files for issues:**
```bash
cutesy "*.html"                    # Check all HTML files
cutesy "templates/**/*.html"       # Check recursively
cutesy --code '<div>test</div>'    # Check code string
```

**Fix issues automatically:**
```bash
cutesy "*.html" --fix              # Fix all issues
cutesy "*.html" --fix --quiet      # Fix quietly
cutesy "*.html" --return-zero      # Don't fail CI on issues
```

### Key Options

| Option | Description | Example |
|--------|-------------|---------|
| `--fix` | Auto-fix issues (recommended) | `cutesy "*.html" --fix` |
| `--extras` | Enable template/framework support | `--extras=[django,tailwind]` |
| `--ignore` | Ignore specific rules | `--ignore=[F1,D5]` |
| `--quiet` | Suppress detailed output | `--quiet` |
| `--check-doctype` | Process non-HTML5 files | `--check-doctype` |

## ⚙️ Configuration

### Configuration Files

Create a `cutesy.toml` file in your project:

```toml
fix = true
extras = ["django", "tailwind"]
indentation_type = "spaces"
line_length = 99
ignore = ["F1"]  # Ignore specific rules
```

**Also supports:**
- `pyproject.toml` (under `[tool.cutesy]`)
- `setup.cfg` (under `[cutesy]`)

### Common Configurations

**Django + TailwindCSS:**
```toml
fix = true
extras = ["django", "tailwind"]
line_length = 120
max_items_per_line = 6
```

> 📚 **Complete guide**: See [Configuration Documentation](docs/configuration.md) for all options and examples.

## 🎭 Template Languages

### Django Templates

Enable Django template processing:

```bash
cutesy "templates/*.html" --fix --extras=django
```

**Supports:**
- `{% %}` template tags with proper indentation
- `{{ }}` variables
- Template inheritance (`{% extends %}`, `{% block %}`)
- Complex template logic with nested HTML

**Example transformation:**
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

## 🎨 CSS Framework Support

### TailwindCSS

Automatic class sorting and organization:

```bash
cutesy "*.html" --fix --extras=tailwind
```

**Features:**
- **Smart sorting**: Groups utility classes logically
- **Responsive prefixes**: Maintains `sm:`, `md:`, `lg:` order
- **Pseudo-classes**: Preserves `hover:`, `focus:`, etc.
- **Custom classes**: Keeps your custom classes at the end

**Example:**
```html
<!-- Before -->
<div class="text-red-500 p-4 bg-white hover:bg-gray-100 md:p-8 rounded-lg">

<!-- After -->
<div class="bg-white hover:bg-gray-100 p-4 md:p-8 rounded-lg text-red-500">
```

### AlpineJS & HTMX

Cutesy works great with attribute-heavy frameworks:

- **Proper indentation** for multi-line attributes
- **Whitespace normalization** inside attributes
- **Consistent formatting** across your components

## 📖 Examples

Cutesy ensures that HTML documents contain consistent whitespace, follow best practices, and adhere to common conventions. In `--fix` mode, Cutesy turns this:

```html
    <!doctype html>
<html>
                    <head>
        <title>Cutesy 🥰 demo</title>
    </head>
<body>
            <h1>Hi     there!</h1>


            {% if request.user.is_authenticated %}
                    <p>Cutesy is so happy      when your code is neat.</p>
                            {% endif %}



                <div     class='danger-zone'
                        id="lintTrap"   ></div    >
                    </body>
</html>
```

…into this:

```html
<!doctype html>
<html>
<head>
    <title>Cutesy 🥰 demo</title>
</head>
<body>
    <h1>Hi there!</h1>

    {% if request.user.is_authenticated %}
        <p>Cutesy is so happy when your code is neat.</p>
    {% endif %}

    <div id="lintTrap" class="danger-zone"></div>
</body>
</html>
```

### Real-World Usage

**Django Project:**
```bash
# Format all templates
cutesy "templates/**/*.html" --fix --extras=[django,tailwind]

# Check before committing
cutesy "templates/**/*.html" --quiet
```

**Static Site:**
```bash
# Format with custom config
cutesy "src/**/*.html" --fix --line-length=120

# Format specific files
cutesy "src/components/*.html" --fix --extras=tailwind
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Installation Guide](docs/installation.md)** | Complete installation instructions, editor integration, CI/CD setup |
| **[Configuration Guide](docs/configuration.md)** | All configuration options, file formats, project examples |
| **[Rules Reference](docs/rules.md)** | Complete list of all rules with examples and fixes |
| **[Development Guide](docs/development.md)** | Contributing, testing, and development setup |

## 🎯 Benefits

✅ **Validate AI code output** - Catch inconsistencies in generated HTML
✅ **Enforce team standards** - Consistent formatting across all developers
✅ **Catch errors early** - Find malformed HTML and template syntax issues
✅ **Save time** - No more manual formatting or style discussions
✅ **Better code reviews** - Focus on logic, not formatting
✅ **Framework integration** - Works with your existing tools and workflows

## 🏷️ Badge

Show off how Cutesy keeps you in line.

[![code style: cutesy](https://img.shields.io/badge/code_style-cutesy_🥰-f34e5d.svg?style=flat)](https://github.com/chasefinch/cutesy)

```markdown
[![code style: cutesy](https://img.shields.io/badge/code_style-cutesy_🥰-f34e5d.svg?style=flat)](https://github.com/chasefinch/cutesy)
```

## 🛠️ Development

**Setup development environment:**
```bash
git clone https://github.com/chasefinch/cutesy.git
cd cutesy
make setup
source bin/activate
```

**Run tests:**
```bash
make test        # Run all tests
make test-unit   # Unit tests only
make lint        # Check code style
make format      # Format code
```

**Project requirements:**
- **Python 3.11+** for development
- Uses modern Python features and type hints
- Comprehensive test suite with 91%+ coverage

> 📚 **Contributing**: See [Development Guide](docs/development.md) for detailed contribution guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Whether it's:

- 🐛 **Bug reports** via [GitHub Issues](https://github.com/chasefinch/cutesy/issues)
- 💡 **Feature requests** via [GitHub Discussions](https://github.com/chasefinch/cutesy/discussions)
- 🔧 **Code contributions** via Pull Requests
- 📖 **Documentation improvements**

See our [Development Guide](docs/development.md) for getting started.

---

**Keep your HTML cute and tidy with Cutesy! 🥰**

Or els̴͔e.
