import numpy as np
import math
from random import *
from scipy.signal import chirp
import matplotlib.pyplot as plt
from chipper.ifdvsonogramonly import ifdvsonogramonly



def make_syllable(slope, shape, vertex=True):
    amp_scale = round(uniform(amp_min, amp_max), 2)
    start_freq = randint(freq_min, freq_max)

    if slope == 'flat':
        end_freq =  start_freq
    elif slope == 'up':
        end_freq = randint(start_freq, freq_max)
    else: # slope == 'down'
        end_freq = randint(freq_min, start_freq)

    len_syll = round(uniform(dur_min, dur_max), 2)
    t = np.linspace(0, len_syll, np.ceil(sampling_rate*len_syll))
    amplitude = np.linspace(1, 1, np.ceil(sampling_rate*len_syll))
    amplitude[0:2000] = np.linspace(0, 1, 2000)
    amplitude[len(amplitude)-2000:] = np.linspace(1, 0, 2000)
    syll = np.exp(-3*t)*amplitude*amp_scale*chirp(t, start_freq, t[-1], end_freq, shape)
    return amp_scale, start_freq, end_freq, len_syll, syll

folder = ""
baseFileName = 'SyntheticSong1.wav'
fullFileName = folder + "/" + baseFileName
print(fullFileName)

sampling_rate = 44100

dur_min = 0.01
dur_max = 0.9

freq_min = 1000
freq_max = 10000

amp_min = 1/50
amp_max = 100

all_amp_scales = []
all_start_freq = []
all_end_freq = []

silence_len = 0.2
sil = 0 # not sure what this is for
silence_time = np.linspace(0, silence_len, np.ceil(sampling_rate*silence_len))
silence = np.sin(2*math.pi*sil*silence_time)
# print(type(2*math.pi*sil*silence_time))

amp, start, stop, syll_len, syll = make_syllable('up', 'linear')

total_length = silence_len + syll_len + silence_len

t = np.linspace(0, total_length, np.ceil(sampling_rate*total_length))

all_signal = np.concatenate((silence, syll, silence))

y = all_signal

print(len(t))
print(len(y))

plt.figure()
plt.plot(t, y, 'b-')
plt.show()

sonogram, __, __ = ifdvsonogramonly(y, sampling_rate, 1024, 1010, 2)

plt.figure()
[rows, cols] = np.shape(sonogram)
print(rows, cols)
plt.imshow(np.log(sonogram+3), cmap='hot', extent=[0, cols, 0, rows],
                                           aspect='auto')
plt.show()