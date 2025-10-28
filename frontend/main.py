from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
# import screens
from screens.login import LoginScreen
from screens.register import RegisterScreen
from screens.tasks import TaskScreen
from screens.chat import ChatScreen
from screens.commute import CommuteScreen
from screens.profile import ProfileScreen
from screens.verify import VerifyEmailScreen

# optional: simulate mobile window size in desktop
Window.size = (360, 640)
# Make the entire UI background white
Window.clearcolor = (1, 1, 1, 1)

# optional: simulate design in iPhone 13/14 baseline
# Window.size = (390, 844)

# optional: simulate design in Samsung S23 baseline
# Window.size = (384, 852)


class ErrandBuddyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(TaskScreen(name="tasks"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(CommuteScreen(name="commute"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(VerifyEmailScreen(name="verify"))
        return sm

if __name__ == "__main__":
    ErrandBuddyApp().run()

