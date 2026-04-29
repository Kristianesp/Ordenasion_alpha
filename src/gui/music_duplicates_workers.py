#!/usr/bin/env python3
"""Workers asíncronos para la vista musical."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.audio_duplicates import audio_duplicate_finder
from src.core.audio_fingerprint import audio_fingerprint_service
from src.core.audio_index import audio_metadata_service


class AudioLookupWorker(QThread):
    progress = pyqtSignal(str, int, int)
    result_ready = pyqtSignal(dict)
    finished_ok = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, tracks: List[Dict[str, Any]], force_refresh: bool = False):
        super().__init__()
        self.tracks = list(tracks)
        self.force_refresh = bool(force_refresh)

    def run(self):
        try:
            total = len(self.tracks)
            for index, track in enumerate(self.tracks, start=1):
                file_path = Path(track.get("file_path", ""))
                self.progress.emit(
                    f"🌐 Buscando online [{index}/{total}]: {file_path.name}",
                    index,
                    total,
                )
                result = audio_fingerprint_service.get_or_lookup_online_metadata(
                    file_path,
                    track,
                    force_refresh=self.force_refresh,
                )
                result["file_path"] = str(file_path)
                self.result_ready.emit(result)
            self.finished_ok.emit()
        except Exception as exc:
            self.error_occurred.emit(str(exc))


class AudioLibraryWorker(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, folder: str, recursive: bool, include_duplicates: bool):
        super().__init__()
        self.folder = str(folder)
        self.recursive = bool(recursive)
        self.include_duplicates = bool(include_duplicates)

    def run(self):
        try:
            folder_path = Path(self.folder)
            self.progress.emit(f"🎵 Indexando biblioteca: {folder_path}")
            indexed = audio_metadata_service.index_folder(
                folder_path,
                recursive=self.recursive,
            )
            duplicates: Dict[str, List[Dict[str, Any]]] = {}
            if self.include_duplicates:
                self.progress.emit("🎵 Analizando duplicados musicales...")
                duplicates = audio_duplicate_finder.scan_folder(
                    str(folder_path),
                    recursive=self.recursive,
                )
            self.finished_ok.emit(
                {
                    "folder": str(folder_path),
                    "recursive": self.recursive,
                    "indexed": indexed,
                    "include_duplicates": self.include_duplicates,
                    "duplicates": duplicates,
                }
            )
        except Exception as exc:
            self.error_occurred.emit(str(exc))
