from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from services.api import api

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.username = TextInput(hint_text="Username", multiline=False)
        self.email = TextInput(hint_text="Email", multiline=False)
        self.password = TextInput(hint_text="Password", password=True, multiline=False)
        register_btn = Button(text="Register", size_hint=(1, None), height=50)
        register_btn.bind(on_press=self.do_register)
        back_btn = Button(text="Back to Login", size_hint=(1, None), height=40)
        back_btn.bind(on_press=lambda *a: setattr(self.manager, "current", "login"))
        layout.add_widget(self.username)
        layout.add_widget(self.email)
        layout.add_widget(self.password)
        layout.add_widget(register_btn)
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def do_register(self, instance):
        username = self.username.text.strip()
        email = self.email.text.strip()
        password = self.password.text.strip()
        if not email or not password:
            self._alert("Please enter email and password.")
            return
        # Enforce KPU student domain on the client side too
        if not email.lower().endswith("@student.kpu.ca"):
            self._alert("Please use your KPU student email (@student.kpu.ca).")
            return
        resp = api.register(email=email, password=password, username=username)
        if resp.status_code in (200, 201):
            print("Registered:", resp.json())
            self.manager.current = "login"
        else:
            try:
                data = resp.json()
                msg = data.get("msg") or resp.text
            except Exception:
                msg = resp.text
            self._alert(f"Registration failed: {msg}")

    def _alert(self, message: str):
        content = BoxLayout(orientation="vertical", padding=12, spacing=10)
        content.add_widget(Label(text=message, color=(0,0,0,1), size_hint=(1, None), halign='center', valign='middle'))
        btn = Button(text="OK", size_hint=(1, None), height=40)
        popup = Popup(title="Notice", content=content, size_hint=(None, None), size=(320, 200), auto_dismiss=False)
        btn.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(btn)
        popup.open()
