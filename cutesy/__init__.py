"""Cutesy - A linter & formatter for consistent HTML code."""

from .linter import HTMLLinter

# Try to import Rust extensions if available
# The mypyc-compiled Python code can call these for maximum performance
try:
    from . import cutesy_core  # type: ignore[attr-defined]

    _rust_available = True
except ImportError:
    cutesy_core = None  # type: ignore[assignment]
    _rust_available = False


__all__ = ["HTMLLinter", "_rust_available", "cutesy_core"]
