"""
INTERACTIVE 3D WORKSPACE: Drag-to-Create with Context-Aware Attachment

Features:
1. Right-click drag creates polyforms based on slider parameters
2. Automatic attachment to nearby polyforms
3. Dynamic LOD and scaling for large assemblies (n > 1000)
4. Real-time preview during drag
5. Smart snapping and bond suggestion
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================================
# DRAG-TO-CREATE SYSTEM
# ============================================================================

@dataclass
class DragContext:
    """Context for a drag operation."""
    start_pos: Tuple[float, float, float]
    current_pos: Tuple[float, float, float]
    start_time: float
    
    # Slider parameters at drag start
    sides: int = 4
    complexity: float = 0.5
    symmetry: float = 0.75
    
    # Nearby context
    nearest_polyforms: List[Dict[str, Any]] = field(default_factory=list)
    snap_target: Optional[Dict[str, Any]] = None
    snap_distance: float = float('inf')
    
    @property
    def drag_distance(self) -> float:
        """Total distance dragged in 3D space."""
        start = np.array(self.start_pos)
        current = np.array(self.current_pos)
        return float(np.linalg.norm(current - start))
    
    @property
    def drag_direction(self) -> np.ndarray:
        """Normalized drag direction."""
        start = np.array(self.start_pos)
        current = np.array(self.current_pos)
        diff = current - start
        norm = np.linalg.norm(diff)
        return diff / norm if norm > 1e-6 else np.array([0, 0, 0])
    
    @property
    def duration_ms(self) -> float:
        """Duration of drag in milliseconds."""
        return (time.time() - self.start_time) * 1000


class AttachmentMode(Enum):
    """How polyforms attach to nearby polyforms."""
    NONE = "none"                 # No attachment
    EDGE_TO_EDGE = "edge_to_edge" # Connect via matching edges
    FACE_TO_FACE = "face_to_face" # Connect via faces
    VERTEX_SNAP = "vertex_snap"   # Snap vertices together
    AUTO = "auto"                 # Automatic based on geometry


class PolyformLibrary:
    """Library of predefined polyhedra shapes."""
    
    @staticmethod
    def create_cube(position=(0, 0, 0), size=1.0) -> Dict[str, Any]:
        """Create a cube (hexahedron)."""
        s = size / 2
        vertices = [
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],  # bottom
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],      # top
        ]
        
        # Translate to position
        vertices = [[v[0] + position[0], v[1] + position[1], v[2] + position[2]] for v in vertices]
        
        return {
            'type': 'cube',
            'sides': 6,
            'vertices': vertices,
            'position': list(position),
            'edges': 12,
            'faces': 6,
            'symmetry': 1.0,
        }
    
    @staticmethod
    def create_octahedron(position=(0, 0, 0), size=1.0) -> Dict[str, Any]:
        """Create an octahedron (8 faces, 6 vertices)."""
        s = size / np.sqrt(2)
        vertices = [
            [s, 0, 0], [-s, 0, 0],
            [0, s, 0], [0, -s, 0],
            [0, 0, s], [0, 0, -s],
        ]
        
        # Translate
        vertices = [[v[0] + position[0], v[1] + position[1], v[2] + position[2]] for v in vertices]
        
        return {
            'type': 'octahedron',
            'sides': 8,
            'vertices': vertices,
            'position': list(position),
            'edges': 12,
            'faces': 8,
            'symmetry': 1.0,
        }
    
    @staticmethod
    def create_tetrahedron(position=(0, 0, 0), size=1.0) -> Dict[str, Any]:
        """Create a tetrahedron."""
        a = size / np.sqrt(8/3)
        h = size * np.sqrt(2/3)
        vertices = [
            [0, 0, 0],
            [a, 0, 0],
            [a/2, a*np.sqrt(3)/2, 0],
            [a/2, a*np.sqrt(3)/6, h],
        ]
        
        # Translate
        vertices = [[v[0] + position[0], v[1] + position[1], v[2] + position[2]] for v in vertices]
        
        return {
            'type': 'tetrahedron',
            'sides': 4,
            'vertices': vertices,
            'position': list(position),
            'edges': 6,
            'faces': 4,
            'symmetry': 1.0,
        }
    
    @staticmethod
    def create_icosahedron(position=(0, 0, 0), size=1.0) -> Dict[str, Any]:
        """Create an icosahedron (20 faces, 12 vertices)."""
        phi = (1 + np.sqrt(5)) / 2
        s = size / (2 * np.sqrt(phi + 2))
        
        vertices = [
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
        ]
        
        vertices = [[v[0]*s + position[0], v[1]*s + position[1], v[2]*s + position[2]] for v in vertices]
        
        return {
            'type': 'icosahedron',
            'sides': 20,
            'vertices': vertices,
            'position': list(position),
            'edges': 30,
            'faces': 20,
            'symmetry': 1.0,
        }
    
    @staticmethod
    def create_dodecahedron(position=(0, 0, 0), size=1.0) -> Dict[str, Any]:
        """Create a dodecahedron (12 pentagonal faces)."""
        phi = (1 + np.sqrt(5)) / 2
        s = size / (2 * phi)
        
        vertices = [
            [s, s, s], [-s, -s, s], [-s, s, -s], [s, -s, -s],
            [0, s*phi, s/phi], [0, -s*phi, s/phi],
            [0, -s*phi, -s/phi], [0, s*phi, -s/phi],
            [s/phi, 0, s*phi], [-s/phi, 0, s*phi],
            [-s/phi, 0, -s*phi], [s/phi, 0, -s*phi],
            [s*phi, s/phi, 0], [-s*phi, -s/phi, 0],
            [-s*phi, s/phi, 0], [s*phi, -s/phi, 0],
        ]
        
        vertices = [[v[0] + position[0], v[1] + position[1], v[2] + position[2]] for v in vertices]
        
        return {
            'type': 'dodecahedron',
            'sides': 12,
            'vertices': vertices,
            'position': list(position),
            'edges': 30,
            'faces': 12,
            'symmetry': 1.0,
        }
    
    @staticmethod
    def select_shape_from_slider(sides: int) -> str:
        """Select polyhedron based on slider sides value."""
        if sides <= 4:
            return 'tetrahedron'
        elif sides == 5:
            return 'cube'  # Approximate
        elif sides == 6:
            return 'cube'
        elif sides == 8:
            return 'octahedron'
        elif sides == 12:
            return 'icosahedron'
        else:
            return 'cube'  # Fallback
    
    @classmethod
    def create_from_slider(cls, sides: int, complexity: float, 
                          symmetry: float, position=(0, 0, 0), 
                          size=1.0) -> Dict[str, Any]:
        """Create polyhedron based on slider parameters."""
        shape = cls.select_shape_from_slider(sides)
        
        if shape == 'tetrahedron':
            poly = cls.create_tetrahedron(position, size)
        elif shape == 'cube':
            poly = cls.create_cube(position, size)
        elif shape == 'octahedron':
            poly = cls.create_octahedron(position, size)
        elif shape == 'icosahedron':
            poly = cls.create_icosahedron(position, size)
        elif shape == 'dodecahedron':
            poly = cls.create_dodecahedron(position, size)
        else:
            poly = cls.create_cube(position, size)
        
        # Apply complexity (perturbation)
        if complexity > 0.1:
            poly = cls._apply_complexity(poly, complexity)
        
        # Apply symmetry constraint
        poly['symmetry'] = symmetry
        
        return poly
    
    @staticmethod
    def _apply_complexity(poly: Dict[str, Any], complexity: float) -> Dict[str, Any]:
        """Apply complexity perturbation to vertices."""
        vertices = np.array(poly['vertices'])
        perturbation = np.random.normal(0, complexity * 0.1, vertices.shape)
        vertices = vertices + perturbation
        poly['vertices'] = vertices.tolist()
        return poly


# ============================================================================
# AUTOMATIC ATTACHMENT SYSTEM
# ============================================================================

class AttachmentCalculator:
    """Calculates optimal attachment points between polyforms."""
    
    def __init__(self, snap_distance: float = 2.0):
        """
        Initialize calculator.
        
        Args:
            snap_distance: Maximum distance to consider for snapping
        """
        self.snap_distance = snap_distance
    
    def find_attachments(self, new_poly: Dict[str, Any], 
                        nearby_polys: List[Dict[str, Any]],
                        max_attachments: int = 3) -> List[Tuple[Dict, str, float]]:
        """
        Find potential attachment points with nearby polyforms.
        
        Args:
            new_poly: Newly created polyform
            nearby_polys: List of nearby polyforms to consider
            max_attachments: Maximum attachments to return
        
        Returns:
            List of (target_poly, attachment_type, score) tuples
        """
        attachments = []
        
        for target in nearby_polys:
            # Calculate edge-to-edge attachment
            edge_score = self._calculate_edge_attachment(new_poly, target)
            if edge_score > 0:
                attachments.append((target, AttachmentMode.EDGE_TO_EDGE, edge_score))
            
            # Calculate face-to-face attachment
            face_score = self._calculate_face_attachment(new_poly, target)
            if face_score > 0:
                attachments.append((target, AttachmentMode.FACE_TO_FACE, face_score))
            
            # Calculate vertex snapping
            vertex_score = self._calculate_vertex_snap(new_poly, target)
            if vertex_score > 0:
                attachments.append((target, AttachmentMode.VERTEX_SNAP, vertex_score))
        
        # Sort by score and return top attachments
        attachments.sort(key=lambda x: x[2], reverse=True)
        return attachments[:max_attachments]
    
    def _calculate_edge_attachment(self, poly1: Dict, poly2: Dict) -> float:
        """Calculate edge-to-edge attachment score."""
        verts1 = np.array(poly1['vertices'])
        verts2 = np.array(poly2['vertices'])
        
        # Get edge midpoints and normals
        edges1 = self._get_edges(verts1)
        edges2 = self._get_edges(verts2)
        
        max_score = 0.0
        for e1 in edges1:
            for e2 in edges2:
                mid1 = (verts1[e1[0]] + verts1[e1[1]]) / 2
                mid2 = (verts2[e2[0]] + verts2[e2[1]]) / 2
                dist = np.linalg.norm(mid1 - mid2)
                
                if dist < self.snap_distance:
                    # Closer edges = higher score
                    score = 1.0 - (dist / self.snap_distance)
                    max_score = max(max_score, score)
        
        return max_score
    
    def _calculate_face_attachment(self, poly1: Dict, poly2: Dict) -> float:
        """Calculate face-to-face attachment score."""
        # Simplified: use centroid distance as proxy
        pos1 = np.array(poly1['position'])
        pos2 = np.array(poly2['position'])
        dist = np.linalg.norm(pos1 - pos2)
        
        if dist < self.snap_distance * 2:
            return 0.5 * (1.0 - (dist / (self.snap_distance * 2)))
        return 0.0
    
    def _calculate_vertex_snap(self, poly1: Dict, poly2: Dict) -> float:
        """Calculate vertex snapping score."""
        verts1 = np.array(poly1['vertices'])
        verts2 = np.array(poly2['vertices'])
        
        max_score = 0.0
        for v1 in verts1:
            for v2 in verts2:
                dist = np.linalg.norm(v1 - v2)
                if dist < self.snap_distance * 0.5:
                    score = 1.0 - (dist / (self.snap_distance * 0.5))
                    max_score = max(max_score, score)
        
        return max_score * 0.7  # Lower priority than edge/face
    
    @staticmethod
    def _get_edges(vertices: np.ndarray) -> List[Tuple[int, int]]:
        """Extract edges from vertices (simplified)."""
        edges = []
        n = len(vertices)
        # Connect adjacent vertices
        for i in range(n):
            edges.append((i, (i + 1) % n))
        return edges


# ============================================================================
# INTERACTIVE WORKSPACE CONTROLLER
# ============================================================================

class InteractiveWorkspaceController:
    """
    Manages drag-to-create interactions and assembly building.
    
    WORKFLOW:
    1. User right-clicks and drags in workspace
    2. Drag distance and direction determine polyform placement
    3. Slider parameters (sides, complexity, symmetry) define shape
    4. Automatic attachment to nearby polyforms
    5. Dynamic scaling/LOD for large assemblies
    """
    
    def __init__(self, on_polyform_created: Optional[Callable] = None):
        """
        Initialize controller.
        
        Args:
            on_polyform_created: Callback when polyform is created
        """
        self.on_polyform_created = on_polyform_created
        self.current_drag: Optional[DragContext] = None
        self.polyforms: List[Dict[str, Any]] = []
        self.attachment_calc = AttachmentCalculator(snap_distance=2.0)
        
        # Tracking
        self.stats = {
            'total_created': 0,
            'total_attachments': 0,
            'average_attachment_distance': 0.0,
        }
        
        # LOD settings
        self.lod_enabled = True
        self.lod_threshold = 1000  # Enable LOD at n > 1000
    
    def on_right_click_start(self, position: Tuple[float, float, float],
                            sides: int, complexity: float, symmetry: float):
        """
        Start drag operation.
        
        Args:
            position: 3D position where drag started
            sides: Slider value for sides (3-12)
            complexity: Slider value for complexity (0.0-1.0)
            symmetry: Slider value for symmetry (0.0-1.0)
        """
        self.current_drag = DragContext(
            start_pos=position,
            current_pos=position,
            start_time=time.time(),
            sides=sides,
            complexity=complexity,
            symmetry=symmetry,
        )
        
        # Find nearby polyforms for context
        self.current_drag.nearest_polyforms = self._find_nearby_polyforms(position, radius=5.0)
        
        logger.debug(f"Drag started at {position} with {len(self.current_drag.nearest_polyforms)} nearby polyforms")
    
    def on_right_click_drag(self, current_position: Tuple[float, float, float]):
        """
        Update drag operation (called continuously during drag).
        
        Args:
            current_position: Current 3D position
        """
        if not self.current_drag:
            return
        
        self.current_drag.current_pos = current_position
        
        # Update snap target based on proximity
        self._update_snap_target()
    
    def on_right_click_release(self):
        """Complete drag operation and create polyform with attachments."""
        if not self.current_drag:
            return
        
        drag = self.current_drag
        logger.debug(f"Drag completed: distance={drag.drag_distance:.2f}m, duration={drag.duration_ms:.0f}ms")
        
        # Determine placement based on drag
        placement_pos = self._calculate_placement(drag)
        
        # Determine size based on drag distance
        size = self._calculate_size(drag)
        
        # Create polyform from slider parameters
        poly = PolyformLibrary.create_from_slider(
            sides=drag.sides,
            complexity=drag.complexity,
            symmetry=drag.symmetry,
            position=placement_pos,
            size=size,
        )
        
        poly['id'] = f'drag_{self.stats["total_created"]:05d}'
        poly['creation_time'] = time.time()
        
        # Find and create attachments
        attachments = self.attachment_calc.find_attachments(
            poly, drag.nearest_polyforms, max_attachments=3
        )
        
        # Create bonds to nearby polyforms
        bonds = []
        for target_poly, attachment_mode, score in attachments:
            if score > 0.3:  # Threshold for automatic attachment
                bond = {
                    'poly1_id': poly['id'],
                    'poly2_id': target_poly.get('id'),
                    'type': attachment_mode.value,
                    'strength': float(score),
                }
                bonds.append(bond)
                self.stats['total_attachments'] += 1
        
        poly['bonds'] = bonds
        
        # Add to assembly
        self.polyforms.append(poly)
        self.stats['total_created'] += 1
        
        # Trigger callback
        if self.on_polyform_created:
            self.on_polyform_created(poly)
        
        logger.info(f"Created polyform {poly['id']} with {len(bonds)} attachments")
        
        # Cleanup
        self.current_drag = None
    
    def _find_nearby_polyforms(self, position: Tuple[float, float, float], 
                               radius: float = 5.0) -> List[Dict[str, Any]]:
        """Find polyforms within radius of position."""
        nearby = []
        pos = np.array(position)
        
        for poly in self.polyforms:
            poly_pos = np.array(poly['position'])
            dist = np.linalg.norm(poly_pos - pos)
            if dist < radius:
                nearby.append(poly)
        
        return nearby
    
    def _update_snap_target(self):
        """Update snap target based on current proximity."""
        if not self.current_drag:
            return
        
        current_pos = np.array(self.current_drag.current_pos)
        min_dist = float('inf')
        best_target = None
        
        for poly in self.current_drag.nearest_polyforms:
            poly_pos = np.array(poly['position'])
            dist = np.linalg.norm(current_pos - poly_pos)
            
            if dist < min_dist:
                min_dist = dist
                best_target = poly
        
        self.current_drag.snap_target = best_target
        self.current_drag.snap_distance = min_dist
    
    def _calculate_placement(self, drag: DragContext) -> Tuple[float, float, float]:
        """Calculate placement based on drag and snap targets."""
        # If close to snap target, snap to it
        if drag.snap_target and drag.snap_distance < 1.5:
            target_pos = np.array(drag.snap_target['position'])
            # Place offset from target along drag direction
            offset = drag.drag_direction * 2.0
            placement = target_pos + offset
        else:
            # Place at current position
            placement = drag.current_pos
        
        return tuple(placement)
    
    def _calculate_size(self, drag: DragContext) -> float:
        """Calculate size based on drag distance."""
        # Drag distance influences size: longer drag = larger polyform
        # Max size at 10m drag distance
        size = min(3.0, 0.5 + (drag.drag_distance / 10.0) * 2.0)
        return float(size)
    
    def get_preview_polyform(self) -> Optional[Dict[str, Any]]:
        """Get preview of polyform during drag (for rendering)."""
        if not self.current_drag:
            return None
        
        drag = self.current_drag
        placement_pos = self._calculate_placement(drag)
        size = self._calculate_size(drag)
        
        preview = PolyformLibrary.create_from_slider(
            sides=drag.sides,
            complexity=drag.complexity,
            symmetry=drag.symmetry,
            position=placement_pos,
            size=size,
        )
        
        preview['preview'] = True
        preview['snap_target'] = drag.snap_target
        preview['snap_distance'] = drag.snap_distance
        
        return preview
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get assembly statistics."""
        return {
            'total_polyforms': len(self.polyforms),
            'total_created': self.stats['total_created'],
            'total_attachments': self.stats['total_attachments'],
            'avg_attachments_per_polyform': (
                self.stats['total_attachments'] / max(1, len(self.polyforms))
            ),
            'lod_enabled': self.lod_enabled,
            'lod_active': len(self.polyforms) > self.lod_threshold,
        }
    
    def get_assembly_state(self) -> Dict[str, Any]:
        """Get complete assembly state for saving/loading."""
        return {
            'polyforms': self.polyforms,
            'statistics': self.get_statistics(),
            'timestamp': time.time(),
        }


# ============================================================================
# DYNAMIC SCALING & LOD
# ============================================================================

class DynamicScalingManager:
    """Manages LOD and scaling for large assemblies."""
    
    def __init__(self, assembly_controller: InteractiveWorkspaceController):
        self.controller = assembly_controller
        self.lod_levels = [100, 500, 1000, 2000, 5000]
        self.current_lod_level = 0
    
    def update_lod(self) -> bool:
        """
        Update LOD based on assembly size.
        
        Returns:
            True if LOD level changed
        """
        n = len(self.controller.polyforms)
        new_level = 0
        
        for i, threshold in enumerate(self.lod_levels):
            if n > threshold:
                new_level = i + 1
        
        if new_level != self.current_lod_level:
            logger.info(f"LOD changed: level {self.current_lod_level} → {new_level} (n={n})")
            self.current_lod_level = new_level
            return True
        
        return False
    
    def get_render_config(self) -> Dict[str, Any]:
        """Get rendering configuration for current LOD level."""
        n = len(self.controller.polyforms)
        
        if n < 100:
            return {
                'level': 'high',
                'render_all': True,
                'shadows': True,
                'reflections': True,
                'anti_alias': 'high',
            }
        elif n < 500:
            return {
                'level': 'medium',
                'render_all': True,
                'shadows': True,
                'reflections': False,
                'anti_alias': 'medium',
            }
        elif n < 1000:
            return {
                'level': 'low',
                'render_all': True,
                'shadows': False,
                'reflections': False,
                'anti_alias': 'low',
                'cull_distant': True,
                'cull_distance': 50.0,
            }
        elif n < 5000:
            return {
                'level': 'very_low',
                'render_visible_only': True,
                'frustum_cull': True,
                'lod_meshes': True,
                'batch_render': True,
            }
        else:
            return {
                'level': 'ultra_low',
                'render_visible_only': True,
                'frustum_cull': True,
                'lod_meshes': True,
                'batch_render': True,
                'instanced_render': True,
            }


if __name__ == '__main__':
    # Example usage
    def on_polyform_created(poly):
        print(f"Created: {poly['id']} at {poly['position']}")
    
    controller = InteractiveWorkspaceController(on_polyform_created=on_polyform_created)
    scaler = DynamicScalingManager(controller)
    
    # Simulate drag interaction
    print("Simulating drag interaction...")
    controller.on_right_click_start((0, 0, 0), sides=6, complexity=0.5, symmetry=0.8)
    controller.on_right_click_drag((3, 2, 1))  # Drag 3m away
    controller.on_right_click_release()
    
    print(f"Assembly stats: {controller.get_statistics()}")
    print(f"Render config: {scaler.get_render_config()}")
