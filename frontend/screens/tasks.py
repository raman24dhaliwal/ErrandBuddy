from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from components.task_card import TaskCard
from services.api import api

DARK_BLUE = (0.10, 0.20, 0.55, 1)

class TaskScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background for the screen
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # root container; views are swapped in/out
        self.root_layout = BoxLayout(orientation="vertical", padding=20, spacing=8)
        self.add_widget(self.root_layout)

        # caches for form inputs
        self.title_input = None
        self.desc_input = None
        self.reward_input = None
        self.deadline_input = None
        self.location_input = None

    def on_enter(self, *args):
        self.show_home()

    def load_tasks(self):
        # Build list view with header + scroll
        self.root_layout.clear_widgets()
        header = BoxLayout(size_hint=(1, None), height=50, spacing=8)
        header.add_widget(Label(text="My Tasks", font_size=20, color=DARK_BLUE))
        back_btn = Button(text="Back", size_hint=(None, None), size=(80, 36))
        back_btn.bind(on_press=lambda *a: self.show_home())
        header.add_widget(back_btn)
        self.root_layout.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation="vertical", spacing=6, size_hint=(1, None))
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        self.root_layout.add_widget(scroll)
        if not api.token:
            self.content.add_widget(Label(text="Please log in to view your tasks.", color=DARK_BLUE))
            return
        resp = api.list_my_tasks()
        if resp.status_code == 200:
            tasks = resp.json()
            if not tasks:
                self.content.add_widget(Label(text="No tasks yet.", color=DARK_BLUE))
            for t in tasks:
                can_delete = bool(api.user) and t.get("user_id") == api.user.get("id")
                card = TaskCard(task=t, on_view=self.view_task, on_delete=self.delete_task, can_delete=can_delete)
                self.content.add_widget(card)
        else:
            self.content.add_widget(Label(text="Failed to load tasks.", color=DARK_BLUE))

    def open_add_task(self, instance):
        self.show_form()

    def create_task_from_form(self, instance):
        title = (self.title_input.input.text if self.title_input else "").strip()
        desc = (self.desc_input.input.text if self.desc_input else "").strip()
        reward = (self.reward_input.input.text if self.reward_input else "").strip()
        deadline = (self.deadline_input.input.text if self.deadline_input else "").strip()
        location = (self.location_input.input.text if self.location_input else "").strip()
        if not title:
            print("Please enter a task title.")
            return
        if not api.token:
            print("Please log in to create tasks.")
            return
        extra = []
        if reward:
            extra.append(f"Reward: {reward}")
        if deadline:
            extra.append(f"Deadline: {deadline}")
        if location:
            extra.append(f"Location: {location}")
        if extra:
            desc = (desc + "\n" if desc else "") + " | ".join(extra)
        resp = api.create_task(title, desc)
        if resp.status_code in (200, 201):
            print("Task created")
            self.show_home()
        else:
            print("Failed to create task:", getattr(resp, 'text', resp))

    def view_task(self, task):
        # Show task details (title + description) in a popup
        box = BoxLayout(orientation="vertical", padding=10, spacing=8)
        title = Label(text=f"[b]{task.get('title','')}[/b]", markup=True, size_hint=(1, None), height=28, color=DARK_BLUE)
        desc = TextInput(text=task.get("description", ""), readonly=True, size_hint=(1, 1))
        close = Button(text="Close", size_hint=(1, None), height=44)
        popup = Popup(title="Task Details", content=box, size_hint=(None, None), size=(360, 320), auto_dismiss=False)
        close.bind(on_press=lambda *a: popup.dismiss())
        box.add_widget(title)
        box.add_widget(desc)
        box.add_widget(close)
        popup.open()

    def delete_task(self, task):
        if not api.token:
            print("Please log in to delete tasks.")
            return
        resp = api.delete_task(task.get("id"))
        if resp.status_code == 200:
            print("Task deleted")
            self.load_tasks()
        else:
            print("Delete failed:", getattr(resp, 'text', resp))

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def sign_out(self, instance):
        api.logout()
        # clear current list and go back to login
        self.root_layout.clear_widgets()
        if self.manager:
            self.manager.current = "login"

    # --- new views matching provided screenshots ---
    def show_home(self):
        self.root_layout.clear_widgets()
        container = AnchorLayout(anchor_x='center', anchor_y='center')
        col = BoxLayout(orientation='vertical', spacing=18, size_hint=(None, None), size=(300, 420))
        logo = Image(source='frontend/assets/logo.jpeg', size_hint=(None, None), size=(180, 100))
        icon = Label(text='\U0001F4DD', font_size=72, color=DARK_BLUE, size_hint=(1, None), height=100)
        post_btn = Button(text='Post a Task', size_hint=(None, None), size=(240, 44), background_normal='', background_color=(0.7, 0.7, 0.7, 1), color=(0,0,0,1))
        post_btn.bind(on_press=lambda *a: self.show_form())
        view_btn = Button(text='View My Tasks', size_hint=(None, None), size=(240, 40))
        view_btn.bind(on_press=lambda *a: self.load_tasks())
        col.add_widget(logo)
        col.add_widget(icon)
        col.add_widget(post_btn)
        col.add_widget(view_btn)
        container.add_widget(col)
        self.root_layout.add_widget(container)

    def show_form(self):
        self.root_layout.clear_widgets()
        wrapper = BoxLayout(orientation='vertical', spacing=12, padding=[20, 20, 20, 20])
        header = Label(text='Post a Task', font_size=22, color=(0,0,0,1), size_hint=(1, None), height=36)
        # rounded inputs
        self.title_input = RoundedInput(hint='Task Title')
        self.desc_input = RoundedInput(hint='Description', multiline=True, height=90)
        self.reward_input = RoundedInput(hint='Reward Points (Optional)')
        self.deadline_input = RoundedInput(hint='Deadline')
        self.location_input = RoundedInput(hint='Location (Optional)')
        submit = Button(text='SUBMIT', size_hint=(None, None), size=(220, 48), background_normal='', background_color=(0.0, 0.45, 1.0, 1), color=(1,1,1,1))
        submit.bind(on_press=self.create_task_from_form)
        back = Button(text='Back', size_hint=(None, None), size=(120, 40))
        back.bind(on_press=lambda *a: self.show_home())
        wrapper.add_widget(header)
        wrapper.add_widget(self.title_input)
        wrapper.add_widget(self.desc_input)
        wrapper.add_widget(self.reward_input)
        wrapper.add_widget(self.deadline_input)
        wrapper.add_widget(self.location_input)
        wrapper.add_widget(submit)
        wrapper.add_widget(back)
        self.root_layout.add_widget(wrapper)


# Helper classes for rounded inputs and primary button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line

class RoundedInput(BoxLayout):
    def __init__(self, hint="", password=False, multiline=False, height=44, **kwargs):
        super().__init__(orientation="vertical", size_hint=(1, None), height=height, **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[14])
            Color(0.82, 0.82, 0.82, 1)
            self._line = Line(rounded_rectangle=(0, 0, 0, 0, 14), width=1)
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.input = TextInput(
            hint_text=hint,
            multiline=multiline,
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
        self._line.rounded_rectangle = (x, y, w, h, 14)
