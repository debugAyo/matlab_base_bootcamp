# FUTMinna MATLAB Space

FUTMinna MATLAB Space is a one-week, hands-on MATLAB training program at Federal University of Technology, Minna. **August 17 – 24, 2026**.

**Live Site:** Available on Vercel

> The app reads its database connection from `DATABASE_URL`; it is not hardcoded into the script. If you run it locally without that variable, the site still starts, but registration and admin routes stay disabled until you configure Postgres.

## Overview

- **Registration form** — collects name, email, phone, level, department, and expectation
- **Admin dashboard** — lets admins search, filter, paginate, and export registrations
- **Daily attendance** — mark present/absent per day (Day 1–8), Excel import/export
- **Certificates** — auto-generate personalized certificate PDFs from attendance, with a configurable "minimum days" eligibility rule, live name positioning preview, single/bulk generation, and email delivery via SMTP
- **Duplicate protection** — one registration per email address
- **Rate limiting** — `/api/register` allows 5 submissions per minute per IP
- **Success modal** — confirms registration and offers Google Calendar and `.ics` download links
- **Polished UI** — animated hero, subtle motion, and a responsive layout

## Stack

- **Backend:** Flask (Python)
- **Database:** PostgreSQL on Neon (serverless, persistent — survives Vercel cold starts)
- **Frontend:** Vanilla HTML/CSS/JS with animations
- **Deploy:** Vercel (serverless)

## Database Setup

1. Create a free account at [neon.tech](https://neon.tech) and create a project.
2. In the project dashboard, open **Connection Details** and copy the **pooled** connection string.
3. Set it as the `DATABASE_URL` environment variable locally and on Vercel.
4. The table is created automatically on first request.

## Brand Copy

- Public name: FUTMinna MATLAB Space
- Email field: prefer a FUTMinna school email if you have one
- Registration placeholders are generic rather than personal examples

## Local Setup

```bash
git clone https://github.com/debugAyo/matlab_base_bootcamp.git
cd matlab_base_bootcamp
pip install -r requirements.txt
$env:DATABASE_URL="postgresql://..."   # your Neon pooled connection string
$env:ADMIN_PASSWORD="your-strong-password"
python app.py
```

Open `http://localhost:5000`.

## Admin Access

- URL: `/admin`
- Password: set via the `ADMIN_PASSWORD` environment variable. If it is not set, login is disabled.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | **Yes** | Postgres pooled connection string |
| `ADMIN_PASSWORD` | **Yes** | Admin dashboard password |
| `SECRET_KEY` | No | Flask session secret. Falls back to a random value per restart if unset |
| `SMTP_HOST` | For sending certs | SMTP server for certificate emails (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | No | SMTP port, defaults to `587` |
| `SMTP_USER` | For sending certs | SMTP username |
| `SMTP_PASSWORD` | For sending certs | SMTP password / app password |
| `MAIL_FROM` | No | "From" address. Defaults to `SMTP_USER` |
| `MAIL_FROM_NAME` | No | Display name in the From line. Defaults to the event name |

> **Note:** SMTP can also be configured from the browser — open **Certificates → SMTP Settings** in the admin dashboard and use the **Test Connection** button. Settings saved there are stored in the database and take effect immediately. Environment variables take priority if both are set.

## Certificates

Open **Admin → Certificates** in the dashboard.

1. **Upload the certificate template** (PNG/JPG) once your designer finishes it.
2. **Position the name** with the live preview — set X, Y, font size (as % of image width), color, and font, then **Save Settings**.
3. **Set the minimum days** to qualify (default 4). Participants with attendance `>=` this number are marked *Eligible*.
4. **Generate All Eligible** creates one personalized PDF per eligible participant. Long names auto-shrink or wrap to two lines.
5. **Download** single certificates, or **Send Unsent Certificates** to email each one (participants with placeholder emails, e.g. `@placeholder.local`, are skipped).

### Preview & Gallery

- **Preview** (per row): opens the actual rendered certificate (PNG) for any participant in a modal, so you can confirm the name/position before sending.
- **Gallery**: a grid of every generated certificate thumbnail at the bottom of the Certificates page. Click any thumbnail to enlarge it. Uses your real participant names.

### Fixing Names ("only one name shows")

Certificates render exactly what is stored in the database. If a participant's name was saved with only one word (e.g. only "Caleb"), use the **Edit Name** button on their row (in either the Dashboard or Certificates page) to enter the correct full name (e.g. "Caleb Emmanuel"). The database is updated and the certificate is **regenerated automatically** if one already exists.

To prevent this going forward, the public registration form **requires a full name** (first + last name), validated on both the frontend and backend (`/api/register`). Imported names are normalized/capitalized on save.

Eligibility can be exported as CSV any time. Certificate PDFs and the template are stored in Postgres so they survive Vercel cold starts.

## Deploying to Vercel

In your Vercel project → **Settings → Environment Variables**, add:

- `DATABASE_URL` — your pooled connection string
- `ADMIN_PASSWORD` — a strong password for the admin dashboard
- `SECRET_KEY` — any long random string (recommended)

Then redeploy. Registrations persist in your database across cold starts.

## Project Structure

```
├── app.py                  # Flask backend
├── certificates.py         # Certificate rendering, eligibility + SMTP email helper
├── fonts/                  # Bundled TTF fonts used for certificate name text
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── index.html              # Landing page + registration form
├── style.css               # All styles + animations
├── script.js               # Particles, scroll reveals, form logic
└── templates/
    ├── admin_login.html    # Admin login page
    ├── admin_dashboard.html # Admin dashboard with search/filter/export/pagination
    ├── admin_attendance.html # Daily attendance marking + Excel import/export
    └── admin_certificates.html # Certificate template upload, positioning, generation & emailing
```

## License

MIT
