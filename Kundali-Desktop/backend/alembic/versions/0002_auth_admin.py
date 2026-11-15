"""add authentication administration support

Revision ID: 0002_auth_admin
Revises: 0001_initial
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


revision: str = "0002_auth_admin"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Desktop databases created by Base.metadata.create_all() already have these
    # tables and columns, so every step is guarded and becomes a no-op there.
    bind = op.get_bind()
    inspector = sa_inspect(bind)

    def _has_column(table: str, column: str) -> bool:
        if table not in inspector.get_table_names():
            return False
        return column in {c["name"] for c in inspector.get_columns(table)}

    if not _has_column("users", "is_master"):
        op.add_column(
            "users",
            sa.Column("is_master", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if "otp_store" not in inspector.get_table_names():
        op.create_table(
            "otp_store",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("otp_code", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_otp_store_id", "otp_store", ["id"])
        op.create_index("ix_otp_store_email", "otp_store", ["email"])

    if "app_config" not in inspector.get_table_names():
        op.create_table(
            "app_config",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("key", sa.String(), nullable=False),
            sa.Column("value", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_app_config_id", "app_config", ["id"])
        op.create_index("ix_app_config_key", "app_config", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_app_config_key", table_name="app_config")
    op.drop_index("ix_app_config_id", table_name="app_config")
    op.drop_table("app_config")
    op.drop_index("ix_otp_store_email", table_name="otp_store")
    op.drop_index("ix_otp_store_id", table_name="otp_store")
    op.drop_table("otp_store")
    op.drop_column("users", "is_master")
