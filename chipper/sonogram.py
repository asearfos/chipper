import glob
import os

import numpy as np
import soundfile as sf
from kivy.core.audio import SoundLoader

from chipper.functions import load_bout_data
from chipper.ifdvsonogramonly import ifdvsonogramonly


class Sonogram(object):
    def __init__(self, wavfile, directory, find_gzips):
        f_path = os.path.join(directory, wavfile)
        # audio data always returned as 2d array
        song1, sample_rate = sf.read(f_path, always_2d=True)

        song1 = song1[:, 0]  # make files mono

        # make spectrogram binary, divide by max value to get 0-1 range
        sonogram, ms_per_pix, hz_per_pix = ifdvsonogramonly(song1, sample_rate,
                                                            1024, 1010, 2)
        [rows, cols] = sonogram.shape
        sonogram_padded = np.zeros((rows, cols + 300))
        # padding for window to start
        sonogram_padded[:, 150:cols + 150] = sonogram
        self.sound = SoundLoader.load(f_path)
        self.sonogram = sonogram_padded
        self.ms_pix = ms_per_pix
        self.hertzPerPixel = hz_per_pix
        self.rows, self.cols = np.shape(self.sonogram)
        self.filter_boundary = [0, self.rows]
        self.bout_range = [0, self.cols]
        self.percent_keep = None
        self.min_silence = None
        self.min_syllable = None
        self.normalized = None
        # override with previous
        if find_gzips:
            # check if there is a corresponding gzip from a previous run
            _path = '{}/**/SegSyllsOutput_{}.gzip'.format(
                os.path.split(os.path.split(directory)[0])[0], wavfile[:4]
            )
            zip_file = glob.glob(_path, recursive=True)
        else:
            zip_file = []

        if zip_file:
            # if prev zip file, open and use the saved parameters
            self.params, self.prev_onsets, self.prev_offsets = \
                load_bout_data(zip_file[0])
            self.update_by_params(self.params)
        else:
            self.params = dict()
            self.prev_onsets = np.empty([0])
            self.prev_offsets = np.empty([0])

    def set_params(self, params, onsets, offsets):
        self.params = params
        self.prev_onsets = onsets
        self.prev_offsets = offsets

    def update_by_params(self, params):
        if 'HighPassFilter' in params:
            # this is added because we used to only have a high pass filter
            # (single slider versus range slider)
            self.filter_boundary = [self.rows - params['HighPassFilter'],
                                    self.rows]
        else:
            self.filter_boundary = params['FrequencyFilter']
        self.bout_range = params['BoutRange']
        self.percent_keep = params['PercentSignalKept']
        self.min_silence = params['MinSilenceDuration']
        self.min_syllable = params['MinSyllableDuration']
        if 'Normalized' in params:
            if params['Normalized'] == 'yes':
                self.normalized = 'down'
            else:
                self.normalized = 'normal'
        else:
            self.normalized = 'normal'

    def reset_params(self, user_signal_thresh, user_min_silence,
                     user_min_syllable, id_min_sil, id_min_syl):
        self.filter_boundary = [0, self.rows]
        self.bout_range = [0, self.cols]
        self.percent_keep = float(user_signal_thresh)
        self.min_silence = float(user_min_silence) / self.ms_pix
        if self.min_silence == 0:
            self.min_silence = id_min_sil
        self.min_syllable = float(user_min_syllable) / self.ms_pix
        if self.min_syllable == 0:
            self.min_syllable = id_min_syl
        self.normalized = 'normal'

    def set_song_params(self, filter_boundary=None, bout_range=None,
                        percent_keep=None, min_silence=None,
                        min_syllable=None, normalized=None,
                        user_signal_thresh=None, user_min_silence=None,
                        user_min_syllable=None,
                        id_min_sil=None, id_min_syl=None):

        if filter_boundary is not None:
            # TODO: this is current fix for range slider,
            # could fix in range_slider_from_google.py instead of here
            # have to check list from range sliders to make sure the first one
            # is less than the second
            # if they are not in ascending order, must reverse the list
            if filter_boundary[1] < filter_boundary[0]:
                filter_boundary.reverse()
            if filter_boundary[0] == self.rows:
                filter_boundary[0] = self.rows - 1
            elif filter_boundary[1] == 0:
                filter_boundary[1] = 1
            elif filter_boundary[0] == filter_boundary[1]:
                filter_boundary[1] = filter_boundary[0] + 1
            self.filter_boundary = filter_boundary

        if bout_range is not None:
            if bout_range[1] < bout_range[0]:
                bout_range.reverse()
            self.bout_range = bout_range

        # next three parameters are set to the default defined by user in
        # landing page if there is no previous value (from chippering before)
        if percent_keep is None:
            self.percent_keep = float(user_signal_thresh)
        else:
            self.percent_keep = percent_keep

        if min_silence is None:
            self.min_silence = float(user_min_silence) / self.ms_pix
            if self.min_silence == 0:
                self.min_silence = id_min_sil
        else:
            self.min_silence = min_silence

        if min_syllable is None:
            self.min_syllable = float(user_min_syllable) / self.ms_pix
            if self.min_syllable == 0:
                self.min_syllable = id_min_syl
        else:
            self.min_syllable = min_syllable
        if normalized is None:
            self.normalized = 'normal'
        else:
            self.normalized = normalized

    def save_dict(self):
        return {
            'FrequencyFilter': self.filter_boundary,
            'BoutRange': self.bout_range,
            'PercentSignalKept': self.percent_keep,
            'MinSilenceDuration': self.min_silence,
            'MinSyllableDuration': self.min_syllable,
            'Normalized': 'yes' if self.normalized == 'down' else 'no'
        }
