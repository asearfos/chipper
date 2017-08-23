import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen

#from kivy.uix.filechooser import FileChooser

from os.path import sep, expanduser, isdir, dirname
from kivy.garden.filebrowser import FileBrowser
from kivy.utils import platform

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt

import numpy as np
import segmentSylls_functionsForGUI as seg
import csv


class Manager(ScreenManager):
    pass


class ScreenOne(Screen):
    def _fbrowser_canceled(self, instance):
        print ('cancelled, Close self.')

    def _fbrowser_success(self, instance):
        print (instance.selection)
    #
    # def getBrowser(self):
    #     if platform == 'win':
    #         user_path = dirname(expanduser('~')) + sep + 'Documents'
    #     else:
    #         user_path = expanduser('~') + sep + 'Documents'
    #     browser = FileBrowser(select_string='Select',
    #                           favorites=[(user_path, 'Documents')])
    #     browser.bind(
    #                 on_success=self._fbrowser_success,
    #                 on_canceled=self._fbrowser_canceled)
    #     return browser


class DonePopup(Popup):
    pass


class ControlPanel(Screen):
    def __init__(self, directory, **kwargs):
        super(ControlPanel, self).__init__(**kwargs)
        self.directory = directory

    def setup(self):
        self.i = 0
        self.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/TestingGUI/PracticeBouts/"
        # self.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"
        self.files = seg.initialize(self.directory)
        self.save_parameters = {}
        self.save_syllables = {}
        self.save_tossed = {}
        self.next()

    # def __init__(self,**kwargs):
    #     super(ControlPanel, self).__init__(**kwargs)
    #     self.i = 0
    #     self.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/TestingGUI/PracticeBouts/"
    #     # self.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"
    #     self.files = seg.initialize(self.directory)
    #     self.save_parameters = {}
    #     self.save_syllables = {}
    #     self.save_tossed = {}
    #     #self.next()

    def next(self):
        # set default parameters
        self.filter_boundary = 0
        self.percent_keep = 2
        self.min_silence = 10
        self.min_syllable = 20

        # connect defaults to .kv (would like to do this the other way around)
        self.ids.slider_high_pass_filter.value = self.filter_boundary
        self.ids.slider_threshold.value = self.percent_keep
        self.ids.slider_min_silence.value = self.min_silence
        self.ids.slider_min_syllable.value = self.min_syllable

        self.sonogram = seg.initial_sonogram(self.i, self.files, self.directory)
        # run update to load images for the first time for this file
        self.syllable_onsets, self.syllable_offsets = self.update(self.sonogram, 513-self.filter_boundary, self.percent_keep, self.min_silence, self.min_syllable)
        self.i += 1

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
        with open((self.directory + 'segmentedSyllables_parameters'), 'w') as params:
            params_fields = ['FileName', 'HighPassFilter', 'PercentSignalKept', 'MinSilenceDuration',
                             'MinSyllableDuration']
            params_file = csv.DictWriter(params, params_fields, delimiter='\t')
            params_file.writeheader()
            for key, val in self.save_parameters.items():
                row = {'FileName': key}
                row.update(val)
                params_file.writerow(row)
            params.close()
        with open((self.directory + 'segmentedSyllables_syllables'), 'w') as sylls:
            sylls_fields = ['FileName', 'Onsets', 'Offsets']
            sylls_file = csv.DictWriter(sylls, sylls_fields, delimiter='\t')
            sylls_file.writeheader()
            for key, val in self.save_syllables.items():
                row = {'FileName': key}
                row.update(val)
                sylls_file.writerow(row)
            sylls.close()
        # try using pandas dataframe --> to csv
        with open((self.directory + 'segmentedSyllables_tossed'), 'w') as tossed:
            tossed_fields = ['FileName']
            tossed_file = csv.DictWriter(tossed, tossed_fields, delimiter='\t')
            tossed_file.writeheader()
            for key, val in self.save_tossed.items():
                row = {'FileName': key}
                row.update(val)
                tossed_file.writerow(row)
            tossed.close()
        self.done_window()

    def update(self, sonogram, filter_boundary, percent_keep, min_silence, min_syllable):
        self.filter_boundary = filter_boundary
        self.percent_keep = percent_keep
        self.min_silence = min_silence
        self.min_syllable = min_syllable
        #sonogram = seg.initial_sonogram(self.i, self.files, self.directory)
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

    def image_sonogram(self, data):
        self.ids.graph_sonogram.clear_widgets()

        [rows, cols] = np.shape(data)
        plt.style.use('dark_background')
        fig1 = plt.figure()
        plot_sonogram = plt.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
        #plot_sonogram.axes.axis('off')
        fig1.tight_layout()

        fig1 = plt.gcf()
        self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(fig1))
        # look up how to speed up matplotlip --> make one canvas
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

        fig2 = plt.gcf()
        self.ids.graph_binary.add_widget(FigureCanvasKivyAgg(fig2))
        return plot_sonogram

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


class SegmentSyllablesGUI_withJamesApp(App):
    def build(self):
        return Manager()

if __name__ == "__main__":
    SegmentSyllablesGUI_withJamesApp().run()
