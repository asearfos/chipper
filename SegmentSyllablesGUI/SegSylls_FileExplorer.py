from kivy.uix.screenmanager import Screen


class FileExplorer(Screen):
    def _fbrowser_canceled(self, instance):
        print('cancelled, Close SegmentSyllablesGUI.')
        quit()

    def _fbrowser_success(self, instance):
        [chosen_directory] = instance.selection
        # self.parent.directory = chosen_directory + '\\'
        self.parent.directory = "C:/Users/abiga/Box Sync/Abigail_Nicole/TestingGUI/PracticeBouts/"
