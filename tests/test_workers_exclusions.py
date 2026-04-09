from pathlib import Path

from src.core.workers import AnalysisWorker


def test_analysis_worker_skips_ignored_extension_and_small_files(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    keep = root / "keep.mp3"
    keep.write_bytes(b"x" * 1024 * 1024)
    ignored = root / "ignore.tmp"
    ignored.write_bytes(b"x" * 1024 * 1024)
    tiny = root / "tiny.mp3"
    tiny.write_bytes(b"x")

    worker = AnalysisWorker(
        str(root),
        {},
        {".mp3": "MUSICA"},
        ignored_extensions=[".tmp"],
        min_file_size_mb=1,
    )

    files = worker.analyze_loose_files()

    assert [item["file"].name for item in files] == ["keep.mp3"]


def test_analysis_worker_skips_ignored_paths(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    ignored_dir = root / "skipme"
    ignored_dir.mkdir()
    (ignored_dir / "track.mp3").write_bytes(b"x" * 1024)
    visible_dir = root / "keepme"
    visible_dir.mkdir()
    (visible_dir / "track.mp3").write_bytes(b"x" * 1024)

    worker = AnalysisWorker(
        str(root),
        {},
        {".mp3": "MUSICA"},
        ignored_paths=[str(ignored_dir)],
    )

    folders = worker.analyze_folders()

    assert len(folders) == 1
    assert folders[0]["folder"].name == "keepme"
