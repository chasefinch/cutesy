"""Tests for __main__ module."""

import os
import subprocess
import sys
from pathlib import Path


class TestMain:
    """Test the __main__ module."""

    def test_main_module_executable(self) -> None:
        """Test that the main module can be executed via python -m."""
        # Set up environment to include current directory in PYTHONPATH
        env = os.environ.copy()
        project_root = Path(
            __file__,
        ).parent.parent.parent  # Go up 3 levels: test_main.py -> unit -> tests -> project root
        env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Test that we can run cutesy as a module with --help
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "cutesy", "--help"],
            check=False,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

        assert result.returncode == 0
        assert "Cutesy" in result.stdout
        assert "--fix" in result.stdout

    def test_main_module_direct_execution_path_exists(self) -> None:
        """Test that __main__.py contains the direct execution path."""
        # Read the __main__.py file and verify it has the expected structure
        main_file = Path(__file__).parent.parent.parent / "cutesy" / "__main__.py"
        file_content = main_file.read_text()

        # Verify the file contains the expected direct execution pattern
        assert 'if __name__ == "__main__":' in file_content
        assert "sys.exit(main())" in file_content
        assert "from .cli import main" in file_content
