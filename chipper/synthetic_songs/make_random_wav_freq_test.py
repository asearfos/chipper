import numpy as np
import math
from random import *
from scipy.signal import chirp
import matplotlib.pyplot as plt
from chipper.ifdvsonogramonly import ifdvsonogramonly
import scipy.io.wavfile
import csv
import soundfile as sf
import glob
import os
import shutil


def make_syllable(slope, shape, vertex=True, symmetric=False):
    amp_scale = round(uniform(amp_min, amp_max), 2)
    start_freq = randint(freq_min, freq_max)

    if slope == 'flat':
        end_freq =  start_freq
    elif slope == 'up':
        end_freq = randint(start_freq, freq_max)
    else: # slope == 'down'
        end_freq = randint(freq_min, start_freq)

    len_syll = round(uniform(syll_dur_min, syll_dur_max), 2)
    if symmetric:
        t = np.linspace(0, len_syll, sampling_rate*len_syll)
        t = t-(len_syll/2)
    else:
        t = np.linspace(0, len_syll, sampling_rate*len_syll)
    amplitude = np.linspace(1, 1, sampling_rate*len_syll)
    edge = int(round(len(amplitude)*0.4))
    amplitude[0:edge] = np.linspace(0, 1, edge)
    amplitude[len(amplitude)-edge:] = np.linspace(1, 0, edge)
    syll = np.exp(-3*t)*amplitude*amp_scale*chirp(t, start_freq, t[-1], end_freq, shape, vertex_zero=vertex)
    return amp_scale, start_freq, end_freq, len_syll, syll


def make_silence():
    silence_len = round(uniform(sil_dur_min, sil_dur_max), 2)
    sil = 0  # not sure what this is for
    silence_time = np.linspace(0, silence_len, sampling_rate*silence_len)
    silence = np.sin(0.000001 * silence_time)
    # silence = np.sin(2 * math.pi * sil * silence_time)
    return silence_len, silence


def add_noise(signal, signal_info, noise_file):
    noise, rate = sf.read(noise_file)
    y_noise = signal + noise[:len(signal)]
    with open(signal_info, 'a', newline='') as info:
        writer = csv.writer(info)
        writer.writerow(['Signal Amplitude:', max(signal)])
        writer.writerow(['Noise Amplitude:', max(noise)])
    return y_noise

"""
create random songs
"""
# folder = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/SyntheticSongs/SyntheticSongs_py_amp100"
# baseFileName = 'SyntheticSong_py_amp100_'
#
# sampling_rate = 44100
#
# syll_dur_min = 0.1
# syll_dur_max = 0.9
#
# sil_dur_min = 0.01
# sil_dur_max = 0.5
#
# freq_min = 1000
# freq_max = 10000
#
# amp_min = 1/50*100
# amp_max = 100*100
#
# all_amp_scales = []
# all_start_freq = []
# all_end_freq = []
# all_syll_len = []
# all_silence_len = []
#
# syllables_types = [['flat', 'linear', True, False], ['up', 'linear', True, False], ['down', 'linear', True, False],
#                    ['up', 'quadratic', True, False], ['up', 'quadratic', False, False],
#                    ['down', 'quadratic', True, False], ['down', 'quadratic', False, False],
#                    ['up', 'quadratic', True, True],
#                    ['up', 'logarithmic', True, False], ['down', 'logarithmic', True, False]]
#
#
# for i in range(0, 50):
#     fullFileName = folder + "/" + baseFileName + str(i+1)
#     print(fullFileName)
#
#     total_length = 0
#     all_signal = np.empty(0)
#     for type in syllables_types:
#         slope, shape, vertex, symm = type
#
#         silence_len, silence = make_silence()
#         amp, start, stop, syll_len, syll = make_syllable(slope, shape, vertex, symm)
#
#         total_length += (silence_len + syll_len)
#         all_signal = np.concatenate((all_signal, silence, syll))
#
#         all_amp_scales.append(amp)
#         all_start_freq.append(start)
#         all_end_freq.append(stop)
#         all_syll_len.append(syll_len)
#         all_silence_len.append(silence_len)
#
#     # add one more silence to the end
#     silence_len, silence = make_silence()
#     all_silence_len.append(silence_len)
#     total_length += silence_len
#     all_signal = np.concatenate((all_signal, silence))
#
#     t = np.linspace(0, total_length, sampling_rate*total_length)
#
#     y = all_signal
#
#     if len(t) > len(y):
#         # print('t > y')
#         y = np.pad(y, (0, len(t)-len(y)), mode='constant', constant_values=0)
#     elif len(t) < len(y):
#         # print('t < y', len(y)-len(t))
#         t = np.pad(t, (0, len(y)-len(t)), mode='constant', constant_values=0)
#
#     # print(len(t))
#     # print(len(y))
#     # print(all_amp_scales)
#
#     y = np.asarray(y, dtype=np.int16)
#     scipy.io.wavfile.write(fullFileName + '.wav', sampling_rate, y)
#
#     with open(fullFileName + '.csv', 'w', newline='') as file:
#         filewriter = csv.writer(file, delimiter=',')
#         filewriter.writerow(['Amplitude Scales:', all_amp_scales])
#         filewriter.writerow(['Starting Frequencies:', all_start_freq])
#         filewriter.writerow(['Ending Frequencies:', all_end_freq])
#         filewriter.writerow(['Syllable Durations:', all_syll_len])
#         filewriter.writerow(['Silence Durations:', all_silence_len])
#         file.close()


"""
add white noise
"""
song_folder = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/SyntheticSongs/SyntheticSongs_py_amp100"
synthetic_songs = glob.glob(song_folder + '/*.wav')
# noiseFileName = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/SyntheticSongs/WhiteNoiseTracks/WhiteNoise_1" \
#                 ".wav"
noiseFileName = "C:/Users/abiga\Box Sync\Abigail_Nicole\ChipperPaper\SyntheticSongs/NaturalNoiseTracks" \
                "\S4A06622_20180722_170100_clip.wav"
save_folder = os.path.dirname(song_folder) + '/' + os.path.basename(song_folder) + '_' + os.path.splitext(os.path.basename(
    noiseFileName))[0]
os.mkdir(save_folder)

for i in synthetic_songs:
    name = os.path.splitext(os.path.basename(i))[0]
    srcpath = os.path.splitext(i)[0] + '.csv'
    dstpath = save_folder + '/' + name + '_' + os.path.splitext(os.path.basename(noiseFileName))[0] + '.csv'
    shutil.copy(srcpath, dstpath)
    song, rate = sf.read(i)
    song_with_noise = add_noise(song, dstpath, noiseFileName)
    scipy.io.wavfile.write(save_folder + '/' + name + os.path.splitext(os.path.basename(noiseFileName))[0] + '.wav',
                           rate, song_with_noise)



# # plot the signal and spectrogram
# plt.figure()
# plt.plot(t, y, 'b-')
# plt.show()
#
# sonogram, __, __ = ifdvsonogramonly(y, sampling_rate, 1024, 1010, 2)
#
# plt.figure()
# [rows, cols] = np.shape(sonogram)
# print(rows, cols)
# plt.imshow(np.log(sonogram+3),
#            cmap='hot',
#            extent=[0, cols, 0, rows],
#            aspect='auto')
# plt.show()
