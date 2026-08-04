# FUTMinna MATLAB Space

FUTMinna MATLAB Space is a one-week, hands-on MATLAB training program at Federal University of Technology, Minna. **August 17 – 24, 2026**.

**Live Site:** Available on Vercel

> The app reads its database connection from `DATABASE_URL`; it is not hardcoded into the script. If you run it locally without that variable, the site still starts, but registration and admin routes stay disabled until you configure Postgres.

## Overview

- **Registration form** — collects name, email, phone, level, department, and expectation
- **Admin dashboard** — lets admins search, filter, paginate, and export registrations
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

## Deploying to Vercel

In your Vercel project → **Settings → Environment Variables**, add:

- `DATABASE_URL` — your pooled connection string
- `ADMIN_PASSWORD` — a strong password for the admin dashboard
- `SECRET_KEY` — any long random string (recommended)

Then redeploy. Registrations persist in your database across cold starts.

## Project Structure

```
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── index.html              # Landing page + registration form
├── style.css               # All styles + animations
├── script.js               # Particles, scroll reveals, form logic
└── templates/
    ├── admin_login.html    # Admin login page
    └── admin_dashboard.html # Admin dashboard with search/filter/export/pagination
```

## License

MIT
