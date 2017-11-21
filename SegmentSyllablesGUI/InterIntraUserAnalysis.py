import pandas as pd
import os
import fnmatch
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import numpy as np
from pandas.io.common import EmptyDataError
from itertools import combinations
from scipy import stats

rootdir = 'C:/Users/abiga\Box Sync\SongGUI\ChippingSparrowTestSet_forGUIv10162017'

analysis_list = []
tossed_list = []
for dirName, subFolders, files in os.walk(rootdir):
    for f in files:
        if f.startswith('AnalysisOutput'):
            path = dirName.split('\\')
            user = fnmatch.filter(path, '*Data')
            attempt = fnmatch.filter(path, 'SegSyllsOutput*')
            analysis_list.append(pd.read_table(os.path.join(dirName, f), index_col=False).assign(User=user[0],
                                                                                                 Attempt=attempt[0]))
        if f.startswith('segmentedSyllables_tossed'):
            tossed_path = dirName.split('\\')
            try:
                tossed_list.append(pd.read_table(os.path.join(dirName, f), index_col=False))
            except EmptyDataError:
                pass


"""
Clean up analysis data.
"""
analysis_df = pd.concat(analysis_list)
# go through and alter Attempt to either first or second if there are two file names
# first have to sort and re-index before iterating through df
analysis_df = analysis_df.sort_values(by=['User', 'FileName', 'Attempt']).reset_index(drop=True)
for index, row in analysis_df.iterrows():
    if index == 0:
        pass
    elif analysis_df.loc[index, 'FileName'] == analysis_df.loc[index-1, 'FileName']:
        analysis_df.loc[index-1, 'Attempt'] = 'first'
        analysis_df.loc[index, 'Attempt'] = 'second'
    else:
        pass

# remove any analysis data for single-run file
analysis_df_woSingleAttempts = analysis_df[analysis_df.Attempt.isin(['first', 'second'])]
clean_df = analysis_df_woSingleAttempts.set_index(['User', 'Attempt'])

"""
Clean up tossed file list.
"""
tossed_df = pd.concat(tossed_list).drop_duplicates()
tossed_df['FileName'] = 'SegSyllsOutput_' + tossed_df['FileName'].astype(str)
tossed_df['FileName'] = tossed_df['FileName'].str.replace('.wav', '.gzip')


"""
Remove any files that were tossed for inter analysis. 
"""
inter_df = clean_df
for fn in tossed_df['FileName'].values:
    inter_df = inter_df[inter_df['FileName'] != fn]

# another way to do this without loop
# test = clean_df.loc[(clean_df['FileName'].isin(tossed_df['FileName'].values)) == False, :]
# print('size inter', np.shape(inter_df))
# print('size test', np.shape(test))
#
# print(test.equals(inter_df))

# # remove Nicole's messed up file (think she may have submitted without parsing)
# inter_df = inter_df[inter_df['FileName'] != 'SegSyllsOutput_29804411_b3of5.gzip']

inter_df.sort_index(inplace=True)  # not exactly sure why this has to be done but found solution here:
# https://www.somebits.com/~nelson/pandas-multiindex-slice-demo.html)

"""
Plotting functions and code to print to pdf
"""
def plot_intra(variable):
    fig, axs = plt.subplots(2, 2, sharex='col', sharey='row')
    # plt.gca().axis('equal')
    fig.suptitle(variable, fontsize=8)

    subplot_index = [(0, 0), (0, 1), (1, 0), (1, 1)]
    i = 0

    for username in clean_df.index.levels[0]:
        data1 = clean_df[variable][username]['first'].values
        data2 = clean_df[variable][username]['second'].values
        plt.title(username)

        r, pval = stats.pearsonr(data1, data2)

        if pval < 0.001:
            textstr = '$r=%.4f$\n$pval<0.001$' % r
        else:
            textstr = '$r=%.4f$\n$r\_pval=%.4f$' % (r, pval)

        # axs[subplot_index[i]].scatter(data1, data2, s=10, c='black')
        sns.regplot(x=data1, y=data2, label=username, scatter_kws={'s': 10}, ax=axs[subplot_index[i]])
        axs[subplot_index[i]].set_title(username, fontsize=6)
        axs[subplot_index[i]].set_xlabel('First Attempt', fontsize=6)
        axs[subplot_index[i]].set_ylabel('Second Attempt', fontsize=6)
        axs[subplot_index[i]].tick_params(axis='both', which='major', labelsize=6)
        axs[subplot_index[i]].text(0.05, 0.95, textstr, transform=axs[subplot_index[i]].transAxes, fontsize=6,
                                   verticalalignment='top')

        # add line of equality
        x_min, x_max = axs[subplot_index[i]].get_xlim()
        axs[subplot_index[i]].plot([x_min, x_max], [x_min, x_max], 'k-')

        i += 1

# pdf = PdfPages('C:/Users/abiga\Box '
#                'Sync\SongGUI\ChippingSparrowTestSet_forGUIv10162017/IntraUserAnalysis_LinReg_95CI.pdf')
# for var in clean_df.columns:
#     if clean_df[var].dtype == 'float64' or clean_df[var].dtype == 'int64':
#         plot_intra(var)
#         pdf.savefig()
#         plt.close()
# pdf.close()


def bland_altman_plot(variable):
    data1 = clean_df.xs('first', level='Attempt', axis=0)[variable].values
    data2 = clean_df.xs('second', level='Attempt', axis=0)[variable].values

    mean_data = np.mean([data1, data2], axis=0)  # used if wanting a non-user labled graph
    diff_data = data1-data2
    mean_diff = np.mean(diff_data)
    std_diff = np.std(diff_data, axis=0)

    fig, (ax1, ax2) = plt.subplots(1, 2)

    for username in clean_df.index.levels[0]:
        sub_data1 = clean_df[variable][username]['first'].values
        sub_data2 = clean_df[variable][username]['second'].values
        sub_mean_data = np.mean([sub_data1, sub_data2], axis=0)
        sub_diff_data = sub_data1-sub_data2
        ax1.scatter(sub_mean_data, sub_diff_data, s=10, label=username)

    # ax1.scatter(mean_data, diff_data, s=10, c='black')
    ax1.axhline(mean_diff,                 color='black', linestyle='-')
    ax1.axhline(mean_diff + 1.96*std_diff, color='gray', linestyle='--')
    ax1.axhline(mean_diff - 1.96*std_diff, color='gray', linestyle='--')
    ax1.set_title(variable)
    ax1.set_xlabel('mean_data')
    ax1.set_ylabel('difference Attempt1-Attempt2')
    ax1.legend(fontsize='small')

    ax2.hist(diff_data[~np.isnan(diff_data)])
    ax2.set_xlabel('difference Attempt1-Attempt2')
    ax2.set_ylabel('frequency')


# pdf = PdfPages('C:/Users/abiga\Box '
#                'Sync\SongGUI\ChippingSparrowTestSet_forGUIv10162017/IntraUserAnalysis_BlandAltmanPlots'
#                '.pdf')
# for var in clean_df.columns:
#     if clean_df[var].dtype == 'float64' or clean_df[var].dtype == 'int64':
#         bland_altman_plot(var)
#         # plt.show()
#         pdf.savefig()
#         plt.close()
# pdf.close()


def rank_plots(variable):
    attempt = 'second'
    fig, axs = plt.subplots(2, 3, sharex='col', sharey='row')
    # plt.gca().axis('equal')
    fig.suptitle(variable, fontsize=8)

    subplot_index = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
    i = 0

    for combo in combinations(range(np.size(inter_df.index.levels[0])), 2):
        user1 = inter_df.index.levels[0][combo[0]]
        user2 = inter_df.index.levels[0][combo[1]]
        sorter = inter_df.loc[(user1, attempt), ('FileName', variable)].sort_values(by=variable, axis=0,
                                                                                    )['FileName'].values

        # sort inter_df using the input order from the user1 data sorted in variable
        # inter_df.FileName = inter_df.FileName.astype("category")
        # inter_df.FileName.cat.set_categories(sorter, inplace=True)
        # data2 = inter_df.loc[(user2, attempt), ('FileName', variable)].sort_values(['FileName'])[variable].values

        # create a user2 DataFrame that will have 2 columns - FileName and variable
        # sort this new DataFrame using the order of the FileName column of inter_df after it's sorted by the variable
        user2_df = inter_df.loc[(user2, attempt), ('FileName', variable)]
        user2_df = user2_df.set_index('FileName')
        user2_df = user2_df.reindex(index=sorter)
        user2_df = user2_df.reset_index()

        data1 = inter_df[variable][user1][attempt].sort_values(axis=0).values
        data2 = user2_df[variable].values
        rho, rho_pval = stats.spearmanr(data1, data2)
        r, r_pval = stats.pearsonr(data1, data2)

        if r_pval < 0.001:
            textstr = '$rho=%.4f$\n$r=%.4f$\n$r\_pval<0.001$' % (rho, r)
        else:
            textstr = '$rho=%.4f$\n$r=%.4f$\n$r\_pval=%.4f$' % (rho, r, r_pval)

        # axs[subplot_index[i]].scatter(data1, data2, s=10, c='black')
        sns.regplot(x=data1, y=data2, scatter_kws={'s': 10}, ax=axs[subplot_index[i]])
        axs[subplot_index[i]].set_xlabel(user1, fontsize=6)
        axs[subplot_index[i]].set_ylabel(user2, fontsize=6)
        axs[subplot_index[i]].tick_params(axis='both', which='major', labelsize=6)
        axs[subplot_index[i]].text(0.05, 0.95, textstr, transform=axs[subplot_index[i]].transAxes, fontsize=6,
                verticalalignment='top')

        # add line of equality
        x_min, x_max = axs[subplot_index[i]].get_xlim()
        axs[subplot_index[i]].plot([x_min, x_max], [x_min, x_max], 'k-')

        i += 1


pdf = PdfPages('C:/Users/abiga\Box '
               'Sync\SongGUI\ChippingSparrowTestSet_forGUIv10162017/InterUserAnalysis_RankPlots_secondAttempt'
               '.pdf')
for var in inter_df.columns:
    if inter_df[var].dtype == 'float64' or inter_df[var].dtype == 'int64':
        rank_plots(var)
    # plt.show()
        pdf.savefig()
        plt.close()
pdf.close()






