import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from kivy.uix.screenmanager import Screen

from chipper.popups import SyllSimThreshInstructionsPopup

import os
import glob
import chipper.analysis as analyze
import numpy as np


class SyllSimThresholdPage(Screen):

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
        self.files = [os.path.basename(i) for i in glob.glob(self.parent.directory + '*.gzip')]
        self.next()

    def next(self):
        # if not first entering the app, record the threshold
        if self.i > 0:
            self.syllsim_thresholds.append(int(self.ids.user_syllsim.text))
        # otherwise it is the first time, so reset syllable similarity threshold to the default
        else:
            self.ids.user_syllsim.text = '120'

        # if it is the last song go to syllable similarity threshold summary page, otherwise process song
        if self.i == len(self.files):
            self.manager.current = 'syllsim_summary_page'
        else:
            self.ids.user_syllsim.text = self.ids.user_syllsim.text
            ons, offs, thresh, ms, htz = analyze.load_bout_data(os.path.join(self.parent.directory, self.files[self.i]))
            self.onsets = ons
            self.offsets = offs
            self.threshold_sonogram = thresh
            [self.rows, self.cols] = np.shape(self.threshold_sonogram)

            # prepare graph and make plot take up the entire space
            data = np.zeros((self.rows, self.cols))
            self.ax5.clear()
            self.ax5 = plt.Axes(self.fig5, [0., 0., 1., 1.])
            self.ax5.set_axis_off()
            self.fig5.add_axes(self.ax5)

            # plot placeholder data
            cmap = plt.cm.prism
            cmap.set_under(color='black')
            cmap.set_bad(color='white')
            self.plot_syllsim = self.ax5.imshow(data+3, extent=[0, self.cols, 0, self.rows],
                                              aspect='auto', cmap=cmap, norm=matplotlib.colors.LogNorm(),
                                              vmin=3.01)

            self.ids.syllsim_graph.clear_widgets()
            self.ids.syllsim_graph.add_widget(self.plot_syllsim_canvas)
            self.new_thresh()
            self.i += 1

    def new_thresh(self):
        # find notes and label based on connectivity
        num_notes, props, labeled_sonogram = analyze.get_notes(self.threshold_sonogram, self.onsets, self.offsets)
        # change label of all notes with size > threshold to be the same and all < to be the same
        for region in props:
            if region.area > int(self.ids.user_syllsim.text):
                labeled_sonogram[labeled_sonogram == region.label] = region.area
            else:
                labeled_sonogram[labeled_sonogram == region.label] = 1

        labeled_sonogram = np.ma.masked_where(labeled_sonogram == 1, labeled_sonogram)
        # update image in widget
        # plot the actual data now
        self.plot_syllsim.set_data(labeled_sonogram+3)
        self.plot_syllsim_canvas.draw()

    def syllsim_thresh_instructions(self):
        syllsim_popup = SyllSimThreshInstructionsPopup()
        syllsim_popup.open()
