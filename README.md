# Cutesy 🥰

![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue) [![Build Status](https://travis-ci.com/chasefinch/cutesy.svg?branch=main)](https://travis-ci.com/chasefinch/cutesy)

A cute little HTML linter, until y̵ou ma̴k̵e i̴͌ͅt̴̖̀ a̵̤̤͕̰͐̅͘͘n̶̦̣͙̑̌̆̄ǵ̷̗̗̀͝r̷̭̈́͂͘ẙ̶͔̟̞̊̈…̴̢͘

Cutesy reformats & lints HTML documents, including HTML templates. It includes a set of rules, most of which can be fixed automatically.

Cutesy expects HTML5 files, with UTF-8 encoding.

## Benefits

- Catch accidental errors.
- Enforce best practices.
- Code without worrying about formatting. Cutesy formats automatically.
- Improve code readability.
- Small diffs for easier code review.
- Supports template languages

## Templating languages

Cutesy works with templating languages, such as Django Template Language or Ruby's ERB. These are handled during the "preprocessing" step. Because of this, Cutesy takes dynamic template tags into account for certain types of formatting (such as indentation) & some rules (such as balancing HTML tags).

Preprocessing is supported for these templating languages:

- [x] Django
- [ ] Jinja2
- [ ] ERB
- [ ] Handlebars
- [ ] EJS
- [ ] Mustache
- [ ] Nunjucks
- [ ] Smarty
- [ ] Liquid

## Attribute-based CSS & JavaScript frameworks

Cutesy works with CSS and JavaScript frameworks that rely heavily on HTML attributes, such as TailwindCSS and AlpineJS. It provides hooks for inspecting and rewriting HTML attributes, style blocks, and script blocks, making it possible to enforce consistent formatting directly within your HTML.

### CSS

Cutesy can apply formatters and linters (like Prettier and Stylelint) to inline CSS. It’s also able to sort Tailwind classes into a consistent order, ensuring a clean and predictable style across your markup.

### JavaScript

For in-attribute JavaScript, Cutesy can apply formatters and linters (such as Prettier and ESLint). It can also extract inline scripts, type check them, and run tests, bringing modern development safeguards to code that normally lives inside your HTML.

## Examples

Cutesy ensures that HTML documents contain consistent whitespace, follow best practices, and adhere to common conventions. In `--fix` mode, Cutesy turns this:

        <!doctype html>
    <html>
                        <head>
        <title>Test Page</title>
       </head>
    <body>
                <h1>Hello     world! </h1>


                {% if condition1 %}
                                <p>I love           cookies.</p>
                              {% endif %}



                    <div     class='someDiv'
                           id="theDiv"   ></div    >
                        </body>
    </html>

…into this:

    <!doctype html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello world! </h1>

        {% if condition1 %}
            <p>I love cookies.</p>
        {% endif %}

        <div id="theDiv" class="someDiv"></div>
    </body>
    </html>

See the [full list of rules](docs/rules.md) for more information.

## Installation

Cutesy is written in Python. Install via PyPI:

    uv pip install cutesy

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
