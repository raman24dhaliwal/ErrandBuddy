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
