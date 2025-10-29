from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from services.api import api
from components.bottom_nav import BottomNav

class CommuteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=8)
        # Header with back button
        header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=44, spacing=8)
        title = Label(text="Commute", size_hint=(1, 1), halign='center', valign='middle')
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        header.add_widget(title)
        self.layout.add_widget(header)
        self.origin = TextInput(hint_text="Origin", size_hint=(1, None), height=40)
        self.destination = TextInput(hint_text="Destination", size_hint=(1, None), height=40)
        self.time = TextInput(hint_text="Time", size_hint=(1, None), height=40)
        btn = Button(text="Create Ride", size_hint=(1, None), height=48)
        btn.bind(on_press=self.create_ride)
        self.layout.add_widget(self.origin)
        self.layout.add_widget(self.destination)
        self.layout.add_widget(self.time)
        self.layout.add_widget(btn)
        # Bottom navigation bar
        self._add_bottom_nav()
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def create_ride(self, instance):
        o = self.origin.text.strip(); d = self.destination.text.strip(); t = self.time.text.strip()
        if not (o and d and t):
            print("Missing fields")
            return
        resp = api.create_ride(o, d, t)
        if resp.status_code in (200, 201):
            print("Ride created")
        else:
            print("Ride failed", resp.text)

    # back button removed; use bottom nav for navigation

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
            on_commute=lambda: None,
            on_profile=lambda: self._go_screen('profile', 'left'),
            active="Commute",
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
