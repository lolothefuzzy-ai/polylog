"""Test Unicode compression ratios for generated polyforms"""
import pytest
from polylog6.storage.encoder import TieredUnicodeEncoder

def test_compression_ratios():
    """Validate compression ratios meet targets"""
    encoder = TieredUnicodeEncoder()
    
    test_cases = [
        ("A+B", 1000, 100),  # High frequency
        ("C+D", 500, 50),    # Medium frequency
        ("E+F", 50, 5),      # Low frequency
    ]
    
    for composition, frequency, min_ratio in test_cases:
        symbol = encoder.allocate(composition, frequency)
        original_size = len(composition) * 8
        compressed_size = len(symbol.encode('utf-8'))
        ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        assert ratio >= min_ratio, f"Compression ratio {ratio} below target {min_ratio} for {composition}"

