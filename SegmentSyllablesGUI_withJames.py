import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from RangeSlider_FromGoogle import RangeSlider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.config import Config
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.logger import Logger
# Logger.disabled = True

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib.backend_kivy import FigureCanvasKivy
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
plt.style.use('dark_background')
from matplotlib.lines import Line2D

from bisect import bisect_left

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


class FinishMarksPopup(Popup):
    def __init__(self, controls, **kwargs):  # controls is now the object where popup was called from.
        # self.register_event_type('on_connect')
        super(FinishMarksPopup, self).__init__(**kwargs)
        self.controls = controls


class CheckLengthPopup(Popup):
    # def __init__(self, len_onsets, len_offsets, **kwargs):  # controls is now the object where popup was called from.
    #     # self.register_event_type('on_connect')
    #     super(CheckLengthPopup, self).__init__(**kwargs)
    #     # self.ids.lengths.text = len_onsets
    #     self.len_onsets = len_onsets
    len_onsets = StringProperty()
    len_offsets = StringProperty()


class DonePopup(Popup):
    pass


class ImageSonogram(GridLayout):

    def image_sonogram_initial(self, rows, cols):
        data = np.zeros((rows, cols))
        self.fig1, self.ax1 = plt.subplots()
        self.plot_sonogram_canvas = FigureCanvasKivyAgg(self.fig1)

        # make plot take up the entire space
        self.ax1 = plt.Axes(self.fig1, [0., 0., 1., 1.])
        self.ax1.set_axis_off()
        self.fig1.add_axes(self.ax1)

        # plot data
        self.plot_sonogram = self.ax1.imshow(np.log(data + 3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')

        # create widget
        self.clear_widgets()
        self.add_widget(self.plot_sonogram_canvas)


    def image_sonogram(self, data):
        self.plot_sonogram.set_data(np.log(data + 3))
        self.plot_sonogram.autoscale()
        self.plot_sonogram_canvas.draw()

        # TODO: !!!SHOULD BE ABLE TO SPEED UP FASTER LIKE THIS BUT CAN'T GET TO WORK!!!
        # self.ax1.draw_artist(self.ax1.patch)
        # self.ax1.draw_artist(self.plot_sonogram)
        # self.canvas.update()
        # self.canvas.flush_events


class ControlPanel(Screen):
    top_image = ObjectProperty(None)
    mark_boolean = False
    click = 0
    # bottom_image = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_check_boolean')
        super(ControlPanel, self).__init__(**kwargs)

    def on_check_boolean(self):
        if self.click >= 2:
            marks_popup = FinishMarksPopup(self)
            marks_popup.open()

    def on_touch_down(self, touch):
        super(ControlPanel, self).on_touch_down(touch)
        if self.mark_boolean is True:
            self.click += 1
            self.dispatch('on_check_boolean')
            ControlPanel.disabled = True
            return True

    def move_mark(self, event):
        if self.ids.add.state == 'down':  # adding
            if event.key == 'left':
                if self.graph_location >= 25:
                    self.graph_location -= 5
                self.update_mark(self.graph_location)
            elif event.key == 'right':
                # print('length', self.cols)
                # print('location', self.graph_location)
                if self.graph_location < self.cols-25: #the mark is not resolved on the screen past this even though it is still within the size of the image
                    self.graph_location += 5
                # print('updated location', self.graph_location)
                self.update_mark(self.graph_location)
            elif event.key == 'enter':
                # if self.ids.syllable_toggle.state == 'normal':
                if self.ids.syllable_beginning.state == 'down':
                    self.add_onsets()
                else:
                    self.add_offsets()
                self.mark_boolean = False
                self.click = 0
                ControlPanel.disabled = False
            elif event.key == 'x':
                self.cancel_mark()
        elif self.ids.delete.state == 'down':  # deleting
            if event.key == 'left':
                self.index -= 1
                # if self.ids.syllable_toggle.state == 'normal':
                if self.ids.syllable_beginning.state == 'down':
                    if self.index < 0:
                        self.index = len(self.syllable_onsets) - 1
                    self.update_mark(self.syllable_onsets[self.index])
                else:
                    self.update_mark(self.syllable_offsets[self.index])
            elif event.key == 'right':
                self.index += 1
                # if self.ids.syllable_toggle.state == 'normal':
                if self.ids.syllable_beginning.state == 'down':
                    if self.index >= len(self.syllable_onsets):
                        self.index = 0
                    self.update_mark(self.syllable_onsets[self.index])
                else:
                    self.update_mark(self.syllable_offsets[self.index])
            elif event.key == 'enter':
                # if self.ids.syllable_toggle.state == 'normal':
                if self.ids.syllable_beginning.state == 'down':
                    self.delete_onsets()
                else:
                    self.delete_offsets()
                self.mark_boolean = False
                self.click = 0
                ControlPanel.disabled = False
            elif event.key == 'x':
                self.cancel_mark()

    def enter_mark(self):
        if self.ids.add.state == 'down':  # adding
            # if self.ids.syllable_toggle.state == 'normal':
            if self.ids.syllable_beginning.state == 'down':
                self.add_onsets()
            else:
                self.add_offsets()
        elif self.ids.delete.state == 'down':  # deleting
            # if self.ids.syllable_toggle.state == 'normal':
            if self.ids.syllable_beginning.state == 'down':
                self.delete_onsets()
            else:
                self.delete_offsets()
        self.mark_boolean = False
        self.click = 0
        ControlPanel.disabled = False

    def cancel_mark(self):
        self.mark.remove()
        self.image_syllable_marks()
        self.mark_boolean = False
        self.click = 0
        ControlPanel.disabled = False

    def update_mark(self, new_mark):
        self.mark.set_xdata(new_mark)
        self.plot_binary_canvas.draw()

    def add_mark(self, touchx, touchy):
        self.mark_boolean = True
        conversion = np.shape(self.sonogram)[1]/self.ids.graph_binary.size[0]
        self.graph_location = math.floor((touchx-self.ids.graph_binary.pos[0])*conversion)

        # if self.ids.syllable_toggle.state == 'normal':
        if self.ids.syllable_beginning.state == 'down':
            ymax = 0.75
        else:
            ymax = 0.90

        # self.image_syllable_marks()
        # self.bottom_image.image_syllable_marks(self.syllable_onsets, self.syllable_offsets)

        # use one of the below options to graph as another color/group of lines
        self.mark = self.ax2.axvline(self.graph_location, ymax=ymax, color='m', linewidth=.5)
        self.plot_binary_canvas.draw()
        # or can plot like this... not sure which is best
        # self.ax2.plot(np.repeat(graph_location, 3), np.tile([0, .75, np.nan], 1), linewidth=2, color='m', transform=self.trans)
        # self.plot_binary_canvas.draw()

    def add_onsets(self):
        self.syllable_onsets = np.insert(self.syllable_onsets, np.searchsorted(self.syllable_onsets, self.graph_location), self.graph_location)
        self.mark.remove()
        self.image_syllable_marks()

    def add_offsets(self):
        self.syllable_offsets = np.insert(self.syllable_offsets, np.searchsorted(self.syllable_offsets, self.graph_location), self.graph_location)
        self.mark.remove()
        self.image_syllable_marks()

    def takeClosest(self, myList, myNumber):
        """
        Assumes myList is sorted. Returns index of closest value to myNumber.

        If two numbers are equally close, return the index of the smallest number.
        """
        pos = bisect_left(myList, myNumber)
        if pos == 0:
            return pos
        if pos == len(myList):
            return -1
        before = myList[pos - 1]
        after = myList[pos]
        if after - myNumber < myNumber - before:
            return pos
        else:
            return pos-1

    def delete_mark(self, touchx, touchy):
        self.mark_boolean = True
        conversion = np.shape(self.sonogram)[1] / self.ids.graph_binary.size[0]
        self.graph_location = math.floor((touchx - self.ids.graph_binary.pos[0]) * conversion)

        # if self.ids.syllable_toggle.state == 'normal':
        if self.ids.syllable_beginning.state == 'down':
            ymax = 0.75
            # find nearest onset
            self.index = self.takeClosest(self.syllable_onsets, self.graph_location)
            location = self.syllable_onsets[self.index]
        else:
            ymax = 0.90
            # find nearest offset
            self.index = self.takeClosest(self.syllable_offsets, self.graph_location)
            location = self.syllable_offsets[self.index]

        self.mark = self.ax2.axvline(location, ymax=ymax, color='m', linewidth=0.5)
        self.plot_binary_canvas.draw()

    def delete_onsets(self):
        onsets_list = list(self.syllable_onsets)
        onsets_list.remove(self.syllable_onsets[self.index])
        self.syllable_onsets = np.array(onsets_list)
        self.mark.remove()
        self.image_syllable_marks()

    def delete_offsets(self):
        offsets_list = list(self.syllable_offsets)
        offsets_list.remove(self.syllable_offsets[self.index])
        self.syllable_offsets = np.array(offsets_list)
        self.mark.remove()
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
        # self.ids.syllable_toggle.state = 'normal'
        self.ids.syllable_beginning.state = 'down'
        self.ids.add.state = 'normal'
        self.ids.delete.state = 'normal'

        # get initial data
        self.sonogram = seg.initial_sonogram(self.i, self.files, self.parent.directory)

        # connect size of sonogram to maximum of sliders for HPF and crop
        [self.rows, self.cols] = np.shape(self.sonogram)
        self.ids.slider_high_pass_filter.max = self.rows
        self.bout_range = [0, self.cols]  # TODO: make self.cols instead so you don't create arrays in multiple places
        self.ids.range_slider_crop.value1 = self.bout_range[0]
        self.ids.range_slider_crop.value2 = self.bout_range[1]
        self.ids.range_slider_crop.min = self.bout_range[0]
        self.ids.range_slider_crop.max = self.bout_range[1]

        # initialize the matplotlib figures/axes (no data yet)
        self.top_image.image_sonogram_initial(self.rows, self.cols)  # TODO: decide if rows and cols should be self variables instead of passing into functions
        self.image_binary_initial()

        # run update to load images for the first time for this file
        self.update(self.rows-self.filter_boundary, self.bout_range, self.percent_keep, self.min_silence, self.min_syllable)

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
        self.top_image.image_sonogram(hpf_sonogram)

        # apply threshold to signal, calculate onsets and offsets, plot resultant binary sonogram
        thresh_sonogram = seg.threshold_image(percent_keep, scaled_sonogram)
        onsets, offsets2, silence_durations, sum_sonogram_scaled = seg.initialize_onsets_offsets(thresh_sonogram)
        syllable_onsets, syllable_offsets = seg.set_min_silence(min_silence, onsets, offsets2, silence_durations)
        syllable_onsets, syllable_offsets = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets)
        self.syllable_onsets, self.syllable_offsets = seg.crop(bout_range, syllable_onsets, syllable_offsets)

        self.image_binary(thresh_sonogram)
        self.image_syllable_marks()
        # self.bottom_image.image_syllable_marks(self.syllable_onsets, self.syllable_offsets)

    # def image_sonogram_initial(self, rows, cols):
    #     data = np.zeros((rows, cols))
    #     self.fig1, self.ax1 = plt.subplots()
    #     self.plot_sonogram_canvas = FigureCanvasKivyAgg(self.fig1)
    #
    #     # make plot take up the entire space
    #     self.ax1 = plt.Axes(self.fig1, [0., 0., 1., 1.])
    #     self.ax1.set_axis_off()
    #     self.fig1.add_axes(self.ax1)
    #
    #     # plot data
    #     self.plot_sonogram = self.ax1.imshow(np.log(data+3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')
    #
    #     # create widget
    #     self.ids.graph_sonogram.clear_widgets()
    #     self.ids.graph_sonogram.add_widget(self.plot_sonogram_canvas)  # doesn't work without draw
    #
    # def image_sonogram(self, data):
    #     # self.ids.graph_sonogram.clear_widgets()
    #     # self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(self.fig1))
    #     # self.plot_sonogram.set_data(np.log(data+3))
    #     # self.plot_sonogram.autoscale()
    #
    #     # TODO: !!!SHOULD BE ABLE TO SPEED UP FASTER LIKE THIS BUT CAN'T GET TO WORK!!!
    #     self.plot_sonogram.set_data(np.log(data+3))
    #     self.plot_sonogram.autoscale()
    #     self.plot_sonogram_canvas.draw()
    #     # self.ax1.draw_artist(self.ax1.patch)
    #     # self.ax1.draw_artist(self.plot_sonogram)
    #     # self.plot_sonogram_canvas.update()
    #     # self.plot_sonogram_canvas.flush_events()  # supposed to get rid of the lag due to sleep

    def image_binary_initial(self):
        data = np.zeros((self.rows, self.cols))
        # self.lines = {}
        self.fig2, self.ax2 = plt.subplots()
        # x = [0]

        # make plot take up the entire space
        self.ax2 = plt.Axes(self.fig2, [0., 0., 1., 1.])
        self.ax2.set_axis_off()
        self.fig2.add_axes(self.ax2)

        # plot data
        self.plot_binary = self.ax2.imshow(np.log(data+3), cmap='jet', extent=[0, self.cols, 0, self.rows], aspect='auto')

        self.trans = tx.blended_transform_factory(self.ax2.transData, self.ax2.transAxes)
        self.lines_on, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .75, np.nan], 1), linewidth=0.5, color='g', transform=self.trans)
        self.lines_off, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .90, np.nan], 1), linewidth=0.5, color='g', transform=self.trans)
        # self.add_on, = self.ax2.plot(np.repeat(x, 3), np.tile([0, .75, np.nan], len(x)), linewidth=2, color='g', transform=self.trans)

        self.ids.graph_binary.clear_widgets()
        self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        self.fig2.canvas.mpl_connect('key_press_event', self.move_mark)
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
        self.lines_off.set_xdata(np.repeat(self.syllable_offsets, 3))
        self.lines_off.set_ydata(np.tile([0, .90, np.nan], len(self.syllable_offsets)))
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
        if len(self.syllable_onsets) != len(self.syllable_offsets):
            # check_length = CheckLengthPopup(len(self.syllable_onsets), len(self.syllable_offsets))
            check_length = CheckLengthPopup()
            check_length.len_onsets = str(len(self.syllable_onsets))
            check_length.len_offsets = str(len(self.syllable_offsets))
            check_length.open()
        else:
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
    # Window.fullscreen = 'auto'
    SegmentSyllablesGUI_withJamesApp().run()
