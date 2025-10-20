# simple reusable form helpers (Kivy widgets)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class LabeledInput(BoxLayout):
    def __init__(self, label_text="", hint_text="", password=False, **kwargs):
        super().__init__(orientation="vertical", spacing=4, size_hint=(None, None), **kwargs)
        self.label = Label(text=label_text, size_hint=(None, None), size=(280, 20))
        self.input = TextInput(hint_text=hint_text, password=password, size_hint=(None, None), size=(280, 40), multiline=False,
                               background_normal="", background_color=(1,1,1,1), foreground_color=(0,0,0,1))
        self.add_widget(self.label)
        self.add_widget(self.input)

    def get(self):
        return self.input.text.strip()
