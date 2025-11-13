"""
Persistent storage for learned symmetries and patterns.

This database learns:
- Rotation symmetries
- Reflection symmetries
- Spatial layout patterns
- Fold angle preferences
- Template usage statistics
"""
import json
import os
import time
from typing import Dict, List, Optional, Tuple

import numpy as np


class SymmetryDatabase:
    """
    Persistent storage for learned symmetries and patterns.
    
    Learns:
    - Rotation symmetries
    - Reflection symmetries
    - Spatial layout patterns
    - Fold angle preferences
    - Template usage statistics
    """
    
    def __init__(self, db_path='data/symmetries.json'):
        self.db_path = db_path
        self.data = self._load_db()
        
        # Pattern collections
        self.layout_patterns = self.data.get('layouts', [])
        self.fold_preferences = self.data.get('folds', {})
        self.template_usage = self.data.get('templates', {})
        self.learned_patterns = self.data.get('patterns', {})
    
    def get_likely_symmetry(self, sides: int) -> Optional[Dict]:
        """Get most likely symmetry for polygon type."""
        # Check if this polygon type has learned symmetry
        key = f"sides_{sides}"
        
        if key in self.data.get('symmetries', {}):
            return self.data['symmetries'][key]
        
        # Default symmetries based on polygon type
        if sides % 2 == 0:
            # Even-sided: likely has reflection symmetry
            return {'reflection_axis': 'x'}
        
        return None
    
    def add_layout_pattern(self, pattern: Dict):
        """Store a discovered layout pattern."""
        # Avoid duplicates
        if not self._is_duplicate_pattern(pattern):
            self.layout_patterns.append({
                'pattern': pattern,
                'discovered': time.time(),
                'usage_count': 1
            })
            self._save_db()
    
    def query_similar_ranges(self, min_sides: int, max_sides: int) -> List[Dict]:
        """Find layout patterns for similar ranges."""
        results = []
        
        for entry in self.layout_patterns:
            pattern = entry['pattern']
            # Check if pattern matches range
            # (Implementation depends on how patterns are stored)
            results.append(pattern)
        
        # Sort by usage count
        results.sort(key=lambda p: self._get_usage_count_for_pattern(p), reverse=True)
        return results[:5]
    
    def _get_usage_count_for_pattern(self, pattern: Dict) -> int:
        """Helper to get usage count for a pattern."""
        # Find the corresponding entry in layout_patterns
        for entry in self.layout_patterns:
            if entry['pattern'] == pattern:
                return entry.get('usage_count', 0)
        return 0
    
    def add_fold_preference(self, poly_types: Tuple, angle: float, stability: float):
        """Record preferred fold angle for poly combination."""
        key = str(poly_types)
        
        if key not in self.fold_preferences:
            self.fold_preferences[key] = []
        
        self.fold_preferences[key].append({
            'angle': angle,
            'stability': stability,
            'timestamp': time.time()
        })
        
        # Keep only recent preferences (last 100)
        self.fold_preferences[key] = self.fold_preferences[key][-100:]
        
        self._save_db()
    
    def get_preferred_fold_angle(self, poly_types: Tuple) -> Optional[float]:
        """Get most common fold angle for poly combination."""
        key = str(poly_types)
        
        if key not in self.fold_preferences:
            return None
        
        # Weight by stability and recency
        prefs = self.fold_preferences[key]
        if not prefs:
            return None
        
        # Weighted average
        angles = np.array([p['angle'] for p in prefs])
        weights = np.array([p['stability'] for p in prefs])
        
        return float(np.average(angles, weights=weights))
    
    def increment_template_usage(self, template_name: str):
        """Track template usage frequency."""
        if template_name not in self.template_usage:
            self.template_usage[template_name] = 0
        
        self.template_usage[template_name] += 1
        self._save_db()
    
    def get_popular_templates(self, top_n=5) -> List[str]:
        """Get most frequently used templates."""
        sorted_templates = sorted(
            self.template_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [name for name, count in sorted_templates[:top_n]]
    
    def add_learned_pattern(self, pattern_id: str, pattern_data: Dict):
        """Store a newly learned assembly pattern."""
        self.learned_patterns[pattern_id] = {
            'data': pattern_data,
            'created': time.time(),
            'usage_count': 0
        }
        self._save_db()
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Retrieve learned pattern."""
        entry = self.learned_patterns.get(pattern_id)
        if entry:
            entry['usage_count'] += 1
            self._save_db()
            return entry['data']
        return None
    
    def _is_duplicate_pattern(self, pattern: Dict) -> bool:
        """Check if pattern already exists."""
        # Simple comparison (could be more sophisticated)
        for entry in self.layout_patterns:
            if entry['pattern']['type'] == pattern['type']:
                if entry['pattern'].get('coherence', 0) > 0.9:
                    return True
        return False
    
    def _load_db(self) -> Dict:
        """Load database from disk."""
        if not os.path.exists(self.db_path):
            return {}
        
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_db(self):
        """Save database to disk."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.data['layouts'] = self.layout_patterns
        self.data['folds'] = self.fold_preferences
        self.data['templates'] = self.template_usage
        self.data['patterns'] = self.learned_patterns
        
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=2)
