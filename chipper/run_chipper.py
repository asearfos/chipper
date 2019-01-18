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
from chipper.note_threshold_page import NoteThresholdPage
from chipper.note_summary_page import NoteSummaryPage
from chipper.syllable_similarity_threshold_page import SyllSimThresholdPage
from chipper.syllable_similarity_summary_page import SyllSimSummaryPage
from chipper.analysis import Analysis
from chipper.popups import FinishMarksPopup, CheckLengthPopup, CheckForSyllablesPopup, CheckBeginningEndPopup, \
    CheckOrderPopup, DonePopup
from chipper.sliders import MySlider, MyRangeSlider
from chipper.image_sonogram import ImageSonogram
from chipper.text_inputs import NumericInput
from kivy.app import App
from kivy.core.window import Window
from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')
import os
import sys


class run_chipperApp(App):
    # # will need if the thread for analysis is not daemon
    # def on_stop(self):
    #     # The Kivy event loop is about to stop, set a stop signal;
    #     # otherwise the app window will close, but the Python process will
    #     # keep running until all secondary threads exit.
    #     self.root.current_screen.stop.set()

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
