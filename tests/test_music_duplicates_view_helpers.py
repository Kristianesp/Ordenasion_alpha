from src.gui.music_duplicates_view import MusicDuplicatesView


def _view() -> MusicDuplicatesView:
    return MusicDuplicatesView.__new__(MusicDuplicatesView)


def test_lookup_result_is_applied_only_when_selected_matches_applied():
    view = _view()

    assert (
        view._lookup_result_is_applied(
            {
                "selected_candidate_index": 1,
                "applied_candidate_index": 1,
                "suggested_updates": {"title": "Song"},
            }
        )
        is True
    )
    assert (
        view._lookup_result_is_applied(
            {
                "selected_candidate_index": 1,
                "applied_candidate_index": 0,
                "suggested_updates": {"title": "Song"},
            }
        )
        is False
    )


def test_track_state_label_prioritizes_applied_and_complete_states():
    view = _view()

    assert (
        view._track_state_label(
            {"review_status": "applied"},
            {
                "selected_candidate_index": 0,
                "applied_candidate_index": 0,
                "suggested_updates": {"title": "Song"},
            },
        )
        == "aplicada"
    )
    assert (
        view._track_state_label(
            {"review_status": "complete"},
            {
                "selected_candidate_index": 0,
                "applied_candidate_index": 0,
                "suggested_updates": {"title": "Song"},
            },
        )
        == "completa"
    )


def test_find_candidate_index_for_updates_matches_selected_payload():
    view = _view()
    result = {
        "candidates": [
            {
                "suggested_updates": {
                    "title": "Song A",
                    "artist": "Artist A",
                    "album": "Album A",
                }
            },
            {
                "suggested_updates": {
                    "title": "Song B",
                    "artist": "Artist B",
                    "album": "Album B",
                }
            },
        ]
    }

    index = view._find_candidate_index_for_updates(
        result,
        {"title": "Song B", "artist": "Artist B", "album": "Album B"},
    )

    assert index == 1


def test_selected_variant_matches_updates_uses_clean_title_logic():
    view = _view()
    result = {
        "selected_candidate_index": 0,
        "candidates": [
            {
                "suggested_updates": {
                    "title": "01 My Song.mp3",
                    "artist": "Artist",
                    "album": "Album",
                }
            }
        ],
    }

    assert (
        view._selected_variant_matches_updates(
            result,
            {"title": "My Song", "artist": "Artist", "album": "Album"},
        )
        is True
    )
    assert (
        view._selected_variant_matches_updates(
            result,
            {"title": "Other", "artist": "Artist", "album": "Album"},
        )
        is False
    )


def test_auto_selectable_candidate_index_uses_high_confidence_best_candidate():
    view = _view()
    view._lookup_results_by_path = {}
    result = {
        "file_path": "Artist - Song.mp3",
        "local_metadata": {
            "file_path": "Artist - Song.mp3",
            "title": "Song",
            "artist": "Artist",
        },
        "selected_candidate_index": 0,
        "candidates": [
            {
                "title": "Song",
                "artist": "Artist",
                "confidence": 240,
                "suggested_updates": {"title": "Song", "artist": "Artist"},
            },
            {
                "title": "Song (Live)",
                "artist": "Artist",
                "confidence": 180,
                "suggested_updates": {"title": "Song (Live)", "artist": "Artist"},
            },
        ],
    }

    assert view._auto_selectable_candidate_index("Artist - Song.mp3", result) == 0


def test_store_lookup_result_restores_selected_cover_choice_when_still_available(
    monkeypatch,
):
    view = _view()
    view._lookup_results_by_path = {
        "track.mp3": {
            "file_path": "track.mp3",
            "cache_status": "cached",
            "selected_cover_url": "https://img/two.jpg",
            "cover_url": "https://img/two.jpg",
            "thumb_url": "https://img/two.jpg",
            "cached_cover_art": b"cover-bytes",
            "cover_choices": [
                {"url": "https://img/one.jpg", "label": "One", "source": "mb"},
                {"url": "https://img/two.jpg", "label": "Two", "source": "dg"},
            ],
        }
    }

    persisted = []
    monkeypatch.setattr(
        "src.gui.music_duplicates_lookup_logic.audio_metadata_service.set_lookup_cache",
        lambda *args, **kwargs: persisted.append((args, kwargs)) or True,
    )

    stored = view._store_lookup_result(
        "track.mp3",
        {
            "file_path": "track.mp3",
            "cache_key": "cache-key",
            "cover_url": "https://img/one.jpg",
            "thumb_url": "https://img/one.jpg",
            "cover_choices": [
                {"url": "https://img/one.jpg", "label": "One", "source": "mb"},
                {"url": "https://img/two.jpg", "label": "Two", "source": "dg"},
            ],
            "candidates": [],
        },
        persist=True,
    )

    assert stored["selected_cover_url"] == "https://img/two.jpg"
    assert stored["cover_url"] == "https://img/two.jpg"
    assert stored["thumb_url"] == "https://img/two.jpg"
    assert stored["cached_cover_art"] == b"cover-bytes"
    assert persisted


def test_store_lookup_result_does_not_restore_missing_selected_cover_choice(
    monkeypatch,
):
    view = _view()
    view._lookup_results_by_path = {
        "track.mp3": {
            "file_path": "track.mp3",
            "cache_status": "cached",
            "selected_cover_url": "https://img/removed.jpg",
            "cover_url": "https://img/removed.jpg",
            "thumb_url": "https://img/removed.jpg",
        }
    }

    monkeypatch.setattr(
        "src.gui.music_duplicates_lookup_logic.audio_metadata_service.set_lookup_cache",
        lambda *args, **kwargs: True,
    )

    stored = view._store_lookup_result(
        "track.mp3",
        {
            "file_path": "track.mp3",
            "cache_key": "cache-key",
            "cover_url": "https://img/one.jpg",
            "thumb_url": "https://img/one.jpg",
            "cover_choices": [
                {"url": "https://img/one.jpg", "label": "One", "source": "mb"},
                {"url": "https://img/two.jpg", "label": "Two", "source": "dg"},
            ],
            "candidates": [],
        },
        persist=True,
    )

    assert stored.get("selected_cover_url") in (None, "")
    assert stored["cover_url"] == "https://img/one.jpg"
    assert stored["thumb_url"] == "https://img/one.jpg"
