from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from services.api import api

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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

    def do_register(self, instance):
        username = self.username.text.strip()
        email = self.email.text.strip()
        password = self.password.text.strip()
        if not email or not password:
            print("Missing fields")
            return
        resp = api.register(email=email, password=password, username=username)
        if resp.status_code in (200, 201):
            print("Registered:", resp.json())
            self.manager.current = "login"
        else:
            print("Register failed:", resp.text)
