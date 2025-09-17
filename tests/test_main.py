"""Tests for __main__ module."""

import subprocess
import sys
from pathlib import Path


class TestMain:
    """Test the __main__ module."""

    def test_main_module_executable(self) -> None:
        """Test that the main module can be executed via python -m."""
        # Test that we can run cutesy as a module with --help
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "cutesy", "--help"],
            check=False,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Cutesy" in result.stdout
        assert "--fix" in result.stdout

    def test_main_module_version(self) -> None:
        """Test that the main module can show version."""
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "cutesy", "--version"],
            check=False,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        # Version output should contain some version information
        assert result.stdout.strip() != ""
