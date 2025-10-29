from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from services.api import api
from components.bottom_nav import BottomNav

class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=8)
        # Header row with centered title (no back)
        header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=44, spacing=8)
        title = Label(text="Profile", size_hint=(1, 1), halign='center', valign='middle')
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        header.add_widget(title)
        self.layout.add_widget(header)
        self.first_name = TextInput(hint_text="First Name", size_hint=(1, None), height=40)
        self.last_name = TextInput(hint_text="Last Name", size_hint=(1, None), height=40)
        self.bio = TextInput(hint_text="Bio", size_hint=(1, None), height=80)
        save = Button(text="Save", size_hint=(1, None), height=48)
        save.bind(on_press=self.save_profile)
        # Footer actions: Sign Out
        actions = BoxLayout(orientation="horizontal", size_hint=(1, None), height=44, spacing=8)
        signout = Button(text="Sign Out", size_hint=(None, None), size=(120, 40))
        signout.bind(on_press=self.sign_out)
        actions.add_widget(signout)
        self.layout.add_widget(self.first_name)
        self.layout.add_widget(self.last_name)
        self.layout.add_widget(self.bio)
        self.layout.add_widget(save)
        self.layout.add_widget(actions)
        # Bottom navigation bar
        self._add_bottom_nav()
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def on_enter(self, *args):
        if api.user:
            self.first_name.text = api.user.get("first_name", "")
            self.last_name.text = api.user.get("last_name", "")
            self.bio.text = api.user.get("bio", "")

    def save_profile(self, instance):
        from requests import put
        if not api.token:
            print("Login first")
            return
        payload = {
            "first_name": self.first_name.text.strip(),
            "last_name": self.last_name.text.strip(),
            "username": (self.first_name.text.strip() + " " + self.last_name.text.strip()).strip(),
            "bio": self.bio.text.strip(),
        }
        resp = put(f"{api.base}/users/me", json=payload, headers=api._headers())
        if resp.status_code == 200:
            print("Profile updated")
        else:
            print("Failed", resp.text)

    def sign_out(self, *_):
        api.logout()
        try:
            self.manager.current = 'login'
        except Exception:
            pass

    def _add_bottom_nav(self):
        def go_home():
            try:
                t = self.manager.get_screen('tasks')
                t.show_home()
            except Exception:
                pass
            self._go_screen('tasks', 'right')
        def go_tasks():
            try:
                t = self.manager.get_screen('tasks')
                t.load_tasks()
            except Exception:
                pass
            self._go_screen('tasks', 'right')
        nav = BottomNav(
            on_home=go_home,
            on_chat=lambda: self._go_screen('chats', 'left'),
            on_tasks=go_tasks,
            on_study=lambda: self._go_screen('study', 'left'),
            on_commute=lambda: self._go_screen('commute', 'left'),
            on_profile=lambda: None,
            active="Profile",
        )
        self.layout.add_widget(nav)

    def _go_screen(self, name: str, direction: str = 'left'):
        try:
            from kivy.uix.screenmanager import SlideTransition
            if self.manager:
                self.manager.transition = SlideTransition(direction=direction, duration=0.18)
                self.manager.current = name
        except Exception:
            try:
                self.manager.current = name
            except Exception:
                pass
