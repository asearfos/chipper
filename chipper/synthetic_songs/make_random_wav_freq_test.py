import numpy as np
import math
from random import *
from scipy.signal import chirp
import matplotlib.pyplot as plt
from chipper.ifdvsonogramonly import ifdvsonogramonly
import scipy.io.wavfile


def make_syllable(slope, shape, vertex=True, symmetric=False):
    amp_scale = round(uniform(amp_min, amp_max), 2)
    start_freq = randint(freq_min, freq_max)

    if slope == 'flat':
        end_freq =  start_freq
    elif slope == 'up':
        end_freq = randint(start_freq, freq_max)
    else: # slope == 'down'
        end_freq = randint(freq_min, start_freq)

    len_syll = round(uniform(dur_min, dur_max), 2)
    if symmetric:
        t = np.linspace(0, len_syll, np.ceil(sampling_rate*len_syll))
        t = t-(len_syll/2)
    else:
        t = np.linspace(0, len_syll, np.ceil(sampling_rate*len_syll))
    amplitude = np.linspace(1, 1, np.ceil(sampling_rate*len_syll))
    # percent = 0.5*amp_scale
    # print(amp_scale, percent)
    edge = int(round(len(amplitude)*0.4))
    amplitude[0:edge] = np.linspace(0, 1, edge)
    amplitude[len(amplitude)-edge:] = np.linspace(1, 0, edge)
    syll = np.exp(-3*t)*amplitude*amp_scale*chirp(t, start_freq, t[-1], end_freq, shape, vertex_zero=vertex)
    return amp_scale, start_freq, end_freq, len_syll, syll


def make_silence():
    silence_len = round(uniform(dur_min, dur_max), 2)
    sil = 0  # not sure what this is for
    silence_time = np.linspace(0, silence_len, np.ceil(sampling_rate * silence_len))
    silence = np.sin(0.000001 * silence_time)
    # silence = np.sin(2 * math.pi * sil * silence_time)
    return silence_len, silence

folder = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/SyntheticSongs"
baseFileName = 'SyntheticSong_py_amp100_small_pycrop2.wav'
fullFileName = folder + "/" + baseFileName
print(fullFileName)

sampling_rate = 44100

dur_min = 0.05
dur_max = 0.9

freq_min = 1000
freq_max = 10000

amp_min = 1/50*100
amp_max = 100*100

all_amp_scales = []
all_start_freq = []
all_end_freq = []
all_syll_len = []
all_silence_len = []

# silence_len = 0.2
# sil = 0 # not sure what this is for
# silence_time = np.linspace(0, silence_len, np.ceil(sampling_rate*silence_len))
# silence = np.sin(2*math.pi*sil*silence_time)
# # print(type(2*math.pi*sil*silence_time))

syllables_types = [['flat', 'linear', True, False], ['up', 'linear', True, False], ['down', 'linear', True, False],
                   ['up', 'quadratic', True, False], ['up', 'quadratic', False, False],
                   ['down', 'quadratic', True, False], ['down', 'quadratic', False, False],
                   ['up', 'quadratic', True, True],
                   ['up', 'logarithmic', True, False], ['down', 'logarithmic', True, False]]

total_length = 0
all_signal = np.empty(0)
for type in syllables_types:
    slope, shape, vertex, symm = type

    silence_len, silence = make_silence()
    amp, start, stop, syll_len, syll = make_syllable(slope, shape, vertex, symm)

    total_length += (silence_len + syll_len)
    all_signal = np.concatenate((all_signal, silence, syll))

    all_amp_scales.append(amp)
    all_start_freq.append(start)
    all_end_freq.append(stop)
    all_syll_len.append(syll_len)
    all_silence_len.append(silence_len)


# add one more silence to the end
silence_len, silence = make_silence()
all_silence_len.append(silence_len)
total_length += silence_len
all_signal = np.concatenate((all_signal, silence))

t = np.linspace(0, total_length, np.ceil(sampling_rate*total_length))

y = all_signal

if len(t) > len(y):
    print('t > y')
    y = np.pad(y, (0, len(t)-len(y)), mode='constant', constant_values=0)
elif len(t) < len(y):
    print('t < y', len(y)-len(t))
    t = np.pad(t, (0, len(y)-len(t)), mode='constant', constant_values=0)

print(len(t))
print(len(y))

plt.figure()
plt.plot(t, y, 'b-')
plt.show()

y = np.asarray(y, dtype=np.int16)
y = y[4000:-4000]
sonogram, __, __ = ifdvsonogramonly(y, sampling_rate, 1024, 1010, 2)

plt.figure()
[rows, cols] = np.shape(sonogram)
print(rows, cols)
plt.imshow(np.log(sonogram+3), cmap='hot', extent=[0, cols, 0, rows],
                                           aspect='auto')
plt.show()

# y = np.asarray(y, dtype=np.int16)
# scipy.io.wavfile.write(fullFileName, sampling_rate, y)
