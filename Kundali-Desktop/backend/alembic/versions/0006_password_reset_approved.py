"""
add the admin-approval flag for normal-user password resets

Revision ID: 0006_password_reset_approved
Revises: 0005_backfill_user_columns
Create Date: 2026-09-26

A normal user can no longer reset their password from the stored mobile number
(that is the *admin's* recovery route).  Instead they file a "password change
request", the admin approves it, and this new column records that approval so
the reset page unlocks for exactly that user.

``forgot_password_requested`` stays as it was - it is the pending request flag.
``password_reset_approved`` is the admin's answer to it, and is consumed (reset
to False) the moment the user saves their new password.

Like 0005, every column is added only when absent so a desktop database that
was created by ``create_all()`` is upgraded without being rebuilt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision: str = "0006_password_reset_approved"
down_revision: Union[str, None] = "0005_backfill_user_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMN = "password_reset_approved"


def upgrade() -> None:
    inspector = sa_inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return
    if _COLUMN not in {c["name"] for c in inspector.get_columns("users")}:
        op.add_column(
            "users",
            sa.Column(_COLUMN, sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    inspector = sa_inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return
    if _COLUMN in {c["name"] for c in inspector.get_columns("users")}:
        op.drop_column("users", _COLUMN)