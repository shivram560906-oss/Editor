# Native Desktop Packaging

The desktop product is the standalone PySide6 application started by
[`desktop_main.py`](../desktop_main.py). It imports the calculation backend
directly through [`gui/backend_bridge.py`](../gui/backend_bridge.py). It does not
start FastAPI, bind a localhost port, load React, use a browser, or require a
separately started server.

Use 64-bit Python 3.11 on Windows and run the commands below from the
`Kundali-Desktop` directory (the folder that contains `desktop_main.py`).

## Development Run

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-native.txt
.venv\Scripts\python desktop_main.py
```

`requirements-native.txt` is the only dependency manifest for the native app.
It covers PySide6, Matplotlib/NumPy chart support, Swiss Ephemeris, Alembic and
the backend calculation packages. No Node.js or frontend build is needed.

## Validate The Packaging Contract

Run the static, dependency-free check:

```bat
.venv\Scripts\python tools\validate_desktop_packaging.py
```

The validator does **not** launch Qt or run PyInstaller. It checks that:

- the native entry point and required runtime data files exist
  (`de421.bsp`, Atlas data, Avakahada data, icon);
- `requirements-native.txt` declares every third-party import used by the
  desktop code path;
- the entry point does not start a web server;
- the calculation-regression baseline exists.

## Tests

The native GUI tests use `unittest` and run headlessly with Qt's offscreen
platform:

```bat
set QT_QPA_PLATFORM=offscreen
.venv\Scripts\python -m unittest discover -s gui\tests -p "test_*_native.py" -v
```

Some Qt printing tests are skipped on the Windows offscreen platform because
`QPrinter` can trigger a native exception there; run those tests on a normal
desktop session.

## Build

No PyInstaller spec file is committed in this folder yet. A release build must:

1. pass `tools\validate_desktop_packaging.py`;
2. bundle `desktop_main.py`, the complete `gui` and `backend` packages, Alembic
   configuration/versions, `de421.bsp`, `Atlas\`, `formatted_extracted.txt`,
   `qt.conf` and `public\favicon.svg`;
3. collect PySide6 Qt plugins and Matplotlib data through PyInstaller's hooks;
4. produce a one-file or one-folder Windows executable and smoke-test it on a
   clean machine (startup, chart calculation, printing/PDF, saved-chart
   persistence).

Add the spec and build script to this folder when they are ready; keep this
document in sync with their actual file names.

## Writable Data

Saved charts and settings live in a per-user SQLite database:

```text
%LOCALAPPDATA%\ShivramJyotish\jyotish.db
```

If `%LOCALAPPDATA%` is unavailable, the app uses `ShivramJyotish` under the
current user's home directory. The installation directory is treated as
read-only. A `jyotish.db` inside the source checkout is **not** used by the
native desktop app.

Alembic migrations run at startup and bring an older desktop database up to
date. Before a pending migration changes the schema, a consistent backup is
written to:

```text
%LOCALAPPDATA%\ShivramJyotish\backups\
```

The newest five automatic backups are kept; a manual backup is never removed
automatically. The Settings page also has a **Back Up Now** action that writes a
manual backup on demand.
