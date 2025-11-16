"""
Tracks attachment schema coverage.
"""
from typing import Dict, Any


class SchemaIndexMonitor:
    """Monitors attachment schema coverage."""
    
    def __init__(self):
        self.coverage = {
            "primitive_pairs": 0,
            "platonic_to_primitive": 0,
            "high_frequency_pairs": 0,
            "total_viable_pairs": 0,
            "covered_pairs": 0
        }
    
    def update(
        self,
        primitive_pairs: int,
        platonic_to_primitive: int,
        high_frequency_pairs: int,
        total_viable_pairs: int
    ):
        """Update coverage metrics."""
        self.coverage["primitive_pairs"] = primitive_pairs
        self.coverage["platonic_to_primitive"] = platonic_to_primitive
        self.coverage["high_frequency_pairs"] = high_frequency_pairs
        self.coverage["total_viable_pairs"] = total_viable_pairs
        self.coverage["covered_pairs"] = primitive_pairs + platonic_to_primitive + high_frequency_pairs
    
    def as_dict(self) -> Dict[str, Any]:
        """Return coverage metrics as dictionary."""
        return self.coverage
