# frontend/services/api.py
import requests

# base url of backend
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

    # AUTH
    def register(self, email, password, username=None):
        username = username or email.split("@")[0]
        payload = {"email": email, "password": password, "username": username}
        resp = requests.post(f"{self.base}/auth/register", json=payload, headers=self._headers())
        return resp

    def login(self, email, password):
        payload = {"email": email, "password": password}
        resp = requests.post(f"{self.base}/auth/login", json=payload, headers=self._headers())
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token")
            self.user = data.get("user")
        return resp

    # TASKS
    def list_tasks(self):
        resp = requests.get(f"{self.base}/tasks", headers=self._headers())
        return resp

    def create_task(self, title, description=""):
        payload = {"title": title, "description": description}
        resp = requests.post(f"{self.base}/tasks", json=payload, headers=self._headers())
        return resp

    def get_task(self, task_id):
        resp = requests.get(f"{self.base}/tasks/{task_id}", headers=self._headers())
        return resp

    # Add more methods for chat, rides, profile etc.
    # Example: def list_users(self): requests.get(f"{self.base}/users", headers=self._headers())
