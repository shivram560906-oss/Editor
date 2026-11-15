"""Manual schema patch for the project-root jyotish.db (dev only).

This script exists because the desktop app used to run
``Base.metadata.create_all()`` instead of running Alembic migrations, so a
model change could leave an existing database without the new columns.
Prefer ``alembic upgrade head`` (backend/) for anything real.

Usage:  python scripts/dev/fix_db.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "jyotish.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add missing columns to users table
columns_to_add = [
    ('role', 'VARCHAR DEFAULT "USER"'),
    ('is_active', 'BOOLEAN DEFAULT 1'),
    ('force_password_change', 'BOOLEAN DEFAULT 0'),
    ('updated_at', 'DATETIME'),
    ('last_login_at', 'DATETIME'),
    ('password_changed_at', 'DATETIME'),
]

for col_name, col_def in columns_to_add:
    try:
        cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_def}')
        print(f'Added {col_name}')
    except Exception as e:
        print(f'Failed to add {col_name}: {e}')

# Add attempt_count and created_at to otp_store if missing
try:
    cursor.execute('ALTER TABLE otp_store ADD COLUMN attempt_count INTEGER DEFAULT 0')
    print('Added attempt_count to otp_store')
except Exception as e:
    print(f'attempt_count: {e}')

try:
    cursor.execute('ALTER TABLE otp_store ADD COLUMN created_at DATETIME')
    print('Added created_at to otp_store')
except Exception as e:
    print(f'created_at: {e}')

conn.commit()

cursor.execute('PRAGMA table_info(users)')
for row in cursor.fetchall():
    print(row)

conn.close()
