from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class TaskCard(BoxLayout):
    def __init__(self, task, on_view=None, on_delete=None, can_delete=False, **kwargs):
        super().__init__(orientation="vertical", padding=8, spacing=6, size_hint=(1, None), height=110, **kwargs)
        self.task = task
        dark_blue = (0.10, 0.20, 0.55, 1)
        title = Label(text=task.get("title"), size_hint=(1, None), height=30, color=dark_blue)
        desc = Label(text=task.get("description", ""), size_hint=(1, None), height=40, color=dark_blue)
        btns = BoxLayout(size_hint=(1, None), height=40, spacing=8)
        view_btn = Button(text="View", size_hint=(0.5, 1))
        if on_view:
            view_btn.bind(on_press=lambda *a: on_view(task))
        btns.add_widget(view_btn)
        if can_delete and on_delete:
            del_btn = Button(text="Delete", size_hint=(0.5, 1))
            del_btn.bind(on_press=lambda *a: on_delete(task))
            btns.add_widget(del_btn)
        self.add_widget(title)
        self.add_widget(desc)
        self.add_widget(btns)
