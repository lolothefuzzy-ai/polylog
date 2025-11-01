import json
import time
import uuid
from typing import Any, Dict, List, Optional


class StableLibrary:
    def __init__(self, path: str = 'stable_polyforms.jsonl'):
        self.path = path
        # Ensure file exists
        try:
            open(self.path, 'a', encoding='utf-8').close()
        except Exception:
            pass

    # ---------------------- Internal helpers ----------------------
    def _normalize_polyform_for_save(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Make a JSON-serializable copy of a polyform.
        - Ensures mesh is serialized as dict if present
        - Ensures has_3d_mesh flag is consistent
        """
        q = dict(p)
        # Normalize mesh field
        mesh = q.get('mesh')
        if mesh is not None:
            # If mesh is an object with to_dict, convert
            try:
                if hasattr(mesh, 'to_dict') and callable(mesh.to_dict):
                    q['mesh'] = mesh.to_dict()
                elif isinstance(mesh, dict):
                    # Already good
                    pass
                else:
                    # Unknown type: drop to avoid JSON errors
                    q['mesh'] = None
            except Exception:
                q['mesh'] = None
        # Set/normalize flags
        q['has_3d_mesh'] = bool(q.get('mesh')) or bool(q.get('has_3d_mesh'))
        if 'mesh_thickness' in q:
            try:
                q['mesh_thickness'] = float(q['mesh_thickness'])
            except Exception:
                del q['mesh_thickness']
        # Ensure vertices are basic types
        if 'vertices' in q:
            try:
                q['vertices'] = [[float(c) for c in v[:3]] for v in q['vertices']]
            except Exception:
                # Leave as-is if conversion fails
                pass
        return q
    
    def _serialize_hinge_data(self, hinge_manager) -> Dict[str, Any]:
        """Serialize HingeManager data to JSON-serializable dict."""
        try:
            hinges_data = []
            for hinge in hinge_manager.graph.hinges:
                if not hinge.is_active:
                    continue
                
                hinge_dict = {
                    'poly1_id': hinge.poly1_id,
                    'poly2_id': hinge.poly2_id,
                    'edge1_idx': int(hinge.edge1_idx),
                    'edge2_idx': int(hinge.edge2_idx),
                    'axis_start': hinge.axis_start.tolist(),
                    'axis_end': hinge.axis_end.tolist(),
                    'fold_angle': float(hinge.fold_angle),
                    'is_active': bool(hinge.is_active)
                }
                hinges_data.append(hinge_dict)
            
            return {
                'hinges': hinges_data,
                'version': '1.0'
            }
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to serialize hinge data: {e}")
            return {'hinges': [], 'version': '1.0'}
    
    def _deserialize_hinge_data(self, hinge_data: Dict[str, Any], id_map: Dict[str, str]):
        """Deserialize hinge data and remap IDs.
        
        Args:
            hinge_data: Serialized hinge data
            id_map: Mapping of old polyform IDs to new IDs
        
        Returns:
            List of hinge dicts with remapped IDs
        """
        import numpy as np
        
        hinges = []
        for hinge_dict in hinge_data.get('hinges', []):
            # Remap polyform IDs
            old_poly1 = hinge_dict['poly1_id']
            old_poly2 = hinge_dict['poly2_id']
            
            if old_poly1 not in id_map or old_poly2 not in id_map:
                continue  # Skip if mapping not found
            
            remapped_hinge = {
                'poly1_id': id_map[old_poly1],
                'poly2_id': id_map[old_poly2],
                'edge1_idx': hinge_dict['edge1_idx'],
                'edge2_idx': hinge_dict['edge2_idx'],
                'axis_start': np.array(hinge_dict['axis_start']),
                'axis_end': np.array(hinge_dict['axis_end']),
                'fold_angle': hinge_dict['fold_angle'],
                'is_active': hinge_dict.get('is_active', True)
            }
            hinges.append(remapped_hinge)
        
        return hinges

    # ---------------------- Save / Load ----------------------

    def save_assembly(self, assembly, name: Optional[str] = None, meta: Optional[Dict[str, Any]] = None,
                       hinge_manager=None) -> str:
        """Persist the current assembly (polyforms + bonds) as a stable entry.
        
        Args:
            assembly: Assembly object
            name: Optional name for this save
            meta: Optional metadata dict
            hinge_manager: Optional HingeManager instance to save hinge data
        
        Returns:
            Entry ID string
        """
        entry_id = str(uuid.uuid4())
        raw_polyforms = assembly.get_all_polyforms()
        polyforms = [self._normalize_polyform_for_save(p) for p in raw_polyforms]
        bonds = assembly.get_bonds()
        
        record = {
            'id': entry_id,
            'ts': time.time(),
            'name': name or f"assembly_{int(time.time())}",
            'n': len(polyforms),
            'polyforms': polyforms,
            'bonds': bonds,
            'meta': meta or {},
        }
        
        # Save hinge data if HingeManager provided
        if hinge_manager is not None:
            record['hinge_data'] = self._serialize_hinge_data(hinge_manager)
        try:
            with open(self.path, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(record) + '\n')
        except Exception:
            pass
        return entry_id

    def save_component(self, polyforms: List[Dict[str, Any]], bonds: List[Dict[str, Any]], name: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> str:
        entry_id = str(uuid.uuid4())
        polyforms_norm = [self._normalize_polyform_for_save(p) for p in polyforms]
        record = {
            'id': entry_id,
            'ts': time.time(),
            'name': name or f"component_{int(time.time())}",
            'n': len(polyforms_norm),
            'polyforms': polyforms_norm,
            'bonds': bonds,
            'meta': meta or {},
        }
        try:
            with open(self.path, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(record) + '\n')
        except Exception:
            pass
        return entry_id

    def list_entries(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    try:
                        obj = json.loads(line)
                        entries.append({'id': obj.get('id'), 'name': obj.get('name'), 'n': obj.get('n'), 'ts': obj.get('ts')})
                    except Exception:
                        continue
        except FileNotFoundError:
            pass
        return entries

    def list_full(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    try:
                        obj = json.loads(line)
                        rows.append(obj)
                    except Exception:
                        continue
        except FileNotFoundError:
            pass
        return rows

    def load_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Load entry from library, reconstructing 3D meshes if needed."""
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    try:
                        obj = json.loads(line)
                        if obj.get('id') == entry_id:
                            # Ensure polyforms have 3D mesh data
                            return self._restore_3d_meshes(obj)
                    except Exception:
                        continue
        except FileNotFoundError:
            return None
        return None
    
    def _restore_3d_meshes(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Restore 3D mesh data in polyforms, reconstructing if necessary."""
        from geometry3d import MeshData
        from polygon_utils import add_3d_mesh_to_polyform
        
        if 'polyforms' not in entry:
            return entry
        
        for polyform in entry['polyforms']:
            # Check if mesh needs to be restored
            if polyform.get('has_3d_mesh'):
                mesh_dict = polyform.get('mesh')
                
                if mesh_dict:
                    # Mesh data exists as dict, reconstruct MeshData object
                    try:
                        # Store dict for compatibility
                        if isinstance(mesh_dict, dict):
                            mesh_data = MeshData.from_dict(mesh_dict)
                            # Keep dict in polyform for JSON serialization
                            polyform['mesh'] = mesh_dict
                    except Exception as e:
                        print(f"Warning: Could not reconstruct mesh for {polyform.get('id')}: {e}")
                        # Fallback: regenerate from vertices
                        if polyform.get('vertices'):
                            try:
                                thickness = polyform.get('mesh_thickness', 0.15)
                                add_3d_mesh_to_polyform(polyform, thickness=thickness)
                            except Exception:
                                polyform['has_3d_mesh'] = False
            else:
                # No 3D mesh flag, but might have 3D vertices - regenerate if applicable
                if polyform.get('vertices'):
                    try:
                        thickness = polyform.get('mesh_thickness', 0.15)
                        add_3d_mesh_to_polyform(polyform, thickness=thickness)
                    except Exception:
                        pass  # Leave as 2D if regeneration fails
        
        return entry

    def add_entry_to_assembly(self, assembly, entry_id: str):
        """Instantiate saved polyforms into the given assembly with fresh ids.
        
        Preserves 3D mesh data and other properties.
        """
        entry = self.load_entry(entry_id)
        if not entry:
            return
        
        id_map: Dict[str, str] = {}
        
        # Instantiate polyforms with all their data
        for p in entry.get('polyforms', []):
            new_p = dict(p)  # Deep copy of polyform
            new_id = str(uuid.uuid4())
            id_map[p.get('id')] = new_id
            new_p['id'] = new_id
            
            # Preserve 3D mesh data
            if p.get('has_3d_mesh'):
                # Mesh dict was already loaded/reconstructed
                new_p['has_3d_mesh'] = True
                if 'mesh' in p:
                    new_p['mesh'] = dict(p['mesh']) if isinstance(p['mesh'], dict) else p['mesh']
                if 'mesh_thickness' in p:
                    new_p['mesh_thickness'] = p['mesh_thickness']
            
            assembly.add_polyform(new_p)
        
        # Recreate bonds with mapped ids, preserving fold angles
        for b in entry.get('bonds', []):
            mapped = {
                'poly1_id': id_map.get(b.get('poly1_id')),
                'edge1_idx': int(b.get('edge1_idx', 0)),
                'poly2_id': id_map.get(b.get('poly2_id')),
                'edge2_idx': int(b.get('edge2_idx', 0)),
                'fold_angle': float(b.get('fold_angle', 0.0))
            }
            if mapped['poly1_id'] and mapped['poly2_id']:
                assembly.add_bond(mapped)

    # ---------------------- Pruning ----------------------
    def _signature_from_polyforms(self, polys: List[Dict[str, Any]]) -> str:
        # Build S_id = S:axc_...
        counts: Dict[int, int] = {}
        for p in polys:
            s = int(p.get('sides', 0))
            if s >= 3:
                counts[s] = counts.get(s, 0) + 1
        parts = [f"{a}x{c}" for a, c in sorted(counts.items())]
        return "S:" + "_".join(parts)

    def prune_duplicates(self, keep: str = 'latest') -> Dict[str, int]:
        """Rewrite library keeping one entry per signature (S_id), default latest by ts.
        Returns stats of {'before': N, 'after': M, 'removed': R}.
        """
        rows = self.list_full()
        before = len(rows)
        grouped: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            sig = r.get('meta', {}).get('S_id') or self._signature_from_polyforms(r.get('polyforms', []))
            key = sig
            prev = grouped.get(key)
            if not prev:
                grouped[key] = r
            else:
                if keep == 'latest':
                    if float(r.get('ts', 0)) >= float(prev.get('ts', 0)):
                        grouped[key] = r
                else:
                    # keep earliest
                    if float(r.get('ts', 0)) <= float(prev.get('ts', 0)):
                        grouped[key] = r
        # Rewrite file
        try:
            with open(self.path, 'w', encoding='utf-8') as fh:
                for r in grouped.values():
                    fh.write(json.dumps(r) + '\n')
        except Exception:
            pass
        after = len(grouped)
        return {'before': before, 'after': after, 'removed': before - after}
