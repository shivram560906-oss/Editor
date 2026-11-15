"""Force the alembic_version stamp on the project-root jyotish.db (dev only).

The desktop app never ran Alembic itself, so the version table could drift away
from the real schema. Prefer ``alembic upgrade head`` from backend/.

Usage:  python scripts/dev/update_alembic.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "jyotish.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('UPDATE alembic_version SET version_num = "9d87ce3f33a4"')
conn.commit()
print('Updated alembic_version')
conn.close()
