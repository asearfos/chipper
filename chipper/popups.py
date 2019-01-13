from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty, ListProperty


class FinishMarksPopup(Popup):
    def __init__(self, controls, **kwargs):  # controls is now the object where popup was called from.
        # self.register_event_type('on_connect')
        super(FinishMarksPopup, self).__init__(**kwargs)
        self.controls = controls


class CheckLengthPopup(Popup):
    len_onsets = StringProperty()
    len_offsets = StringProperty()


class CheckBeginningEndPopup(Popup):
    start_onset = BooleanProperty()
    end_offset = BooleanProperty()
    two_onsets = BooleanProperty()
    two_offsets = BooleanProperty()


class CheckOrderPopup(Popup):
    order = ListProperty()


class DonePopup(Popup):
    def quit_app(self):
        print('song segmentation complete, Close chipper.')
        quit()


class StartSegmentationPopup(Popup):
    len_files = StringProperty()


class DetermineNoteThresholdPopup(Popup):
    len_files = StringProperty()


class NoteThreshInstructionsPopup(Popup):
    pass


class DetermineSyllSimThresholdPopup(Popup):
    len_files = StringProperty()


class SyllSimThreshInstructionsPopup(Popup):
    pass


class StartAnalysisPopup(Popup):
    len_files = StringProperty()


class NoGzipsFoundPopup(Popup):
    pass


class NoWavsFoundPopup(Popup):
    pass


