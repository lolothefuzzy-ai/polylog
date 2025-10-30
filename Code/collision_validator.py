"""
Collision Validation Module

Integrates BVH collision detection into the assembly validation pipeline.
Provides utilities to detect self-intersections and inter-mesh collisions.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import logging
from collections import OrderedDict

from bvh3d import TriangleCollisionDetector
from polygon_utils import get_polyform_mesh

logger = logging.getLogger(__name__)


class CollisionValidator:
    """
    Validates assembly for collision/intersection issues.
    
    Uses BVH-accelerated triangle collision detection to catch:
    - Self-intersecting polyforms
    - Overlapping polyforms
    - Invalid fold states
    """
    
    def __init__(self, epsilon: float = 1e-6, max_cache_size: int = 50):
        """
        Initialize collision validator.
        
        Args:
            epsilon: Distance threshold for collision detection
            max_cache_size: Maximum number of detectors to cache (LRU eviction)
        """
        self.epsilon = epsilon
        
        # PHASE 1 STABILIZATION: Adaptive cache sizing based on available memory
        # Prevents OOM at high n by scaling cache to available resources
        try:
            import psutil
            available_mb = psutil.virtual_memory().available / 1024 / 1024
            # Use 5% of available memory for detectors (conservative)
            # Assume ~2MB per BVH detector
            detector_size_mb = 2.0
            adaptive_size = max(50, int(available_mb * 0.05 / detector_size_mb))
            self.max_cache_size = adaptive_size
            logger.info(f"Adaptive collision cache: {adaptive_size} detectors (~{adaptive_size * detector_size_mb:.0f}MB)")
        except Exception as e:
            # Fallback to parameter if psutil unavailable
            self.max_cache_size = max_cache_size
            logger.debug(f"Could not calculate adaptive cache size: {e}, using default {max_cache_size}")
        
        # Use OrderedDict for LRU cache - tracks access order
        self.detectors_cache: OrderedDict[str, TriangleCollisionDetector] = OrderedDict()
    
    def clear_cache(self):
        """Clear cached collision detectors."""
        self.detectors_cache.clear()
    
    def get_detector(self, polyform: Dict[str, Any]) -> Optional[TriangleCollisionDetector]:
        """
        Get or create collision detector for a polyform.
        Uses LRU cache with bounded size to prevent memory growth.
        
        Args:
            polyform: Polyform dictionary
        
        Returns:
            TriangleCollisionDetector or None if no 3D mesh
        """
        poly_id = polyform.get('id')
        if not poly_id:
            return None
        
        # Check cache - move to end if found (mark as recently used)
        if poly_id in self.detectors_cache:
            # Move to end to mark as recently used
            self.detectors_cache.move_to_end(poly_id)
            return self.detectors_cache[poly_id]
        
        # Get mesh
        mesh = get_polyform_mesh(polyform)
        if mesh is None:
            return None
        
        # Create detector
        detector = TriangleCollisionDetector(mesh)
        detector.build_bvh()
        
        # Add to cache
        self.detectors_cache[poly_id] = detector
        
        # Evict oldest entry if cache exceeds max size
        if len(self.detectors_cache) > self.max_cache_size:
            # Remove first (oldest) item
            oldest_id, _ = self.detectors_cache.popitem(last=False)
            logger.debug(f"LRU cache eviction: removed detector for {oldest_id}")
        
        return detector
    
    def check_self_intersection(self, polyform: Dict[str, Any]) -> bool:
        """
        Check if a polyform self-intersects.
        
        Args:
            polyform: Polyform dictionary
        
        Returns:
            True if self-intersection detected
        """
        detector = self.get_detector(polyform)
        if detector is None:
            return False  # No 3D mesh, assume valid
        
        return detector.check_self_intersection(self.epsilon)
    
    def check_pair_collision(self, poly1: Dict[str, Any], poly2: Dict[str, Any]) -> bool:
        """
        Check if two polyforms collide.
        
        Args:
            poly1: First polyform
            poly2: Second polyform
        
        Returns:
            True if collision detected
        """
        detector1 = self.get_detector(poly1)
        detector2 = self.get_detector(poly2)
        
        if detector1 is None or detector2 is None:
            return False  # Can't check, assume valid
        
        return detector1.check_collision(detector2, self.epsilon)
    
    def check_assembly_collisions(self, assembly) -> List[Dict[str, Any]]:
        """
        Comprehensive collision check for entire assembly.
        
        Args:
            assembly: Assembly object with get_all_polyforms()
        
        Returns:
            List of collision reports: {
                'type': 'self_intersection' | 'pair_collision',
                'poly1_id': str,
                'poly2_id': Optional[str],
                'severity': 'warning' | 'error'
            }
        """
        reports = []
        polyforms = assembly.get_all_polyforms()
        
        # Check self-intersections
        for poly in polyforms:
            poly_id = poly.get('id')
            if not poly_id:
                continue
            
            if self.check_self_intersection(poly):
                reports.append({
                    'type': 'self_intersection',
                    'poly1_id': poly_id,
                    'poly2_id': None,
                    'severity': 'error',
                    'message': f'Polyform {poly_id} has self-intersecting geometry'
                })
                logger.warning(f"Self-intersection detected in {poly_id}")
        
        # Check pairwise collisions
        for i, poly1 in enumerate(polyforms):
            poly1_id = poly1.get('id')
            if not poly1_id:
                continue
            
            for poly2 in polyforms[i+1:]:
                poly2_id = poly2.get('id')
                if not poly2_id:
                    continue
                
                if self.check_pair_collision(poly1, poly2):
                    reports.append({
                        'type': 'pair_collision',
                        'poly1_id': poly1_id,
                        'poly2_id': poly2_id,
                        'severity': 'warning',
                        'message': f'Collision between {poly1_id} and {poly2_id}'
                    })
                    logger.warning(f"Collision detected between {poly1_id} and {poly2_id}")
        
        return reports
    
    def validate_fold_operation(self, assembly, poly_id: str, 
                               target_angle: float) -> Tuple[bool, str]:
        """
        Validate if a fold operation would cause collisions.
        
        Args:
            assembly: Assembly object
            poly_id: Polyform ID to fold
            target_angle: Target fold angle in radians
        
        Returns:
            (is_valid, message)
        """
        # Get polyform
        polyform = assembly.get_polyform(poly_id)
        if polyform is None:
            return False, f"Polyform {poly_id} not found"
        
        # Check self-intersection after fold
        if self.check_self_intersection(polyform):
            return False, f"Fold operation would cause self-intersection in {poly_id}"
        
        # Check collisions with other polyforms
        other_polys = [p for p in assembly.get_all_polyforms() 
                       if p.get('id') != poly_id]
        
        for other in other_polys:
            if self.check_pair_collision(polyform, other):
                other_id = other.get('id')
                return False, f"Fold operation would collide {poly_id} with {other_id}"
        
        return True, "Fold operation is valid"
    
    def get_collision_report(self, assembly) -> str:
        """
        Generate human-readable collision report.
        
        Args:
            assembly: Assembly object
        
        Returns:
            Formatted report string
        """
        reports = self.check_assembly_collisions(assembly)
        
        if not reports:
            return "✓ Assembly is collision-free"
        
        lines = ["⚠ Collision Report:"]
        
        self_intersections = [r for r in reports if r['type'] == 'self_intersection']
        if self_intersections:
            lines.append(f"\nSelf-Intersections ({len(self_intersections)}):")
            for r in self_intersections:
                lines.append(f"  - {r['poly1_id']}: {r['message']}")
        
        pair_collisions = [r for r in reports if r['type'] == 'pair_collision']
        if pair_collisions:
            lines.append(f"\nPairwise Collisions ({len(pair_collisions)}):")
            for r in pair_collisions:
                lines.append(f"  - {r['poly1_id']} ↔ {r['poly2_id']}: {r['message']}")
        
        return "\n".join(lines)


# Global validator instance
_validator: Optional[CollisionValidator] = None


def get_collision_validator() -> CollisionValidator:
    """Get or create global collision validator."""
    global _validator
    if _validator is None:
        _validator = CollisionValidator()
    return _validator


def check_assembly_for_collisions(assembly) -> bool:
    """
    Quick check if assembly has any collisions.
    
    Args:
        assembly: Assembly object
    
    Returns:
        True if any collisions found
    """
    validator = get_collision_validator()
    reports = validator.check_assembly_collisions(assembly)
    return len(reports) > 0


def validate_fold_safe(assembly, poly_id: str, target_angle: float) -> bool:
    """
    Check if fold operation is safe (no collisions).
    
    Args:
        assembly: Assembly object
        poly_id: Polyform to fold
        target_angle: Target fold angle
    
    Returns:
        True if operation is safe
    """
    validator = get_collision_validator()
    is_valid, _ = validator.validate_fold_operation(assembly, poly_id, target_angle)
    return is_valid
