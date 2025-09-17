# Cutesy 🥰

A cute little HTML linter, until y̵ou ma̴k̵e i̴͌ͅt̴̖̀ a̵̤̤͕̰͐̅͘͘n̶̦̣͙̑̌̆̄ǵ̷̗̗̀͝r̷̭̈́͂͘ẙ̶͔̟̞̊̈…̴̢͘

Cutesy reformats & lints HTML documents, including HTML templates. Most code issues that it finds can be fixed automatically.

- Works with Django templates 🐍💕
- Sorts classes for TailwindCSS 💖✨
- Plays nice with code-in-attribute Javascript frameworks like AlpineJS and HTMX ⚡💘

## Templating languages

Templating languages are handled during the "preprocessing" step. Because of this, Cutesy takes dynamic template tags into account for certain types of formatting (such as indentation) & some rules (such as balancing HTML tags).

Cutesy currently supports preprocessing for Django templates.

## Attribute-based CSS & JavaScript frameworks

Works with CSS and JavaScript frameworks that rely heavily on HTML attributes, suxch as TailwindCSS, AlpineJS, and HTMX.

### CSS

Automatically sorts Tailwind classes into a consistent order, and indents multi-line class statements properly.

### JavaScript

For in-attribute JavaScript, Cutesy applies consistent indentation and normalizes whitespace. It also provides hooks for inspecting and rewriting HTML attributes, so future Cutesy plugins can can apply alternative formatters and linters (such as Prettier and ESLint), type-check code, and run tests, bringing modern development safeguards to logic that lives inside your HTML.

## Examples

Cutesy ensures that HTML documents contain consistent whitespace, follow best practices, and adhere to common conventions. In `--fix` mode, Cutesy turns this:

```html
    <!doctype html>
<html>
                    <head>
        <title>Cutesy 🥰 demo</title>
    </head>
<body>
            <h1>Hi     there!</h1>


            {% if cookies_enabled %}
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

    {% if cookies_enabled %}
        <p>Cutesy is so happy when your code is neat.</p>
    {% endif %}

    <div id="lintTrap" class="danger-zone"></div>
</body>
</html>
```

See the [full list of rules](docs/rules.md) for more information.

## Benefits

- Catch accidental errors.
- Enforce best practices.
- Code without worrying about formatting. Cutesy formats automatically.
- Improve code readability.
- Small diffs for easier code review.
- Format & lint Django templates or plain HTML5 documents
- Sort & format TailwindCSS classes

## Installation

Cutesy is written in Python. Install via PyPI:

    pip install cutesy

## Usage

Minimal usage:

    cutesy some_file.html


Lint multiple files using a glob pattern:

    cutesy "*.html"
    cutesy "path/to/templates/**/*.html"
    # etc…


Fix files automatically (recommended):

    cutesy "*.html" --fix


Cutesy can check HTML fragments, or whole HTML documents. By default, Cutesy ignores files specifying a non-HTML5 doctype (anything other than `<!doctype html>`).

To assume (and enforce) that all matching files are HTML5, use the `--check-doctype` flag:

    cutesy "*.html" --fix --check-doctype


To lint files written in a template language, such as the Django Template Language:

    cutesy "*.html" --fix --preprocessor django


Other options:

- `--code`: Process the code passed in as a string.
- `--quiet`: Don't print individual problems.
- `--return-zero`: Always exit with 0, even if unfixed problems remain.
- `--version`: Show the version and exit.
- `--help`: Show the CLI help and exit.


## Badge

Show off how Cutesy keeps you in line.

[![code style: cutesy](https://img.shields.io/badge/markup_style-cutesy_🥰-f34e5d.svg?style=flat)](https://github.com/chasefinch/cutesy)

```md
[![code style: cutesy](https://img.shields.io/badge/markup_style-cutesy_🥰-f34e5d.svg?style=flat)](https://github.com/chasefinch/cutesy)
```


## Testing, etc.

Install development requirements (Requires Python >= 3.13):

    cd /path/to/cutesy/
    make setup
    source bin/activate

Sort imports:

    make format

Lint:

    make configure
    make lint

Test:

    make test
