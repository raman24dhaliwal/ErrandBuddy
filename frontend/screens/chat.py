from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from services.api import api
# Reuse shared button style from Tasks screen
try:
    from screens.tasks import LightRoundedButton
except Exception:
    LightRoundedButton = Button
try:
    from local_store import (
        get_cleared_at,
        set_cleared_now,
        get_last_read,
        set_last_read_now,
        get_title_override,
    )
except Exception:
    from frontend.local_store import (
        get_cleared_at,
        set_cleared_now,
        get_last_read,
        set_last_read_now,
        get_title_override,
    )
from datetime import datetime
from kivy.clock import Clock
from components.message_bubble import MessageBubble

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.current_task_id = None
        self.other_user_id = None
        self._prev_screen = 'tasks'
        self._poll_ev = None
        self.layout = BoxLayout(orientation="vertical", padding=8, spacing=8)
        self.header = BoxLayout(size_hint=(1, None), height=46, spacing=8)
        # Left-anchored title that doesn't shift when text grows
        self.title = Label(text="Chat", color=(0.1,0.2,0.55,1), halign='left', valign='middle', size_hint=(1, 1))
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        self.header.add_widget(self.title)
        # Clear + Back buttons at top-right
        self.header.add_widget(Widget(size_hint=(1, 1)))
        clear_btn = LightRoundedButton(text="Clear", size_hint=(None, None), size=(80, 36))
        clear_btn.bind(on_press=lambda *_: self.clear_chat())
        self.header.add_widget(clear_btn)
        back_btn = LightRoundedButton(text="Back", size_hint=(None, None), size=(80, 36))
        back_btn.bind(on_press=lambda *_: self._go_back())
        self.header.add_widget(back_btn)
        self.layout.add_widget(self.header)
        from kivy.uix.scrollview import ScrollView
        self.scroll = ScrollView(size_hint=(1, 1))
        self.messages_box = BoxLayout(orientation="vertical", spacing=6, size_hint=(1, None))
        self.messages_box.bind(minimum_height=self.messages_box.setter('height'))
        self.scroll.add_widget(self.messages_box)
        self.layout.add_widget(self.scroll)
        self.input_box = BoxLayout(size_hint=(1, None), height=48, spacing=8)
        self.text = TextInput(hint_text="Message...", multiline=False)
        send = LightRoundedButton(text="Send", size_hint=(None, None), width=100, height=36)
        send.bind(on_press=self.send_message)
        self.input_box.add_widget(self.text)
        self.input_box.add_widget(send)
        self.layout.add_widget(self.input_box)
        self.add_widget(self.layout)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def on_pre_enter(self, *args):
        # start a light polling to keep messages fresh when the screen is visible
        if self._poll_ev is None:
            self._poll_ev = Clock.schedule_interval(lambda dt: self.refresh_messages(), 3.0)

    def on_leave(self, *args):
        if self._poll_ev is not None:
            try:
                self._poll_ev.cancel()
            except Exception:
                pass
            self._poll_ev = None

    def _go_back(self):
        try:
            from kivy.uix.screenmanager import SlideTransition
            if self.manager:
                self.manager.transition = SlideTransition(direction='right', duration=0.18)
                self.manager.current = self._prev_screen or 'tasks'
        except Exception:
            try:
                self.manager.current = self._prev_screen or 'tasks'
            except Exception:
                pass

    def open_for_task(self, task: dict):
        self.current_task_id = task.get('id')
        self.other_user_id = None
        self._prev_screen = 'tasks'
        # determine the other user's id from the task
        try:
            my_id = (api.user or {}).get('id')
            owner_id = task.get('user_id')
            assignee_id = task.get('assignee_id')
            other_id = assignee_id if my_id == owner_id else owner_id
            # fetch user to display name
            name = None
            if other_id:
                r = api.get_user(other_id)
                if r.status_code == 200:
                    u = r.json() or {}
                    fn = (u.get('first_name') or '').strip()
                    ln = (u.get('last_name') or '').strip()
                    name = (fn + ' ' + ln).strip() or u.get('username') or u.get('email')
            self.title.text = name if name else f"Task #{self.current_task_id}"
        except Exception:
            self.title.text = f"Task #{self.current_task_id}"
        self.refresh_messages()
        # mark as read when opened
        self._mark_read()

    def open_with_user(self, user_id: int, display_name: str = None, prev_screen: str = 'study'):
        self.other_user_id = int(user_id) if user_id is not None else None
        self.current_task_id = None
        self._prev_screen = prev_screen or 'tasks'
        # Set header title
        # Prefer provided display name; else fall back to user name
        title_text = None
        if display_name:
            title_text = display_name
        else:
            try:
                r = api.get_user(self.other_user_id)
                if r.status_code == 200:
                    u = r.json() or {}
                    fn = (u.get('first_name') or '').strip()
                    ln = (u.get('last_name') or '').strip()
                    title_text = (fn + ' ' + ln).strip() or u.get('username')
            except Exception:
                pass
        # If a Study Buddy title override exists like "Study Buddy Session (COURSE)",
        # show just the course to keep the header short.
        try:
            key = f'user:{self.other_user_id}' if self.other_user_id else None
            override = get_title_override(key) if key else None
            if override:
                if '(' in override and ')' in override:
                    course = override.split('(', 1)[1].split(')', 1)[0].strip()
                    if course:
                        title_text = course
                else:
                    title_text = override
        except Exception:
            pass
        self.title.text = title_text or 'Chat'
        self.refresh_messages()
        self._mark_read()

    def refresh_messages(self):
        self.messages_box.clear_widgets()
        if not api.token:
            return
        if self.current_task_id:
            resp = api.list_task_messages(self.current_task_id)
        elif self.other_user_id:
            resp = api.list_conversation(self.other_user_id)
        else:
            return
        if resp.status_code == 200:
            msgs = resp.json() or []
            # Apply local clear threshold if set
            key = self._conversation_key()
            try:
                cut = get_cleared_at(key)
                if cut:
                    try:
                        cut_dt = datetime.fromisoformat(cut)
                        def _after(m):
                            ts = m.get('timestamp')
                            try:
                                mt = datetime.fromisoformat(ts)
                                return mt > cut_dt
                            except Exception:
                                return True
                        msgs = [m for m in msgs if _after(m)]
                    except Exception:
                        pass
            except Exception:
                pass
            my_id = (api.user or {}).get('id')
            for m in msgs:
                mine = m.get('sender_id') == my_id
                self.messages_box.add_widget(MessageBubble(m, mine=mine))
            self._snap_scroll()
        else:
            self.messages_box.add_widget(Label(text=f"Failed to load messages: {getattr(resp,'text',resp)}"))

    def send_message(self, instance):
        if not api.token:
            print("Not ready")
            return
        content = self.text.text.strip()
        if not content:
            return
        if self.current_task_id:
            resp = api.send_task_message(self.current_task_id, content)
        elif self.other_user_id:
            resp = api.send_message(self.other_user_id, content)
        else:
            return
        if resp.status_code in (200, 201):
            try:
                data = resp.json() or {}
                m = data.get('message') or {}
                # append locally for instant feedback
                self.messages_box.add_widget(MessageBubble(m, mine=True))
                self._snap_scroll()
            except Exception:
                self.refresh_messages()
            self.text.text = ""
        else:
            print("Send failed", getattr(resp,'text',resp))
        # update read marker after sending
        self._mark_read()

    def _snap_scroll(self):
        """Anchor to top if content fits; bottom if overflowing."""
        try:
            from kivy.clock import Clock
            def _do(*_):
                try:
                    viewport_h = self.scroll.height
                    content_h = self.messages_box.height
                    if content_h <= viewport_h + 1:
                        # stick to top when content doesn't overflow
                        self.scroll.scroll_y = 1
                    else:
                        # overflow: show latest at bottom
                        self.scroll.scroll_y = 0
                except Exception:
                    pass
            Clock.schedule_once(_do, 0)
        except Exception:
            pass

    def _conversation_key(self):
        if self.current_task_id:
            return f"task:{self.current_task_id}"
        if self.other_user_id:
            return f"user:{self.other_user_id}"
        return None

    def clear_chat(self):
        key = self._conversation_key()
        if not key:
            return
        set_cleared_now(key)
        self.refresh_messages()

    def _mark_read(self):
        key = self._conversation_key()
        if key:
            try:
                set_last_read_now(key)
            except Exception:
                pass
