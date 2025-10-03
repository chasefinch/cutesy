"""Cutesy - A linter & formatter for consistent HTML code."""

__version__ = "1.0b11"

# Try to import the Rust extension if available
# Falls back gracefully if not compiled yet
try:
    from . import cutesy_core
    _rust_available = True
except ImportError:
    _rust_available = False
    cutesy_core = None

__all__ = ["__version__", "cutesy_core"]
