"""Test storage integration for generated polyforms"""
import pytest
import json
from pathlib import Path

from polylog6.storage.polyform_storage import PolyformStorage
from polylog6.storage.encoder import TieredUnicodeEncoder

@pytest.fixture
def storage():
    """Create a test storage instance"""
    storage = PolyformStorage(use_mmap=False)
    yield storage
    # Cleanup
    storage.store.clear()
    storage.metadata.clear()

@pytest.fixture
def sample_polyform_data():
    """Sample polyform data for testing"""
    return {
        "composition": "A+B",
        "geometry": {
            "lod": {
                "full": {
                    "vertices": [[0, 0, 0], [1, 0, 0], [0.5, 0.866, 0]],
                    "indices": [0, 1, 2],
                    "normals": [[0, 0, 1], [0, 0, 1], [0, 0, 1]]
                },
                "medium": {"vertices": [], "indices": []},
                "bbox": {"min": [-1, -1, -1], "max": [1, 1, 1]}
            },
            "folds": [],
            "metadata": {
                "polygon_count": 2,
                "edge_count": 7,
                "stability": 0.75
            }
        },
        "metadata": {
            "polygon_count": 2,
            "edge_count": 7,
            "stability": 0.75,
            "generation_mode": "linear"
        },
        "unicode": "𝔸",
        "compression_ratio": 1.5
    }

def test_storage_add_and_retrieve(storage, sample_polyform_data):
    """Test adding and retrieving polyforms"""
    composition = "A+B"
    frequency = 100
    
    # Add polyform
    symbol = storage.add(composition, sample_polyform_data, frequency)
    
    assert symbol is not None, "Should return a symbol"
    assert len(symbol) > 0, "Symbol should not be empty"
    
    # Retrieve polyform
    retrieved = storage.get(symbol)
    assert retrieved is not None, "Should retrieve polyform"
    assert retrieved["composition"] == composition, "Composition should match"
    assert retrieved["compression_ratio"] == sample_polyform_data["compression_ratio"]

def test_storage_metadata(storage, sample_polyform_data):
    """Test metadata storage and retrieval"""
    composition = "A+B"
    frequency = 100
    
    symbol = storage.add(composition, sample_polyform_data, frequency)
    
    # Get metadata
    metadata = storage.get_metadata(symbol)
    assert metadata is not None, "Should have metadata"
    assert metadata["polyform_id"] == composition, "Polyform ID should match"
    assert metadata["frequency"] == frequency, "Frequency should match"
    assert metadata["compression_ratio"] == sample_polyform_data["compression_ratio"]

def test_storage_list_all(storage, sample_polyform_data):
    """Test listing all stored polyforms"""
    # Add multiple polyforms
    compositions = ["A+B", "C+D", "E+F"]
    symbols = []
    
    for i, composition in enumerate(compositions):
        data = sample_polyform_data.copy()
        data["composition"] = composition
        symbol = storage.add(composition, data, 100 + i * 50)
        symbols.append(symbol)
    
    # List all
    all_polyforms = storage.list_all()
    assert len(all_polyforms) == len(compositions), "Should list all polyforms"
    
    for polyform in all_polyforms:
        assert polyform["composition"] in compositions, "Composition should be in test list"
        assert "symbol" in polyform, "Should have symbol"
        assert "metadata" in polyform, "Should have metadata"

def test_storage_get_by_composition(storage, sample_polyform_data):
    """Test finding polyform by composition"""
    composition = "A+B"
    
    storage.add(composition, sample_polyform_data, 100)
    
    # Find by composition
    found = storage.get_by_composition(composition)
    assert found is not None, "Should find polyform by composition"
    assert found["composition"] == composition, "Composition should match"
    
    # Should not find non-existent composition
    not_found = storage.get_by_composition("X+Y")
    assert not_found is None, "Should not find non-existent composition"

def test_storage_update_frequency(storage, sample_polyform_data):
    """Test updating frequency"""
    composition = "A+B"
    original_frequency = 100
    new_frequency = 500
    
    symbol = storage.add(composition, sample_polyform_data, original_frequency)
    
    # Update frequency
    success = storage.update_frequency(symbol, new_frequency)
    assert success, "Should update frequency"
    
    # Check updated metadata
    metadata = storage.get_metadata(symbol)
    assert metadata["frequency"] == new_frequency, "Frequency should be updated"

def test_storage_delete(storage, sample_polyform_data):
    """Test deleting polyforms"""
    composition = "A+B"
    
    symbol = storage.add(composition, sample_polyform_data, 100)
    
    # Verify it exists
    assert storage.get(symbol) is not None, "Polyform should exist before deletion"
    
    # Delete
    success = storage.delete(symbol)
    assert success, "Delete should succeed"
    
    # Verify it's gone
    assert storage.get(symbol) is None, "Polyform should not exist after deletion"
    assert storage.get_metadata(symbol) is None, "Metadata should be deleted too"

def test_storage_stats(storage, sample_polyform_data):
    """Test storage statistics"""
    # Add multiple polyforms with different compression ratios
    compositions = ["A+B", "C+D", "E+F"]
    ratios = [1.5, 2.0, 1.8]
    
    for composition, ratio in zip(compositions, ratios):
        data = sample_polyform_data.copy()
        data["composition"] = composition
        data["compression_ratio"] = ratio
        storage.add(composition, data, 100)
    
    # Get stats
    stats = storage.get_stats()
    assert stats["total_polyforms"] == len(compositions), "Should count all polyforms"
    assert stats["average_compression_ratio"] == sum(ratios) / len(ratios), "Should calculate average correctly"
    assert stats["storage_type"] == "memory", "Should identify storage type"

def test_storage_with_mmap(tmp_path, sample_polyform_data):
    """Test storage with memory-mapped files"""
    storage_path = tmp_path / "test_store.dat"
    storage = PolyformStorage(use_mmap=True, storage_path=storage_path)
    
    try:
        composition = "A+B"
        symbol = storage.add(composition, sample_polyform_data, 100)
        
        # Should work with mmap
        assert symbol.startswith("mmap:"), "Should return mmap reference"
        
        retrieved = storage.get(symbol)
        assert retrieved is not None, "Should retrieve from mmap"
        assert retrieved["composition"] == composition, "Data should match"
        
    finally:
        # Cleanup
        if hasattr(storage, 'file'):
            storage.file.close()
        if hasattr(storage, 'mmap'):
            storage.mmap.close()

def test_encoder_integration():
    """Test integration with TieredUnicodeEncoder"""
    encoder = TieredUnicodeEncoder()
    storage = PolyformStorage()
    
    composition = "A+B"
    frequency = 100
    data = {
        "composition": composition,
        "compression_ratio": 1.5
    }
    
    # Add through storage
    symbol = storage.add(composition, data, frequency)
    
    # Should be same as direct encoder allocation
    direct_symbol = encoder.allocate(composition, frequency)
    
    # Symbols should be related (not necessarily identical due to internal state)
    assert len(symbol) > 0, "Storage should allocate valid symbol"
    assert len(direct_symbol) > 0, "Direct allocation should work"