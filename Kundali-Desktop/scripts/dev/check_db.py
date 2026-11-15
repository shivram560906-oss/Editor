"""Manual DB inspection helper (dev only).

Note: the desktop app stores its database at
%LOCALAPPDATA%\\ShivramJyotish\\jyotish.db — this script inspects the
project-root jyotish.db left over from older runs.

Usage:  python scripts/dev/check_db.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "jyotish.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print(cursor.fetchall())
cursor.execute('PRAGMA table_info(users)')
for row in cursor.fetchall():
    print(row)
cursor.execute('PRAGMA table_info(otp_store)')
for row in cursor.fetchall():
    print(row)
conn.close()
