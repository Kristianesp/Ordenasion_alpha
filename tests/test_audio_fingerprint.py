from pathlib import Path
import json

from src.core.audio_fingerprint import AudioFingerprintService


def test_fingerprint_file_returns_hash(tmp_path):
    file_path = tmp_path / "song.mp3"
    file_path.write_bytes(b"abc123")

    service = AudioFingerprintService()
    result = service.fingerprint_file(file_path)

    assert result["available"] is True
    assert result["fingerprint"] is not None
    assert result["strategy"] == "sha1-file"


def test_lookup_online_metadata_falls_back_without_dependencies(tmp_path):
    file_path = tmp_path / "track.mp3"
    file_path.write_bytes(b"abc123")

    service = AudioFingerprintService()
    result = service.lookup_online_metadata(file_path, {"title": ""})

    assert result["source"]
    assert "suggested_updates" in result


def test_should_auto_apply_candidate_requires_strong_match():
    service = AudioFingerprintService()
    local = {
        "file_path": "Artist - Song.mp3",
        "title": "Song",
        "artist": "Artist",
    }
    strong_candidate = {
        "title": "Song",
        "artist": "Artist",
        "confidence": 215,
        "suggested_updates": {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
        },
    }
    weak_candidate = {
        "title": "Some Other Song",
        "artist": "Another Artist",
        "confidence": 150,
        "suggested_updates": {
            "title": "Some Other Song",
            "artist": "Another Artist",
            "album": "Album",
        },
    }

    assert service.should_auto_apply_candidate(local, strong_candidate) is True
    assert service.should_auto_apply_candidate(local, weak_candidate) is False


def test_should_auto_apply_candidate_respects_210_threshold():
    service = AudioFingerprintService()
    local = {
        "file_path": "Artist - Song.mp3",
        "title": "Song",
        "artist": "Artist",
    }
    below_threshold_candidate = {
        "title": "Song",
        "artist": "Artist",
        "confidence": 209,
        "suggested_updates": {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
        },
    }
    above_threshold_candidate = {
        "title": "Song",
        "artist": "Artist",
        "confidence": 210,
        "suggested_updates": {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
        },
    }

    assert (
        service.should_auto_apply_candidate(local, below_threshold_candidate) is False
    )
    assert service.should_auto_apply_candidate(local, above_threshold_candidate) is True


def test_should_auto_apply_result_requires_single_candidate():
    service = AudioFingerprintService()
    result = {
        "file_path": "Artist - Song.mp3",
        "local_metadata": {"title": "Song", "artist": "Artist"},
        "candidates": [
            {
                "title": "Song",
                "artist": "Artist",
                "confidence": 200,
                "suggested_updates": {"title": "Song", "artist": "Artist"},
            },
            {
                "title": "Song (Live)",
                "artist": "Artist",
                "confidence": 198,
                "suggested_updates": {
                    "title": "Song (Live)",
                    "artist": "Artist",
                },
            },
        ],
    }

    assert service.should_auto_apply_result(result) is False


def test_build_batch_suggestions_uses_cached_lookup(monkeypatch, tmp_path):
    file_path = tmp_path / "song.mp3"
    file_path.write_bytes(b"abc123")

    service = AudioFingerprintService()
    expected = {
        "file_path": str(file_path),
        "cache_key": "abc",
        "suggested_updates": {"title": "Song"},
        "candidates": [{"suggested_updates": {"title": "Song"}}],
        "candidate_count": 1,
    }

    calls = []

    def fake_get_or_lookup(path, metadata=None, force_refresh=False):
        calls.append((Path(path), dict(metadata or {}), force_refresh))
        return dict(expected)

    monkeypatch.setattr(service, "get_or_lookup_online_metadata", fake_get_or_lookup)

    results = service.build_batch_suggestions(
        [{"file_path": str(file_path), "title": "Song"}]
    )

    assert len(results) == 1
    assert results[0]["file_path"] == str(file_path)
    assert calls == [(file_path, {"file_path": str(file_path), "title": "Song"}, False)]


def test_get_or_lookup_online_metadata_marks_cached_results(monkeypatch, tmp_path):
    file_path = tmp_path / "song.mp3"
    file_path.write_bytes(b"abc123")
    service = AudioFingerprintService()

    cached_payload = {
        "file_path": str(file_path),
        "cache_key": "cached-key",
        "suggested_updates": {"title": "Song"},
        "candidates": [{"suggested_updates": {"title": "Song"}}],
        "cache_updated_at": "2026-04-13T12:00:00",
    }

    from src.core.audio_index import audio_metadata_service

    monkeypatch.setattr(
        audio_metadata_service,
        "get_lookup_cache",
        lambda path, key=None: dict(cached_payload),
    )

    result = service.get_or_lookup_online_metadata(file_path, {"title": "Song"})

    assert result["cache_status"] == "cached"
    assert result["cache_updated_at"] == "2026-04-13T12:00:00"


def test_lookup_discogs_normalizes_release_album(monkeypatch, tmp_path):
    file_path = tmp_path / "Artist - Track.mp3"
    file_path.write_bytes(b"abc123")
    service = AudioFingerprintService()

    monkeypatch.setattr(service, "_get_discogs_token", lambda: "token")
    monkeypatch.setattr(service, "_get_discogs_enabled", lambda: True)

    payload = {
        "results": [
            {
                "id": 123,
                "title": "Artist - Greatest Hits",
                "year": "2004",
                "thumb": "https://img/thumb.jpg",
                "cover_image": "https://img/cover.jpg",
                "genre": ["Rock"],
                "style": ["Alternative Rock"],
            }
        ]
    }

    class _FakeResponse:
        status = 200

        def read(self):
            return json.dumps(payload).encode("utf-8")

        def getcode(self):
            return 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=20: _FakeResponse(),
    )

    result = service.lookup_discogs(
        file_path,
        {"title": "Track", "artist": "Artist", "file_path": str(file_path)},
    )

    assert result["reason"] == "ok"
    assert result["suggested_updates"]["title"] == "Track"
    assert result["suggested_updates"]["album"] == "Greatest Hits"
    assert result["suggested_updates"]["genre"] == "Alternative Rock"


def test_lookup_discogs_penalizes_generic_compilations(monkeypatch, tmp_path):
    file_path = tmp_path / "Artist - Track.mp3"
    file_path.write_bytes(b"abc123")
    service = AudioFingerprintService()

    monkeypatch.setattr(service, "_get_discogs_token", lambda: "token")
    monkeypatch.setattr(service, "_get_discogs_enabled", lambda: True)

    payload = {
        "results": [
            {
                "id": 111,
                "title": "Artist - Greatest Hits",
                "year": "2004",
                "genre": ["Rock"],
                "style": ["Alternative Rock"],
                "format": ["Compilation"],
            },
            {
                "id": 222,
                "title": "Artist - Shadow Zone",
                "year": "2003",
                "genre": ["Rock"],
                "style": ["Alternative Rock"],
                "format": ["Album"],
            },
        ]
    }

    class _FakeResponse:
        status = 200

        def read(self):
            return json.dumps(payload).encode("utf-8")

        def getcode(self):
            return 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=20: _FakeResponse(),
    )

    result = service.lookup_discogs(
        file_path,
        {"title": "Track", "artist": "Artist", "file_path": str(file_path)},
    )

    assert result["reason"] == "ok"
    assert result["suggested_updates"]["album"] == "Shadow Zone"


def test_prepare_lookup_result_builds_deduped_cover_choices(tmp_path):
    file_path = tmp_path / "song.mp3"
    file_path.write_bytes(b"demo")
    service = AudioFingerprintService()

    prepared = service._prepare_lookup_result(
        file_path,
        {"title": "Song", "artist": "Artist", "file_path": str(file_path)},
        {
            "source": "musicbrainz",
            "cover_url": "https://img/cover-a.jpg",
            "candidates": [
                {
                    "source": "musicbrainz",
                    "cover_url": "https://img/cover-a.jpg",
                    "thumb_url": "https://img/thumb-a.jpg",
                    "suggested_updates": {"album": "Album A"},
                },
                {
                    "source": "discogs",
                    "cover_url": "https://img/cover-b.jpg",
                    "thumb_url": "https://img/thumb-b.jpg",
                    "suggested_updates": {"album": "Album B"},
                },
            ],
        },
        "cache-key",
    )

    assert [choice["url"] for choice in prepared["cover_choices"]] == [
        "https://img/cover-a.jpg",
        "https://img/thumb-a.jpg",
        "https://img/cover-b.jpg",
        "https://img/thumb-b.jpg",
    ]
