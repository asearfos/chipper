import numpy as np
# import bottleneck as bn
import glob
import os
import soundfile as sf
from chipper.ifdvsonogramonly import ifdvsonogramonly
#import matplotlib.pyplot as plt
import chipper.utils as utils
import gzip


def initialize(directory):
    files = [os.path.basename(i) for i in glob.glob(directory+'*.wav')]
    # look for a gzip from a previous run
    return files

def load_bout_data(f_name):
    """
    Load sonogram and syllable marks (onsets and offsets).
    """
    try:
        song_data = utils.load_gz_p(f_name)
    except:
        song_data = utils.load_old(f_name)
    params = song_data[0]
    return params

def initial_sonogram(i, files, directory):
    wavfile = files[i]
    song1, sample_rate = sf.read(directory + wavfile, always_2d=True)  # audio data always returned as 2d array
    song1 = song1[:, 0]  # make files mono

    # check if there is a corresponding gzip from a previous run
    zip_file = glob.glob(directory + '/SegSyllsOutput*/' + 'SegSyllsOutput_' + wavfile.replace('.wav', '') + '.gzip')

    if zip_file:
        # if there is corresponding zip file, open and use the saved parameters
        params = load_bout_data(zip_file[0])
    else:
        params = []

    # make spectrogram binary, divide by max value to get 0-1 range
    sonogram, millisecondsPerPixel, hertzPerPixel = ifdvsonogramonly(song1, 44100, 1024, 1010, 2)
    [rows, cols] = sonogram.shape
    sonogram_padded = np.zeros((rows, cols + 300))
    sonogram_padded[:, 150:cols + 150] = sonogram  # padding for window to start

    return sonogram_padded, millisecondsPerPixel, hertzPerPixel, params


def high_pass_filter(filter_boundary, sonogram):
    rows = sonogram.shape[0]
    sonogram[filter_boundary:rows, :] = 0
    return sonogram


def normalize_amplitude(sonogram):
    [rows, cols] = sonogram.shape

    # sliding window average of amplitude
    amplitude_vector = np.squeeze(np.sum(sonogram, axis=0))
    amplitude_average_vector = np.zeros((len(amplitude_vector), 1))

    for f in range(0, np.size(amplitude_vector)):
        vecstart = max(0, f-500)  # index to start window -> first one of array, check if the index is outside the bounds of the data (negative index)
        # index to end window -> the last one of the array
        # if the index is outside the bounds of the data (too large of index) (not really sure if I need this since an index outside automatically just goes to end and does not throw errow in Python)
        # else have to add one in python since it is not inclusive
        vecend = len(amplitude_vector) if f + 500 > len(amplitude_vector) else f + 501
        amplitude_average_vector[f] = np.mean(amplitude_vector[vecstart:vecend])

    # use average amplitude to rescale and increase low amplitude sections
    amplitude_average_vector_scaled = amplitude_average_vector / max(amplitude_average_vector)
    divide_matrix = np.tile(np.transpose(amplitude_average_vector_scaled), (rows, 1))

    scaled_sonogram = sonogram / divide_matrix
    return scaled_sonogram


def threshold_image(top_threshold, scaled_sonogram):
    percentile = np.percentile(scaled_sonogram, 100-top_threshold)
    sonogram_thresh = np.zeros(scaled_sonogram.shape)
    sonogram_thresh[scaled_sonogram > percentile] = 1

    return sonogram_thresh


def initialize_onsets_offsets(sonogram_thresh):
    [rows, cols] = sonogram_thresh.shape

    # sonogram summed
    sum_sonogram = sum(sonogram_thresh)  # collapse matrix to one row by summing columns (gives total signal over time)
    sum_sonogram_scaled = (sum_sonogram / max(sum_sonogram) * rows)

    # create a vector that equals 1 when amplitude exceeds threshold and 0 when it is below
    high_amp = sum_sonogram_scaled > 4  # threshold: must have more than 4 voxels of signal at a particular time to keep
    high_amp = [int(x) for x in high_amp]
    high_amp[0] = 0
    high_amp[-1] = 0

    # add one so that the onsets are the first column with signal and offsets are the first column after signal
    # (for analysis: this will keep the durations correct when subtracting and python indexing correct for syll-images)
    onsets = np.where(np.diff(high_amp) == 1)[0] + 1
    offsets = np.where(np.diff(high_amp) == - 1)[0] + 1

    silence_durations = [onsets[i] - offsets[i-1] for i in range(1, len(onsets))]

    return onsets, offsets, silence_durations, sum_sonogram_scaled


def set_min_silence(min_silence, onsets, offsets, silence_durations):
    syllable_onsets = []
    syllable_offsets = []

    # keep first onsets
    syllable_onsets.append(onsets[0])

    # check if you keep onsets and offsets around the silences based on silence threshold
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
        if syllable_offsets[j] - syllable_onsets[j] < min_syllable:  # sets minimum syllable size
            syllable_offsets[j] = 0
            syllable_onsets[j] = 0

    # remove zeros after correcting for syllable size
    syllable_onsets = syllable_onsets[syllable_onsets != 0]
    syllable_offsets = syllable_offsets[syllable_offsets != 0]

    return syllable_onsets, syllable_offsets


def crop(bout_range, syllable_onsets, syllable_offsets):
    [beginning, ending] = bout_range
    syllable_onsets = syllable_onsets[np.logical_and(syllable_onsets >= beginning, syllable_onsets <= ending)]
    syllable_offsets = syllable_offsets[np.logical_and(syllable_offsets >= beginning, syllable_offsets <= ending)]

    return syllable_onsets, syllable_offsets










