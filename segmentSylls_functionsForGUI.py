import numpy as np
#import glob
#import os
#import soundfile as sf
#from ifdvsonogramonly import ifdvsonogramonly
#import matplotlib.pyplot as plt


def high_pass_filter(filter_boundary, sonogram, rows):
    sonogram[filter_boundary:rows, :] = 0
    return sonogram


def threshold(percent_keep, sonogram):
    [rows, cols] = np.shape(sonogram)
    num_elements = rows*cols
    sonogram_binary = sonogram/np.max(sonogram)  # scaling before making binary
    sonogram_vector = np.reshape(sonogram_binary, num_elements, 1)
    sonogram_vector_sorted = np.sort(sonogram_vector)

    # making sonogram_binary actually binary now by keeping some top percentage of the signal
    decimal_keep = percent_keep/100
    top_percent = sonogram_vector_sorted[int(num_elements-round(num_elements*decimal_keep, 0))]  # find value at keep boundary
    sonogram_thresh = np.zeros((rows, cols))
    sonogram_thresh[sonogram_binary < top_percent] = 0
    sonogram_thresh[sonogram_binary > top_percent] = 1

    return sonogram_thresh


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


def toss_sample(toss, i):
    pass

