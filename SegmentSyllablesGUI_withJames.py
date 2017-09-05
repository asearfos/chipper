import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from RangeSlider_FromGoogle import RangeSlider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.config import Config
from kivy.uix.behaviors.focus import FocusBehavior

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib.backend_kivy import FigureCanvasKivy
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
plt.style.use('dark_background')

import re
import numpy as np
import csv
import math
import matplotlib.transforms as tx


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
    def __init__(self, **kwargs):
        super(ControlPanel, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def test(self, event):
        if event.key == 'left' and self.ids.add.state == 'down':
            print('left')
        if event.key == 'right' and self.ids.add.state == 'down':
            print('right')

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.key = keycode[1]
        if keycode[1] == 'left' and self.ids.add.state == 'down':
            print('left')
        if keycode[1] == 'right' and self.ids.add.state == 'down':
            print('right')
        return True

    def add(self, touchx, touchy):
        conversion = np.shape(self.sonogram)[1]/self.ids.graph_binary.size[0]
        graph_location = math.floor((touchx-self.ids.graph_binary.pos[0])*conversion)

        print(graph_location)
        if self.ids.syllable_toggle.state == 'normal':
            self.syllable_onsets = np.append(self.syllable_onsets, graph_location)
            # ymax = 0.75
        else:
            self.syllable_offsets = np.append(self.syllable_offsets, graph_location)
            # ymax = 0.90

        self.image_syllable_marks()
        # use one of the below options to graph as another color/group of lines
        # add_on = self.ax2.axvline(graph_location, ymax=ymax, color='m', linewidth=1)
        # self.plot_binary_canvas.draw()
        # or can plot like this... not sure which is best
        # self.ax2.plot(np.repeat(graph_location, 3), np.tile([0, .75, np.nan], 1), linewidth=2, color='m', transform=self.trans)
        # self.plot_binary_canvas.draw()

    def delete(self, touchx, touchy):
        conversion = np.shape(self.sonogram)[1] / self.ids.graph_binary.size[0]
        graph_location = math.floor((touchx - self.ids.graph_binary.pos[0]) * conversion)

        if self.ids.syllable_toggle.state == 'normal':
            try:
                onsets_list = list(self.syllable_onsets)
                onsets_list.remove(graph_location)
                self.syllable_onsets = np.array(onsets_list)
                print('removed', graph_location)
            except ValueError:
                print('try again', graph_location, self.syllable_onsets)
        else:
            try:
                onsets_list = list(self.syllable_offsets)
                onsets_list.remove(graph_location)
                self.syllable_offsets = np.array(onsets_list)
                print('removed', graph_location)
            except ValueError:
                print('try again', graph_location, self.syllable_offsets)

        self.image_syllable_marks()

    def setup(self):
        self.i = 0
        self.files = seg.initialize(self.parent.directory)
        self.save_parameters = {}
        self.save_syllables = {}
        self.save_tossed = {}
        self.next()

    def next(self):
        # reset default parameters for new song (will be used by update to graph the first attempt)
        self.filter_boundary = 0
        self.percent_keep = 2
        self.min_silence = 10
        self.min_syllable = 20

        # !!!SHOULDN'T NEED THE VALUES SET IN .KV NOW!!!
        # TODO: connect defaults to .kv (would like to do this the other way around) or remove values from .kv
        self.ids.slider_high_pass_filter.value = self.filter_boundary
        self.ids.slider_threshold.value = self.percent_keep
        self.ids.slider_min_silence.value = self.min_silence
        self.ids.slider_min_syllable.value = self.min_syllable
        self.ids.syllable_toggle.state = 'normal'
        self.ids.add.state = 'normal'
        self.ids.delete.state = 'normal'

        # get initial data
        self.sonogram = seg.initial_sonogram(self.i, self.files, self.parent.directory)

        # connect size of sonogram to maximum of sliders for HPF and crop
        [rows, cols] = np.shape(self.sonogram)
        self.ids.slider_high_pass_filter.max = rows
        self.bout_range = [0, cols]  # TODO: make self.cols instead so you don't create arrays in multiple places
        self.ids.range_slider_crop.value1 = self.bout_range[0]
        self.ids.range_slider_crop.value2 = self.bout_range[1]
        self.ids.range_slider_crop.min = self.bout_range[0]
        self.ids.range_slider_crop.max = self.bout_range[1]

        # initialize the matplotlib figures/axes (no data yet)
        self.image_sonogram_initial(rows, cols)  # TODO: decide if rows and cols should be self variables instead of passing into functions
        self.image_binary_initial(rows, cols)

        # run update to load images for the first time for this file
        self.update(rows-self.filter_boundary, self.bout_range, self.percent_keep, self.min_silence, self.min_syllable)

        # increment i so next file will be opened on submit/toss
        self.i += 1

    def update(self, filter_boundary, bout_range, percent_keep, min_silence, min_syllable):
        # update variables based on input to function
        self.filter_boundary = filter_boundary
        self.bout_range = bout_range
        self.percent_keep = percent_keep
        self.min_silence = min_silence
        self.min_syllable = min_syllable
        sonogram = self.sonogram.copy()  # must do this for image to update for some reason

        # run HPF, scale based on average amplitude (increases low amplitude sections), and graph sonogram
        hpf_sonogram = seg.high_pass_filter(filter_boundary, sonogram)
        scaled_sonogram = seg.normalize_amplitude(hpf_sonogram)
        self.image_sonogram(hpf_sonogram)

        # apply threshold to signal, calculate onsets and offsets, plot resultant binary sonogram
        thresh_sonogram = seg.threshold(percent_keep, scaled_sonogram)
        onsets, offsets2, silence_durations, sum_sonogram_scaled, rows = seg.initialize_onsets_offsets(thresh_sonogram)
        syllable_onsets, syllable_offsets = seg.set_min_silence(min_silence, onsets, offsets2, silence_durations)
        # self.syllable_onsets, self.syllable_offsets, syllable_marks = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets, sum_sonogram_scaled, rows)

        syllable_onsets, syllable_offsets = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets)
        self.syllable_onsets, self.syllable_offsets = seg.crop(bout_range, syllable_onsets, syllable_offsets)
        # syllable_marks = seg.create_syllable_marks(self.syllable_onsets, self.syllable_offsets, sum_sonogram_scaled, rows)

        self.image_binary(thresh_sonogram)
        self.image_syllable_marks()
        # return syllable_onsets, syllable_offsets

    def image_sonogram_initial(self, rows, cols):
        data = np.zeros((rows, cols))
        self.fig1, self.ax1 = plt.subplots()
        self.plot_sonogram_canvas = FigureCanvasKivyAgg(self.fig1)

        # make plot take up the entire space
        self.ax1 = plt.Axes(self.fig1, [0., 0., 1., 1.])
        self.ax1.set_axis_off()
        self.fig1.add_axes(self.ax1)

        # plot data
        self.plot_sonogram = self.ax1.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')

        # create widget
        self.ids.graph_sonogram.clear_widgets()
        self.ids.graph_sonogram.add_widget(self.plot_sonogram_canvas)  # doesn't work without draw

    def image_sonogram(self, data):
        # self.ids.graph_sonogram.clear_widgets()
        # self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(self.fig1))
        # self.plot_sonogram.set_data(np.log(data+3))
        # self.plot_sonogram.autoscale()

        # TODO: !!!SHOULD BE ABLE TO SPEED UP FASTER LIKE THIS BUT CAN'T GET TO WORK!!!
        self.plot_sonogram.set_data(np.log(data+3))
        self.plot_sonogram.autoscale()
        self.plot_sonogram_canvas.draw()
        # self.ax1.draw_artist(self.ax1.patch)
        # self.ax1.draw_artist(self.plot_sonogram)
        # self.plot_sonogram_canvas.update()
        # self.plot_sonogram_canvas.flush_events()  # supposed to get rid of the lag due to sleep

    def image_binary_initial(self, rows, cols):
        data = np.zeros((rows, cols))
        # self.lines = {}
        self.fig2, self.ax2 = plt.subplots()
        # x = [0]

        # make plot take up the entire space
        self.ax2 = plt.Axes(self.fig2, [0., 0., 1., 1.])
        self.ax2.set_axis_off()
        self.fig2.add_axes(self.ax2)

        # plot data
        self.plot_binary = self.ax2.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')

        self.trans = tx.blended_transform_factory(self.ax2.transData, self.ax2.transAxes)
        self.lines_on, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .75, np.nan], 1), linewidth=1, color='g', transform=self.trans)
        self.lines_off, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .90, np.nan], 1), linewidth=1, color='g', transform=self.trans)
        # self.add_on, = self.ax2.plot(np.repeat(x, 3), np.tile([0, .75, np.nan], len(x)), linewidth=2, color='g', transform=self.trans)

        self.ids.graph_binary.clear_widgets()
        self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        self.fig2.canvas.mpl_connect('key_press_event', self.test)
        self.ids.graph_binary.add_widget(self.plot_binary_canvas)

        # self.plot_binary_canvas.draw()

        # self.vert_on = self.ax2.axvline(ymax=0.90, color='m', linewidth=1)

        # self.lines[0] = self.ax2.vlines(0, ymin=0, ymax=0, colors='m', linewidth=0.5)

    def image_binary(self, data):
        # self.ids.graph_binary.clear_widgets()
        # self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        # self.ids.graph_binary.add_widget(self.plot_binary_canvas)
        self.plot_binary.set_data(np.log(data+3))
        self.plot_binary.autoscale()

    def image_syllable_marks(self):
        self.lines_on.set_xdata(np.repeat(self.syllable_onsets, 3))
        self.lines_on.set_ydata(np.tile([0, .75, np.nan], len(self.syllable_onsets)))
        # self.fig2.canvas.show()
        self.plot_binary_canvas.draw()

        self.lines_off.set_xdata(np.repeat(self.syllable_offsets, 3))
        self.lines_off.set_ydata(np.tile([0, .90, np.nan], len(self.syllable_offsets)))
        # self.fig2.canvas.show()
        self.plot_binary_canvas.draw()

        # self.ax2.draw_artist(self.ax2.patch)
        # self.ax2.draw_artist(self.lines)
        # self.plot_binary_canvas.update()
        # self.plot_binary_canvas.flush_events()

        # for x in self.syllable_onsets.astype(np.int64):
        #     self.vert_on.set_xdata(x)
        #     self.plot_binary_canvas.draw()
            # self.vert_on = self.ax2.axvline(x, ymax=0.90, color='m', linewidth=1)
        # for x in self.syllable_offsets.astype(np.int64):
        #     self.vert_off = self.ax2.axvline(x, color='m', linewidth=1)
        # self.vert.set_xdata(xdata=indexes)

        # remove old lines and replot onsets and offsets
        # self.lines.pop(0).remove()
        # indexes = np.squeeze(np.nonzero(syllable_marks))
        # ymin = np.zeros(len(indexes))
        # ymax = syllable_marks[syllable_marks != 0]
        # self.lines[0] = self.ax2.vlines(indexes, ymin=ymin, ymax=ymax, colors='m', linewidth=0.5)

    def save(self):
        # save parameters to dictionary
        self.save_parameters[self.files[self.i-1]] = {'HighPassFilter': self.filter_boundary, 'PercentSignalKept': self.percent_keep, 'MinSilenceDuration': self.min_silence, 'MinSyllableDuration': self.min_syllable}
        self.save_syllables[self.files[self.i-1]] = {'Onsets': self.syllable_onsets, 'Offsets': self.syllable_offsets}

        # write if last file otherwise go to next file
        if self.i == len(self.files):
            self.write()
        else:
            self.next()

    def toss(self):
        # save file name to dictionary
        self.save_tossed[self.i-1] = {'FileName': self.files[self.i-1]}

        # write if last file otherwise go to next file
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
        # TODO: !!!!try using pandas dataframe --> to csv!!!
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
    Window.fullscreen = 'auto'
    SegmentSyllablesGUI_withJamesApp().run()
