import numpy as np
import matplotlib as plt
#import scipy.io as sp

#just here for reference for parameters
#ifdvsonogramonly(song1,44100,1024,1010,2,1,3,5,5);

#for testing
#SAMPLING = 44100
#N = 1024
#OVERLAP = 1010
#sigma = 2
#s = np.genfromtxt("C:/Users/abiga/Box Sync/Abigail_Nicole/SongAnalysis/song1mat.txt", delimiter='\n', usecols=0, dtype='float')

#sp.io.loadmat('C:\Users\abiga\Box Sync\Abigail_Nicole\SongAnalysis\song1_testingPython')


def ifdvsonogramonly(s, SAMPLING, N, OVERLAP, sigma, ZOOMT, ZOOMF, TL, FL):
    t = np.arange(-N/2+1, N/2+1, 1)

    sigma = (sigma/1000)*SAMPLING
    w = np.exp(-(t/sigma)**2)

# I think Fs default in matlab is 1 and in python it is 2
    [q,frequencies,t] = plt.mlab.specgram(s, NFFT=N, Fs=1, window=w, noverlap=OVERLAP, mode='complex') + np.spacing(1)
    sonogram = q
    sonogram = abs(np.flipud(sonogram))
    return sonogram


