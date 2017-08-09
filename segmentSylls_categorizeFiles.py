import numpy as np
import glob
import os
import soundfile as sf
from ifdvsonogramonly import ifdvsonogramonly
import matplotlib.pyplot as plt

# import a directory of wav files
directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"
files = [os.path.basename(i) for i in glob.glob(directory+'*.wav')]

F = len(files) + 1  # not sure if i really need the +1 (if not, then change range of for loop)

# define overarching variables here

# not altered to python yet:
# scrsz = get(0,'ScreenSize')

analyzed_wav_files = []
analyzed_wav_files.append('test.wav')
onset_cells = 1
offset_cells = 1

wavlist = []
for i in range(0, F-1):
    i
    # del sonogram* -------how to do this in python?

    wavfile = files[i]
    song1, sample_rate = sf.read(directory+wavfile, always_2d=True) #audio data always returned as 2d array
    song1 = song1[:, 0]  # make files mono

    wavfile  # not sure if we want this printed or not
    wavlist.append(wavfile)

    test_if_analyzed = wavlist[i] in analyzed_wav_files
    if not test_if_analyzed:
        analyzed_wav_files.append(wavlist[i])
    # char(analyzed_wav_files) # don't think we need this
    file_number = analyzed_wav_files.index(wavlist[i])

    # make spectrogram binary, divide by max value to get 0-1 range
    # sonogram = np.genfromtxt("C:/Users/abiga/Box Sync/Abigail_Nicole/SongAnalysis/sonogram.txt", delimiter='\n', usecols=0, dtype='float') # for testing if function isn't working
    sonogram = ifdvsonogramonly(song1, 44100, 1024, 1010, 2, 1, 3, 5, 5)
    [rows, cols] = np.shape(sonogram)
    sonogram_padded = np.zeros((rows, cols+300))
    sonogram_padded[:, 150:cols+150] = sonogram  # padding for window to start
    sonogram = sonogram_padded

# MAKE THIS A FUNCTION WITH BOUNDARY INPUT
    # high pass filter (get rid of low freq noise)
    sonogram[474:513, :] = 0

    # sliding window average of amplitude
    amplitude_vector = np.squeeze(np.sum(sonogram, axis=0))
    amplitude_average_vector = np.zeros((len(amplitude_vector),1))

    for f in range(0, np.size(amplitude_vector)):
        if f-500 <= 0:  # if the index is outside the bounds of the data (negative index)
            vecstart = 0  # index to start window -> first one of array
        else:
            vecstart = f-500
        if f+500 > len(amplitude_vector):  # if the index is outside the bounds of the data (too large of index) (not really sure if I need this since an index outside automatically just goes to end and does not throw errow in Python)
            vecend = len(amplitude_vector)  # index to end window -> the last one of the array
        else:
            vecend = f+500+1  # have to add one in python since it is not inclusive
        print(vecstart, vecend)
        amplitude_average_vector[f] = np.mean(amplitude_vector[vecstart:vecend])

    # use average amplitude to rescale and increase low amplitude sections
    amplitude_average_vector_scaled = amplitude_average_vector/max(amplitude_average_vector)
    divide_matrix = np.tile(np.transpose(amplitude_average_vector_scaled), (513, 1))

    scaled_sonogram = sonogram/divide_matrix
    sonogram = scaled_sonogram

    # PLOT --> not sure if I will need to position these since it will be in a GUI eventually
    # figure('Position',[1 scrsz(4)/2 scrsz(3) (scrsz(4)/2-60)])
    # %figure('Position',[1 scrsz(4)/2 scrsz(3) (scrsz(4)/2-100)])
    plt.imshow(np.log(sonogram+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')


    [rows, cols] = np.shape(sonogram)  # update since sonogram has now been padded
    num_elements = rows*cols
    sonogram_binary = sonogram/np.max(sonogram)  # scaling before making binary

    # scale sonogram so that some top % is maximized while the rest is set to 0 (thresholding)
    sonogram_vector = np.reshape(sonogram_binary, num_elements, 1)
    sonogram_vector_sorted = np.sort(sonogram_vector)

    # not used currently in the MATLAB code
    # fortypercent = sonogramvectorsorted(round(numelements / 2.5));
    # s40 = ge(sonogrambinary, fortypercent); % ge(A, B) equivalent to A >= B
    # sonogram40 = s40. * sonogrambinary;

    # THRESHOLDING
    # making sonogram_binary actually binary now by keeping some top percentage of the signal
    top_percent = sonogram_vector_sorted[int(num_elements-round(num_elements/57, 0))] # takes top _% off of ranked num_elements
    sonogram_thresh = np.zeros((rows, cols))
    sonogram_thresh[sonogram_binary < top_percent] = 0
    sonogram_thresh[sonogram_binary > top_percent] = 1

    # sonogram summed
    sum_sonogram = sum(sonogram_thresh)
    sum_sonogram_scaled = (sum_sonogram/max(sum_sonogram)*rows)

    if not test_if_analyzed:
        # create a vector that equals 1 when amplitude exceeds threshold and 0 when it is below
        high_amp = sum_sonogram_scaled > 4
        high_amp = [int(x) for x in high_amp]
        high_amp[0] = 0
        high_amp[len(high_amp)-1] = 0
        onsets = np.nonzero(np.diff(high_amp) == 1)
        onsets = np.squeeze(onsets)
        offsets = np.nonzero(np.diff(high_amp) == -1)
        offsets = np.squeeze(offsets)
        offsets2 = np.zeros(len(offsets)+1)
        # push offset index by one because when diff is taken it places it in the element before the zeros
        for j in range(0, len(offsets)):
            offsets2[j+1] = offsets[j]
        offsets2[0] = 1
        onsets = np.append(onsets, len(sum_sonogram_scaled))

        # define silence durations
        silence_durations = np.zeros(len(onsets)-1)
        mean_silence_durations = []
        for j in range(0, len(onsets)-1):
            silence_durations[j] = onsets[j]-offsets2[j]
        mean_silence_durations.append(np.mean(silence_durations))  # different from MATLAB code in that it does not add it to index = file_number; not sure if this will matter

        # define syllable onsets and offsets
        syllable_onsets = np.zeros(len(onsets))
        syllable_offsets = np.zeros(len(onsets))
        for j in range(0, len(silence_durations)):
            if silence_durations[j] > 26:  # sets minimum silence
                syllable_onsets[j] = onsets[j]
                syllable_offsets[j] = offsets2[j]
        syllable_offsets[0] = 0
        syllable_offsets[len(silence_durations)] = offsets2[len(offsets2)-1]

        # remove zeros
        syllable_onsets = syllable_onsets[syllable_onsets != 0]
        syllable_offsets = syllable_offsets[syllable_offsets != 0]
        if syllable_offsets[0] < syllable_onsets[0]:  # make sure there is always first an onset
            np.delete(syllable_offsets, 0)
        for j in range(0, len(syllable_offsets)-1):
            if syllable_offsets[j] - syllable_onsets[j] < 10:  # sets minimum syllable size
                syllable_offsets[j] = 0
                syllable_onsets[j] = 0
        # remove zeros again after correcting for syllable size
        syllable_onsets = syllable_onsets[syllable_onsets != 0]
        syllable_offsets = syllable_offsets[syllable_offsets != 0]

        syllable_marks = np.zeros(len(sum_sonogram_scaled))
        syllable_marks[syllable_onsets.astype(int)] = rows + 30
        syllable_marks[syllable_offsets.astype(int)] = rows + 10

        # PLOT --> need to change to python
        # %draw spectrogram with sumsonogram overlaid
        # figure('Position',[1 50 scrsz(3) (scrsz(4)/2-120)])
        # %figure('Position',[1 50 scrsz(3) (scrsz(4)/2-75)])
        # %figure('Position',[1 scrsz(4)/2 scrsz(3) (scrsz(4)/2-100)])
        # hold on
        # imagesc(log(sonogramthresh+3))
        # set(gca,'YDir', 'reverse')
        # xlim([0 cols])
        # colormap hot
        # plot(syllable_marks,'m-')
        # hold off

        # plot binary sonogram
        plt.imshow(np.log(sonogram_thresh + 3), cmap='hot', extent=[0, cols, 0, rows], aspect='auto')

        # plot onsets and offsets
        indexes = np.squeeze(np.nonzero(syllable_marks))
        ymin = np.zeros(len(indexes))
        ymax = syllable_marks[syllable_marks != 0]
        plt.vlines(indexes, ymin=ymin, ymax=ymax, colors='m')
        plt.show()










