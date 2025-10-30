"""
Ray-Casting & Selection System for Polylog6

Handles mouse-based picking, ray-casting through 3D geometry,
and selection state management with visual highlighting.
"""

from typing import Optional, List, Tuple, Dict, Any
import numpy as np
from enum import Enum


class SelectionMode(Enum):
    """Selection interaction modes"""
    SINGLE = 1      # Click to select one
    MULTI = 2       # Shift+Click to add to selection
    TOGGLE = 3      # Ctrl+Click to toggle
    BOX = 4         # Drag box to select multiple


class RaycastingEngine:
    """
    Ray-casting for 3D mesh picking.
    
    Given a 2D screen position, projects ray into 3D space
    and detects intersection with mesh geometry.
    """
    
    def __init__(self):
        """Initialize raycasting engine"""
        self.epsilon = 1e-8
    
    def screen_to_ray(self, screen_x: float, screen_y: float, 
                     viewport: Tuple[int, int],
                     view_matrix: np.ndarray,
                     proj_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert 2D screen coordinates to 3D ray in world space.
        
        Args:
            screen_x, screen_y: Screen coordinates in pixels
            viewport: (width, height) of viewport
            view_matrix: 4x4 view matrix from camera
            proj_matrix: 4x4 projection matrix from camera
            
        Returns:
            (ray_origin, ray_direction) as numpy arrays
        """
        width, height = viewport
        
        # Normalize to [-1, 1]
        ndc_x = (2.0 * screen_x) / width - 1.0
        ndc_y = 1.0 - (2.0 * screen_y) / height
        
        # Create NDC ray endpoints (near and far plane)
        ray_ndc_near = np.array([ndc_x, ndc_y, -1.0, 1.0])
        ray_ndc_far = np.array([ndc_x, ndc_y, 1.0, 1.0])
        
        # Inverse matrices
        try:
            inv_proj = np.linalg.inv(proj_matrix)
            inv_view = np.linalg.inv(view_matrix)
        except np.linalg.LinAlgError as e:
            # Log error instead of silently failing
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Matrix singularity in screen_to_ray: projection or view matrix not invertible. {e}")
            # Fallback if matrices are singular
            return np.array([0, 0, 0]), np.array([0, 0, 1])
        
        # Transform from NDC to eye space
        ray_eye_near = inv_proj @ ray_ndc_near
        ray_eye_far = inv_proj @ ray_ndc_far
        
        # Divide by w to get 3D coordinates
        ray_eye_near = ray_eye_near[:3] / (ray_eye_near[3] + self.epsilon)
        ray_eye_far = ray_eye_far[:3] / (ray_eye_far[3] + self.epsilon)
        
        # Transform from eye space to world space
        ray_world_near = (inv_view @ np.append(ray_eye_near, 1))[:3]
        ray_world_far = (inv_view @ np.append(ray_eye_far, 1))[:3]
        
        ray_origin = ray_world_near
        ray_dir = ray_world_far - ray_world_near
        ray_dir = ray_dir / (np.linalg.norm(ray_dir) + self.epsilon)
        
        return ray_origin, ray_dir
    
    def ray_triangle_intersection(self, ray_origin: np.ndarray,
                                ray_dir: np.ndarray,
                                v0: np.ndarray,
                                v1: np.ndarray,
                                v2: np.ndarray) -> Optional[Tuple[float, np.ndarray]]:
        """
        Möller-Trumbore ray-triangle intersection algorithm.
        
        Args:
            ray_origin: Ray origin point
            ray_dir: Ray direction (should be normalized)
            v0, v1, v2: Triangle vertices
            
        Returns:
            (distance, intersection_point) or None if no hit
        """
        # Edges
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        # Cross product
        h = np.cross(ray_dir, edge2)
        a = np.dot(edge1, h)
        
        if abs(a) < self.epsilon:
            return None  # Ray parallel to triangle
        
        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)
        
        if u < 0.0 or u > 1.0:
            return None
        
        q = np.cross(s, edge1)
        v = f * np.dot(ray_dir, q)
        
        if v < 0.0 or u + v > 1.0:
            return None
        
        t = f * np.dot(edge2, q)
        
        if t > self.epsilon:  # Positive t
            intersection_point = ray_origin + t * ray_dir
            return t, intersection_point
        
        return None
    
    def ray_mesh_intersections(self, ray_origin: np.ndarray,
                             ray_dir: np.ndarray,
                             mesh_vertices: np.ndarray,
                             mesh_faces: np.ndarray) -> List[Dict[str, Any]]:
        """
        Find all intersections along ray with mesh.
        
        Args:
            ray_origin: Ray origin point
            ray_dir: Ray direction (normalized)
            mesh_vertices: Nx3 array of vertex positions
            mesh_faces: Mx3 array of face indices
            
        Returns:
            List of hits sorted by distance, each containing:
            - distance: float
            - point: np.ndarray (intersection point)
            - face_id: int (triangle index)
        """
        hits = []
        
        if len(mesh_faces) == 0:
            return hits
        
        for face_id, face in enumerate(mesh_faces):
            try:
                v0 = mesh_vertices[int(face[0])]
                v1 = mesh_vertices[int(face[1])]
                v2 = mesh_vertices[int(face[2])]
            except (IndexError, TypeError):
                continue
            
            result = self.ray_triangle_intersection(ray_origin, ray_dir, v0, v1, v2)
            
            if result:
                distance, intersection_point = result
                hits.append({
                    'distance': distance,
                    'point': intersection_point,
                    'face_id': face_id
                })
        
        # Sort by distance
        hits.sort(key=lambda h: h['distance'])
        
        return hits
    
    def closest_hit(self, ray_origin: np.ndarray, ray_dir: np.ndarray,
                   mesh_vertices: np.ndarray, mesh_faces: np.ndarray) -> Optional[Dict]:
        """Get only the closest intersection"""
        hits = self.ray_mesh_intersections(ray_origin, ray_dir, mesh_vertices, mesh_faces)
        return hits[0] if hits else None


class SelectionManager:
    """
    Manages selection state and highlighting.
    """
    
    def __init__(self, renderer):
        """
        Initialize selection manager.
        
        Args:
            renderer: GLRenderer instance for updating highlights
        """
        self.renderer = renderer
        self.selected_polyforms: set = set()
        self.selected_faces: set = set()  # (polyform_id, face_idx)
        self.selected_edges: set = set()  # (polyform_id, edge_idx)
        self.mode = SelectionMode.SINGLE
        self.hover_highlight: Optional[str] = None
    
    def select_polyform(self, polyform_id: str, add: bool = False):
        """Select entire polyform"""
        if not add:
            self.clear_selection()
        self.selected_polyforms.add(polyform_id)
        self._update_highlights()
    
    def select_face(self, polyform_id: str, face_idx: int, add: bool = False):
        """Select individual face"""
        if not add:
            self.clear_selection()
        self.selected_faces.add((polyform_id, face_idx))
        self._update_highlights()
    
    def select_edge(self, polyform_id: str, edge_idx: int, add: bool = False):
        """Select individual edge"""
        if not add:
            self.clear_selection()
        self.selected_edges.add((polyform_id, edge_idx))
        self._update_highlights()
    
    def clear_selection(self):
        """Clear all selections"""
        self.selected_polyforms.clear()
        self.selected_faces.clear()
        self.selected_edges.clear()
        self._update_highlights()
    
    def toggle_selection(self, selection_id: str, select_type: str = 'polyform'):
        """Toggle selection on/off"""
        if select_type == 'polyform':
            if selection_id in self.selected_polyforms:
                self.selected_polyforms.remove(selection_id)
            else:
                self.selected_polyforms.add(selection_id)
        self._update_highlights()
    
    def _update_highlights(self):
        """Refresh visual highlights in renderer"""
        # Clear old highlights
        if hasattr(self.renderer, '_clear_highlights'):
            self.renderer._clear_highlights()
        
        # Add new highlights for selected polyforms
        for poly_id in self.selected_polyforms:
            self._highlight_polyform(poly_id, color=(0, 1, 1, 1))  # Cyan
        
        # Add highlights for selected faces
        for poly_id, face_idx in self.selected_faces:
            self._highlight_face(poly_id, face_idx, color=(1, 1, 0, 1))  # Yellow
        
        # Add highlights for selected edges
        for poly_id, edge_idx in self.selected_edges:
            self._highlight_edge(poly_id, edge_idx, color=(1, 0, 1, 1))  # Magenta
    
    def _highlight_polyform(self, poly_id: str, color):
        """Highlight entire polyform with colored outline"""
        # Use renderer's highlight system if available
        if hasattr(self.renderer, '_highlight_polyform'):
            self.renderer._highlight_polyform(poly_id, color)
    
    def _highlight_face(self, poly_id: str, face_idx: int, color):
        """Highlight specific face"""
        # Would extract face vertices and highlight them
        pass
    
    def _highlight_edge(self, poly_id: str, edge_idx: int, color):
        """Highlight specific edge"""
        if hasattr(self.renderer, '_highlight_edge'):
            self.renderer._highlight_edge(poly_id, edge_idx, color)


class InteractionManager:
    """
    Main interaction coordinator.
    Connects mouse events, ray-casting, and selection.
    """
    
    def __init__(self, renderer, assembly, view_widget):
        """
        Initialize interaction manager.
        
        Args:
            renderer: GLRenderer instance
            assembly: Assembly object with polyforms
            view_widget: GLViewWidget for camera matrices
        """
        self.renderer = renderer
        self.assembly = assembly
        self.view_widget = view_widget
        self.raycaster = RaycastingEngine()
        self.selection = SelectionManager(renderer)
        
        # Context menu callback
        self.context_menu_callback = None
        
        # Drag state
        self.dragging = False
        self.drag_start = (0, 0)
    
    def handle_mouse_press(self, screen_x: int, screen_y: int, 
                          modifiers: List[str], button: str):
        """
        Handle mouse click for selection.
        
        Args:
            screen_x, screen_y: Screen coordinates
            modifiers: List of modifier keys (['shift', 'ctrl'])
            button: 'left' or 'right'
        """
        if button == 'left':
            # Perform pick
            hit = self._pick_at_screen_pos(screen_x, screen_y)
            
            if hit:
                add_to_selection = 'shift' in modifiers
                self.selection.select_polyform(hit['mesh_id'], add=add_to_selection)
            else:
                # Clicked empty space
                if 'shift' not in modifiers:
                    self.selection.clear_selection()
            
            self.dragging = True
            self.drag_start = (screen_x, screen_y)
        
        elif button == 'right':
            # Context menu
            hit = self._pick_at_screen_pos(screen_x, screen_y)
            if self.context_menu_callback:
                self.context_menu_callback(hit, screen_x, screen_y)
    
    def handle_mouse_release(self, screen_x: int, screen_y: int):
        """Handle mouse release"""
        self.dragging = False
    
    def handle_mouse_move(self, screen_x: int, screen_y: int):
        """Update hover highlighting"""
        hit = self._pick_at_screen_pos(screen_x, screen_y)
        if hit:
            new_hover = hit['mesh_id']
            if new_hover != self.selection.hover_highlight:
                self.selection.hover_highlight = new_hover
                # Could add subtle glow effect here
        else:
            self.selection.hover_highlight = None
    
    def _pick_at_screen_pos(self, screen_x: int, screen_y: int) -> Optional[Dict]:
        """Internal: perform raycasting at screen position"""
        try:
            # Get camera matrices from view widget
            proj_matrix = self._get_projection_matrix()
            view_matrix = self._get_view_matrix()
            
            if proj_matrix is None or view_matrix is None:
                return None
            
            # Convert screen coords to ray
            viewport = self._get_viewport()
            ray_origin, ray_dir = self.raycaster.screen_to_ray(
                screen_x, screen_y,
                viewport,
                view_matrix,
                proj_matrix
            )
            
            # Cast ray through all polyforms
            closest_hit = None
            min_distance = float('inf')
            
            for polyform in self.assembly.get_all_polyforms():
                hit = self._pick_polyform(polyform, ray_origin, ray_dir)
                
                if hit and hit['distance'] < min_distance:
                    min_distance = hit['distance']
                    hit['mesh_id'] = polyform['id']
                    closest_hit = hit
            
            return closest_hit
        
        except Exception as e:
            print(f"Error in pick: {e}")
            return None
    
    def _pick_polyform(self, polyform: Dict, ray_origin: np.ndarray,
                      ray_dir: np.ndarray) -> Optional[Dict]:
        """Try to pick a single polyform"""
        # Get mesh data
        if 'mesh_data' in polyform:
            mesh_data = polyform['mesh_data']
            
            # Try BVH-accelerated raycasting first
            if hasattr(mesh_data, 'vertices') and hasattr(mesh_data, 'faces'):
                # Check if we can use bvh3d.TriangleCollisionDetector for acceleration
                try:
                    from bvh3d import TriangleCollisionDetector
                    detector = TriangleCollisionDetector(mesh_data)
                    detector.build_bvh()
                    hit = detector.raycast(ray_origin, ray_dir)
                    if hit:
                        return hit
                except Exception:
                    # Fallback to naive raycasting
                    pass
            
            # Fallback: handle both MeshData objects and dicts
            if hasattr(mesh_data, 'vertices') and hasattr(mesh_data, 'faces'):
                vertices = mesh_data.vertices
                faces = mesh_data.faces
            elif isinstance(mesh_data, dict):
                vertices = np.array(mesh_data.get('vertices', []))
                faces = np.array(mesh_data.get('faces', []))
            else:
                return None
            
            if len(vertices) == 0 or len(faces) == 0:
                return None
            
            return self.raycaster.closest_hit(ray_origin, ray_dir, vertices, faces)
        
        # Fallback: use 2D polygon vertices as point cloud
        vertices = polyform.get('vertices', [])
        if not vertices:
            return None
        
        vertices_3d = []
        for v in vertices:
            if isinstance(v, (list, tuple)):
                if len(v) == 2:
                    vertices_3d.append([v[0], v[1], 0.0])
                else:
                    vertices_3d.append(v[:3])
            else:
                vertices_3d.append(v)
        
        vertices_3d = np.array(vertices_3d, dtype=float)
        
        # Create simple triangulation (fan from center)
        if len(vertices_3d) < 3:
            return None
        
        faces = []
        for i in range(1, len(vertices_3d) - 1):
            faces.append([0, i, i + 1])
        
        faces = np.array(faces, dtype=int)
        
        return self.raycaster.closest_hit(ray_origin, ray_dir, vertices_3d, faces)
    
    def _get_projection_matrix(self) -> Optional[np.ndarray]:
        """Get projection matrix from view widget"""
        try:
            if hasattr(self.view_widget, 'projectionMatrix'):
                proj_qmatrix = self.view_widget.projectionMatrix()
                # Convert QMatrix4x4 to numpy
                return self._qmatrix_to_numpy(proj_qmatrix)
            elif hasattr(self.view_widget, 'opts'):
                # Fallback for pyqtgraph GLViewWidget
                # Use perspective projection from camera parameters
                distance = self.view_widget.opts.get('distance', 10.0)
                fov = self.view_widget.opts.get('fov', 60.0)
                center = self.view_widget.opts.get('center')
                
                # Get actual viewport dimensions for correct aspect ratio
                viewport_width, viewport_height = self._get_viewport()
                aspect = viewport_width / max(viewport_height, 1)  # Prevent division by zero
                near = 0.1
                far = 1000.0
                f = 1.0 / np.tan(np.radians(fov) / 2.0)
                
                proj = np.array([
                    [f/aspect, 0, 0, 0],
                    [0, f, 0, 0],
                    [0, 0, (far+near)/(near-far), -1],
                    [0, 0, (2*far*near)/(near-far), 0]
                ], dtype=np.float32)
                return proj
        except Exception as e:
            print(f"Error getting projection matrix: {e}")
        return None
    
    def _get_view_matrix(self) -> Optional[np.ndarray]:
        """Get view matrix from view widget"""
        try:
            if hasattr(self.view_widget, 'viewMatrix'):
                view_qmatrix = self.view_widget.viewMatrix()
                return self._qmatrix_to_numpy(view_qmatrix)
            elif hasattr(self.view_widget, 'opts'):
                # Fallback: construct from pyqtgraph camera options
                center = self.view_widget.opts.get('center')
                distance = self.view_widget.opts.get('distance', 10.0)
                elevation = self.view_widget.opts.get('elevation', 30.0)
                azimuth = self.view_widget.opts.get('azimuth', 45.0)
                
                # Convert spherical to cartesian
                elev_rad = np.radians(elevation)
                azim_rad = np.radians(azimuth)
                
                x = distance * np.cos(elev_rad) * np.cos(azim_rad)
                y = distance * np.cos(elev_rad) * np.sin(azim_rad)
                z = distance * np.sin(elev_rad)
                
                if center:
                    cx, cy, cz = center.x(), center.y(), center.z()
                else:
                    cx, cy, cz = 0, 0, 0
                
                eye = np.array([cx + x, cy + y, cz + z])
                target = np.array([cx, cy, cz])
                up = np.array([0, 0, 1])
                
                # LookAt matrix
                f = target - eye
                f = f / (np.linalg.norm(f) + 1e-10)
                
                s = np.cross(f, up)
                s = s / (np.linalg.norm(s) + 1e-10)
                
                u = np.cross(s, f)
                
                view = np.array([
                    [s[0], s[1], s[2], -np.dot(s, eye)],
                    [u[0], u[1], u[2], -np.dot(u, eye)],
                    [-f[0], -f[1], -f[2], np.dot(f, eye)],
                    [0, 0, 0, 1]
                ], dtype=np.float32)
                return view
        except Exception as e:
            print(f"Error getting view matrix: {e}")
        return None
    
    def _qmatrix_to_numpy(self, qmatrix) -> np.ndarray:
        """Convert QMatrix4x4 to numpy array"""
        try:
            # Try to get data
            if hasattr(qmatrix, 'data'):
                return np.array(qmatrix.data()).reshape(4, 4)
            elif hasattr(qmatrix, '__getitem__'):
                data = []
                for i in range(16):
                    data.append(qmatrix[i])
                return np.array(data).reshape(4, 4)
        except Exception:
            pass
        
        # Fallback: identity matrix
        return np.eye(4)
    
    def _get_viewport(self) -> Tuple[int, int]:
        """Get viewport dimensions"""
        try:
            if hasattr(self.view_widget, 'width') and hasattr(self.view_widget, 'height'):
                return (self.view_widget.width(), self.view_widget.height())
        except Exception:
            pass
        return (800, 600)  # Fallback
