from kivy.logger import Logger

from chipper.analysis import Song

Logger.setLevel(2)


def test_song_class():
    one_song = r"C:\Users\james\PycharmProjects\chipper\build\PracticeBouts\SegSyllsOutput_20190104_T100951\SegSyllsOutput_b1s white crowned sparrow 16652.gzip"
    results = Song(one_song, 50, .40, testing=True).run_analysis()
    print(len(results))
    assert len(results) == 44


if __name__ == '__main__':
    test_song_class()
