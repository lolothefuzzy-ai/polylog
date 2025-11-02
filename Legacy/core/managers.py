import json
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# -------------------- Simple Spatial Hash -----------------------

class _SimpleSpatialHash:
    """Lightweight spatial hash for vertex proximity queries"""
    def __init__(self, cell_size: float = 0.25):
        self.cell_size = float(cell_size)
        self.grid: Dict[Tuple[int, int, int], List[Tuple[str, int, np.ndarray]]] = {}
    
    def _cell_key(self, point: np.ndarray) -> Tuple[int, int, int]:
        return tuple(int(p / self.cell_size) for p in point[:3])
    
    def clear(self):
        self.grid.clear()
    
    def insert_vertices(self, poly_id: str, vertices: List[List[float]]):
        for idx, v in enumerate(vertices):
            pt = np.array(v, dtype=float)
            key = self._cell_key(pt)
            if key not in self.grid:
                self.grid[key] = []
            self.grid[key].append((poly_id, idx, pt))
    
    def query_neighbors(self, point: np.ndarray, radius: float) -> List[Tuple[str, int, np.ndarray]]:
        """Find vertices within radius of point"""
        result = []
        center_key = self._cell_key(point)
        # Check neighboring cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    key = (center_key[0] + dx, center_key[1] + dy, center_key[2] + dz)
                    if key in self.grid:
                        for pid, idx, v in self.grid[key]:
                            if np.linalg.norm(v - point) <= radius:
                                result.append((pid, idx, v))
        return result

# --------------------------- Scalers ---------------------------

class Scaler:
    def __init__(self, name: str, signatures: List[str], fold_angle_rad: float, confidence: float):
        self.name = name
        self.signatures = set(signatures)  # e.g., {"4-4", "3-3", "3-4"}
        self._fold_angle = float(fold_angle_rad)
        self._confidence = float(confidence)

    def matches(self, signature: str) -> bool:
        return signature in self.signatures

    def get_fold_angle(self, poly1_id: str, edge1_idx: int, poly2_id: str, edge2_idx: int) -> float:
        # Could adjust by edge indices if needed; for now return constant per scaler
        return self._fold_angle

    def confidence(self) -> float:
        return self._confidence


# ------------------------ Memory Manager -----------------------

class RealMemoryManager:
    # PHASE 1 STABILIZATION: Prevent unbounded pattern recording memory growth
    _MAX_PATTERNS = 10000  # Enforce hard limit on stored patterns
    
    def __init__(self):
        # Preload some simple scalers
        self._scalers: Dict[str, Scaler] = {
            'square_pair': Scaler('square_pair', ['4-4'], np.pi / 2, 0.9),
            'triangle_pair': Scaler('triangle_pair', ['3-3'], 2 * np.pi / 3, 0.9),
            'triangle_square': Scaler('triangle_square', ['3-4', '4-3'], np.pi / 2, 0.8),
        }
        # Learned patterns: mapping context/ids to success rates
        self._successful_patterns: List[Dict[str, Any]] = []
        self._stable_patterns: List[Dict[str, Any]] = []

    def get_scaler_confidence(self, name: str) -> float:
        sc = self._scalers.get(name)
        return sc.confidence() if sc else 0.5

    def get_all_scalers(self) -> Dict[str, Scaler]:
        return self._scalers

    def get_scaler(self, name: str) -> Optional[Scaler]:
        return self._scalers.get(name)

    def record_success(self, signature: str, context: Dict[str, Any], score: float):
        """Record a successful placement. Enforces memory limits for high-n stability."""
        self._successful_patterns.append({'signature': signature, 'context': context, 'success_rate': float(score), 'ts': time.time()})
        
        # PHASE 1 STABILIZATION: Enforce max patterns limit (FIFO eviction)
        while len(self._successful_patterns) > self._MAX_PATTERNS:
            self._successful_patterns.pop(0)  # Remove oldest pattern

    def query_successful_patterns(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Return top-N generic suggestions based on context averages
        res = []
        avg = context.get('avg_sides', 4) or 4
        candidates = [int(max(3, min(8, round(avg)))), 3, 4, 5, 6]
        for s in candidates:
            res.append({'name': f'sides_{s}', 'next_polyform': {'type': 'polygon', 'sides': s}, 'success_rate': 0.6})
        return res

    def query_stable_patterns(self, composition: str) -> List[Dict[str, Any]]:
        """Query stable patterns matching a composition signature.
        
        This method can be extended to integrate with the StableLibrary
        for querying pre-known stable polyhedron configurations.
        Currently returns empty list as patterns are learned at runtime.
        """
        # Future: integrate with StableLibrary.query() for pre-known patterns
        # For now, rely on runtime learning via _successful_patterns
        return []


# ------------------------ Chain Manager ------------------------

class RealChainManager:
    def get_connected_components(self, assembly) -> List[List[Dict[str, Any]]]:
        # Build graph of polyform ids via bonds
        polyforms = {p['id']: p for p in assembly.get_all_polyforms()}
        adj: Dict[str, List[str]] = {pid: [] for pid in polyforms}
        for b in assembly.get_bonds():
            p1 = b.get('poly1_id'); p2 = b.get('poly2_id')
            if p1 in adj and p2 in adj:
                adj[p1].append(p2)
                adj[p2].append(p1)
        # BFS components
        seen = set()
        comps: List[List[Dict[str, Any]]] = []
        for pid in polyforms:
            if pid in seen:
                continue
            q = [pid]; seen.add(pid); comp_ids = []
            while q:
                cur = q.pop(0)
                comp_ids.append(cur)
                for nb in adj.get(cur, []):
                    if nb not in seen:
                        seen.add(nb); q.append(nb)
            comps.append([polyforms[i] for i in comp_ids])
        return comps


# ----------------------- Fold Validator ------------------------

class RealFoldValidator:
    def __init__(self, min_edge_len: float = 1e-6, min_segment_distance: float = 1e-3,
                 use_3d_collision: bool = True):
        self.min_edge_len = float(min_edge_len)
        self.min_seg_dist = float(min_segment_distance)
        self.use_bvh = True
        self.use_3d_collision = use_3d_collision
        self.collision_cache: Dict[str, Any] = {}  # Cache BVH builds for performance
        
        # Try to import 3D collision detection
        try:
            from polygon_utils import get_polyform_mesh

            from bvh3d import TriangleCollisionDetector
            self._collision_detector_cls = TriangleCollisionDetector
            self._get_mesh_fn = get_polyform_mesh
            self._3d_available = True
        except ImportError:
            self._3d_available = False

    def _segments(self, poly: Dict[str, Any]) -> List[Tuple[np.ndarray, np.ndarray]]:
        verts = np.array(poly.get('vertices', []), dtype=float)
        n = len(verts)
        return [(verts[i], verts[(i+1) % n]) for i in range(n)] if n >= 2 else []

    def _seg_distance(self, p1: np.ndarray, p2: np.ndarray, q1: np.ndarray, q2: np.ndarray) -> float:
        # Minimum distance between two line segments in 3D
        # Algorithm from http://geomalgorithms.com/a07-_distance.html
        u = p2 - p1
        v = q2 - q1
        w0 = p1 - q1
        a = np.dot(u, u)
        b = np.dot(u, v)
        c = np.dot(v, v)
        d = np.dot(u, w0)
        e = np.dot(v, w0)
        D = a*c - b*b
        sc, sN, sD = 0.0, 0.0, D
        tc, tN, tD = 0.0, 0.0, D
        SMALL = 1e-12
        if D < SMALL:
            sN = 0.0
            sD = 1.0
            tN = e
            tD = c
        else:
            sN = (b*e - c*d)
            tN = (a*e - b*d)
            if sN < 0.0:
                sN = 0.0
                tN = e
                tD = c
            elif sN > sD:
                sN = sD
                tN = e + b
                tD = c
        if tN < 0.0:
            tN = 0.0
            if -d < 0.0:
                sN = 0.0
            elif -d > a:
                sN = sD
            else:
                sN = -d
                sD = a
        elif tN > tD:
            tN = tD
            if (-d + b) < 0.0:
                sN = 0
            elif (-d + b) > a:
                sN = sD
            else:
                sN = (-d + b)
                sD = a
        sc = 0.0 if abs(sN) < SMALL else sN / sD
        tc = 0.0 if abs(tN) < SMALL else tN / tD
        dP = w0 + (sc * u) - (tc * v)
        return float(np.linalg.norm(dP))

    def validate_fold_3d(self, polyform: Dict[str, Any], angle: float, edge_idx: int, 
                        assembly) -> Dict[str, Any]:
        """
        Validate a fold operation using 3D collision detection.
        
        Args:
            polyform: The polyform being folded
            angle: Fold angle in radians
            edge_idx: Index of the edge being folded around
            assembly: Assembly containing all polyforms
        
        Returns:
            Dict with 'is_valid' bool and optional 'reason' string
        """
        if not self._3d_available or not self.use_3d_collision:
            # Fall back to 2D validation
            return self.validate_fold(assembly)
        
        if not polyform.get('has_3d_mesh'):
            # No 3D mesh, use 2D validation
            return self.validate_fold(assembly)
        
        try:
            # Get mesh for this polyform
            mesh = self._get_mesh_fn(polyform)
            if mesh is None:
                return {'is_valid': True}  # No mesh to check
            
            # TODO: Apply fold transform to mesh
            # For now, just check current mesh for self-intersection
            detector = self._collision_detector_cls(mesh)
            detector.build_bvh()
            
            # Check self-intersection
            if detector.check_self_intersection():
                return {'is_valid': False, 'reason': 'self_intersection'}
            
            # Check collision with other polyforms in assembly
            for other_poly in assembly.get_all_polyforms():
                if other_poly['id'] == polyform['id']:
                    continue
                
                if not other_poly.get('has_3d_mesh'):
                    continue
                
                other_mesh = self._get_mesh_fn(other_poly)
                if other_mesh is None:
                    continue
                
                other_detector = self._collision_detector_cls(other_mesh)
                other_detector.build_bvh()
                
                if detector.check_collision(other_detector):
                    return {'is_valid': False, 'reason': 'mesh_collision'}
            
            return {'is_valid': True}
            
        except Exception as e:
            # On error, fall back to conservative validation
            import logging
            logging.warning(f"3D collision detection failed: {e}, falling back to 2D")
            return self.validate_fold(assembly)
    
    def validate_fold(self, assembly) -> Dict[str, Any]:
        # Check edge lengths and minimum distances
        polys = assembly.get_all_polyforms()
        # Check min edge length
        for poly in polys:
            segs = self._segments(poly)
            for s in segs:
                if np.linalg.norm(s[1] - s[0]) < self.min_edge_len:
                    return {'is_valid': False, 'reason': 'degenerate_edge'}
        # Check segment distances via BVH broad-phase when available
        bonds = assembly.get_bonds()
        bonded_set = set()
        for b in bonds:
            bonded_set.add((b['poly1_id'], b['edge1_idx']))
            bonded_set.add((b['poly2_id'], b['edge2_idx']))
        
        segmap: Dict[str, List[Tuple[int, np.ndarray, np.ndarray]]] = {}
        for poly in polys:
            verts = np.array(poly.get('vertices', []), dtype=float)
            n = len(verts)
            segmap[poly['id']] = [(i, verts[i], verts[(i+1) % n]) for i in range(n)]
        
        if self.use_bvh and hasattr(self, 'workspace'):
            # Fallback if no workspace attached
            pass
        
        # Iterate segments and query overlaps to avoid O(E^2)
        for pid, segs in segmap.items():
            for (e1, p1, p2) in segs:
                # Skip bonded
                if (pid, e1) in bonded_set:
                    continue
                mins = np.minimum(p1, p2)
                maxs = np.maximum(p1, p2)
                candidates: List[Tuple[str, int]] = []
                if hasattr(assembly, 'workspace') and hasattr(assembly.workspace, 'query_edge_overlaps'):
                    try:
                        candidates = assembly.workspace.query_edge_overlaps(mins, maxs)
                    except Exception:
                        candidates = []
                else:
                    # No BVH: degrade to checking all
                    for pid2, segs2 in segmap.items():
                        for (e2, q1, q2) in segs2:
                            candidates.append((pid2, e2))
                # Narrow phase
                for (pid2, e2) in candidates:
                    if pid2 == pid and abs(e1 - e2) <= 1:
                        continue
                    if (pid2, e2) in bonded_set:
                        continue
                    # Get actual segment
                    for (idx, q1, q2) in segmap[pid2]:
                        if idx == e2:
                            dist = self._seg_distance(p1, p2, q1, q2)
                            if dist < self.min_seg_dist:
                                return {'is_valid': False, 'reason': 'segment_collision'}
                            break
        return {'is_valid': True}


# --------------------- Workspace Manager -----------------------

class RealWorkspaceManager:
    def __init__(self, cell_size: float = 0.25, snap_tol: float = 1e-3):
        self._events: List[Dict[str, Any]] = []
        # Simple spatial hash for vertex snapping
        self.spatial = _SimpleSpatialHash(cell_size=cell_size)
        self.snap_tol = float(snap_tol)

    def update_bond_visualization(self, bond: Dict[str, Any]):
        self._events.append({'type': 'bond', 'bond': bond, 'ts': time.time()})

    def trigger_decay_animation(self, assembly, new_polyforms: List[str]):
        self._events.append({'type': 'decay', 'new_polyforms': new_polyforms, 'ts': time.time()})

    def render(self):
        """Render hook for external visualization systems.
        
        This method is called by the workspace to trigger rendering updates.
        In GUI contexts, this is typically connected to the 3D OpenGL renderer.
        In CLI/API contexts, this may trigger ASCII art or JSON state dumps.
        """
        # Implementation provided by subclass (e.g., GUIWorkspaceManager)
        pass
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to workspace coordinates.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            
        Returns:
            (world_x, world_y) tuple
            
        Note:
            Default implementation assumes 1:1 mapping.
            Subclasses (e.g., GUIWorkspaceManager) should override with proper
            camera/viewport transformations.
        """
        # Default: 1:1 mapping
        return (screen_x, screen_y)
    
    def contains_point(self, screen_x: float, screen_y: float) -> bool:
        """Check if screen point is within workspace bounds.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            
        Returns:
            True if point is in workspace
        """
        # Default: always valid
        return True
    
    def add_polyform(self, polyform: Dict[str, Any]) -> bool:
        """Add a polyform to the workspace.
        
        Args:
            polyform: Polyform dictionary
            
        Returns:
            True if added successfully
            
        Note:
            This is a hook for drag-drop integration.
            Actual implementation should delegate to assembly manager.
        """
        # Default: no-op, subclass should override
        return False

    # ---- Spatial post-processing ----
    def register_assembly(self, assembly):
        self.spatial.clear()
        for p in assembly.get_all_polyforms():
            self.spatial.insert_vertices(p['id'], p.get('vertices', []))
        # Edge BVH would go here if needed (currently optional)
        self._edge_bvh = None

    def postprocess_assembly(self, assembly):
        # Snap near-coincident vertices and auto-bond aligned edges
        self._snap_vertices(assembly)
        self._auto_bond_edges(assembly)

    def _snap_vertices(self, assembly):
        changed = False
        for p in assembly.get_all_polyforms():
            verts = np.array(p.get('vertices', []), dtype=float)
            for i, v in enumerate(verts):
                neigh = self.spatial.query_neighbors(v, self.snap_tol)
                for (pid, vidx, pv) in neigh:
                    if pid == p['id'] and vidx == i:
                        continue
                    # Snap to existing point
                    verts[i] = pv
                    changed = True
                    break
            if changed:
                p['vertices'] = verts.tolist()
        if changed:
            self.register_assembly(assembly)

    def _auto_bond_edges(self, assembly):
        # For each pair of polys, if an edge pair is coincident and anti-parallel, create a bond
        polys = assembly.get_all_polyforms()
        ids = [p['id'] for p in polys]
        id_to_poly = {p['id']: p for p in polys}
        existing = set()
        for b in assembly.get_bonds():
            existing.add((b['poly1_id'], b['edge1_idx'], b['poly2_id'], b['edge2_idx']))
            existing.add((b['poly2_id'], b['edge2_idx'], b['poly1_id'], b['edge1_idx']))
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                p1 = id_to_poly[ids[i]]; p2 = id_to_poly[ids[j]]
                e1s = self._edges(p1); e2s = self._edges(p2)
                for idx1, (a1, b1) in enumerate(e1s):
                    for idx2, (a2, b2) in enumerate(e2s):
                        # Check endpoints near-coincident
                        if (np.linalg.norm(a1 - b2) < self.snap_tol and np.linalg.norm(b1 - a2) < self.snap_tol) or \
                           (np.linalg.norm(a1 - a2) < self.snap_tol and np.linalg.norm(b1 - b2) < self.snap_tol):
                            # Check direction anti-parallel
                            v1 = b1 - a1; v2 = b2 - a2
                            if np.linalg.norm(v1) < 1e-8 or np.linalg.norm(v2) < 1e-8:
                                continue
                            v1n = v1/np.linalg.norm(v1); v2n = v2/np.linalg.norm(v2)
                            if abs(np.dot(v1n, v2n)) > 0.98:  # parallel or anti-parallel
                                key = (p1['id'], idx1, p2['id'], idx2)
                                if key not in existing:
                                    bond = {'poly1_id': p1['id'], 'edge1_idx': idx1, 'poly2_id': p2['id'], 'edge2_idx': idx2}
                                    assembly.add_bond(bond)
                                    self.update_bond_visualization(bond)
                                    existing.add(key)

    def _edges(self, poly: Dict[str, Any]) -> List[Tuple[np.ndarray, np.ndarray]]:
        verts = np.array(poly.get('vertices', []), dtype=float)
        n = len(verts)
        return [(verts[i], verts[(i+1) % n]) for i in range(n)]

    # Expose BVH query for validator
    def query_edge_overlaps(self, mins: np.ndarray, maxs: np.ndarray) -> List[Tuple[str, int]]:
        try:
            from bvh import query_overlaps
            ids: List[int] = []
            query_overlaps(self._edge_bvh, (mins, maxs), ids, pad=0.0)
            return [self._edge_refs[i] for i in ids]
        except Exception:
            return []

    def drain_events(self) -> List[Dict[str, Any]]:
        ev = self._events
        self._events = []
        return ev


# ------------------- Provenance (JSON log) --------------------

class RealProvenanceTracker:
    def __init__(self, path: str = 'provenance_log.jsonl'):
        self.path = path
        self._fh = None
        try:
            self._fh = open(self.path, 'a', encoding='utf-8')
        except Exception:
            self._fh = None

    def log_placement(self, result: Any):
        rec = {
            'ts': time.time(),
            'event': 'placement',
            'success': getattr(result, 'success', False) if not isinstance(result, dict) else result.get('success'),
            'decay': getattr(result, 'decay_triggered', False) if not isinstance(result, dict) else result.get('decay_triggered'),
            'total_time': getattr(result, 'total_time', None) if not isinstance(result, dict) else result.get('total_time'),
        }
        try:
            if self._fh:
                self._fh.write(json.dumps(rec) + '\n')
                self._fh.flush()
        except Exception:
            pass

    def log_validation(self, report: Dict[str, Any]):
        rec = {
            'ts': time.time(),
            'event': 'validation',
            **report
        }
        try:
            if self._fh:
                self._fh.write(json.dumps(rec) + '\n')
                self._fh.flush()
        except Exception:
            pass

    def __del__(self):
        try:
            if self._fh:
                self._fh.close()
        except Exception:
            pass
