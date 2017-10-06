import json
import numpy as np
import gzip
import pandas as pd
import os
import time
# from scipy.ndimage.measurements import label
from skimage.measure import label, regionprops
from skimage.color import label2rgb
from matplotlib import pyplot as plt


class SyllableAnalysis(object):
    def __init__(self, filepath):

        # file names
        dirname, basename = os.path.split(filepath)
        file_name = os.path.splitext(basename)[0]
        output_path = dirname + "/AnalysisOutput_" + time.strftime("%Y%m%d_T%H%M%S") + '/'

        # load data
        self.onsets, self.offsets, self.threshold_sonogram = self.load_bout_data(dirname, basename)

        # run analysis
        syllable_durations, num_syllables, bout_stats = self.get_bout_stats()
        syllable_stats = self.get_syllable_stats(syllable_durations, num_syllables)
        note_stats = self.get_note_stats()

        # write output
        final_output = self.update_dict([bout_stats, syllable_stats, note_stats])
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
                # json_bytes = fin.read()
                # json_str = json_bytes.decode('utf-8')
                # print(type(json_str))
                # song_data = json.loads(json_bytes, encoding='utf-8')
            fin.close()

        onsets = np.asarray(song_data[1]['Onsets'], dtype='int')
        offsets = np.asarray(song_data[1]['Offsets'], dtype='int')
        threshold_sonogram = np.asarray(song_data[2]['Sonogram'])
        return onsets, offsets, threshold_sonogram

    """ 
    Write output.
    """
    def output_bout_data(self, output_path, file_name, output_dict):
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        df_output = pd.DataFrame.from_dict(output_dict, orient='index')
        df_output.index.name = 'FileName'
        df_output.to_csv((output_path + 'AnalysisOutput_' + file_name + '.txt'), sep="\t")

    """
    General methods
    """
    def get_basic_stats(self, durations, data_type):
        stats = {'longest_' + data_type: max(durations), 'shortest_' + data_type: min(durations), 'avg_' + data_type:
            np.mean(durations), 'std_' + data_type: np.std(durations)}
        return stats

    def update_dict(self, dictionaries):
        new_dict = {}
        for d in dictionaries:
            new_dict.update(d)
        return new_dict

    """ 
    Algebraic calculations: use onsets and offsets to get basic bout information
    """
    def get_bout_stats(self):
        syllable_durations = self.offsets - self.onsets
        silence_durations = [self.onsets[i] - self.offsets[i-1] for i in range(1, len(self.onsets))]
        bout_duration = self.offsets[-1] - self.onsets[0]
        num_syllables = len(syllable_durations)
        num_syllables_per_bout_duration = num_syllables/bout_duration
        song_stats = {'bout_duration': bout_duration, 'num_syllables': num_syllables,
                      'num_syllable_per_bout_duration': num_syllables_per_bout_duration}
        basic_syllable_stats = self.get_basic_stats(syllable_durations, 'syllable')
        basic_silence_stats = self.get_basic_stats(silence_durations, 'silence')
        bout_stats = self.update_dict([song_stats, basic_syllable_stats, basic_silence_stats])

        return syllable_durations, num_syllables, bout_stats

    """
    Analyse syllables: find unique syllables, syllable pattern, and stereotypy
    """
    def max_correlation(self):
        sonogram_self_correlation = np.zeros(len(self.onsets))
        for j in range(len(self.onsets)):
            start = self.onsets[j]
            stop = self.offsets[j]
            sonogram_self_correlation[j] = sum(sum(self.threshold_sonogram[:, start:stop]*self.threshold_sonogram[:,
                                                                                          start:stop]))
        return sonogram_self_correlation

    def get_sonogram_correlation(self, sonogram_self_correlation, syllable_durations, corr_thresh=50):
        sonogram_correlation = np.zeros((len(self.onsets), len(self.onsets)))

        for j in range(len(self.onsets)):
            for k in range(len(self.onsets)):

                if j > k:  # do not want to fill the second half of the diagonal matrix
                    continue

                maxoverlap = max(sonogram_self_correlation[j], sonogram_self_correlation[k])

                shift_factor = abs(syllable_durations[j]-syllable_durations[k])

                if syllable_durations[j] < syllable_durations[k]:
                    min_length = syllable_durations[j]
                    syllable_correlation = self.get_syllable_correlation(j, k, shift_factor, min_length, maxoverlap)
                else:  # will be if k is shorter than j or they are equal
                    min_length = syllable_durations[k]
                    syllable_correlation = self.get_syllable_correlation(k, j, shift_factor, min_length, maxoverlap)

                # fill both upper and lower diagonal of symmetric matrix
                sonogram_correlation[j, k] = max(syllable_correlation)
                sonogram_correlation[k, j] = max(syllable_correlation)

        # print(np.shape(sonogram_correlation), (sonogram_correlation.transpose() == sonogram_correlation).all())

        sonogram_correlation_binary = np.zeros(sonogram_correlation.shape)
        sonogram_correlation_binary[sonogram_correlation > corr_thresh] = 1
        return sonogram_correlation, sonogram_correlation_binary

    def get_syllable_correlation(self, a, b, shift_factor, min_length, maxoverlap):
        syllable_correlation = []
        for m in range(shift_factor+1):
            syll_1 = self.threshold_sonogram[:, self.onsets[a]:(self.onsets[a] + min_length)]
            syll_2 = self.threshold_sonogram[:, (self.onsets[b] + m):(self.onsets[b] + min_length + m)]
            syllable_correlation.append((sum(sum(syll_1 * syll_2)) / maxoverlap) * 100)
        return syllable_correlation

    def get_syllable_stats(self, syllable_durations, num_syllables, corr_thresh=50):
        sonogram_self_correlation = self.max_correlation()
        sonogram_correlation, sonogram_correlation_binary = self.get_sonogram_correlation(
            sonogram_self_correlation, syllable_durations, corr_thresh)

        # get syllable pattern
        syllable_pattern = np.zeros(len(sonogram_correlation_binary), 'int')
        for j in range(len(sonogram_correlation_binary)):
            syllable_pattern[j] = np.nonzero(sonogram_correlation_binary[:, j])[0][0]

        # find unique syllables
        num_unique_syllables = len(np.unique(syllable_pattern))
        num_syllables_per_num_unique = num_syllables/num_unique_syllables

    # add sequential analysis?

        # check syllable pattern
        syllable_pattern_checked = np.zeros(syllable_pattern.shape, 'int')
        for j in range(len(syllable_pattern)):
            if syllable_pattern[j] < j:
                syllable_pattern_checked[j] = syllable_pattern[syllable_pattern[j]]
            else:
                syllable_pattern_checked[j] = syllable_pattern[j]

        # determine syllable stereotypy
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
            syllable_stereotypy[j] = np.mean(x_syllable_correlations[x_syllable_correlations != 0])

        syllable_stats = {'num_unique_syllables': num_unique_syllables, 'num_syllables_per_num_unique':
            num_syllables_per_num_unique, 'syllable_pattern': syllable_pattern_checked, 'syllable_stereotypy':
            syllable_stereotypy}
        return syllable_stats

    """
    Analysis of notes: frequency information and categorization
    """
    def get_notes(self):
        labeled_sonogram, num_notes = label(self.threshold_sonogram, return_num=True, connectivity=1)
                                                                        # ^connectivity 1=4 or 2=8(include diagonals)
        props = regionprops(labeled_sonogram)

        image_label_overlay = label2rgb(labeled_sonogram, image=self.threshold_sonogram)
        imgplot = plt.imshow(labeled_sonogram)
        # imgplot = plt.imshow(self.threshold_sonogram)
        plt.colorbar()
        # imgplot.set_cmap('nipy_spectral')
        plt.show()
        return num_notes, props

    def convert_freq(self, freq_range_upper, freq_range_lower, freq_factor=22050/513):
        upper_freq_scaled = (513-np.array(freq_range_upper))*freq_factor
        lower_freq_scaled = (513-np.array(freq_range_lower))*freq_factor
        avg_upper_freq = np.mean(upper_freq_scaled)
        avg_lower_freq = np.mean(lower_freq_scaled)
        max_freq = max(upper_freq_scaled)
        min_freq = min(lower_freq_scaled)
        overall_freq_range = max_freq-min_freq
        freq_modulation_per_note = upper_freq_scaled - lower_freq_scaled
        mean_freq_modulation = np.mean(freq_modulation_per_note)
        std_freq_modulation = np.std(freq_modulation_per_note)
        freq_dict = {'avg_upper_freq': avg_upper_freq, 'avg_lower_freq': avg_lower_freq, 'max_freq': max_freq,
                     'min_freq': min_freq, 'overall_freq_range': overall_freq_range, 'freq_modulation_per_note':
                     freq_modulation_per_note, 'mean_freq_modulation': mean_freq_modulation,
                     'std_freq_modulation': std_freq_modulation}
        return freq_dict

    def get_note_stats(self):
        num_notes, props = self.get_notes()
        num_notes_updated = num_notes  # initialize, will be altered if the "note" is too small (<60 pixels)

        # stats per note
        freq_range_upper = []
        freq_range_lower = []
        note_length = []

        # note stats per bout
        num_flat = 0
        num_upsweeps = 0
        num_downsweeps = 0
        num_parabolas = 0

        for j in range(num_notes):
            note_ycoords = []  # clear/initialize for each note

            # use bounding box of the note
            min_row, min_col, max_row, max_col = props[j].bbox
            freq_range_upper.append(min_row)
            freq_range_lower.append(max_row - 1)

            # use only the part of the matrix with the note
            sonogram_one_note = props[j].filled_image
            if np.size(sonogram_one_note) <= 60:
                note_length.append(0)  # place holder
                num_notes_updated -= 1
            else:  # check the note is actually large enough to be a note and not just noise
                note_length.append(np.shape(sonogram_one_note)[1])

                # fit quadratic to notes
                for i in range(note_length[j]):
                    note_ycoords.append(np.mean(np.nonzero(sonogram_one_note[:, i])[0]))
                note_xcoords = np.arange(0, note_length[j])
                poly = np.polyfit(note_xcoords, note_ycoords, deg=2)
                a = poly[0]
                b = poly[1]
                x_vertex = -b/(2*a)  # gives x position of max or min of quadratic

                print(poly)
                # classify shape of note
                if np.isclose(a, 0):  # check if the note is linear
                    if np.isclose(b, 0):
                        num_flat += 1
                    elif b > 0:  # b is the slope if the poly is actually linear
                        num_upsweeps += 1
                    else:
                        num_downsweeps += 1
                # now categorize non-linear notes
                elif x_vertex < .2*note_length[j]:
                    if a > 0:
                        num_upsweeps += 1
                    else:
                        num_downsweeps += 1
                elif x_vertex > .8*note_length[j]:
                    if a > 0:
                        num_downsweeps += 1
                    else:
                        num_upsweeps += 1
                else:  # the vertex is not within the first or last 20% of the note
                    num_parabolas += 1

        # collect stats into dictionaries for output
        basic_stats = self.get_basic_stats(note_length, 'note_length')
        note_categories = {'num_notes': num_notes_updated, 'num_flat': num_flat, 'num_upsweeps': num_upsweeps,
                           'num_downsweeps': num_downsweeps,
                           'num_parabolas': num_parabolas}
        freq_stats = self.convert_freq(freq_range_upper, freq_range_lower)

        note_stats = self.update_dict([basic_stats, note_categories, freq_stats])
        return note_stats



# part that actually calls/runs code
filepath = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\white crowned sparrows for ' \
           'testing\OneBout\Output_20171004_T141722\output_b1s white crowned sparrow 66722amp.gzip'
SyllableAnalysis(filepath)































