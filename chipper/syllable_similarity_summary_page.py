import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
from kivy.uix.screenmanager import Screen

import numpy as np


class SyllSimSummaryPage(Screen):
    def __init__(self, *args, **kwargs):
        self.fig6, self.ax6 = plt.subplots()
        self.syllsim_hist_canvas = FigureCanvasKivyAgg(self.fig6)
        super(SyllSimSummaryPage, self).__init__(*args, **kwargs)

    def calculate_syllsim_thresh_stats(self):
        # note thresholds from all the songs processed
        syllsim_thresholds = self.manager.get_screen('syllsim_threshold_page').syllsim_thresholds

        # clear the plot
        self.ax6.clear()

        # plot histogram of the note thresholds used
        if len(np.unique(syllsim_thresholds)) > 20:
            self.ax6.hist(x=syllsim_thresholds, bins='auto', color=(0.196, 0.643, 0.80), alpha=0.7)
        else:
            # the trick is to set up the bins centered on the integers, i.e.
            # -0.5, 0.5, 1,5, 2.5, ... up to max(data) + 1.5. Then you substract -0.5 to
            # eliminate the extra bin at the end.
            if max(syllsim_thresholds) - min(syllsim_thresholds) >= 1000:
                bins = np.arange(min(syllsim_thresholds), max(syllsim_thresholds) + 150, 100) - 50
                print('>= 1000', bins)
            elif max(syllsim_thresholds) - min(syllsim_thresholds) >= 250:
                bins = np.arange(min(syllsim_thresholds), max(syllsim_thresholds) + 15, 10) - 5
                print('>= 500', bins)
            else:
                bins = np.arange(min(syllsim_thresholds), max(syllsim_thresholds) + 1.5, 1) - 0.5
            self.ax6.hist(x=syllsim_thresholds, bins=bins, color=(0.196, 0.643, 0.80), alpha=0.7)

        self.ax6.set_xlabel('Syllable Similarity Threshold')
        self.ax6.set_ylabel('Number of Songs with Threshold')
        self.syllsim_hist_canvas.draw()

        self.ids.syllsim_hist.clear_widgets()
        self.ids.syllsim_hist.add_widget(self.syllsim_hist_canvas)

        # calculate stats for the submitted thresholds and add them to the screen
        self.ids.num_files.text = 'Number of Files: ' + str((len(syllsim_thresholds)))
        self.ids.avg_syllsim_thresh.text = 'Average: ' + str(round(np.mean(syllsim_thresholds), 1))
        self.ids.std_dev_syllsim_thresh.text = 'Standard Deviation: ' + str(round(np.std(syllsim_thresholds), 1))
        self.ids.min_syllsim_thresh.text = 'Minimum: ' + str(min(syllsim_thresholds))
        self.ids.max_syllsim_thresh.text = 'Maximum: ' + str(max(syllsim_thresholds))

        # set the user input to the average as a default (they can change this before submitting)
        self.ids.submitted_syllsim_thresh_input.text = str(int(round(np.mean(syllsim_thresholds), 0)))

    def submit_syllsim_thresh(self):
        # update the landing page with the note size threshold the user chooses/submits
        self.manager.get_screen('landing_page').ids.syll_sim_input.text = self.ids.submitted_syllsim_thresh_input.text
