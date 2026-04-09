from src.utils.app_config import AppConfig


def test_app_config_persists_path_memory_and_exclusions(tmp_path):
    config = AppConfig(str(tmp_path / "app_config.json"))

    assert config.set_ignored_extensions(["tmp", ".log", " .bak "])
    assert config.set_ignored_paths(["/tmp/cache", "/tmp/cache/sub", ""])
    assert config.set_protected_paths(["/home/user/Documents"])
    assert config.set_min_file_size_mb(25)
    assert config.add_favorite_path("/data/media")
    assert config.push_recent_path("/data/downloads")

    reloaded = AppConfig(str(tmp_path / "app_config.json"))
    assert reloaded.get_ignored_extensions() == [".bak", ".log", ".tmp"]
    assert reloaded.get_ignored_paths() == ["/tmp/cache", "/tmp/cache/sub"]
    assert reloaded.get_protected_paths() == ["/home/user/Documents"]
    assert reloaded.get_min_file_size_mb() == 25
    assert reloaded.get_favorite_paths() == ["/data/media"]
    assert reloaded.get_recent_paths()[0] == "/data/downloads"


def test_app_config_persists_duplicate_preferences(tmp_path):
    config = AppConfig(str(tmp_path / "app_config.json"))

    assert config.set_ignored_duplicate_hashes(["abc", "def", "abc"])
    assert config.set_preferred_original("hash1", "/tmp/fileA")
    assert config.set_preferred_original("hash2", "/tmp/fileB")
    assert config.remove_preferred_original("hash1")

    reloaded = AppConfig(str(tmp_path / "app_config.json"))
    assert reloaded.get_ignored_duplicate_hashes() == ["abc", "def"]
    assert reloaded.get_preferred_originals() == {"hash2": "/tmp/fileB"}
