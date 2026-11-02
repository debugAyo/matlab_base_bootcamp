# SETUP.md

## Project
**FUTMinna MATLAB Space** — Flask app for the MATLAB bootcamp (FUT Minna, Nigeria): public registration form, admin dashboard, daily attendance tracking, and certificate generation/sending (individual, bulk ZIP, and email).

## Current State (as of Sep 2026)
- The app has been **ported to a local SQLite database**. It runs on your PC only (a file-based DB does not work on Vercel serverless).
- Active connection: `DATABASE_URL=sqlite:///bootcamp.db` in `.env`.

## Neon (Postgres) Status — IMPORTANT
- Original cloud database URL is saved in `.env` as **`DATABASE_URL_NEON`**.
- The Neon free tier exceeded its **data-transfer quota**, so all connections are blocked (pooled + direct + web SQL editor).
- **Your data is safe — nothing was deleted.** It is waiting in Neon until the quota resets (monthly). Check the exact reset date at: **console.neon.tech → project → Usage**.
- Do **not** delete or edit data in Neon — it is your original source of record.

## How to Run Locally
```bash
python app.py
```
- Open http://localhost:5000
- Admin login: **admin** / **a1000b2000** (set via `ADMIN_PASSWORD` in `.env`)

## Certificate Workflow (current "forget attendance, use names" mode)
1. **Upload the certificate template image** → Admin → **Certificates** page → template uploader (PNG/JPG, max 15 MB).
2. **Upload a names spreadsheet** → Admin → **Registrations** → Import → choose the Excel file (a sheet with just a **`Name`** column is enough) → tick **"Fast issue"** → Import. Everyone in the sheet becomes certificate-ready.
3. **Generate certificates** → Admin → **Quick Generate** (nav bar):
   - Type any name → **Download PDF** → instant single certificate.
   - Click **Download all as ZIP** → one PDF per name in the database.
4. Names are styled automatically; tune position/size/color via the **Certificates** page (preview tool).

## Recovering Data from Neon (month-end, once quota resets)
```bash
python migrate_to_sqlite.py
```
Copies all tables into `bootcamp.db`: registrations, attendance, admins, settings, certificates (with stored PDFs), certificate template image, and SMTP settings — preserving IDs and relations.

## Architecture Notes (read before editing)
- **No ORM.** All queries are raw SQL. The code is SQLite-flavored: placeholders are `?`, `LIKE` instead of `ILIKE`, `date(created_at)` instead of `created_at::date`, dynamic `IN (?,?,...)` instead of `= ANY(%s)`.
- `get_db()` in `app.py` returns a `_SQLiteConn` connection (commits/rolls back + closes on `with`) whose `cursor()` returns `_SQLiteCursor`. This is required because **Python 3.11**'s `sqlite3.Cursor` does not support the context manager protocol.
- **Timestamps** are stored as Lagos (Africa/Lagos) time text strings via `certs.lagos_now()` in `certificates.py` — e.g. `2026-08-17 09:30:00`. Simple `date(created_at)` queries work on these.
- **Schema** lives in `schema.py` (`create_schema(conn)`), shared by the app startup (`ensure_db`) and `migrate_to_sqlite.py`. If you change the schema, change it there.
- `email` uses a plain `UNIQUE` constraint (replaces the old Postgres `LOWER(email)` index); emails are always stored lowercase. Duplicate-email errors surface as `sqlite3.IntegrityError`.
- Quick generate endpoints: `/admin/certificates/quick`, `/admin/certificates/quick/build` (single PDF), `/admin/certificates/quick/bulk` (ZIP of everyone).
- Imports: `/admin/import/registrations` accepts name-only sheets and a `fast_issue` flag. `/admin/import/attendance` imports per-day attendance.

## Deployment / Branches
- The original **PostgreSQL + Vercel** version is preserved intact on the git branch **`deploy-neon`**.
- Current branch (`main`) is the SQLite/local workflow. Do **not** run `deploy-neon` code against the current `.env` (it expects a Postgres `DATABASE_URL`).
- The local DB (`bootcamp.db`) and `.env` are gitignored — they will not be committed.

## Useful Facts
- Admin pages are rate-limited only for the public `/api/register` endpoint (flask-limiter). Credentials: `cert.futminnamatlabspace@gmail.com` (SMTP) — see `.env`.
- Bootcamp days are hardcoded in `app.py` (`BOOTCAMP_DAYS`, Aug 17–24 2026).