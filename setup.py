"""Define metadata for Cutesy 🥰."""

import os
from pathlib import Path

import setuptools

VERSION = "1.0b24"

# Modules to skip for mypyc compilation (use Path for cross-platform compatibility)
MYPYC_SKIP = frozenset(
    str(Path(path))
    for path in (
        "cutesy/__init__.py",  # Imports Rust module which doesn't exist during build
        "cutesy/__main__.py",  # Entry point, doesn't need compilation
        "cutesy/types.py",  # Uses DataEnum metaclass
        "cutesy/rules.py",  # Uses DataEnum metaclass
    )
)

# Build configuration
USE_MYPYC = os.environ.get("CUTESY_USE_MYPYC", "1") == "1"
USE_RUST = os.environ.get("CUTESY_USE_RUST", "1") == "1"

ext_modules = []
rust_extensions = []

# Add mypyc-compiled Python extensions
if USE_MYPYC:
    try:
        from mypyc.build import mypycify
    except ImportError:
        """Mypyc not available, build without compilation."""
    else:
        # Compile all modules in cutesy/ except those in MYPYC_SKIP
        all_modules = [str(path) for path in Path("cutesy").rglob("*.py")]
        compile_modules = [module for module in all_modules if module not in MYPYC_SKIP]

        ext_modules = mypycify(
            ["cutesy"],  # Analyze entire package
            only_compile_paths=compile_modules,  # But only compile these
            opt_level="3",
        )

# Add Rust extensions
if USE_RUST:
    try:
        from setuptools_rust import Binding, RustExtension
    except ImportError:
        """Setuptools-rust not available, build without Rust extensions."""
    else:
        rust_extensions = [
            RustExtension(
                "cutesy.cutesy_core",
                path="rust/Cargo.toml",
                binding=Binding.PyO3,
                debug=False,
            ),
        ]

readme_path = Path("README.md")
with readme_path.open(encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="cutesy",
    version=VERSION,
    author="Chase Finch",
    author_email="chase@finch.email",
    description="A linter & formatter for consistent HTML code, or else.",
    keywords=[
        "Cutesy",
        "HTML",
        "lint",
        "linter",
        "format",
        "formatter",
        "autoformat",
        "autoformatter",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chasefinch/cutesy",
    packages=setuptools.find_packages(),
    ext_modules=ext_modules,
    rust_extensions=rust_extensions,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Rust",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "data-enum>=2.0.1,<3",
        "click>=8.1.8,<9",
    ],
    entry_points={
        "console_scripts": ["cutesy=cutesy.cli:main"],
    },
    zip_safe=False,
)
