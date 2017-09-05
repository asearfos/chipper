import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

import matplotlib
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt

import matplotlib.image as mpimg

import numpy as np
import segmentSylls_functionsForGUI as seg


class ControlPanel(BoxLayout):

    def update(self, sonogram, filter_boundary, percent_keep, min_silence, min_syllable):
        hpf_sonogram = seg.high_pass_filter(filter_boundary, sonogram)
        scaled_sonogram = seg.normalize_amplitude(hpf_sonogram)
        ControlPanel.image_sonogram(self, scaled_sonogram)
        #thresh_sonogram = seg.threshold(percent_keep, scaled_sonogram)

    def image_sonogram(self, data):
        self.ids.graph_sonogram.clear_widgets()

        [rows, cols] = np.shape(data)
        plot_sonogram = plt.imshow(np.log(data + 3), cmap='jet', extent=[0, cols, 0, rows], aspect='auto')

        self.fig = plt.gcf()
        self.ids.graph_sonogram.add_widget(FigureCanvasKivyAgg(self.fig))
        return plot_sonogram

    def image2(self):
        self.ids.graph_binary.clear_widgets()
        img = mpimg.imread('C:/Users/abiga/PycharmProjects/SongAnalysisGUI/stinkbug.png')
        imgplot = plt.imshow(img)
        self.fig = plt.gcf()
        self.ids.graph_binary.add_widget(FigureCanvasKivyAgg(self.fig))
        return imgplot

    i = 0
    directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"

    [files, F] = seg.initialize(directory)
    sonogram = seg.initial_sonogram(i, files, directory)
    #image_sonogram(sonogram) # only works if moved below def's but then it says it doesn't have enough arguments


class SegmentSyllablesGUIApp(App):

    # def on_start(self):
    #     i = 0
    #     directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/chipping sparrow new recording/fromEBird/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung/eBird_MLCatNum_ChippingSparrows_asOf07142017_fromMatthewYoung_bouts/"
    #
    #     [files, F] = seg.initialize(directory)
    #     sonogram = seg.initial_sonogram(i, files, directory)
    #     self.image_sonogram(sonogram)

    def build(self):
        return ControlPanel()

if __name__ == "__main__":
    SegmentSyllablesGUIApp().run()
