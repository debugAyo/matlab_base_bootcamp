import io
import os
import smtplib
import re
from email.message import EmailMessage

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")

FONTS = {
    "georgia": os.path.join(FONT_DIR, "georgia.ttf"),
    "georgia_bold": os.path.join(FONT_DIR, "georgiab.ttf"),
    "times": os.path.join(FONT_DIR, "times.ttf"),
    "arial": os.path.join(FONT_DIR, "arial.ttf"),
    "arial_bold": os.path.join(FONT_DIR, "arialbd.ttf"),
}

CERT_SETTINGS_DEFAULTS = {
    "cert_min_days": "4",
    "cert_name_x": "50",
    "cert_name_y": "60",
    "cert_name_size": "3.8",
    "cert_name_color": "000000",
    "cert_font": "georgia",
    "cert_event_name": "FUTMinna MATLAB Space",
    "cert_theme": "Beyond the Code, Decode Your World",
    "cert_number_prefix": "FMNS-2026",
    "cert_body": "for successfully completing the intensive hands-on MATLAB training workshop.",
}

CERT_SETTING_KEYS = list(CERT_SETTINGS_DEFAULTS.keys())


def get_settings(conn):
    settings = dict(CERT_SETTINGS_DEFAULTS)
    with conn.cursor() as cur:
        cur.execute("SELECT key, value FROM settings")
        for key, value in cur.fetchall():
            if key in settings:
                settings[key] = value
    return settings


def save_settings(conn, values):
    with conn.cursor() as cur:
        for key, value in values.items():
            if key in CERT_SETTINGS_DEFAULTS:
                cur.execute(
                    "INSERT INTO settings (key, value) VALUES (%s, %s) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    (key, str(value)),
                )
    conn.commit()


def get_template(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT image FROM cert_template WHERE id = 1")
        row = cur.fetchone()
        return row[0] if row else None


def save_template(conn, image_bytes):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO cert_template (id, image, created_at) VALUES (1, %s, NOW() AT TIME ZONE 'Africa/Lagos') "
            "ON CONFLICT (id) DO UPDATE SET image = EXCLUDED.image, created_at = NOW() AT TIME ZONE 'Africa/Lagos'",
            (image_bytes,),
        )
    conn.commit()


def normalize_name(name):
    if not name:
        return name or ""
    name = re.sub(r"\s+", " ", name.strip())
    tokens = []
    for word in name.split(" "):
        parts = re.split(r"([-' ])", word)
        word_out = ""
        for part in parts:
            if part in ("-", "'"):
                word_out += part
            elif part.strip():
                word_out += part.capitalize()
            else:
                word_out += part
        tokens.append(word_out)
    return " ".join(tokens)


def load_font(font_key, size):
    if font_key not in FONTS:
        font_key = "georgia"
    return ImageFont.truetype(FONTS[font_key], size)


def parse_color(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0, 0, 0)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _fit_name_lines(name, font, max_width):
    if font.getbbox(name)[2] <= max_width:
        return [name]
    words = name.split(" ")
    if len(words) >= 3:
        mid = len(words) // 2
        first = " ".join(words[:mid])
        second = " ".join(words[mid:])
        if font.getbbox(first)[2] <= max_width and font.getbbox(second)[2] <= max_width:
            return [first, second]
    return [name]


def render_certificate_png(template_bytes, name, settings):
    img = Image.open(io.BytesIO(template_bytes)).convert("RGB")
    width, height = img.size
    draw = ImageDraw.Draw(img)

    font_size = int(width * float(settings.get("cert_name_size", 3.8)) / 100.0)
    font = load_font(settings.get("cert_font", "georgia"), font_size)

    max_width = width * 0.85
    while font.getbbox(name)[2] > max_width and font.size > 8:
        font = load_font(settings.get("cert_font", "georgia"), font.size - 1)

    lines = _fit_name_lines(name, font, max_width)
    color = parse_color(settings.get("cert_name_color", "000000"))

    x = width * float(settings.get("cert_name_x", 50)) / 100.0
    y = height * float(settings.get("cert_name_y", 60)) / 100.0
    line_height = font.size * 1.15
    start_y = y - (len(lines) - 1) * line_height / 2.0

    for i, line in enumerate(lines):
        draw.text((x, start_y + i * line_height), line, font=font, fill=color, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_certificate_pdf(template_bytes, name, settings):
    png = render_certificate_png(template_bytes, name, settings)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def assign_next_certificate_number(conn, prefix):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM certificates WHERE certificate_number IS NOT NULL"
        )
        count = cur.fetchone()[0]
    return f"{prefix}-{count + 1:04d}"


def eligible_participants(conn, min_days):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.id, r.fullname, r.email,
                   COUNT(a.id) AS days_attended
            FROM registrations r
            LEFT JOIN attendance a ON a.registration_id = r.id
            GROUP BY r.id, r.fullname, r.email
            ORDER BY r.fullname ASC
            """
        )
        rows = cur.fetchall()

        cur.execute("SELECT registration_id, day_number FROM attendance")
        matrix = {}
        for reg_id, day in cur.fetchall():
            matrix.setdefault(reg_id, set()).add(day)

        cur.execute("SELECT registration_id FROM certificates")
        existing = {r[0] for r in cur.fetchall()}

    participants = []
    for r in rows:
        reg_id, fullname, email, days = r
        participants.append({
            "registration_id": reg_id,
            "fullname": normalize_name(fullname),
            "email": email or "",
            "days_attended": days or 0,
            "days_list": sorted(matrix.get(reg_id, set())),
            "eligible": (days or 0) >= min_days,
            "has_certificate": reg_id in existing,
        })
    return participants


def is_placeholder_email(email):
    return not email or "placeholder.local" in email.lower() or "@" not in email


def smtp_configured():
    return bool(
        os.environ.get("SMTP_HOST")
        and os.environ.get("SMTP_USER")
        and os.environ.get("SMTP_PASSWORD")
    )


def send_certificate_email(to_email, fullname, cert_number, pdf_bytes, settings):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    from_addr = os.environ.get("MAIL_FROM", user)
    from_name = os.environ.get("MAIL_FROM_NAME", settings.get("cert_event_name", "FUTMinna MATLAB Space"))

    event = settings.get("cert_event_name", "FUTMinna MATLAB Space")
    theme = settings.get("cert_theme", "")

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to_email
    msg["Subject"] = f"Congratulations {fullname} \u2014 Certificate of Participation ({event})"
    msg.set_content(
        f"Dear {fullname},\n\n"
        f"Congratulations! You successfully completed the {event} training.\n"
        f"{theme}\n\n"
        f"Your certificate number is {cert_number}.\n"
        f"Attached is your personalized certificate. Please keep it safe.\n\n"
        f"Thank you for participating.\n"
        f"{from_name}"
    )

    safe_name = re.sub(r"[^A-Za-z0-9 _-]", "", fullname).replace(" ", "_")
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"FUTMinna_MATLAB_Certificate_{safe_name}.pdf",
    )

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        if port in (587, 2525, 465):
            server.starttls()
            server.ehlo()
        server.login(user, password)
        server.send_message(msg)

    return True