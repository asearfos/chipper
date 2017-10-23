import json
import numpy as np
import gzip
import pandas as pd
import os
import time
import glob
from scipy.ndimage.measurements import label as label2
from skimage.measure import label, regionprops
from skimage.color import label2rgb
from matplotlib import pyplot as plt
import matplotlib.transforms as tx


class SyllableAnalysis(object):
    def __init__(self, filepath):

        # file names
        dirname, basename = os.path.split(filepath)
        file_name = os.path.splitext(basename)[0]
        output_path = dirname + "/AnalysisOutput_" + time.strftime("%Y%m%d_T%H%M%S") + '/'

        # load data
        self.onsets, self.offsets, self.threshold_sonogram, self.millisecondsPerPixel, self.hertzPerPixel = \
            self.load_bout_data(dirname, basename)

        # fig, ax = plt.subplots()
        # ax.imshow(self.threshold_sonogram)
        # syllable_marks = np.append(self.onsets, self.offsets)
        # ymin = np.zeros(len(syllable_marks))
        # ymax = 513
        # ax.vlines(syllable_marks, ymin=ymin, ymax=ymax, colors='m', linewidth=0.5)
        # plt.show()
        # # print('sonogram size', self.threshold_sonogram.shape)

        # run analysis
        syllable_durations, num_syllables, bout_stats = self.get_bout_stats()
        syllable_stats = self.get_syllable_stats(syllable_durations, num_syllables)
        freq_range_upper, freq_range_lower, note_stats = self.get_note_stats(num_syllables)
        freq_stats = self.get_freq_stats(freq_range_upper, freq_range_lower)

        # write output
        final_output = self.update_dict([bout_stats, syllable_stats, note_stats, freq_stats])
        self.output_bout_data(output_path, file_name, final_output)

        super(SyllableAnalysis, self).__init__()

    """ 
    Load sonogram and syllable marks (onsets and offsets).
    """
    def load_bout_data(self, dirname, basename):
        song_data = []
        with gzip.open(os.path.join(dirname, basename), 'rb') as fin:
            for line in fin:
                json_line = json.loads(line, encoding='utf-8')
                song_data.append(json_line)
            fin.close()

        onsets = np.asarray(song_data[1]['Onsets'], dtype='int')
        offsets = np.asarray(song_data[1]['Offsets'], dtype='int')
        threshold_sonogram = np.asarray(song_data[2]['Sonogram'])
        millisecondsPerPixel = np.asarray(song_data[3]['timeAxisConversion'])
        hertzPerPixel = np.asarray(song_data[3]['freqAxisConversion'])
        return onsets, offsets, threshold_sonogram, millisecondsPerPixel, hertzPerPixel

    """ 
    Write output.
    """
    def output_bout_data(self, output_path, file_name, output_dict):
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        df_output = pd.DataFrame.from_dict(output_dict, orient='index')
        df_output.index.name = 'FileName'
        df_output.columns = [file_name]
        df_output.to_csv((output_path + 'AnalysisOutput_' + file_name + '.txt'), sep="\t")

    """
    General methods
    """
    def get_basic_stats(self, durations, data_type, units):
        stats = {'largest_' + data_type + units: max(durations),
                 'smallest_' + data_type + units: min(durations),
                 'avg_' + data_type + units: np.mean(durations),
                 'std_' + data_type + units: np.std(durations, ddof=1)}
        return stats

    def update_dict(self, dictionaries):
        new_dict = {}
        for d in dictionaries:
            new_dict.update(d)
        return new_dict

    """ 
    Analyze Bout: use onsets and offsets to get basic bout information (algebraic calcs)
    """
    def get_bout_stats(self):
        syllable_durations = self.offsets - self.onsets

        syllable_durations_scaled = syllable_durations*self.millisecondsPerPixel
        silence_durations_scaled = [self.onsets[i] - self.offsets[i-1] for i in range(1, len(self.onsets))]*self.millisecondsPerPixel
        bout_duration_scaled = (self.offsets[-1] - self.onsets[0])*self.millisecondsPerPixel

        num_syllables = len(syllable_durations)
        num_syllables_per_bout_duration = num_syllables/bout_duration_scaled

        song_stats = {'bout_duration(ms)': bout_duration_scaled,
                      'num_syllables': num_syllables,
                      'num_syllable_per_bout_duration(1/ms)': num_syllables_per_bout_duration}
        basic_syllable_stats = self.get_basic_stats(syllable_durations_scaled, 'syllable_duration', '(ms)')
        basic_silence_stats = self.get_basic_stats(silence_durations_scaled, 'silence_duration', '(ms)')
        bout_stats = self.update_dict([song_stats, basic_syllable_stats, basic_silence_stats])

        return syllable_durations, num_syllables, bout_stats

    """
    Analyze syllables: find unique syllables, syllable pattern, and stereotypy
    """
    def calc_max_correlation(self):
        sonogram_self_correlation = np.zeros(len(self.onsets))
        for j in range(len(self.onsets)):
            start = self.onsets[j]
            stop = self.offsets[j]
            sonogram_self_correlation[j] = sum(sum(self.threshold_sonogram[:, start:stop]*self.threshold_sonogram[:,
                                                                                          start:stop]))
        return sonogram_self_correlation

    def calc_syllable_correlation(self, a, b, shift_factor, min_length, max_overlap):
        syllable_correlation = []
        for m in range(shift_factor + 1):
            syll_1 = self.threshold_sonogram[:, self.onsets[a]:(self.onsets[a] + min_length)]
            syll_2 = self.threshold_sonogram[:, (self.onsets[b] + m):(self.onsets[b] + min_length + m)]
            syllable_correlation.append((sum(sum(syll_1*syll_2))/max_overlap)*100)

            # print('onset', self.onsets[b], 'offset', self.offsets[b])
            # print('corrd', self.onsets[b] + m, (self.onsets[b] + min_length + m))
            #
            # if m > shift_factor-2:
            #     fig, ax = plt.subplots()
            #     ax.imshow(self.threshold_sonogram)
            #     ax.vlines((self.onsets[b] + min_length + m), ymin=0, ymax=513, colors='m', linewidth=0.5)
            #     plt.show()

        return syllable_correlation

    def get_sonogram_correlation(self, syllable_durations, corr_thresh=50):
        sonogram_self_correlation = self.calc_max_correlation()

        sonogram_correlation = np.zeros((len(self.onsets), len(self.onsets)))

        for j in range(len(self.onsets)):
            for k in range(len(self.onsets)):

                if j > k:  # do not want to fill the second half of the diagonal matrix
                    continue

                max_overlap = max(sonogram_self_correlation[j], sonogram_self_correlation[k])

                shift_factor = np.array(abs(syllable_durations[j]-syllable_durations[k]))

                if syllable_durations[j] < syllable_durations[k]:
                    min_length = syllable_durations[j]
                    syllable_correlation = self.calc_syllable_correlation(j, k, shift_factor, min_length, max_overlap)
                else:  # will be if k is shorter than j or they are equal
                    min_length = syllable_durations[k]
                    syllable_correlation = self.calc_syllable_correlation(k, j, shift_factor, min_length, max_overlap)

                # fill both upper and lower diagonal of symmetric matrix
                sonogram_correlation[j, k] = max(syllable_correlation)
                sonogram_correlation[k, j] = max(syllable_correlation)

        sonogram_correlation_binary = np.zeros(sonogram_correlation.shape)
        sonogram_correlation_binary[sonogram_correlation > corr_thresh] = 1
        return sonogram_correlation, sonogram_correlation_binary

    def find_syllable_pattern(self, sonogram_correlation_binary):
        # get syllable pattern
        syllable_pattern = np.zeros(len(sonogram_correlation_binary), 'int')
        for j in range(len(sonogram_correlation_binary)):
            syllable_pattern[j] = np.nonzero(sonogram_correlation_binary[:, j])[0][0]

        # check syllable pattern --> should be no new number that is smaller than it's index (ex: 12333634 --> the 4
        # should be a 3 but didn't match up enough; know this since 4 < pos(4) = 8)
        syllable_pattern_checked = np.zeros(syllable_pattern.shape, 'int')
        for j in range(len(syllable_pattern)):
            if syllable_pattern[j] < j:
                syllable_pattern_checked[j] = syllable_pattern[syllable_pattern[j]]
            else:
                syllable_pattern_checked[j] = syllable_pattern[j]

        return syllable_pattern_checked

    def calc_syllable_stereotypy(self, sonogram_correlation, syllable_pattern_checked):
        syllable_stereotypy = np.zeros(len(sonogram_correlation))
        for j in range(len(sonogram_correlation)):
            x_syllable_locations = np.where(syllable_pattern_checked == j)[0]  # locations of all like syllables
            # initialize arrays
            x_syllable_correlations = np.zeros([len(syllable_pattern_checked), len(syllable_pattern_checked)])
            if len(x_syllable_locations) > 1:
                for k in range(len(x_syllable_locations)):
                    for h in range(len(x_syllable_locations)):
                        if k > h:  # fill only the lower triangle (not upper and not diagonal) so that similarities aren't double counted when taking the mean later
                            x_syllable_correlations[k, h] = sonogram_correlation[x_syllable_locations[k],
                                                                                 x_syllable_locations[h]]
            syllable_stereotypy[j] = np.nanmean(x_syllable_correlations[x_syllable_correlations != 0])

        return syllable_stereotypy

    def get_syllable_stats(self, syllable_durations, num_syllables, corr_thresh=50):
        # get syllable correlations for entire sonogram
        sonogram_correlation, sonogram_correlation_binary = self.get_sonogram_correlation(syllable_durations,
                                                                                          corr_thresh)

        # get syllable pattern
        syllable_pattern_checked = self.find_syllable_pattern(sonogram_correlation_binary)

        # find unique syllables
        num_unique_syllables = len(np.unique(syllable_pattern_checked))
        num_syllables_per_num_unique = num_syllables / num_unique_syllables

        # determine how often the next syllable is the same as the previous syllable (for chippies, should be one
        # less than number of syllables in the bout)
        sequential_rep1 = len(np.where(np.diff(syllable_pattern_checked) == 0)[0])/(len(syllable_pattern_checked)-1)

        # determine syllable stereotypy
        syllable_stereotypy = self.calc_syllable_stereotypy(sonogram_correlation, syllable_pattern_checked)
        mean_syllable_stereotypy = np.nanmean(syllable_stereotypy)
        std_syllable_stereotypy = np.nanstd(syllable_stereotypy, ddof=1)

        syllable_stats = {'num_unique_syllables': num_unique_syllables,
                          'num_syllables_per_num_unique': num_syllables_per_num_unique,
                          'syllable_pattern': syllable_pattern_checked,
                          'sequential_repetition': sequential_rep1,
                          'syllable_stereotypy': syllable_stereotypy,
                          'mean_syllable_stereotypy': mean_syllable_stereotypy,
                          'std_syllable_stereotypy': std_syllable_stereotypy}
        return syllable_stats

    """
    Analysis of notes: num of notes and categorization; also outputs freq ranges of each note
    """
    def get_notes(self):
        labeled_sonogram, num_notes = label(self.threshold_sonogram, return_num=True, connectivity=1)
                                                                        # ^connectivity 1=4 or 2=8(include diagonals)
        props = regionprops(labeled_sonogram)

        # labeled_sonogram2, num_notes2 = label2(self.threshold_sonogram)

        # # image_label_overlay = label2rgb(labeled_sonogram, image=self.threshold_sonogram)
        # imgplot = plt.imshow(labeled_sonogram, cmap='spectral')
        # # imgplot = plt.imshow(self.threshold_sonogram)
        # plt.colorbar()
        # # imgplot.set_cmap('nipy_spectral')
        # plt.show()
        #
        # plt.imshow(labeled_sonogram2)
        # plt.colorbar()
        # plt.show()
        # plt.title('ndimage')

        return num_notes, props

    def get_note_stats(self, num_syllables):
        num_notes, props = self.get_notes()
        num_notes_updated = num_notes  # initialize, will be altered if the "note" is too small (<60 pixels)

        # stats per note
        freq_range_upper = []
        freq_range_lower = []
        note_length = []

        # # note stats per bout
        # num_flat = 0
        # num_upsweeps = 0
        # num_downsweeps = 0
        # num_parabolas = 0

        for j in range(num_notes):
            # note_ycoords = []  # clear/initialize for each note

            # use only the part of the matrix with the note
            sonogram_one_note = props[j].filled_image

            if np.size(sonogram_one_note) <= 60:  # check the note is large enough to be a note and not just noise
                note_length.append(0)  # place holder
                num_notes_updated -= 1
                # print('not a note')
            else:
                # use bounding box of the note (note, indexing is altered since python starts with 0 and we want to
                # convert rows to actual frequency)
                min_row, min_col, max_row, max_col = props[j].bbox
                freq_range_upper.append(min_row)  # min row is inclusive (first row with labeled section)
                freq_range_lower.append(max_row)  # max row is not inclusive (first zero row after the labeled section)

                note_length.append(np.shape(sonogram_one_note)[1])
                #
                # # fit quadratic to notes
                # for i in range(note_length[j]):
                #     note_ycoords.append(np.mean(np.nonzero(sonogram_one_note[:, i])[0]))
                # note_xcoords = np.arange(0, note_length[j])
                # poly = np.polyfit(note_xcoords, note_ycoords, deg=2)
                # a = poly[0]
                # b = poly[1]
                # x_vertex = -b/(2*a)  # gives x position of max or min of quadratic
                # # print('original', poly)
                #
                # # # new package
                # # import numpy.polynomial.polynomial as poly
                # # coefs = poly.polyfit(note_xcoords, note_ycoords, 2)
                # # # print('new poly', coefs)
                # # x_new = np.linspace(note_xcoords[0], note_xcoords[-1], num=len(note_xcoords)*10)
                # # ffit = poly.polyval(x_new, coefs)
                # # # plt.scatter(note_xcoords, note_ycoords)
                # # # plt.plot(x_new, ffit)
                # # # plt.imshow(sonogram_one_note)
                # # # plt.show()
                #
                # # classify shape of note
                # if np.isclose(a, 0, rtol=9e-02, atol=9e-02):  # check if the note is linear
                #     if np.isclose(b, 0, rtol=9e-02, atol=9e-02):
                #         num_flat += 1
                #         # print('is flat')
                #     elif b > 0:  # b is the slope if the poly is actually linear
                #         num_upsweeps += 1
                #         # print('is upsweep')
                #     else:
                #         num_downsweeps += 1
                #         # print('is downsweep')
                # # now categorize non-linear notes
                # elif x_vertex < .2*note_length[j]:
                #     if a > 0:
                #         num_upsweeps += 1
                #     else:
                #         num_downsweeps += 1
                # elif x_vertex > .8*note_length[j]:
                #     if a > 0:
                #         num_downsweeps += 1
                #     else:
                #         num_upsweeps += 1
                # else:  # the vertex is not within the first or last 20% of the note
                #     num_parabolas += 1

        # collect stats into dictionaries for output
        note_length_array = np.asarray(note_length)
        note_counts = {'num_notes': num_notes_updated,
                       'num_notes_per_syll': num_notes_updated/num_syllables}
        basic_note_stats = self.get_basic_stats(note_length_array[note_length_array != 0], 'note_duration', '(ms)')
        # freq_stats = self.convert_freq(freq_range_upper, freq_range_lower)

        # note_categories = {'num_flat': num_flat/num_notes_updated, 'num_upsweeps': num_upsweeps/num_notes_updated,
        #                    'num_downsweeps': num_downsweeps/num_notes_updated, 'num_parabolas':
        #                        num_parabolas/num_notes_updated}
        # note_categories = {'num_flat': num_flat, 'num_upsweeps': num_upsweeps,
        #                    'num_downsweeps': num_downsweeps, 'num_parabolas':
        #                        num_parabolas}

        note_stats = self.update_dict([note_counts, basic_note_stats])
        return freq_range_upper, freq_range_lower, note_stats

    """
    Analysis of frequencies: general frequency stats and frequency modulation stats
    """
    def get_freq_stats(self, freq_range_upper, freq_range_lower):
        rows = np.shape(self.threshold_sonogram)[0]

        avg_upper_freq = np.mean(freq_range_upper)
        avg_lower_freq = np.mean(freq_range_lower) - 1  # must subtract 1 since freq_range_lower is exclusive
        # note: max freq is min row; min freq is max row --> python matrix indexes starting at 0 (highest freq)
        max_freq = min(freq_range_upper)
        min_freq = max(freq_range_lower) - 1  # must subtract 1 since freq_range_lower is exclusive
        overall_freq_range = abs(max_freq-min_freq) + 1  # add one back so difference is accurate (need min_freq
        # exclusive)

        avg_upper_freq_scaled = (rows-avg_upper_freq)*self.hertzPerPixel
        avg_lower_freq_scaled = (rows-avg_lower_freq)*self.hertzPerPixel
        max_freq_scaled = (rows-max_freq)*self.hertzPerPixel
        min_freq_scaled = (rows-min_freq)*self.hertzPerPixel
        overall_freq_range_scaled = overall_freq_range*self.hertzPerPixel

        freq_stats = {
                'avg_upper_freq(Hz)': avg_upper_freq_scaled,
                'avg_lower_freq(Hz)': avg_lower_freq_scaled,
                'max_freq(Hz)': max_freq_scaled,
                'min_freq(Hz)': min_freq_scaled,
                'overall_freq_range(Hz)': overall_freq_range_scaled
        }

        freq_modulation_per_note = abs(np.asarray(freq_range_upper) - np.asarray(freq_range_lower))*self.hertzPerPixel
        basic_freq_stats = self.get_basic_stats(freq_modulation_per_note, 'freq_modulation', '(Hz)')

        freq_stats = self.update_dict([freq_stats, basic_freq_stats])

        return freq_stats

# part that actually calls/runs code
# # filepath = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\white crowned sparrows for ' \
# #            'testing\OneBout\Output_20171004_T141722\output_b1s white crowned sparrow 66722amp.gzip'
# filepath_newOnOff = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\white crowned sparrows for ' \
#                     'testing\OneBout\SeqSyllsOutput_20171013_T164506\SegSyllsOutput_b1s white crowned sparrow 66722amp.gzip'
# filepath_withConversions = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\white crowned sparrows for ' \
#                            'testing\OneBout\SeqSyllsOutput_20171020_T144430\SegSyllsOutput_b1s white crowned sparrow 66722amp.gzip'
#
# SyllableAnalysis(filepath_withConversions)


directory_regRes = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\TestingAxes\ControlChippies' \
           '\SeqSyllsOutput_20171022_T193442/'

directory_doubleRes = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\TestingAxes\ControlChippies' \
              '\SeqSyllsOutput_20171022_T215611/'


# files = [os.path.basename(i) for i in glob.glob(directory_regRes + '*.gzip')]
files = glob.glob(directory_doubleRes + '*.gzip')

for f in files:
    SyllableAnalysis(f)

































