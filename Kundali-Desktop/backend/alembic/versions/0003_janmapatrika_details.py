"""add traditional Janmapatrika identity details

Revision ID: 0003_janmapatrika_details
Revises: 0002_auth_admin
Create Date: 2026-08-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


revision: str = "0003_janmapatrika_details"
down_revision: Union[str, None] = "0002_auth_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS = (
    ("timezone_id", 100),
    ("country", 100),
    ("birth_place", 200),
    ("full_name", 200),
    ("father_name", 200),
    ("mother_name", 200),
    ("gotra", 100),
    ("surname", 100),
    ("kula", 100),
    ("kuladevata", 200),
    ("spouse_name", 200),
    ("marital_status", 50),
    ("caste", 100),
    ("religion", 100),
    ("family_details", 2000),
)


def upgrade() -> None:
    # Skip columns that already exist: a desktop database created by
    # Base.metadata.create_all() has them all, and a bare ADD COLUMN would abort.
    inspector = sa_inspect(op.get_bind())
    if "kundali_records" not in inspector.get_table_names():
        return
    live = {c["name"] for c in inspector.get_columns("kundali_records")}
    for name, length in _COLUMNS:
        if name in live:
            continue
        op.add_column("kundali_records", sa.Column(name, sa.String(length=length), nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("kundali_records", name)
