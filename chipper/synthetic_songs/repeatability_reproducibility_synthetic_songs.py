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

nicole_data_try1 = pd.read_csv("ChipperedByNicole_v20190528\AnalysisOutput_20190627_T184003.txt", sep="\t")
nicole_data_try1['User'] = 'Nicole'
nicole_data_try1['Try'] = 1

nicole_data_try2 = pd.read_csv("ChipperedByNicole_v20190528\AnalysisOutput_20190627_T184003.txt", sep="\t")
nicole_data_try2['User'] = 'Nicole'
nicole_data_try2['Try'] = 2

megan_data_try1 = pd.read_csv("ChipperedByMegan_v20190528\AnalysisOutput_20190627_T191243.txt", sep="\t")
megan_data_try1['User'] = 'Megan'
megan_data_try1['Try'] = 1

megan_data_try2 = pd.read_csv("ChipperedByMegan_v20190528\AnalysisOutput_20190627_T191243.txt", sep="\t")
megan_data_try2['User'] = 'Megan'
megan_data_try2['Try'] = 2


chipper_data = pd.concat([nicole_data_try1, megan_data_try1, nicole_data_try2, megan_data_try2], ignore_index=True)
chipper_data['FileName'].replace(regex=True, inplace=True, to_replace=r'\SegSyllsOutput_', value=r'')
chipper_data['FileName'].replace(regex=True, inplace=True, to_replace=r'.gzip', value=r'')

chipper_data['Track'] = chipper_data.apply(lambda row:
                                           '_'.join(row.FileName.split('_')[:4]),
                                           axis=1)

chipper_data['Noise'] = chipper_data.apply(lambda row:
                                           ''.join(row.FileName.split('_')[4:]),
                                           axis=1)
chipper_data['Noise'].replace(inplace=True, to_replace=r'', value=r'None')


print(chipper_data.shape)

variables = []
order = []
order = ['None', 'WhiteNoise0001',  'WhiteNoise001', 'S4A0662220180409161600clip', 'WhiteNoise01',
         'S4A0662220180722170100clip', 'WhiteNoise1']

"""
Reproducibility (using Megan Try 1 and Nicole Try 2, all noise levels)
"""
for var in variables:
    fig = plt.figure(figsize=(11.69, 8.27))
    my_dpi = 96
    sns.set(style='white')
    # for i in np.unique(chipper_data.Noise):
    #     data = chipper_data[chipper_data.Noise == i]
    #     g = sns.regplot(x=data[var[0]], y=data[var[1]]*var[2], scatter_kws=dict(alpha=0))
    g = sns.scatterplot(x=chipper_data[var[0]], y=chipper_data[var[1]]*var[2],
                        hue=chipper_data['Noise'], hue_order=order,
                        style=chipper_data['User'], markers=['|', '_'], palette=sns.color_palette("RdPu", 5))
    # plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    x0, x1 = g.get_xlim()
    y0, y1 = g.get_ylim()
    lims = [max(x0, y0), min(x1, y1)]
    g.plot(lims, lims, ':k')

    # plt.savefig('FiguresForCommitteeMtg/' + var[0] + '.pdf', type='pdf', dpi=fig.dpi,
    #             bbox_inches='tight', transparent=True)

    plt.close()
    # plt.show()