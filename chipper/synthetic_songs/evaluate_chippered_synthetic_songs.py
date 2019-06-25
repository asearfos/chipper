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

""""
Read in Synthetic Real Values
"""
all_csv_files = []
for path, subdir, files in os.walk('SynSongs/SynSongs_amp100_30p'):
    for file in glob(os.path.join(path, '*.csv')):
        all_csv_files.append(file)

real_values = pd.DataFrame()
for f in all_csv_files:
    d = {}
    with open(f) as file:
        reader = csv.reader(file)
        for r in reader:
            key = r[0][:-1]
            value = np.array([float(i) for i in r[1][1:-1].split(',')])
            d.update({'Track': [f]})
            d.update({key: [value]})
            data = pd.DataFrame.from_dict(d)
        real_values = real_values.append(data, ignore_index=True)

real_values = real_values[['Track', 'Amplitude Scales', 'Starting Frequencies',
                           'Ending Frequencies', 'Syllable Durations', 'Silence Durations']]
real_values.columns = [c.replace(' ', '_') for c in real_values.columns]
real_values['Track'] = real_values.apply(lambda row:
                                         row.Track.split('\\')[-1].split('.csv')[0],
                                         axis=1)

# print(sum(real_values.Syllable_Durations[0]))

real_values['song_duration'] = real_values.apply(lambda row:
                                                 sum(row.Syllable_Durations) + sum(row.Silence_Durations),
                                                 axis=1)
real_values['avg_syll_dur'] = real_values.apply(lambda row:
                                                np.mean(row.Syllable_Durations),
                                                axis=1)
real_values['avg_sil_dur'] = real_values.apply(lambda row:
                                               np.mean(row.Silence_Durations),
                                               axis=1)
real_values['num_sylls'] = real_values.apply(lambda row:
                                             len(row.Syllable_Durations),
                                             axis=1)
real_values['avg_syll_freq_mod'] = real_values.apply(lambda row:
                                                     sum(abs(row.Starting_Frequencies -
                                                             row.Ending_Frequencies)) / row.num_sylls,
                                                     axis=1)
real_values['avg_syll_max_freq'] = real_values.apply(lambda row:
                                                     sum(np.maximum(row.Starting_Frequencies,
                                                         row.Ending_Frequencies)) / row.num_sylls,
                                                     axis=1)
real_values['avg_syll_min_freq'] = real_values.apply(lambda row:
                                                     sum(np.minimum(row.Starting_Frequencies,
                                                         row.Ending_Frequencies)) / row.num_sylls,
                                                     axis=1)
real_values['max_syll_freq'] = real_values.apply(lambda row:
                                                 max(np.concatenate([row.Starting_Frequencies,
                                                     row.Ending_Frequencies])),
                                                 axis=1)
real_values['min_syll_freq'] = real_values.apply(lambda row:
                                                 min(np.concatenate([row.Starting_Frequencies,
                                                     row.Ending_Frequencies])),
                                                 axis=1)



"""
Read in Chipper outputs
"""

nicole_data = pd.read_csv("ChipperedByNicole_v20190528\AnalysisOutput_20190601_T113055.txt", sep="\t")
nicole_data['User'] = 'Nicole'
megan_data = pd.read_csv("ChipperedByMegan_v20190528\AnalysisOutput_20190601_T102822.txt", sep="\t")
megan_data['User'] = 'Megan'

chipper_data = pd.concat([nicole_data, megan_data], ignore_index=True)
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


"""
Merge tables using Name (from real values) and Track (from chipper data)
"""

combined_data = chipper_data.merge(real_values, how='left', on='Track')
combined_data = combined_data[combined_data.Noise != 'WhiteNoise0001']
combined_data = combined_data[combined_data.Noise != 'WhiteNoise1']

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

order = ['None', 'WhiteNoise001', 'S4A0662220180409161600clip', 'WhiteNoise01',
         'S4A0662220180722170100clip']
for var in variables:
    fig = plt.figure(figsize=(11.69, 8.27))
    my_dpi = 96
    sns.set(style='white')
    g = sns.scatterplot(x=combined_data[var[0]], y=combined_data[var[1]]*var[2],
                        hue=combined_data['Noise'], hue_order=order,
                        style=combined_data['User'], markers=['|', '_'], palette=sns.color_palette("RdPu", 5))
    # plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    x0, x1 = g.get_xlim()
    y0, y1 = g.get_ylim()
    lims = [max(x0, y0), min(x1, y1)]
    g.plot(lims, lims, ':k')

    plt.savefig('FiguresForCommitteeMtg/' + var[0] + '.pdf', type='pdf', dpi=fig.dpi,
                bbox_inches='tight', transparent=True)

    plt.close()
    # plt.show()
