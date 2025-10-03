default: configure format lint check test

configure:
	@echo "Checking configuration against global spec..."
	@nitpick check
	@printf "\e[1mConfiguration is in sync!\e[0m\n\n"

format:
	@echo "Formatting Python docstrings..."
	@docformatter . -r --in-place --exclude bin lib .git || true
	@echo "...done."
	@echo "Formatting Python files..."
	@echo "  1. Ruff Format"
	@ruff format . > /dev/null
	@echo "  2. Ruff Check (fix only)"
	@ruff check --fix-only . --quiet
	@echo "  3. Add trailing commas"
	@# Add trailing commas to dangling lines and function calls
	@find . \( -path ./lib -o -path ./bin \) -prune -o -name '*.py' -print0 | xargs -P 16 -0 -I{} sh -c 'add-trailing-comma "{}" || true'
	@echo "  4. Ruff Format (again)"
	@# Format again after adding trailing commas
	@ruff format . --quiet
	@echo "  5. Ruff Check (fix only, again)"
	@ruff check --fix-only . --quiet
	@echo "...done."

lint:
	@echo "Checking for Python formatting issues which can be fixed automatically..."
	@echo "  1. Ruff Format"
	@ruff format . --diff > /dev/null 2>&1 || (printf 'Found files which need to be auto-formatted. Make sure your dependencies are up to date and then run \e[1mmake format-py\e[0m and re-lint.\n'; exit 1)
	@echo "  2. Ruff Check (fix only)"
	@ruff check . --diff --silent || (printf 'Found files which need to be auto-formatted. Make sure your dependencies are up to date and then run \e[1mmake format-py\e[0m and re-lint.\n'; exit 1)
	@echo "...done. No issues found."
	@echo "Running Python linter..."
	@echo "  1. Ruff Check"
	@ruff check . --quiet
	@echo "  2. Flake8"
	@flake8 .
	@echo "...done. No issues found."

check:
	@echo "Running Python type checks..."
	@mypy .
	@echo "...done. No issues found."

test: test-unit test-integration test-private
	@echo "Combining coverage reports..."
	coverage combine
	coverage report -m --fail-under 91
	@echo "All tests completed successfully!"

test-unit:
	@echo "Running unit tests..."
	find . -name "*.pyc" -delete
	coverage erase
	coverage run --source=cutesy --data-file=.coverage.unit -m pytest tests/unit --ignore=bin --ignore=lib --ignore=dist --ignore=prof --ignore=build -vv

test-integration:
	@echo "Running integration tests..."
	find . -name "*.pyc" -delete
	coverage run --source=cutesy --data-file=.coverage.integration -m pytest tests/integration --ignore=bin --ignore=lib --ignore=dist --ignore=prof --ignore=build -vv

test-private:
	@echo "Running private tests..."
	find . -name "*.pyc" -delete
	coverage run --source=cutesy --data-file=.coverage.private -m pytest tests/private --ignore=bin --ignore=lib --ignore=dist --ignore=prof --ignore=build -vv

setup:
	python3 -m venv .
	chmod +x ./bin/activate
	uv pip install -r requirements/develop.txt

teardown:
	-rm -r lib/*
	-rm -r bin/*
	-rm pyvenv.cfg

# Build with mypyc + Rust compilation
build:
	@echo "Building with mypyc + Rust compilation..."
	@echo "  1. Cleaning previous build..."
	@$(MAKE) clean-build
	@echo "  2. Uninstalling previous version..."
	@pip uninstall -y cutesy 2>/dev/null || true
	@echo "  3. Building and installing with compilation..."
	@pip install --no-deps .
	@echo "...done. Extensions compiled."
	@$(MAKE) test-compiled

# Build release wheels
build-release:
	@echo "Building release wheels..."
	@$(MAKE) clean-build
	@python setup.py bdist_wheel
	@echo "...done. Wheel created in dist/"

test-compiled:
	@echo "Testing mypyc compilation..."
	@python -c "import sys; import cutesy.linter; compiled = [m for m in sys.modules if 'cutesy' in m and hasattr(sys.modules.get(m), '__file__') and (sys.modules.get(m).__file__ or '').endswith('.so')]; print('✓ mypyc compiled modules:', compiled) if compiled else print('⚠ No compiled modules found (running pure Python)')"

clean-build:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info
	@find cutesy -name "*.so" -delete
	@find cutesy -name "*.c" -delete
	@echo "...done."

.PHONY: default configure format lint test test-unit test-integration test-private setup build build-release test-compiled clean-build
