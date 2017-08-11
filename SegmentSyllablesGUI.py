#import kivy
#kivy.require()

from kivy.app import App

from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


class ControlPanel(BoxLayout):
    pass


class SegmentSyllablesGUIApp(App):
    def build(self):
        # grid1 = GridLayout(rows=2, cols=1)
        # submit = Button(text='SUBMIT')
        # toss = Button(text='TOSS')

        # grid1.add_widget(submit)
        # grid1.add_widget(toss)
        return ControlPanel()


if __name__ == "__main__":
    SegmentSyllablesGUIApp().run()
