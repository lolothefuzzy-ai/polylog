"""Tiered Unicode library manager for INT-005 prepopulation roadmap.

Provides a light-weight implementation that supports Tier 0/1/2 caches,
lookup statistics, and graceful fallback when no embedded library bundle is
available yet. This scaffold will be extended once the Tier 0 dataset lands.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class UnicodeLibraryEntry:
    """Represents a single prepopulated topology entry."""

    char: str
    uuid: str
    semantic_id: str
    composition: str
    attachment_schemas: Iterable[str]
    symmetry_char: str
    scaler_table: MutableMapping[str, Any]
    cgal_boundary: MutableMapping[str, Any]
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class UnicodeLibraryManager:
    """Tiered cache for Unicode topology library.

    Tier 0: Embedded bundle (immutable, eagerly loaded when present)
    Tier 1: Working LRU cache (bounded by entry count and approximate size)
    Tier 2: Persistent cache (disk-backed, promoted from Tier 1)
    """

    _DEFAULT_TIER1_LIMIT = 5000
    _DEFAULT_TIER1_SIZE_MB = 100

    def __init__(
        self,
        *,
        preload_embedded: bool = True,
        tier0_path: Optional[Path] = None,
        max_tier1_entries: int = _DEFAULT_TIER1_LIMIT,
        max_tier1_size_mb: int = _DEFAULT_TIER1_SIZE_MB,
    ) -> None:
        self._tier0_path = tier0_path or Path("data/unicode_library_tier0.json")
        self.max_tier1_entries = max_tier1_entries
        self.max_tier1_size_mb = max_tier1_size_mb

        self.tier0_embedded: Dict[str, UnicodeLibraryEntry] = {}
        self.tier1_working: Dict[str, UnicodeLibraryEntry] = {}
        self.tier2_persistent: Dict[str, UnicodeLibraryEntry] = {}

        self.char_to_entry: Dict[str, UnicodeLibraryEntry] = {}
        self.uuid_to_char: Dict[str, str] = {}

        self.statistics: Dict[str, int] = {
            "tier0_hits": 0,
            "tier1_hits": 0,
            "tier2_hits": 0,
            "misses": 0,
            "total_lookups": 0,
        }

        if preload_embedded:
            self._load_tier0_embedded()

    # ------------------------------------------------------------------
    # Loading / persistence
    # ------------------------------------------------------------------
    def _load_tier0_embedded(self) -> None:
        """Load the Tier 0 bundle if present on disk.

        The method is tolerant of missing artifacts to keep dev loops smooth.
        """

        if not self._tier0_path.exists():
            LOGGER.debug("Tier 0 Unicode library not found at %s", self._tier0_path)
            return

        start = time.time()
        try:
            bundle = json.loads(self._tier0_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to load Tier 0 library %s: %s", self._tier0_path, exc)
            return

        entries = bundle.get("entries", [])
        loaded = 0
        for entry_data in entries:
            try:
                entry = UnicodeLibraryEntry(
                    char=str(entry_data["char"]),
                    uuid=str(entry_data["uuid"]),
                    semantic_id=str(entry_data.get("semantic_id", "")),
                    composition=str(entry_data.get("composition", "")),
                    attachment_schemas=tuple(entry_data.get("attachment_schemas", [])),
                    symmetry_char=str(entry_data.get("symmetry_char", "")),
                    scaler_table=dict(entry_data.get("scaler_table", {})),
                    cgal_boundary=dict(entry_data.get("cgal_boundary", {})),
                    metadata=dict(entry_data.get("metadata", {})),
                )
            except KeyError as exc:  # pragma: no cover - bundle hygiene
                LOGGER.debug("Skipping malformed Tier 0 entry: missing %s", exc)
                continue

            self._insert_into_tier0(entry)
            loaded += 1

        elapsed_ms = (time.time() - start) * 1000
        LOGGER.info("Loaded %d Tier 0 entries in %.1f ms", loaded, elapsed_ms)

    def _insert_into_tier0(self, entry: UnicodeLibraryEntry) -> None:
        self.tier0_embedded[entry.uuid] = entry
        self.char_to_entry[entry.char] = entry
        self.uuid_to_char[entry.uuid] = entry.char

    # ------------------------------------------------------------------
    # Lookup / caching APIs
    # ------------------------------------------------------------------
    def lookup(self, uuid: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Return the (char, scaler_table, boundary) tuple for a UUID if present."""

        self.statistics["total_lookups"] += 1

        if uuid in self.tier0_embedded:
            entry = self.tier0_embedded[uuid]
            self._touch_entry(entry)
            self.statistics["tier0_hits"] += 1
            return entry.char, entry.scaler_table, entry.cgal_boundary

        if uuid in self.tier1_working:
            entry = self.tier1_working[uuid]
            self._touch_entry(entry)
            self.statistics["tier1_hits"] += 1
            return entry.char, entry.scaler_table, entry.cgal_boundary

        if uuid in self.tier2_persistent:
            entry = self.tier2_persistent[uuid]
            self._touch_entry(entry)
            self.statistics["tier2_hits"] += 1
            self._promote_to_tier1(uuid, entry)
            return entry.char, entry.scaler_table, entry.cgal_boundary

        self.statistics["misses"] += 1
        return None, None, None

    def cache_entry(
        self,
        uuid: str,
        *,
        char: str,
        scaler_table: MutableMapping[str, Any],
        cgal_boundary: MutableMapping[str, Any],
        metadata: Optional[MutableMapping[str, Any]] = None,
        semantic_id: Optional[str] = None,
        composition: str = "",
        attachment_schemas: Optional[Iterable[str]] = None,
        symmetry_char: str = "",
    ) -> None:
        """Cache a newly discovered topology into Tier 1 (and index by char/uuid)."""

        entry = UnicodeLibraryEntry(
            char=char,
            uuid=uuid,
            semantic_id=semantic_id or metadata.get("semantic_id", f"user_{uuid[:8]}") if metadata else f"user_{uuid[:8]}",
            composition=composition,
            attachment_schemas=tuple(attachment_schemas or ()),
            symmetry_char=symmetry_char,
            scaler_table=dict(scaler_table),
            cgal_boundary=dict(cgal_boundary),
            metadata=dict(metadata or {}),
        )
        self._insert_into_tier1(entry)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _touch_entry(self, entry: UnicodeLibraryEntry) -> None:
        entry.access_count += 1
        entry.last_accessed = time.time()

    def _insert_into_tier1(self, entry: UnicodeLibraryEntry) -> None:
        self.tier1_working[entry.uuid] = entry
        self.char_to_entry[entry.char] = entry
        self.uuid_to_char[entry.uuid] = entry.char
        self._enforce_tier1_limits()

    def _promote_to_tier1(self, uuid: str, entry: UnicodeLibraryEntry) -> None:
        self.tier1_working[uuid] = entry
        self._enforce_tier1_limits()

    def _enforce_tier1_limits(self) -> None:
        """Evict least-recently-used entries when limits are exceeded."""

        if len(self.tier1_working) <= self.max_tier1_entries:
            return

        # Evict 10% oldest entries by last_accessed timestamp.
        eviction_count = max(1, len(self.tier1_working) // 10)
        sorted_entries = sorted(self.tier1_working.items(), key=lambda item: item[1].last_accessed)
        for uuid, entry in sorted_entries[:eviction_count]:
            self.tier1_working.pop(uuid, None)
            self.char_to_entry.pop(entry.char, None)
            # Keep uuid_to_char for Tier 2 awareness.

    # ------------------------------------------------------------------
    # Statistics / diagnostics
    # ------------------------------------------------------------------
    def get_statistics(self) -> Dict[str, Any]:
        total = self.statistics["total_lookups"]
        if total == 0:
            return {
                **self.statistics,
                "hit_rate_pct": 0.0,
                "tier0_hit_rate": 0.0,
                "tier1_hit_rate": 0.0,
                "tier2_hit_rate": 0.0,
                "miss_rate_pct": 0.0,
                "tier1_size": len(self.tier1_working),
                "tier2_size": len(self.tier2_persistent),
            }

        hit_total = self.statistics["tier0_hits"] + self.statistics["tier1_hits"] + self.statistics["tier2_hits"]
        return {
            **self.statistics,
            "hit_rate_pct": hit_total / total * 100,
            "tier0_hit_rate": self.statistics["tier0_hits"] / total * 100,
            "tier1_hit_rate": self.statistics["tier1_hits"] / total * 100,
            "tier2_hit_rate": self.statistics["tier2_hits"] / total * 100,
            "miss_rate_pct": self.statistics["misses"] / total * 100,
            "tier1_size": len(self.tier1_working),
            "tier2_size": len(self.tier2_persistent),
        }


_unicode_library_singleton: Optional[UnicodeLibraryManager] = None


def get_unicode_library(**kwargs: Any) -> UnicodeLibraryManager:
    """Return the process-wide Unicode library manager singleton."""

    global _unicode_library_singleton
    if _unicode_library_singleton is None:
        _unicode_library_singleton = UnicodeLibraryManager(**kwargs)
    return _unicode_library_singleton


__all__ = ["UnicodeLibraryEntry", "UnicodeLibraryManager", "get_unicode_library"]
