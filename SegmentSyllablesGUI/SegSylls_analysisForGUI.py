import json
import numpy as np
import gzip
import pandas as pd
import os
import time
import multiprocessing as mp
from skimage.measure import label, regionprops


class SongAnalysis(object):
    def __init__(self, cores, directory, output_path=None):

        if output_path is None:
            output_path = directory + "/AnalysisOutput_" + time.strftime("%Y%m%d_T%H%M%S")

        files = []
        file_names = []
        for f in os.listdir(directory):
            if f.endswith('gzip'):
                files.append(os.path.join(directory, f))
                file_names.append(f)

        processes = mp.Pool(cores)
        final_output = processes.map(self.run_analysis, files)
        self.output_bout_data(output_path, file_names, final_output)

        super(SongAnalysis, self).__init__()

    def run_analysis(self, filepath):
        # file names
        dirname, basename = os.path.split(filepath)

        # load data
        self.onsets, self.offsets, self.threshold_sonogram, self.millisecondsPerPixel, self.hertzPerPixel = \
            self.load_bout_data(dirname, basename)

        # run analysis
        syllable_durations, num_syllables, bout_stats = self.get_bout_stats()
        syllable_stats = self.get_syllable_stats(syllable_durations, num_syllables)
        note_stats = self.get_note_stats(num_syllables)

        # write output
        final_output = self.update_dict([bout_stats, syllable_stats, note_stats])
        return final_output

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
        df_output = pd.DataFrame.from_dict(output_dict)
        df_output.index = [file_name]

        if not os.path.isfile(output_path + '.txt') and not os.path.isfile(output_path):
            if output_path.endswith('.txt'):
                df_output.to_csv(output_path, sep="\t", index_label='FileName')
            else:
                df_output.to_csv((output_path + '.txt'), sep="\t", index_label='FileName')
        else:
            if output_path.endswith('.txt'):
                df_output.to_csv(output_path, sep="\t", mode='a', header=False)
            else:
                df_output.to_csv(output_path + '.txt', sep="\t", mode='a', header=False)

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

    def get_freq_stats(self, freq_range_upper, freq_range_lower, data_type):
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
                'avg_' + data_type + '_upper_freq(Hz)': avg_upper_freq_scaled,
                'avg_' + data_type + '_lower_freq(Hz)': avg_lower_freq_scaled,
                'max_' + data_type + '_freq(Hz)': max_freq_scaled,
                'min_' + data_type + '_freq(Hz)': min_freq_scaled,
                'overall_' + data_type + '_freq_range(Hz)': overall_freq_range_scaled
        }

        freq_modulation_per_note = abs(np.asarray(freq_range_upper) - np.asarray(freq_range_lower))*self.hertzPerPixel
        basic_freq_stats = self.get_basic_stats(freq_modulation_per_note, data_type + '_freq_modulation', '(Hz)')

        freq_stats = self.update_dict([freq_stats, basic_freq_stats])

        return freq_stats

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
    def calc_sylls_freq_ranges(self):
        sylls_freq_range_upper = []
        sylls_freq_range_lower = []
        for j in range(len(self.onsets)):
            start = self.onsets[j]
            stop = self.offsets[j]
            rows_with_signal = np.nonzero(np.sum(self.threshold_sonogram[:, start:stop], axis=1))[0]
            sylls_freq_range_upper.append(rows_with_signal[0])  # will be inclusive
            sylls_freq_range_lower.append(rows_with_signal[-1] + 1)  # add one so that the lower will be exclusive

        return sylls_freq_range_upper, sylls_freq_range_lower

    def calc_max_correlation(self):
        sonogram_self_correlation = np.zeros(len(self.onsets))
        for j in range(len(self.onsets)):
            start = self.onsets[j]
            stop = self.offsets[j]
            sonogram_self_correlation[j] = (self.threshold_sonogram[:, start:stop]*self.threshold_sonogram[:,
                                                                                          start:stop]).sum()
        return sonogram_self_correlation

    def calc_syllable_correlation(self, a, b, shift_factor, min_length, max_overlap):
        syllable_correlation = []
        scale_factor = 100./max_overlap
        for m in range(shift_factor+1):
            syll_1 = self.threshold_sonogram[:, self.onsets[a]:(self.onsets[a] + min_length)]
            syll_2 = self.threshold_sonogram[:, (self.onsets[b] + m):(self.onsets[b] + min_length + m)]
            syllable_correlation.append(scale_factor*(syll_1*syll_2).sum())

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

        syllable_stats_general = {'syll_correlation_threshold': corr_thresh,
                                  'num_unique_syllables': num_unique_syllables,
                                  'num_syllables_per_num_unique': num_syllables_per_num_unique,
                                  'syllable_pattern': syllable_pattern_checked.tolist(),
                                  'sequential_repetition': sequential_rep1,
                                  'syllable_stereotypy': syllable_stereotypy[~np.isnan(syllable_stereotypy)],
                                  'mean_syllable_stereotypy': mean_syllable_stereotypy,
                                  'std_syllable_stereotypy': std_syllable_stereotypy}

        sylls_freq_range_upper, sylls_freq_range_lower = self.calc_sylls_freq_ranges()
        syll_freq_stats = self.get_freq_stats(sylls_freq_range_upper, sylls_freq_range_lower, 'sylls')

        syllable_stats = self.update_dict([syllable_stats_general, syll_freq_stats])

        return syllable_stats

    """
    Analysis of notes: num of notes and categorization; also outputs freq ranges of each note
    """
    def get_notes(self):
        # zero anything before first onset or after last offset (not offset row is already zeros, so okay to include)
        # this will take care of any noise before or after the song before labeling the notes
        threshold_sonogram_crop = self.threshold_sonogram.copy()
        threshold_sonogram_crop[:, 0:self.onsets[0]] = 0
        threshold_sonogram_crop[:, self.offsets[-1]:-1] = 0

        labeled_sonogram, num_notes = label(threshold_sonogram_crop, return_num=True, connectivity=1)
                                                                        # ^connectivity 1=4 or 2=8(include diagonals)
        props = regionprops(labeled_sonogram)

        return num_notes, props

    def get_note_stats(self, num_syllables, note_size_thresh=60):
        num_notes, props = self.get_notes()
        num_notes_updated = num_notes  # initialize, will be altered if the "note" is too small (<60 pixels)

        # stats per note
        notes_freq_range_upper = []
        notes_freq_range_lower = []
        note_length = []

        for j in range(num_notes):
            # note_ycoords = []  # clear/initialize for each note

            # use only the part of the matrix with the note
            sonogram_one_note = props[j].filled_image

            if np.size(sonogram_one_note) <= note_size_thresh:  # check the note is large enough to be a note and not
                # just noise
                note_length.append(0)  # place holder
                num_notes_updated -= 1
                # print('not a note')
            else:
                # use bounding box of the note (note, indexing is altered since python starts with 0 and we want to
                # convert rows to actual frequency)
                min_row, min_col, max_row, max_col = props[j].bbox
                notes_freq_range_upper.append(min_row)  # min row is inclusive (first row with labeled section)
                notes_freq_range_lower.append(max_row)  # max row is not inclusive (first zero row after the labeled section)

                note_length.append(np.shape(sonogram_one_note)[1])

        # collect stats into dictionaries for output
        note_length_array = np.asarray(note_length)
        note_length_array = note_length_array[note_length_array != 0]
        note_length_array_scaled = note_length_array*self.millisecondsPerPixel
        note_counts = {'note_size_threshold': note_size_thresh,
                       'num_notes': num_notes_updated,
                       'num_notes_per_syll': num_notes_updated/num_syllables}
        basic_note_stats = self.get_basic_stats(note_length_array_scaled, 'note_duration', '(ms)')
        note_freq_stats = self.get_freq_stats(notes_freq_range_upper, notes_freq_range_lower, 'notes')

        note_stats = self.update_dict([note_counts, basic_note_stats, note_freq_stats])
        return note_stats


# part that actually calls/runs code

directory_regRes = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\TestingAxes\ControlChippies' \
           '\SegSyllsOutput_20171022_T193442/'

directory_doubleRes = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\TestingAxes\ControlChippies' \
              '\SegSyllsOutput_20171024_T101407/'

directory_oneBout = 'C:/Users/abiga\Box Sync\Abigail_Nicole\TestingGUI\white crowned sparrows for ' \
                    'testing\OneBout\SegSyllsOutput_20171024_T160406/'


if __name__ == '__main__':
    SongAnalysis(2, directory_oneBout)










