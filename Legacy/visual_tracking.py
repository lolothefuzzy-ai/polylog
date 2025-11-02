"""
Visual Tracking System - Motion trails, glow effects, and camera following for polyforms.
Enhances visual feedback during animations and interactions.
"""
import time
from collections import deque
from typing import Dict, Optional, Tuple

import numpy as np
import pyqtgraph.opengl as gl


class MotionTrail:
    """Represents a motion trail for tracking polyform movement."""
    
    def __init__(self, max_points: int = 50, fade_time: float = 2.0):
        """
        Initialize motion trail.
        
        Args:
            max_points: Maximum number of trail points to retain
            fade_time: Time in seconds for trail to fade out
        """
        self.max_points = max_points
        self.fade_time = fade_time
        self.points: deque = deque(maxlen=max_points)
        self.timestamps: deque = deque(maxlen=max_points)
        self.gl_item: Optional[gl.GLLinePlotItem] = None
    
    def add_point(self, position: np.ndarray, timestamp: Optional[float] = None):
        """
        Add a point to the trail.
        
        Args:
            position: 3D position (numpy array)
            timestamp: Time of the point (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        self.points.append(np.array(position, dtype=np.float32))
        self.timestamps.append(timestamp)
    
    def get_active_points(self, current_time: Optional[float] = None) -> np.ndarray:
        """
        Get trail points that are still within fade time.
        
        Args:
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Array of valid trail points
        """
        if current_time is None:
            current_time = time.time()
        
        if not self.points:
            return np.array([])
        
        active_points = []
        for point, timestamp in zip(self.points, self.timestamps):
            age = current_time - timestamp
            if age <= self.fade_time:
                active_points.append(point)
        
        return np.array(active_points) if active_points else np.array([])
    
    def get_fade_factors(self, current_time: Optional[float] = None) -> np.ndarray:
        """
        Get opacity/fade factors for each active point (0-1).
        
        Args:
            current_time: Current timestamp
        
        Returns:
            Array of fade factors
        """
        if current_time is None:
            current_time = time.time()
        
        factors = []
        for timestamp in self.timestamps:
            age = current_time - timestamp
            if age <= self.fade_time:
                factor = 1.0 - (age / self.fade_time)
                factors.append(factor)
        
        return np.array(factors)
    
    def clear(self):
        """Clear all trail points."""
        self.points.clear()
        self.timestamps.clear()


class GlowEffect:
    """Manages glow/aura effects for selected or highlighted polyforms."""
    
    def __init__(self, intensity: float = 0.5, pulse_speed: float = 2.0):
        """
        Initialize glow effect.
        
        Args:
            intensity: Glow intensity (0-1)
            pulse_speed: Speed of glow pulsing effect in Hz
        """
        self.intensity = intensity
        self.pulse_speed = pulse_speed
        self.start_time = time.time()
        self.is_active = False
    
    def activate(self):
        """Activate the glow effect."""
        self.is_active = True
        self.start_time = time.time()
    
    def deactivate(self):
        """Deactivate the glow effect."""
        self.is_active = False
    
    def get_current_intensity(self) -> float:
        """
        Get current glow intensity with pulsing effect.
        
        Returns:
            Glow intensity value (0-1)
        """
        if not self.is_active:
            return 0.0
        
        elapsed = time.time() - self.start_time
        # Create a pulsing effect using sine wave
        pulse = 0.5 + 0.5 * np.sin(elapsed * self.pulse_speed * 2 * np.pi)
        return self.intensity * pulse
    
    def get_color_with_glow(self, base_color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """
        Get modified color with glow intensity applied.
        
        Args:
            base_color: RGBA color tuple
        
        Returns:
            Modified RGBA color with glow
        """
        intensity = self.get_current_intensity()
        r, g, b, a = base_color
        
        # Enhance brightness based on glow
        r = min(1.0, r + intensity)
        g = min(1.0, g + intensity)
        b = min(1.0, b + intensity)
        
        return (r, g, b, a)


class SmoothCameraFollower:
    """Smoothly follows a polyform during animation."""
    
    def __init__(self, view: gl.GLViewWidget, follow_speed: float = 5.0):
        """
        Initialize camera follower.
        
        Args:
            view: GLViewWidget to control
            follow_speed: Speed of camera following (0-1, where 1 is instant)
        """
        self.view = view
        self.follow_speed = np.clip(follow_speed, 0.0, 1.0)
        self.target_position: Optional[np.ndarray] = None
        self.is_following = False
        self.offset = np.array([0.0, 0.0, 10.0])  # Default offset from target
    
    def start_following(self, target_position: np.ndarray, offset: Optional[np.ndarray] = None):
        """
        Start following a target position.
        
        Args:
            target_position: Target position to follow
            offset: Camera offset from target (relative position)
        """
        self.target_position = np.array(target_position, dtype=np.float32)
        self.is_following = True
        
        if offset is not None:
            self.offset = np.array(offset, dtype=np.float32)
    
    def stop_following(self):
        """Stop following."""
        self.is_following = False
        self.target_position = None
    
    def update(self, current_position: np.ndarray):
        """
        Update camera position towards target.
        
        Args:
            current_position: Polyform's current position
        """
        if not self.is_following or self.target_position is None:
            return
        
        # Update target position
        self.target_position = np.array(current_position, dtype=np.float32)
        
        # Calculate desired camera position
        desired_cam_pos = self.target_position + self.offset
        
        # Get current camera position
        try:
            current_cam = self.view.cameraPosition()
            current_cam_pos = np.array([current_cam.x(), current_cam.y(), current_cam.z()])
            
            # Interpolate camera position
            new_cam_pos = current_cam_pos + (desired_cam_pos - current_cam_pos) * self.follow_speed
            
            # Update camera to look at target
            self.view.setCameraPosition(pos=tuple(new_cam_pos), distance=None)
            
            # Make camera look at the target
            from PySide6.QtGui import QVector3D
            self.view.opts['center'] = QVector3D(*self.target_position)
        except Exception:
            pass


class PolyformTracker:
    """Tracks visual state and effects for a specific polyform."""
    
    def __init__(self, poly_id: str, enable_trail: bool = True, enable_glow: bool = True):
        """
        Initialize polyform tracker.
        
        Args:
            poly_id: ID of the polyform to track
            enable_trail: Whether to enable motion trail
            enable_glow: Whether to enable glow effect
        """
        self.poly_id = poly_id
        self.motion_trail: Optional[MotionTrail] = MotionTrail() if enable_trail else None
        self.glow: Optional[GlowEffect] = GlowEffect() if enable_glow else None
        self.last_position: Optional[np.ndarray] = None
        self.color: Tuple[float, float, float, float] = (0.2, 0.7, 1.0, 1.0)
    
    def update(self, position: np.ndarray):
        """
        Update tracker with current polyform position.
        
        Args:
            position: Current centroid position
        """
        self.last_position = np.array(position, dtype=np.float32)
        
        # Add to motion trail if enabled
        if self.motion_trail:
            self.motion_trail.add_point(position)
    
    def set_glow_active(self, active: bool):
        """Enable or disable glow effect."""
        if self.glow:
            if active:
                self.glow.activate()
            else:
                self.glow.deactivate()
    
    def get_effective_color(self) -> Tuple[float, float, float, float]:
        """
        Get current effective color with glow applied.
        
        Returns:
            RGBA color
        """
        if self.glow:
            return self.glow.get_color_with_glow(self.color)
        return self.color
    
    def get_trail_points(self) -> np.ndarray:
        """Get current trail points."""
        if self.motion_trail:
            return self.motion_trail.get_active_points()
        return np.array([])
    
    def clear(self):
        """Clear all tracking data."""
        if self.motion_trail:
            self.motion_trail.clear()
        if self.glow:
            self.glow.deactivate()


class VisualTrackingManager:
    """Master manager for all visual tracking effects."""
    
    def __init__(self, view: gl.GLViewWidget):
        """
        Initialize visual tracking manager.
        
        Args:
            view: GLViewWidget for rendering effects
        """
        self.view = view
        self.trackers: Dict[str, PolyformTracker] = {}
        self.trail_items: Dict[str, gl.GLLinePlotItem] = {}
        self.camera_follower = SmoothCameraFollower(view)
        self.enable_trails = True
        self.enable_glow = True
        self.show_trails = True
    
    def start_tracking(self, poly_id: str) -> PolyformTracker:
        """
        Start tracking a polyform.
        
        Args:
            poly_id: ID of polyform to track
        
        Returns:
            Tracker object
        """
        if poly_id not in self.trackers:
            self.trackers[poly_id] = PolyformTracker(poly_id, self.enable_trails, self.enable_glow)
            self.trackers[poly_id].set_glow_active(True)
        return self.trackers[poly_id]
    
    def stop_tracking(self, poly_id: str):
        """Stop tracking a polyform and clean up."""
        if poly_id in self.trackers:
            self.trackers[poly_id].clear()
            del self.trackers[poly_id]
        
        # Remove trail visualization
        if poly_id in self.trail_items:
            try:
                self.view.removeItem(self.trail_items[poly_id])
            except Exception:
                pass
            del self.trail_items[poly_id]
    
    def update_tracker(self, poly_id: str, position: np.ndarray):
        """
        Update tracker with current position.
        
        Args:
            poly_id: Polyform ID
            position: Current position
        """
        if poly_id not in self.trackers:
            self.start_tracking(poly_id)
        
        self.trackers[poly_id].update(position)
    
    def update_trails_visualization(self):
        """Update trail visualization in the view."""
        if not self.show_trails:
            # Clear all trails if hidden
            for item in list(self.trail_items.values()):
                try:
                    self.view.removeItem(item)
                except Exception:
                    pass
            self.trail_items.clear()
            return
        
        # Use list() to avoid modifying dict during iteration
        for poly_id in list(self.trackers.keys()):
            tracker = self.trackers.get(poly_id)
            if not tracker or not tracker.motion_trail:
                continue
            
            points = tracker.get_trail_points()
            if len(points) < 2:
                # Remove trail if insufficient points
                if poly_id in self.trail_items:
                    try:
                        self.view.removeItem(self.trail_items[poly_id])
                        del self.trail_items[poly_id]
                    except Exception:
                        pass
                continue
            
            # Properly remove old trail item
            if poly_id in self.trail_items:
                old_item = self.trail_items[poly_id]
                try:
                    self.view.removeItem(old_item)
                except Exception as e:
                    print(f"Warning: Failed to remove trail item {poly_id}: {e}")
                
                # Force cleanup
                try:
                    del self.trail_items[poly_id]
                except KeyError:
                    pass
            
            # Create new trail with proper error handling
            try:
                fade_factors = tracker.motion_trail.get_fade_factors()
                if len(fade_factors) == 0:
                    continue
                
                # Create trail line with fade
                trail_item = gl.GLLinePlotItem(
                    pos=points,
                    color=(0.0, 1.0, 0.5, 0.7),  # Simplified color
                    width=2,
                    mode='line_strip',
                    antialias=True
                )
                
                self.view.addItem(trail_item)
                self.trail_items[poly_id] = trail_item
            except Exception as e:
                print(f"Warning: Failed to create trail for {poly_id}: {e}")
    def follow_polyform(self, poly_id: str, position: np.ndarray, 
                       offset: Optional[np.ndarray] = None):
        """
        Start camera following a polyform.
        
        Args:
            poly_id: Polyform ID
            position: Current position
            offset: Camera offset from target
        """
        self.camera_follower.start_following(position, offset)
        self.start_tracking(poly_id)
    
    def stop_following(self):
        """Stop camera following."""
        self.camera_follower.stop_following()
    
    def update_camera(self, position: np.ndarray):
        """Update camera towards current target."""
        self.camera_follower.update(position)
    
    def get_tracker(self, poly_id: str) -> Optional[PolyformTracker]:
        """Get tracker for a polyform."""
        return self.trackers.get(poly_id)
    
    def clear_all(self):
        """Clear all tracking data."""
        for poly_id in list(self.trackers.keys()):
            self.stop_tracking(poly_id)
        self.stop_following()
    
    def set_trails_visible(self, visible: bool):
        """Show or hide all trails."""
        self.show_trails = visible
        if not visible:
            # Remove all trail items
            for item in self.trail_items.values():
                try:
                    self.view.removeItem(item)
                except Exception:
                    pass
            self.trail_items.clear()


class MotionIndicator:
    """Visual indicator for polyform movement speed and direction."""
    
    def __init__(self, base_color: Tuple[float, float, float, float] = (1.0, 0.5, 0.0, 0.8)):
        """
        Initialize motion indicator.
        
        Args:
            base_color: Base color for indicator
        """
        self.base_color = base_color
        self.positions: deque = deque(maxlen=10)  # Track last 10 positions
        self.velocities: deque = deque(maxlen=10)
        self.last_update = time.time()
    
    def update_position(self, position: np.ndarray):
        """
        Update with new position.
        
        Args:
            position: Current position
        """
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        if dt <= 0:
            return
        
        self.positions.append(np.array(position, dtype=np.float32))
        
        if len(self.positions) > 1:
            # Calculate velocity
            prev_pos = self.positions[-2]
            curr_pos = self.positions[-1]
            velocity = (curr_pos - prev_pos) / dt
            self.velocities.append(velocity)
    
    def get_current_speed(self) -> float:
        """Get current movement speed."""
        if not self.velocities:
            return 0.0
        
        velocity = self.velocities[-1]
        return float(np.linalg.norm(velocity))
    
    def get_current_direction(self) -> Optional[np.ndarray]:
        """Get current movement direction (normalized)."""
        speed = self.get_current_speed()
        if speed < 1e-6 or not self.velocities:
            return None
        
        velocity = self.velocities[-1]
        return velocity / (speed + 1e-10)
    
    def get_indicator_arrow(self, origin: np.ndarray, scale: float = 1.0) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get arrow points for velocity indicator.
        
        Args:
            origin: Starting position for arrow
            scale: Scale factor for arrow
        
        Returns:
            Tuple of (start_point, end_point) or None
        """
        direction = self.get_current_direction()
        speed = self.get_current_speed()
        
        if direction is None or speed < 0.01:
            return None
        
        arrow_length = min(speed * scale, 2.0)
        end_point = origin + direction * arrow_length
        
        return (origin, end_point)
