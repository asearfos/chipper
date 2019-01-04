import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from kivy.uix.screenmanager import Screen

import os
import glob
import chipper.functions as seg
import chipper.analysis as analyze
import numpy as np



class NoteThresholdPage(Screen):

    def __init__(self, *args, **kwargs):
        self.note_thresholds = []
        self.fig3, self.ax3 = plt.subplots()
        self.plot_notes_canvas = FigureCanvasKivyAgg(self.fig3)

        self.ax3 = plt.Axes(self.fig3, [0., 0., 1., 1.])
        self.ax3.set_axis_off()
        self.fig3.add_axes(self.ax3)
        super(NoteThresholdPage, self).__init__(*args, **kwargs)

    def setup(self):
        self.i = 0
        self.files = [os.path.basename(i) for i in glob.glob(self.parent.directory + '*.gzip')]
        self.next()

    def next(self):
        # if not first entering the app, record the threshold
        if self.i > 0:
            self.note_thresholds.append(int(self.ids.user_note_size.text))

        # if it is the last song go to note threshold summary page, otherwise process song
        if self.i == len(self.files):
            print(self.note_thresholds)
        else:
            self.ids.user_note_size.text = self.ids.user_note_size.text
            ons, offs, thresh, ms, htz = analyze.load_bout_data(os.path.join(self.parent.directory, self.files[self.i]))
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

            # plot placeholder data
            # colors = [(0, 0, 0), (1, 0, 0), (0.196, 0.643, 0.80), (1, 1, 1)]
            colors = [(0, 0, 0), (0.196, 0.643, 0.80), (1, 1, 1)]
            my_cmap = LinearSegmentedColormap.from_list('my_cmap', colors,
                                                        N=len(colors))
            self.plot_notes = self.ax3.imshow(np.log(data + 3), cmap=my_cmap, extent=[0, self.cols, 0, self.rows],
                                              aspect='auto')

            self.ids.note_graph.clear_widgets()
            self.ids.note_graph.add_widget(self.plot_notes_canvas)
            self.new_thresh()
            self.i += 1

    def new_thresh(self):
        # find notes and label based on connectivity
        num_notes, props, labeled_sonogram = analyze.get_notes(self.threshold_sonogram, self.onsets, self.offsets)

        # change label of all notes with size > threshold to be the same and all < to be the same
        for region in props:
            if region.area > int(self.ids.user_note_size.text):
                labeled_sonogram[labeled_sonogram == region.label] = 1
                # if region.label % 2 == 0:  # even
                #     labeled_sonogram[labeled_sonogram == region.label] = 1
                # else:
                #     labeled_sonogram[labeled_sonogram == region.label] = 2
            else:
                labeled_sonogram[labeled_sonogram == region.label] = 2

        # update image in widget
        # plot the actual data now
        # self.plot_notes.set_data(np.log(self.threshold_sonogram+3))
        self.plot_notes.set_data(np.log(labeled_sonogram+3))
        self.plot_notes.autoscale()
        self.plot_notes_canvas.draw()
