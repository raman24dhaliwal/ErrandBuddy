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

    def register(self, email, password, username=None):
        username = username or email.split("@")[0]
        payload = {"email": email, "password": password, "username": username}
        return requests.post(f"{self.base}/auth/register", json=payload, headers=self._headers())

    def login(self, email, password):
        payload = {"email": email, "password": password}
        resp = requests.post(f"{self.base}/auth/login", json=payload, headers=self._headers())
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token")
            self.user = data.get("user")
        return resp

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

    def delete_task(self, task_id):
        return requests.delete(f"{self.base}/tasks/{task_id}", headers=self._headers())

    def send_message(self, receiver_id, content):
        payload = {"receiver_id": receiver_id, "content": content}
        return requests.post(f"{self.base}/chat/send", json=payload, headers=self._headers())

    def list_rides(self):
        return requests.get(f"{self.base}/rides", headers=self._headers())

    def create_ride(self, origin, destination, time):
        payload = {"origin": origin, "destination": destination, "time": time}
        return requests.post(f"{self.base}/rides", json=payload, headers=self._headers())

api = ApiService()
