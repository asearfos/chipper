from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class NumericInput(TextInput):
    min_value = NumericProperty()
    max_value = NumericProperty()

    def __init__(self, *args, **kwargs):
        TextInput.__init__(self, *args, **kwargs)
        self.input_filter = 'float'

    def insert_text(self, string, from_undo=False):
        new_text = self.text + string
        if new_text == '.':  # can start with a decimal
            TextInput.insert_text(self, string, from_undo=from_undo)
        elif new_text != "":
            if isfloat(new_text):
                if '.' not in new_text:  # if there not a decimal check if value is in range
                    if self.min_value <= float(new_text) <= self.max_value:
                        TextInput.insert_text(self, string, from_undo=from_undo)
                elif len(new_text.split('.')[1]) <= 1:  # check to make sure there is only one decimal place
                    if self.min_value <= float(new_text) <= self.max_value:
                        TextInput.insert_text(self, string, from_undo=from_undo)
                else:
                    pass
