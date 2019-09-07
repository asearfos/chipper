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


def make_syllable(song_amplitude, slope, shape, vertex=True, symmetric=False):
    # for each syllable pick an amplitude within 30% of the song amplitude
    amp_scale = round(uniform(song_amplitude - song_amplitude*.3, song_amplitude + song_amplitude*.3), 2)
    start_freq = randint(freq_min, freq_max)  # Return ints from discrete uniform dist [low, high)

    if slope == 'flat':
        end_freq = start_freq
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

    # create vector of ones for amplitude
    amplitude = np.linspace(1, 1, sampling_rate*len_syll)
    # define how much of the syllable will be ramping up to full amplitude and back down will be
    edge = int(round(len(amplitude)*0.4))
    # ramp up to full amplitude from 0
    amplitude[0:edge] = np.linspace(0, 1, edge)
    # ramp down from full amplitude to zero
    amplitude[len(amplitude)-edge:] = np.linspace(1, 0, edge)

    # multiply amplitude by exponential decay to decrease amplitude throughout the syllable (to mimic bird sounds)
    syll = np.exp(-3*t)*amplitude*amp_scale*chirp(t, start_freq, t[-1], end_freq, shape, vertex_zero=vertex)
    return amp_scale, start_freq, end_freq, len_syll, syll


def make_silence():
    silence_len = round(uniform(sil_dur_min, sil_dur_max), 2)
    silence_time = np.linspace(0, silence_len, sampling_rate*silence_len)
    silence = np.sin(2 * math.pi * silence_time)
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
folder = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/synthetic_songs/SynSongs_amp100_30p"
baseFileName = 'SynSongs_amp100_30p_'

sampling_rate = 44100

syll_dur_min = 0.1
syll_dur_max = 0.9

sil_dur_min = 0.01
sil_dur_max = 0.5

freq_min = 2000
freq_max = 10000

amp_min = 1*100
amp_max = 100*100

syllables_types = [['flat', 'linear', True, False], ['up', 'linear', True, False], ['down', 'linear', True, False],
                   ['up', 'quadratic', True, False], ['up', 'quadratic', False, False],
                   ['down', 'quadratic', True, False], ['down', 'quadratic', False, False],
                   ['up', 'quadratic', True, True],
                   ['up', 'logarithmic', True, False], ['down', 'logarithmic', True, False]]


for i in range(0, 50):
    fullFileName = folder + "/" + baseFileName + str(i+1)
    print(fullFileName)

    total_length = 0
    all_signal = np.empty(0)

    all_amp_scales = []
    all_start_freq = []
    all_end_freq = []
    all_syll_len = []
    all_silence_len = []

    # randomly set rough amplitude for the song
    song_amp = round(uniform(amp_min, amp_max), 2)

    for type in syllables_types:
        slope, shape, vertex, symm = type

        if type[0] == 'flat':  # don't add a silence before the first syllable
            amp, start, stop, syll_len, syll = make_syllable(song_amp, slope, shape, vertex, symm)
            total_length += syll_len
            all_signal = np.concatenate((all_signal, syll))

            all_amp_scales.append(amp)
            all_start_freq.append(start)
            all_end_freq.append(stop)
            all_syll_len.append(syll_len)
        else:
            silence_len, silence = make_silence()
            amp, start, stop, syll_len, syll = make_syllable(song_amp, slope, shape, vertex, symm)

            total_length += (silence_len + syll_len)
            all_signal = np.concatenate((all_signal, silence, syll))

            all_amp_scales.append(amp)
            all_start_freq.append(start)
            all_end_freq.append(stop)
            all_syll_len.append(syll_len)
            all_silence_len.append(silence_len)

    time = np.linspace(0, total_length, sampling_rate*total_length)

    wavform = all_signal

    if len(time) > len(wavform):
        wavform = np.pad(wavform, (0, len(time)-len(wavform)), mode='constant', constant_values=0)
    elif len(time) < len(wavform):
        time = np.pad(wavform, (0, len(wavform)-len(time)), mode='constant', constant_values=0)

    time = np.pad(time, (10000, 10000), mode='constant', constant_values=0)
    wavform = np.pad(wavform, (10000, 10000), mode='constant', constant_values=0)

    wavform = np.asarray(wavform, dtype=np.int16)
    scipy.io.wavfile.write(fullFileName + '.wav', sampling_rate, wavform)

    with open(fullFileName + '.csv', 'w', newline='') as file:
        filewriter = csv.writer(file, delimiter=',')
        filewriter.writerow(['Amplitude Scales:', all_amp_scales])
        filewriter.writerow(['Starting Frequencies:', all_start_freq])
        filewriter.writerow(['Ending Frequencies:', all_end_freq])
        filewriter.writerow(['Syllable Durations:', all_syll_len])
        filewriter.writerow(['Silence Durations:', all_silence_len])
        file.close()


"""
add noise
"""
song_folder = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/synthetic_songs/SynSongs_amp100_30p"
synthetic_songs = glob.glob(song_folder + '/*.wav')
noiseFileName = "C:/Users/abiga/Box Sync/Abigail_Nicole/ChipperPaper/synthetic_songs/WhiteNoiseTracks/WhiteNoise_0001" \
                ".wav"

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
    scipy.io.wavfile.write(save_folder + '/' + name + '_' + os.path.splitext(os.path.basename(noiseFileName))[0] +
                           '.wav',
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
