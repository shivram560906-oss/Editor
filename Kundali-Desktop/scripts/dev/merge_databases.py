#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/dev/merge_databases.py

Consolidate legacy Jyotish databases into the one canonical desktop database.

Background
----------
Before ``gui/paths.py`` existed, three modules each set ``DATABASE_URL`` with a
different path, so depending on import order the app used either

    %LOCALAPPDATA%\\ShivramJyotish\\jyotish.db   (canonical)
    <repo_root>/jyotish.db                       (legacy, still holds data)

Saved kundalis therefore appeared to "disappear" between launches.

Safety
------
* **Dry run by default** - nothing is written without ``--apply``.
* The canonical database is backed up before any write, and the merge runs in a
  single transaction that is rolled back on error.
* Source databases are opened read-only and are never deleted.
* Duplicate kundalis (same name + birth date/time + coordinates) are skipped and
  reported instead of being copied twice.

Usage
-----
    python scripts/dev/merge_databases.py            # dry run
    python scripts/dev/merge_databases.py --apply    # write
"""
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gui.paths import database_path  # noqa: E402

MERGE_TABLES = ("users", "kundali_records", "settings", "app_config")
KUNDALI_IDENTITY = ("name", "birth_date", "birth_time", "latitude", "longitude")

#: Integer primary keys restart at 1 in every database, so the column must not
#: be copied - otherwise the first rows collide with UNIQUE(id) and silently
#: skip.  SQLite assigns a fresh id when the column is omitted.
AUTO_ID_TABLES = {"users", "kundali_records", "settings", "app_config"}


def _connect_readonly(path):
    return sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)


def _tables(conn):
    return {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}


def _columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def candidate_sources(canonical):
    """Legacy databases that may still hold data."""
    out = []
    for path in (REPO / "jyotish.db", REPO / "backend" / "jyotish.db"):
        if path.exists() and path.resolve() != Path(canonical).resolve():
            out.append(path)
    return out


def _kundali_key(row):
    return tuple(row.get(column) for column in KUNDALI_IDENTITY)


def _existing_kundali_keys(canonical):
    conn = _connect_readonly(canonical)
    try:
        if "kundali_records" not in _tables(conn):
            return set()
        return {tuple(r) for r in conn.execute(
            f"SELECT {', '.join(KUNDALI_IDENTITY)} FROM kundali_records"
        )}
    finally:
        conn.close()


def _existing_usernames(canonical):
    conn = _connect_readonly(canonical)
    try:
        if "users" not in _tables(conn):
            return set()
        return {r[0] for r in conn.execute("SELECT username FROM users")}
    finally:
        conn.close()


def _existing_config_keys(canonical, table):
    """Keyed tables (``app_config``) are deduped by their ``key`` column.

    ``settings`` has no ``key`` column - it is a per-user single row - so it
    simply has no dedupe key.
    """
    conn = _connect_readonly(canonical)
    try:
        if table not in _tables(conn):
            return set()
        columns = [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]
        if "key" not in columns:
            return set()
        return {r[0] for r in conn.execute(f"SELECT key FROM {table}")}
    finally:
        conn.close()


def analyse(canonical, sources):
    """Describe what would be copied, without writing anything."""
    report = {"canonical": str(canonical), "sources": []}
    seen_keys = _existing_kundali_keys(canonical)
    seen_users = _existing_usernames(canonical)

    for src in sources:
        conn = _connect_readonly(src)
        try:
            present = _tables(conn)
            info = {"path": str(src), "tables": {}, "inserts": {},
                    "skipped": {}, "conflicts": []}
            for table in MERGE_TABLES:
                if table not in present:
                    continue
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                cols = _columns(conn, table)
                info["tables"][table] = len(rows)
                inserts = skipped = 0
                for raw in rows:
                    row = dict(zip(cols, raw))
                    if table == "kundali_records":
                        key = _kundali_key(row)
                        if key in seen_keys:
                            skipped += 1
                            continue
                        seen_keys.add(key)
                    if table == "users" and row.get("username") in seen_users:
                        info["conflicts"].append(
                            f"user '{row['username']}' already exists in the "
                            "canonical database - keeping the existing one"
                        )
                        skipped += 1
                        continue
                    inserts += 1
                info["inserts"][table] = inserts
                info["skipped"][table] = skipped
            report["sources"].append(info)
        finally:
            conn.close()
    return report




def apply(canonical, sources):
    """Copy missing rows into the canonical database inside one transaction."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = Path(str(canonical) + f".bak-{stamp}")
    shutil.copy2(canonical, backup)
    print(f"Backup written: {backup}")

    conn = sqlite3.connect(canonical)
    inserted = 0
    try:
        canon_tables = _tables(conn)
        for src in sources:
            sconn = _connect_readonly(src)
            try:
                present = _tables(sconn)
                for table in MERGE_TABLES:
                    if table not in present or table not in canon_tables:
                        continue
                    shared = [c for c in _columns(sconn, table)
                              if c in set(_columns(conn, table))]
                    if table in AUTO_ID_TABLES:
                        shared = [c for c in shared if c != "id"]
                    if not shared:
                        continue
                    rows = sconn.execute(
                        f"SELECT {', '.join(shared)} FROM {table}"
                    ).fetchall()
                    placeholders = ", ".join("?" * len(shared))
                    if table == "kundali_records":
                        seen_keys = _existing_kundali_keys(canonical)
                    if table == "users":
                        seen_users = _existing_usernames(canonical)
                    if table in ("settings", "app_config"):
                        seen_config = _existing_config_keys(canonical, table)
                    for raw in rows:
                        row = dict(zip(shared, raw))
                        if table == "kundali_records":
                            key = _kundali_key(row)
                            if key in seen_keys:
                                continue
                            seen_keys.add(key)
                        if table == "users" and row.get("username") in seen_users:
                            continue
                        if table in ("settings", "app_config"):
                            config_key = row.get("key")
                            if config_key and config_key in seen_config:
                                continue
                            if config_key:
                                seen_config.add(config_key)
                        try:
                            conn.execute(
                                f"INSERT INTO {table} ({', '.join(shared)}) "
                                f"VALUES ({placeholders})", raw,
                            )
                            inserted += 1
                        except sqlite3.Error as exc:
                            print(f"    skipped a {table} row: {exc}")
            finally:
                sconn.close()
        conn.commit()
    except Exception:
        conn.rollback()
        print("Merge failed - rolled back. The backup is intact.")
        raise
    finally:
        conn.close()
    return inserted


def dedupe_settings(canonical):
    """``settings`` holds one row per user; merging can leave duplicates.

    Keeps the lowest id per (user_id) and reports how many rows were removed.
    """
    conn = sqlite3.connect(canonical)
    removed = 0
    try:
        if "settings" not in _tables(conn):
            return 0
        seen = set()
        for row_id, user_id in conn.execute("SELECT id, user_id FROM settings ORDER BY id").fetchall():
            if user_id in seen:
                conn.execute("DELETE FROM settings WHERE id = ?", (row_id,))
                removed += 1
            else:
                seen.add(user_id)
        conn.commit()
    finally:
        conn.close()
    return removed


def main():
    parser = argparse.ArgumentParser(description="Merge legacy Jyotish databases.")
    parser.add_argument("--apply", action="store_true",
                        help="write to the canonical database (default: dry run)")
    args = parser.parse_args()

    canonical = database_path(create=False)
    if not os.path.exists(canonical):
        print(f"Canonical database not found: {canonical}")
        return 1
    sources = candidate_sources(canonical)
    print(f"Canonical database : {canonical}")
    print(f"Source databases   : {len(sources)}")
    if not sources:
        print("Nothing to merge - no legacy databases found.")
        return 0

    for info in analyse(canonical, sources)["sources"]:
        print(f"\n--- {info['path']}")
        for table, total in info["tables"].items():
            print(f"    {table:16s} rows={total:<5d} to_insert={info['inserts'][table]:<5d} "
                  f"skipped={info['skipped'][table]}")
        for conflict in info["conflicts"]:
            print(f"    ! {conflict}")

    if not args.apply:
        print("\nDRY RUN - nothing was written. Re-run with --apply to merge.")
        return 0

    inserted = apply(canonical, sources)
    removed = dedupe_settings(canonical)
    print(f"\nMerged {inserted} rows into {canonical}")
    if removed:
        print(f"Removed {removed} duplicate settings row(s).")
    print("Source databases were left untouched; verify the app, then delete them manually.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
