import json
import numpy as np

class SyllableAnalysis(Screen):
    def __init__(self, filename, **kwargs):

        #any self variables
        filename = 'jsontesting25574571_b1of2.wav.txt'
        onsets, offsets, threshold_sonogram = self.load_bout_data(filename)
        [] = self.get_bout_stats(onsets, offsets)

        super(SyllableAnalysis, self).__init__(**kwargs)

    """ 
    Load sonogram and syllable marks (onsets and offsets).
    """

    def load_bout_data(self, filename):
        load_file = open(filename, 'r')
        song_data = []

        for line in load_file:
            json_line = json.loads(line)
            song_data.append(json_line)
        load_file.close()

        onsets = np.asarray(song_data[1]['Onsets'])
        offsets = np.asarray(song_data[1]['Offsets'])
        threshold_sonogram = song_data[2]['Sonogram']
        print(onsets)
        print(offsets)
        return onsets, offsets, threshold_sonogram

    """ 
    Algebraic calculations using onsets and offsets
    """
    def get_bout_stats(self, onsets, offsets):
        syllable_durations = offsets - onsets
        silence_durations = [onsets[i] - offsets[i-1] for i in range(1, len(onsets))]
        bout_duration = offsets[-1] - onsets[0]
        num_syllables = len(syllable_durations)
        num_sylls_per_bout_duration = num_syllables/bout_duration
        num_syllables_per_bout_duration = num_syllables/bout_duration
        syllable_stats = self.get_stats(syllable_durations)
        silence_stats = self.get_stats(silence_durations)

    def get_stats(self, durations):
        stats = {'longest': max(durations), 'shortest': min(durations), 'mean': np.mean(durations), 'std': np.std(durations)}
        return stats

    """
    Compare syllables to each other
    """
    def max_correlation(self, threshold_sonogram, syllable_onsets, syllable_offsets):
        sonogram_self_correlation = []
        for j in syllable_onsets:
            sonogram_self_correlation[j] = sum(sum(threshold_sonogram[:, syllable_onsets[j]:syllable_offsets[j]]*threshold_sonogram[:, syllable_onsets[j]:syllable_offsets[j]]))
        return sonogram_self_correlation

    def get_sonogram_correlation(self, threshold_sonogram, syllable_onsets, syllable_offsets, syllable_durations, corr_thresh = 50):

        sonogram_self_correlation = self.max_correlation(threshold_sonogram, syllable_onsets, syllable_offsets)

        sonogram_correlation = []
        syllable_correlation = []
        for j in syllable_onsets:
            for k in syllable_onsets:

                if j>k:  # do not want to fill the second half of the diagonal matrix
                    continue

                maxoverlap = max(sonogram_self_correlation[j], sonogram_self_correlation[k])

                if syllable_durations[j] == syllable_durations[k]:
                    shift_factor = 0
                else:
                    shift_factor = abs(syllable_durations[j]-syllable_durations[k]) - 1

                if syllable_durations[j] < syllable_durations[k]:
                    min_length = syllable_durations[j]
                    for m in range(shift_factor+1): # TODO: fix this (also check indexing..may need to add one to the end index since python is not inclusive
                        syllable_correlation[m] = (sum(sum(threshold_sonogram[:,syllable_onsets[j]:(syllable_onsets[j]+min_length)]*threshold_sonogram[:,(syllable_onsets[k]+m):(syllable_onsets[k]+min_length+m)]))/maxoverlap)*100
                else:  # will be if k is shorter than j or they are equal
                    min_length = syllable_durations[k]
                    for m in range(shift_factor+1):
                        syllable_correlation[m] = (sum(sum(threshold_sonogram[:,(syllable_onsets[j]+m):(syllable_onsets[j]+min_length+m)]*threshold_sonogram[:,syllable_onsets[k]:(syllable_onsets[k]+min_length)]))/maxoverlap)*100

                # fill both upper and lower diagonal of symmetric matrix
                sonogram_correlation[j,k] = max(syllable_correlation)
                sonogram_correlation[k,j] = max(syllable_correlation)

        sonogram_correlation_binary = np.zeros(sonogram_correlation.shape)
        sonogram_correlation_binary[sonogram_correlation > corr_thresh] = 1

    def get_syllable_pattern(self, symmetric_binary):
        syllable_pattern = np.zeros(len(symmetric_binary), 'int')
        for j in range(len(symmetric_binary)):
            syllable_pattern[j] = np.nonzero(symmetric_binary[:,j])[0][0]
        return syllable_pattern

    def pattern_stats(self, syllable_pattern, num_syllables):
        num_unique_syllables = len(np.unique(syllable_pattern))
        num_syllables_per_num_unique = num_syllables/num_unique_syllables

    # add sequential analysis?

    def check_syllable_pattern(self, syllable_pattern):
        syllable_pattern_checked = np.zeros(syllable_pattern.shape, 'int')
        for j in range(len(syllable_pattern)):
            if syllable_pattern[j] < j:
                syllable_pattern_checked[j] = syllable_pattern[syllable_pattern[j]]
            else:
                syllable_pattern_checked[j] = syllable_pattern[j]




















