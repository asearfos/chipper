import numpy as np
import matplotlib as plt

"""
Remapped sonograms, as described in
Gardner & Magnasco PNAS 2006

For lack of a better name, at the moment, "ifdgram" is the new sonogram

 [s] Signal to be analyzed.
 [SAMPLING] Sampling rate of the signal.
 [N] Number of filters in the filter-bank.
------
 [OVERLAP] Number of samples to overlap in each successive window;

 The number of time points in the final image is proportional to
 length(s)/(N-OVERLAP);
 Higher overlap will result in sharper lines.
------
 [sigma] is the temporal resolution of the analysis in milliseconds.
 N should be larger than 5*SAMPLING*(sigma/1000);

 Choose sigma small to represent sound in a time-like fashion - as a
 series of clicks, or sigma large, to represent sound in a frequency-like
 fashion, as a series of tones. For most signals of interest, intermediate
 values of sigma are best.
-------
 [ZOOMT] sets the temporal resolution of the final image typically ZOOMT=1.
-------
[ZOOMF] sets the resolution of final image in Frequency. Res=ZOOMF*(N/2)
 In contrast to ZOOMT, it is typically useful to set ZOOMF great than one.
------

[TL] temporal locking window in pixels
[FL] frequency locking window in pixels

When the remapping moves a pixel by more than TL, or FL, that pixel
acquires zero weight. For discussion of the locking window, see
Gardner & Magnasco, J. Acoust. Soc. Am. 2005

When these parameters are small (order 1) "stray" points are removed and the lines are sharpened.
If these parameters are too small, lines become too thin, and appear
discontinuous.

Typical parameters: SAMPLING 44100, N=1024, OVERLAP=1010,
sigma=2, ZOOMT=1, ZOOMF=3; FL=5;TL=5
---
 Implementation note:
The best results will come from calculating an ifdgram for many values of
sigma, (.5:.1:3.5) for example, then combining by multiplying together images
with neighboring values of sigma, and adding them all together.
Rational for this is given in Gardner & Magnasco PNAS 2006.
---------------
example: Compute an ifdgram of 100ms of white noise
s=rand(4000,1)-0.5;
[ifdgram,sonogram]=ifdv(s,44100,1024,1020,1,1,1,2,2);
colormap(hot)
imagesc(log(ifdgram+3));
-------
Comment: As in the previous example, log scaling of the ifdgram,
may be optimal for most sounds.
"""

def ifdvsonogramonly(s, SAMPLING, N, OVERLAP, sigma, ZOOMT, ZOOMF, TL, FL):
    t = np.arange(-N/2+1, N/2+1, 1)

    sigma = (sigma/1000)*SAMPLING
    w = np.exp(-(t/sigma)**2)

    # Found Fs default in matlab is 1 (for spectrogram) and 2 for specgram and in python it is 2
    [q, frequencies, t] = plt.mlab.specgram(s, NFFT=N, Fs=1, window=w, noverlap=OVERLAP, mode='complex') + np.spacing(1)  # Gaussian windowed spectrogram
    sonogram = q
    sonogram = abs(np.flipud(sonogram))  # this is the standard sonogram
    return sonogram


