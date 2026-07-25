import os
import csv
import io
import sqlite3
from datetime import date
from functools import wraps
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = os.environ.get("VERCEL") == "1"

PUBLIC_DIR = os.path.join(BASE_DIR, "public")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=PUBLIC_DIR, static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "futminna-matlab-base-2026")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

if IS_VERCEL:
    DB = "/tmp/registrations.db"
else:
    DB = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "registrations.db"))

_db_initialized = False


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db():
    global _db_initialized
    if _db_initialized:
        return
    try:
        with get_db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                level TEXT NOT NULL,
                department TEXT NOT NULL,
                expectation TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )""")
            conn.commit()
        _db_initialized = True
    except Exception as e:
        print(f"DB init error: {e}")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ensure_db()
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def home():
    ensure_db()
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(PUBLIC_DIR, filename)


@app.route("/api/register", methods=["POST"])
def register():
    ensure_db()
    data = request.get_json(force=True)
    required = ["fullname", "email", "phone", "level", "department", "expectation"]
    if not all(data.get(f, "").strip() for f in required):
        return jsonify({"error": "Missing fields"}), 400

    with get_db() as conn:
        conn.execute(
            "INSERT INTO registrations (fullname, email, phone, level, department, expectation) VALUES (?, ?, ?, ?, ?, ?)",
            (data["fullname"].strip(), data["email"].strip(), data["phone"].strip(),
             data["level"], data["department"].strip(), data["expectation"])
        )
        conn.commit()
    return jsonify({"message": "Registration successful"}), 201


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    ensure_db()
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid password. Please try again."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    search = request.args.get("search", "").strip()
    level_filter = request.args.get("level", "").strip()
    dept_filter = request.args.get("department", "").strip()

    query = "SELECT id, fullname, email, phone, level, department, expectation, created_at FROM registrations WHERE 1=1"
    params = []

    if search:
        query += " AND (fullname LIKE ? OR email LIKE ? OR department LIKE ? OR phone LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    if level_filter:
        query += " AND level = ?"
        params.append(level_filter)

    if dept_filter:
        query += " AND department = ?"
        params.append(dept_filter)

    query += " ORDER BY id DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
        today_count = conn.execute(
            "SELECT COUNT(*) FROM registrations WHERE DATE(created_at) = ?", (str(date.today()),)
        ).fetchone()[0]
        departments = [r[0] for r in conn.execute(
            "SELECT DISTINCT department FROM registrations WHERE department != '' ORDER BY department"
        ).fetchall()]
        unique_depts = len(departments)

    return render_template("admin_dashboard.html",
        rows=rows, total=total, today_count=today_count,
        unique_depts=unique_depts, departments=departments,
        search=search, level_filter=level_filter, dept_filter=dept_filter)


@app.route("/admin/export")
@admin_required
def export_csv():
    search = request.args.get("search", "").strip()
    level_filter = request.args.get("level", "").strip()
    dept_filter = request.args.get("department", "").strip()

    query = "SELECT fullname, email, phone, level, department, expectation, created_at FROM registrations WHERE 1=1"
    params = []

    if search:
        query += " AND (fullname LIKE ? OR email LIKE ? OR department LIKE ? OR phone LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    if level_filter:
        query += " AND level = ?"
        params.append(level_filter)

    if dept_filter:
        query += " AND department = ?"
        params.append(dept_filter)

    query += " ORDER BY id DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    output = io.StringIO()
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
