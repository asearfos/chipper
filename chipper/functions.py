import glob
import os

import numpy as np
import soundfile as sf
from kivy.core.audio import SoundLoader

import chipper.utils as utils
from chipper.ifdvsonogramonly import ifdvsonogramonly


def load_bout_data(f_name):
    """
    Load sonogram and syllable marks (onsets and offsets).
    """
    try:
        song_data = utils.load_gz_p(f_name)
    except:
        song_data = utils.load_old(f_name)
    params = song_data[0]
    onsets = np.asarray(song_data[1]['Onsets'], dtype='int')
    offsets = np.asarray(song_data[1]['Offsets'], dtype='int')
    return params, onsets, offsets


def initial_sonogram(i, files, directory, find_gzips):
    wavfile = files[i]
    # audio data always returned as 2d array
    song1, sample_rate = sf.read(os.path.join(directory, wavfile),
                                 always_2d=True)
    sound = SoundLoader.load(os.path.join(directory, wavfile))

    song1 = song1[:, 0]  # make files mono

    if find_gzips:
        # check if there is a corresponding gzip from a previous run
        zip_file = glob.glob(os.path.split(os.path.split(directory)[0])[0] +
                             '/**/' + 'SegSyllsOutput_' + wavfile.replace(
            '.wav', '') + '.gzip', recursive=True)
    else:
        zip_file = []

    if zip_file:
        # if there is corresponding zip file, open and use the saved parameters
        params, prev_onsets, prev_offsets = load_bout_data(zip_file[0])
    else:
        params = []
        prev_onsets = np.empty([0])
        prev_offsets = np.empty([0])

    # make spectrogram binary, divide by max value to get 0-1 range
    sonogram, millisecondsPerPixel, hertzPerPixel = ifdvsonogramonly(song1,
                                                                     sample_rate,
                                                                     1024,
                                                                     1010,
                                                                     2)
    [rows, cols] = sonogram.shape
    sonogram_padded = np.zeros((rows, cols + 300))
    # padding for window to start
    sonogram_padded[:, 150:cols + 150] = sonogram

    return sound, sonogram_padded, millisecondsPerPixel, hertzPerPixel, \
           params, prev_onsets, prev_offsets


def frequency_filter(filter_boundary, sonogram):
    rows = sonogram.shape[0]
    sonogram[(rows - int(filter_boundary[0])):rows, :] = 0  # high pass filter
    sonogram[0:(rows-int(filter_boundary[1])), :] = 0  # low pass filter
    return sonogram


def normalize_amplitude(sonogram):
    rows = sonogram.shape[0]

    # sliding window average of amplitude
    amplitude_vector = np.squeeze(np.sum(sonogram, axis=0))
    amplitude_average_vector = np.zeros((len(amplitude_vector), 1))

    for f in range(0, np.size(amplitude_vector)):
        # index to start window -> first one of array, check if the index is
        # outside the bounds of the data (negative index)
        vecstart = max(0, f - 500)
        # index to end window -> the last one of the array
        # if the index is outside the bounds of the data (too large of index)
        # (not really sure if I need this since an index outside automatically
        # just goes to end and does not throw errow in Python)
        # else have to add one in python since it is not inclusive
        vecend = len(amplitude_vector) if f + 500 > len(amplitude_vector) \
            else f + 501
        amplitude_average_vector[f] = np.mean(amplitude_vector[vecstart:vecend])

    # use average amplitude to rescale and increase low amplitude sections
    amplitude_average_vector_scaled = amplitude_average_vector / max(
        amplitude_average_vector)
    divide_matrix = np.tile(np.transpose(amplitude_average_vector_scaled),
                            (rows, 1))

    scaled_sonogram = sonogram / divide_matrix
    return scaled_sonogram


def threshold_image(top_threshold, scaled_sonogram):
    percentile = np.percentile(scaled_sonogram, 100-top_threshold)
    sonogram_thresh = np.zeros(scaled_sonogram.shape)
    sonogram_thresh[scaled_sonogram > percentile] = 1

    return sonogram_thresh


def initialize_onsets_offsets(sonogram_thresh):
    rows = sonogram_thresh.shape[0]

    # collapse matrix to one row by summing columns
    # (gives total signal over time)
    sum_sonogram = sum(sonogram_thresh)
    sum_sonogram_scaled = (sum_sonogram / max(sum_sonogram) * rows)

    # create a vector that equals 1 when amplitude exceeds threshold
    # and 0 when it is below
    # threshold: must have more than 4 voxels of signal at a particular time
    high_amp = sum_sonogram_scaled > 4
    high_amp = [int(x) for x in high_amp]
    high_amp[0] = 0
    high_amp[-1] = 0

    # add one so that the onsets are the first column with signal and offsets
    # are the first column after signal. (for analysis: this will keep the
    # durations correct when subtracting and python indexing correct for
    # syll-images)
    onsets = np.where(np.diff(high_amp) == 1)[0] + 1
    offsets = np.where(np.diff(high_amp) == - 1)[0] + 1

    silence_durations = [onsets[i] - offsets[i - 1]
                         for i in range(1, len(onsets))]

    return onsets, offsets, silence_durations, sum_sonogram_scaled


def set_min_silence(min_silence, onsets, offsets, silence_durations):
    syllable_onsets = []
    syllable_offsets = []

    # keep first onsets
    syllable_onsets.append(onsets[0])

    # check if you keep onsets and offsets around the silences based on
    # silence threshold
    for j in range(len(silence_durations)):
        if silence_durations[j] > min_silence:
            syllable_onsets.append(onsets[j+1])
            syllable_offsets.append(offsets[j])

    # keep last offset
    syllable_offsets.append(offsets[-1])

    return syllable_onsets, syllable_offsets


def set_min_syllable(min_syllable, syllable_onsets, syllable_offsets):
    syllable_onsets = np.asarray(syllable_onsets)
    syllable_offsets = np.asarray(syllable_offsets)

    for j in range(len(syllable_offsets)):
        # sets minimum syllable size
        if syllable_offsets[j] - syllable_onsets[j] < min_syllable:
            syllable_offsets[j] = 0
            syllable_onsets[j] = 0

    # remove zeros after correcting for syllable size
    syllable_onsets = syllable_onsets[syllable_onsets != 0]
    syllable_offsets = syllable_offsets[syllable_offsets != 0]

    return syllable_onsets, syllable_offsets


def crop(bout_range, syllable_onsets, syllable_offsets):
    [beginning, ending] = bout_range
    syllable_onsets = syllable_onsets[np.logical_and(syllable_onsets >=
                                                     beginning,
                                                     syllable_onsets <=
                                                     ending)]
    syllable_offsets = syllable_offsets[np.logical_and(syllable_offsets >=
                                                       beginning,
                                                       syllable_offsets <=
                                                       ending)]

    return syllable_onsets, syllable_offsets










