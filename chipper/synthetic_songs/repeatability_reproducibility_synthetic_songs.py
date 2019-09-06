import os
import pandas as pd
import csv
from glob import glob
import numpy as np

import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

os.chdir("C:/Users/abiga\Box Sync\Abigail_Nicole\ChipperPaper\SyntheticSongs/")

"""
Read in Chipper outputs
"""

nicole_data_try1 = pd.read_csv(
    "ChipperedByNicole_Try1ForPaper_basedOn20190528\AnalysisOutput_20190902_T175722_songsylls.txt", sep="\t")
nicole_data_try1['User'] = 'Nicole'
nicole_data_try1['Try'] = 1

nicole_data_try2 = pd.read_csv(
    "ChipperedByNicole_Try3ForPaper\AnalysisOutput_20190903_T215612_songsylls.txt", sep="\t")
nicole_data_try2['User'] = 'Nicole'
nicole_data_try2['Try'] = 2

megan_data_try1 = pd.read_csv("ChipperedByMegan_Try1ForPaper_basedOn20190528\AnalysisOutput_20190902_T150653_songsylls.txt", sep="\t")
megan_data_try1['User'] = 'Megan'
megan_data_try1['Try'] = 1

megan_data_try2 = pd.read_csv("ChipperedByMegan_Try2ForPaper\AnalysisOutput_20190902_T165647_songsylls.txt", sep="\t")
megan_data_try2['User'] = 'Megan'
megan_data_try2['Try'] = 2


chipper_data = pd.concat([nicole_data_try1, megan_data_try1, nicole_data_try2, megan_data_try2], ignore_index=True)
chipper_data['FileName'].replace(regex=True, inplace=True, to_replace=r'\SegSyllsOutput_', value=r'')
chipper_data['FileName'].replace(regex=True, inplace=True, to_replace=r'.gzip', value=r'')

"""
Plotting
"""

variables = [['bout_duration(ms)', 'song_duration', 1000],
             ['avg_syllable_duration(ms)', 'avg_syll_dur', 1000],
             ['avg_silence_duration(ms)', 'avg_sil_dur', 1000],
             ['num_syllables', 'num_sylls', 1],
             ['avg_sylls_freq_modulation(Hz)', 'avg_syll_freq_mod', 1],
             ['avg_sylls_upper_freq(Hz)', 'avg_syll_max_freq', 1],
             ['avg_sylls_lower_freq(Hz)', 'avg_syll_min_freq', 1],
             ['max_sylls_freq(Hz)', 'max_syll_freq', 1],
             ['min_sylls_freq(Hz)', 'min_syll_freq', 1]
             ]

order = ['None',
         'WhiteNoise001',
         'WhiteNoise01',
         'S4A0662220180409161600clip',
         'S4A0662220180722170100clip']
"""
Reproducibility (using Megan Try 1 and Nicole Try 1)
"""
data1 = chipper_data[chipper_data['Try'] == 1]

for var in variables:
    data_for_reprod = data1.pivot(index='FileName', columns='User',
                                  values=var[0])
    data_for_reprod = data_for_reprod.rename_axis('FileName').reset_index()
    data_for_reprod['Noise'] = data_for_reprod.apply(lambda row:
                                               ''.join(row.FileName.split('_')[
                                                       4:]),
                                                     axis=1)
    data_for_reprod['Noise'].replace(inplace=True, to_replace=r'', value=r'None')
    data_for_reprod = data_for_reprod[data_for_reprod.Noise.isin(order)]

    fig = plt.figure(figsize=(8.27, 8.27))
    my_dpi = 96
    sns.set(style='white')
    sns.set_style("ticks")

    g = sns.scatterplot(x=data_for_reprod['Nicole'], y=data_for_reprod['Megan'],
                        hue=data_for_reprod['Noise'], hue_order=order,
                        palette=sns.color_palette("RdPu", 5),
                        linewidth=0.25,
                        edgecolor='k')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    x0, x1 = g.get_xlim()
    y0, y1 = g.get_ylim()
    lims = [min(x0, y0), max(x1, y1)]
    g.plot(lims, lims, ':k')

    plt.savefig('PlotsForPaper/NicoleVSMegan/' + var[0] + '.pdf', type='pdf',
                dpi=fig.dpi,
                bbox_inches='tight', transparent=True)

    plt.close()
    # plt.show()

"""
Repeatability (using Nicole Try 1 and Nicole Try 2)
"""

data2 = chipper_data[chipper_data['User'] == 'Nicole']

for var in variables:
    data_for_repeat = data2.pivot(index='FileName', columns='Try',
                                  values=var[0])
    data_for_repeat = data_for_repeat.rename_axis('FileName').reset_index()
    data_for_repeat['Noise'] = data_for_repeat.apply(lambda row:
                                               ''.join(row.FileName.split('_')[
                                                       4:]),
                                                     axis=1)
    data_for_repeat['Noise'].replace(inplace=True, to_replace=r'', value=r'None')
    data_for_repeat = data_for_repeat[data_for_repeat.Noise.isin(order)]

    fig = plt.figure(figsize=(8.27, 8.27))
    my_dpi = 96
    sns.set(style='white')
    sns.set_style("ticks")

    g = sns.scatterplot(x=data_for_repeat[1], y=data_for_repeat[2],
                        hue=data_for_repeat['Noise'], hue_order=order,
                        palette=sns.color_palette("RdPu", 5),
                        linewidth=0.25,
                        edgecolor='k')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    x0, x1 = g.get_xlim()
    y0, y1 = g.get_ylim()
    lims = [min(x0, y0), max(x1, y1)]
    g.plot(lims, lims, ':k')

    plt.savefig('PlotsForPaper/NicoleVSNicole_T13/' + var[0] + '.pdf',
                type='pdf',
                dpi=fig.dpi,
                bbox_inches='tight', transparent=True)

    plt.close()
    # plt.show()
