text = 'The colors are here to help you distinguish the syntax of the song which is also written above the ' \
       'spectrogram. ' \
       'Two syllables are considered to be identical if they overlap with an accuracy greater than or equal to the ' \
       'syllable similarity threshold. ' \
       'The syntax is found sequentially, meaning if the second syllable is found to be the same as the first, ' \
       'and the third syllable is found to be the same as the second but not the first, the third will still be the ' \
       'same as both first and second syllables.\n\n' \
       'To help, the average, minimum, and maximum percent similarity between like syllables is also provided. ' \
       'Note, the minimum can be less than the threshold due to the sequential nature of how the syntax is found.\n\n' \
       'The purpose of the widget is to help you determine a common ' \
       'threshold for syllable similarity for all of your data. ' \
       'We recommend you perform this step for a set of songs from the same ' \
       'species. Specifically, you can use a subset of your data (~20 songs) ' \
       'to determine the threshold. You will adjust the threshold for each ' \
       'song until satisfied with the results. A summary of the thresholds ' \
       'used for the sample songs will be given at the end. Then, you will be ' \
       'given the chance to adjust the final threshold to be used in song ' \
       'analysis.\n\n' \
       'Any signal between syllables appears grey and will not be ' \
       'considered in the analysis. Similarly, any noise (determined using ' \
       'the Noise Threshold from the previous step) will appear white and ' \
       'will not be considered in the analysis.'