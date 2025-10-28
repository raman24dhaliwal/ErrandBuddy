from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from services.api import api
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
        self._poll_ev = None
        self.layout = BoxLayout(orientation="vertical", padding=8, spacing=8)
        self.header = BoxLayout(size_hint=(1, None), height=46, spacing=8)
        # Left-anchored title that doesn't shift when text grows
        self.title = Label(text="Chat", color=(0.1,0.2,0.55,1), halign='left', valign='middle', size_hint=(1, 1))
        self.title.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
        self.header.add_widget(self.title)
        # Back button at top-right
        self.header.add_widget(Widget(size_hint=(1, 1)))
        back_btn = Button(text="Back", size_hint=(None, None), size=(80, 36),
                          background_normal='', background_color=(0.95,0.95,0.95,1), color=(0.10,0.20,0.55,1))
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
        send = Button(text="Send", size_hint=(None, None), width=100, height=48)
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
            self.manager.current = 'tasks'
        except Exception:
            pass

    def open_for_task(self, task: dict):
        self.current_task_id = task.get('id')
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

    def refresh_messages(self):
        self.messages_box.clear_widgets()
        if not (api.token and self.current_task_id):
            return
        resp = api.list_task_messages(self.current_task_id)
        if resp.status_code == 200:
            msgs = resp.json() or []
            my_id = (api.user or {}).get('id')
            for m in msgs:
                mine = m.get('sender_id') == my_id
                self.messages_box.add_widget(MessageBubble(m, mine=mine))
            self._snap_scroll()
        else:
            self.messages_box.add_widget(Label(text=f"Failed to load messages: {getattr(resp,'text',resp)}"))

    def send_message(self, instance):
        if not (api.token and self.current_task_id):
            print("Not ready")
            return
        content = self.text.text.strip()
        if not content:
            return
        resp = api.send_task_message(self.current_task_id, content)
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
