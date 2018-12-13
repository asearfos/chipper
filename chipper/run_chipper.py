# import sys
import kivy
from kivy.logger import Logger
Logger.disabled = True
# sys.path.insert(0, 'bin')
kivy.require('1.10.0')

from chipper.manager import Manager
from chipper.landing_page import LandingPage
from chipper.file_explorer import FileExplorer
from chipper.control_panel import ControlPanel
from chipper.popups import FinishMarksPopup, CheckLengthPopup, CheckBeginningEndPopup, CheckOrderPopup, \
    DonePopup
from chipper.sliders import MySlider, MyRangeSlider
from chipper.image_sonogram import ImageSonogram
from chipper.text_inputs import PercentInput
from kivy.app import App
from kivy.core.window import Window
from kivy.config import Config
import os
import sys


class run_chipperApp(App):
    def build(self):
        dir = os.path.dirname(__file__)
        self.icon = os.path.join(dir, 'SP1.png')
        return Manager()

# add function if using --onefile in PyInstaller
# def resourcePath():
#     '''Returns path containing content - either locally or in PyInstaller tmp file'''
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS)
#
#     return os.path.join(os.path.abspath("."))

try:  # needed for PyInstaller to work with --windowed option and not throw fatal error
    # print('Please wait while loading Chipper...')
    if __name__ == "__main__":
        # kivy.resources.resource_add_path(resourcePath())  # add this line if using --onefile in PyInstaller
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        # Window.fullscreen = 'auto'
        run_chipperApp().run()
except:
    pass
