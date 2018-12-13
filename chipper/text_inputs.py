from kivy.uix.textinput import TextInput


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class PercentInput(TextInput):
    min_value = 0
    max_value = 100

    def __init__(self, *args, **kwargs):
        TextInput.__init__(self, *args, **kwargs)
        self.input_filter = 'float'

    def insert_text(self, string, from_undo=False):
        new_text = self.text + string
        if new_text != "":
            if isfloat(new_text):
                if self.min_value <= float(new_text) <= self.max_value:
                    TextInput.insert_text(self, string, from_undo=from_undo)