import numpy as np
import glob
import os
import soundfile as sf
from ifdvsonogramonly import ifdvsonogramonly
#import matplotlib.pyplot as plt


def initialize(directory):
    files = [os.path.basename(i) for i in glob.glob(directory+'*.wav')]
    F = len(files) + 1  # not sure if i really need the +1 (if not, then change range of for loop)

    # # define overarching variables here
    # analyzed_wav_files = []
    # analyzed_wav_files.append('test.wav')
    #
    # wavlist = []
    return files, F


def initial_sonogram(i, files, directory):
    wavfile = files[i]
    song1, sample_rate = sf.read(directory + wavfile, always_2d=True)  # audio data always returned as 2d array
    song1 = song1[:, 0]  # make files mono

    # wavfile  # not sure if we want this printed or not
    # wavlist.append(wavfile)
    #
    # test_if_analyzed = wavlist[i] in analyzed_wav_files
    # if not test_if_analyzed:
    #     analyzed_wav_files.append(wavlist[i])
    # # char(analyzed_wav_files) # don't think we need this
    # file_number = analyzed_wav_files.index(wavlist[i])

    # make spectrogram binary, divide by max value to get 0-1 range
    sonogram = ifdvsonogramonly(song1, 44100, 1024, 1010, 2, 1, 3, 5, 5)
    [rows, cols] = np.shape(sonogram)
    sonogram_padded = np.zeros((rows, cols + 300))
    sonogram_padded[:, 150:cols + 150] = sonogram  # padding for window to start
    sonogram = sonogram_padded
    return sonogram


def high_pass_filter(filter_boundary, sonogram):
    [rows, cols] = np.shape(sonogram)
    sonogram[filter_boundary:rows, :] = 0
    return sonogram


def normalize_amplitude(sonogram):
    [rows, cols] = np.shape(sonogram)

    # sliding window average of amplitude
    amplitude_vector = np.squeeze(np.sum(sonogram, axis=0))
    amplitude_average_vector = np.zeros((len(amplitude_vector), 1))

    for f in range(0, np.size(amplitude_vector)):
        if f - 500 <= 0:  # if the index is outside the bounds of the data (negative index)
            vecstart = 0  # index to start window -> first one of array
        else:
            vecstart = f - 500
        if f + 500 > len(
                amplitude_vector):  # if the index is outside the bounds of the data (too large of index) (not really sure if I need this since an index outside automatically just goes to end and does not throw errow in Python)
            vecend = len(amplitude_vector)  # index to end window -> the last one of the array
        else:
            vecend = f + 500 + 1  # have to add one in python since it is not inclusive
        amplitude_average_vector[f] = np.mean(amplitude_vector[vecstart:vecend])

    # use average amplitude to rescale and increase low amplitude sections
    amplitude_average_vector_scaled = amplitude_average_vector / max(amplitude_average_vector)
    divide_matrix = np.tile(np.transpose(amplitude_average_vector_scaled), (rows, 1))

    scaled_sonogram = sonogram / divide_matrix
    return scaled_sonogram


def threshold(percent_keep, scaled_sonogram):
    [rows, cols] = np.shape(scaled_sonogram)
    num_elements = rows*cols
    sonogram_binary = scaled_sonogram/np.max(scaled_sonogram)  # scaling before making binary
    sonogram_vector = np.reshape(sonogram_binary, num_elements, 1)
    sonogram_vector_sorted = np.sort(sonogram_vector)

    # making sonogram_binary actually binary now by keeping some top percentage of the signal
    decimal_keep = percent_keep/100
    top_percent = sonogram_vector_sorted[int(num_elements-round(num_elements*decimal_keep, 0))]  # find value at keep boundary
    sonogram_thresh = np.zeros((rows, cols))
    sonogram_thresh[sonogram_binary < top_percent] = 0
    sonogram_thresh[sonogram_binary > top_percent] = 1

    return sonogram_thresh


def initialize_onsets_offsets(sonogram_thresh):
    [rows, cols] = np.shape(sonogram_thresh)

    # sonogram summed
    sum_sonogram = sum(sonogram_thresh)  # collapse matrix to one row by summing columns (gives total signal over time)
    sum_sonogram_scaled = (sum_sonogram / max(sum_sonogram) * rows)

    #if not test_if_analyzed:

    # create a vector that equals 1 when amplitude exceeds threshold and 0 when it is below
    high_amp = sum_sonogram_scaled > 4
    high_amp = [int(x) for x in high_amp]
    high_amp[0] = 0
    high_amp[len(high_amp) - 1] = 0
    onsets = np.nonzero(np.diff(high_amp) == 1)
    onsets = np.squeeze(onsets)
    offsets = np.nonzero(np.diff(high_amp) == -1)
    offsets = np.squeeze(offsets)
    offsets2 = np.zeros(len(offsets) + 1)
    # push offset index by one because when diff is taken it places it in the element before the zeros
    for j in range(0, len(offsets)):
        offsets2[j + 1] = offsets[j]
    offsets2[0] = 1
    onsets = np.append(onsets, len(sum_sonogram_scaled))

    # define silence durations
    silence_durations = np.zeros(len(onsets) - 1)
    mean_silence_durations = []
    for j in range(0, len(onsets) - 1):
        silence_durations[j] = onsets[j] - offsets2[j]
    mean_silence_durations.append(np.mean(
        silence_durations))  # different from MATLAB code in that it does not add it to index = file_number; not sure if this will matter
    return onsets, offsets2, silence_durations, sum_sonogram_scaled, rows

def set_min_silence(min_silence, onsets, offsets2, silence_durations):
    syllable_onsets = np.zeros(len(onsets))
    syllable_offsets = np.zeros(len(onsets))
    for j in range(0, len(silence_durations)):
        if silence_durations[j] > min_silence:  # sets minimum silence
            syllable_onsets[j] = onsets[j]
            syllable_offsets[j] = offsets2[j]
    syllable_offsets[0] = 0
    syllable_offsets[len(silence_durations)] = offsets2[len(offsets2) - 1]

    return syllable_onsets, syllable_offsets


def set_min_syllable(min_syllable, syllable_onsets, syllable_offsets, sum_sonogram_scaled, rows):
    syllable_onsets = syllable_onsets[syllable_onsets != 0]
    syllable_offsets = syllable_offsets[syllable_offsets != 0]
    if syllable_offsets[0] < syllable_onsets[0]:  # make sure there is always first an onset
        np.delete(syllable_offsets, 0)
    for j in range(0, len(syllable_offsets) - 1):
        if syllable_offsets[j] - syllable_onsets[j] < min_syllable:  # sets minimum syllable size
            syllable_offsets[j] = 0
            syllable_onsets[j] = 0
    # remove zeros again after correcting for syllable size
    syllable_onsets = syllable_onsets[syllable_onsets != 0]
    syllable_offsets = syllable_offsets[syllable_offsets != 0]

    syllable_marks = np.zeros(len(sum_sonogram_scaled))
    syllable_marks[syllable_onsets.astype(int)] = rows + 30
    syllable_marks[syllable_offsets.astype(int)] = rows + 10

    return syllable_marks


def toss_sample(i):
    i = i+1
    return i

