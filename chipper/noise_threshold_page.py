import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from skimage.measure import label, regionprops

from chipper.popups import NoiseThreshInstructionsPopup

import os
import chipper.analysis as analyze
import numpy as np


class NoiseThresholdPage(Screen):
    user_noise_thresh = StringProperty()

    def __init__(self, *args, **kwargs):
        self.fig3, self.ax3 = plt.subplots()
        self.plot_noise_canvas = FigureCanvasKivyAgg(self.fig3)

        self.ax3 = plt.Axes(self.fig3, [0., 0., 1., 1.])
        self.ax3.set_axis_off()
        self.fig3.add_axes(self.ax3)
        super(NoiseThresholdPage, self).__init__(*args, **kwargs)

    def setup(self):
        self.noise_thresholds = []
        self.i = 0
        # self.files = [os.path.basename(i) for i in glob.glob(self.parent.directory + '*.gzip')]
        self.files = self.parent.files
        self.next()

    def next(self):
        # if not first entering the app, record the threshold
        if self.i > 0:
            self.noise_thresholds.append(int(self.ids.user_noise_size.text))
        # otherwise it is the first time,
        # so reset noise size threshold to the default
        else:
            self.ids.user_noise_size.text = self.user_noise_thresh

        # if it is the last song go to noise threshold summary page,
        # otherwise process song
        if self.i == len(self.files):
            self.manager.current = 'noise_summary_page'
        else:
            self.ids.user_noise_size.text = self.ids.user_noise_size.text
            ons, offs, thresh, ms, htz = analyze.load_bout_data(
                os.path.join(self.parent.directory, self.files[self.i])
            )
            self.onsets = ons
            self.offsets = offs
            self.threshold_sonogram = thresh
            [self.rows, self.cols] = np.shape(self.threshold_sonogram)

            # prepare graph and make plot take up the entire space
            data = np.zeros((self.rows, self.cols))
            self.ax3.clear()
            self.ax3 = plt.Axes(self.fig3, [0., 0., 1., 1.])
            self.ax3.set_axis_off()
            self.fig3.add_axes(self.ax3)

            cmap = plt.cm.prism
            cmap.set_under(color='black')
            cmap.set_bad(color='white')
            self.plot_noise = self.ax3.imshow(
                data + 3,
                extent=[0, self.cols, 0, self.rows],
                aspect='auto',
                cmap=cmap,
                norm=matplotlib.colors.LogNorm(),
                vmin=3.01
            )

            self.ids.noise_graph.clear_widgets()
            self.ids.noise_graph.add_widget(self.plot_noise_canvas)
            self.new_thresh()
            self.i += 1

    def new_thresh(self):
        # find notes and label based on connectivity
        num_notes, props, labeled_sonogram = self.get_notes()
        # change label of all notes with size > threshold to be the same
        # and all < to be the same
        for region in props:
            if region.area > int(self.ids.user_noise_size.text):
                labeled_sonogram[labeled_sonogram == region.label] = region.area
            else:
                labeled_sonogram[labeled_sonogram == region.label] = 1

        labeled_sonogram = np.ma.masked_where(labeled_sonogram == 1,
                                              labeled_sonogram)
        # update image in widget
        # plot the actual data now
        self.plot_noise.set_data(labeled_sonogram + 3)
        self.plot_noise_canvas.draw()

    def noise_thresh_instructions(self):
        noise_popup = NoiseThreshInstructionsPopup()
        noise_popup.open()

    def get_notes(self):
        """
        num of notes and categorization
        """
        # zero anything before first onset or after last offset
        # (not offset row is already zeros, so okay to include)
        # this will take care of any noise before or after the song
        # before labeling the notes
        threshold_sonogram_crop = self.threshold_sonogram.copy()
        threshold_sonogram_crop[:, 0:self.onsets[0]] = 0
        threshold_sonogram_crop[:, self.offsets[-1]:-1] = 0

        # ^connectivity 1=4 or 2=8(include diagonals)
        labeled_sonogram, num_notes = label(threshold_sonogram_crop,
                                            return_num=True,
                                            connectivity=1)

        props = regionprops(labeled_sonogram)

        return num_notes, props, labeled_sonogram


