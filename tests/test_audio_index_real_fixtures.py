import shutil
from pathlib import Path

import pytest

from src.core.audio_index import AudioMetadataService


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "audio"


@pytest.mark.parametrize(
    ("fixture_name", "new_title"),
    [
        ("lame.mp3", "Fixture MP3"),
        ("silence.wav", "Fixture WAV"),
        ("8k-1ch-1s-silence.aif", "Fixture AIFF"),
        ("flac_application.flac", "Fixture FLAC"),
        ("has-tags.m4a", "Fixture M4A"),
        ("alac.m4a", "Fixture ALAC"),
        ("empty.ogg", "Fixture OGG"),
    ],
)
def test_real_audio_fixtures_accept_cover_art_by_format(
    tmp_path, fixture_name, new_title
):
    source = FIXTURE_ROOT / fixture_name
    assert source.exists(), f"Missing fixture: {source}"
    cover = (FIXTURE_ROOT / "image.jpg").read_bytes()

    target = tmp_path / fixture_name
    shutil.copy2(source, target)

    service = AudioMetadataService(str(tmp_path / "media_index.db"))

    assert service._write_cover_art(target, cover) is True
    assert service.get_cover_art_bytes(target) == cover

    if target.suffix.lower() not in {".aif", ".wav"}:
        assert (
            service.update_track_tags(target, {"title": new_title}, cover_art=cover)
            is True
        )
        metadata = service.extract_metadata(target)
        assert metadata.title == new_title
        assert service.get_cover_art_bytes(target) == cover
