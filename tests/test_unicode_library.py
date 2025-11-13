from __future__ import annotations

from polylog6.storage.unicode_library import UnicodeLibraryManager


def test_lookup_miss_without_tier0_bundle() -> None:
    manager = UnicodeLibraryManager(preload_embedded=False)

    char, scaler, boundary = manager.lookup("missing-uuid")

    assert char is None
    assert scaler is None
    assert boundary is None
    stats = manager.get_statistics()
    assert stats["misses"] == 1
    assert stats["hit_rate_pct"] == 0.0


def test_cache_entry_roundtrip() -> None:
    manager = UnicodeLibraryManager(preload_embedded=False)

    manager.cache_entry(
        "uuid-1234",
        char="⬚₁",
        scaler_table={"fold_angles": [70.5]},
        cgal_boundary={"aabb": (0, 0, 1, 1)},
        metadata={"semantic_id": "test_entry"},
        composition="A₃B₂",
        attachment_schemas=["∠₃◆₂◯₁"],
        symmetry_char="χ₂",
    )

    char, scaler, boundary = manager.lookup("uuid-1234")

    assert char == "⬚₁"
    assert scaler == {"fold_angles": [70.5]}
    assert boundary == {"aabb": (0, 0, 1, 1)}

    entry = manager.char_to_entry["⬚₁"]
    assert entry.semantic_id == "test_entry"
    assert entry.access_count >= 1
    stats = manager.get_statistics()
    assert stats["tier1_hits"] == 1
    assert stats["hit_rate_pct"] == 50.0
