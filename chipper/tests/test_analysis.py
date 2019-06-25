import os

from kivy.logger import Logger

from chipper.analysis import Song
from chipper.command_line import run_analysis
Logger.setLevel(2)


def test_song_class():
    f_path = os.path.join(os.path.dirname(__file__), 'test_data', 'test.gzip')
    results = Song(f_path, 50, 40).run_analysis()
    assert len(results) == 44


def test_command_line():
    f_path = os.path.join(os.path.dirname(__file__), 'test_data')
    run_analysis(f_path, 50, 40, 'output_test')

if __name__ == '__main__':
    test_command_line()
