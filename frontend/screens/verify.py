from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from services.api import api


class VerifyEmailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self._email = ""
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.info = Label(text="Enter the 6-digit OTP sent to your email", color=(0,0,0,1), size_hint=(1, None), height=40)
        self.email_label = Label(text="", color=(0,0,0,1), size_hint=(1, None), height=24)
        self.otp = TextInput(hint_text="OTP Code", multiline=False, size_hint=(1, None), height=48)
        verify_btn = Button(text="Verify", size_hint=(1, None), height=50)
        verify_btn.bind(on_press=self.verify)
        resend_btn = Button(text="Resend Code", size_hint=(1, None), height=44)
        resend_btn.bind(on_press=self.resend)
        back_btn = Button(text="Back to Login", size_hint=(1, None), height=40)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, "current", "login"))
        
        layout.add_widget(self.info)
        layout.add_widget(self.email_label)
        layout.add_widget(self.otp)
        layout.add_widget(verify_btn)
        layout.add_widget(resend_btn)
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def set_email(self, email: str):
        self._email = email or ""
        self.email_label.text = f"Email: {self._email}"

    def _alert(self, message: str, title: str = "Notice"):
        content = BoxLayout(orientation="vertical", padding=12, spacing=10)
        content.add_widget(Label(text=message, color=(0,0,0,1), size_hint=(1, None), halign='center', valign='middle'))
        btn = Button(text="OK", size_hint=(1, None), height=40)
        popup = Popup(title=title, content=content, size_hint=(None, None), size=(320, 200), auto_dismiss=False)
        btn.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(btn)
        popup.open()

    def verify(self, *_):
        code = self.otp.text.strip()
        if not self._email or not code:
            self._alert("Missing email or code")
            return
        resp = api.verify_otp(self._email, code)
        if resp.status_code == 200:
            self._alert("Email verified! You can now log in.")
            self.manager.current = "login"
        else:
            try:
                data = resp.json(); msg = data.get("msg") or resp.text
            except Exception:
                msg = resp.text
            self._alert(f"Verification failed: {msg}")

    def resend(self, *_):
        if not self._email:
            self._alert("Missing email")
            return
        resp = api.resend_otp(self._email)
        if resp.status_code == 200:
            self._alert("A new code has been sent.")
        else:
            try:
                data = resp.json(); msg = data.get("msg") or resp.text
            except Exception:
                msg = resp.text
            self._alert(f"Resend failed: {msg}")

