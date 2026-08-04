import os
import csv
import io
import secrets
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_url_path="")

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print("WARNING: SECRET_KEY not set; using a random value (sessions reset on every restart)")
app.secret_key = SECRET_KEY

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_hex(16)
    print("WARNING: ADMIN_PASSWORD not set; admin login is disabled until you set it")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not set; registrations and admin features are disabled until you configure a Postgres connection.")

DB_AVAILABLE = bool(DATABASE_URL)


def get_db():
    if not DB_AVAILABLE:
        raise RuntimeError("DATABASE_URL is not configured.")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def ensure_db():
    if not DB_AVAILABLE:
        return False
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id SERIAL PRIMARY KEY,
                    fullname TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    level TEXT NOT NULL,
                    department TEXT NOT NULL,
                    expectation TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'Africa/Lagos')
                )
            """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_registrations_email_lower "
                "ON registrations (LOWER(email))"
            )
        conn.commit()
    return True


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DB_AVAILABLE:
            return render_template(
                "admin_login.html",
                error="DATABASE_URL is not set. Configure a Postgres connection to enable registrations and admin access."
            ), 503
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def serve_css():
    return send_from_directory(BASE_DIR, "style.css", mimetype="text/css")


@app.route("/script.js")
def serve_js():
    return send_from_directory(BASE_DIR, "script.js", mimetype="application/javascript")


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(os.path.join(BASE_DIR, "images"), filename)


@app.route("/api/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    if not DB_AVAILABLE:
        return jsonify({"error": "DATABASE_URL is not set. Registration is disabled until you configure a Postgres connection."}), 503
    data = request.get_json(force=True)
    required = ["fullname", "email", "phone", "level", "department", "expectation"]
    if not all(data.get(f, "").strip() for f in required):
        return jsonify({"error": "Missing fields"}), 400

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO registrations (fullname, email, phone, level, department, expectation) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (data["fullname"].strip(), data["email"].strip().lower(), data["phone"].strip(),
                     data["level"], data["department"].strip(), data["expectation"])
                )
            conn.commit()
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "This email is already registered."}), 409
    except psycopg2.Error:
        return jsonify({"error": "Could not save your registration. Please try again."}), 500

    return jsonify({"message": "Registration successful"}), 201


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if ADMIN_PASSWORD and secrets.compare_digest(password, ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid password. Please try again."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


PER_PAGE = 25


def build_query(filters):
    search = filters.get("search")
    level_filter = filters.get("level")
    dept_filter = filters.get("department")

    query = "SELECT id, fullname, email, phone, level, department, expectation, created_at FROM registrations WHERE 1=1"
    params = []

    if search:
        query += " AND (fullname ILIKE %s OR email ILIKE %s OR department ILIKE %s OR phone ILIKE %s)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    if level_filter:
        query += " AND level = %s"
        params.append(level_filter)

    if dept_filter:
        query += " AND department = %s"
        params.append(dept_filter)

    return query, params


@app.route("/admin")
@admin_required
def admin_dashboard():
    search = request.args.get("search", "").strip()
    level_filter = request.args.get("level", "").strip()
    dept_filter = request.args.get("department", "").strip()

    filters = {"search": search, "level": level_filter, "department": dept_filter}
    where_query, params = build_query(filters)

    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    with get_db() as conn:
        with conn.cursor() as cur:
            count_query = where_query.replace(
                "SELECT id, fullname, email, phone, level, department, expectation, created_at",
                "SELECT COUNT(*)"
            )
            cur.execute(count_query, params)
            filtered_count = cur.fetchone()[0]
            total_pages = max((filtered_count + PER_PAGE - 1) // PER_PAGE, 1)
            page = min(page, total_pages)

            cur.execute(where_query + " ORDER BY id DESC LIMIT %s OFFSET %s", params + [PER_PAGE, (page - 1) * PER_PAGE])
            rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM registrations")
            total = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM registrations WHERE created_at::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Africa/Lagos')::date")
            today_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT department) FROM registrations WHERE department != ''")
            unique_depts = cur.fetchone()[0]

            cur.execute("SELECT DISTINCT department FROM registrations WHERE department != '' ORDER BY department")
            departments = [r[0] for r in cur.fetchall()]

    window = 2
    start = max(page - window, 1)
    end = min(page + window, total_pages)
    page_range = list(range(start, end + 1))

    return render_template("admin_dashboard.html",
        rows=rows, total=total, today_count=today_count,
        unique_depts=unique_depts, departments=departments,
        search=search, level_filter=level_filter, dept_filter=dept_filter,
        page=page, total_pages=total_pages, page_range=page_range,
        has_prev=page > 1, has_next=page < total_pages, per_page=PER_PAGE)


@app.route("/admin/export")
@admin_required
def export_csv():
    search = request.args.get("search", "").strip()
    level_filter = request.args.get("level", "").strip()
    dept_filter = request.args.get("department", "").strip()

    filters = {"search": search, "level": level_filter, "department": dept_filter}
    where_query, params = build_query(filters)
    query = "SELECT fullname, email, phone, level, department, expectation, created_at FROM registrations WHERE 1=1"
    if search or level_filter or dept_filter:
        query = where_query.replace(
            "SELECT id, fullname, email, phone, level, department, expectation, created_at",
            "SELECT fullname, email, phone, level, department, expectation, created_at"
        )
    query += " ORDER BY id DESC"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(["Full Name", "Email", "Phone", "Level", "Department", "Expectation", "Timestamp"])
    for r in rows:
        writer.writerow(list(r))

    return app.response_class(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"}
    )


if __name__ == "__main__":
    ensure_db()
    app.run(debug=True, port=5000)
