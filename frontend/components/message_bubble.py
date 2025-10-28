from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle


class MessageBubble(BoxLayout):
    """
    Chat bubble aligned based on `mine`.
    - mine=True  -> align LEFT (sender/current user)
    - mine=False -> align RIGHT (received)
    Wraps long text to avoid overflow using ~70% of window width.
    """

    def __init__(self, message, mine=False, **kwargs):
        super().__init__(orientation='vertical', size_hint=(1, None), padding=[10, 4, 10, 4], **kwargs)

        text = str(message.get("content", ""))
        # Anchor left for own messages, right for received (per request)
        anchor_x = 'left' if mine else 'right'
        row = AnchorLayout(anchor_x=anchor_x, size_hint=(1, None))
        self.add_widget(row)

        # Label inside rounded bubble
        lbl = Label(text=text, size_hint=(None, None), halign='left' if mine else 'right', valign='middle', color=(0, 0, 0, 1))
        lbl.bind(texture_size=lambda *_: self._refresh_sizes(row, bubble, lbl))

        bubble = BoxLayout(size_hint=(None, None), padding=[10, 6, 10, 6])
        with bubble.canvas.before:
            # light tint bubble
            Color(0.93, 0.93, 0.97, 1)
            bubble._rect = RoundedRectangle(pos=bubble.pos, size=(0, 0), radius=[12])
        bubble.bind(pos=lambda *_: self._update_rect(bubble), size=lambda *_: self._update_rect(bubble))
        bubble.add_widget(lbl)
        row.add_widget(bubble)

        # Initial size compute
        self._refresh_sizes(row, bubble, lbl)

    def _max_width(self):
        try:
            return int(max(180, min(0.72 * Window.width, 320)))
        except Exception:
            return 260

    def _refresh_sizes(self, row, bubble, lbl):
        # wrap to max width
        lbl.text_size = (self._max_width(), None)
        lbl.texture_update()
        lbl.size = (min(lbl.texture_size[0], self._max_width()), max(24, lbl.texture_size[1]))
        bubble.size = (lbl.size[0] + bubble.padding[0] + bubble.padding[2], lbl.size[1] + bubble.padding[1] + bubble.padding[3])
        row.height = bubble.height
        self.height = bubble.height + self.padding[1] + self.padding[3]
        self._update_rect(bubble)

    def _update_rect(self, bubble):
        try:
            bubble._rect.pos = bubble.pos
            bubble._rect.size = bubble.size
        except Exception:
            pass
