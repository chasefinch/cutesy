"""Define metadata for Cutesy 🥰."""

# Third Party
import setuptools

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="cutesy",
    version="1.0a2",
    author="Chase Finch",
    author_email="chase@finch.email",
    description="A linter & autoformatter for consistent HTML code, or else.",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["cutesy=cutesy.cli:main"],
    },
)
