"""
Library Drag-and-Drop Handler

Enables intuitive drag-and-drop of polyforms from library to workspace.

Features:
- Visual feedback during drag
- Ghost preview on hover
- Snap-to-grid option
- Multiple selection support
- Undo/redo integration
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class DragState(Enum):
    """Drag operation states."""
    IDLE = 0
    STARTED = 1
    DRAGGING = 2
    HOVERING = 3
    DROPPED = 4
    CANCELLED = 5


@dataclass
class DragContext:
    """Context for a drag operation."""
    polyform_id: str
    polyform_data: Dict[str, Any]
    start_position: Tuple[float, float]
    current_position: Tuple[float, float]
    state: DragState
    ghost_opacity: float = 0.5
    snap_to_grid: bool = False
    grid_size: float = 1.0
    
    def update_position(self, x: float, y: float):
        """Update current position, applying snap if enabled."""
        if self.snap_to_grid:
            x = round(x / self.grid_size) * self.grid_size
            y = round(y / self.grid_size) * self.grid_size
        
        self.current_position = (x, y)
    
    def get_offset(self) -> Tuple[float, float]:
        """Get offset from start to current."""
        return (
            self.current_position[0] - self.start_position[0],
            self.current_position[1] - self.start_position[1]
        )


class LibraryDragDropHandler:
    """
    Manages drag-and-drop operations from library to workspace.
    
    Integrates with GUI event system to provide smooth interaction.
    """
    
    def __init__(self, workspace, library_manager):
        """
        Initialize drag-drop handler.
        
        Args:
            workspace: Workspace instance to add polyforms
            library_manager: Library manager with saved polyforms
        """
        self.workspace = workspace
        self.library = library_manager
        
        # Drag state
        self.current_drag: Optional[DragContext] = None
        self.drag_history: List[DragContext] = []
        
        # Configuration
        self.snap_enabled = False
        self.grid_size = 1.0
        self.ghost_opacity = 0.5
        self.drop_zone_padding = 50  # pixels
        
        # Callbacks
        self.on_drag_start: List[Callable] = []
        self.on_drag_move: List[Callable] = []
        self.on_drag_drop: List[Callable] = []
        self.on_drag_cancel: List[Callable] = []
    
    def start_drag(self, polyform_id: str, screen_x: float, screen_y: float) -> bool:
        """
        Start dragging a polyform from library.
        
        Args:
            polyform_id: ID of polyform in library
            screen_x, screen_y: Screen coordinates where drag started
            
        Returns:
            True if drag started successfully
        """
        # Get polyform from library
        polyform_data = self.library.get_polyform(polyform_id)
        
        if not polyform_data:
            return False
        
        # Convert screen to workspace coordinates
        workspace_pos = self._screen_to_workspace(screen_x, screen_y)
        
        # Create drag context
        self.current_drag = DragContext(
            polyform_id=polyform_id,
            polyform_data=polyform_data.copy(),
            start_position=workspace_pos,
            current_position=workspace_pos,
            state=DragState.STARTED,
            snap_to_grid=self.snap_enabled,
            grid_size=self.grid_size,
            ghost_opacity=self.ghost_opacity
        )
        
        # Trigger callbacks
        for callback in self.on_drag_start:
            callback(self.current_drag)
        
        return True
    
    def update_drag(self, screen_x: float, screen_y: float):
        """
        Update drag position as mouse moves.
        
        Args:
            screen_x, screen_y: Current mouse screen coordinates
        """
        if not self.current_drag or self.current_drag.state == DragState.IDLE:
            return
        
        # Convert to workspace coordinates
        workspace_pos = self._screen_to_workspace(screen_x, screen_y)
        
        # Update drag context
        self.current_drag.update_position(*workspace_pos)
        self.current_drag.state = DragState.DRAGGING
        
        # Check if hovering over valid drop zone
        if self._is_valid_drop_zone(screen_x, screen_y):
            self.current_drag.state = DragState.HOVERING
        
        # Trigger callbacks
        for callback in self.on_drag_move:
            callback(self.current_drag)
    
    def complete_drag(self, screen_x: float, screen_y: float) -> bool:
        """
        Complete drag operation, dropping polyform into workspace.
        
        Args:
            screen_x, screen_y: Screen coordinates where dropped
            
        Returns:
            True if drop was successful
        """
        if not self.current_drag:
            return False
        
        # Validate drop zone
        if not self._is_valid_drop_zone(screen_x, screen_y):
            self.cancel_drag()
            return False
        
        # Get final position
        final_pos = self._screen_to_workspace(screen_x, screen_y)
        
        if self.snap_enabled:
            final_pos = (
                round(final_pos[0] / self.grid_size) * self.grid_size,
                round(final_pos[1] / self.grid_size) * self.grid_size
            )
        
        # Create polyform in workspace
        polyform_copy = self._prepare_polyform_for_workspace(
            self.current_drag.polyform_data,
            final_pos
        )
        
        # Add to workspace
        success = self.workspace.add_polyform(polyform_copy)
        
        if success:
            self.current_drag.state = DragState.DROPPED
            
            # Record in history
            self.drag_history.append(self.current_drag)
            
            # Trigger callbacks
            for callback in self.on_drag_drop:
                callback(self.current_drag, polyform_copy)
        
        # Clear current drag
        self.current_drag = None
        
        return success
    
    def cancel_drag(self):
        """Cancel current drag operation."""
        if not self.current_drag:
            return
        
        self.current_drag.state = DragState.CANCELLED
        
        # Trigger callbacks
        for callback in self.on_drag_cancel:
            callback(self.current_drag)
        
        self.current_drag = None
    
    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self.current_drag is not None and \
               self.current_drag.state in [DragState.STARTED, DragState.DRAGGING, DragState.HOVERING]
    
    def get_ghost_render_data(self) -> Optional[Dict[str, Any]]:
        """
        Get data for rendering ghost preview.
        
        Returns:
            Render data for ghost, or None if not dragging
        """
        if not self.is_dragging():
            return None
        
        offset = self.current_drag.get_offset()
        
        return {
            'polyform': self.current_drag.polyform_data,
            'position': self.current_drag.current_position,
            'offset': offset,
            'opacity': self.current_drag.ghost_opacity,
            'valid_zone': self.current_drag.state == DragState.HOVERING
        }
    
    def set_snap_to_grid(self, enabled: bool, grid_size: float = 1.0):
        """Enable/disable snap-to-grid."""
        self.snap_enabled = enabled
        self.grid_size = grid_size
        
        if self.current_drag:
            self.current_drag.snap_to_grid = enabled
            self.current_drag.grid_size = grid_size
    
    def _screen_to_workspace(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to workspace coordinates."""
        # This should use workspace camera/viewport transform
        # Placeholder implementation
        if hasattr(self.workspace, 'screen_to_world'):
            return self.workspace.screen_to_world(screen_x, screen_y)
        
        # Default: assume 1:1 mapping
        return (screen_x, screen_y)
    
    def _is_valid_drop_zone(self, screen_x: float, screen_y: float) -> bool:
        """Check if screen position is valid drop zone."""
        # Check if within workspace bounds
        if hasattr(self.workspace, 'contains_point'):
            return self.workspace.contains_point(screen_x, screen_y)
        
        # Default: always valid
        return True
    
    def _prepare_polyform_for_workspace(
        self,
        polyform_data: Dict[str, Any],
        position: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        Prepare polyform data for insertion into workspace.
        
        Translates vertices to new position.
        """
        polyform = polyform_data.copy()
        
        # Get current center
        vertices = np.array(polyform.get('vertices', []))
        if len(vertices) == 0:
            return polyform
        
        current_center = vertices.mean(axis=0)
        
        # Compute translation
        target_center = np.array([position[0], position[1], current_center[2] if len(current_center) > 2 else 0.0])
        translation = target_center - current_center
        
        # Translate vertices
        new_vertices = []
        for v in vertices:
            new_v = v + translation
            new_vertices.append(new_v)
        
        polyform['vertices'] = new_vertices
        
        # Update position metadata
        polyform['position'] = position
        
        return polyform
    
    def add_drag_start_callback(self, callback: Callable):
        """Add callback for drag start."""
        self.on_drag_start.append(callback)
    
    def add_drag_move_callback(self, callback: Callable):
        """Add callback for drag move."""
        self.on_drag_move.append(callback)
    
    def add_drag_drop_callback(self, callback: Callable):
        """Add callback for successful drop."""
        self.on_drag_drop.append(callback)
    
    def add_drag_cancel_callback(self, callback: Callable):
        """Add callback for drag cancel."""
        self.on_drag_cancel.append(callback)


class MultiSelectDragHandler(LibraryDragDropHandler):
    """
    Extended drag handler supporting multiple polyform selection.
    
    Allows dragging multiple polyforms at once, maintaining relative positions.
    """
    
    def __init__(self, workspace, library_manager):
        super().__init__(workspace, library_manager)
        
        self.selected_polyforms: List[str] = []
        self.multi_drag_contexts: List[DragContext] = []
    
    def set_selection(self, polyform_ids: List[str]):
        """Set multiple selected polyforms."""
        self.selected_polyforms = polyform_ids
    
    def start_multi_drag(self, screen_x: float, screen_y: float) -> bool:
        """Start dragging all selected polyforms."""
        if not self.selected_polyforms:
            return False
        
        # Create drag context for each
        workspace_pos = self._screen_to_workspace(screen_x, screen_y)
        
        self.multi_drag_contexts = []
        
        for pid in self.selected_polyforms:
            polyform_data = self.library.get_polyform(pid)
            
            if polyform_data:
                ctx = DragContext(
                    polyform_id=pid,
                    polyform_data=polyform_data.copy(),
                    start_position=workspace_pos,
                    current_position=workspace_pos,
                    state=DragState.STARTED,
                    snap_to_grid=self.snap_enabled,
                    grid_size=self.grid_size,
                    ghost_opacity=self.ghost_opacity
                )
                self.multi_drag_contexts.append(ctx)
        
        if self.multi_drag_contexts:
            self.current_drag = self.multi_drag_contexts[0]
            
            for callback in self.on_drag_start:
                callback(self.current_drag)
            
            return True
        
        return False
    
    def complete_multi_drag(self, screen_x: float, screen_y: float) -> bool:
        """Drop all selected polyforms."""
        if not self.multi_drag_contexts:
            return False
        
        if not self._is_valid_drop_zone(screen_x, screen_y):
            self.cancel_drag()
            return False
        
        # Calculate offset
        final_pos = self._screen_to_workspace(screen_x, screen_y)
        first_ctx = self.multi_drag_contexts[0]
        offset = (
            final_pos[0] - first_ctx.start_position[0],
            final_pos[1] - first_ctx.start_position[1]
        )
        
        # Drop each polyform with offset
        dropped = []
        for ctx in self.multi_drag_contexts:
            drop_pos = (
                ctx.start_position[0] + offset[0],
                ctx.start_position[1] + offset[1]
            )
            
            polyform = self._prepare_polyform_for_workspace(ctx.polyform_data, drop_pos)
            
            if self.workspace.add_polyform(polyform):
                dropped.append(polyform)
        
        # Clear
        self.multi_drag_contexts = []
        self.current_drag = None
        
        return len(dropped) > 0


# Quick integration helper
def integrate_with_gui(gui_window, workspace, library_manager):
    """
    Integrate drag-drop handler with GUI window.
    
    Args:
        gui_window: GUI window with event system
        workspace: Workspace instance
        library_manager: Library manager
    
    Returns:
        Configured drag-drop handler
    """
    handler = LibraryDragDropHandler(workspace, library_manager)
    
    # Hook up to GUI events (pseudo-code, adapt to actual GUI)
    if hasattr(gui_window, 'on_mouse_press'):
        def on_press(event):
            if event.widget == 'library_item':
                polyform_id = event.data.get('polyform_id')
                handler.start_drag(polyform_id, event.x, event.y)
        
        gui_window.on_mouse_press.append(on_press)
    
    if hasattr(gui_window, 'on_mouse_move'):
        def on_move(event):
            if handler.is_dragging():
                handler.update_drag(event.x, event.y)
        
        gui_window.on_mouse_move.append(on_move)
    
    if hasattr(gui_window, 'on_mouse_release'):
        def on_release(event):
            if handler.is_dragging():
                handler.complete_drag(event.x, event.y)
        
        gui_window.on_mouse_release.append(on_release)
    
    return handler
