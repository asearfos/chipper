text = 'WOW! That is a lot of colors! \n\n' \
       'Quick Reference: noise is in white, notes are in color.\n\n' \
       'The colors are here to help you distinguish separate notes. ' \
       'A note is considered to be a set of connected matrix elements in the binary spectrogram ' \
       'having an area greater than the noise threshold. ' \
       'So, if two notes are very close to one another and the same color, they are most likely one note. ' \
       'This may be due to the limits of screen resolution.  If the area of ' \
       'a note is less than or equal to the noise threshold, it will be ' \
       'considered noise, appearing white in the spectrogram. ' \
       'Noise will not be considered in the analysis calculations.\n\n'  \
       'The purpose of this widget is to help you determine a common ' \
       'threshold for noise for all of your data. We recommend you perform ' \
       'this step for a set of songs from the same species. Specifically, ' \
       'you can use a subset of your data (~20 songs) to determine the ' \
       'threshold. You will adjust the threshold for each song until ' \
       'satisfied with the results. A summary of the thresholds used for the ' \
       'sample songs will be given at the end. Then, you will be given the ' \
       'chance to adjust the final threshold to be used in song analysis.\n\n'\
       'You can return to this widget as many times as you wish to ' \
       'visualize the chosen threshold for any songs of interest.'