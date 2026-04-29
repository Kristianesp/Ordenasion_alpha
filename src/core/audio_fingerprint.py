#!/usr/bin/env python3
"""Fingerprint opcional y enriquecimiento online de metadatos."""

from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Optional
import urllib.error
import urllib.parse
import urllib.request
import json
import subprocess
import shutil


class AudioFingerprintService:
    """Servicio opcional que prepara fingerprints y metadatos externos."""

    AUTO_APPLY_CONFIDENCE_THRESHOLD = 210
    AUTO_APPLY_EXACT_RATIO = 0.985
    AUTO_APPLY_STRONG_TITLE_RATIO = 0.94
    AUTO_APPLY_STRONG_ARTIST_RATIO = 0.90

    def _is_online_metadata_enabled(self) -> bool:
        try:
            from src.utils.app_config import AppConfig

            return AppConfig().get_audio_online_metadata_enabled()
        except Exception:
            return True

    def _disabled_lookup_result(
        self,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        reason: str = "not_attempted",
    ) -> Dict[str, Any]:
        metadata = dict(metadata or {})
        metadata.setdefault("file_path", str(file_path))
        return {
            "available": False,
            "source": "offline",
            "reason": reason,
            "suggested_updates": self._suggest_from_local(file_path, metadata),
            "confidence": 0,
            "cover_url": "",
            "thumb_url": "",
            "candidates": [],
            "diagnostics": {
                "lookup_mode": "disabled",
                "fingerprint_strategy": "none",
                "acoustid_reason": reason,
                "musicbrainz_reason": reason,
                "discogs_reason": reason,
                "candidate_counts": {
                    "acoustid": 0,
                    "musicbrainz": 0,
                    "discogs": 0,
                },
            },
        }

    def build_lookup_cache_key(
        self, file_path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        payload = {
            "file_path": str(Path(file_path)),
            "file_size": str((metadata or {}).get("file_size") or ""),
            "mtime": str((metadata or {}).get("mtime") or ""),
            "title": str((metadata or {}).get("title") or "").strip(),
            "artist": str((metadata or {}).get("artist") or "").strip(),
            "album_artist": str((metadata or {}).get("album_artist") or "").strip(),
            "album": str((metadata or {}).get("album") or "").strip(),
            "year": str((metadata or {}).get("year") or "").strip(),
            "genre": str((metadata or {}).get("genre") or "").strip(),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()

    def get_or_lookup_online_metadata(
        self,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        from src.core.audio_index import audio_metadata_service

        file_path = Path(file_path)
        metadata = dict(metadata or {})
        metadata.setdefault("file_path", str(file_path))
        cache_key = self.build_lookup_cache_key(file_path, metadata)
        if not force_refresh:
            cached = audio_metadata_service.get_lookup_cache(file_path, cache_key)
            if cached:
                cached.setdefault("file_path", str(file_path))
                cached.setdefault("local_metadata", dict(metadata))
                cached.setdefault(
                    "candidate_count", len(cached.get("candidates") or [])
                )
                cached["cache_status"] = "cached"
                return cached

        if not self._is_online_metadata_enabled():
            disabled_result = self._disabled_lookup_result(
                file_path,
                metadata,
                reason="not_attempted",
            )
            disabled_result["file_path"] = str(file_path)
            disabled_result["local_metadata"] = dict(metadata)
            disabled_result["cache_key"] = cache_key
            disabled_result["candidate_count"] = 0
            return disabled_result

        raw_result = self.lookup_online_metadata(file_path, metadata)
        prepared = self._prepare_lookup_result(
            file_path, metadata, raw_result, cache_key
        )
        prepared["cache_status"] = "fresh"
        prepared["cache_updated_at"] = datetime.now().isoformat(timespec="seconds")
        audio_metadata_service.set_lookup_cache(
            file_path,
            cache_key,
            prepared,
            cover_art=prepared.get("cached_cover_art"),
        )
        return prepared

    def get_cover_art_bytes_for_result(
        self, file_path: Path, result: Optional[Dict[str, Any]] = None
    ) -> bytes | None:
        from src.core.audio_index import audio_metadata_service

        file_path = Path(file_path)
        result = dict(result or {})
        cached_cover_art = result.get("cached_cover_art")
        if cached_cover_art:
            return bytes(cached_cover_art)

        cache_key = str(result.get("cache_key") or "").strip()
        if not cache_key:
            local_metadata = dict(result.get("local_metadata") or {})
            if local_metadata:
                cache_key = self.build_lookup_cache_key(file_path, local_metadata)
        if cache_key:
            cached = audio_metadata_service.get_lookup_cache(file_path, cache_key)
            if cached and cached.get("cached_cover_art"):
                return bytes(cached.get("cached_cover_art") or b"")

        cover_art = self._download_cover_art_for_result(result)
        if cover_art and cache_key:
            audio_metadata_service.update_lookup_cache_cover_art(
                file_path,
                cache_key,
                cover_art,
            )
        return cover_art

    def get_cover_art_bytes_for_url(self, url: str) -> bytes | None:
        return self._download_cover_art_from_url(url)

    def _cover_urls_for_result(
        self, result: Optional[Dict[str, Any]] = None
    ) -> list[str]:
        result = dict(result or {})
        urls: list[str] = []

        def add_url(value: Any) -> None:
            candidate = str(value or "").strip()
            if candidate and candidate not in urls:
                urls.append(candidate)

        add_url(result.get("selected_cover_url"))
        for choice in result.get("cover_choices") or []:
            if isinstance(choice, dict):
                add_url(choice.get("url"))
            else:
                add_url(choice)
        for key in ("cover_url", "thumb_url"):
            add_url(result.get(key))
        for candidate in result.get("candidates") or []:
            for choice in candidate.get("cover_choices") or []:
                if isinstance(choice, dict):
                    add_url(choice.get("url"))
                else:
                    add_url(choice)
            for key in ("cover_url", "thumb_url"):
                add_url(candidate.get(key))
        return urls

    def _download_cover_art_for_result(
        self, result: Optional[Dict[str, Any]] = None
    ) -> bytes | None:
        for url in self._cover_urls_for_result(result):
            data = self._download_cover_art_from_url(url)
            if data:
                return data
        return None

    def _download_cover_art_from_url(self, url: str) -> bytes | None:
        value = str(url or "").strip()
        if not value:
            return None
        try:
            request = urllib.request.Request(
                value,
                headers={"User-Agent": self._resolve_useragent()},
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                data = response.read()
            return data if data else None
        except Exception:
            return None

    def _prepare_lookup_result(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        result: Dict[str, Any],
        cache_key: str,
    ) -> Dict[str, Any]:
        diagnostics = result.get("diagnostics", {})
        candidate_list = list(result.get("candidates", []))
        cover_choices = self._build_cover_choices(result, candidate_list)
        for candidate in candidate_list:
            candidate.setdefault("diagnostics", diagnostics)
            candidate.setdefault("reason", result.get("reason", "ok"))
            candidate.setdefault(
                "fingerprint_strategy",
                diagnostics.get("fingerprint_strategy", "none"),
            )
        cover_art = self._download_cover_art_for_result(result)
        return {
            "file_path": str(file_path),
            "local_metadata": dict(metadata),
            "confidence": candidate_list[0].get("confidence", 0)
            if candidate_list
            else 0,
            "candidate_count": len(candidate_list),
            "cache_key": cache_key,
            "cached_cover_art": cover_art,
            "cache_status": "fresh",
            "cover_choices": cover_choices,
            **result,
            "candidates": candidate_list,
        }

    def _build_cover_choices(
        self, result: Dict[str, Any], candidate_list: list[Dict[str, Any]]
    ) -> list[Dict[str, str]]:
        seen: set[str] = set()
        choices: list[Dict[str, str]] = []

        def add_choice(url: str, source: str, label: str) -> None:
            normalized = str(url or "").strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            choices.append(
                {
                    "url": normalized,
                    "source": str(source or "unknown"),
                    "label": str(label or "Portada"),
                }
            )

        add_choice(
            str(result.get("cover_url") or result.get("thumb_url") or ""),
            str(result.get("source") or "unknown"),
            "Principal",
        )
        add_choice(
            str(result.get("thumb_url") or ""),
            str(result.get("source") or "unknown"),
            "Miniatura principal",
        )
        for index, candidate in enumerate(candidate_list, start=1):
            suggested = dict(candidate.get("suggested_updates") or {})
            album = str(suggested.get("album") or candidate.get("album") or "").strip()
            label = album or f"Candidata {index}"
            add_choice(
                str(candidate.get("cover_url") or candidate.get("thumb_url") or ""),
                str(candidate.get("source") or result.get("source") or "unknown"),
                label,
            )
            add_choice(
                str(candidate.get("thumb_url") or ""),
                str(candidate.get("source") or result.get("source") or "unknown"),
                f"{label} (miniatura)",
            )
        return choices

    def fingerprint_file(self, file_path: Path) -> Dict[str, Any]:
        file_path = Path(file_path)
        acoustid_key = self._get_acoustid_api_key()
        fpcalc_path = self._resolve_fpcalc_path()
        self._debug(
            f"Fingerprint start | file={file_path.name} | acoustid_key={self._mask_secret(acoustid_key)} | fpcalc={fpcalc_path or 'missing'}"
        )
        if acoustid_key and fpcalc_path:
            try:
                self._debug(
                    f"Running fpcalc | file={file_path.name} | binary={fpcalc_path}"
                )
                result = subprocess.run(
                    [fpcalc_path, str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=25,
                    check=True,
                )
                payload = self._parse_fpcalc_output(result.stdout)
                if not payload:
                    self._debug(
                        f"fpcalc unparsed stdout | file={file_path.name} | {self._preview_value(result.stdout, 700)}"
                    )
                    if result.stderr:
                        self._debug(
                            f"fpcalc stderr | file={file_path.name} | {self._preview_value(result.stderr, 280)}"
                        )
                    raise ValueError("fpcalc_output_unparsed")
                fingerprint_value = str(payload.get("fingerprint") or "")
                self._debug(
                    "fpcalc ok | "
                    f"file={file_path.name} | duration={payload.get('duration')} | "
                    f"fingerprint_len={len(fingerprint_value)} | "
                    f"fingerprint_preview={self._preview_value(fingerprint_value, 36)}"
                )
                return {
                    "file_path": str(file_path),
                    "fingerprint": payload.get("fingerprint"),
                    "duration": payload.get("duration"),
                    "strategy": "chromaprint",
                    "available": True,
                }
            except Exception as exc:
                self._debug(
                    f"fpcalc failed | file={file_path.name} | error={type(exc).__name__}: {exc}"
                )
                stdout = getattr(exc, "stdout", "")
                stderr = getattr(exc, "stderr", "")
                if stdout:
                    self._debug(
                        f"fpcalc stdout | file={file_path.name} | {self._preview_value(stdout, 280)}"
                    )
                if stderr:
                    self._debug(
                        f"fpcalc stderr | file={file_path.name} | {self._preview_value(stderr, 280)}"
                    )
        else:
            reasons = []
            if not acoustid_key:
                reasons.append("missing_acoustid_key")
            if not fpcalc_path:
                reasons.append("missing_fpcalc")
            self._debug(
                f"Chromaprint skip | file={file_path.name} | reason={'+'.join(reasons) or 'unknown'}"
            )
        try:
            data = file_path.read_bytes()
            sha1_value = hashlib.sha1(data).hexdigest()
            self._debug(
                f"SHA1 fallback | file={file_path.name} | size={len(data)} | sha1={sha1_value[:16]}..."
            )
            return {
                "file_path": str(file_path),
                "fingerprint": sha1_value,
                "strategy": "sha1-file",
                "available": True,
            }
        except Exception as exc:
            self._debug(
                f"Fingerprint unavailable | file={file_path.name} | error={type(exc).__name__}: {exc}"
            )
            return {
                "file_path": str(file_path),
                "fingerprint": None,
                "strategy": "unavailable",
                "available": False,
                "error": str(exc),
            }

    def lookup_online_metadata(
        self, file_path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Busca candidatos online gratuitos y devuelve sugerencias priorizadas."""
        metadata = metadata or {}
        if not self._is_online_metadata_enabled():
            return self._disabled_lookup_result(
                Path(file_path),
                metadata,
                reason="not_attempted",
            )
        self._debug(
            "Online lookup start | "
            f"file={Path(file_path).name} | "
            f"title={self._preview_value(metadata.get('title') or '', 80)} | "
            f"artist={self._preview_value(metadata.get('artist') or metadata.get('album_artist') or '', 80)} | "
            f"album={self._preview_value(metadata.get('album') or '', 80)}"
        )
        useragent = self._resolve_useragent()
        self._debug(
            f"Online lookup user-agent | file={Path(file_path).name} | ua={useragent}"
        )
        if not useragent:
            return {
                "available": False,
                "source": "offline",
                "reason": "missing_useragent",
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "candidates": [],
            }

        acoustid_result = self.lookup_acoustid(file_path, metadata)
        self._debug(
            "AcoustID result | "
            f"file={Path(file_path).name} | reason={acoustid_result.get('reason', 'unknown')} | "
            f"candidates={len(acoustid_result.get('candidates', []))} | "
            f"fingerprint={acoustid_result.get('fingerprint_strategy', 'none')}"
        )
        musicbrainz_result = self.lookup_musicbrainz_candidates(file_path, metadata)
        self._debug(
            "MusicBrainz result | "
            f"file={Path(file_path).name} | reason={musicbrainz_result.get('reason', 'unknown')} | "
            f"candidates={len(musicbrainz_result.get('candidates', []))} | "
            f"query={self._preview_value(musicbrainz_result.get('query') or '', 120)}"
        )
        discogs_result = self.lookup_discogs(file_path, metadata)
        discogs_reason = discogs_result.get("reason", "unknown")
        self._debug(
            "Discogs result | "
            f"file={Path(file_path).name} | reason={discogs_reason} | "
            f"candidates={len(discogs_result.get('candidates', []))}"
        )

        acoustid_candidates = list(acoustid_result.get("candidates", []))
        musicbrainz_candidates = list(musicbrainz_result.get("candidates", []))
        discogs_candidates = list(discogs_result.get("candidates", []))
        combined_candidates = self._merge_lookup_candidates(
            acoustid_candidates,
            musicbrainz_candidates,
            discogs_candidates,
        )
        diagnostics = {
            "acoustid_reason": acoustid_result.get("reason", "not_used"),
            "fingerprint_strategy": acoustid_result.get("fingerprint_strategy", "none"),
            "lookup_mode": "combined",
            "musicbrainz_query": musicbrainz_result.get("query", ""),
            "musicbrainz_reason": musicbrainz_result.get("reason", "not_run"),
            "discogs_reason": discogs_reason,
            "candidate_counts": {
                "acoustid": len(acoustid_candidates),
                "musicbrainz": len(musicbrainz_candidates),
                "discogs": len(discogs_candidates),
            },
        }
        self._debug(
            "Combined lookup result | "
            f"file={Path(file_path).name} | acoustid={len(acoustid_candidates)} | "
            f"musicbrainz={len(musicbrainz_candidates)} | discogs={len(discogs_candidates)} | "
            f"total={len(combined_candidates)} | top={self._summarize_candidates(combined_candidates)}"
        )

        if combined_candidates:
            top_candidate = combined_candidates[0]
            return {
                "available": True,
                "source": top_candidate.get("source", "unknown"),
                "reason": "ok",
                "suggested_updates": top_candidate.get("suggested_updates", {}),
                "confidence": top_candidate.get("confidence", 0),
                "cover_url": top_candidate.get("cover_url", ""),
                "thumb_url": top_candidate.get("thumb_url", ""),
                "diagnostics": diagnostics,
                "candidates": combined_candidates,
            }

        return {
            "available": False,
            "source": "mixed",
            "reason": self._select_lookup_reason(
                [
                    acoustid_result.get("reason", ""),
                    musicbrainz_result.get("reason", ""),
                    discogs_result.get("reason", ""),
                ]
            ),
            "suggested_updates": self._suggest_from_local(file_path, metadata),
            "confidence": 0,
            "cover_url": "",
            "thumb_url": "",
            "diagnostics": diagnostics,
            "candidates": [],
        }

    def lookup_acoustid(
        self, file_path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        api_key = self._get_acoustid_api_key()
        fingerprint = self.fingerprint_file(file_path)
        diagnostics = {
            "lookup_mode": "acoustid",
            "fingerprint_strategy": fingerprint.get("strategy", "none"),
            "acoustid_reason": "pending",
        }
        if not api_key:
            diagnostics["acoustid_reason"] = "missing_api_key"
            self._debug(
                f"AcoustID skipped | file={Path(file_path).name} | reason=missing_api_key"
            )
            return {
                "available": False,
                "source": "acoustid",
                "reason": "missing_api_key",
                "fingerprint_strategy": fingerprint.get("strategy", "none"),
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        if not fingerprint.get("available") or not fingerprint.get("fingerprint"):
            diagnostics["acoustid_reason"] = "fingerprint_unavailable"
            self._debug(
                "AcoustID skipped | "
                f"file={Path(file_path).name} | reason=fingerprint_unavailable | "
                f"strategy={fingerprint.get('strategy', 'none')}"
            )
            return {
                "available": False,
                "source": "acoustid",
                "reason": "fingerprint_unavailable",
                "fingerprint_strategy": fingerprint.get("strategy", "none"),
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        duration = int(float(fingerprint.get("duration") or 0))
        fingerprint_value = str(fingerprint.get("fingerprint") or "")
        if fingerprint.get("strategy") != "chromaprint" or duration <= 0:
            diagnostics["acoustid_reason"] = "invalid_fingerprint_payload"
            self._debug(
                "AcoustID skipped | "
                f"file={Path(file_path).name} | reason=invalid_fingerprint_payload | "
                f"strategy={fingerprint.get('strategy', 'none')} | duration={duration}"
            )
            return {
                "available": False,
                "source": "acoustid",
                "reason": "invalid_fingerprint_payload",
                "fingerprint_strategy": fingerprint.get("strategy", "none"),
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        self._debug(
            "AcoustID request | "
            f"file={Path(file_path).name} | duration={duration} | "
            f"fingerprint_strategy={fingerprint.get('strategy', 'none')} | "
            f"fingerprint_len={len(fingerprint_value)} | "
            f"fingerprint_preview={self._preview_value(fingerprint_value, 36)}"
        )
        params = urllib.parse.urlencode(
            {
                "client": api_key,
                "duration": duration,
                "fingerprint": fingerprint.get("fingerprint"),
                "meta": "recordings+releases+releasegroups+compress",
            }
        )
        request = urllib.request.Request(
            f"https://api.acoustid.org/v2/lookup?{params}",
            headers={"User-Agent": self._resolve_useragent()},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_status = (
                    getattr(response, "status", None) or response.getcode()
                )
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as exc:
            diagnostics["acoustid_reason"] = "lookup_failed"
            body = exc.read().decode("utf-8", errors="ignore")
            error_reason = self._parse_acoustid_error_reason(body) or "lookup_failed"
            diagnostics["acoustid_reason"] = error_reason
            self._debug(
                "AcoustID HTTP error | "
                f"file={Path(file_path).name} | status={exc.code} | reason={exc.reason}"
            )
            if body:
                self._debug(
                    f"AcoustID error body | file={Path(file_path).name} | {self._preview_value(body, 700)}"
                )
            if error_reason == "invalid_client_key":
                self._debug(
                    "AcoustID hint | lookup expects the application client key; the profile page key is not valid for client="
                )
            return {
                "available": False,
                "source": "acoustid",
                "reason": error_reason,
                "fingerprint_strategy": fingerprint.get("strategy", "none"),
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        except Exception as exc:
            diagnostics["acoustid_reason"] = "lookup_failed"
            self._debug(
                f"AcoustID lookup failed | file={Path(file_path).name} | error={type(exc).__name__}: {exc}"
            )
            return {
                "available": False,
                "source": "acoustid",
                "reason": "lookup_failed",
                "fingerprint_strategy": fingerprint.get("strategy", "none"),
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        payload = self._hydrate_acoustid_results(payload, api_key, file_path)
        raw_results = payload.get("results", [])
        raw_recordings = sum(len(item.get("recordings", [])) for item in raw_results)
        self._debug(
            "AcoustID response | "
            f"file={Path(file_path).name} | http_status={response_status} | "
            f"api_status={payload.get('status')} | results={len(raw_results)} | recordings={raw_recordings}"
        )
        self._debug_payload("AcoustID response", payload, limit=900)
        candidates = self._parse_acoustid_results(payload, metadata)
        diagnostics["acoustid_reason"] = "ok" if candidates else "no_candidates"
        self._debug(
            "AcoustID parsed candidates | "
            f"file={Path(file_path).name} | kept={len(candidates)} | "
            f"top={self._summarize_candidates(candidates)}"
        )
        return {
            "available": bool(candidates),
            "source": "acoustid",
            "reason": "ok" if candidates else "no_candidates",
            "fingerprint_strategy": fingerprint.get("strategy", "none"),
            "suggested_updates": candidates[0].get("suggested_updates", {})
            if candidates
            else self._suggest_from_local(file_path, metadata),
            "diagnostics": diagnostics,
            "candidates": candidates,
        }

    def lookup_musicbrainz_candidates(
        self, file_path: Path, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        metadata = dict(metadata or {})
        metadata.setdefault("file_path", str(file_path))
        queries = self._build_query_strategies(file_path, metadata)
        self._debug(
            "MusicBrainz strategies | "
            f"file={Path(file_path).name} | queries={self._preview_value(queries, 700)}"
        )
        last_query = ""
        seen: dict[str, Dict[str, Any]] = {}

        for query in queries:
            if not query:
                continue
            last_query = query
            for candidate in self._query_musicbrainz_api(query, metadata):
                key = candidate.get("mbid") or self._candidate_key(candidate)
                previous = seen.get(key)
                if not previous or candidate.get("confidence", 0) > previous.get(
                    "confidence", 0
                ):
                    candidate["query"] = query
                    seen[key] = candidate

        if not seen:
            for candidate in self._query_musicbrainz_release_group(file_path, metadata):
                key = candidate.get("mbid") or self._candidate_key(candidate)
                previous = seen.get(key)
                if not previous or candidate.get("confidence", 0) > previous.get(
                    "confidence", 0
                ):
                    seen[key] = candidate

        candidates = list(seen.values())

        candidates = sorted(
            candidates, key=lambda item: item.get("confidence", 0), reverse=True
        )
        candidates = self._dedupe_candidates(candidates)
        suggested = (
            candidates[0].get("suggested_updates", {})
            if candidates
            else self._suggest_from_local(file_path, metadata)
        )
        self._debug(
            "MusicBrainz aggregated candidates | "
            f"file={Path(file_path).name} | total={len(candidates)} | "
            f"top={self._summarize_candidates(candidates)}"
        )

        return {
            "available": True,
            "source": "musicbrainz",
            "reason": "ok" if candidates else "no_candidates",
            "query": last_query,
            "suggested_updates": suggested,
            "candidates": candidates,
        }

    def _query_musicbrainz_api(
        self, query: str, metadata: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        params = urllib.parse.urlencode({"query": query, "fmt": "json", "limit": 10})
        url = f"https://musicbrainz.org/ws/2/recording/?{params}"
        self._debug(f"MusicBrainz request | query={self._preview_value(query, 180)}")
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"{self._resolve_useragent()} (https://musicbrainz.org)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                response_status = (
                    getattr(response, "status", None) or response.getcode()
                )
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            self._debug(
                "MusicBrainz HTTP error | "
                f"query={self._preview_value(query, 180)} | status={exc.code} | reason={exc.reason}"
            )
            if body:
                self._debug(
                    f"MusicBrainz error body | query={self._preview_value(query, 120)} | {self._preview_value(body, 500)}"
                )
            return []
        except Exception as exc:
            self._debug(
                f"MusicBrainz lookup failed | query={self._preview_value(query, 180)} | error={type(exc).__name__}: {exc}"
            )
            return []
        self._debug(
            "MusicBrainz response | "
            f"query={self._preview_value(query, 180)} | http_status={response_status} | "
            f"recordings={len(payload.get('recordings', []))}"
        )
        candidates: list[Dict[str, Any]] = []
        for rec in payload.get("recordings", []):
            candidates.append(self._build_candidate_from_recording(rec, metadata))
        candidates = self._filter_irrelevant_candidates(candidates, metadata)
        candidates = self._dedupe_candidates(candidates)
        self._debug(
            "MusicBrainz parsed candidates | "
            f"query={self._preview_value(query, 180)} | kept={len(candidates[:10])} | "
            f"top={self._summarize_candidates(candidates)}"
        )
        return candidates[:10]

    def _query_musicbrainz_release_group(
        self, file_path: Path, metadata: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        title = self._best_value(metadata, ["title"]) or file_path.stem
        artist = self._best_value(metadata, ["artist", "album_artist"])
        query = urllib.parse.urlencode(
            {
                "query": f'title:"{title}"'
                + (f' AND artist:"{artist}"' if artist else ""),
                "fmt": "json",
                "limit": 5,
            }
        )
        url = f"https://musicbrainz.org/ws/2/recording/?{query}"
        self._debug(
            "MusicBrainz release-group request | "
            f"file={file_path.name} | query={self._preview_value(urllib.parse.unquote(query), 180)}"
        )
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                response_status = (
                    getattr(response, "status", None) or response.getcode()
                )
                data = json.loads(response.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            self._debug(
                "MusicBrainz release-group HTTP error | "
                f"file={file_path.name} | status={exc.code} | reason={exc.reason}"
            )
            if body:
                self._debug(
                    f"MusicBrainz release-group error body | file={file_path.name} | {self._preview_value(body, 500)}"
                )
            return []
        except Exception as exc:
            self._debug(
                f"MusicBrainz release-group failed | file={file_path.name} | error={type(exc).__name__}: {exc}"
            )
            return []
        self._debug(
            "MusicBrainz release-group response | "
            f"file={file_path.name} | http_status={response_status} | recordings={len(data.get('recordings', []))}"
        )
        candidates: list[Dict[str, Any]] = []
        for rec in data.get("recordings", []):
            artist_name = ""
            if rec.get("artist-credit"):
                artist_name = " ".join(
                    part.get("name", "")
                    for part in rec["artist-credit"]
                    if isinstance(part, dict)
                )
            candidates.append(
                self._build_candidate_from_recording(
                    {
                        "id": rec.get("id", ""),
                        "title": rec.get("title", ""),
                        "artist-credit": rec.get("artist-credit", []),
                        "release-list": rec.get("releases", []),
                    },
                    metadata,
                )
            )
        filtered = self._filter_irrelevant_candidates(candidates, metadata)
        self._debug(
            "MusicBrainz release-group parsed candidates | "
            f"file={file_path.name} | kept={len(filtered)} | top={self._summarize_candidates(filtered)}"
        )
        return filtered

    def build_batch_suggestions(
        self, tracks: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        items = []
        for track in tracks:
            file_path = Path(track.get("file_path", ""))
            result = self.get_or_lookup_online_metadata(file_path, track)
            result["file_path"] = str(file_path)
            items.append(result)
        return items

    def should_auto_apply_result(self, result: Dict[str, Any]) -> bool:
        candidates = list(result.get("candidates") or [])
        if len(candidates) != 1:
            return False
        local_metadata = dict(result.get("local_metadata") or {})
        file_path = str(
            result.get("file_path") or local_metadata.get("file_path") or ""
        )
        if file_path and not local_metadata.get("file_path"):
            local_metadata["file_path"] = file_path
        return self.should_auto_apply_candidate(local_metadata, candidates[0])

    def should_auto_apply_candidate(
        self, local_metadata: Dict[str, Any], candidate: Dict[str, Any]
    ) -> bool:
        suggested = candidate.get("suggested_updates") or {}
        if not suggested:
            return False

        confidence = int(candidate.get("confidence", 0) or 0)
        if confidence < self.AUTO_APPLY_CONFIDENCE_THRESHOLD:
            return False

        match = self._auto_apply_match_context(local_metadata, candidate)
        expected_title = match["expected_title"]
        expected_artist = match["expected_artist"]
        candidate_title = match["candidate_title"]
        title_ratio = match["title_ratio"]
        artist_ratio = match["artist_ratio"]

        if not expected_title or not candidate_title:
            return False

        title_exact = title_ratio >= self.AUTO_APPLY_EXACT_RATIO
        artist_exact = (
            not expected_artist or artist_ratio >= self.AUTO_APPLY_EXACT_RATIO
        )
        if title_exact and artist_exact:
            return True

        if title_ratio < self.AUTO_APPLY_STRONG_TITLE_RATIO:
            return False
        if expected_artist and artist_ratio < self.AUTO_APPLY_STRONG_ARTIST_RATIO:
            return False
        return True

    def _auto_apply_match_context(
        self, local_metadata: Dict[str, Any], candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        file_path = Path(str(local_metadata.get("file_path") or "track.mp3"))
        file_artist, file_title = self._split_filename_guess(file_path)
        expected_title = self.clean_text_for_query(
            self._best_value(local_metadata, ["title"]) or file_title or file_path.stem
        ).lower()
        expected_artist = self.clean_text_for_query(
            self._best_value(local_metadata, ["artist", "album_artist"]) or file_artist
        ).lower()
        suggested = candidate.get("suggested_updates") or {}
        candidate_title = self.clean_text_for_query(
            str(candidate.get("title") or suggested.get("title") or "")
        ).lower()
        candidate_artist = self.clean_text_for_query(
            str(candidate.get("artist") or suggested.get("artist") or "")
        ).lower()
        return {
            "expected_title": expected_title,
            "expected_artist": expected_artist,
            "candidate_title": candidate_title,
            "candidate_artist": candidate_artist,
            "title_ratio": self._similarity_ratio(expected_title, candidate_title),
            "artist_ratio": self._similarity_ratio(expected_artist, candidate_artist),
        }

    def _similarity_ratio(self, expected: str, candidate: str) -> float:
        left = str(expected or "").strip().lower()
        right = str(candidate or "").strip().lower()
        if not left or not right:
            return 0.0
        if left == right:
            return 1.0
        return SequenceMatcher(None, left, right).ratio()

    def _build_candidate_from_recording(
        self, rec: Dict[str, Any], local: Dict[str, Any]
    ) -> Dict[str, Any]:
        title = rec.get("title", "")
        artist = ""
        if rec.get("artist-credit"):
            artist = " ".join(
                part.get("name", "")
                for part in rec["artist-credit"]
                if isinstance(part, dict)
            )
        releases = rec.get("release-list") or rec.get("releases") or []
        release = releases[0] if releases else {}
        album = release.get("title", "")
        year = (
            release.get("date", "")[:4]
            if release.get("date")
            else str(rec.get("first-release-date") or "")[:4]
        )
        duration = self._extract_recording_duration(rec) or self._extract_duration(
            local
        )
        search_score = self._extract_search_score(rec)
        release_mbid = str(release.get("id") or "")
        cover_url = self._build_musicbrainz_cover_url(release_mbid)
        confidence = self._score_candidate(
            local, title, artist, album, duration, search_score
        )
        suggested = {
            "title": title or local.get("title") or "",
            "artist": artist or local.get("artist") or local.get("album_artist") or "",
            "album": album or local.get("album") or "",
        }
        if year:
            suggested["year"] = year
        return {
            "title": title,
            "artist": artist,
            "album": album,
            "year": year,
            "mbid": rec.get("id", ""),
            "release_mbid": release_mbid,
            "confidence": confidence,
            "search_score": search_score,
            "duration": duration,
            "source": "musicbrainz",
            "cover_url": cover_url,
            "thumb_url": cover_url,
            "suggested_updates": suggested,
        }

    def _build_musicbrainz_cover_url(self, release_mbid: str) -> str:
        release_id = str(release_mbid or "").strip()
        if not release_id:
            return ""
        return f"https://coverartarchive.org/release/{release_id}/front-250"

    def _score_candidate(
        self,
        local: Dict[str, Any],
        title: str,
        artist: str,
        album: str,
        duration: float | None = None,
        search_score: int = 0,
    ) -> int:
        score = max(0, search_score)
        local_title = str(local.get("title") or "").strip().lower()
        local_artist = (
            str(local.get("artist") or local.get("album_artist") or "").strip().lower()
        )
        local_album = str(local.get("album") or "").strip().lower()
        file_artist, file_title = self._split_filename_guess(
            Path(str(local.get("file_path") or "track.mp3"))
        )
        if local_title:
            score += int(SequenceMatcher(None, local_title, title.lower()).ratio() * 50)
        if local_artist:
            score += int(
                SequenceMatcher(None, local_artist, artist.lower()).ratio() * 30
            )
        if local_album:
            score += int(SequenceMatcher(None, local_album, album.lower()).ratio() * 20)
        if file_title:
            score += int(
                SequenceMatcher(
                    None,
                    self.clean_text_for_query(file_title).lower(),
                    self.clean_text_for_query(title).lower(),
                ).ratio()
                * 35
            )
        if file_artist:
            score += int(
                SequenceMatcher(
                    None,
                    self.clean_text_for_query(file_artist).lower(),
                    self.clean_text_for_query(artist).lower(),
                ).ratio()
                * 20
            )
        if duration:
            local_duration = self._extract_duration(local)
            if local_duration:
                delta = abs(local_duration - duration)
                score += max(0, 20 - int(delta * 2))
        file_artist = self._best_value(local, ["artist", "album_artist"])
        file_title = self._best_value(local, ["title"]) or self.clean_text_for_query(
            str(local.get("file_path", ""))
        )
        if file_title:
            score += int(
                SequenceMatcher(
                    None,
                    self.clean_text_for_query(file_title).lower(),
                    self.clean_text_for_query(title).lower(),
                ).ratio()
                * 20
            )
        if file_artist:
            score += int(
                SequenceMatcher(
                    None,
                    self.clean_text_for_query(file_artist).lower(),
                    self.clean_text_for_query(artist).lower(),
                ).ratio()
                * 10
            )
        if score == 0:
            score = 5
        return score

    def _resolve_useragent(self) -> str:
        return (
            os.environ.get("MUSICBRAINZ_USERAGENT", "").strip()
            or os.environ.get("MUSICBRAINZ_APP_NAME", "").strip()
            or "OrdenasionAlpha/1.0"
        )

    def _sanitize_query_text(self, value: str) -> str:
        value = str(value or "").strip().replace('"', " ")
        return self.clean_text_for_query(value)

    def _split_filename_guess(self, file_path: Path) -> tuple[str, str]:
        raw_stem = str(file_path.stem or "").strip()
        if " - " in raw_stem:
            left, right = raw_stem.split(" - ", 1)
            return self._clean_artist_hint(left), self.clean_text_for_query(right)
        normalized = raw_stem.replace(" - ", "_")
        if "_" in normalized:
            parts = [p.strip() for p in normalized.split("_") if p.strip()]
            if len(parts) >= 2:
                return self._clean_artist_hint(parts[0]), self.clean_text_for_query(
                    " ".join(parts[1:])
                )
        stem = self.clean_text_for_query(raw_stem)
        return "", stem

    def _build_query_strategies(
        self, file_path: Path, metadata: Dict[str, Any]
    ) -> list[str]:
        file_artist, file_title = self._split_filename_guess(file_path)
        raw_stem = self.clean_text_for_query(file_path.stem)
        title = self._sanitize_query_text(
            self._best_value(metadata, ["title", "track_name"])
            or file_title
            or raw_stem
        )
        artist = self._sanitize_query_text(
            self._best_value(metadata, ["artist", "album_artist"]) or file_artist
        )
        album = self._sanitize_query_text(self._best_value(metadata, ["album"]))

        queries: list[str] = []
        if title and artist:
            queries.append(f'recording:"{title}" AND artist:"{artist}"')
            queries.append(f'artist:"{artist}" AND recording:"{title}"')
        if raw_stem:
            queries.append(f'recording:"{raw_stem}"')
            queries.append(f'"{raw_stem}"')
        if title:
            queries.append(f'recording:"{title}"')
        if title and album:
            queries.append(f'recording:"{title}" AND release:"{album}"')
        if raw_stem and artist:
            queries.append(f'"{raw_stem}" AND artist:"{artist}"')
        if file_artist and file_title:
            queries.append(f'artist:"{file_artist}" AND recording:"{file_title}"')
            queries.append(f'artist:"{file_artist}" AND "{file_title}"')

        unique_queries: list[str] = []
        for query in queries:
            candidate = query.strip()
            if candidate and candidate not in unique_queries:
                unique_queries.append(candidate)
        return unique_queries

    def _candidate_key(self, candidate: Dict[str, Any]) -> str:
        return "|".join(
            [
                str(candidate.get("title") or ""),
                str(candidate.get("artist") or ""),
                str(candidate.get("album") or ""),
            ]
        )

    def _merge_lookup_candidates(
        self, *candidate_groups: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        merged: list[Dict[str, Any]] = []
        for group in candidate_groups:
            for candidate in group or []:
                merged.append(dict(candidate))
        merged = self._dedupe_candidates(merged)
        priority = {"acoustid": 0, "musicbrainz": 1, "discogs": 2}
        return sorted(
            merged,
            key=lambda item: (
                priority.get(str(item.get("source") or "").lower(), 99),
                -(int(item.get("confidence") or 0)),
                self.clean_text_for_query(str(item.get("artist") or "")).lower(),
                self.clean_text_for_query(str(item.get("title") or "")).lower(),
            ),
        )

    def _select_lookup_reason(self, reasons: list[str]) -> str:
        ordered = [str(reason or "") for reason in reasons if str(reason or "")]
        for preferred in (
            "invalid_client_key",
            "lookup_failed",
            "fingerprint_unavailable",
            "invalid_fingerprint_payload",
            "missing_api_key",
            "disabled_or_missing_token",
            "no_candidates",
        ):
            if preferred in ordered:
                return preferred
        return ordered[0] if ordered else "lookup_failed"

    def _dedupe_candidates(
        self, candidates: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        ordered: list[Dict[str, Any]] = []
        seen: dict[str, int] = {}
        for candidate in candidates:
            key = "|".join(
                [
                    self.clean_text_for_query(
                        str(candidate.get("title") or "")
                    ).lower(),
                    self.clean_text_for_query(
                        str(candidate.get("artist") or "")
                    ).lower(),
                    self.clean_text_for_query(
                        str(candidate.get("album") or "")
                    ).lower(),
                    str(candidate.get("year") or "").strip(),
                    str(candidate.get("source") or "").strip().lower(),
                ]
            )
            previous_index = seen.get(key)
            if previous_index is None:
                seen[key] = len(ordered)
                ordered.append(candidate)
                continue
            previous = ordered[previous_index]
            if candidate.get("confidence", 0) > previous.get("confidence", 0):
                ordered[previous_index] = candidate
        return ordered

    def clean_text_for_query(self, value: str) -> str:
        value = re.sub(r"(?i)\.(mp3|flac|wav|m4a|aac|ogg|wma)$", "", value)
        value = re.sub(r"(?i)https?://\S+|www\.\S+", " ", value)
        value = re.sub(
            r"(?i)[\[(]?(?:www|http|https|com|net|org|es|info|blog|download)[^\])]*[\])]?,?",
            " ",
            value,
        )
        value = re.sub(r"(?i)^\s*0\d{1,2}[\s._-]+", "", value)
        value = re.sub(r"(?i)^\s*\d{1,3}[._-]+\s*", "", value)
        value = re.sub(r"(?i)[\s._-]+\d{1,3}\s*$", "", value)
        value = re.sub(r"[_\-]+", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def _clean_artist_hint(self, value: str) -> str:
        value = str(value or "").strip()
        value = re.sub(r"(?i)https?://\S+|www\.\S+", " ", value)
        value = re.sub(r"\s+", " ", value).strip(" _-.")
        return value

    def _best_value(self, metadata: Dict[str, Any], keys: list[str]) -> str:
        for key in keys:
            value = metadata.get(key)
            if value:
                return str(value).strip()
        return ""

    def _extract_duration(self, metadata: Dict[str, Any]) -> float | None:
        for key in ("duration", "length", "track_length"):
            value = metadata.get(key)
            if value:
                try:
                    return float(value)
                except Exception:
                    continue
        return None

    def _extract_recording_duration(self, rec: Dict[str, Any]) -> float | None:
        value = rec.get("length") or rec.get("duration")
        if value is None:
            return None
        try:
            numeric = float(value)
        except Exception:
            return None
        if numeric > 1000:
            return numeric / 1000.0
        return numeric

    def _extract_search_score(self, rec: Dict[str, Any]) -> int:
        value = rec.get("score")
        if value is None:
            return 0
        try:
            return int(float(value))
        except Exception:
            return 0

    def _parse_acoustid_results(
        self, payload: Dict[str, Any], local: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        candidates: list[Dict[str, Any]] = []
        for result in payload.get("results", []):
            score = float(result.get("score") or 0.0)
            for recording in result.get("recordings", []):
                candidate = self._build_candidate_from_recording(
                    self._normalize_acoustid_recording(recording), local
                )
                candidate["source"] = "acoustid"
                candidate["confidence"] = max(
                    candidate.get("confidence", 0), int(score * 100)
                )
                candidates.append(candidate)
        candidates = self._filter_irrelevant_candidates(candidates, local)
        ranked = sorted(
            candidates, key=lambda item: item.get("confidence", 0), reverse=True
        )
        return self._dedupe_candidates(ranked)[:10]

    def _hydrate_acoustid_results(
        self, payload: Dict[str, Any], api_key: str, file_path: Path
    ) -> Dict[str, Any]:
        results = payload.get("results", [])
        hydrated = False
        for result in results:
            if result.get("recordings"):
                continue
            track_id = str(result.get("id") or "").strip()
            if not track_id:
                continue
            recordings = self._lookup_acoustid_trackid(track_id, api_key, file_path)
            if recordings:
                result["recordings"] = recordings
                hydrated = True
        if hydrated:
            self._debug_payload("AcoustID hydrated response", payload, limit=900)
        return payload

    def _lookup_acoustid_trackid(
        self, track_id: str, api_key: str, file_path: Path
    ) -> list[Dict[str, Any]]:
        params = urllib.parse.urlencode(
            {
                "client": api_key,
                "trackid": track_id,
                "meta": "recordings+releases+releasegroups+compress",
            }
        )
        request = urllib.request.Request(
            f"https://api.acoustid.org/v2/lookup?{params}",
            headers={"User-Agent": self._resolve_useragent()},
        )
        self._debug(
            f"AcoustID track lookup | file={file_path.name} | trackid={track_id}"
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_status = (
                    getattr(response, "status", None) or response.getcode()
                )
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            self._debug(
                "AcoustID track HTTP error | "
                f"file={file_path.name} | trackid={track_id} | status={exc.code} | reason={exc.reason}"
            )
            if body:
                self._debug(
                    f"AcoustID track error body | file={file_path.name} | {self._preview_value(body, 700)}"
                )
            return []
        except Exception as exc:
            self._debug(
                f"AcoustID track lookup failed | file={file_path.name} | trackid={track_id} | error={type(exc).__name__}: {exc}"
            )
            return []
        results = payload.get("results", [])
        recordings = []
        for result in results:
            recordings.extend(result.get("recordings", []))
        self._debug(
            "AcoustID track response | "
            f"file={file_path.name} | trackid={track_id} | http_status={response_status} | recordings={len(recordings)}"
        )
        if payload:
            self._debug_payload("AcoustID track response", payload, limit=800)
        return recordings

    def _normalize_acoustid_recording(
        self, recording: Dict[str, Any]
    ) -> Dict[str, Any]:
        rec = dict(recording or {})
        if not rec.get("artist-credit") and rec.get("artists"):
            rec["artist-credit"] = [
                {"name": str(item.get("name") or "")}
                for item in rec.get("artists", [])
                if isinstance(item, dict)
            ]
        if not rec.get("release-list"):
            releases = rec.get("releases") or []
            release_groups = rec.get("releasegroups") or []
            if releases:
                rec["release-list"] = releases
            elif release_groups:
                rec["release-list"] = [
                    {
                        "title": str(group.get("title") or ""),
                        "date": str(group.get("first-release-date") or ""),
                    }
                    for group in release_groups
                    if isinstance(group, dict)
                ]
        return rec

    def lookup_discogs(
        self, file_path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        token = self._get_discogs_token()
        discogs_enabled = self._get_discogs_enabled()
        diagnostics = {
            "lookup_mode": "discogs_fallback",
            "fingerprint_strategy": "none",
            "acoustid_reason": "not_used",
            "discogs_reason": "pending",
        }
        self._debug(
            "Discogs config | "
            f"file={Path(file_path).name} | enabled={discogs_enabled} | token={self._mask_secret(token)}"
        )
        if not token or not discogs_enabled:
            diagnostics["discogs_reason"] = "disabled_or_missing_token"
            self._debug(
                f"Discogs skipped | file={Path(file_path).name} | reason=disabled_or_missing_token"
            )
            return {
                "available": False,
                "source": "discogs",
                "reason": "disabled_or_missing_token",
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }

        file_artist, file_title = self._split_filename_guess(file_path)
        query = self.clean_text_for_query(file_title or file_path.stem)
        local_title = (
            self._best_value(metadata, ["title"]) or file_title or file_path.stem
        )
        local_artist = (
            self._best_value(metadata, ["artist", "album_artist"]) or file_artist
        )
        artist = self.clean_text_for_query(local_artist)
        params = {"q": query, "type": "release", "per_page": 10}
        if artist:
            params["artist"] = artist
        url = "https://api.discogs.com/database/search?" + urllib.parse.urlencode(
            params
        )
        self._debug(
            "Discogs request | "
            f"file={Path(file_path).name} | query={self._preview_value(query, 120)} | "
            f"artist={self._preview_value(artist, 120)} | url={url}"
        )
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self._resolve_useragent(),
                "Authorization": f"Discogs token={token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_status = (
                    getattr(response, "status", None) or response.getcode()
                )
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as exc:
            diagnostics["discogs_reason"] = "lookup_failed"
            body = exc.read().decode("utf-8", errors="ignore")
            self._debug(
                "Discogs HTTP error | "
                f"file={Path(file_path).name} | status={exc.code} | reason={exc.reason}"
            )
            if body:
                self._debug(
                    f"Discogs error body | file={Path(file_path).name} | {self._preview_value(body, 700)}"
                )
            return {
                "available": False,
                "source": "discogs",
                "reason": "lookup_failed",
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        except Exception as exc:
            diagnostics["discogs_reason"] = "lookup_failed"
            self._debug(
                f"Discogs lookup failed | file={Path(file_path).name} | error={type(exc).__name__}: {exc}"
            )
            return {
                "available": False,
                "source": "discogs",
                "reason": "lookup_failed",
                "suggested_updates": self._suggest_from_local(file_path, metadata),
                "diagnostics": diagnostics,
                "candidates": [],
            }
        self._debug(
            "Discogs response | "
            f"file={Path(file_path).name} | http_status={response_status} | results={len(payload.get('results', []))}"
        )
        self._debug_payload("Discogs response", payload, limit=900)

        candidates: list[Dict[str, Any]] = []
        for item in payload.get("results", []):
            title_text = str(item.get("title") or "")
            guessed_artist, guessed_title = self._split_discogs_title(title_text)
            album_title = self._normalize_discogs_album_title(
                item,
                fallback=guessed_title or title_text,
            )
            artist_name = guessed_artist or artist or local_artist
            year_value = self._normalize_discogs_year(item.get("year"))
            genre_value = self._normalize_discogs_genre(item)
            candidate = {
                "title": local_title,
                "artist": artist_name,
                "album": album_title,
                "year": year_value,
                "genre": genre_value,
                "mbid": str(item.get("id") or ""),
                "release_id": str(item.get("id") or ""),
                "cover_url": str(item.get("cover_image") or item.get("thumb") or ""),
                "thumb_url": str(item.get("thumb") or item.get("cover_image") or ""),
                "confidence": max(
                    0,
                    self._score_candidate(
                        {**metadata, "file_path": str(file_path)},
                        local_title,
                        artist_name,
                        album_title,
                        self._extract_duration(metadata),
                        52,
                    )
                    - self._discogs_candidate_penalty(item, album_title),
                ),
                "source": "discogs",
                "suggested_updates": {
                    "title": local_title,
                    "artist": artist_name,
                    "album": album_title,
                    "year": year_value,
                    "genre": genre_value,
                },
            }
            candidates.append(candidate)

        candidates = self._filter_irrelevant_candidates(
            candidates, {**metadata, "file_path": str(file_path)}
        )
        diagnostics["discogs_reason"] = "ok" if candidates else "no_candidates"
        ranked_candidates = sorted(
            candidates, key=lambda item: item.get("confidence", 0), reverse=True
        )
        ranked_candidates = self._dedupe_candidates(ranked_candidates)[:10]
        self._debug(
            "Discogs parsed candidates | "
            f"file={Path(file_path).name} | kept={len(ranked_candidates)} | "
            f"top={self._summarize_candidates(ranked_candidates)}"
        )
        return {
            "available": bool(ranked_candidates),
            "source": "discogs",
            "reason": "ok" if ranked_candidates else "no_candidates",
            "suggested_updates": ranked_candidates[0].get("suggested_updates", {})
            if ranked_candidates
            else self._suggest_from_local(file_path, metadata),
            "candidates": ranked_candidates,
            "diagnostics": diagnostics,
        }

    def _split_discogs_title(self, title_text: str) -> tuple[str, str]:
        value = str(title_text or "").strip()
        if " - " in value:
            artist, title = value.split(" - ", 1)
            return artist.strip(), title.strip()
        return "", value

    def _normalize_discogs_album_title(
        self, item: Dict[str, Any], fallback: str = ""
    ) -> str:
        raw_title = str(item.get("title") or fallback or "").strip()
        _, release_title = self._split_discogs_title(raw_title)
        album = release_title or raw_title or str(fallback or "").strip()
        album = re.sub(
            r"\s*\((?:\d{4}|\d+|CD\d+|File|Compilation|Album|Single|EP)\)\s*$",
            "",
            album,
            flags=re.IGNORECASE,
        )
        album = re.sub(r"\s{2,}", " ", album).strip(" -_")
        return album

    def _normalize_discogs_year(self, value: Any) -> str:
        text = str(value or "").strip()
        match = re.search(r"(19|20)\d{2}", text)
        return match.group(0) if match else ""

    def _normalize_discogs_genre(self, item: Dict[str, Any]) -> str:
        for key in ("style", "genre"):
            values = item.get(key) or []
            if isinstance(values, list) and values:
                return str(values[0] or "").strip()
            if isinstance(values, str) and values.strip():
                return values.strip()
        return ""

    def _discogs_candidate_penalty(self, item: Dict[str, Any], album_title: str) -> int:
        penalty = 0
        formats = item.get("format") or []
        format_values = (
            [str(value or "").lower() for value in formats]
            if isinstance(formats, list)
            else [str(formats or "").lower()]
        )
        if any(
            token in value
            for value in format_values
            for token in ("comp", "sampler", "promo", "bootleg", "unofficial")
        ):
            penalty += 12
        if any(token in str(item.get("type") or "").lower() for token in ("master",)):
            penalty += 4
        label_text = " ".join(
            str(value or "").lower() for value in (item.get("label") or [])
        )
        if any(token in label_text for token in ("various", "unknown", "promo")):
            penalty += 6
        country = str(item.get("country") or "").strip().lower()
        if country in {"unknown", "none"}:
            penalty += 4
        normalized_album = self.clean_text_for_query(album_title).lower()
        if any(
            token in normalized_album
            for token in (
                "greatest hits",
                "best of",
                "live",
                "collection",
                "anthology",
                "soundtrack",
            )
        ):
            penalty += 10
        if not album_title:
            penalty += 12
        return penalty

    def _filter_irrelevant_candidates(
        self, candidates: list[Dict[str, Any]], local: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        file_artist, file_title = self._split_filename_guess(
            Path(str(local.get("file_path") or "track.mp3"))
        )
        expected_title = self.clean_text_for_query(
            self._best_value(local, ["title"]) or file_title
        ).lower()
        expected_artist = self.clean_text_for_query(
            self._best_value(local, ["artist", "album_artist"]) or file_artist
        ).lower()
        filtered: list[Dict[str, Any]] = []
        for candidate in candidates:
            candidate_title = self.clean_text_for_query(
                str(candidate.get("title") or "")
            ).lower()
            candidate_artist = self.clean_text_for_query(
                str(candidate.get("artist") or "")
            ).lower()
            title_ratio = (
                SequenceMatcher(None, expected_title, candidate_title).ratio()
                if expected_title
                else 0.0
            )
            artist_ratio = (
                SequenceMatcher(None, expected_artist, candidate_artist).ratio()
                if expected_artist
                else 0.0
            )
            if (
                expected_title
                and title_ratio < 0.35
                and expected_artist
                and artist_ratio < 0.35
            ):
                continue
            filtered.append(candidate)
        return filtered or candidates

    def _suggest_from_local(
        self, file_path: Path, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        if not metadata.get("title"):
            updates["title"] = file_path.stem
        if not metadata.get("album"):
            updates["album"] = file_path.parent.name
        if not metadata.get("artist"):
            updates["artist"] = metadata.get("album_artist") or "Unknown Artist"
        return updates

    def _parse_fpcalc_output(self, output: str) -> Dict[str, Any]:
        text = str(output or "").strip()
        if not text:
            return {}
        if text.startswith("{"):
            try:
                payload = json.loads(text)
                return {
                    "fingerprint": payload.get("fingerprint"),
                    "duration": self._coerce_numeric(payload.get("duration")),
                }
            except Exception:
                return {}
        parsed: Dict[str, Any] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            normalized_key = key.strip().lower()
            parsed[normalized_key] = value.strip()
        fingerprint = parsed.get("fingerprint")
        duration = self._coerce_numeric(parsed.get("duration"))
        if not fingerprint:
            return {}
        return {"fingerprint": fingerprint, "duration": duration}

    def _coerce_numeric(self, value: Any) -> float | int | None:
        if value in (None, ""):
            return None
        try:
            numeric = float(value)
        except Exception:
            return None
        if numeric.is_integer():
            return int(numeric)
        return numeric

    def _parse_acoustid_error_reason(self, body: str) -> str:
        text = str(body or "").strip()
        if not text:
            return "lookup_failed"
        try:
            payload = json.loads(text)
        except Exception:
            lowered = text.lower()
            if "invalid api key" in lowered:
                return "invalid_client_key"
            return "lookup_failed"
        message = (
            str(payload.get("error", {}).get("message") or payload.get("message") or "")
            .strip()
            .lower()
        )
        if "invalid api key" in message:
            return "invalid_client_key"
        return "lookup_failed"

    def _debug(self, message: str) -> None:
        try:
            from src.utils.logger import debug as logger_debug

            logger_debug(f"[AudioFingerprint] {message}")
        except Exception:
            try:
                print(f"[DEBUG] [AudioFingerprint] {message}")
            except Exception:
                pass

    def _mask_secret(self, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            return "missing"
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"

    def _preview_value(self, value: Any, limit: int = 400) -> str:
        if isinstance(value, (dict, list, tuple)):
            text = json.dumps(value, ensure_ascii=True, default=str)
        else:
            text = str(value or "")
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= limit:
            return text
        return text[:limit] + "...(truncated)"

    def _debug_payload(self, label: str, payload: Any, limit: int = 600) -> None:
        self._debug(f"{label} | payload={self._preview_value(payload, limit)}")

    def _summarize_candidates(
        self, candidates: list[Dict[str, Any]], limit: int = 3
    ) -> str:
        parts: list[str] = []
        for candidate in candidates[:limit]:
            artist = (
                self.clean_text_for_query(str(candidate.get("artist") or "")) or "?"
            )
            title = self.clean_text_for_query(str(candidate.get("title") or "")) or "?"
            source = str(candidate.get("source") or "?")
            confidence = candidate.get("confidence", 0)
            parts.append(f"{artist} - {title} [{source}:{confidence}]")
        return " | ".join(parts) if parts else "none"

    def get_useragent(self) -> str:
        """Retorna el user-agent utilizado para MusicBrainz."""
        return self._resolve_useragent()

    def _resolve_fpcalc_path(self) -> str | None:
        exe_name = "fpcalc.exe" if os.name == "nt" else "fpcalc"
        candidates = []
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "bin" / exe_name)
        candidates.append(Path.cwd() / "bin" / exe_name)
        candidates.append(Path(__file__).resolve().parents[2] / "bin" / exe_name)
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return shutil.which(exe_name) or shutil.which("fpcalc")

    def _get_acoustid_api_key(self) -> str:
        try:
            from src.utils.app_config import AppConfig

            config_key = AppConfig().get_acoustid_api_key().strip()
            if config_key:
                return config_key
        except Exception:
            pass
        return os.environ.get("ACOUSTID_API_KEY", "").strip()

    def _get_discogs_token(self) -> str:
        try:
            from src.utils.app_config import AppConfig

            token = AppConfig().get_discogs_token().strip()
            if token:
                return token
        except Exception:
            pass
        return os.environ.get("DISCOGS_TOKEN", "").strip()

    def _get_discogs_enabled(self) -> bool:
        try:
            from src.utils.app_config import AppConfig

            return bool(AppConfig().get_discogs_enabled())
        except Exception:
            return False


audio_fingerprint_service = AudioFingerprintService()
