#!/usr/bin/env python3
"""Helpers de formato para la vista musical."""

from __future__ import annotations

from typing import Any, Dict

from src.gui.music_duplicates_constants import LOOKUP_REASON_LABELS


def format_lookup_reason(reason: str) -> str:
    return LOOKUP_REASON_LABELS.get(str(reason or ""), str(reason or ""))


def format_quality(track: Dict[str, Any]) -> str:
    bitrate = track.get("bitrate")
    sample_rate = track.get("sample_rate")
    channels = track.get("channels")
    parts = []
    try:
        if bitrate:
            parts.append(f"{int(float(bitrate) / 1000)} kbps")
    except Exception:
        pass
    try:
        if sample_rate:
            parts.append(f"{float(sample_rate) / 1000:.1f} kHz")
    except Exception:
        pass
    try:
        if channels:
            parts.append(f"{int(channels)} ch")
    except Exception:
        pass
    return " | ".join(parts) if parts else "-"


def format_bitrate(bitrate: Any) -> str:
    try:
        value = int(float(bitrate or 0))
        return f"{value // 1000} kbps" if value > 0 else "-"
    except Exception:
        return "-"


def format_file_size(size: Any) -> str:
    try:
        value = float(size or 0)
    except Exception:
        return "-"
    if value <= 0:
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return "-"


def format_duration(duration: Any) -> str:
    try:
        total_seconds = int(round(float(duration or 0)))
    except Exception:
        return "-"
    if total_seconds <= 0:
        return "-"
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"
