import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.slider import Slider
from RangeSlider_FromGoogle import RangeSlider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.config import Config

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib.backend_kivy import FigureCanvas
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
plt.style.use('dark_background')

import re
import numpy as np
import csv

# import my own functions for data analysis
import segmentSylls_functionsForGUI as seg


class Manager(ScreenManager):
    pass


class ScreenOne(Screen):
    def _fbrowser_canceled(self, instance):
        print('cancelled, Close SegmentSyllablesGUI.')
        quit()

    def _fbrowser_success(self, instance):
        [chosen_directory] = instance.selection
        # self.parent.directory = chosen_directory + '\\'
        self.parent.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/TestingGUI/PracticeBouts/"


class DonePopup(Popup):
    pass


class ControlPanel(Screen):

    def test(self, touchx, touchy):
        print(touchx, touchy)
        # new = touch.apply_transform_2d(self.to_window)
        # print(new)


    def setup(self):
        self.i = 0
        self.files = seg.initialize(self.parent.directory)
        self.save_parameters = {}
        self.save_syllables = {}
        self.save_tossed = {}
        self.next()


    def next(self):
        # reset default parameters for new song
        # !!!SHOULDN'T NEED THE VALUES SET IN .KV NOW!!!
        self.filter_boundary = 0
        self.percent_keep = 2
        self.min_silence = 10
        self.min_syllable = 20

        # connect defaults to .kv (would like to do this the other way around)
        self.ids.slider_high_pass_filter.value = self.filter_boundary
        self.ids.slider_threshold.value = self.percent_keep
        self.ids.slider_min_silence.value = self.min_silence
        self.ids.slider_min_syllable.value = self.min_syllable

        self.sonogram = seg.initial_sonogram(self.i, self.files, self.parent.directory)
        # run update to load images for the first time for this file
        [rows, cols] = np.shape(self.sonogram)
        self.ids.slider_high_pass_filter.max = rows
        self.ids.range_slider_crop.max = cols

        self.image_sonogram_initial(rows, cols)
        self.image_binary_initial(rows, cols)
        self.syllable_onsets, self.syllable_offsets = self.update(self.sonogram, 513-self.filter_boundary, self.percent_keep, self.min_silence, self.min_syllable)
        self.i += 1

    def update(self, sonogram, filter_boundary, percent_keep, min_silence, min_syllable):
        self.filter_boundary = filter_boundary
        self.percent_keep = percent_keep
        self.min_silence = min_silence
        self.min_syllable = min_syllable
        sonogram = self.sonogram.copy()
        hpf_sonogram = seg.high_pass_filter(filter_boundary, sonogram)
        scaled_sonogram = seg.normalize_amplitude(hpf_sonogram)
        self.image_sonogram(hpf_sonogram)

        thresh_sonogram = seg.threshold(percent_keep, scaled_sonogram)
        onsets, offsets2, silence_durations, sum_sonogram_scaled, rows = seg.initialize_onsets_offsets(thresh_sonogram)
        syllable_onsets, syllable_offsets = seg.set_min_silence(min_silence, onsets, offsets2, silence_durations)
        syllable_onsets, syllable_offsets, syllable_marks = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets, sum_sonogram_scaled, rows)
        self.image_binary(thresh_sonogram, syllable_marks)
        return syllable_onsets, syllable_offsets

    def image_sonogram_initial(self, rows, cols):
        data = np.zeros((rows, cols))
        self.fig1, self.ax1 = plt.subplots()
        # self.fig1.tight_layout()
        # make plot take up the entire space
        self.ax1 = plt.Axes(self.fig1, [0., 0., 1., 1.])
        self.ax1.set_axis_off()
        self.fig1.add_axes(self.ax1)
        self.plot_sonogram = self.ax1.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')

    def image_sonogram(self, data):
        self.ids.graph_sonogram.clear_widgets()
        self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(self.fig1))
        self.plot_sonogram.set_data(np.log(data+3))
        self.plot_sonogram.autoscale()
        # self.ids.graph_sonogram.clear_widgets()
        # self.ids.graph_sonogram.add_widget(FigureCanvas(self.fig1)) # doesn't work without draw
        # self.plot_sonogram.set_data(np.log(data+3))
        # self.plot_sonogram.autoscale()
        # self.fig1.canvas.draw() # this doesn't work:  AttributeError: 'numpy.ndarray' object has no attribute 'get_size_out'
        # self.fig1.canvas.flush_events() # supposed to get rid of the lag due to sleep

    # def image_sonogram(self, data):
    #     # plt.close('all')
    #     self.ids.graph_sonogram.clear_widgets()
    #
    #     [rows, cols] = np.shape(data)
    #     fig1, ax1 = plt.subplots()
    #     fig1.tight_layout()
    #     plot_sonogram = ax1.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
    #     # plot_sonogram.set_data(np.log(data+3))
    #     self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(fig1))
    #     # look up how to speed up matplotlip --> make one canvas

    def image_binary_initial(self, rows, cols):
        data = np.zeros((rows, cols))
        self.lines = {}
        self.fig2, self.ax2 = plt.subplots()
        # self.fig2.tight_layout()
        # make plot take up the entire space
        self.ax2 = plt.Axes(self.fig2, [0., 0., 1., 1.])
        self.ax2.set_axis_off()
        self.fig2.add_axes(self.ax2)
        self.plot_binary = self.ax2.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
        self.lines[0] = self.ax2.vlines(0, ymin=0, ymax=0, colors='m', linewidth=0.5)


    def image_binary(self, data, syllable_marks):
        self.ids.graph_binary.clear_widgets()
        self.ids.graph_binary.add_widget(FigureCanvasKivyAgg(self.fig2))
        self.plot_binary.set_data(np.log(data+3))
        self.plot_binary.autoscale()
        # self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(self.fig2))

        # plot onsets and offsets
        self.lines.pop(0).remove()
        indexes = np.squeeze(np.nonzero(syllable_marks))
        ymin = np.zeros(len(indexes))
        ymax = syllable_marks[syllable_marks != 0]
        self.lines[0] = self.ax2.vlines(indexes, ymin=ymin, ymax=ymax, colors='m', linewidth=0.5)


    # def image_binary(self, data, syllable_marks):
    #     self.ids.graph_binary.clear_widgets()
    #
    #     [rows, cols] = np.shape(data)
    #     plt.style.use('dark_background')
    #     fig2 = plt.figure()
    #     plot_sonogram = plt.imshow(np.log(data + 3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
    #     #plot_sonogram.axes.axis('off')
    #     fig2.tight_layout()
    #
    #     # plot onsets and offsets
    #     indexes = np.squeeze(np.nonzero(syllable_marks))
    #     ymin = np.zeros(len(indexes))
    #     ymax = syllable_marks[syllable_marks != 0]
    #     plt.vlines(indexes, ymin=ymin, ymax=ymax, colors='m', linewidth=0.5)
    #     plt.show(block=False)
    #
    #     fig2 = plt.gcf()
    #     self.ids.graph_binary.add_widget(FigureCanvasKivyAgg(fig2))
    #     return plot_sonogram

    def save(self):
        # save parameters to dictionary
        self.save_parameters[self.files[self.i-1]] = {'HighPassFilter': self.filter_boundary, 'PercentSignalKept': self.percent_keep, 'MinSilenceDuration': self.min_silence, 'MinSyllableDuration': self.min_syllable}
        self.save_syllables[self.files[self.i-1]] = {'Onsets': self.syllable_onsets, 'Offsets': self.syllable_offsets}
        # go to next file
        if self.i == len(self.files):
            self.write()
        else:
            self.next()

    def toss(self):
        # send file name to .txt or send file to folder
        self.save_tossed[self.i-1] = {'FileName': self.files[self.i-1]}
        # print(self.save_tossed)
        if self.i == len(self.files):
            self.write()
        else:
            self.next()

    def write(self):
        # write save_parameters to files
        with open((self.parent.directory + 'segmentedSyllables_parameters'), 'w') as params:
            params_fields = ['FileName', 'HighPassFilter', 'PercentSignalKept', 'MinSilenceDuration',
                             'MinSyllableDuration']
            params_file = csv.DictWriter(params, params_fields, delimiter='\t')
            params_file.writeheader()
            for key, val in self.save_parameters.items():
                row = {'FileName': key}
                row.update(val)
                params_file.writerow(row)
            params.close()
        with open((self.parent.directory + 'segmentedSyllables_syllables'), 'w') as sylls:
            sylls_fields = ['FileName', 'Onsets', 'Offsets']
            sylls_file = csv.DictWriter(sylls, sylls_fields, delimiter='\t')
            sylls_file.writeheader()
            for key, val in self.save_syllables.items():
                row = {'FileName': key}
                row.update(val)
                sylls_file.writerow(row)
            sylls.close()
        # !!!!try using pandas dataframe --> to csv!!!
        with open((self.parent.directory + 'segmentedSyllables_tossed'), 'w') as tossed:
            tossed_fields = ['FileName']
            tossed_file = csv.DictWriter(tossed, tossed_fields, delimiter='\t')
            tossed_file.writeheader()
            for key, val in self.save_tossed.items():
                row = {'FileName': key}
                row.update(val)
                tossed_file.writerow(row)
            tossed.close()
        self.done_window()

    def done_window(self):
        done_popup = DonePopup()
        done_popup.open()


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


class MyRangeSlider(RangeSlider):
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        super(MyRangeSlider, self).__init__(**kwargs)

    def on_release(self):
        pass

    def on_touch_up(self, touch):
        super(MyRangeSlider, self).on_touch_up(touch)
        if touch.grab_current == self:
            self.dispatch('on_release')
            return True


class SegmentSyllablesGUI_withJamesApp(App):
    def build(self):
        return Manager()

if __name__ == "__main__":
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    # mouse = Mouse, disable_multitouch
    Window.fullscreen = 'auto'
    SegmentSyllablesGUI_withJamesApp().run()
