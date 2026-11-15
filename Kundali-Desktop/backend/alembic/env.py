"""Alembic environment.

Uses the application's own :class:`Settings` to resolve the database URL so
migrations run against the same database the app uses (honouring ``DATABASE_URL``
and the local SQLite fallback).
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the backend directory is importable so `config`, `database` resolve.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402
from database.connection import Base  # noqa: E402
import database.models  # noqa: F401,E402  # registers models on Base.metadata

# this is the Alembic Config object.
config = context.config

# Inject the runtime database URL.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to a script)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect and apply)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Do NOT enable render_as_batch here.  Batch mode makes Alembic recreate
        # the whole table (copy-and-swap) even for a plain ADD COLUMN, which
        # fails on the legacy desktop schema where earlier migrations never ran
        # (a NOT NULL email with a UNIQUE constraint).  Migration 0004 adds its
        # columns with a native SQLite ALTER TABLE ... ADD COLUMN, which is safe
        # on every desktop database.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=False,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
