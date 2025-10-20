from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class MessageBubble(BoxLayout):
    def __init__(self, message, mine=False, **kwargs):
        super().__init__(size_hint=(1, None), height=40, padding=6, **kwargs)
        bubble = Label(text=message.get("content"), halign="left" if not mine else "right")
        self.add_widget(bubble)
