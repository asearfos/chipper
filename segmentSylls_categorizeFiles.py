import numpy as np
import glob
import os
import soundfile as sf
from ifdvsonogramonly import ifdvsonogramonly

# import a directory of wav files
directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"
files = [os.path.basename(i) for i in glob.glob(directory+'*.wav')]

F = len(files) + 1  # not sure if i really need the +1 (if not, then change range of for loop)

# define overarching variables here

# not altered to python yet:
# scrsz = get(0,'ScreenSize')

analyzed_wav_files = 'test.wav'
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
    wavlist[i] = wavfile

    # not sure if I want to use this
        # test_if_analyzed = strmatch(wavlist{i}, analyzed_wav_files, 'exact')
        # if isempty(test_if_analyzed) == 1
        #    analyzed_wav_files = [analyzed_wav_files wavlist{i}];
        # end
        # char(analyzed_wav_files)
        # file_number = strmatch(wavlist{i}, analyzed_wav_files, 'exact')

    # make spectrogram binary, divide by max value to get 0-1 range
#### for now load in sonogram from .mat file to test until function is working
    # sonogram = np.genfromtxt("C:/Users/abiga/Box Sync/Abigail_Nicole/SongAnalysis/sonogram.txt", delimiter='\n', usecols=0, dtype='float')
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
            vecend = f+500
        amplitude_average_vector[f] = np.mean(amplitude_vector[vecstart:vecend])

    # use average amplitude to rescale and increase low amplitude sections
    amplitude_average_vector_scaled = amplitude_average_vector/max(amplitude_average_vector)
    divide_matrix = np.tile(np.transpose(amplitude_average_vector_scaled),(513,1))

    scaled_sonogram = sonogram/divide_matrix
    sonogram = scaled_sonogram

    # PLOT --> need to change to python
    # figure('Position',[1 scrsz(4)/2 scrsz(3) (scrsz(4)/2-60)])
    # %figure('Position',[1 scrsz(4)/2 scrsz(3) (scrsz(4)/2-100)])
    # imagesc(log(sonogram+3))
    # %colormap jet

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

