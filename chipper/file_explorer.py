import os
import sys
from os.path import expanduser, dirname
from pathlib import Path

from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen

from chipper.popups import StartSegmentationPopup, DetermineNoteThresholdPopup, \
    DetermineSyllSimThresholdPopup, \
    StartAnalysisPopup, NoGzipsFoundPopup, NoWavsFoundPopup
from chipper.utils import get_basename, get_file_prefix


class FileExplorer(Screen):
    radio_chipper = BooleanProperty()
    radio_note = BooleanProperty()
    radio_syllsim = BooleanProperty()
    radio_analyze = BooleanProperty()

    def __init__(self, **kwargs):
        super(FileExplorer, self).__init__(**kwargs)
        if sys.platform == 'win':
            user_path = dirname(expanduser('~'))
        else:
            user_path = expanduser('~')
        self.home = user_path

    def _fbrowser_success(self, instance):
        [chosen_directory] = instance.selection
        if Path(chosen_directory).is_dir():
            dir_name = chosen_directory
            check_multiple_files = True
        else:
            dir_name = os.path.dirname(chosen_directory)
            check_multiple_files = False
        self.parent.directory = dir_name

        # check which process the user wants to do
        if self.radio_chipper:
            if check_multiple_files:
                self.parent.files = get_basename(os.listdir(dir_name), 'wav')
                self.parent.file_names = get_file_prefix(self.parent.files)
            else:
                if not Path(chosen_directory).is_file():
                    raise AssertionError("Not a file")
                self.parent.files = get_basename([chosen_directory], 'wav')
                self.parent.file_names = get_file_prefix(self.parent.files)

            n_files = len(self.parent.files)
            if not n_files:
                no_wavs = NoWavsFoundPopup()
                no_wavs.open()
            else:
                segment_popup = StartSegmentationPopup(str(n_files))
                segment_popup.open()
        else:
            if check_multiple_files:
                self.parent.files = get_basename(os.listdir(dir_name), 'gzip')
                self.parent.file_names = get_file_prefix(self.parent.files)
            else:
                if not Path(chosen_directory).is_file():
                    raise AssertionError("Not a file")
                self.parent.files = get_basename([chosen_directory], 'gzip')
                self.parent.file_names = get_file_prefix(self.parent.files)
            n_files = len(self.parent.files)
            if not n_files:
                no_gzips = NoGzipsFoundPopup()
                no_gzips.open()
            elif self.radio_note:
                noise_popup = DetermineNoteThresholdPopup(str(n_files))
                noise_popup.open()
            elif self.radio_syllsim:
                syllsim_popup = DetermineSyllSimThresholdPopup(str(n_files))
                syllsim_popup.open()
            elif self.radio_analyze:
                analysis_popup = StartAnalysisPopup(str(n_files))
                analysis_popup.open()
