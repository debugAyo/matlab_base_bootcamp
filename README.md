# FUTMinna MATLAB Base

A one-week, hands-on MATLAB training program at Federal University of Technology, Minna. **August 17 – 24, 2026**.

**Live Site:** [futminna-matlab-base.vercel.app](https://futminna-matlab-base.vercel.app)

## What It Does

- **Registration form** — students sign up with name, email, phone, level, department, and expectation
- **Admin dashboard** — view all registrations, search/filter by name/email/department/level, export to CSV
- **Success modal** — after registration, shows bootcamp details with Google Calendar and .ics download
- **Preloader + animations** — particle canvas, scroll reveals, glassmorphism navbar

## Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** Vanilla HTML/CSS/JS with animations
- **Deploy:** Vercel (serverless)

## Local Setup

```bash
git clone https://github.com/debugAyo/matlab_base_bootcamp.git
cd matlab_base_bootcamp
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`

## Admin Access

- URL: `/admin`
- Password: `admin123` (configurable via `ADMIN_PASSWORD` env var)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `futminna-matlab-base-2026` | Flask session secret |
| `ADMIN_PASSWORD` | `admin123` | Admin dashboard password |
| `DB_PATH` | `./registrations.db` | SQLite database path |

## Project Structure

```
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── public/
│   ├── index.html          # Landing page + registration form
│   ├── style.css           # All styles + animations
│   └── script.js           # Particles, scroll reveals, form logic
└── templates/
    ├── admin_login.html    # Admin login page
    └── admin_dashboard.html # Admin dashboard with search/filter/export
```

## License

MIT
