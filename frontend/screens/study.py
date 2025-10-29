from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Ellipse, Line

# Reuse shared styles from Task screen
try:
    from screens.tasks import LightRoundedButton, DARK_BLUE
except Exception:  # fallback colors if import fails during design time
    LightRoundedButton = Button
    DARK_BLUE = (0.10, 0.20, 0.55, 1)
from services.api import api


class _ColorDot(Widget):
    def __init__(self, rgba=(0.6, 0.6, 0.6, 1), size_px=36, **kwargs):
        super().__init__(size_hint=(None, None), size=(size_px, size_px), **kwargs)
        with self.canvas:
            Color(*rgba)
            self._circle = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        if hasattr(self, "_circle"):
            self._circle.pos = self.pos
            self._circle.size = self.size


class _StudyRow(BoxLayout):
    def __init__(self, session: dict, connect_cb=None, update_cb=None, delete_cb=None, view_cb=None, dot_rgba=(0.6, 0.6, 0.6, 1), **kwargs):
        super().__init__(orientation="horizontal", size_hint=(1, None), height=74, padding=[10, 8, 10, 8], spacing=10, **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(0.90, 0.90, 0.92, 1)
            self._line = Line(points=[])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.session = session or {}
        self.connect_cb = connect_cb or (lambda *_: None)
        self.update_cb = update_cb or (lambda *_: None)
        self.delete_cb = delete_cb or (lambda *_: None)
        self.view_cb = view_cb or (lambda *_: None)

        self.add_widget(_ColorDot(dot_rgba, size_px=34))

        # Center column
        col = BoxLayout(orientation="vertical")
        col.add_widget(Label(text="[b]Course[/b]", markup=True, color=DARK_BLUE, size_hint=(1, None), height=22))
        col.add_widget(Label(text=self.session.get('course') or '', color=(0, 0, 0, 1), size_hint=(1, None), height=20))
        available = bool(self.session.get('available'))
        # Show simple availability text only to avoid overlap
        status_text = "Available now" if available else "Not available"
        status_color = (0.15, 0.55, 0.25, 1) if available else (0.55, 0.15, 0.15, 1)
        col.add_widget(Label(text=status_text, color=status_color, size_hint=(1, None), height=18))
        self.add_widget(col)

        # Right side controls
        right = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(None, 1), width=150)
        owner_id = self.session.get('user_id')
        me = (api.user or {}).get('id')
        if me and owner_id == me:
            # Owner controls: single Edit button opens popup
            edit_btn = LightRoundedButton(text="Edit", size_hint=(None, None), size=(80, 36))
            edit_btn.bind(on_press=lambda *_: self.update_cb(self.session, None))
            right.add_widget(edit_btn)
        else:
            btn = LightRoundedButton(text="View", size_hint=(None, None), size=(100, 36))
            if not available:
                # still allow viewing even if not available
                pass
            btn.bind(on_press=lambda *_: self.view_cb(self.session))
            right.add_widget(btn)
        self.add_widget(right)

    def _connect(self, title, course):
        pass

    def _update_bg(self, *args):
        if hasattr(self, "_bg"):
            self._bg.pos = self.pos
            self._bg.size = self.size
        # top divider line to separate rows
        x, y = self.pos
        w, h = self.size
        self._line.points = [x, y + h, x + w, y + h]


class StudyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.root_layout = BoxLayout(orientation="vertical", padding=20, spacing=8)
        self.add_widget(self.root_layout)

        # Header with centered title and back/plus buttons
        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=56)

        title_row = BoxLayout(size_hint=(1, None), height=44, spacing=6)
        from kivy.uix.widget import Widget as _W
        # Left spacer balanced to two buttons on right
        title_row.add_widget(_W(size_hint=(None, None), size=(84, 32)))
        title_lbl = Label(text="[b]Study Buddy[/b]", markup=True, color=DARK_BLUE, halign='center', valign='middle')
        title_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        title_lbl.size_hint = (1, 1)
        title_row.add_widget(title_lbl)
        # Right-side buttons: + and Filter
        actions = BoxLayout(orientation='horizontal', size_hint=(None, None), height=32, width=84, spacing=6)
        plus = LightRoundedButton(text="+", size_hint=(None, None), size=(36, 32))
        plus.bind(on_press=lambda *_: self._open_create_popup())
        filt = LightRoundedButton(text="Filter", size_hint=(None, None), size=(42, 32))
        filt.bind(on_press=lambda *_: self._open_filter_popup())
        actions.add_widget(plus)
        actions.add_widget(filt)
        title_row.add_widget(actions)
        header.add_widget(title_row)
        self.root_layout.add_widget(header)

        # Scrollable list
        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_box = BoxLayout(orientation="vertical", size_hint=(1, None), spacing=0, padding=[0, 0, 0, 8])
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.root_layout.add_widget(self.scroll)

        # Bottom nav
        self._add_bottom_nav()

    def on_pre_enter(self, *args):
        # current filter
        if not hasattr(self, '_filter'):
            self._filter = {"q": None, "campus": None}
        self._populate_list()

    def _populate_list(self):
        self.list_box.clear_widgets()
        try:
            q = None; campus = None
            f = getattr(self, '_filter', {}) or {}
            q = (f.get('q') or '').strip() or None
            campus = (f.get('campus') or '').strip() or None
            if campus and campus.lower() == 'any':
                campus = None
            resp = api.list_study_sessions(q=q, campus=campus)
            if resp.status_code != 200:
                raise Exception(getattr(resp, 'text', resp))
            sessions = resp.json() or []
        except Exception as e:
            self.list_box.add_widget(Label(text=f"Failed to load sessions: {e}", color=DARK_BLUE))
            return
        # color cycle for dots
        colors = [
            (0.95, 0.35, 0.55, 1),
            (0.10, 0.20, 0.55, 1),
            (0.40, 0.85, 0.75, 1),
            (0.70, 0.40, 0.95, 1),
            (0.25, 0.70, 0.40, 1),
        ]
        for i, s in enumerate(sessions):
            rgba = colors[i % len(colors)]
            row = _StudyRow(
                s,
                connect_cb=self._connect_to_session,
                update_cb=self._update_session_status,
                delete_cb=self._delete_session,
                view_cb=self._open_view_session_popup,
                dot_rgba=rgba,
            )
            self.list_box.add_widget(row)

        if not sessions:
            self.list_box.add_widget(Label(text="No sessions match the filter.", color=DARK_BLUE, size_hint=(1, None), height=24))

    def _add_bottom_nav(self):
        try:
            from components.bottom_nav import BottomNav
        except Exception:
            return
        def go_home():
            try:
                t = self.manager.get_screen('tasks')
                t.show_home()
            except Exception:
                pass
            self._go_screen('tasks', 'right')
        def go_tasks():
            try:
                t = self.manager.get_screen('tasks')
                t.load_tasks()
            except Exception:
                pass
            self._go_screen('tasks', 'right')
        nav = BottomNav(
            on_home=go_home,
            on_chat=lambda: self._go_screen('chats', 'left'),
            on_tasks=go_tasks,
            on_study=lambda: None,
            on_commute=lambda: self._go_screen('commute', 'left'),
            on_profile=lambda: self._go_screen('profile', 'left'),
            active="Study Buddy",
        )
        self.root_layout.add_widget(nav)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

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

    # --- actions ---
    def _open_create_popup(self):
        box = BoxLayout(orientation='vertical', padding=12, spacing=10, size_hint=(1, 1))
        # Solid background for popup content (slightly darker gray)
        try:
            with box.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            box.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass

        info = Label(text='What class is the study session for?', color=DARK_BLUE, size_hint=(1, None), height=24)
        input_box = TextInput(hint_text='Course e.g., CPSC 1100', multiline=False, size_hint=(1, None), height=44)
        # Campus selector
        from kivy.uix.spinner import Spinner
        campus_label = Label(text='Campus', color=DARK_BLUE, size_hint=(1, None), height=20)
        campus_spinner = Spinner(text='Surrey', values=('Surrey','Langley','Richmond'), size_hint=(1, None), height=40, color=DARK_BLUE)
        # Teacher and Description
        teacher_label = Label(text='Teacher', color=DARK_BLUE, size_hint=(1, None), height=20)
        teacher_input = TextInput(hint_text='e.g., Dr. Smith', multiline=False, size_hint=(1, None), height=44)
        desc_label = Label(text='Description', color=DARK_BLUE, size_hint=(1, None), height=20)
        desc_input = TextInput(hint_text='Add any details…', multiline=True, size_hint=(1, None), height=80)
        row = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=40)
        btn_now = LightRoundedButton(text='Available Now', size_hint=(1, 1))
        btn_na = LightRoundedButton(text='Not Available', size_hint=(1, 1))
        row.add_widget(btn_now); row.add_widget(btn_na)
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        ok = LightRoundedButton(text='Post', size_hint=(1, 1))
        cancel = LightRoundedButton(text='Cancel', size_hint=(1, 1))
        actions.add_widget(ok); actions.add_widget(cancel)
        box.add_widget(info)
        box.add_widget(input_box)
        box.add_widget(campus_label)
        box.add_widget(campus_spinner)
        box.add_widget(teacher_label)
        box.add_widget(teacher_input)
        box.add_widget(desc_label)
        box.add_widget(desc_input)
        box.add_widget(row)
        box.add_widget(actions)
        # Dynamically size the popup relative to the window so content fits
        try:
            from kivy.core.window import Window
            pop_h = int(max(480, min(Window.height * 0.90, 720)))
        except Exception:
            pop_h = 560
        popup = Popup(
            title='New Study Session',
            content=box,
            size_hint=(None, None),
            size=(360, pop_h),
            auto_dismiss=False,
            background_color=(0.90, 0.90, 0.94, 1),  # darker gray than app background
        )

        state = {"available": True}

        def set_now(*_):
            state["available"] = True
        def set_na(*_):
            state["available"] = False
        btn_now.bind(on_press=set_now)
        btn_na.bind(on_press=set_na)

        def do_post(*_):
            course = input_box.text.strip()
            if not course:
                return
            campus = campus_spinner.text.strip() or 'Surrey'
            r = api.create_study_session(course, state["available"], campus, teacher_input.text.strip() or None, desc_input.text.strip() or None)
            if r.status_code in (200, 201):
                popup.dismiss()
                self._populate_list()
            else:
                print('Create failed', getattr(r, 'text', r))
        def do_cancel(*_):
            popup.dismiss()
        ok.bind(on_press=do_post)
        cancel.bind(on_press=do_cancel)
        popup.open()

    def _update_session_status(self, session: dict, available_bool: bool):
        # When available_bool is None, open edit popup; otherwise update availability directly
        if available_bool is None:
            self._open_edit_session_popup(session)
            return
        sid = session.get('id')
        if not sid:
            return
        r = api.update_study_session(sid, available=available_bool)
        if r.status_code == 200:
            self._populate_list()
        else:
            print('Update failed', getattr(r, 'text', r))

    def _open_edit_session_popup(self, session: dict):
        from kivy.uix.togglebutton import ToggleButton
        box = BoxLayout(orientation='vertical', padding=12, spacing=10)
        # Solid background matching create popup style
        try:
            with box.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            box.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass
        head = Label(text='Edit Study Session', color=DARK_BLUE, size_hint=(1, None), height=24)
        box.add_widget(head)
        sel = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=36)
        cur = bool(session.get('available'))
        t_av = ToggleButton(text='Available Now', group='avail', state='down' if cur else 'normal')
        t_na = ToggleButton(text='Not Available', group='avail', state='down' if not cur else 'normal')
        try:
            t_av.color = DARK_BLUE; t_na.color = DARK_BLUE
        except Exception:
            pass
        sel.add_widget(t_av); sel.add_widget(t_na)
        box.add_widget(sel)
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=40)
        save = LightRoundedButton(text='Save')
        delete = LightRoundedButton(text='Delete')
        cancel = LightRoundedButton(text='Cancel')
        actions.add_widget(save); actions.add_widget(delete); actions.add_widget(cancel)
        box.add_widget(actions)
        popup = Popup(
            title='Edit Session',
            content=box,
            size_hint=(None, None),
            size=(340, 280),
            auto_dismiss=False,
            background_color=(0.90, 0.90, 0.94, 1),
        )

        def do_save(*_):
            avail = True if t_av.state == 'down' else False
            r = api.update_study_session(session.get('id'), available=avail)
            if r.status_code == 200:
                popup.dismiss(); self._populate_list()
            else:
                print('Update failed', getattr(r, 'text', r))
        def do_delete(*_):
            self._delete_session(session); popup.dismiss()
        def do_cancel(*_):
            popup.dismiss()
        save.bind(on_press=do_save)
        delete.bind(on_press=do_delete)
        cancel.bind(on_press=do_cancel)
        popup.open()

    def _delete_session(self, session: dict):
        sid = session.get('id')
        if not sid:
            return
        r = api.delete_study_session(sid)
        if r.status_code == 200:
            self._populate_list()
        else:
            print('Delete failed', getattr(r, 'text', r))

    def _connect_to_session(self, session: dict):
        sid = session.get('id')
        owner_id = session.get('user_id')
        # Store a local title override so Chats list can render informative DM titles
        try:
            key = f"user:{owner_id}"
            from local_store import set_title_override
        except Exception:
            try:
                from frontend.local_store import set_title_override
            except Exception:
                set_title_override = None
        try:
            course = (session.get('course') or '').strip()
            if set_title_override and owner_id and course:
                set_title_override(key, f"Study Buddy Session ({course})")
        except Exception:
            pass
        # Call connect endpoint (optional, but keeps API semantics)
        r = api.connect_study_session(sid)
        if r.status_code not in (200, 201):
            # fallback: use owner_id from session list
            print('Connect fallback: ', getattr(r, 'text', r))
        try:
            data = r.json() if r.status_code in (200, 201) else {}
            owner_id = data.get('owner_id') or owner_id
        except Exception:
            pass
        if not (api.token and owner_id):
            print('Login required or missing owner')
            return
        # Open chat with owner
        try:
            chat = self.manager.get_screen('chat')
        except Exception:
            chat = None
        if chat:
            # For study buddy chats, set the header to the course only
            course = (session.get('course') or '').strip() or None
            chat.open_with_user(owner_id, display_name=course, prev_screen='study')
            try:
                from kivy.uix.screenmanager import SlideTransition
                if self.manager:
                    self.manager.transition = SlideTransition(direction='left', duration=0.18)
            except Exception:
                pass
            self.manager.current = 'chat'
        else:
            print('Chat screen not found')

    def _open_view_session_popup(self, session: dict):
        box = BoxLayout(orientation='vertical', padding=12, spacing=8)
        # Background styling
        try:
            with box.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            box.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass

        def line(label, value):
            row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=26, spacing=6)
            row.add_widget(Label(text=f"{label}", color=DARK_BLUE, size_hint=(None, 1), width=90))
            row.add_widget(Label(text=value or '', color=(0,0,0,1)))
            return row

        box.add_widget(Label(text='Study Session', color=DARK_BLUE, size_hint=(1, None), height=24))
        box.add_widget(line('Course:', session.get('course') or ''))
        box.add_widget(line('Campus:', session.get('campus') or ''))
        box.add_widget(line('Teacher:', session.get('teacher') or ''))
        # Description as multi-line block
        desc = (session.get('description') or '').strip()
        box.add_widget(Label(text='Description:', color=DARK_BLUE, size_hint=(1, None), height=20))
        from kivy.uix.scrollview import ScrollView
        sc = ScrollView(size_hint=(1, None), height=100)
        desc_lbl = Label(text=desc or '(No description)', color=(0,0,0,1), size_hint=(1, None))
        desc_lbl.bind(texture_size=lambda i, v: setattr(i, 'height', i.texture_size[1]))
        sc.add_widget(desc_lbl)
        box.add_widget(sc)

        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        connect = LightRoundedButton(text='Connect', size_hint=(1, 1))
        back = LightRoundedButton(text='Back', size_hint=(1, 1))
        actions.add_widget(connect); actions.add_widget(back)
        box.add_widget(actions)

        popup = Popup(title='Study Session', content=box, size_hint=(None, None), size=(360, 380), auto_dismiss=False, background_color=(0.90, 0.90, 0.94, 1))

        def do_connect(*_):
            popup.dismiss(); self._connect_to_session(session)
        def do_back(*_):
            popup.dismiss()
        connect.bind(on_press=do_connect)
        back.bind(on_press=do_back)
        popup.open()

    def _open_filter_popup(self):
        # Create filter popup: course query + campus spinner, Apply/Clear/Cancel
        box = BoxLayout(orientation='vertical', padding=12, spacing=10)
        # Solid background
        try:
            with box.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            box.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass
        info = Label(text='Filter Study Sessions', color=DARK_BLUE, size_hint=(1, None), height=24)
        from kivy.uix.spinner import Spinner
        q = TextInput(hint_text='Search class e.g., INFO or INFO 1212', multiline=False, size_hint=(1, None), height=44)
        campus = Spinner(text=(self._filter.get('campus') or 'Any') if hasattr(self, '_filter') else 'Any', values=('Any','Surrey','Langley','Richmond'), size_hint=(1, None), height=40, color=DARK_BLUE)
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        apply_b = LightRoundedButton(text='Apply', size_hint=(1, 1))
        clear_b = LightRoundedButton(text='Clear', size_hint=(1, 1))
        cancel_b = LightRoundedButton(text='Cancel', size_hint=(1, 1))
        actions.add_widget(apply_b); actions.add_widget(clear_b); actions.add_widget(cancel_b)
        box.add_widget(info); box.add_widget(q); box.add_widget(campus); box.add_widget(actions)
        popup = Popup(title='Filter', content=box, size_hint=(None, None), size=(340, 260), auto_dismiss=False, background_color=(0.90, 0.90, 0.94, 1))

        def do_apply(*_):
            self._filter = {"q": q.text.strip() or None, "campus": campus.text.strip()}
            popup.dismiss(); self._populate_list()
        def do_clear(*_):
            self._filter = {"q": None, "campus": None}
            popup.dismiss(); self._populate_list()
        def do_cancel(*_):
            popup.dismiss()
        apply_b.bind(on_press=do_apply)
        clear_b.bind(on_press=do_clear)
        cancel_b.bind(on_press=do_cancel)
        popup.open()
