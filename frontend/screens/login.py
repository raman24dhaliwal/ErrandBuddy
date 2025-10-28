from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from services.api import api


class RoundedButton(Button):
    def __init__(self, bg=(0.07, 0.1, 0.5, 1), fg=(1, 1, 1, 1), radius=20, **kwargs):
        super().__init__(background_normal="", background_color=(0, 0, 0, 0), color=fg, **kwargs)
        self._bg = bg
        self._radius = radius
        with self.canvas.before:
            Color(*self._bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class OutlinedButton(Button):
    def __init__(self, stroke=(0.36, 0.25, 0.84, 1), fg=(0.36, 0.25, 0.84, 1), radius=20, **kwargs):
        super().__init__(background_normal="", background_color=(0, 0, 0, 0), color=fg, **kwargs)
        self._stroke = stroke
        self._radius = radius
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._fill = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        with self.canvas.after:
            Color(*self._stroke)
            self._outline = Line(rounded_rectangle=(0, 0, 0, 0, self._radius), width=1.5)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._fill.pos = self.pos
        self._fill.size = self.size
        x, y = self.pos
        w, h = self.size
        self._outline.rounded_rectangle = (x, y, w, h, self._radius)


class RoundedInput(BoxLayout):
    def __init__(self, hint="", password=False, **kwargs):
        super().__init__(orientation="vertical", size_hint=(None, None), size=(280, 44), **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[18])
            Color(0.8, 0.8, 0.8, 1)
            self._line = Line(rounded_rectangle=(0, 0, 0, 0, 18), width=1)
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.input = TextInput(
            hint_text=hint,
            multiline=False,
            password=password,
            background_normal="",
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0, 0, 1),
            padding=[12, 10, 12, 10],
            size_hint=(1, 1),
        )
        self.add_widget(self.input)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        x, y = self.pos
        w, h = self.size
        self._line.rounded_rectangle = (x, y, w, h, 18)


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background on this screen
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[0])
        self.bind(pos=self._update_bg, size=self._update_bg)

        # center card using AnchorLayout for consistent centering
        root = AnchorLayout(anchor_x='center', anchor_y='center')
        card = BoxLayout(
            orientation="vertical",
            spacing=14,
            size_hint=(None, None),
            size=(320, 560),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        # Logo
        logo = Image(source="frontend/assets/logo.jpeg", size_hint=(None, None), size=(200, 120))
        card.add_widget(logo)
        # Title/tagline (optional to mimic figma text)
        card.add_widget(Label(text="ERRANDBUDDY", font_size=18, color=(0.1,0.2,0.4,1), size_hint=(1,None), height=22))
        
        # Inputs with rounded borders
        self.email_box = RoundedInput(hint="EMAIL ADDRESS")
        self.password_box = RoundedInput(hint="PASSWORD", password=True)
        card.add_widget(self.email_box)
        card.add_widget(self.password_box)

        # Buttons styled to match figma
        login_btn = RoundedButton(text="Log in", size_hint=(None, None), size=(220, 48), bg=(0.18, 0.15, 0.6, 1))
        login_btn.bind(on_press=self.login)
        signup_btn = OutlinedButton(text="\U0001F464  SIGN UP", size_hint=(None, None), size=(220, 44))
        signup_btn.bind(on_press=self.go_register)
        card.add_widget(login_btn)
        card.add_widget(signup_btn)
        root.add_widget(card)
        self.add_widget(root)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def login(self, instance):
        email = self.email_box.input.text.strip() if self.email_box else ""
        password = self.password_box.input.text.strip() if self.password_box else ""
        if not email or not password:
            print("Please enter Email & Password.")
            return
        resp = api.login(email, password)
        if resp.status_code == 200:
            print("Login success")
            self.manager.current = "tasks"
        else:
            print("Login failed:", resp.text)

    def go_register(self, instance):
        self.manager.current = "register"
