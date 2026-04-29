from pathlib import Path
import sys
import types

from src.core.audio_index import AudioMetadataService


def test_audio_index_fallback_without_mutagen(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "mutagen", None)

    audio_file = tmp_path / "track.mp3"
    audio_file.write_bytes(b"fake mp3 data")

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    metadata = service.extract_metadata(audio_file)

    assert metadata.file_path.endswith("track.mp3")
    assert metadata.error == "mutagen_no_disponible"
    assert metadata.extension == ".mp3"
    assert metadata.lossless is False


def test_audio_index_persists_basic_record(tmp_path):
    audio_file = tmp_path / "song.flac"
    audio_file.write_bytes(b"fake flac data")

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    metadata = service.extract_metadata(audio_file)

    assert service.upsert_metadata(metadata) is True
    stored = service.get_metadata(audio_file)

    assert stored is not None
    assert stored["file_path"].endswith("song.flac")
    assert stored["extension"] == ".flac"


def test_review_status_and_lookup_cache_roundtrip(tmp_path):
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"fake mp3 data")

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    metadata = service.extract_metadata(audio_file)
    assert service.upsert_metadata(metadata) is True

    assert service.set_track_review_status(audio_file, "no_match") is True
    stored = service.get_metadata(audio_file)
    assert stored is not None
    assert stored["review_status"] == "no_match"

    payload = {
        "file_path": str(audio_file),
        "suggested_updates": {"title": "Song"},
        "candidates": [{"suggested_updates": {"title": "Song"}}],
    }
    assert service.set_lookup_cache(audio_file, "cache-key", payload, cover_art=b"img")

    cached = service.get_lookup_cache(audio_file, "cache-key")
    assert cached is not None
    assert cached["cache_key"] == "cache-key"
    assert cached["suggested_updates"]["title"] == "Song"
    assert cached["cached_cover_art"] == b"img"


def test_find_missing_metadata_excludes_applied_tracks(tmp_path):
    audio_file = tmp_path / "pending.mp3"
    audio_file.write_bytes(b"fake mp3 data")

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    metadata = service.extract_metadata(audio_file)
    assert service.upsert_metadata(metadata) is True
    assert service.set_track_review_status(audio_file, "applied") is True

    missing = service.find_missing_metadata(limit=50)
    paths = {item["file_path"] for item in missing}
    assert str(audio_file) not in paths


class _FakeID3Tags(dict):
    def __init__(self):
        super().__init__()
        self.frames = []
        self.deleted = []

    def delall(self, name):
        self.deleted.append(name)
        self.frames = []

    def add(self, frame):
        self.frames.append(frame)

    def getall(self, name):
        return list(self.frames) if name == "APIC" else []


class _FakeMP3Audio:
    def __init__(self):
        self.tags = _FakeID3Tags()
        self.saved = False

    def save(self):
        self.saved = True


class _FakeFlacAudio:
    def __init__(self):
        self.tags = {}
        self.pictures = []
        self.cleared = False
        self.saved = False

    def clear_pictures(self):
        self.cleared = True
        self.pictures = []

    def add_picture(self, picture):
        self.pictures.append(picture)

    def save(self):
        self.saved = True


class _FakeMP4Audio(dict):
    def __init__(self):
        super().__init__()
        self.tags = self
        self.saved = False

    def save(self):
        self.saved = True


class _FakeOggAudio(dict):
    def __init__(self):
        super().__init__()
        self.tags = self
        self.saved = False

    def save(self):
        self.saved = True


class _FakePicture:
    def __init__(self, payload=None):
        self.data = b""
        self.type = 0
        self.mime = ""
        if payload and bytes(payload).startswith(b"picture:"):
            self.data = bytes(payload)[8:]

    def write(self):
        return b"picture:" + bytes(self.data)


class _FakeAPIC:
    def __init__(self, encoding, mime, type, desc, data):
        self.encoding = encoding
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data


class _FakeMP4Cover(bytes):
    FORMAT_JPEG = 1
    FORMAT_PNG = 2
    imageformat: int | None

    def __new__(cls, data, imageformat=None):
        value = bytes.__new__(cls, data)
        value.imageformat = imageformat
        return value


def _install_fake_mutagen(monkeypatch, mapping):
    mutagen_module = types.ModuleType("mutagen")
    setattr(mutagen_module, "File", lambda path, easy=False: mapping[str(path)])

    flac_module = types.ModuleType("mutagen.flac")
    setattr(flac_module, "Picture", _FakePicture)

    id3_module = types.ModuleType("mutagen.id3")
    setattr(id3_module, "APIC", _FakeAPIC)

    mp4_module = types.ModuleType("mutagen.mp4")
    setattr(mp4_module, "MP4Cover", _FakeMP4Cover)

    monkeypatch.setitem(sys.modules, "mutagen", mutagen_module)
    monkeypatch.setitem(sys.modules, "mutagen.flac", flac_module)
    monkeypatch.setitem(sys.modules, "mutagen.id3", id3_module)
    monkeypatch.setitem(sys.modules, "mutagen.mp4", mp4_module)


def test_write_cover_art_mp3_uses_apic(monkeypatch, tmp_path):
    file_path = tmp_path / "song.mp3"
    file_path.write_bytes(b"fake")
    audio = _FakeMP3Audio()
    _install_fake_mutagen(monkeypatch, {str(file_path): audio})

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    assert service._write_cover_art(file_path, b"\xff\xd8\xffcover") is True

    assert audio.tags.deleted == ["APIC"]
    assert len(audio.tags.frames) == 1
    assert audio.tags.frames[0].mime == "image/jpeg"
    assert audio.tags.frames[0].data == b"\xff\xd8\xffcover"
    assert audio.saved is True


def test_write_cover_art_flac_uses_picture_blocks(monkeypatch, tmp_path):
    file_path = tmp_path / "song.flac"
    file_path.write_bytes(b"fake")
    audio = _FakeFlacAudio()
    _install_fake_mutagen(monkeypatch, {str(file_path): audio})

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    assert service._write_cover_art(file_path, b"\x89PNG\r\n\x1a\ncover") is True

    assert audio.cleared is True
    assert len(audio.pictures) == 1
    assert audio.pictures[0].mime == "image/png"
    assert audio.pictures[0].data == b"\x89PNG\r\n\x1a\ncover"
    assert audio.saved is True


def test_write_cover_art_mp4_uses_covr(monkeypatch, tmp_path):
    file_path = tmp_path / "song.m4a"
    file_path.write_bytes(b"fake")
    audio = _FakeMP4Audio()
    _install_fake_mutagen(monkeypatch, {str(file_path): audio})

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    assert service._write_cover_art(file_path, b"\x89PNG\r\n\x1a\ncover") is True

    assert "covr" in audio
    assert len(audio["covr"]) == 1
    assert bytes(audio["covr"][0]) == b"\x89PNG\r\n\x1a\ncover"
    assert audio["covr"][0].imageformat == _FakeMP4Cover.FORMAT_PNG
    assert audio.saved is True


def test_write_cover_art_ogg_uses_metadata_block_picture(monkeypatch, tmp_path):
    file_path = tmp_path / "song.ogg"
    file_path.write_bytes(b"fake")
    audio = _FakeOggAudio()
    _install_fake_mutagen(monkeypatch, {str(file_path): audio})

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    assert service._write_cover_art(file_path, b"\xff\xd8\xffcover") is True

    assert "metadata_block_picture" in audio
    encoded = audio["metadata_block_picture"][0]
    assert isinstance(encoded, str)
    assert audio.saved is True


def test_rename_track_file_updates_lookup_cache_payload(tmp_path):
    file_path = tmp_path / "01_bad title.mp3"
    file_path.write_bytes(b"fake mp3 data")

    service = AudioMetadataService(str(tmp_path / "media_index.db"))
    metadata = service.extract_metadata(file_path)
    assert service.upsert_metadata(metadata) is True
    assert service.set_lookup_cache(
        file_path,
        "cache-key",
        {
            "file_path": str(file_path),
            "local_metadata": {"file_path": str(file_path), "title": "Bad"},
            "suggested_updates": {"title": "Bad"},
            "candidates": [],
        },
        cover_art=b"img",
    )

    assert service.rename_track_file(file_path, "bad title.mp3") is True

    renamed = tmp_path / "bad title.mp3"
    cached = service.get_lookup_cache(renamed, "cache-key")
    assert cached is not None
    assert cached["file_path"] == str(renamed)
    assert cached["local_metadata"]["file_path"] == str(renamed)


def test_clean_track_filename_strips_invalid_windows_chars(tmp_path):
    service = AudioMetadataService(str(tmp_path / "media_index.db"))

    assert service.clean_track_filename("01: demo/title*?") == "demo title"
