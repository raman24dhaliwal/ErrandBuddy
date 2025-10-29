from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
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
        # Logo (centered)
        logo = Image(source="frontend/assets/logo.jpeg", size_hint=(None, None), size=(200, 120))
        logo_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=130)
        logo_box.add_widget(logo)
        card.add_widget(logo_box)
        # Title/tagline (centered)
        title = Label(text="ERRANDBUDDY", font_size=18, color=(0.1,0.2,0.4,1), size_hint=(1,None), height=22, halign='center', valign='middle')
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        card.add_widget(title)
        
        # Inputs with rounded borders
        self.email_box = RoundedInput(hint="EMAIL ADDRESS")
        self.password_box = RoundedInput(hint="PASSWORD", password=True)
        # Tab focus order: email -> password -> login button
        try:
            self.email_box.input.write_tab = False
            self.password_box.input.write_tab = False
        except Exception:
            pass
        email_box_wrap = AnchorLayout(anchor_x='center', size_hint=(1, None), height=50)
        email_box_wrap.add_widget(self.email_box)
        pass_box_wrap = AnchorLayout(anchor_x='center', size_hint=(1, None), height=50)
        pass_box_wrap.add_widget(self.password_box)
        card.add_widget(email_box_wrap)
        card.add_widget(pass_box_wrap)

        # Buttons styled to match figma
        login_btn = RoundedButton(text="Log in", size_hint=(None, None), size=(220, 48), bg=(0.18, 0.15, 0.6, 1))
        login_btn.bind(on_press=self.login)
        signup_btn = OutlinedButton(text="\U0001F464  SIGN UP", size_hint=(None, None), size=(220, 44))
        signup_btn.bind(on_press=self.go_register)
        login_wrap = AnchorLayout(anchor_x='center', size_hint=(1, None), height=52)
        login_wrap.add_widget(login_btn)
        signup_wrap = AnchorLayout(anchor_x='center', size_hint=(1, None), height=48)
        signup_wrap.add_widget(signup_btn)
        card.add_widget(login_wrap)
        card.add_widget(signup_wrap)

        # Ensure focus traversal works using FocusBehavior
        try:
            self.email_box.input.focus_next = self.password_box.input
            self.password_box.input.focus_previous = self.email_box.input
            # Pressing Enter in password triggers login
            self.password_box.input.bind(on_text_validate=lambda *_: self.login(None))
        except Exception:
            pass
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
            self._alert("Please enter Email & Password.")
            return
        try:
            resp = api.login(email, password)
        except Exception:
            self._alert("Network error. Please try again.")
            return
        try:
            status = resp.status_code
        except Exception:
            status = 0
        if status == 200:
            print("Login success")
            try:
                t = self.manager.get_screen('tasks')
                if t:
                    t.show_home()
            except Exception:
                pass
            self.manager.current = "tasks"
            return
        # Graceful messaging for common cases
        if status == 401:
            self._alert("Wrong email or password. Please try again.")
            return
        if status == 403:
            self._alert("Email not verified. Please check your inbox for the OTP.")
            return
        # Fallback: show server message or generic
        try:
            data = resp.json(); msg = data.get("msg") or resp.text
        except Exception:
            msg = getattr(resp, 'text', 'Login failed')
        self._alert(f"Login failed: {msg}")

    def go_register(self, instance):
        self.manager.current = "register"

    def _alert(self, message: str):
        content = BoxLayout(orientation="vertical", padding=12, spacing=10)
        content.add_widget(Label(text=message, color=(0,0,0,1), size_hint=(1, None), halign='center', valign='middle'))
        btn = Button(text="OK", size_hint=(1, None), height=40)
        popup = Popup(title="Notice", content=content, size_hint=(None, None), size=(320, 200), auto_dismiss=False)
        btn.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(btn)
        popup.open()
