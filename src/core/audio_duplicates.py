#!/usr/bin/env python3
"""
Deteccion inicial de duplicados musicales.

Agrupa pistas por huellas locales y estima calidad tecnica para sugerir la
mejor copia sin hacer matching online ni fingerprint perceptual avanzado.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .audio_index import audio_metadata_service, AudioMetadata


@dataclass
class AudioDuplicateCandidate:
    file_path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    codec: str = "unknown"
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    duration: Optional[float] = None
    lossless: Optional[bool] = None
    file_size: int = 0
    identity_key: str = ""
    quality_score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AudioDuplicateFinder:
    """Agrupa audio por identidad tecnica y calcula calidad relativa."""

    def __init__(self):
        self.audio_service = audio_metadata_service

    def scan_folder(
        self, folder_path: str, recursive: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        root = Path(folder_path)
        if not root.exists():
            return {}

        groups: Dict[str, List[AudioDuplicateCandidate]] = {}
        for file_path in self._iter_audio_files(root, recursive=recursive):
            meta = self.audio_service.extract_metadata(file_path)
            if meta.error == "mutagen_no_disponible":
                continue

            identity_key = self._build_identity_key(meta)
            candidate = self._build_candidate(meta, identity_key)
            groups.setdefault(identity_key, []).append(candidate)

        duplicate_groups: Dict[str, List[Dict[str, Any]]] = {}
        for identity_key, candidates in groups.items():
            if len(candidates) < 2:
                continue
            ranked = sorted(
                candidates, key=lambda item: item.quality_score, reverse=True
            )
            duplicate_groups[identity_key] = [item.to_dict() for item in ranked]

        return duplicate_groups

    def _iter_audio_files(self, root: Path, recursive: bool):
        iterator = root.rglob("*") if recursive else root.iterdir()
        for file_path in iterator:
            if file_path.is_file() and self.audio_service.is_audio_file(file_path):
                yield file_path

    def _build_identity_key(self, meta: AudioMetadata) -> str:
        normalized = "|".join(
            [
                self._normalize_text(meta.artist),
                self._normalize_text(meta.album_artist),
                self._normalize_text(meta.album),
                self._normalize_text(meta.title),
                self._normalize_text(meta.track_number),
                self._normalize_text(meta.disc_number),
                str(round(meta.duration or 0.0, 1)),
            ]
        )
        if normalized.strip("|"):
            return hashlib.sha1(normalized.encode("utf-8", errors="ignore")).hexdigest()
        return self._file_fingerprint(Path(meta.file_path))

    def _file_fingerprint(self, file_path: Path) -> str:
        try:
            data = file_path.read_bytes()
            return hashlib.sha1(data).hexdigest()
        except Exception:
            return hashlib.sha1(str(file_path).encode("utf-8")).hexdigest()

    def _build_candidate(
        self, meta: AudioMetadata, identity_key: str
    ) -> AudioDuplicateCandidate:
        score = self._quality_score(meta)
        return AudioDuplicateCandidate(
            file_path=meta.file_path,
            title=meta.title,
            artist=meta.artist,
            album=meta.album,
            codec=meta.codec,
            bitrate=meta.bitrate,
            sample_rate=meta.sample_rate,
            channels=meta.channels,
            bit_depth=meta.bit_depth,
            duration=meta.duration,
            lossless=meta.lossless,
            file_size=meta.file_size,
            identity_key=identity_key,
            quality_score=score,
        )

    def _quality_score(self, meta: AudioMetadata) -> int:
        score = 0
        if meta.lossless:
            score += 5000
        if meta.bitrate:
            score += min(meta.bitrate // 1000, 3200)
        if meta.sample_rate:
            score += min(meta.sample_rate // 10, 500)
        if meta.channels:
            score += meta.channels * 100
        if meta.bit_depth:
            score += meta.bit_depth * 50
        score += min(meta.file_size // (1024 * 1024), 2000)
        if meta.codec:
            codec = meta.codec.lower()
            if any(token in codec for token in ("flac", "alac", "wav")):
                score += 1500
            elif any(token in codec for token in ("mp3", "aac", "ogg", "wma")):
                score += 500
        return score

    def _normalize_text(self, value: str) -> str:
        return " ".join(str(value or "").strip().lower().split())


audio_duplicate_finder = AudioDuplicateFinder()
