import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt

import numpy as np
import segmentSylls_functionsForGUI as seg


class ControlPanel(BoxLayout):

    def __init__(self):
        super(ControlPanel, self).__init__()
        self.i = 0
        self.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"
        self.files, self.F = seg.initialize(self.directory)
        # add save parameters here - dictionary of dictionary
        self.next()

    def next(self):
        # set default parameters
        self.filter_boundary = 0
        self.percent_keep = 2
        self.min_silence = 10
        self.min_syllable = 20

        #connect defaults to .kv (would like to do this the other way around)
        self.ids.slider_high_pass_filter.value = self.filter_boundary
        self.ids.slider_threshold.value = self.percent_keep
        self.ids.slider_min_silence.value = self.min_silence
        self.ids.slider_min_syllable.value = self.min_syllable

        self.sonogram = seg.initial_sonogram(self.i, self.files, self.directory)
        #run update to load images for the first time for this file
        self.update(self.sonogram, 513-self.filter_boundary, self.percent_keep, self.min_silence, self.min_syllable)
        self.i += 1

    def save(self):
        # save parameters to dictionary
        self.next()

    def toss(self):
        # send file name to .txt or send file to folder
        self.next()

    def update(self, sonogram, filter_boundary, percent_keep, min_silence, min_syllable):
        hpf_sonogram = seg.high_pass_filter(filter_boundary, sonogram)
        scaled_sonogram = seg.normalize_amplitude(hpf_sonogram)
        self.image_sonogram(hpf_sonogram)

        thresh_sonogram = seg.threshold(percent_keep, scaled_sonogram)
        onsets, offsets2, silence_durations, sum_sonogram_scaled, rows = seg.initialize_onsets_offsets(thresh_sonogram)
        syllable_onsets, syllable_offsets = seg.set_min_silence(min_silence, onsets, offsets2, silence_durations)
        syllable_marks = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets, sum_sonogram_scaled, rows)
        self.image_binary(thresh_sonogram, syllable_marks)

    def image_sonogram(self, data):
        self.ids.graph_sonogram.clear_widgets()

        [rows, cols] = np.shape(data)
        plt.style.use('dark_background')
        fig1 = plt.figure()
        plot_sonogram = plt.imshow(np.log(data + 3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
        #plot_sonogram.axes.axis('off')
        fig1.tight_layout()

        self.fig1 = plt.gcf()
        self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(self.fig1))
        return plot_sonogram

    def image_binary(self, data, syllable_marks):
        self.ids.graph_binary.clear_widgets()

        [rows, cols] = np.shape(data)
        plt.style.use('dark_background')
        fig2 = plt.figure()
        plot_sonogram = plt.imshow(np.log(data + 3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
        #plot_sonogram.axes.axis('off')
        fig2.tight_layout()

        # plot onsets and offsets
        indexes = np.squeeze(np.nonzero(syllable_marks))
        ymin = np.zeros(len(indexes))
        ymax = syllable_marks[syllable_marks != 0]
        plt.vlines(indexes, ymin=ymin, ymax=ymax, colors='m', linewidth=0.5)
        plt.show(block=False)

        self.fig2 = plt.gcf()
        self.ids.graph_binary.add_widget(FigureCanvasKivyAgg(self.fig2))
        return plot_sonogram


class MySlider(Slider):
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        super(MySlider, self).__init__(**kwargs)

    def on_release(self):
        pass

    def on_touch_up(self, touch):
        super(MySlider, self).on_touch_up(touch)
        if touch.grab_current == self:
            self.dispatch('on_release')
            return True


class SegmentSyllablesGUI_withJamesApp(App):
    def build(self):
        return ControlPanel()

if __name__ == "__main__":
    SegmentSyllablesGUI_withJamesApp().run()
