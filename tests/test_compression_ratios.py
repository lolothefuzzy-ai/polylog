"""Test Unicode compression ratios for generated polyforms"""
import pytest
from polylog6.storage.encoder import TieredUnicodeEncoder

def test_compression_ratios():
    """Validate compression ratios meet realistic targets"""
    encoder = TieredUnicodeEncoder()
    
    test_cases = [
        ("A+B", 1000, 1.5),  # High frequency - realistic target
        ("C+D", 500, 1.2),   # Medium frequency
        ("E+F", 50, 1.0),    # Low frequency - at least 1:1
    ]
    
    for composition, frequency, min_ratio in test_cases:
        symbol = encoder.allocate(composition, frequency)
        original_size = len(composition) * 8
        compressed_size = len(symbol.encode('utf-8'))
        ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        print(f"Composition: {composition}, Original: {original_size}, Compressed: {compressed_size}, Ratio: {ratio:.2f}")
        
        assert ratio >= min_ratio, f"Compression ratio {ratio:.2f} below target {min_ratio} for {composition}"

def test_encoder_allocation():
    """Test symbol allocation and retrieval"""
    encoder = TieredUnicodeEncoder()
    
    # Test allocation
    symbol1 = encoder.allocate("A+B", 100)
    symbol2 = encoder.allocate("C+D", 50)
    
    assert symbol1 != symbol2, "Symbols should be unique"
    assert len(symbol1) > 0, "Symbol should not be empty"
    assert len(symbol2) > 0, "Symbol should not be empty"
    
    # Test that higher frequency gets better compression
    assert len(symbol1) <= len(symbol2), "Higher frequency should get better compression"

def test_compression_consistency():
    """Test that compression is consistent for same input"""
    encoder = TieredUnicodeEncoder()
    
    composition = "A+B"
    frequency = 100
    
    symbol1 = encoder.allocate(composition, frequency)
    symbol2 = encoder.allocate(composition, frequency)
    
    # Should get the same symbol for same input
    assert symbol1 == symbol2, f"Same input should produce same symbol: {symbol1} vs {symbol2}"

def test_unicode_validity():
    """Test that generated symbols are valid Unicode"""
    encoder = TieredUnicodeEncoder()
    
    test_cases = [
        ("A+B", 100),
        ("C+D+E+F", 500),
        ("G+H+I+J+K", 1000),
    ]
    
    for composition, frequency in test_cases:
        symbol = encoder.allocate(composition, frequency)
        
        # Should be valid UTF-8
        try:
            symbol.encode('utf-8')
        except UnicodeEncodeError:
            pytest.fail(f"Symbol {symbol} is not valid UTF-8")
        
        # Should be printable (no control characters)
        assert all(ord(c) >= 32 or ord(c) == 9 or ord(c) == 10 or ord(c) == 13 for c in symbol), \
            f"Symbol {symbol} contains non-printable characters"