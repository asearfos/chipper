import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import matplotlib.transforms as tx
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects


from chipper.popups import SyllSimThreshInstructionsPopup

import os
import chipper.analysis as analyze
import numpy as np


class SyllSimThresholdPage(Screen):
    user_noise_thresh = StringProperty()

    def __init__(self, *args, **kwargs):
        self.fig5, self.ax5 = plt.subplots()
        self.plot_syllsim_canvas = FigureCanvasKivyAgg(self.fig5)

        self.ax5 = plt.Axes(self.fig5, [0., 0., 1., 1.])
        self.ax5.set_axis_off()
        self.fig5.add_axes(self.ax5)
        super(SyllSimThresholdPage, self).__init__(*args, **kwargs)

    def setup(self):
        self.syllsim_thresholds = []
        self.i = 0
        # self.files = [os.path.basename(i) for i in glob.glob(self.parent.directory + '*.gzip')]
        self.files = self.parent.files
        self.next()

    def next(self):
        # if not first entering the app, record the threshold
        if self.i > 0:
            self.syllsim_thresholds.append(float(self.ids.user_syllsim.text))
        # otherwise it is the first time, so reset syllable similarity threshold to the default
        else:
            self.ids.user_syllsim.text = '70.0'

        # if it is the last song go to syllable similarity threshold
        # summary page, otherwise process song'
        if self.i == len(self.files):
            self.manager.current = 'syllsim_summary_page'
        else:
            self.ids.user_syllsim.text = self.ids.user_syllsim.text
            ons, offs, thresh, ms, htz = analyze.load_bout_data(
                os.path.join(self.parent.directory, self.files[self.i])
            )
            self.onsets = ons
            self.offsets = offs
            self.syll_dur = self.offsets - self.onsets
            self.threshold_sonogram = thresh
            [self.rows, self.cols] = np.shape(self.threshold_sonogram)

            # zero anything before first onset or after last offset
            # (not offset row is already zeros, so okay to include)
            # this will take care of any noise before or after the song
            threshold_sonogram_crop = self.threshold_sonogram.copy()
            threshold_sonogram_crop[:, 0:self.onsets[0]] = 0
            threshold_sonogram_crop[:, self.offsets[-1]:-1] = 0

            # ^connectivity 1=4 or 2=8(include diagonals)
            self.labeled_sonogram = label(threshold_sonogram_crop,
                                          connectivity=1)

            corrected_sonogram = remove_small_objects(self.labeled_sonogram,
                                                      min_size=float(self.user_noise_thresh) + 1,  # add one to make =< threshold
                                                      connectivity=1)

            # prepare graph and make plot take up the entire space
            data = np.zeros((self.rows, self.cols))
            self.ax5.clear()
            self.ax5 = plt.Axes(self.fig5, [0., 0., 1., 1.])
            self.ax5.set_axis_off()
            self.fig5.add_axes(self.ax5)

            # plot placeholder data
            cmap = plt.cm.rainbow
            cmap.set_under(color='black')
            self.plot_syllsim = self.ax5.imshow(
                data + 3,
                extent=[0, self.cols, 0, self.rows],
                aspect='auto',
                cmap=cmap,
                # norm=matplotlib.colors.LogNorm(),
                vmin=3.01
            )

            self.trans = tx.blended_transform_factory(self.ax5.transData,
                                                      self.ax5.transAxes)
            self.lines_on, = self.ax5.plot(np.repeat(self.onsets, 3),
                                           np.tile([0, .75, np.nan],
                                                   len(self.onsets)),
                                           linewidth=0.75, color='g',
                                           transform=self.trans)
            self.lines_off, = self.ax5.plot(np.repeat(self.offsets, 3),
                                            np.tile([0, .90, np.nan],
                                                    len(self.offsets)),
                                            linewidth=0.75, color='g',
                                            transform=self.trans)

            self.ids.syllsim_graph.clear_widgets()
            self.ids.syllsim_graph.add_widget(self.plot_syllsim_canvas)

            self.son_corr, son_corr_bin = analyze.get_sonogram_correlation(
                sonogram=corrected_sonogram, onsets=self.onsets,
                offsets=self.offsets, syll_duration=self.syll_dur,
                corr_thresh=float(self.ids.user_syllsim.text)
            )

            self.new_thresh()
            self.i += 1

    def new_thresh(self):
        # get syllable correlations for entire sonogram

        # create new binary matrix with new threshold
        son_corr_bin = np.zeros(self.son_corr.shape)
        son_corr_bin[self.son_corr >= float(self.ids.user_syllsim.text)] = 1

        # get syllable pattern
        syll_pattern = analyze.find_syllable_pattern(son_corr_bin)
        self.ids.song_syntax.text = 'Song Syntax: ' + ", ".join(str(x) for x in syll_pattern)

        syll_stereotypy, syll_stereotypy_max, syll_stereotypy_min = \
            analyze.calc_syllable_stereotypy(self.son_corr, syll_pattern)

        stereotypy_text = 'Syllable: Avg, Min, Max\n'
        for idx in range(len(syll_stereotypy)):
            if not np.isnan(syll_stereotypy[idx]):
                stereotypy_text += '\n' + str(idx) + ': ' + str(round(syll_stereotypy[idx], 1)) + ', ' + \
                                   str(round(syll_stereotypy_min[idx], 1)) + ', ' + \
                                   str(round(syll_stereotypy_max[idx], 1))
        if stereotypy_text == 'Syllable: Avg, Min, Max\n':
            stereotypy_text += 'No Repeated Syllables'
        else:
            self.ids.similarity.text = stereotypy_text

        # color syllables based on syntax
        props = regionprops(self.labeled_sonogram)

        # labeled_sonogram[labeled_sonogram > 0] = 1
        syll_labeled_sonogram = self.threshold_sonogram.copy()
        for on, off, syll in zip(self.onsets, self.offsets, syll_pattern):
            syll_labeled_sonogram[:, on:off][syll_labeled_sonogram[:, on:off] == 1] = syll + 3

        for region in props:
            if region.area <= int(self.user_noise_thresh):
                syll_labeled_sonogram[self.labeled_sonogram == region.label] = 1

        # update image in widget
        # plot the actual data now
        self.plot_syllsim.set_data(syll_labeled_sonogram+3)
        self.plot_syllsim_canvas.draw()

    def syllsim_thresh_instructions(self):
        syllsim_popup = SyllSimThreshInstructionsPopup()
        syllsim_popup.open()
