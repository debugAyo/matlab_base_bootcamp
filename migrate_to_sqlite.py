"""
One-time migration: copy all data from the Neon (PostgreSQL) database
into the local SQLite database (bootcamp.db).

How to run:
    python migrate_to_sqlite.py

The Neon connection string is read from DATABASE_URL_NEON in .env
(falls back to DATABASE_URL if it still points at Postgres).

If Neon is still blocked by the data-transfer quota you will get a short
message telling you so - then just run this again after the monthly reset
or after an upgrade.
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from schema import create_schema

load_dotenv()

SQLITE_PATH = os.environ.get("SQLITE_PATH", "bootcamp.db")
NEON_URL = (
    os.environ.get("DATABASE_URL_NEON")
    or os.environ.get("DATABASE_URL")
    or ""
)

TABLES = [
    ("registrations", ["id", "fullname", "email", "phone", "level", "department", "expectation", "created_at"]),
    ("attendance", ["id", "registration_id", "day_number", "attendance_date", "marked_at"]),
    ("admins", ["id", "username", "password_hash", "role", "created_at"]),
    ("settings", ["key", "value"]),
    ("certificates", ["id", "registration_id", "days_attended", "eligible", "certificate_number", "certificate_pdf", "generated_at", "sent_at", "created_at"]),
    ("cert_template", ["id", "image", "created_at"]),
    ("smtp_settings", ["key", "value"]),
]


def ts(value):
    """Convert Postgres datetime/date/str to the ISO-style text format used by SQLite."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def normalize_row(table, cols, row):
    out = []
    for col, val in zip(cols, row):
        if table in ("certificates", "cert_template") and col in ("certificate_pdf", "image"):
            out.append(bytes(val) if val is not None else None)
        elif col in ("created_at", "generated_at", "sent_at", "marked_at", "attendance_date"):
            out.append(ts(val))
        else:
            out.append(val)
    return out


def main():
    if not NEON_URL:
        print("No Neon URL found. Set DATABASE_URL_NEON in .env (e.g. postgresql://...).")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("psycopg2 is not installed. Run:  pip install psycopg2-binary")
        sys.exit(1)

    try:
        pg = psycopg2.connect(NEON_URL, sslmode="require", connect_timeout=20)
    except Exception as e:
        msg = str(e)
        print("Could not connect to Neon. Most likely the data-transfer quota is still\n"
              "blocking connections. Check the Neon dashboard (Usage page) for the\n"
              "monthly reset date, then run this script again once it resets.")
        print("\nDetail:", msg.splitlines()[0][:160] if msg else e)
        sys.exit(1)

    sqlite_conn = None
    try:
        import sqlite3
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_conn.execute("PRAGMA foreign_keys = OFF")
        create_schema(sqlite_conn)
        sqlite_conn.execute("PRAGMA foreign_keys = ON")

        print(f"Copying data from Neon into {SQLITE_PATH} ...")
        with pg.cursor() as cur:
            for table, cols in TABLES:
                cur.execute(f"SELECT {', '.join(cols)} FROM {table}")
                rows = cur.fetchall()
                placeholders = ", ".join("?" * len(cols))
                sqlite_conn.executemany(
                    f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
                    [normalize_row(table, cols, row) for row in rows],
                )
                print(f"  {table:<16} {len(rows):>6} rows")

        sqlite_conn.commit()
        print("\nMigration complete. All data is now in the local database.")
    except Exception as e:
        if sqlite_conn:
            sqlite_conn.rollback()
        print("Migration failed:", e)
        sys.exit(1)
    finally:
        pg.close()
        if sqlite_conn:
            sqlite_conn.close()


if __name__ == "__main__":
    main()