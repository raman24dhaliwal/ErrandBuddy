from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from services.api import api

class CommuteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.layout = BoxLayout(orientation="vertical", padding=8)
        self.origin = TextInput(hint_text="Origin", size_hint=(1, None), height=40)
        self.destination = TextInput(hint_text="Destination", size_hint=(1, None), height=40)
        self.time = TextInput(hint_text="Time", size_hint=(1, None), height=40)
        btn = Button(text="Create Ride", size_hint=(1, None), height=48)
        btn.bind(on_press=self.create_ride)
        self.layout.add_widget(self.origin)
        self.layout.add_widget(self.destination)
        self.layout.add_widget(self.time)
        self.layout.add_widget(btn)
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
