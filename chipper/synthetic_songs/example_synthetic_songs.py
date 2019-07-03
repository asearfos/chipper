import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
from chipper.ifdvsonogramonly import ifdvsonogramonly
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
from matplotlib.backends.backend_pdf import PdfPages
# import seaborn as sns; sns.set()
from matplotlib.ticker import FuncFormatter


os.chdir("C:/Users/abiga\Box Sync\Abigail_Nicole\ChipperPaper\SyntheticSongs/SynSongs")

"""
Load in example songs and make figures
"""

basename = 'SynSongs_amp100_30p'
noise = ['',
         '_S4A06622_20180409_161600_clip',
         '_S4A06622_20180722_170100_clip',
         '_WhiteNoise_0001',
         '_WhiteNoise_001',
         '_WhiteNoise_01',
         '_WhiteNoise_1']

sample = 'SynSongs_amp100_30p_1'

for n in noise:
    song_file = basename + n + '/' + sample + n + '.wav'
    song, rate = sf.read(song_file)
    sonogram, timeAxis_conversion, freqAxis_conversion = ifdvsonogramonly(song,
                                                                          rate,
                                                                          1024,
                                                                          1010.0,
                                                                          2.0)
    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(1, 1, 1)
    # sns.set(style='white')
    [rows, cols] = np.shape(sonogram)
    im = plt.imshow(np.log(sonogram+3),
                    cmap='gray_r',
                    extent=[0, cols, 0, rows],
                    aspect='auto')

    ax.get_xaxis().set_major_formatter(plt.FuncFormatter(
            lambda x, p: "%.2f" % (x*timeAxis_conversion/1000)))
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(
            lambda x, p: "%.0f" % (x*freqAxis_conversion/1000)))
    plt.tick_params(labelsize=14)
    plt.savefig("C:/Users/abiga\Box Sync\Abigail_Nicole\ChipperPaper\SyntheticSongs\SynSongs\SpectrogramsOfSynSongs\Ex2_SynSongs_amp100_30p_1/" +
                sample + n + '_sonogram' + '.pdf', type='pdf',
                dpi=fig.dpi, bbox_inches='tight',
                transparent=True)
    # plt.show()
