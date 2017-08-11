import numpy as np
import matplotlib as plt
#import scipy.io as sp


#s = np.genfromtxt("C:/Users/abiga/Box Sync/Abigail_Nicole/SongAnalysis/song1mat.txt", delimiter='\n', usecols=0, dtype='float')

#sp.io.loadmat('C:\Users\abiga\Box Sync\Abigail_Nicole\SongAnalysis\song1_testingPython')


def ifdvsonogramonly(s, SAMPLING, N, OVERLAP, sigma, ZOOMT, ZOOMF, TL, FL):
    t = np.arange(-N/2+1, N/2+1, 1)

    sigma = (sigma/1000)*SAMPLING
    w = np.exp(-(t/sigma)**2)

    # Found Fs default in matlab is 1 (for spectrogram) and 2 for specgram and in python it is 2
    [q, frequencies, t] = plt.mlab.specgram(s, NFFT=N, Fs=1, window=w, noverlap=OVERLAP, mode='complex') + np.spacing(1)
    sonogram = q
    sonogram = abs(np.flipud(sonogram))
    return sonogram


