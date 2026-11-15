"""
add user phone + profile-change support

Revision ID: 0004_add_user_phone
Revises: 9d87ce3f33a4
Create Date: 2026-09-26

Adds the informational contact number that registration now requires.  The
number is *not* an OTP factor (the project has no SMS gateway): it is stored for
information and is only compared when the owner asks to recover the master
password, and as the confirmation value when a user updates their own profile.

Note: this deliberately does NOT use ``batch_alter_table``.  Adding columns to
SQLite is a cheap ``ALTER TABLE ... ADD COLUMN`` that preserves every existing
row, constraint and index; the batch copy-and-swap would instead recreate the
table and fail on legacy schemas where the earlier migrations never ran
(e.g. a desktop database created by ``create_all()`` with a NOT NULL ``email``).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_add_user_phone"
down_revision: Union[str, None] = "9d87ce3f33a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table_name: str) -> set[str]:
    """Column names already present on *table_name* (empty if it is absent)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    # Legacy desktop databases were created by ``Base.metadata.create_all()``
    # and may already have some/all of these columns even though Alembic never
    # recorded 0004.  ``ALTER TABLE ... ADD COLUMN`` is not idempotent, so add
    # only what is genuinely missing instead of aborting the whole migration.
    existing = _existing_columns("users")
    columns = (
        ("phone", sa.String()),
        ("phone_verified_at", sa.DateTime()),
        ("phone_updated_at", sa.DateTime()),
    )
    for name, column_type in columns:
        if name not in existing:
            op.add_column("users", sa.Column(name, column_type, nullable=True))


def downgrade() -> None:
    existing = _existing_columns("users")
    for name in ("phone_updated_at", "phone_verified_at", "phone"):
        if name in existing:
            op.drop_column("users", name)

