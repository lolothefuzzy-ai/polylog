"""
Placement and exploration algorithms for autonomous polygon arrangement.

Implements intelligent placement strategies for polyforms.
"""

import random
import math
from typing import List, Dict, Any, Tuple, Optional


class PlacementAlgorithm:
    """Handles autonomous placement and exploration of polygons."""
    
    def __init__(self, grid_size: float = 1.0, margin: float = 0.5):
        """Initialize placement algorithm."""
        self.grid_size = grid_size
        self.margin = margin
        self.occupied_positions = []
    
    def find_placement(self, polygon: Dict[str, Any], strategy: str = 'nearest') -> Tuple[float, float]:
        """
        Find a placement position for a polygon.
        
        Strategies:
        - nearest: Place nearest to existing polygons
        - random: Random valid position
        - grid: Grid-based placement
        - spiral: Spiral outward from center
        """
        if strategy == 'nearest':
            return self._place_nearest(polygon)
        elif strategy == 'random':
            return self._place_random(polygon)
        elif strategy == 'grid':
            return self._place_grid(polygon)
        elif strategy == 'spiral':
            return self._place_spiral(polygon)
        else:
            return (0.0, 0.0)
    
    def _place_nearest(self, polygon: Dict[str, Any]) -> Tuple[float, float]:
        """Place polygon nearest to existing polygons."""
        if not self.occupied_positions:
            return (0.0, 0.0)
        
        # Find nearest occupied position
        nearest_pos = min(
            self.occupied_positions,
            key=lambda p: (p[0] ** 2 + p[1] ** 2) ** 0.5
        )
        
        # Place near nearest position
        angle = random.uniform(0, 2 * math.pi)
        distance = 2.0 + random.uniform(-0.5, 0.5)
        
        x = nearest_pos[0] + distance * math.cos(angle)
        y = nearest_pos[1] + distance * math.sin(angle)
        
        return (x, y)
    
    def _place_random(self, polygon: Dict[str, Any]) -> Tuple[float, float]:
        """Place polygon at random valid position."""
        max_attempts = 10
        
        for _ in range(max_attempts):
            x = random.uniform(-5.0, 5.0)
            y = random.uniform(-5.0, 5.0)
            
            if self._is_valid_position(x, y, polygon):
                return (x, y)
        
        # Fallback to random even if invalid
        return (random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0))
    
    def _place_grid(self, polygon: Dict[str, Any]) -> Tuple[float, float]:
        """Place polygon on a grid."""
        grid_count = len(self.occupied_positions)
        cols = max(1, int(math.ceil(math.sqrt(grid_count + 1))))
        
        row = grid_count // cols
        col = grid_count % cols
        
        x = (col - cols / 2) * self.grid_size * 2
        y = (row - cols / 2) * self.grid_size * 2
        
        return (x, y)
    
    def _place_spiral(self, polygon: Dict[str, Any]) -> Tuple[float, float]:
        """Place polygon in spiral pattern."""
        count = len(self.occupied_positions)
        angle = count * 0.5  # Golden angle approximation
        radius = 1.0 + count * 0.3
        
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        return (x, y)
    
    def _is_valid_position(self, x: float, y: float, polygon: Dict[str, Any]) -> bool:
        """Check if position is valid (no collision)."""
        dist_to_occupied = min(
            (
                ((x - pos[0]) ** 2 + (y - pos[1]) ** 2) ** 0.5
                for pos in self.occupied_positions
            ),
            default=float('inf')
        )
        
        # Need minimum distance
        return dist_to_occupied > (self.grid_size + self.margin)
    
    def register_position(self, x: float, y: float) -> None:
        """Register a polygon as placed at position."""
        self.occupied_positions.append((x, y))
    
    def clear_positions(self) -> None:
        """Clear all registered positions."""
        self.occupied_positions = []
    
    def get_success_rate(self) -> float:
        """Calculate placement success rate (0-1)."""
        if not hasattr(self, 'total_attempts'):
            self.total_attempts = 0
            self.successful_placements = 0
        
        if self.total_attempts == 0:
            return 1.0
        
        return self.successful_placements / self.total_attempts


class ExploreMode:
    """Autonomous exploration and arrangement of polygons."""
    
    def __init__(self, max_iterations: int = 50):
        """Initialize explore mode."""
        self.max_iterations = max_iterations
        self.iteration = 0
        self.is_exploring = False
        self.placement_algo = PlacementAlgorithm()
    
    def start_exploration(self) -> None:
        """Start exploration mode."""
        self.is_exploring = True
        self.iteration = 0
        self.placement_algo.clear_positions()
    
    def stop_exploration(self) -> None:
        """Stop exploration mode."""
        self.is_exploring = False
    
    def explore_step(self, polygons: List[Dict[str, Any]]) -> bool:
        """
        Execute one step of exploration.
        
        Returns True if exploration continues, False if complete.
        """
        if not self.is_exploring:
            return False
        
        if self.iteration >= self.max_iterations:
            self.is_exploring = False
            return False
        
        # Rearrange a random polygon
        if polygons:
            poly = random.choice(polygons)
            x, y = self.placement_algo.find_placement(poly)
            poly['position'] = [x, y, 0]
        
        self.iteration += 1
        return self.iteration < self.max_iterations
    
    def get_progress(self) -> float:
        """Get exploration progress (0-1)."""
        if self.max_iterations == 0:
            return 1.0
        return min(1.0, self.iteration / self.max_iterations)
