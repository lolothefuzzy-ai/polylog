"""
Camera animation helper for smooth transitions.

Provides smooth camera movement and transitions.
"""

from typing import Tuple, Optional


class CameraAnimator:
    """Handles smooth camera animations and transitions."""
    
    def __init__(self):
        """Initialize animator."""
        self.is_animating = False
        self.start_distance = 5.0
        self.end_distance = 5.0
        self.start_angle_x = 45.0
        self.end_angle_x = 45.0
        self.start_angle_y = 45.0
        self.end_angle_y = 45.0
        self.start_pan_x = 0.0
        self.end_pan_x = 0.0
        self.start_pan_y = 0.0
        self.end_pan_y = 0.0
        
        self.elapsed = 0.0
        self.duration = 1.0
    
    def animate_to(
        self,
        distance: float,
        angle_x: float,
        angle_y: float,
        pan_x: float = 0.0,
        pan_y: float = 0.0,
        duration: float = 1.0
    ):
        """Start animation to target camera state."""
        self.start_distance = self.end_distance
        self.start_angle_x = self.end_angle_x
        self.start_angle_y = self.end_angle_y
        self.start_pan_x = self.end_pan_x
        self.start_pan_y = self.end_pan_y
        
        self.end_distance = distance
        self.end_angle_x = angle_x
        self.end_angle_y = angle_y
        self.end_pan_x = pan_x
        self.end_pan_y = pan_y
        
        self.duration = max(0.01, duration)
        self.elapsed = 0.0
        self.is_animating = True
    
    def update(self, delta_time: float):
        """Update animation with time delta."""
        if not self.is_animating:
            return
        
        self.elapsed += delta_time
        
        if self.elapsed >= self.duration:
            self.is_animating = False
            self.elapsed = self.duration
            return
        
        # Clamp progress to [0, 1]
        progress = min(1.0, self.elapsed / self.duration)
        
        # Smooth easing (ease-in-out)
        t = progress
        if t < 0.5:
            t = 2 * t * t
        else:
            t = 1 - (-2 * t + 2) ** 2 / 2
        
        # Update internal values for retrieval
        self.current_distance = self._lerp(self.start_distance, self.end_distance, t)
        self.current_angle_x = self._lerp(self.start_angle_x, self.end_angle_x, t)
        self.current_angle_y = self._lerp(self.start_angle_y, self.end_angle_y, t)
        self.current_pan_x = self._lerp(self.start_pan_x, self.end_pan_x, t)
        self.current_pan_y = self._lerp(self.start_pan_y, self.end_pan_y, t)
    
    @staticmethod
    def _lerp(start: float, end: float, t: float) -> float:
        """Linear interpolation."""
        return start + (end - start) * t
    
    def get_state(self) -> Tuple[float, float, float, float, float]:
        """Get current camera state."""
        if self.is_animating:
            return (
                self.current_distance,
                self.current_angle_x,
                self.current_angle_y,
                self.current_pan_x,
                self.current_pan_y
            )
        else:
            return (
                self.end_distance,
                self.end_angle_x,
                self.end_angle_y,
                self.end_pan_x,
                self.end_pan_y
            )
