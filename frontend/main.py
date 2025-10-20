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

# optional: simulate mobile window size in desktop
Window.size = (360, 640)

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
