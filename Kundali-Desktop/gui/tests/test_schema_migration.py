# -*- coding: utf-8 -*-
"""Schema-migration regression tests for the local desktop database.

The desktop database is upgraded by Alembic, not by ``create_all()``.  These
tests run against throw-away SQLite files and never touch the real database.

Account tables remain in the schema so existing installations keep upgrading
cleanly; the application itself no longer uses login, passwords or accounts.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
_BACKEND = REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TMP_DIR = Path(tempfile.mkdtemp(prefix="jyotish_schema_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP_DIR / 'bootstrap.db').as_posix()}"

from gui.paths import run_migrations  # noqa: E402


class SchemaMigrationTests(unittest.TestCase):
    """Alembic, not create_all(), is what upgrades a real desktop database."""

    db_label = "schema"
    _counter = 0

    def setUp(self):
        type(self)._counter += 1
        self.db_path = _TMP_DIR / f"{self.db_label}_{type(self)._counter}.db"
        if self.db_path.exists():
            self.db_path.unlink()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path.as_posix()}"

        from database import connection as db_connection
        from sqlalchemy import create_engine

        db_connection.engine.dispose()
        db_connection.engine = create_engine(
            f"sqlite:///{self.db_path.as_posix()}", future=True
        )
        db_connection.SessionLocal.configure(bind=db_connection.engine)

        from database.models import Base
        import database.models  # noqa: F401  (registers the tables)

        Base.metadata.create_all(bind=db_connection.engine)

    def tearDown(self):
        try:
            from database import connection as db_connection

            db_connection.engine.dispose()
        except Exception:
            pass

    def test_migrations_add_missing_columns(self):
        # run_migrations() reads its URL from backend.config.settings, which is
        # frozen at import time, so point that at this test's database first.
        import config
        from database import connection as db_connection

        previous = config.settings.DATABASE_URL
        config.settings.DATABASE_URL = f"sqlite:///{self.db_path.as_posix()}"
        try:
            self.assertIsNone(run_migrations(), run_migrations())
        finally:
            config.settings.DATABASE_URL = previous
            db_connection.engine.dispose()

        import sqlite3

        connection = sqlite3.connect(self.db_path)
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        finally:
            connection.close()
        for name in (
            "phone",
            "phone_verified_at",
            "phone_updated_at",
            "password_reset_approved",
        ):
            self.assertIn(name, columns)

    def test_legacy_database_is_backed_up_and_upgraded(self):
        """An unstamped create_all() database migrates without being rebuilt.

        A real legacy install has the phone columns (created by the models) but
        no ``password_reset_approved`` and no ``alembic_version`` row.  The
        migration must add the missing column, leave existing data intact, and
        write the backup *before* changing the schema.
        """
        import config
        import sqlite3
        from database import connection as db_connection

        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("ALTER TABLE users DROP COLUMN password_reset_approved")
            connection.commit()
        finally:
            connection.close()

        backup_dir = self.db_path.parent / "backups"
        backups_before = (
            set(backup_dir.glob("jyotish-*.db")) if backup_dir.exists() else set()
        )

        previous = config.settings.DATABASE_URL
        config.settings.DATABASE_URL = f"sqlite:///{self.db_path.as_posix()}"
        try:
            self.assertIsNone(run_migrations())
        finally:
            config.settings.DATABASE_URL = previous
            db_connection.engine.dispose()

        connection = sqlite3.connect(self.db_path)
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
            revision = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()
        finally:
            connection.close()
        self.assertIn("password_reset_approved", columns)
        self.assertIn("phone", columns)
        self.assertEqual(revision, ("0006_password_reset_approved",))

        new_backups = set(backup_dir.glob("jyotish-*.db")) - backups_before
        self.assertTrue(new_backups, "a pre-migration backup must be created")
        newest = max(new_backups, key=lambda path: path.stat().st_mtime)
        connection = sqlite3.connect(newest)
        try:
            backed_up = {
                row[1] for row in connection.execute("PRAGMA table_info(users)")
            }
        finally:
            connection.close()
        self.assertNotIn(
            "password_reset_approved",
            backed_up,
            "the backup must be the schema as it was before migrating",
        )


if __name__ == "__main__":
    unittest.main()
