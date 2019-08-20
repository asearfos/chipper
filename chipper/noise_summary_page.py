import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from kivy.uix.screenmanager import Screen

import numpy as np


class NoiseSummaryPage(Screen):
    def __init__(self, *args, **kwargs):
        self.fig4, self.ax4 = plt.subplots()
        self.noise_hist_canvas = FigureCanvasKivyAgg(self.fig4)
        super(NoiseSummaryPage, self).__init__(*args, **kwargs)

    def calculate_noise_thresh_stats(self):
        # note thresholds from all the songs processed
        note_thresholds = self.manager.get_screen(
            'noise_threshold_page').note_thresholds

        # clear the plot
        self.ax4.clear()

        # plot histogram of the note thresholds used
        if len(np.unique(note_thresholds)) > 20:
            self.ax4.hist(x=note_thresholds, bins='auto', color=(0.196, 0.643, 0.80), alpha=0.7)
        else:
            # the trick is to set up the bins centered on the integers, i.e.
            # -0.5, 0.5, 1,5, 2.5, ... up to max(data) + 1.5. Then you substract -0.5 to
            # eliminate the extra bin at the end.
            if max(note_thresholds) - min(note_thresholds) >= 1000:
                bins = np.arange(min(note_thresholds), max(note_thresholds) + 150, 100) - 50
                print('>= 1000', bins)
            elif max(note_thresholds) - min(note_thresholds) >= 250:
                bins = np.arange(min(note_thresholds), max(note_thresholds) + 15, 10) - 5
                print('>= 500', bins)
            else:
                bins = np.arange(min(note_thresholds), max(note_thresholds) + 1.5, 1) - 0.5
            self.ax4.hist(x=note_thresholds, bins=bins, color=(0.196, 0.643, 0.80), alpha=0.7)

        self.ax4.set_xlabel('Note Size Threshold')
        self.ax4.set_ylabel('Number of Songs with Threshold')
        self.noise_hist_canvas.draw()

        self.ids.noise_hist.clear_widgets()
        self.ids.noise_hist.add_widget(self.noise_hist_canvas)

        # calculate stats for the submitted thresholds and add them to the screen
        self.ids.num_files.text = 'Number of Files: ' + str((len(note_thresholds)))
        self.ids.avg_note_thresh.text = 'Average: ' + str(round(np.mean(note_thresholds), 1))
        self.ids.std_dev_note_thresh.text = 'Standard Deviation: ' + str(round(np.std(note_thresholds), 1))
        self.ids.min_note_thresh.text = 'Minimum: ' + str(min(note_thresholds))
        self.ids.max_note_thresh.text = 'Maximum: ' + str(max(note_thresholds))

        # set the user input to the average as a default (they can change this before submitting)
        self.ids.submitted_note_thresh_input.text = str(int(round(np.mean(note_thresholds), 0)))

    def submit_note_thresh(self):
        # update the landing page with the note size threshold the user chooses/submits
        self.manager.get_screen('landing_page').ids.note_thresh_input.text = self.ids.submitted_note_thresh_input.text
