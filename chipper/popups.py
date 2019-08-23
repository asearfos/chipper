from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.uix.popup import Popup


class FinishMarksPopup(Popup):

    def __init__(self, controls, **kwargs):
        # controls is now the object where popup was called from.
        # self.register_event_type('on_connect')
        super(FinishMarksPopup, self).__init__(**kwargs)
        self.controls = controls


class CheckLengthPopup(Popup):
    len_onsets = StringProperty()
    len_offsets = StringProperty()


class CheckForSyllablesPopup(Popup):
    pass


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


class LargeFilePopup(Popup):
    message = StringProperty()
    file_size = StringProperty()

    def __init__(self, controls, file_name, f_size, **kwargs):
        super(LargeFilePopup, self).__init__(**kwargs)
        self.controls = controls
        self.message = file_name
        self.file_size = f_size


class StartSegmentationPopup(Popup):
    len_files = StringProperty()

    def __init__(self, n_files, **kwargs):
        super(StartSegmentationPopup, self).__init__(**kwargs)
        self.len_files = n_files


class DetermineNoiseThresholdPopup(Popup):
    len_files = StringProperty()

    def __init__(self, n_files, **kwargs):
        super(DetermineNoiseThresholdPopup, self).__init__(**kwargs)
        self.len_files = n_files


class NoiseThreshInstructionsPopup(Popup):
    pass


class DetermineSyllSimThresholdPopup(Popup):
    len_files = StringProperty()

    def __init__(self, n_files, **kwargs):
        super(DetermineSyllSimThresholdPopup, self).__init__(**kwargs)
        self.len_files = n_files


class SyllSimThreshInstructionsPopup(Popup):
    pass


class StartAnalysisPopup(Popup):
    len_files = StringProperty()

    def __init__(self, n_files, **kwargs):
        super(StartAnalysisPopup, self).__init__(**kwargs)
        self.len_files = n_files


class NoGzipsFoundPopup(Popup):
    pass


class NoWavsFoundPopup(Popup):
    pass
