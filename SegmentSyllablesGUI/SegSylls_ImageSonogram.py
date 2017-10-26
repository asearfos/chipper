import numpy as np
import matplotlib
from kivy.uix.gridlayout import GridLayout
matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
plt.style.use('dark_background')


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
        self.plot_sonogram = self.ax1.imshow(np.log(data + 3), cmap='hot', extent=[0, cols, 0, rows],
                                             aspect='auto')

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

