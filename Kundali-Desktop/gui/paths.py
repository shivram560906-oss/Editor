# -*- coding: utf-8 -*-
"""
gui/paths.py — single source of truth for desktop paths and the database URL.

Why this module exists
----------------------
Modules used to resolve the database location independently::

    gui/backend_bridge.py        %LOCALAPPDATA%\\ShivramJyotish\\jyotish.db
    gui/utils/chart_storage.py   %LOCALAPPDATA%\\ShivramJyotish\\jyotish.db
    backend/config.py            <repo_root>/jyotish.db   (fallback)

Each one used ``os.environ.setdefault("DATABASE_URL", ...)``, so the *first*
module imported won and the others silently followed.  In practice the two
databases both accumulated data (saved kundalis), which is why charts appeared
to "disappear" depending on how the app was started.

``configure()`` must run **before** ``backend.config`` is imported, because
``backend/config.py`` evaluates ``settings = get_settings()`` at import time and
freezes the database URL from the environment.

Nothing in this module touches the calculation engine, so results are unchanged.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional

import logging
import datetime
import sqlite3

from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy import inspect as sa_inspect

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

APP_DIR_NAME = "ShivramJyotish"
DB_FILENAME = "jyotish.db"


def appdata_dir(create: bool = True) -> Path:
    """Return the per-user application data directory."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    path = Path(base) / APP_DIR_NAME
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def database_path(create: bool = True) -> Path:
    """Return the canonical SQLite file for saved charts and settings."""
    return appdata_dir(create=create) / DB_FILENAME


def database_url() -> str:
    """SQLAlchemy URL for the canonical database (honours DATABASE_URL)."""
    override = (os.environ.get("DATABASE_URL") or "").strip()
    if override:
        return override
    return "sqlite:///" + database_path().resolve().as_posix()


#: Pre-migration / manual backups live next to the database, never in the repo.
BACKUP_DIR_NAME = "backups"
MAX_AUTOMATIC_BACKUPS = 5


def backups_dir(create: bool = True) -> Path:
    """Return the directory that holds database backups."""
    path = appdata_dir(create=create) / BACKUP_DIR_NAME
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def _runtime_database_url() -> str:
    """The URL Alembic will actually migrate (honours runtime overrides)."""
    try:
        from config import settings

        configured = (settings.DATABASE_URL or "").strip()
        if configured:
            return configured
    except Exception:
        pass
    return database_url()


def _sqlite_database_file(url: Optional[str] = None) -> Optional[Path]:
    """Resolve a local SQLite file from a database URL, or ``None`` otherwise."""
    from sqlalchemy.engine import make_url

    try:
        parsed = make_url(url or _runtime_database_url())
    except Exception:
        return None
    if parsed.get_backend_name() != "sqlite" or not parsed.database:
        return None
    if parsed.database == ":memory:":
        return None
    return Path(parsed.database)


def backup_database(destination: Optional[Path] = None, manual: bool = False) -> Path:
    """Create a consistent backup of the desktop SQLite database.

    Uses SQLite's online backup API rather than a file copy so a WAL journal or
    an in-flight write cannot produce a torn snapshot.  Returns the backup path.

    Automatic backups (``manual=False``) are pruned to the newest
    :data:`MAX_AUTOMATIC_BACKUPS`; a user-requested manual backup is never pruned
    by that policy.
    """
    source_path = _sqlite_database_file()
    if source_path is None:
        raise RuntimeError("Only a local SQLite database can be backed up.")
    if not source_path.exists():
        raise FileNotFoundError(f"Database not found: {source_path}")

    if destination is None:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        prefix = "manual-jyotish" if manual else "jyotish"
        target = source_path.parent / BACKUP_DIR_NAME / f"{prefix}-{stamp}.db"
    else:
        target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)

    source = sqlite3.connect(str(source_path))
    try:
        backup = sqlite3.connect(str(target))
        try:
            source.backup(backup)
        finally:
            backup.close()
    finally:
        source.close()
    return target


def _prune_automatic_backups(directory: Path, keep: int = MAX_AUTOMATIC_BACKUPS) -> None:
    """Delete the oldest automatic backups, keeping the newest *keep* files."""
    try:
        files = sorted(
            directory.glob("jyotish-*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return
    for stale in files[keep:]:
        try:
            stale.unlink()
        except OSError:
            logger.debug("Could not remove old backup %s", stale)


def _migration_is_pending(config) -> bool:
    """True when the database revision differs from the Alembic head."""
    try:
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory

        head = ScriptDirectory.from_config(config).get_current_head()
        engine = sa_create_engine(_runtime_database_url())
        try:
            with engine.connect() as connection:
                current = MigrationContext.configure(connection).get_current_revision()
        finally:
            engine.dispose()
        return current != head
    except Exception:
        # Unknown state: prefer taking a backup over risking data loss.
        return True


def _backup_before_migration(config) -> None:
    """Best-effort automatic backup before the schema is altered."""
    if not _migration_is_pending(config):
        return
    try:
        target = backup_database()
        _prune_automatic_backups(target.parent)
        logger.info("Database backed up before migration: %s", target)
    except Exception as exc:
        # A backup problem must not prevent the (already validated) migration,
        # but it is important enough to surface in the log.
        logger.warning("Pre-migration database backup failed: %s", exc)


def ensure_backend_on_sys_path() -> None:
    """Make ``backend/`` importable so ``calculator``/``database`` resolve."""
    path = str(BACKEND_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)


def configure() -> Dict[str, str]:
    """Idempotently publish DATABASE_URL into the environment.

    Returns the resolved values for logging/diagnostics.  Safe to call from
    every entry point: an existing environment value always wins.
    """
    ensure_backend_on_sys_path()
    url = database_url()
    os.environ.setdefault("DATABASE_URL", url)
    return {
        "appdata_dir": str(appdata_dir()),
        "database_path": os.environ["DATABASE_URL"],
    }


def _current_revision(conn) -> Optional[str]:
    """Read alembic_version, or None when the table is absent."""
    try:
        result = conn.exec_driver_sql("SELECT version_num FROM alembic_version").fetchone()
    except Exception:      # table does not exist yet
        return None
    return result[0] if result else None


def _stamp_to_head(config, connection) -> bool:
    """Mark an un-stamped-but-current database as up to date.

    The desktop app historically created its schema with
    ``Base.metadata.create_all()``, so existing installations have **no**
    ``alembic_version`` row.  Replaying the whole migration chain against such a
    database would try to recreate tables that already exist and abort.

    When there is no alembic history, check whether the live schema already
    matches the models:
    * yes  -> stamp ``head`` and do nothing else;
    * no   -> stamp the newest *already-applied-looking* migration is unsafe, so
              run the chain from base only when the schema is genuinely empty.
              For a partially-updated legacy database, apply the forward
              migrations that add the missing columns directly.
    """
    if _current_revision(connection) is not None:
        return False  # a real alembic history exists - migrate normally

    from database import models as models_module

    inspector = sa_inspect(connection)
    if "users" not in inspector.get_table_names():
        return False  # no schema at all - run the migrations from base

    missing = []
    for table in models_module.Base.metadata.sorted_tables:
        if table.name not in inspector.get_table_names():
            continue
        live = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name not in live:
                missing.append(f"{table.name}.{column.name}")

    if not missing:
        return True  # schema already current -> stamp head

    # Some columns are missing.  Apply only the forward "add column" migrations
    # rather than replaying the destructive create/recreate chain.
    logger.info("Desktop schema missing %s - applying forward migrations", missing)
    _apply_forward_column_migrations(config)
    return True


def _apply_forward_column_migrations(config) -> None:
    """Run only the migrations whose columns are actually missing.

    Migration 0004 adds columns with native ``ALTER TABLE ... ADD COLUMN``.
    Older desktop databases are unstamped, so ``upgrade head`` would replay
    0001-0003 (which create/recreate tables) and fail.  Instead we stamp the
    parent of 0004 and run it - the only migration that adds columns.
    """
    from alembic import command

    # The forward migrations that add columns to the legacy desktop schema.
    # Everything here uses a native ALTER TABLE ... ADD COLUMN (safe), whereas
    # the older 0001-0003 migrations create/recreate tables and must not be
    # replayed against a database that already has them.
    # Stamp the baseline of the legacy create_all() database, then let
    # `upgrade head` replay the remaining migrations.  Every step after the
    # baseline is written to be safe on a database that already has the tables
    # (create_table is guarded, add_column checks for an existing column).
    _STAMP_BASELINE = "0001_initial"
    command.stamp(config, _STAMP_BASELINE)
    command.upgrade(config, "head")


def run_migrations() -> Optional[str]:
    """Bring the desktop database schema up to date with Alembic.

    The desktop app used to rely on ``Base.metadata.create_all()``, which only
    creates *missing* tables and never alters an existing one - so a model change
    (a new column, for example) left older installations with a stale schema and
    runtime ``no such column`` errors.  Migrations are the supported path.

    Returns None on success, or a short error string on failure.  Never raises:
    a migration problem must not stop the app from starting.
    """
    try:
        from alembic import command
        from alembic.config import Config
    except Exception as exc:  # alembic not installed
        return f"alembic unavailable: {exc}"
    try:
        backend = str(BACKEND_DIR)
        if backend not in sys.path:
            sys.path.insert(0, backend)
        os.environ.setdefault("DATABASE_URL", database_url())
        config = Config(os.path.join(backend, "alembic.ini"))
        # alembic.ini ships with a *relative* script_location ("alembic"), which
        # only resolves when the process cwd is backend/.  The desktop app starts
        # from the project root (or a frozen exe), so pin the absolute paths.
        config.set_main_option("script_location", os.path.join(backend, "alembic"))
        config.set_main_option(
            "version_locations", os.path.join(backend, "alembic", "versions")
        )

        # Never alter an existing schema without a recoverable snapshot.
        _backup_before_migration(config)

        # Detect the un-stamped but current legacy schema and stamp it to head.
        engine = sa_create_engine(_runtime_database_url())
        with engine.connect() as connection:
            stamp_only = _stamp_to_head(config, connection)
        engine.dispose()
        if stamp_only:
            command.stamp(config, "head")
            logger.info("Desktop schema already current; stamped alembic head")
            return None

        command.upgrade(config, "head")
        return None
    except Exception as exc:
        logger.warning("Desktop migration failed: %s", exc)
        return f"{type(exc).__name__}: {exc}"


def describe() -> str:
    """One-line human-readable summary for the Settings/diagnostics UI."""
    return (
        f"Database: {os.environ.get('DATABASE_URL') or database_url()}\n"
        f"App data: {appdata_dir()}"
    )
