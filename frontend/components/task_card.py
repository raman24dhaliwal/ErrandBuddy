from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class TaskCard(BoxLayout):
    def __init__(self, task, on_view=None, **kwargs):
        super().__init__(orientation="vertical", padding=8, spacing=6, size_hint=(1, None), height=100, **kwargs)
        self.task = task
        title = Label(text=task.get("title"), size_hint=(1, None), height=30)
        desc = Label(text=task.get("description", ""), size_hint=(1, None), height=30)
        btns = BoxLayout(size_hint=(1, None), height=40)
        view_btn = Button(text="View", size_hint=(0.5, 1))
        if on_view:
            view_btn.bind(on_press=lambda *a: on_view(task))
        btns.add_widget(view_btn)
        self.add_widget(title)
        self.add_widget(desc)
        self.add_widget(btns)
