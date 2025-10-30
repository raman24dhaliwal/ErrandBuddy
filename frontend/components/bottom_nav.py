from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line


class BottomNav(BoxLayout):
    """
    Simple bottom navigation bar with five buttons:
    Home, Tasks, Study Buddy, Commute, Profile.

    Only the Tasks button is wired by default. You can pass
    callbacks for others if/when needed.

    Usage:
        nav = BottomNav(on_tasks=callback, active="Home")
    """

    def __init__(self, on_home=None, on_chat=None, on_tasks=None, on_study=None,
                 on_commute=None, on_profile=None, active: str = "",
                 **kwargs):
        super().__init__(orientation="horizontal", size_hint=(1, None), height=60, spacing=6, padding=[8, 6, 8, 6], **kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            # subtle top divider
            Color(0.85, 0.85, 0.85, 1)
            self._line = Line(points=[], width=1)
        self.bind(pos=self._update_bg, size=self._update_bg)

        def mk_btn(text, cb=None, is_active=False):
            # Active tab slightly darker background and bold-ish text color
            bg = (0.92, 0.92, 0.95, 1) if is_active else (1, 1, 1, 1)
            fg = (0.10, 0.20, 0.55, 1) if is_active else (0.25, 0.25, 0.25, 1)
            b = Button(
                text=text,
                background_normal="",
                background_color=bg,
                color=fg,
                size_hint=(1, 1),
                halign="center",
                valign="middle",
                font_size=12,
            )
            # ensure multiline text centers properly
            b.bind(size=lambda inst, val: setattr(inst, 'text_size', inst.size))
            if cb:
                b.bind(on_press=lambda *_: cb())
            return b

        # (logical name for active matching, callback, display text)
        names = [
            ("Home", on_home, "Home"),
            ("Chat", on_chat, "Chat"),
            ("Tasks", on_tasks, "Tasks"),
            ("Study Buddy", on_study, "Study\nBuddy"),
            ("Commute", on_commute, "Car\nPool"),
            ("Profile", on_profile, "Profile"),
        ]

        for name, cb, display in names:
            self.add_widget(mk_btn(display, cb, is_active=(name.lower() == (active or "").lower())))

    def _update_bg(self, *args):
        if hasattr(self, "_bg"):
            self._bg.pos = self.pos
            self._bg.size = self.size
        # update divider line along the top edge
        x, y = self.pos
        w, h = self.size
        self._line.points = [x, y + h, x + w, y + h]
