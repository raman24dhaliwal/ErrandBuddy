from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from components.task_card import TaskCard
from services.api import api

class TaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = BoxLayout(orientation="vertical", padding=10, spacing=8)
        header = BoxLayout(size_hint=(1, None), height=50)
        header.add_widget(Label(text="Tasks", font_size=20))
        add_btn = Button(text="Add Task", size_hint=(None, None), size=(120, 40))
        add_btn.bind(on_press=self.open_add_task)
        header.add_widget(add_btn)
        self.root_layout.add_widget(header)
        self.content = BoxLayout(orientation="vertical", spacing=6)
        self.root_layout.add_widget(self.content)
        self.add_widget(self.root_layout)

    def on_enter(self, *args):
        self.load_tasks()

    def load_tasks(self):
        self.content.clear_widgets()
        resp = api.list_tasks()
        if resp.status_code == 200:
            tasks = resp.json()
            if not tasks:
                self.content.add_widget(Label(text="No tasks yet."))
            for t in tasks:
                card = TaskCard(task=t, on_view=self.view_task)
                self.content.add_widget(card)
        else:
            self.content.add_widget(Label(text="Failed to load tasks."))

    def open_add_task(self, instance):
        # For quick demo, create a simple task
        resp = api.create_task("Quick task from app", "Created via Kivy UI")
        if resp.status_code in (200, 201):
            print("Task created")
            self.load_tasks()
        else:
            print("Failed to create task", resp.text)

    def view_task(self, task):
        print("Task tapped:", task)
