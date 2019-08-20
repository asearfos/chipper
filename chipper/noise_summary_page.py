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
        # noise thresholds from all the songs processed
        noise_thresholds = self.manager.get_screen(
            'noise_threshold_page').noise_thresholds

        # clear the plot
        self.ax4.clear()

        # plot histogram of the noise thresholds used
        if len(np.unique(noise_thresholds)) > 20:
            self.ax4.hist(x=noise_thresholds, bins='auto', color=(0.196, 0.643, 0.80), alpha=0.7)
        else:
            # the trick is to set up the bins centered on the integers, i.e.
            # -0.5, 0.5, 1,5, 2.5, ... up to max(data) + 1.5. Then you substract -0.5 to
            # eliminate the extra bin at the end.
            if max(noise_thresholds) - min(noise_thresholds) >= 1000:
                bins = np.arange(min(noise_thresholds), max(noise_thresholds) + 150, 100) - 50
                print('>= 1000', bins)
            elif max(noise_thresholds) - min(noise_thresholds) >= 250:
                bins = np.arange(min(noise_thresholds), max(noise_thresholds) + 15, 10) - 5
                print('>= 500', bins)
            else:
                bins = np.arange(min(noise_thresholds), max(noise_thresholds) + 1.5, 1) - 0.5
            self.ax4.hist(x=noise_thresholds, bins=bins, color=(0.196, 0.643, 0.80), alpha=0.7)

        self.ax4.set_xlabel('Noise Threshold')
        self.ax4.set_ylabel('Number of Songs with Threshold')
        self.noise_hist_canvas.draw()

        self.ids.noise_hist.clear_widgets()
        self.ids.noise_hist.add_widget(self.noise_hist_canvas)

        # calculate stats for the submitted thresholds and add them to the screen
        self.ids.num_files.text = 'Number of Files: ' + str((len(noise_thresholds)))
        self.ids.avg_noise_thresh.text = 'Average: ' + str(round(np.mean(noise_thresholds), 1))
        self.ids.std_dev_noise_thresh.text = 'Standard Deviation: ' + str(round(np.std(noise_thresholds), 1))
        self.ids.min_noise_thresh.text = 'Minimum: ' + str(min(noise_thresholds))
        self.ids.max_noise_thresh.text = 'Maximum: ' + str(max(noise_thresholds))

        # set the user input to the average as a default (they can change this before submitting)
        self.ids.submitted_noise_thresh_input.text = str(int(round(np.mean(noise_thresholds), 0)))

    def submit_noise_thresh(self):
        # update the landing page with the noise threshold the user 
        # chooses/submits
        self.manager.get_screen('landing_page').ids.noise_thresh_input.text = self.ids.submitted_noise_thresh_input.text
