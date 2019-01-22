import matplotlib
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
# from SegSylls_ImageSonogram import ImageSonogram
from kivy.uix.screenmanager import Screen

import chipper.functions as seg
from chipper.popups import FinishMarksPopup, CheckLengthPopup, CheckForSyllablesPopup,\
    CheckBeginningEndPopup, CheckOrderPopup, \
    DonePopup

matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
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
from chipper.utils import save_gzip_pickle


# TODO improve how self variables are being used; some have the same variable but not self as function inputs....
class ControlPanel(Screen):
    find_gzips = BooleanProperty()
    user_signal_thresh = StringProperty()
    user_min_silence = StringProperty()
    user_min_syllable = StringProperty()

    def __init__(self, **kwargs):
        self.top_image = ObjectProperty(None)
        self.mark_boolean = False
        self.click = 0
        self.direction_to_int = {'left': -1, 'right': 1}
        # bottom_image = ObjectProperty(None)

        self.register_event_type('on_check_boolean')

        self.fig2, self.ax2 = plt.subplots()
        self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        self.fig2.canvas.mpl_connect('key_press_event', self.move_mark)

        self.ax2 = plt.Axes(self.fig2, [0., 0., 1., 1.])
        self.ax2.set_axis_off()
        self.fig2.add_axes(self.ax2)

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

    def reset_panel(self):
        self.mark_boolean = False
        self.click = 0
        ControlPanel.disabled = False

    def move_mark(self, event, move_interval=7):
        if self.ids.add.state == 'down':  # adding
            if event.key in self.direction_to_int and (25 <= self.graph_location < self.cols-25):
                self.graph_location += self.direction_to_int[event.key]*move_interval
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
            if event.key in self.direction_to_int:
                self.index += self.direction_to_int[event.key]
                if self.ids.syllable_beginning.state == 'down':  # onsets
                    if self.index < 0:
                        self.index = len(self.syllable_onsets) - 1
                    if self.index >= len(self.syllable_onsets):
                        self.index = 0
                    self.update_mark(self.syllable_onsets[self.index])
                else:  # offsets
                    if self.index < 0:
                        self.index = len(self.syllable_offsets) - 1
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

    def add_mark(self, touchx, touchy):
        self.mark_boolean = True
        conversion = self.sonogram.shape[1]/self.ids.graph_binary.size[0]
        self.graph_location = math.floor((touchx-self.ids.graph_binary.pos[0])*conversion)

        ymax = 0.75 if self.ids.syllable_beginning.state == 'down' else 0.90

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
        conversion = self.sonogram.shape[1] / self.ids.graph_binary.size[0]
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
        if self.index is None:
            return
        else:
            onsets_list = list(self.syllable_onsets)
            onsets_list.remove(self.syllable_onsets[self.index])
            print('onset_list', onsets_list)
            self.syllable_onsets = np.array(onsets_list)
            self.mark.remove()
            self.image_syllable_marks()
            self.index = None

    def delete_offsets(self):
        if self.index is None:
            return
        else:
            offsets_list = list(self.syllable_offsets)
            offsets_list.remove(self.syllable_offsets[self.index])
            self.syllable_offsets = np.array(offsets_list)
            self.mark.remove()
            self.image_syllable_marks()
            self.index = None

    def setup(self):
        self.i = 0
        self.files = seg.initialize(self.parent.directory)
        self.file_names = [os.path.splitext(self.files[i])[0] for i in range(len(self.files))]
        self.save_parameters_all = {}
        self.save_syllables_all = {}
        self.save_tossed = {}
        self.save_conversions_all = {}
        self.next()
        #ToDo: add "_reChipper" to end of output_path if previous .gzips were used.
        self.output_path = self.parent.directory + "SegSyllsOutput_" + time.strftime("%Y%m%d_T%H%M%S")  # + "_reChipper"
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)

    def set_song_params(self, filter_boundary=None, bout_range=None, percent_keep=None, min_silence=None,
                        min_syllable=None):
        if filter_boundary is None:
            self.filter_boundary = []
        else:
            self.filter_boundary = filter_boundary
        if bout_range is None:
            self.bout_range = []
        else:
            self.bout_range = bout_range

        if percent_keep is None:
            self.percent_keep = float(self.user_signal_thresh)
            # self.percent_keep = self.ids.slider_threshold.value
        else:
            self.percent_keep = percent_keep

        if min_silence is None:
            self.min_silence = float(self.user_min_silence)/self.millisecondsPerPixel
            # self.min_silence = self.ids.slider_min_silence.value/self.millisecondsPerPixel
            if self.min_silence == 0:
                self.min_silence = self.ids.slider_min_silence.min
        else:
            self.min_silence = min_silence

        if min_syllable is None:
            self.min_syllable = float(self.user_min_syllable)/self.millisecondsPerPixel
            # self.min_syllable = self.ids.slider_min_syllable.value/self.millisecondsPerPixel
            if self.min_syllable == 0:
                self.min_syllable = self.ids.slider_min_syllable.min
        else:
            self.min_syllable = min_syllable

        self.ids.slider_threshold_label.text = str(self.percent_keep) + "%"
        # have to round these because of the conversion
        self.ids.slider_min_silence_label.text = str(round(self.min_silence*self.millisecondsPerPixel,
                                                           1)) + " ms"
        self.ids.slider_min_syllable_label.text = str(round(self.min_syllable*self.millisecondsPerPixel,
                                                            1)) + " ms"
        self.ids.slider_min_silence.max = 50/self.millisecondsPerPixel  # want max to be 50ms
        self.ids.slider_min_syllable.max = 350/self.millisecondsPerPixel  # want max to be 350ms

    def set_params_in_kv(self):
        # !!!SHOULDN'T NEED THE VALUES SET IN .KV NOW!!!
        # TODO: connect defaults to .kv (would like to do this the other way around) or remove values from .kv
        self.ids.slider_threshold.value = self.percent_keep
        self.ids.slider_min_silence.value = self.min_silence
        self.ids.slider_min_syllable.value = self.min_syllable
        self.ids.syllable_beginning.state = 'down'
        self.ids.syllable_ending.state = 'normal'
        self.ids.add.state = 'normal'
        self.ids.delete.state = 'normal'
        # self.ids.slider_threshold_label.text = str(round(self.percent_keep, 1)) + "%"
        # self.ids.slider_min_silence_label.text = str(round(self.min_silence*self.ms_per_pixel,
        #                                                    1)) + " ms"
        # self.ids.slider_min_syllable_label.text = str(round(self.min_syllable*self.ms_per_pixel,
        #                                                     1)) + " ms"
        # self.ids.slider_min_silence.max = 50/self.ms_per_pixel  # want max to be 50ms
        # self.ids.slider_min_syllable.max = 350/self.ms_per_pixel  # want max to be 350ms

    def connect_song_shape_to_kv(self):
        # connect size of sonogram to maximum of sliders for HPF and crop
        [self.rows, self.cols] = np.shape(self.sonogram)
        if not self.filter_boundary:
            self.filter_boundary = [0, self.rows]
        self.ids.slider_frequency_filter.value1 = self.filter_boundary[0]
        self.ids.slider_frequency_filter.value2 = self.filter_boundary[1]
        self.ids.slider_frequency_filter.min = 0
        self.ids.slider_frequency_filter.max = self.rows
        if not self.bout_range:
            self.bout_range = [0, self.cols]  # TODO: make self.cols instead so you don't create arrays in multiple places
        self.ids.range_slider_crop.value1 = self.bout_range[0]
        self.ids.range_slider_crop.value2 = self.bout_range[1]
        self.ids.range_slider_crop.min = 0
        self.ids.range_slider_crop.max = self.cols

    def reset_parameters(self):
        self.set_song_params()
        self.set_params_in_kv()
        self.connect_song_shape_to_kv()

        self.update(self.filter_boundary, self.bout_range, self.percent_keep, self.min_silence, self.min_syllable)

    def next(self):
        # get initial data
        self.sound, self.sonogram, self.millisecondsPerPixel, self.hertzPerPixel, params, prev_onsets, prev_offsets = \
            seg.initial_sonogram(self.i, self.files, self.parent.directory, find_gzips=self.find_gzips)

        if len(self.save_parameters_all) > 0:
            if self.files[self.i] in self.save_parameters_all:
                params = self.save_parameters_all[self.files[self.i]]
                prev_onsets = np.asarray(self.save_syllables_all[self.files[self.i]]['Onsets'])
                prev_offsets = np.asarray(self.save_syllables_all[self.files[self.i]]['Offsets'])

        # reset default parameters for new song (will be used by update to graph the first attempt)
        self.set_song_params()
        self.set_params_in_kv()
        self.connect_song_shape_to_kv()

        # set parameters if already run through chipper before (params from gzip)
        if params:
            if 'HighPassFilter' in params:
                # this is added because we used to only have a high pass filter (single slider versus range slider)
                self.filter_boundary = [self.rows - params['HighPassFilter'], self.rows]
            else:
                self.filter_boundary = params['FrequencyFilter']
            self.bout_range = params['BoutRange']
            self.percent_keep = params['PercentSignalKept']
            self.min_silence = params['MinSilenceDuration']
            self.min_syllable = params['MinSyllableDuration']

        self.set_params_in_kv()
        self.connect_song_shape_to_kv()

        # update the label stating the current file and the file number out of total number of files
        # use self.i since you have not yet incremented
        self.ids.current_file.text = self.file_names[self.i] + '\nFile ' + str(self.i+1) + ' out of ' + str(len(
            self.files))

        # initialize the matplotlib figures/axes (no data yet)
        self.top_image.image_sonogram_initial(self.rows, self.cols)  # TODO: decide if rows and cols should be self variables instead of passing into functions
        self.image_binary_initial()

        # run update to load images for the first time for this file
        if prev_onsets.size:
            self.update(self.filter_boundary, self.bout_range, self.percent_keep, self.min_silence,
                        self.min_syllable, prev_run_onsets=prev_onsets, prev_run_offsets=prev_offsets)
        else:
            self.update(self.filter_boundary, self.bout_range, self.percent_keep, self.min_silence, self.min_syllable)

        # increment i so next file will be opened on submit/toss
        self.i += 1

    def update(self, filter_boundary, bout_range, percent_keep, min_silence, min_syllable, prev_run_onsets=None,
               prev_run_offsets=None):
        if prev_run_onsets is None:
            prev_run_onsets = np.empty([0])
            prev_run_offsets = np.empty([0])

        # TODO: this is current fix for range slider, could fix in range_slider_from_google.py instead of here
        # have to check list from range sliders to make sure the first one is less than the second
        # if they are not in ascending order, must reverse the list
        if filter_boundary[1] < filter_boundary[0]:
            filter_boundary.reverse()
        if bout_range[1] < bout_range[0]:
            bout_range.reverse()

        # update variables based on input to function
        # frequency_filter throws index error if both slider values are equal (you are selecting no rows of the
        # sonogram), so make sure they are never equal
        if filter_boundary[0] == self.rows:
            filter_boundary[0] = self.rows-1
        elif filter_boundary[1] == 0:
            filter_boundary[1] = 1
        elif filter_boundary[0] == filter_boundary[1]:
            filter_boundary[1] = filter_boundary[0] + 1

        self.set_song_params(filter_boundary=filter_boundary, bout_range=bout_range, percent_keep=percent_keep,
                             min_silence=min_silence, min_syllable=min_syllable)
        sonogram = self.sonogram.copy()  # must do this for image to update for some reason

        # run HPF, scale based on average amplitude (increases low amplitude sections), and graph sonogram
        freqfiltered_sonogram = seg.frequency_filter(filter_boundary, sonogram)
        scaled_sonogram = seg.normalize_amplitude(freqfiltered_sonogram)
        self.top_image.image_sonogram(scaled_sonogram)

        # apply threshold to signal, calculate onsets and offsets, plot resultant binary sonogram
        self.thresh_sonogram = seg.threshold_image(percent_keep, scaled_sonogram)
        onsets, offsets, silence_durations, sum_sonogram_scaled = seg.initialize_onsets_offsets(self.thresh_sonogram)
        syllable_onsets, syllable_offsets = seg.set_min_silence(min_silence, onsets, offsets, silence_durations)
        syllable_onsets, syllable_offsets = seg.set_min_syllable(min_syllable, syllable_onsets, syllable_offsets)
        self.syllable_onsets, self.syllable_offsets = seg.crop(bout_range, syllable_onsets, syllable_offsets)

        if prev_run_onsets.size:
            self.syllable_onsets = prev_run_onsets
            self.syllable_offsets = prev_run_offsets

        self.image_binary()
        self.image_syllable_marks()
        # self.bottom_image.image_syllable_marks(self.syllable_onsets, self.syllable_offsets)

    def image_binary_initial(self):
        data = np.zeros((self.rows, self.cols))

        # make plot take up the entire space
        self.ax2.clear()
        self.ax2 = plt.Axes(self.fig2, [0., 0., 1., 1.])
        self.ax2.set_axis_off()
        self.fig2.add_axes(self.ax2)

        # plot data
        self.plot_binary = self.ax2.imshow(np.log(data+3), cmap='hot', extent=[0, self.cols, 0, self.rows],
                                           aspect='auto')

        self.trans = tx.blended_transform_factory(self.ax2.transData, self.ax2.transAxes)
        self.lines_on, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .75, np.nan], 1), linewidth=0.75, color='g', transform=self.trans)
        self.lines_off, = self.ax2.plot(np.repeat(0, 3), np.tile([0, .90, np.nan], 1), linewidth=0.75, color='g', transform=self.trans)

        hundredMillisecondsInPixels = 100/self.millisecondsPerPixel

        scalebar = AnchoredSizeBar(self.ax2.transData,
                                   hundredMillisecondsInPixels, '100 ms', 1,
                                   pad=0.1,
                                   color='white',
                                   frameon=False,
                                   size_vertical=2)
        self.ax2.add_artist(scalebar)

        self.ids.graph_binary.clear_widgets()
        self.ids.graph_binary.add_widget(self.plot_binary_canvas)

    def image_binary(self):
        self.plot_binary.set_data(np.log(self.thresh_sonogram+3))
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

    def back(self):
        if self.i != 1:
            self.i -= 2
            self.next()

    def save(self):
        if len(self.syllable_onsets) == 0 and len(self.syllable_offsets) == 0:
            check_sylls = CheckForSyllablesPopup()
            check_sylls.open()
        elif len(self.syllable_onsets) != len(self.syllable_offsets):
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
                # save parameters to dictionary; note we use self.i-1 since i is incremented at the end of next()
                self.save_parameters_all[self.files[self.i-1]] = {'FrequencyFilter': self.filter_boundary,
                                                                  'BoutRange': self.bout_range,
                                                                  'PercentSignalKept': self.percent_keep,
                                                                  'MinSilenceDuration': self.min_silence,
                                                                  'MinSyllableDuration': self.min_syllable}
                self.save_syllables_all[self.files[self.i-1]] = {'Onsets': self.syllable_onsets.tolist(),
                                                                 'Offsets': self.syllable_offsets.tolist()}
                self.save_conversions_all[self.files[self.i-1]] = {'timeAxisConversion': self.millisecondsPerPixel,
                                                                   'freqAxisConversion': self.hertzPerPixel}

                filename_gzip = self.output_path + '/SegSyllsOutput_' + self.file_names[self.i - 1] + '.gzip'

                dictionaries = [
                    self.save_parameters_all[self.files[self.i - 1]],
                    self.save_syllables_all[self.files[self.i - 1]],
                    {'Sonogram': self.thresh_sonogram.tolist()},
                    self.save_conversions_all[self.files[self.i - 1]]
                ]
                save_gzip_pickle(filename_gzip, dictionaries)

                # remove from tossed list if file ends up being submitted
                if self.i - 1 in self.save_tossed:
                    del self.save_tossed[self.i - 1]

                # write if last file otherwise go to next file
                if self.i == len(self.files):
                    self.write()
                else:
                    self.next()

    def toss(self):
        # save file name to dictionary
        self.save_tossed[self.i-1] = {'FileName': self.files[self.i-1]}

        # remove from saved parameters and associated gzip if file ends up being tossed
        if self.files[self.i - 1] in self.save_parameters_all:
            del self.save_parameters_all[self.files[self.i - 1]]
            del self.save_syllables_all[self.files[self.i - 1]]
            del self.save_conversions_all[self.files[self.i - 1]]
            os.remove(self.output_path + '/SegSyllsOutput_' + self.file_names[self.i - 1] + '.gzip')

        # write if last file otherwise go to next file
        if self.i == len(self.files):
            self.write()
        else:
            self.next()

    def write(self):

        df_parameters = pd.DataFrame.from_dict(self.save_parameters_all, orient='index')
        df_parameters.index.name = 'FileName'
        df_parameters.to_csv((self.output_path + '/segmentedSyllables_parameters_all.txt'), sep="\t")

        df_syllables = pd.DataFrame.from_dict(self.save_syllables_all, orient='index')
        df_syllables.index.name = 'FileName'
        df_syllables.to_csv((self.output_path + '/segmentedSyllables_syllables_all.txt'), sep="\t")

        df_tossed = pd.DataFrame.from_dict(self.save_tossed, orient='index')
        df_tossed.to_csv((self.output_path + '/segmentedSyllables_tossed.txt'), sep="\t", index=False)

        self.done_window()

    def done_window(self):
        done_popup = DonePopup()
        done_popup.open()

    def play_song(self):
        self.sound.play()
