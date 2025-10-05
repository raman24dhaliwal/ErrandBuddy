from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

Window.size = (360, 640)  # Optional: simulate mobile screen

# ------------------------
# Base Screen with Background
# ------------------------
class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.53, 0.81, 0.92, 1)  # Sky blue
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

# ------------------------
# Login Screen (Mobile style)
# ------------------------
class LoginScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # AnchorLayout to center content
        anchor = AnchorLayout(anchor_x='center', anchor_y='center')

        layout = BoxLayout(
            orientation='vertical',
            padding=[30, 20, 30, 20],
            spacing=15,
            size_hint=(0.85, 0.8)
        )

        # Logo
        layout.add_widget(Image(source="assets/logo.jpeg", size_hint=(1, 0.35)))

        # App name
        layout.add_widget(Label(
            text="ERRANDBUDDY\nBY KPU · FOR KPU",
            font_size=20,
            halign="center",
            size_hint=(1, 0.15)
        ))

        # Email input
        self.email = TextInput(
            hint_text="EMAIL ADDRESS",
            multiline=False,
            size_hint=(1, 0.12),
            background_normal='',
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10]
        )
        layout.add_widget(self.email)

        # Password input
        self.password = TextInput(
            hint_text="PASSWORD",
            password=True,
            multiline=False,
            size_hint=(1, 0.12),
            background_normal='',
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10]
        )
        layout.add_widget(self.password)

        # Login button
        login_btn = Button(
            text="Log in",
            size_hint=(1, 0.15),
            background_normal='',
            background_color=(0.1, 0.1, 0.5, 1),
            color=(1, 1, 1, 1)
        )
        login_btn.bind(on_press=self.login)
        layout.add_widget(login_btn)

        # Sign Up button
        signup_btn = Button(
            text="SIGN UP",
            size_hint=(1, 0.15),
            background_normal='',
            background_color=(0.6, 0.4, 1, 1),
            color=(1, 1, 1, 1)
        )
        signup_btn.bind(on_press=self.go_register)
        layout.add_widget(signup_btn)

        anchor.add_widget(layout)
        self.add_widget(anchor)

    def login(self, instance):
        if self.email.text and self.password.text:
            self.manager.current = "tasks"
        else:
            print("Please enter Email & Password.")

    def go_register(self, instance):
        self.manager.current = "register"

# ------------------------
# Other Screens
# ------------------------
class RegisterScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="REGISTER SCREEN", font_size=24))

class TaskScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="TASK SCREEN"))

class ChatScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="CHAT SCREEN"))

class CommuteScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="COMMUTE SCREEN"))

class ProfileScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="PROFILE SCREEN"))

# ------------------------
# App Entry
# ------------------------
class ErrandBuddyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(TaskScreen(name="tasks"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(CommuteScreen(name="commute"))
        sm.add_widget(ProfileScreen(name="profile"))
        return sm

if __name__ == "__main__":
    ErrandBuddyApp().run()
