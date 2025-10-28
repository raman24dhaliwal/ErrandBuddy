from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from services.api import api

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.layout = BoxLayout(orientation="vertical", padding=8)
        self.messages_box = BoxLayout(orientation="vertical", spacing=6, size_hint=(1, 0.8))
        self.input_box = BoxLayout(size_hint=(1, 0.2))
        self.text = TextInput(hint_text="Message...", multiline=False)
        send = Button(text="Send", size_hint=(None, 0.2), width=100)
        send.bind(on_press=self.send_message)
        self.input_box.add_widget(self.text)
        self.input_box.add_widget(send)
        self.layout.add_widget(self.messages_box)
        self.layout.add_widget(self.input_box)
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def send_message(self, instance):
        # for demo, send to user id 1 (change as needed)
        if not api.user:
            print("Not logged in")
            return
        resp = api.send_message(receiver_id=1, content=self.text.text)
        if resp.status_code in (200, 201):
            print("Message sent")
            self.text.text = ""
        else:
            print("Send failed", resp.text)
