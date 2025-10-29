# frontend/services/api.py
import requests

BASE_URL = "http://127.0.0.1:5000"

class ApiService:
    def __init__(self):
        self.base = BASE_URL
        self.token = None
        self.user = None

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, email, password, first_name="", last_name="", username=None):
        username = username or (f"{first_name} {last_name}".strip() or email.split("@")[0])
        payload = {"email": email, "password": password, "username": username,
                   "first_name": first_name, "last_name": last_name}
        return requests.post(f"{self.base}/auth/register", json=payload, headers=self._headers())

    def login(self, email, password):
        payload = {"email": email, "password": password}
        resp = requests.post(f"{self.base}/auth/login", json=payload, headers=self._headers())
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token")
            self.user = data.get("user")
        return resp

    def verify_otp(self, email, code):
        payload = {"email": email, "otp": str(code)}
        return requests.post(f"{self.base}/auth/verify-otp", json=payload, headers=self._headers())

    def resend_otp(self, email):
        payload = {"email": email}
        return requests.post(f"{self.base}/auth/resend-otp", json=payload, headers=self._headers())

    def logout(self):
        self.token = None
        self.user = None

    def list_tasks(self):
        return requests.get(f"{self.base}/tasks", headers=self._headers())

    def list_my_tasks(self):
        return requests.get(f"{self.base}/tasks/mine", headers=self._headers())

    def create_task(self, title, description=""):
        payload = {"title": title, "description": description}
        return requests.post(f"{self.base}/tasks", json=payload, headers=self._headers())

    def update_task(self, task_id, title=None, description=None, status=None):
        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        return requests.put(f"{self.base}/tasks/{task_id}", json=payload, headers=self._headers())

    def delete_task(self, task_id):
        return requests.delete(f"{self.base}/tasks/{task_id}", headers=self._headers())

    def accept_task(self, task_id):
        return requests.post(f"{self.base}/tasks/{task_id}/accept", headers=self._headers())

    def mark_task_done(self, task_id):
        return requests.post(f"{self.base}/tasks/{task_id}/done", headers=self._headers())

    def send_message(self, receiver_id, content):
        payload = {"receiver_id": receiver_id, "content": content}
        return requests.post(f"{self.base}/chat/send", json=payload, headers=self._headers())

    # Task-specific chat
    def list_task_messages(self, task_id):
        return requests.get(f"{self.base}/chat/task/{task_id}", headers=self._headers())

    def send_task_message(self, task_id, content):
        payload = {"content": content}
        return requests.post(f"{self.base}/chat/task/{task_id}/send", json=payload, headers=self._headers())

    def get_user(self, user_id):
        return requests.get(f"{self.base}/users/{user_id}", headers=self._headers())

    def list_rides(self):
        return requests.get(f"{self.base}/rides", headers=self._headers())

    def create_ride(self, origin, destination, time):
        payload = {"origin": origin, "destination": destination, "time": time}
        return requests.post(f"{self.base}/rides", json=payload, headers=self._headers())

    # Study sessions
    def list_study_sessions(self, q=None, campus=None):
        params = {}
        if q:
            params["q"] = q
        if campus:
            params["campus"] = campus
        return requests.get(f"{self.base}/study", headers=self._headers(), params=params or None)

    def create_study_session(self, course, available=True, campus="Surrey", teacher=None, description=None):
        payload = {"course": course, "available": bool(available), "campus": campus}
        if teacher is not None:
            payload["teacher"] = teacher
        if description is not None:
            payload["description"] = description
        return requests.post(f"{self.base}/study", json=payload, headers=self._headers())

    def update_study_session(self, session_id, course=None, available=None, campus=None, teacher=None, description=None):
        payload = {}
        if course is not None:
            payload["course"] = course
        if available is not None:
            payload["available"] = bool(available)
        if campus is not None:
            payload["campus"] = campus
        if teacher is not None:
            payload["teacher"] = teacher
        if description is not None:
            payload["description"] = description
        return requests.put(f"{self.base}/study/{session_id}", json=payload, headers=self._headers())

    def delete_study_session(self, session_id):
        return requests.delete(f"{self.base}/study/{session_id}", headers=self._headers())

    def connect_study_session(self, session_id):
        return requests.post(f"{self.base}/study/{session_id}/connect", headers=self._headers())

    # Direct chat
    def list_conversation(self, other_user_id):
        return requests.get(f"{self.base}/chat/messages/{other_user_id}", headers=self._headers())

    def list_chat_overview(self):
        return requests.get(f"{self.base}/chat/overview", headers=self._headers())

api = ApiService()
