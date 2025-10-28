from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from services.api import api

class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.layout = BoxLayout(orientation="vertical", padding=8)
        self.username = TextInput(hint_text="Username", size_hint=(1, None), height=40)
        self.bio = TextInput(hint_text="Bio", size_hint=(1, None), height=80)
        save = Button(text="Save", size_hint=(1, None), height=48)
        save.bind(on_press=self.save_profile)
        self.layout.add_widget(self.username)
        self.layout.add_widget(self.bio)
        self.layout.add_widget(save)
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def on_enter(self, *args):
        if api.user:
            self.username.text = api.user.get("username", "")
            self.bio.text = api.user.get("bio", "")

    def save_profile(self, instance):
        from requests import put
        if not api.token:
            print("Login first")
            return
        payload = {"username": self.username.text.strip(), "bio": self.bio.text.strip()}
        resp = put(f"{api.base}/users/me", json=payload, headers=api._headers())
        if resp.status_code == 200:
            print("Profile updated")
        else:
            print("Failed", resp.text)
