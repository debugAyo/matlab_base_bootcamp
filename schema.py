import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    level TEXT NOT NULL,
    department TEXT NOT NULL,
    expectation TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id INTEGER NOT NULL REFERENCES registrations(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    marked_at TEXT NOT NULL,
    UNIQUE(registration_id, day_number)
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id INTEGER NOT NULL UNIQUE REFERENCES registrations(id) ON DELETE CASCADE,
    days_attended INTEGER NOT NULL DEFAULT 0,
    eligible INTEGER NOT NULL DEFAULT 0,
    certificate_number TEXT UNIQUE,
    certificate_pdf BLOB,
    generated_at TEXT,
    sent_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cert_template (
    id INTEGER PRIMARY KEY,
    image BLOB NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS smtp_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def create_schema(conn):
    with conn.cursor() as cur:
        cur.executescript(SCHEMA_SQL)
    conn.commit()