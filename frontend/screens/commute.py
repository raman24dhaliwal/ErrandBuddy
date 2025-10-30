from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line

from services.api import api
from components.bottom_nav import BottomNav

# Reuse shared styles from Tasks screen
try:
    from screens.tasks import LightRoundedButton, RoundedInput, DARK_BLUE
except Exception:
    LightRoundedButton = Button

    def RoundedInput(**kwargs):
        from kivy.uix.textinput import TextInput
        b = BoxLayout(orientation='vertical', size_hint=(1, None), height=44)
        b.input = TextInput(**kwargs)
        b.add_widget(b.input)
        return b

    DARK_BLUE = (0.10, 0.20, 0.55, 1)


class _RideRow(BoxLayout):
    def __init__(self, ride: dict, view_cb=None, dot_rgba=(0.10, 0.20, 0.55, 1), **kwargs):
        super().__init__(orientation='horizontal', size_hint=(1, None), height=86, padding=[12, 8, 12, 8], spacing=10, **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(0.90, 0.90, 0.92, 1)
            self._line = Line(points=[])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.ride = ride or {}
        self.view_cb = view_cb or (lambda *_: None)

        # Middle: header (Offer/Request) + route + time
        mid = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=2)
        orig = (self.ride.get('origin') or '').strip() or 'Origin'
        dest = (self.ride.get('destination') or '').strip() or 'Destination'
        kind = (self.ride.get('kind') or 'offer').strip().lower()
        kind_label = 'Offer' if kind == 'offer' else 'Request'
        self._head_lbl = Label(text=f"[b]{kind_label}[/b]", markup=True, color=DARK_BLUE, size_hint=(1, None), height=20)
        mid.add_widget(self._head_lbl)
        # Route label wraps to available width, row height adjusts accordingly
        self._route_lbl = Label(text=f"{orig} -> {dest}", color=(0, 0, 0, 1), size_hint=(1, None), halign='left', valign='middle')
        self._route_lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
        self._route_lbl.bind(texture_size=lambda i, v: (setattr(i, 'height', i.texture_size[1]), self._update_size()))
        mid.add_widget(self._route_lbl)
        when = (self.ride.get('time') or '').strip()
        self._when_lbl = Label(text=(when or ''), color=(0, 0, 0, 1), size_hint=(1, None), height=18)
        mid.add_widget(self._when_lbl)
        self.add_widget(mid)

        # Right: View button
        right = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(None, 1), width=110)
        view_btn = LightRoundedButton(text='View', size_hint=(None, None), size=(80, 36))
        view_btn.bind(on_press=lambda *_: self.view_cb())
        right.add_widget(view_btn)
        self.add_widget(right)

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size
        x, y = self.pos
        w, h = self.size
        self._line.points = [x, y + h, x + w, y + h]

    def _update_size(self, *args):
        try:
            head_h = getattr(self, '_head_lbl', None).height if hasattr(self, '_head_lbl') else 20
            route_h = getattr(self, '_route_lbl', None).height if hasattr(self, '_route_lbl') else 20
            when_h = getattr(self, '_when_lbl', None).height if hasattr(self, '_when_lbl') else 18
            # vertical padding top+bottom = 16 from [12,8,12,8]
            self.height = max(74, head_h + route_h + when_h + 16 + 2)
        except Exception:
            pass


class CommuteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # white background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.root_layout = BoxLayout(orientation='vertical', padding=20, spacing=8)
        self.add_widget(self.root_layout)

        # Header matching Tasks/Study: centered title with + on the right
        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=56)
        title_row = BoxLayout(size_hint=(1, None), height=44, spacing=6)
        from kivy.uix.widget import Widget as _W
        title_row.add_widget(_W(size_hint=(None, None), size=(84, 32)))
        title_lbl = Label(text='[b]Car Pool[/b]', markup=True, color=DARK_BLUE, halign='center', valign='middle')
        title_lbl.bind(size=lambda i, v: setattr(i, 'text_size', i.size))
        title_lbl.size_hint = (1, 1)
        title_row.add_widget(title_lbl)
        actions = BoxLayout(orientation='horizontal', size_hint=(None, None), height=32, width=120, spacing=6)
        plus = LightRoundedButton(text='+', size_hint=(None, None), size=(36, 32))
        plus.bind(on_press=lambda *_: self._open_create_popup())
        filt = LightRoundedButton(text='Filter', size_hint=(None, None), size=(60, 32))
        filt.bind(on_press=lambda *_: self._open_filter_popup())
        actions.add_widget(plus)
        actions.add_widget(filt)
        title_row.add_widget(actions)
        header.add_widget(title_row)
        self.root_layout.add_widget(header)

        # Scrollable list of offers
        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_box = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=0, padding=[0, 0, 0, 8])
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.root_layout.add_widget(self.scroll)

        # Bottom navigation bar
        self._add_bottom_nav()

    def _update_bg(self, *args):
        if hasattr(self, '_bg'):
            self._bg.pos = self.pos
            self._bg.size = self.size

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        try:
            resp = api.list_rides()
            if resp.status_code != 200:
                raise Exception(getattr(resp, 'text', resp))
            rides = resp.json() or []
        except Exception as e:
            self.list_box.add_widget(Label(text=f'Failed to load rides: {e}', color=DARK_BLUE, size_hint=(1, None), height=24))
            return
        # Initialize and apply filter (Any/Offer/Request)
        if not hasattr(self, '_filter'):
            self._filter = {"kind": 'Any'}
        kind_sel = (getattr(self, '_filter', {}) or {}).get('kind') or 'Any'
        if kind_sel and kind_sel != 'Any':
            want = 'offer' if kind_sel.lower() == 'offer' else 'request'
            rides = [r for r in rides if (r.get('kind') or 'offer').strip().lower() == want]
        if not rides:
            self.list_box.add_widget(Label(text='No car pool offers yet', color=DARK_BLUE, size_hint=(1, None), height=24))
            return
        for r in rides:
            row = _RideRow(r, view_cb=(lambda __r=r: self._open_view_popup(__r)))
            self.list_box.add_widget(row)

    def _open_filter_popup(self):
        from kivy.uix.spinner import Spinner
        box = BoxLayout(orientation='vertical', padding=12, spacing=10)
        try:
            with box.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            box.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass
        info = Label(text='Filter Car Pool', color=DARK_BLUE, size_hint=(1, None), height=24)
        cur = (getattr(self, '_filter', {}) or {}).get('kind') or 'Any'
        kind = Spinner(text=cur, values=('Any','Offer','Request'), size_hint=(1, None), height=40, color=DARK_BLUE)
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        apply_b = LightRoundedButton(text='Apply', size_hint=(1, 1))
        clear_b = LightRoundedButton(text='Clear', size_hint=(1, 1))
        cancel_b = LightRoundedButton(text='Cancel', size_hint=(1, 1))
        actions.add_widget(apply_b); actions.add_widget(clear_b); actions.add_widget(cancel_b)
        box.add_widget(info); box.add_widget(kind); box.add_widget(actions)
        popup = Popup(title='Filter', content=box, size_hint=(None, None), size=(320, 220), auto_dismiss=False, background_color=(0.90, 0.90, 0.94, 1))

        def do_apply(*_):
            self._filter = {"kind": (kind.text or 'Any').strip() or 'Any'}
            popup.dismiss(); self.refresh()
        def do_clear(*_):
            self._filter = {"kind": 'Any'}
            popup.dismiss(); self.refresh()
        def do_cancel(*_):
            popup.dismiss()
        apply_b.bind(on_press=do_apply)
        clear_b.bind(on_press=do_clear)
        cancel_b.bind(on_press=do_cancel)
        popup.open()

    def _open_create_popup(self):
        # Root container with Study Buddy styling
        root = BoxLayout(orientation='vertical', padding=12, spacing=10)
        try:
            with root.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=root.pos, size=root.size)
            root.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            root.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass

        # Scrollable content area to prevent overflow
        from kivy.uix.scrollview import ScrollView
        sc = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, None))
        content.bind(minimum_height=content.setter('height'))

        info = Label(text='Create Car Pool', color=DARK_BLUE, size_hint=(1, None), height=24)
        # Kind selector: Offer or Request
        from kivy.uix.spinner import Spinner
        kind = Spinner(text='Offer', values=('Offer', 'Request'), size_hint=(1, None), height=40, color=DARK_BLUE)
        origin = RoundedInput(hint='Origin')
        destination = RoundedInput(hint='Destination')
        when = RoundedInput(hint='Time (e.g., 5:30 PM)')
        desc = RoundedInput(hint='Description (Optional)', multiline=True, height=90)

        # Assemble content
        for w in (info, kind, origin, destination, when, desc):
            content.add_widget(w)
        sc.add_widget(content)
        root.add_widget(sc)

        # Actions pinned to bottom
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        create_b = LightRoundedButton(text='Create', size_hint=(1, 1))
        cancel_b = LightRoundedButton(text='Cancel', size_hint=(1, 1))
        actions.add_widget(create_b); actions.add_widget(cancel_b)
        root.add_widget(actions)

        popup = Popup(title='New Car Pool', content=root, size_hint=(None, None), size=(380, 460), auto_dismiss=False, background_color=(0.90, 0.90, 0.94, 1))

        def do_create(*_):
            o = (origin.input.text or '').strip()
            d = (destination.input.text or '').strip()
            t = (when.input.text or '').strip()
            k = (kind.text or 'Offer').strip().lower()
            if k not in ('offer', 'request'):
                k = 'offer'
            description = (desc.input.text or '').strip()
            if not (o and d and t):
                print('Please fill all fields')
                return
            try:
                r = api.create_ride(o, d, t, kind=k, description=description or None)
                if r.status_code in (200, 201):
                    popup.dismiss(); self.refresh()
                else:
                    print('Create failed', getattr(r, 'text', r))
            except Exception as e:
                print('Error creating ride', e)

        def do_cancel(*_):
            popup.dismiss()
        create_b.bind(on_press=do_create)
        cancel_b.bind(on_press=do_cancel)
        popup.open()

    def _open_view_popup(self, ride: dict):
        owner_id = ride.get('driver_id')
        me = (api.user or {}).get('id')
        # Root container with styling
        root = BoxLayout(orientation='vertical', padding=12, spacing=10)
        try:
            with root.canvas.before:
                Color(0.90, 0.90, 0.94, 1)
                _bg = Rectangle(pos=root.pos, size=root.size)
            root.bind(pos=lambda i, v: setattr(_bg, 'pos', i.pos))
            root.bind(size=lambda i, v: setattr(_bg, 'size', i.size))
        except Exception:
            pass

        # Scrollable details area
        from kivy.uix.scrollview import ScrollView
        sc = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation='vertical', padding=[0,0,0,0], spacing=6, size_hint=(1, None))
        content.bind(minimum_height=content.setter('height'))

        def line(label, value):
            row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=26, spacing=6)
            row.add_widget(Label(text=f"{label}", color=DARK_BLUE, size_hint=(None, 1), width=90))
            row.add_widget(Label(text=value or '', color=(0, 0, 0, 1)))
            return row

        kind_text = (ride.get('kind') or 'offer').strip().lower()
        kind_text = 'Offer' if kind_text == 'offer' else 'Request'
        route_title = f"{kind_text}: {(ride.get('origin') or '').strip()} -> {(ride.get('destination') or '').strip()}"
        content.add_widget(Label(text=route_title, color=DARK_BLUE, size_hint=(1, None), height=24))
        content.add_widget(line('Type:', kind_text))
        content.add_widget(line('Origin:', ride.get('origin') or ''))
        content.add_widget(line('Destination:', ride.get('destination') or ''))
        content.add_widget(line('Time:', ride.get('time') or ''))
        content.add_widget(Label(text='Description:', color=DARK_BLUE, size_hint=(1, None), height=20))
        desc_lbl = Label(
            text=(ride.get('description') or '').strip() or '(No description)',
            color=(0, 0, 0, 1),
            size_hint=(1, None),
            halign='left', valign='top'
        )
        # Wrap text to the available width and expand height to fit content
        desc_lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
        desc_lbl.bind(texture_size=lambda i, v: setattr(i, 'height', i.texture_size[1]))
        content.add_widget(desc_lbl)
        sc.add_widget(content)
        root.add_widget(sc)

        # Actions row
        actions = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, None), height=44)
        # Owner can delete
        if me and owner_id and me == owner_id:
            del_b = LightRoundedButton(text='Delete', size_hint=(1, 1))
            def do_delete(*_):
                try:
                    r = api.delete_ride(ride.get('id'))
                    if r.status_code == 200:
                        popup.dismiss(); self.refresh()
                    else:
                        print('Delete failed', getattr(r, 'text', r))
                except Exception as e:
                    print('Error deleting ride', e)
            del_b.bind(on_press=do_delete)
            actions.add_widget(del_b)
        else:
            # Non-owner can open chat with owner
            chat_b = LightRoundedButton(text='Chat', size_hint=(1, 1))
            def do_chat(*_):
                try:
                    chat = self.manager.get_screen('chat')
                except Exception:
                    chat = None
                if chat and owner_id:
                    display = 'Car Pool'
                    chat.open_with_user(owner_id, display_name=display, prev_screen='commute')
                    try:
                        from kivy.uix.screenmanager import SlideTransition
                        if self.manager:
                            self.manager.transition = SlideTransition(direction='left', duration=0.18)
                    except Exception:
                        pass
                    self.manager.current = 'chat'
            chat_b.bind(on_press=do_chat)
            actions.add_widget(chat_b)

        close_b = LightRoundedButton(text='Close', size_hint=(1, 1))
        actions.add_widget(close_b)
        root.add_widget(actions)

        popup = Popup(title='Ride', content=root, size_hint=(None, None), size=(340, 460), auto_dismiss=False, background_color=(0.90, 0.90, 0.94, 1))
        close_b.bind(on_press=lambda *_: popup.dismiss())
        popup.open()

    # Bottom navigation and routing helpers
    def _add_bottom_nav(self):
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
            on_study=lambda: self._go_screen('study', 'left'),
            on_commute=lambda: None,
            on_profile=lambda: self._go_screen('profile', 'left'),
            active="Commute",
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
