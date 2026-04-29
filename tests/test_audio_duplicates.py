from pathlib import Path

from src.core.audio_duplicates import AudioDuplicateFinder


def test_audio_duplicate_finder_ignores_nonexistent_folder(tmp_path):
    finder = AudioDuplicateFinder()
    out = finder.scan_folder(str(tmp_path / "missing"))
    assert out == {}


def test_audio_quality_scoring_prefers_lossless(tmp_path):
    finder = AudioDuplicateFinder()
    lossless = tmp_path / "a.flac"
    lossy = tmp_path / "b.mp3"
    lossless.write_bytes(b"x" * 10)
    lossy.write_bytes(b"x" * 10)

    class Meta:
        def __init__(self, path, lossless_flag, bitrate):
            self.file_path = str(path)
            self.title = "Song"
            self.artist = "Artist"
            self.album = "Album"
            self.codec = path.suffix.lstrip(".")
            self.bitrate = bitrate
            self.sample_rate = 44100
            self.channels = 2
            self.bit_depth = None
            self.duration = 180.0
            self.lossless = lossless_flag
            self.file_size = 10
            self.error = ""
            self.track_number = "1"
            self.disc_number = "1"

    assert finder._quality_score(Meta(lossless, True, 0)) > finder._quality_score(
        Meta(lossy, False, 320000)
    )
