import os
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
from components.bottom_nav import BottomNav
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
        header.add_widget(Label(text="Tasks", font_size=20, color=DARK_BLUE))
        back_btn = LightRoundedButton(text="Back", size_hint=(None, None), size=(80, 36))
        back_btn.bind(on_press=lambda *a: self.show_home())
        header.add_widget(back_btn)
        self.root_layout.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation="vertical", spacing=8, size_hint=(1, None), padding=[10, 10, 10, 10])
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        self.root_layout.add_widget(scroll)
        # bottom navigation bar
        self._add_bottom_nav(active="Tasks")

        # fetch all tasks; if not logged in, still show
        resp = api.list_tasks()
        if resp.status_code != 200:
            self.content.add_widget(Label(text="Failed to load tasks.", color=DARK_BLUE))
            return

        tasks = resp.json() or []
        my_id = api.user.get("id") if api.user else None
        mine = [t for t in tasks if my_id and t.get("user_id") == my_id]
        others = [t for t in tasks if not (my_id and t.get("user_id") == my_id)]

        # My tasks first (any status)
        self._add_section_header("My Tasks")
        if not mine:
            self._add_hint("You have not posted any tasks yet.")
        else:
            for t in mine:
                self._add_task_row(t, mine=True)

        # Then group other users' tasks by status
        available = [t for t in others if (t.get('status') or 'open') in ('open', '')]
        in_progress = [t for t in others if (t.get('status') or '').lower() == 'assigned']
        complete = [t for t in others if (t.get('status') or '').lower() == 'done']

        self._add_section_header("Available Tasks")
        if not available:
            self._add_hint("No available tasks.")
        else:
            for t in available:
                self._add_task_row(t, mine=False)

        self._add_section_header("In Progress")
        if not in_progress:
            self._add_hint("No tasks in progress.")
        else:
            for t in in_progress:
                self._add_task_row(t, mine=False)

        self._add_section_header("Complete")
        if not complete:
            self._add_hint("No completed tasks.")
        else:
            for t in complete:
                self._add_task_row(t, mine=False)

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
        # Backward-compat: delegate to inline view
        self.view_task_inline(task)

    def view_task_inline(self, task):
        # Replace content with a detail panel and Accept/Close
        self.root_layout.clear_widgets()
        header = BoxLayout(size_hint=(1, None), height=50, spacing=8)
        back2 = LightRoundedButton(text="< Back", size_hint=(None, None), size=(80, 36))
        back2.bind(on_press=lambda *_: self.load_tasks())
        header.add_widget(back2)
        header.add_widget(Label(text="Task Details", font_size=20, color=DARK_BLUE))
        self.root_layout.add_widget(header)

        body = BoxLayout(orientation="vertical", spacing=10, padding=[16, 10, 16, 10])
        title = Label(text=f"[b]{task.get('title','')}[/b]", markup=True, size_hint=(1, None), height=28, color=DARK_BLUE)
        base_desc, reward, deadline, location = self._parse_details(task.get("description", ""))
        desc = Label(text=base_desc or "(No description)", size_hint=(1, None), height=60, color=(0,0,0,1))
        # chips stacked vertically (one per line)
        chips = BoxLayout(orientation='vertical', spacing=6, size_hint=(1, None))
        chips.bind(minimum_height=chips.setter('height'))
        def add_chip(text):
            row = AnchorLayout(anchor_x='left', size_hint=(1, None), height=32)
            row.add_widget(Chip(text))
            chips.add_widget(row)
        if reward:
            add_chip(f"Reward: {reward}")
        if deadline:
            add_chip(f"Deadline: {deadline}")
        if location:
            add_chip(f"Location: {location}")
        body.add_widget(title)
        body.add_widget(desc)
        if len(chips.children) > 0:
            body.add_widget(chips)

        btns = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        is_owner = bool(api.user) and task.get('user_id') == (api.user or {}).get('id')
        # Accept button only if not owner and status open
        if not is_owner and (task.get('status') in (None, '', 'open')):
            accept = LightRoundedButton(text="Accept Task")
            accept.bind(on_press=lambda *_: self.accept_task(task))
            btns.add_widget(accept)
        # Mark done for owner
        if is_owner and task.get('status') != 'done':
            done = LightRoundedButton(text="Mark Done")
            done.bind(on_press=lambda *_: self.mark_done(task))
            btns.add_widget(done)
        # Chat button when a task has an assignee and current user is owner or assignee
        try:
            uid = (api.user or {}).get('id')
            if task.get('assignee_id') and uid in (task.get('assignee_id'), task.get('user_id')):
                chat_btn = LightRoundedButton(text="Chat")
                def _open_chat(*_):
                    try:
                        chat = self.manager.get_screen('chat')
                        if chat:
                            chat.open_for_task(task)
                            self.manager.current = 'chat'
                    except Exception:
                        pass
                chat_btn.bind(on_press=_open_chat)
                btns.add_widget(chat_btn)
        except Exception:
            pass
        close = LightRoundedButton(text="Close")
        close.bind(on_press=lambda *_: self.load_tasks())
        btns.add_widget(close)
        body.add_widget(btns)
        self.root_layout.add_widget(body)
        # bottom navigation bar
        self._add_bottom_nav(active="Tasks")

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
        container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))
        col = BoxLayout(orientation='vertical', spacing=18, size_hint=(None, None), size=(300, 420))

        # Logo centered
        logo = Image(source='frontend/assets/logo.jpeg', size_hint=(None, None), size=(180, 100))
        logo_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=110)
        logo_box.add_widget(logo)

        # Icon centered (use asset if available, fallback to emoji)
        icon_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=110)
        icon_box.add_widget(self._task_icon_widget())

        # Buttons centered
        post_btn = Button(text='Post a Task', size_hint=(None, None), size=(240, 44), background_normal='', background_color=(0.7, 0.7, 0.7, 1), color=(0,0,0,1))
        post_btn.bind(on_press=lambda *a: self.show_form())
        post_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=48)
        post_box.add_widget(post_btn)

        view_btn = Button(text='View My Tasks', size_hint=(None, None), size=(240, 40))
        view_btn.bind(on_press=lambda *a: self.load_tasks())
        view_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=44)
        view_box.add_widget(view_btn)

        col.add_widget(logo_box)
        col.add_widget(icon_box)
        col.add_widget(post_box)
        col.add_widget(view_box)
        container.add_widget(col)
        self.root_layout.add_widget(container)
        # bottom navigation bar
        self._add_bottom_nav(active="Home")

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
        # bottom navigation bar
        self._add_bottom_nav(active="Home")

        # Tab traversal across form inputs
        try:
            for w in (self.title_input, self.desc_input, self.reward_input, self.deadline_input, self.location_input):
                w.input.write_tab = False
            self.title_input.input.focus_next = self.desc_input.input
            self.desc_input.input.focus_previous = self.title_input.input
            self.desc_input.input.focus_next = self.reward_input.input
            self.reward_input.input.focus_previous = self.desc_input.input
            self.reward_input.input.focus_next = self.deadline_input.input
            self.deadline_input.input.focus_previous = self.reward_input.input
            self.deadline_input.input.focus_next = self.location_input.input
            self.location_input.input.focus_previous = self.deadline_input.input
        except Exception:
            pass

    # --- helpers ---
    def _add_bottom_nav(self, active: str = ""):
        nav = BottomNav(
            on_home=lambda: self.show_home(),
            on_tasks=lambda: self.load_tasks(),
            # For testing: tapping Profile signs out and returns to login
            on_profile=lambda: self.sign_out(None),
            active=active,
        )
        self.root_layout.add_widget(nav)

    def _task_icon_widget(self):
        """Return a centered image widget for the task placeholder icon.
        Tries several common filenames in `frontend/assets` before falling back to an emoji.
        """
        candidates = [
            os.path.join('frontend', 'assets', name)
            for name in (
                'task_icon.png', 'task_icon.jpg', 'task_icon.jpeg',
                'task.png', 'task.jpg', 'task.jpeg'
            )
        ]
        try:
            for path in candidates:
                if os.path.exists(path):
                    return Image(source=path, size_hint=(None, None), size=(72, 72), allow_stretch=False)
        except Exception:
            pass
        # Fallback to a large emoji label
        icon = Label(text='\U0001F4DD', font_size=72, color=DARK_BLUE, size_hint=(None, None), size=(100, 100), halign='center', valign='middle')
        icon.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        return icon

    # --- list helpers ---
    def _add_section_header(self, text: str):
        bar = BoxLayout(size_hint=(1, None), height=24)
        bar.add_widget(Label(text=f"[b]{text}[/b]", markup=True, color=DARK_BLUE, size_hint=(1, 1)))
        self.content.add_widget(bar)

    def _add_hint(self, text: str):
        self.content.add_widget(Label(text=text, color=(0.3,0.3,0.3,1), size_hint=(1, None), height=24))

    def _add_task_row(self, task: dict, mine: bool = False):
        # right-align buttons with a small edge margin; no leading icon
        row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=64, padding=[14, 8, 14, 8], spacing=10)
        # two-line title/status
        mid = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=2)
        mid.add_widget(Label(text=f"[b]{task.get('title','') or 'Untitled'}[/b]", markup=True, size_hint=(1, None), height=22, color=DARK_BLUE))
        subtitle, sub_color = self._status_label(task)
        sub_lbl = Label(text=subtitle, size_hint=(1, None), height=22, color=sub_color)
        mid.add_widget(sub_lbl)
        row.add_widget(mid)
        # flexible spacer pushes the buttons to the far right
        from kivy.uix.widget import Widget
        row.add_widget(Widget(size_hint=(1, 1)))
        # view/delete buttons
        right = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=180, spacing=8)
        view_btn = LightRoundedButton(text='View', size_hint=(None, 1), width=80)
        view_btn.bind(on_press=lambda *_: self.view_task_inline(task))
        right.add_widget(view_btn)
        can_delete = bool(api.user) and task.get('user_id') == (api.user or {}).get('id')
        if can_delete:
            del_btn = LightRoundedButton(text='Delete', size_hint=(None, 1), width=80)
            del_btn.bind(on_press=lambda *_: self.delete_task(task))
            right.add_widget(del_btn)
        row.add_widget(right)
        self.content.add_widget(row)

    def _status_label(self, task: dict):
        status = (task.get('status') or 'open').lower()
        if status in ('open', ''):
            return 'Available', (0.0, 0.5, 0.0, 1)
        if status == 'assigned':
            return 'In-Progress', (0.9, 0.5, 0.0, 1)
        if status == 'done':
            return 'Complete', (0.2, 0.2, 0.2, 1)
        return status.title(), (0, 0, 0, 1)

    def _parse_details(self, description: str):
        if not description:
            return "", "", "", ""
        parts = [p.strip() for p in description.replace('\n', ' | ').split('|')]
        base_parts = []
        reward = deadline = location = ""
        for p in parts:
            low = p.lower()
            if low.startswith('reward:'):
                reward = p.split(':', 1)[1].strip()
            elif low.startswith('deadline:'):
                deadline = p.split(':', 1)[1].strip()
            elif low.startswith('location:'):
                location = p.split(':', 1)[1].strip()
            elif p:
                base_parts.append(p)
        base = '\n'.join(base_parts).strip()
        return base, reward, deadline, location

    def accept_task(self, task: dict):
        if not api.token:
            print("Please log in to accept tasks.")
            return
        resp = api.accept_task(task.get('id'))
        if getattr(resp, 'status_code', 500) == 200:
            print("Task accepted")
        else:
            try:
                data = resp.json(); msg = data.get('msg') or resp.text
            except Exception:
                msg = getattr(resp, 'text', str(resp))
            print("Accept failed:", msg)
        self.load_tasks()

    def mark_done(self, task: dict):
        if not api.token:
            print("Please log in to mark tasks done.")
            return
        resp = api.mark_task_done(task.get('id'))
        if getattr(resp, 'status_code', 500) == 200:
            print("Task marked done")
        else:
            try:
                data = resp.json(); msg = data.get('msg') or resp.text
            except Exception:
                msg = getattr(resp, 'text', str(resp))
            print("Mark done failed:", msg)
        self.load_tasks()


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

class Chip(BoxLayout):
    def __init__(self, text: str, bg=(0.92, 0.92, 0.96, 1), fg=(0.1, 0.2, 0.55, 1), **kwargs):
        super().__init__(orientation='horizontal', padding=[10, 6, 10, 6], spacing=4,
                         size_hint=(None, None), height=28, **kwargs)
        with self.canvas.before:
            Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.label = Label(text=text, color=fg, size_hint=(None, None))
        self.label.bind(texture_size=self._update_width)
        self.add_widget(self.label)
        # initialize sizes
        self._update_width()

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_width(self, *args):
        try:
            self.label.texture_update()
        except Exception:
            pass
        lw = self.label.texture_size[0] if self.label.texture_size else 0
        self.label.size = self.label.texture_size
        pad_left, _, pad_right, _ = self.padding
        self.width = lw + pad_left + pad_right

class LightRoundedButton(Button):
    def __init__(self, text="", radius=10, bg=(0.95, 0.95, 0.95, 1), fg=DARK_BLUE, **kwargs):
        super().__init__(text=text, background_normal="", background_color=(0, 0, 0, 0), color=fg, **kwargs)
        self._bg = bg
        self._radius = radius
        with self.canvas.before:
            Color(*self._bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
