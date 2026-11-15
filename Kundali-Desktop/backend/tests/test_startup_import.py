"""Startup contract tests for the API Docker image.

The Render image installs ``requirements.txt`` only, which intentionally
excludes PySide6. Importing the FastAPI app must therefore never import a
module that needs Qt at module load time.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_app_imports_without_pyside6() -> None:
    script = textwrap.dedent(
        """
        import sys

        class BlockPySide6:
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "PySide6" or fullname.startswith("PySide6."):
                    raise ModuleNotFoundError("No module named 'PySide6'", name=fullname)
                return None

        sys.meta_path.insert(0, BlockPySide6())

        import main

        assert main.app is not None
        print("startup ok")
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, result.stderr
    assert "startup ok" in result.stdout
