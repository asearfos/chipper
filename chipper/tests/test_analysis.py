import os

from kivy.logger import Logger

from chipper.analysis import Song

Logger.setLevel(2)


def test_song_class():
    f_path = os.path.join(os.path.dirname(__file__), 'test_data', 'test.gzip')
    results = Song(f_path, 50, 40, testing=True).run_analysis()
    assert len(results) == 44


if __name__ == '__main__':
    test_song_class()
