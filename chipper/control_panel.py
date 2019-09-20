import matplotlib
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
# from SegSylls_ImageSonogram import ImageSonogram
from kivy.uix.screenmanager import Screen

import chipper.functions as seg
import chipper.popups as popups
from chipper.sonogram import Sonogram

matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import matplotlib.transforms as tx
import matplotlib.figure
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

plt.style.use('dark_background')

from bisect import bisect_left, bisect_right, insort
import numpy as np
import pandas as pd
import os
import math
import time
from chipper.utils import save_gzip_pickle
from kivy.logger import Logger

Logger.disabled = False


class ControlPanel(Screen):
    # these connect the landing page user input to the control panel
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

        self.fig2 = matplotlib.figure.Figure()
        # self.fig2, self.ax2 = plt.subplots()
        self.plot_binary_canvas = FigureCanvasKivyAgg(self.fig2)
        self.fig2.canvas.mpl_connect('key_press_event', self.move_mark)

        # self.ax2 = self.fig2.add_subplot(111)
        self.ax2 = self.fig2.add_axes([0., 0., 1., 1.])
        # self.ax2 = plt.Axes(self.fig2, [0., 0., 1., 1.])
        self.ax2.set_axis_off()
        # self.fig2.add_axes(self.ax2)
        # all songs and files
        self.file_names = None
        self.files = None
        self.output_path = None

        # attributes for song that is being worked on
        self.i = None
        self.song = None
        self.current_file = None
        self.syllable_onsets = None
        self.syllable_offsets = None

        # place holders for plots
        self.plot_binary = None
        self.trans = None
        self.lines_on = None
        self.lines_off = None
        # for plotting
        self.index = None
        self.mark = None
        self.graph_location = None
        super(ControlPanel, self).__init__(**kwargs)

    def on_check_boolean(self):
        if self.click >= 2:
            marks_popup = popups.FinishMarksPopup(self)
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
            if event.key in self.direction_to_int and \
                    (25 <= self.graph_location < self.song.cols - 25):
                self.graph_location += self.direction_to_int[
                                           event.key] * move_interval
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
        # deleting
        elif self.ids.delete.state == 'down':
            if event.key in self.direction_to_int:
                self.index += self.direction_to_int[event.key]
                # onsets
                if self.ids.syllable_beginning.state == 'down':
                    if self.index < 0:
                        self.index = len(self.syllable_onsets) - 1
                    if self.index >= len(self.syllable_onsets):
                        self.index = 0
                    self.update_mark(self.syllable_onsets[self.index])
                # offsets
                else:
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
        conversion = self.song.sonogram.shape[1] / self.ids.graph_binary.size[
            0]
        self.graph_location = math.floor((touchx - self.ids.graph_binary.pos[
            0]) * conversion)

        ymax = 0.75 if self.ids.syllable_beginning.state == 'down' else 0.90

        # graph as another color/group of lines
        self.mark = self.ax2.axvline(self.graph_location, ymax=ymax,
                                     color='m', linewidth=0.75)
        self.plot_binary_canvas.draw()

    def add_onsets(self):
        # https://stackoverflow.com/questions/29408661/add-elements-into-a
        # -sorted-array-in-ascending-order
        if self.graph_location is None:
            return
        else:
            self.syllable_onsets = np.insert(
                self.syllable_onsets,
                np.searchsorted(self.syllable_onsets, self.graph_location),
                self.graph_location
            )
            self.mark.remove()
            self.image_syllable_marks()
            self.graph_location = None

    def add_offsets(self):
        if self.graph_location is None:
            return
        else:
            self.syllable_offsets = np.insert(
                self.syllable_offsets,
                np.searchsorted(self.syllable_offsets, self.graph_location),
                self.graph_location
            )
            self.mark.remove()
            self.image_syllable_marks()
            self.graph_location = None

    def delete_mark(self, touchx, touchy):
        self.mark_boolean = True
        conversion = self.song.sonogram.shape[1] / \
                     self.ids.graph_binary.size[0]

        self.graph_location = math.floor(
            (touchx - self.ids.graph_binary.pos[0]) * conversion
        )

        if self.ids.syllable_beginning.state == 'down':
            ymax = 0.75
            # find nearest onset
            self.index = self.take_closest(self.syllable_onsets,
                                           self.graph_location)
            location = self.syllable_onsets[self.index]
        else:
            ymax = 0.90
            # find nearest offset
            self.index = self.take_closest(self.syllable_offsets,
                                           self.graph_location)
            location = self.syllable_offsets[self.index]

        self.mark = self.ax2.axvline(location, ymax=ymax, color='m',
                                     linewidth=0.75)
        self.plot_binary_canvas.draw()

    def delete_onsets(self):
        if self.index is None:
            return
        else:
            onsets_list = list(self.syllable_onsets)
            onsets_list.remove(self.syllable_onsets[self.index])
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

    # called in kv just before entering control panel screen (on_pre_enter)
    def setup(self):
        Logger.info("Setting up")
        # storage for parameters
        self.save_parameters_all = {}
        self.save_syllables_all = {}
        self.save_tossed = {}
        self.save_conversions_all = {}

        self.i = 0
        self.files = self.parent.files
        self.file_names = self.parent.file_names
        # these are the dictionaries that are added to with each song

        self.output_path = os.path.join(
            self.parent.directory,
            "SegSyllsOutput_{}".format(time.strftime("%Y%m%d_T%H%M%S"))
        )

        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)
        self.next()

    def update_panel_text(self):
        # this updates the text or slider limits on the control panel screen
        self.ids.slider_threshold_label.text = '{}%'.format(
            self.song.percent_keep)
        # have to round these because of the conversion
        self.ids.slider_min_silence_label.text = "{} ms".format(
            round(self.song.min_silence * self.song.ms_pix, 1)
        )
        self.ids.slider_min_syllable_label.text = '{} ms'.format(
            round(self.song.min_syllable * self.song.ms_pix, 1)
        )
        # want max to be 50ms
        self.ids.slider_min_silence.max = 50 / self.song.ms_pix
        # want max to be 350ms
        self.ids.slider_min_syllable.max = 350 / self.song.ms_pix
        self.ids.normalize_amp.state = self.song.normalized
        self.ids.slider_threshold.value = self.song.percent_keep
        self.ids.slider_min_silence.value = self.song.min_silence
        self.ids.slider_min_syllable.value = self.song.min_syllable
        self.ids.syllable_beginning.state = 'down'
        self.ids.syllable_ending.state = 'normal'
        self.ids.add.state = 'normal'
        self.ids.delete.state = 'normal'

        self.ids.slider_frequency_filter.value1 = self.song.filter_boundary[0]
        self.ids.slider_frequency_filter.value2 = self.song.filter_boundary[1]
        self.ids.slider_frequency_filter.min = 0
        self.ids.slider_frequency_filter.max = self.song.rows
        self.ids.range_slider_crop.value1 = self.song.bout_range[0]
        self.ids.range_slider_crop.value2 = self.song.bout_range[1]
        self.ids.range_slider_crop.min = 0
        self.ids.range_slider_crop.max = self.song.cols

    def reset_parameters(self):
        self.song.reset_params(
            user_signal_thresh=self.user_signal_thresh,
            user_min_silence=self.user_min_silence,
            user_min_syllable=self.user_min_syllable,
            id_min_sil=self.ids.slider_min_silence.min,
            id_min_syl=self.ids.slider_min_syllable.min
        )
        self.ids.normalize_amp.state = self.song.normalized
        self.update_panel_text()
        self._update()

    def next(self):

        self.current_file = self.files[self.i]
        # increment i so next file will be opened on submit/toss
        self.i += 1
        # get initial data
        Logger.info("Loading file {}".format(self.current_file))
        f_path = os.path.join(self.parent.directory, self.current_file)
        f_size = os.path.getsize(f_path)
        # 1 000 000 bytes is 1 megabyte
        max_file_size = 3000000
        if f_size > max_file_size:
            Logger.info("Large song")
            popups.LargeFilePopup(self, self.current_file, str(round(f_size/1000000, 1))).open()
        else:
            self.process()

    def toss(self):
        Logger.info("Tossing {}".format(self.current_file))
        # save file name to dictionary
        self.save_tossed[self.i - 1] = {'FileName': self.current_file}

        # remove from saved parameters and associated gzip if
        # file ends up being tossed
        if self.current_file in self.save_parameters_all:
            del self.save_parameters_all[self.current_file]
            del self.save_syllables_all[self.current_file]
            del self.save_conversions_all[self.current_file]
            os.remove(self.output_path + '/SegSyllsOutput_' +
                      self.file_names[self.i - 1] + '.gzip')

        # write if last file otherwise go to next file
        if self.i == len(self.files):
            self.save_all_parameters()
        else:
            self.next()

    def process(self):
        self.song = Sonogram(wavfile=self.current_file,
                             directory=self.parent.directory,
                             find_gzips=self.find_gzips)
        self.ids.freq_axis_middle.text = str(round(
            self.song.rows * self.song.hertzPerPixel / 2 / 1000)) + " kHz"
        # reset default parameters for new song
        # (will be used by update to graph the first attempt)
        Logger.info("Setting default params")
        self.song.set_song_params(
            user_signal_thresh=self.user_signal_thresh,
            user_min_silence=self.user_min_silence,
            user_min_syllable=self.user_min_syllable,
            id_min_sil=self.ids.slider_min_silence.min,
            id_min_syl=self.ids.slider_min_syllable.min
        )
        prev_onsets = self.song.prev_onsets
        prev_offsets = self.song.prev_offsets
        #  if the user goes back to previous song and then goes forward again,
        #  it will pull what they had already submitted (so the user does not
        #  lose progress)
        if len(self.save_parameters_all) > 0:
            if self.current_file in self.save_parameters_all:
                params = self.save_parameters_all[self.current_file]
                prev_onsets = np.asarray(
                    self.save_syllables_all[self.current_file]['Onsets'])
                prev_offsets = np.asarray(
                    self.save_syllables_all[self.current_file]['Offsets'])
                Logger.info("Updating params based on previous run")
                self.song.update_by_params(params)
        Logger.info("Updating panel text")

        if self.song.params:
            self.song.update_by_params(self.song.params)

        self.update_panel_text()

        # update the label stating the current file and the file number out
        # of total number of files
        # use self.i since you have not yet incremented
        self.ids.current_file.text = "{}\nFile {} out of {}".format(
            self.file_names[self.i - 1], self.i, len(self.files)
        )

        # initialize the matplotlib figures/axes (no data yet)

        # ImageSonogram is its own class and top_image is an instance of it
        # (defined in kv) - had trouble doing this for the bottom image
        Logger.info("Creating initial sonogram")
        self.top_image.image_sonogram_initial(self.song.rows, self.song.cols)
        Logger.info("Creating initial binary")
        self.image_binary_initial()

        Logger.info("Updating")
        # run update to load images for the first time for this file
        self._update(prev_run_onsets=prev_onsets,
                     prev_run_offsets=prev_offsets)
        Logger.info("Done with automation portion")

    def update(self, filter_boundary, bout_range, percent_keep,
               min_silence, min_syllable, normalized):

        self.song.set_song_params(
            filter_boundary=filter_boundary,
            bout_range=bout_range,
            percent_keep=percent_keep,
            min_silence=min_silence,
            min_syllable=min_syllable,
            normalized=normalized,
            user_signal_thresh=self.user_signal_thresh,
            user_min_silence=self.user_min_silence,
            user_min_syllable=self.user_min_syllable,
            id_min_sil=self.ids.slider_min_silence.min,
            id_min_syl=self.ids.slider_min_syllable.min
        )
        self.update_panel_text()
        self._update()

    def _update(self, prev_run_onsets=None, prev_run_offsets=None):
        # must do this for image to update for some reason
        sonogram = self.song.sonogram.copy()

        # run HPF, scale based on average amplitude
        # (increases low amplitude sections), and graph sonogram
        freqfiltered_sonogram = seg.frequency_filter(self.song.filter_boundary,
                                                     sonogram)
        # switch next two lines if you don't want amplitude scaled
        if self.ids.normalize_amp.state == 'down':
            scaled_sonogram = seg.normalize_amplitude(freqfiltered_sonogram)
        else:
            scaled_sonogram = freqfiltered_sonogram

        # plot resultant sonogram in the top graph in control panel
        self.top_image.image_sonogram(scaled_sonogram)

        # apply threshold to signal
        self.thresh_sonogram = seg.threshold_image(self.song.percent_keep,
                                                   scaled_sonogram)
        # calculate onsets and offsets using binary (thresholded) image
        onsets, offsets, silence_durations, sum_sonogram_scaled = \
            seg.initialize_onsets_offsets(self.thresh_sonogram)
        # update the automatic onsets and offsets based on the slider values
        # for min silence and min syllable durations
        syllable_onsets, syllable_offsets = seg.set_min_silence(
            self.song.min_silence, onsets, offsets, silence_durations
        )
        syllable_onsets, syllable_offsets = seg.set_min_syllable(
            self.song.min_syllable, syllable_onsets, syllable_offsets
        )
        # lastly, remove onsets and offsets that are outside of the crop
        # values (on the time axis)
        self.syllable_onsets, self.syllable_offsets = \
            seg.crop(self.song.bout_range, syllable_onsets, syllable_offsets)

        # check if the song has been run before (if gzip data was loaded)
        if prev_run_onsets is None:
            prev_run_onsets = np.empty([0])
            prev_run_offsets = np.empty([0])
        # change the onsets and offsets to those in gzip if gzip was loaded
        if prev_run_onsets.size:
            self.syllable_onsets = prev_run_onsets
            self.syllable_offsets = prev_run_offsets
        # plot resultant binary sonogram along with onset and offset lines
        self.image_binary()
        self.image_syllable_marks()
        # self.bottom_image.image_syllable_marks(self.syllable_onsets,
        # self.syllable_offsets)

    def image_binary_initial(self):

        # make plot take up the entire space
        self.ax2.clear()
        self.ax2.set_axis_off()

        data = np.zeros((self.song.rows, self.song.cols))
        # plot data
        self.plot_binary = self.ax2.imshow(
            np.log(data + 3),
            cmap='hot',
            extent=[0, self.song.cols, 0, self.song.rows],
            aspect='auto'
        )

        self.trans = tx.blended_transform_factory(self.ax2.transData,
                                                  self.ax2.transAxes)
        self.lines_on, = self.ax2.plot(
            np.repeat(0, 3),
            np.tile([0, .75, np.nan], 1),
            linewidth=0.75,
            color='#2BB34B',
            transform=self.trans
        )
        self.lines_off, = self.ax2.plot(
            np.repeat(0, 3),
            np.tile([0, .90, np.nan], 1),
            linewidth=0.75,
            color='#2BB34B',
            transform=self.trans
        )

        hundred_ms_in_pix = 100 / self.song.ms_pix

        scalebar = AnchoredSizeBar(self.ax2.transData,
                                   hundred_ms_in_pix, '100 ms', 1, pad=0.1,
                                   color='white', frameon=False,
                                   size_vertical=2)
        self.ax2.add_artist(scalebar)

        self.ids.graph_binary.clear_widgets()
        self.ids.graph_binary.add_widget(self.plot_binary_canvas)

    def image_binary(self):
        self.plot_binary.set_data(np.log(self.thresh_sonogram + 3))
        self.plot_binary.autoscale()

    def image_syllable_marks(self):
        self.lines_on.set_xdata(np.repeat(self.syllable_onsets, 3))
        self.lines_on.set_ydata(np.tile([0, .75, np.nan],
                                        len(self.syllable_onsets)))
        self.lines_off.set_xdata(np.repeat(self.syllable_offsets, 3))
        self.lines_off.set_ydata(np.tile([0, .90, np.nan],
                                         len(self.syllable_offsets)))
        self.plot_binary_canvas.draw()

    def back(self):
        if self.i != 1:
            self.i -= 2
            self.next()

    # called when the user hits submit
    # before saving it checks for errors with onsets and offsets
    def save(self):
        Logger.info("Adding {} to save dictionaries".format(self.current_file))
        # check if there are no syllable lines at all
        if len(self.syllable_onsets) == 0 and len(self.syllable_offsets) == 0:
            check_sylls = popups.CheckForSyllablesPopup()
            check_sylls.open()
        # if there are lines, check that there are equal number of ons and offs
        elif len(self.syllable_onsets) != len(self.syllable_offsets):
            check_length = popups.CheckLengthPopup()
            check_length.len_onsets = str(len(self.syllable_onsets))
            check_length.len_offsets = str(len(self.syllable_offsets))
            check_length.open()
        # check that you start with onset and end with offset
        elif self.syllable_onsets[0] > self.syllable_offsets[0] or \
                self.syllable_onsets[-1] > self.syllable_offsets[-1]:
            check_beginning_end = popups.CheckBeginningEndPopup()
            check_beginning_end.start_onset = not self.syllable_onsets[0] > \
                                                  self.syllable_offsets[0]
            check_beginning_end.end_offset = not self.syllable_onsets[-1] > \
                                                 self.syllable_offsets[-1]
            check_beginning_end.open()
        # check that onsets and offsets alternate
        else:
            combined_onsets_offsets = list(self.syllable_onsets)
            binary_list = [0] * len(self.syllable_onsets)
            for i in range(len(self.syllable_offsets)):
                insertion_pt = bisect_right(combined_onsets_offsets,
                                            self.syllable_offsets[i])
                binary_list.insert(insertion_pt, 1)
                insort(combined_onsets_offsets, self.syllable_offsets[i])
            if sum(binary_list[::2]) != 0 \
                    or sum(binary_list[1::2]) \
                    != len(binary_list) / 2:  # using python slices
                check_order = popups.CheckOrderPopup()
                check_order.order = binary_list
                check_order.open()
            # passed all checks, now info can be stored/written for the song
            else:
                Logger.info("Saving {}".format(self.current_file))
                self.save_parameters_all[
                    self.current_file] = self.song.save_dict()

                self.save_conversions_all[self.current_file] = {
                    'timeAxisConversion': self.song.ms_pix,
                    'freqAxisConversion': self.song.hertzPerPixel
                }

                self.save_syllables_all[self.current_file] = {
                    'Onsets': self.syllable_onsets.tolist(),
                    'Offsets': self.syllable_offsets.tolist()
                }

                filename_gzip = "{}/SegSyllsOutput_{}.gzip".format(
                    self.output_path, self.file_names[self.i - 1]
                )

                dictionaries = [
                    self.save_parameters_all[self.current_file],
                    self.save_syllables_all[self.current_file],
                    {'Sonogram': self.thresh_sonogram.tolist()},
                    self.save_conversions_all[self.current_file]
                ]
                save_gzip_pickle(filename_gzip, dictionaries)

                # remove from tossed list if file ends up being submitted
                if self.i - 1 in self.save_tossed:
                    del self.save_tossed[self.i - 1]

                # write if last file otherwise go to next file
                if self.i == len(self.files):
                    self.save_all_parameters()
                else:
                    self.next()

    def save_all_parameters(self):
        Logger.info("Saving parameters")

        if self.save_parameters_all:

            df_parameters = pd.DataFrame.from_dict(self.save_parameters_all,
                                                   orient='index')

            for r in df_parameters.BoutRange:
                # adjust bout ranges so that they do not include the padding of the
                # spectrogram (150 pixels each side), so user can convert
                # correctly using human-readable files
                r[:] = [x - 150 for x in r]
                if r[0] < 0:
                    r[0] = 0
                if r[-1] > (self.song.cols - 300):
                    r[-1] = (self.song.cols - 300)
            df_parameters.index.name = 'FileName'
            df_parameters.to_csv(
                os.path.join(self.output_path,
                             'segmentedSyllables_parameters_all.txt'),
                sep="\t"
            )

            df_syllables = pd.DataFrame.from_dict(self.save_syllables_all,
                                                  orient='index')
            # adjust onsets and offests so that they do not include the padding of
            # the spectrogram (150 pixels each side), so user can convert
            # correctly using human-readable files
            for on, off in zip(df_syllables.Onsets, df_syllables.Offsets):
                on[:] = [x-150 for x in on]
                off[:] = [y-150 for y in off]
            df_syllables.index.name = 'FileName'
            df_syllables.to_csv(os.path.join(self.output_path,
                                             'segmentedSyllables_syllables_all.txt'),
                                sep="\t")

            df_conversions = pd.DataFrame.from_dict(self.save_conversions_all,
                                                  orient='index')
            df_conversions.index.name = 'FileName'
            df_conversions.to_csv(os.path.join(self.output_path,
                                             'segmentedSyllables_conversions_all.txt'),
                                sep="\t")

            df_tossed = pd.DataFrame.from_dict(self.save_tossed, orient='index')

            df_tossed.to_csv(os.path.join(self.output_path,
                                          'segmentedSyllables_tossed.txt'),
                             sep="\t", index=False)
        else:
            df_tossed = pd.DataFrame.from_dict(self.save_tossed,
                                               orient='index')

            df_tossed.to_csv(os.path.join(self.output_path,
                                          'segmentedSyllables_tossed.txt'),
                             sep="\t", index=False)

        self.done_window()

    def play_song(self):
        self.song.sound.play()

    @staticmethod
    def done_window():
        popups.DonePopup().open()

    @staticmethod
    def take_closest(myList, myNumber):
        """
        Assumes myList is sorted. Returns index of closest value to myNumber.
        If two numbers are equally close, return the index of the smallest
        number. From: https://stackoverflow.com/questions/12141150/from-list-of
        -integers-get-number-closest-to-a-given-value
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
            return pos - 1
