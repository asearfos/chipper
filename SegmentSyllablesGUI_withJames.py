import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from RangeSlider_FromGoogle import RangeSlider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.config import Config
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.logger import Logger
# Logger.disabled = True

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib.backend_kivy import FigureCanvasKivy
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import matplotlib.transforms as tx
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
plt.style.use('dark_background')


from bisect import bisect_left, bisect_right, insort
import numpy as np
import pandas as pd
import os
import math
import time
from kivy.clock import Clock
from time import sleep


# import my own functions for data analysis
import segmentSylls_functionsForGUI as seg


class Manager(ScreenManager):
    pass


class FileExplorer(Screen):
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
    len_onsets = StringProperty()
    len_offsets = StringProperty()


class CheckBeginningEndPopup(Popup):
    start_onset = BooleanProperty()
    end_offset = BooleanProperty()
    two_onsets = BooleanProperty()
    two_offsets = BooleanProperty()


class CheckOrderPopup(Popup):
    order = ListProperty()


class DonePopup(Popup):
    def quit_app(self):
        print('song segmentation complete, Close SegmentSyllablesGUI.')
        quit()


class ZoomPopup(Popup):
    def __init__(self, zoom_x, zoom_y, zoom_data, rows, cols, **kwargs):
        super(ZoomPopup, self).__init__(**kwargs)
        self.zoom_x = zoom_x
        self.zoom_y = zoom_y
        self.zoom_data = zoom_data
        self.rows = rows
        self.cols = cols

        # top_image = ObjectProperty(None)

        # axzoom = figzoom.add_subplot(111, xlim=(0.45, 0.55), ylim=(0.4, .6),
        #                              autoscale_on=False)

        self.figzoom, self.axzoom = plt.subplots()
        # self.zoom_canvas = FigureCanvasKivyAgg(self.figzoom)

        self.axzoom = plt.Axes(self.figzoom, [0., 0., 1., 1.])
        self.axzoom.set_axis_off()
        self.figzoom.add_axes(self.axzoom)

        self.zoom_plot = self.axzoom.imshow(self.zoom_data, cmap='jet', extent=[0, self.cols, 0, self.rows], aspect='auto')

        self.axzoom.set_xlim(self.zoom_x - 1000, self.zoom_x + 1000)
        self.axzoom.set_ylim(0, self.rows)

        # self.zoom_canvas.draw()

        # create widget
        # self.clear_widgets()
        self.zoom_canvas = FigureCanvasKivyAgg(self.figzoom)
        self.add_widget(self.zoom_canvas)


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
                    self.graph_location -= 7
                self.update_mark(self.graph_location)
            elif event.key == 'right':
                # print('length', self.cols)
                # print('location', self.graph_location)
                if self.graph_location < self.cols-25: #the mark is not resolved on the screen past this even though it is still within the size of the image
                    self.graph_location += 7
                self.update_mark(self.graph_location)
            elif event.key == 'enter':
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
                if self.ids.syllable_beginning.state == 'down':
                    if self.index < 0:
                        self.index = len(self.syllable_onsets) - 1
                    self.update_mark(self.syllable_onsets[self.index])
                else:
                    if self.index < 0:
                        self.index = len(self.syllable_offsets) - 1
                    self.update_mark(self.syllable_offsets[self.index])
            elif event.key == 'right':
                self.index += 1
                if self.ids.syllable_beginning.state == 'down':
                    if self.index >= len(self.syllable_onsets):
                        self.index = 0
                    self.update_mark(self.syllable_onsets[self.index])
                else:
                    if self.index >= len(self.syllable_offsets):
                        self.index = 0
                    self.update_mark(self.syllable_offsets[self.index])
            elif event.key == 'enter':
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
            if self.ids.syllable_beginning.state == 'down':
                self.add_onsets()
            else:
                self.add_offsets()
        elif self.ids.delete.state == 'down':  # deleting
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

    def zoom(self, touchx, touchy):
        zoom_popup = ZoomPopup(touchx, touchy, self.zoom_data, self.rows, self.cols)
        # zoom_popup.zoom_x, zoom_popup.zoom_y = touchx, touchy
        zoom_popup.open()

    def add_mark(self, touchx, touchy):
        self.mark_boolean = True
        conversion = np.shape(self.sonogram)[1]/self.ids.graph_binary.size[0]
        self.graph_location = math.floor((touchx-self.ids.graph_binary.pos[0])*conversion)

        if self.ids.syllable_beginning.state == 'down':
            ymax = 0.75
        else:
            ymax = 0.90

        # self.image_syllable_marks()
        # self.bottom_image.image_syllable_marks(self.syllable_onsets, self.syllable_offsets)

        # use one of the below options to graph as another color/group of lines
        self.mark = self.ax2.axvline(self.graph_location, ymax=ymax, color='m', linewidth=0.75)
        self.plot_binary_canvas.draw()
        # or can plot like this... not sure which is best
        # self.ax2.plot(np.repeat(graph_location, 3), np.tile([0, .75, np.nan], 1), linewidth=2, color='m', transform=self.trans)
        # self.plot_binary_canvas.draw()

    def add_onsets(self):
        # TODO: might be able to just use bisect.insort(list, new number) https://stackoverflow.com/questions/29408661/add-elements-into-a-sorted-array-in-ascending-order
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
        From: https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
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

        self.mark = self.ax2.axvline(location, ymax=ymax, color='m', linewidth=0.75)
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
        self.save_threshold_sonogram = {}
        self.next()
        self.output_path = self.parent.directory + "Output_" + time.strftime("%m%d%Y")
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)
        # else:
        #     print(self.output_path + ' already exists')
        #     quit()

    def reset_parameters(self):
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
        self.ids.syllable_beginning.state = 'down'
        self.ids.syllable_ending.state = 'normal'
        self.ids.add.state = 'normal'
        self.ids.delete.state = 'normal'

        # connect size of sonogram to maximum of sliders for HPF and crop
        [self.rows, self.cols] = np.shape(self.sonogram)
        self.ids.slider_high_pass_filter.max = self.rows
        self.bout_range = [0, self.cols]  # TODO: make self.cols instead so you don't create arrays in multiple places
        self.ids.range_slider_crop.value1 = self.bout_range[0]
        self.ids.range_slider_crop.value2 = self.bout_range[1]
        self.ids.range_slider_crop.min = self.bout_range[0]
        self.ids.range_slider_crop.max = self.bout_range[1]

        # run update to load images for the first time for this file
        self.update(self.rows-self.filter_boundary, self.bout_range, self.percent_keep, self.min_silence, self.min_syllable)

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
        self.ids.syllable_beginning.state = 'down'
        self.ids.syllable_ending.state = 'normal'
        self.ids.add.state = 'normal'
        self.ids.delete.state = 'normal'
        self.ids.current_file.text = self.files[self.i-1] + '\nFile ' + str(self.i+1) + ' out of ' + str(len(self.files))

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
        self.thresh_sonogram = seg.threshold_image(percent_keep, scaled_sonogram)
        onsets, offsets2, silence_durations, sum_sonogram_scaled = seg.initialize_onsets_offsets(self.thresh_sonogram)
        syllable_onsets, syllable_offsets = seg.set_min_silence(min_silence, onsets, offsets2, silence_durations)
        syllable_onsets, syllable_offsets = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets)
        self.syllable_onsets, self.syllable_offsets = seg.crop(bout_range, syllable_onsets, syllable_offsets)

        self.image_binary()
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
        # self.zoom_data = np.log(data+3)

        self.trans = tx.blended_transform_factory(self.ax2.transData, self.ax2.transAxes)
        self.lines_on, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .75, np.nan], 1), linewidth=0.75, color='g', transform=self.trans)
        self.lines_off, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .90, np.nan], 1), linewidth=0.75, color='g', transform=self.trans)
        # self.add_on, = self.ax2.plot(np.repeat(x, 3), np.tile([0, .75, np.nan], len(x)), linewidth=2, color='g', transform=self.trans)

        scalebar = AnchoredSizeBar(self.ax2.transData,
                                   100, '100', 1,
                                   pad=0.1,
                                   color='white',
                                   frameon=False,
                                   size_vertical=2)
        self.ax2.add_artist(scalebar)

        self.ids.graph_binary.clear_widgets()
        self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        self.fig2.canvas.mpl_connect('key_press_event', self.move_mark)
        self.ids.graph_binary.add_widget(self.plot_binary_canvas)
        # self.plot_binary_canvas.draw()

        # self.vert_on = self.ax2.axvline(ymax=0.90, color='m', linewidth=1)

        # self.lines[0] = self.ax2.vlines(0, ymin=0, ymax=0, colors='m', linewidth=0.5)

    def image_binary(self):
        # self.ids.graph_binary.clear_widgets()
        # self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        # self.ids.graph_binary.add_widget(self.plot_binary_canvas)
        self.plot_binary.set_data(np.log(self.thresh_sonogram+3))
        self.plot_binary.autoscale()

        self.zoom_data = np.log(self.thresh_sonogram+3)


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

    def back(self):
        self.i -= 2
        self.next()

    def save(self):
        if len(self.syllable_onsets) != len(self.syllable_offsets):
            check_length = CheckLengthPopup()
            check_length.len_onsets = str(len(self.syllable_onsets))
            check_length.len_offsets = str(len(self.syllable_offsets))
            check_length.open()
        elif self.syllable_onsets[0] > self.syllable_offsets[0] or self.syllable_onsets[-1] > self.syllable_offsets[-1]:
            check_beginning_end = CheckBeginningEndPopup()
            check_beginning_end.start_onset = not self.syllable_onsets[0] > self.syllable_offsets[0]
            check_beginning_end.end_offset = not self.syllable_onsets[-1] > self.syllable_offsets[-1]
            check_beginning_end.open()
        else:
            combined_onsets_offsets = list(self.syllable_onsets)
            binary_list = [0] * len(self.syllable_onsets)
            for i in range(len(self.syllable_offsets)):
                insertion_pt = bisect_right(combined_onsets_offsets, self.syllable_offsets[i])
                binary_list.insert(insertion_pt, 1)
                insort(combined_onsets_offsets, self.syllable_offsets[i])
            if sum(binary_list[::2]) != 0 or sum(binary_list[1::2]) != len(binary_list)/2:  # using python slices
                check_order = CheckOrderPopup()
                check_order.order = binary_list
                check_order.open()
            else:
                # save parameters to dictionary
                self.save_parameters[self.files[self.i-1]] = {'HighPassFilter': self.filter_boundary, 'BoutRange': self.bout_range, 'PercentSignalKept': self.percent_keep, 'MinSilenceDuration': self.min_silence, 'MinSyllableDuration': self.min_syllable}
                self.save_syllables[self.files[self.i-1]] = {'Onsets': self.syllable_onsets.tolist(), 'Offsets': self.syllable_offsets.tolist()}
                self.save_threshold_sonogram[self.files[self.i-1]] = {'Sonogram': self.thresh_sonogram.tolist()}

                # start = time.time()
                # # To write each one to it's own file --> this takes a long time and user has to wait between songs
                # # pd.DataFrame(self.thresh_sonogram).to_csv((self.output_path + "\\threshold_sonogram_" + self.files[self.i-1] + '.txt'), sep="\t", index=False, header=False)
                # print(time.time()-start)

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

        df_parameters = pd.DataFrame.from_dict(self.save_parameters, orient='index')
        df_parameters.index.name = 'FileName'
        df_parameters.to_csv((self.output_path + '\segmentedSyllables_parameters.txt'), sep="\t")

        df_syllables = pd.DataFrame.from_dict(self.save_syllables, orient='index')
        df_syllables.index.name = 'FileName'
        df_syllables.to_csv((self.output_path + '\segmentedSyllables_syllables.txt'), sep="\t")

        df_threshold_sonogram = pd.DataFrame.from_dict(self.save_threshold_sonogram, orient='index')
        df_threshold_sonogram.index.name = 'FileName'
        df_threshold_sonogram.to_csv((self.output_path + '\\threshold_sonogram.txt'), sep="\t", header=False)

        df_tossed = pd.DataFrame.from_dict(self.save_tossed, orient='index')
        # df_tossed.index.name = 'FileName'
        df_tossed.to_csv((self.output_path + '\segmentedSyllables_tossed.txt'), sep="\t", index=False)

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
