"""
backfill users columns that only ever existed via create_all()

Revision ID: 0005_backfill_user_columns
Revises: 0004_add_user_phone
Create Date: 2026-09-26

``forgot_password_requested`` and ``last_reset_password`` were added to the
User model without a matching migration, so a database that was brought up
through Alembic (or a fresh install that was stamped) was missing them and every
login failed with "no such column: users.forgot_password_requested".

This closes that gap.  ``full_name`` / ``last_reset_password`` may already exist
on a desktop database, so each column is added only when absent.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision: str = "0005_backfill_user_columns"
down_revision: Union[str, None] = "0004_add_user_phone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_missing() -> None:
    inspector = sa_inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return
    live = {c["name"] for c in inspector.get_columns("users")}
    if "forgot_password_requested" not in live:
        op.add_column(
            "users",
            sa.Column("forgot_password_requested", sa.Boolean(), nullable=False,
                      server_default=sa.false()),
        )
    if "last_reset_password" not in live:
        op.add_column("users", sa.Column("last_reset_password", sa.String(), nullable=True))


def upgrade() -> None:
    _add_missing()


def downgrade() -> None:
    inspector = sa_inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return
    live = {c["name"] for c in inspector.get_columns("users")}
    for name in ("last_reset_password", "forgot_password_requested"):
        if name in live:
            op.drop_column("users", name)
