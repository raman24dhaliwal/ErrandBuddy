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

# Resolve absolute assets directory so images load regardless of CWD
_FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_DIR = os.path.join(_FRONTEND_DIR, 'assets')

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
        self.location_spinner = None
        # track currently open edit popup
        self._edit_popup = None

    def on_enter(self, *args):
        # Do not force a view on enter; navigation callbacks
        # explicitly choose Home or Tasks list as needed.
        pass

    def load_tasks(self):
        # Build list view with header + scroll
        self.root_layout.clear_widgets()
        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=56)

        title_row = BoxLayout(size_hint=(1, None), height=44, spacing=6)
        from kivy.uix.widget import Widget as _W
        # Left spacer balanced to two buttons on right
        title_row.add_widget(_W(size_hint=(None, None), size=(84, 32)))
        title = Label(text="[b]Tasks[/b]", markup=True, font_size=20, color=DARK_BLUE, halign='center', valign='middle')
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        title.size_hint = (1, 1)
        title_row.add_widget(title)
        # Right-side actions: + and Filter
        actions = BoxLayout(orientation='horizontal', size_hint=(None, None), height=32, width=84, spacing=6)
        add_btn = LightRoundedButton(text='+', size_hint=(None, None), size=(36, 32))
        add_btn.bind(on_press=self.open_add_task)
        filt = LightRoundedButton(text='Filter', size_hint=(None, None), size=(42, 32))
        filt.bind(on_press=lambda *_: self._open_filter_popup())
        actions.add_widget(add_btn)
        actions.add_widget(filt)
        title_row.add_widget(actions)
        header.add_widget(title_row)
        self.root_layout.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        # Match Study Buddy list layout: tight rows with top dividers
        self.content = BoxLayout(orientation="vertical", spacing=0, size_hint=(1, None), padding=[0, 0, 0, 8])
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
        # initialize filter if missing
        if not hasattr(self, '_filter'):
            self._filter = {"status": None, "location": None}
        # apply filters
        tasks = self._apply_task_filters(tasks)
        my_id = api.user.get("id") if api.user else None
        # Partition into mine and others
        mine = [t for t in tasks if my_id and t.get("user_id") == my_id]
        others = [t for t in tasks if not (my_id and t.get("user_id") == my_id)]

        # Sort others by status order: open -> assigned -> done
        def _rank_status(t: dict) -> int:
            s = (t.get('status') or 'open').lower()
            if s in ('open', ''):
                return 0
            if s == 'assigned':
                return 1
            if s == 'done':
                return 2
            return 3

        others_sorted = sorted(others, key=_rank_status)

        ordered = (mine or []) + others_sorted
        if not ordered:
            self._add_hint("No tasks yet.")
        else:
            for t in ordered:
                rgba = self._dot_color_for_task(t)
                self._add_task_row(t, mine=bool(my_id and t.get('user_id') == my_id), dot_rgba=rgba)

    def open_add_task(self, instance):
        self.show_form()

    def create_task_from_form(self, instance):
        title = (self.title_input.input.text if self.title_input else "").strip()
        desc = (self.desc_input.input.text if self.desc_input else "").strip()
        reward = (self.reward_input.input.text if self.reward_input else "").strip()
        deadline = (self.deadline_input.input.text if self.deadline_input else "").strip()
        # Location from optional spinner
        try:
            location = (self.location_spinner.text or '').strip()
            if location.lower().startswith('select '):
                location = ''
        except Exception:
            location = ''
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
        # Owner modifications consolidated under single Edit popup
        if is_owner:
            edit = LightRoundedButton(text="Edit")
            edit.bind(on_press=lambda *_: self._open_task_edit_popup(task))
            btns.add_widget(edit)
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

    def _open_task_edit_popup(self, task: dict):
        from kivy.uix.togglebutton import ToggleButton
        box = BoxLayout(orientation='vertical', padding=12, spacing=10)
        title = Label(text='Edit Task', color=(0,0,0,1), size_hint=(1, None), height=24)
        box.add_widget(title)
        # status toggles
        sel_row = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=36)
        cur = (task.get('status') or 'open').lower()
        t_open = ToggleButton(text='Open', group='status', state='down' if cur in ('open','') else 'normal')
        t_done = ToggleButton(text='Done', group='status', state='down' if cur == 'done' else 'normal')
        sel_row.add_widget(t_open); sel_row.add_widget(t_done)
        box.add_widget(sel_row)
        # actions
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=40)
        save = LightRoundedButton(text='Save')
        delete = LightRoundedButton(text='Delete')
        cancel = LightRoundedButton(text='Cancel')
        actions.add_widget(save); actions.add_widget(delete); actions.add_widget(cancel)
        box.add_widget(actions)
        popup = Popup(title='Edit Task', content=box, size_hint=(None, None), size=(320, 220), auto_dismiss=False)
        self._edit_popup = popup

        def do_save(*_):
            if not api.token:
                print('Login required')
                return
            new_status = 'done' if t_done.state == 'down' else 'open'
            r = api.update_task(task.get('id'), status=new_status)
            if getattr(r, 'status_code', 0) in (200, 201):
                popup.dismiss(); self.load_tasks()
            else:
                print('Update failed', getattr(r, 'text', r))
        def do_delete(*_):
            self.delete_task(task); popup.dismiss()
        def do_cancel(*_):
            popup.dismiss()
        save.bind(on_press=do_save)
        delete.bind(on_press=do_delete)
        cancel.bind(on_press=do_cancel)
        popup.open()

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
        logo_path = os.path.join(ASSETS_DIR, 'logo.jpeg')
        logo = Image(source=logo_path, size_hint=(None, None), size=(180, 100))
        logo_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=110)
        logo_box.add_widget(logo)

        # Icon centered (use asset if available, fallback to emoji)
        icon_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=110)
        icon_box.add_widget(self._task_icon_widget())

        # Buttons centered (match Study Buddy button style)
        post_btn = LightRoundedButton(text='Post a Task', size_hint=(None, None), size=(240, 44))
        post_btn.bind(on_press=lambda *a: self.show_form())
        post_box = AnchorLayout(anchor_x='center', size_hint=(1, None), height=48)
        post_box.add_widget(post_btn)

        view_btn = LightRoundedButton(text='View My Tasks', size_hint=(None, None), size=(240, 40))
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
        from kivy.uix.spinner import Spinner
        # Optional location via dropdown
        self.location_spinner = Spinner(
            text='Select Location (Optional)',
            values=('Surrey', 'Richmond', 'Langley'),
            size_hint=(1, None),
            height=40,
            color=DARK_BLUE,
        )
        submit = Button(text='SUBMIT', size_hint=(None, None), size=(220, 48), background_normal='', background_color=(0.0, 0.45, 1.0, 1), color=(1,1,1,1))
        submit.bind(on_press=self.create_task_from_form)
        wrapper.add_widget(header)
        wrapper.add_widget(self.title_input)
        wrapper.add_widget(self.desc_input)
        wrapper.add_widget(self.reward_input)
        wrapper.add_widget(self.deadline_input)
        wrapper.add_widget(self.location_spinner)
        wrapper.add_widget(submit)
        self.root_layout.add_widget(wrapper)
        # bottom navigation bar
        self._add_bottom_nav(active="Home")

        # Tab traversal across form inputs
        try:
            for w in (self.title_input, self.desc_input, self.reward_input, self.deadline_input):
                w.input.write_tab = False
            self.title_input.input.focus_next = self.desc_input.input
            self.desc_input.input.focus_previous = self.title_input.input
            self.desc_input.input.focus_next = self.reward_input.input
            self.reward_input.input.focus_previous = self.desc_input.input
            self.reward_input.input.focus_next = self.deadline_input.input
            self.deadline_input.input.focus_previous = self.reward_input.input
            # Spinner is not a TextInput; do not include in tab order
        except Exception:
            pass

    # --- helpers ---
    def _add_bottom_nav(self, active: str = ""):
        nav = BottomNav(
            on_home=lambda: self.show_home(),
            on_chat=lambda: self._go_screen('chats', 'left'),
            on_tasks=lambda: self.load_tasks(),
            on_study=lambda: self._go_screen('study', 'left'),
            on_commute=lambda: self._go_screen('commute', 'left'),
            on_profile=lambda: self._go_screen('profile', 'left'),
            active=active,
        )
        self.root_layout.add_widget(nav)

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

    def _dot_color_for_task(self, task: dict):
        """Return RGBA for the left dot based on task status.
        - Available (open/empty) -> green
        - In Progress (assigned) -> orange
        - Complete (done) -> black
        """
        s = (task.get('status') or 'open').lower()
        if s in ('open', ''):
            return (0.15, 0.55, 0.25, 1)  # green
        if s == 'assigned':
            return (0.90, 0.50, 0.00, 1)  # orange
        if s == 'done':
            return (0.00, 0.00, 0.00, 1)  # black
        return (0.60, 0.60, 0.60, 1)

    def _open_filter_popup(self):
        from kivy.uix.spinner import Spinner
        box = BoxLayout(orientation='vertical', padding=12, spacing=10)
        # Background styling
        try:
            with box.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            box.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass
        info = Label(text='Filter Tasks', color=DARK_BLUE, size_hint=(1, None), height=24)
        # Status options
        cur_status = (getattr(self, '_filter', {}) or {}).get('status') or 'Any'
        status_values = ('Any', 'Available', 'In Progress', 'Complete')
        status = Spinner(text=cur_status, values=status_values, size_hint=(1, None), height=40, color=DARK_BLUE)
        # Location options
        cur_loc = (getattr(self, '_filter', {}) or {}).get('location') or 'Any'
        loc_values = ('Any', 'Surrey', 'Langley', 'Richmond')
        location = Spinner(text=cur_loc, values=loc_values, size_hint=(1, None), height=40, color=DARK_BLUE)
        # Actions
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        apply_b = LightRoundedButton(text='Apply', size_hint=(1, 1))
        clear_b = LightRoundedButton(text='Clear', size_hint=(1, 1))
        cancel_b = LightRoundedButton(text='Cancel', size_hint=(1, 1))
        actions.add_widget(apply_b); actions.add_widget(clear_b); actions.add_widget(cancel_b)
        box.add_widget(info); box.add_widget(status); box.add_widget(location); box.add_widget(actions)
        popup = Popup(title='Filter', content=box, size_hint=(None, None), size=(340, 260), auto_dismiss=False, background_color=(0.90, 0.90, 0.94, 1))

        def do_apply(*_):
            self._filter = {"status": status.text.strip() or None, "location": location.text.strip() or None}
            popup.dismiss(); self.load_tasks()
        def do_clear(*_):
            self._filter = {"status": None, "location": None}
            popup.dismiss(); self.load_tasks()
        def do_cancel(*_):
            popup.dismiss()
        apply_b.bind(on_press=do_apply)
        clear_b.bind(on_press=do_clear)
        cancel_b.bind(on_press=do_cancel)
        popup.open()

    def _apply_task_filters(self, tasks: list) -> list:
        """Filter tasks by status and location (from description) based on self._filter.
        Status mapping: Available->open, In Progress->assigned, Complete->done.
        Location is matched case-insensitively as a substring of parsed location.
        """
        f = getattr(self, '_filter', {}) or {}
        status_sel = (f.get('status') or 'Any').strip()
        loc_sel = (f.get('location') or 'Any').strip()
        if status_sel == 'Any' and loc_sel == 'Any':
            return tasks
        def status_ok(t: dict) -> bool:
            if status_sel == 'Any':
                return True
            s = (t.get('status') or 'open').lower()
            if status_sel == 'Available':
                return s in ('open', '')
            if status_sel == 'In Progress':
                return s == 'assigned'
            if status_sel == 'Complete':
                return s == 'done'
            return True
        def location_ok(t: dict) -> bool:
            if loc_sel == 'Any':
                return True
            try:
                base, reward, deadline, location = self._parse_details(t.get('description') or '')
                if not location:
                    return False
                return loc_sel.lower() in location.lower()
            except Exception:
                return False
        return [t for t in tasks if status_ok(t) and location_ok(t)]

    def _task_icon_widget(self):
        """Return a centered image widget for the task placeholder icon.
        Tries several common filenames in `frontend/assets` before falling back to an emoji.
        """
        candidates = [
            os.path.join(ASSETS_DIR, name)
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

    def _add_task_row(self, task: dict, mine: bool = False, dot_rgba=(0.6, 0.6, 0.6, 1)):
        def _view_cb(*_):
            self.view_task_inline(task)
        def _edit_cb(*_):
            self._open_task_edit_popup(task)
        row = _TaskRow(task, view_cb=_view_cb, edit_cb=_edit_cb, dot_rgba=dot_rgba)
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
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Ellipse

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

class _ColorDot(Widget):
    def __init__(self, rgba=(0.6, 0.6, 0.6, 1), size_px=34, **kwargs):
        super().__init__(size_hint=(None, None), size=(size_px, size_px), **kwargs)
        with self.canvas:
            Color(*rgba)
            self._circle = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        if hasattr(self, "_circle"):
            self._circle.pos = self.pos
            self._circle.size = self.size

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

class _TaskRow(BoxLayout):
    def __init__(self, task: dict, view_cb=None, edit_cb=None, dot_rgba=(0.6, 0.6, 0.6, 1), **kwargs):
        super().__init__(orientation='horizontal', size_hint=(1, None), height=64, padding=[12, 8, 12, 8], spacing=10, **kwargs)
        # background and top divider like Study Buddy
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(0.90, 0.90, 0.92, 1)
            self._line = Line(points=[])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.task = task or {}
        self.view_cb = view_cb or (lambda *_: None)
        self.edit_cb = edit_cb or (lambda *_: None)

        # Left dot (centered vertically using an AnchorLayout)
        dot_size = 30
        dot_wrap = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(None, 1), width=dot_size)
        dot_wrap.add_widget(_ColorDot(dot_rgba, size_px=dot_size))
        self.add_widget(dot_wrap)

        # Middle: title + status
        mid = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=2)
        title = (self.task.get('title') or '').strip() or 'Untitled'
        mid.add_widget(Label(text=f"[b]{title}[/b]", markup=True, color=DARK_BLUE, size_hint=(1, None), height=22))
        # status label
        status = (self.task.get('status') or 'open').lower()
        if status in ('open', ''):
            sub_text, sub_color = 'Available', (0.0, 0.5, 0.0, 1)
        elif status == 'assigned':
            sub_text, sub_color = 'In-Progress', (0.9, 0.5, 0.0, 1)
        elif status == 'done':
            sub_text, sub_color = 'Complete', (0.2, 0.2, 0.2, 1)
        else:
            sub_text, sub_color = status.title(), (0, 0, 0, 1)
        mid.add_widget(Label(text=sub_text, color=sub_color, size_hint=(1, None), height=20))
        self.add_widget(mid)

        # Right: View (+ Edit if owner)
        right = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=180, spacing=8)
        view_btn = LightRoundedButton(text='View', size_hint=(None, None), size=(80, 36))
        view_btn.bind(on_press=self.view_cb)
        right.add_widget(view_btn)
        # owner can edit
        try:
            from services.api import api as _api
            can_edit = bool(_api.user) and self.task.get('user_id') == (_api.user or {}).get('id')
        except Exception:
            can_edit = False
        if can_edit:
            edit_btn = LightRoundedButton(text='Edit', size_hint=(None, None), size=(80, 36))
            edit_btn.bind(on_press=self.edit_cb)
            right.add_widget(edit_btn)
        self.add_widget(right)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size
        # top divider
        x, y = self.pos
        w, h = self.size
        self._line.points = [x, y + h, x + w, y + h]
