"""
Persistent storage for learned scale factors and bond probabilities.

This database learns optimal sizes for polygons based on usage patterns
and tracks success probabilities for different bond types.
"""
import os
import json
from typing import Dict, Tuple


class ScalerDatabase:
    """
    Persistent storage for learned scale factors.
    
    Learns optimal sizes for polygons based on usage patterns.
    """
    
    def __init__(self, db_path='data/scalers.json'):
        self.db_path = db_path
        self.scalers = self._load_db()
        
        # Default scalers (start with unity)
        self.defaults = {sides: 1.0 for sides in range(3, 13)}
        
        # Bond success probabilities
        self.bond_probs = {}
    
    def get_optimal_scaler(self, sides: int) -> float:
        """Get learned optimal scale for polygon type."""
        return self.scalers.get(sides, self.defaults.get(sides, 1.0))
    
    def set_optimal_scaler(self, sides: int, scaler: float):
        """Update learned scale factor."""
        self.scalers[sides] = scaler
        self._save_db()
    
    def update_bond_probability(self, bond_key: Tuple, success: bool):
        """Update success probability for bond type."""
        key_str = str(bond_key)
        if key_str not in self.bond_probs:
            self.bond_probs[key_str] = {'successes': 0, 'attempts': 0}
        
        self.bond_probs[key_str]['attempts'] += 1
        if success:
            self.bond_probs[key_str]['successes'] += 1
        
        self._save_db()
    
    def get_bond_probability(self, bond_key: Tuple) -> float:
        """Get success probability for bond type."""
        key_str = str(bond_key)
        if key_str not in self.bond_probs:
            return 0.5  # Unknown, assume 50%
        
        data = self.bond_probs[key_str]
        return data['successes'] / max(1, data['attempts'])
    
    def _load_db(self) -> Dict:
        """Load database from disk."""
        if not os.path.exists(self.db_path):
            return {}
        
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.get('scalers', {}).items()}
        except Exception:
            return {}
    
    def _save_db(self):
        """Save database to disk."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        data = {
            'scalers': {str(k): v for k, v in self.scalers.items()},
            'bond_probs': {str(k): v for k, v in self.bond_probs.items()}
        }
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
