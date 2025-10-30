# ErrandBuddy
INFO project
# ErrandBuddy

A mobile-style app for students to:
- Post and complete microtasks
- Find study or commute buddies
- Chat in real time

## Tech Stack
- Frontend: Kivy (Python)
- Backend: Flask (Python)
- Database: MySQL
- Real-time: Flask-SocketIO

## Team Members
- Ramanpreet Kaur (Frontend)
- Laiba Ali (UI Design)
- Umer Ahmad (Backend)
- Landon Taylor (Database)
- Yu-Hao Cha (Testing & Integration)

## Run Instructions
### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py

## Frontend
- Recommended: Python 3.11 on Windows (Kivy wheels available)
- Create venv and install root requirements:
  - py -3.11 -m venv .venv311
  - ./.venv311/Scripts/python.exe -m pip install --upgrade pip
  - ./.venv311/Scripts/pip.exe install -r requirements.txt
- Run: ./.venv311/Scripts/python.exe frontend/main.py

Notes: On Python 3.14, Kivy wheels are not yet available and install fails.

## Email OTP Setup
ErrandBuddy supports email verification (OTP) during signup and requires SMTP configuration.

- Create `backend/.env` with these keys (see `backend/.env.example`):
  - `SMTP_HOST`: your SMTP server host (e.g., `smtp.gmail.com`)
  - `SMTP_PORT`: port (e.g., `465` for SSL or `587` for STARTTLS)
  - `SMTP_USER`: SMTP username (often your email address)
  - `SMTP_PASSWORD`: SMTP password or provider API key
  - `SMTP_FROM`: from/sender email address
  - `SMTP_USE_SSL`: `true` to use SMTPS (port 465)
  - `SMTP_USE_TLS`: `true` to use STARTTLS (port 587)

The backend auto-loads environment variables from `backend/.env` via `python-dotenv`.

Example (Gmail with App Password):
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=yourname@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=yourname@gmail.com
SMTP_USE_SSL=true
SMTP_USE_TLS=false
```

Security: do not commit real credentials. Share `.env` out-of-band or use a secrets manager.
