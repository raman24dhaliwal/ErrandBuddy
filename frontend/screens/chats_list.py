from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from components.bottom_nav import BottomNav
from services.api import api
try:
    from local_store import get_last_read, get_title_override
except Exception:
    from frontend.local_store import get_last_read, get_title_override

DARK_BLUE = (0.10, 0.20, 0.55, 1)


class ChatsListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=8)
        # Header
        title = Label(text='[b]Chats[/b]', markup=True, color=DARK_BLUE, size_hint=(1, None), height=44,
                      halign='center', valign='middle')
        title.bind(size=lambda i, v: setattr(i, 'text_size', i.size))
        self.layout.add_widget(title)
        # List
        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_box = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=6)
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.layout.add_widget(self.scroll)
        # Bottom nav
        self._add_bottom_nav()
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        if not api.token:
            self.list_box.add_widget(Label(text='Login to see your chats', color=DARK_BLUE, size_hint=(1, None), height=24))
            return
        resp = api.list_chat_overview()
        if resp.status_code != 200:
            self.list_box.add_widget(Label(text=f'Failed to load chats: {getattr(resp,"text",resp)}', color=DARK_BLUE, size_hint=(1, None), height=24))
            return
        items = resp.json() or []
        if not items:
            self.list_box.add_widget(Label(text='No active chats yet', color=DARK_BLUE, size_hint=(1, None), height=24))
            return
        for item in items:
            self.list_box.add_widget(self._row(item))

    def _row(self, item: dict):
        row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=56, padding=[8, 6, 8, 6], spacing=8)
        # Left: title + snippet
        box = BoxLayout(orientation='vertical')
        title = self._title_for(item)
        box.add_widget(Label(text=f'[b]{title}[/b]', markup=True, color=DARK_BLUE, size_hint=(1, None), height=22))
        # Status: New Message or Read
        status = self._status_for(item)
        box.add_widget(Label(text=status, color=(0,0,0,1), size_hint=(1, None), height=20))
        row.add_widget(box)
        # Right: Open button
        btn = Button(text='Open', size_hint=(None, None), size=(80, 36))
        btn.bind(on_press=lambda *_: self._open(item))
        row.add_widget(btn)
        return row

    def _title_for(self, item: dict) -> str:
        if (item.get('type') or '') == 'task':
            tid = item.get('task_id')
            other = (item.get('other') or {})
            uname = ((other.get('first_name') or '') + ' ' + (other.get('last_name') or '')).strip() or other.get('username') or ''
            return f'Task #{tid} - {uname}'.strip(' -')
        other = (item.get('other') or {})
        uname = ((other.get('first_name') or '') + ' ' + (other.get('last_name') or '')).strip() or other.get('username') or 'Chat'
        # Try a local title override for Study Buddy Sessions; prefer course only in header
        key = f"user:{item.get('other_id')}"
        override = get_title_override(key)
        course = None
        if override and '(' in override and ')' in override:
            try:
                course = override.split('(', 1)[1].split(')', 1)[0].strip()
            except Exception:
                course = None
        title = (course or override or 'Study Buddy Session') + ' - ' + uname
        return title.strip(' -')

    def _status_for(self, item: dict) -> str:
        lm = (item.get('last_message') or {})
        ts = lm.get('timestamp')
        key = 'task:%s' % item.get('task_id') if (item.get('type') or '') == 'task' else 'user:%s' % item.get('other_id')
        try:
            lr = get_last_read(key)
            if not lr:
                return 'New Message'
            from datetime import datetime
            lt = datetime.fromisoformat(lr)
            mt = datetime.fromisoformat(ts) if ts else None
            if mt and mt > lt:
                return 'New Message'
            return 'Read'
        except Exception:
            return 'New Message' if ts else 'Read'

    def _open(self, item: dict):
        try:
            chat = self.manager.get_screen('chat')
        except Exception:
            chat = None
        if not chat:
            return
        if (item.get('type') or '') == 'task':
            tid = item.get('task_id')
            chat.open_for_task({'id': tid})
        else:
            # For Study Buddy DMs, pass course if available so chat header shows only the course
            other = item.get('other') or {}
            key = f"user:{item.get('other_id')}"
            override = get_title_override(key)
            course = None
            if override and '(' in override and ')' in override:
                try:
                    course = override.split('(', 1)[1].split(')', 1)[0].strip()
                except Exception:
                    course = None
            display = course or None
            chat.open_with_user(item.get('other_id'), display_name=display, prev_screen='chats')
        # slide left to chat
        try:
            from kivy.uix.screenmanager import SlideTransition
            if self.manager:
                self.manager.transition = SlideTransition(direction='left', duration=0.18)
        except Exception:
            pass
        self.manager.current = 'chat'

    def _add_bottom_nav(self):
        def go_home():
            try:
                t = self.manager.get_screen('tasks')
                t.show_home()
            except Exception:
                pass
            self._go('tasks', 'right')
        def go_tasks():
            try:
                t = self.manager.get_screen('tasks')
                t.load_tasks()
            except Exception:
                pass
            self._go('tasks', 'right')
        nav = BottomNav(
            on_home=go_home,
            on_chat=lambda: None,
            on_tasks=go_tasks,
            on_study=lambda: self._go('study', 'left'),
            on_commute=lambda: self._go('commute', 'left'),
            on_profile=lambda: self._go('profile', 'left'),
            active='Chat',
        )
        self.layout.add_widget(nav)

    def _go(self, name: str, direction: str):
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
