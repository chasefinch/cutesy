"""Define metadata for Cutesy 🥰."""

from pathlib import Path

import setuptools

readme_path = Path("README.md")
with readme_path.open() as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="cutesy",
    version="1.0b6",
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
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
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
)
