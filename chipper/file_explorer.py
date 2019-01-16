import os
import sys
from os.path import expanduser, dirname

from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen

from chipper.popups import StartSegmentationPopup, DetermineNoteThresholdPopup, \
    DetermineSyllSimThresholdPopup, \
    StartAnalysisPopup, NoGzipsFoundPopup, NoWavsFoundPopup


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
        self.parent.directory = chosen_directory + '/'

        # check which process the user wants to do
        if self.radio_chipper:
            num_files, found_files = self.check_for_files(directory=self.parent.directory, filetype='wav')
            if not found_files:
                no_wavs = NoWavsFoundPopup()
                no_wavs.open()
            else:
                segment_popup = StartSegmentationPopup()
                segment_popup.len_files = str(num_files)
                segment_popup.open()
        else:
            num_files, found_files = self.check_for_files(directory=self.parent.directory, filetype='gzip')
            if not found_files:
                no_gzips = NoGzipsFoundPopup()
                no_gzips.open()
            elif self.radio_note:
                note_popup = DetermineNoteThresholdPopup()
                note_popup.len_files = str(num_files)
                note_popup.open()
            elif self.radio_syllsim:
                syllsim_popup = DetermineSyllSimThresholdPopup()
                syllsim_popup.len_files = str(num_files)
                syllsim_popup.open()
            elif self.radio_analyze:
                analysis_popup = StartAnalysisPopup()
                analysis_popup.len_files = str(num_files)
                analysis_popup.open()

    def check_for_files(self, directory, filetype):
        found_files = False
        files = []
        file_names = []
        for f in os.listdir(directory):
            if f.endswith(filetype):
                files.append(os.path.join(directory, f))
                file_names.append(f)
        if len(files) != 0:
            found_files = True
        return len(files), found_files
