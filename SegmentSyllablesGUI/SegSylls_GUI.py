# import sys
import kivy
# from kivy.logger import Logger
# Logger.disabled = True
# sys.path.insert(0, 'bin')
kivy.require('1.10.0')

from SegSylls_Manager import Manager
from SegSylls_FileExplorer import FileExplorer
from SegSylls_ControlPanel import ControlPanel
from SegSylls_Popups import FinishMarksPopup, CheckLengthPopup, CheckBeginningEndPopup, CheckOrderPopup, DonePopup
from SegSylls_Sliders import MySlider, MyRangeSlider
from SegSylls_ImageSonogram import ImageSonogram
from kivy.app import App
from kivy.core.window import Window
from kivy.config import Config


class SegSylls_GUIApp(App):
    def build(self):
        return Manager()

if __name__ == "__main__":
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    Window.fullscreen = 'auto'
    SegSylls_GUIApp().run()