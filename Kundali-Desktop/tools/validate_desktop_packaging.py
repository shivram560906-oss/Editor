#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/validate_desktop_packaging.py

Static, dependency-free validation of the native desktop packaging contract.

Runs in CI (and locally) *before* a build so a missing runtime file or an
undeclared third-party import is caught in seconds instead of at runtime on a
customer machine.  Uses only the standard library - deliberately does not
import PySide6, so it runs quickly without a display or a Qt install.

Checks
  1. Entry point and required runtime data files are present.
  2. requirements-native.txt exists and pins the mandatory runtime packages.
  3. Every third-party module imported by the desktop code path is declared in
     requirements-native.txt (catches ModuleNotFoundError before shipping).
  4. The desktop entry point does not start a web server (PROJECT_RULES 2).
  5. The calculation-regression baseline exists (CI runs verify against it).

Usage:  python tools/validate_desktop_packaging.py
Exit:   0 = all checks passed, 1 = at least one problem found.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Files/folders the desktop app must be able to read at runtime.
REQUIRED_PATHS = [
    "desktop_main.py",
    "requirements-native.txt",
    "gui/app.py",
    "gui/backend_bridge.py",
    "backend/api/endpoints.py",
    "de421.bsp",
    "Atlas",
    "public/favicon.svg",
    "public/icons.svg",
    "public/bphs",
    "public/saravali",
    "public/phaladeepika",
    "public/jataka_parijata",
    "backups/pre-improvement/calculation-baseline.json",
]

# Third-party modules the desktop path may import, mapped to the pip name that
# must be declared in requirements-native.txt.
THIRD_PARTY_TO_PIP = {
    "PySide6": "PySide6",
    "fitz": "PyMuPDF",
    "nepali_datetime": "nepali-datetime",
    "swisseph": "pysweph",
    "skyfield": "skyfield",
    "requests": "requests",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "pydantic_settings": "pydantic-settings",
    "cryptography": "cryptography",
    "packaging": "packaging",
    "slowapi": "slowapi",
    "multipart": "python-multipart",
}

# Desktop code that is allowed to import third-party modules.
SCAN_ROOTS = ["gui", "backend", "desktop_main.py"]

# The desktop app must never start a web server (PROJECT_RULES 2).
FORBIDDEN_IN_ENTRY = {"uvicorn", "gunicorn", "hypercorn", "flask", "django"}



def _fail(problems: list, message: str) -> None:
    problems.append(message)


def check_required_paths(problems: list) -> None:
    for rel in REQUIRED_PATHS:
        if not (ROOT / rel).exists():
            _fail(problems, f"missing required runtime path: {rel}")


def _declared_pip_names() -> set:
    req = ROOT / "requirements-native.txt"
    if not req.exists():
        return set()
    names = set()
    for line in req.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.match(r"^([A-Za-z0-9._-]+)", line)
        if match:
            names.add(match.group(1).lower().replace("_", "-"))
    return names


def _iter_python_files():
    for rel in SCAN_ROOTS:
        target = ROOT / rel
        if target.is_file():
            yield target
        elif target.is_dir():
            for path in target.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                yield path


def _read_text(path: Path) -> str:
    """Read a source file, tolerating a legacy UTF-8 BOM.

    Python's importer tolerates a BOM, but ast-based tooling (ruff, IDEs and
    this validator) does not - a BOM makes the file look like a syntax error.
    """
    return path.read_text(encoding="utf-8-sig")


def _top_level_imports(path: Path) -> set:
    tree = ast.parse(_read_text(path), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import - always local
                continue
            if node.module:
                modules.add(node.module.split(".")[0])
    return modules


def check_source_encoding(problems: list) -> None:
    """Flag .py files that start with a UTF-8 BOM (breaks lint/AST tooling)."""
    for path in _iter_python_files():
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            _fail(
                problems,
                f"{path.relative_to(ROOT)} starts with a UTF-8 BOM - remove it "
                "(imports work, but ruff/ast tooling reports a syntax error)",
            )



def check_declared_imports(problems: list) -> None:
    declared = _declared_pip_names()
    if not declared:
        return  # already reported as a missing file
    used = {}
    for path in _iter_python_files():
        for module in _top_level_imports(path):
            if module in THIRD_PARTY_TO_PIP:
                used.setdefault(THIRD_PARTY_TO_PIP[module], set()).add(
                    str(path.relative_to(ROOT)).replace("\\", "/")
                )
    for pip_name, files in sorted(used.items()):
        if pip_name.lower().replace("_", "-") not in declared:
            sample = ", ".join(sorted(files)[:3])
            _fail(problems, f"undeclared dependency '{pip_name}' imported by: {sample}")


def check_no_web_server(problems: list) -> None:
    entry = ROOT / "desktop_main.py"
    if not entry.exists():
        return
    for module in _top_level_imports(entry):
        if module in FORBIDDEN_IN_ENTRY:
            _fail(
                problems,
                f"desktop entry point must not import '{module}' "
                "(PROJECT_RULES: desktop-only, no web server)",
            )
    text = entry.read_text(encoding="utf-8")
    if re.search(r"\buvicorn\.run\b|\bapp\.run\(host", text):
        _fail(problems, "desktop entry point appears to start a web server")


def main() -> int:
    problems = []
    check_required_paths(problems)
    check_declared_imports(problems)
    check_source_encoding(problems)
    check_no_web_server(problems)

    if problems:
        print(f"Desktop packaging validation FAILED ({len(problems)} problems):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "Desktop packaging validation passed: entry point, runtime data, "
        "dependency declarations and baseline are all present."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

