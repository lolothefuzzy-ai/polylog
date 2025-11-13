import json
import os
import uuid
from typing import Any, Dict, List, Optional

from polygon_utils import create_polygon


# Lazy normalization helper to avoid importing GUI modules at module import time
def _normalize_polyform_local(polyform: Dict[str, Any]) -> Dict[str, Any]:
    """
    Try to use the canonical normalize_polyform from gui.polyform_adapter if available.
    Fall back to a minimal normalization (ensure id and 3D vertices) if the adapter
    cannot be imported (headless/test environments).
    """
    try:
        from gui.polyform_adapter import normalize_polyform
        return normalize_polyform(polyform)
    except Exception:
        # Minimal fallback normalization
        pf = dict(polyform)
        pf_id = pf.get('id') or str(uuid.uuid4())
        pf['id'] = pf_id
        verts = []
        for v in pf.get('vertices', []):
            if isinstance(v, (list, tuple)):
                if len(v) == 2:
                    verts.append((float(v[0]), float(v[1]), 0.0))
                else:
                    verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
        if verts:
            pf['vertices'] = verts
        return pf

# Library of pre-arranged polyform assemblies (nets), placed on z=0 plane.
# Uses unit edge length (~1.0); snapping will fix small mismatches.

def make_square(center=(0.0,0.0,0.0)) -> Dict[str, Any]:
    return create_polygon(4, center)

def make_triangle(center=(0.0,0.0,0.0)) -> Dict[str, Any]:
    return create_polygon(3, center)


def add_cube_net(assembly, origin=(0.0,0.0,0.0)) -> List[str]:
    # Cross layout:
    #     [ ]
    # [ ][ ][ ][ ]
    #     [ ]
    ids: List[str] = []
    x0, y0, z0 = origin
    d = 1.0  # center spacing approx one edge length
    centers = [
        (x0 - d, y0, z0),
        (x0, y0, z0),
        (x0 + d, y0, z0),
        (x0 + 2*d, y0, z0),
        (x0, y0 + d, z0),
        (x0, y0 - d, z0),
    ]
    for c in centers:
        p = make_square(c)
        assembly.add_polyform(p)  # This adds the 'id' key
        ids.append(p.get('id', ''))  # Safe access
    return ids


def add_triangular_prism_net(assembly, origin=(0.0,0.0,0.0)) -> List[str]:
    # Net: 3 squares in a row with triangles on ends
    ids: List[str] = []
    x0, y0, z0 = origin
    d = 1.0
    squares = [(x0 - d, y0, z0), (x0, y0, z0), (x0 + d, y0, z0)]
    for c in squares:
        p = make_square(c)
        assembly.add_polyform(p)  # This adds the 'id' key
        ids.append(p.get('id', ''))  # Safe access
    # Triangles at ends (above row)
    tri_left = make_triangle((x0 - d, y0 + d, z0))
    tri_right = make_triangle((x0 + d, y0 + d, z0))
    assembly.add_polyform(tri_left)
    ids.append(tri_left.get('id', ''))
    assembly.add_polyform(tri_right)
    ids.append(tri_right.get('id', ''))
    return ids


# ==================== Library Manager ====================

class PolyformLibraryManager:
    """
    Manages a persistent library of polyforms and assemblies.
    
    Features:
    - Save/load individual polyforms
    - Save/load complete assemblies
    - ID-based retrieval for drag-drop
    - Integration with thumbnail renderer
    - JSON-based storage
    """
    
    def __init__(self, library_dir: str = "polyform_library"):
        """
        Initialize library manager.
        
        Args:
            library_dir: Directory to store library files
        """
        self.library_dir = library_dir
        os.makedirs(library_dir, exist_ok=True)
        
        # In-memory cache
        self._polyforms: Dict[str, Dict[str, Any]] = {}
        self._assemblies: Dict[str, Dict[str, Any]] = {}
        
        # Load existing library
        self._load_library()
    
    def _load_library(self):
        """Load all polyforms and assemblies from disk."""
        # Load polyforms
        polyforms_file = os.path.join(self.library_dir, 'polyforms.json')
        if os.path.exists(polyforms_file):
            try:
                with open(polyforms_file, 'r') as f:
                    self._polyforms = json.load(f)
                # Normalize loaded polyforms to canonical form
                for pid, pf in list(self._polyforms.items()):
                    try:
                        norm = _normalize_polyform_local(pf)
                        self._polyforms[pid] = norm
                    except Exception:
                        # Keep original if normalization fails
                        pass
            except Exception as e:
                print(f"Warning: Failed to load polyforms: {e}")
        
        # Load assemblies
        assemblies_file = os.path.join(self.library_dir, 'assemblies.json')
        if os.path.exists(assemblies_file):
            try:
                with open(assemblies_file, 'r') as f:
                    self._assemblies = json.load(f)
                # Normalize any polyforms embedded in assemblies
                for aid, a in list(self._assemblies.items()):
                    try:
                        if isinstance(a, dict) and 'polyforms' in a:
                            new_pf_list = []
                            for pf in a.get('polyforms', []):
                                try:
                                    new_pf_list.append(_normalize_polyform_local(pf))
                                except Exception:
                                    new_pf_list.append(pf)
                            a['polyforms'] = new_pf_list
                            self._assemblies[aid] = a
                    except Exception:
                        pass
            except Exception as e:
                print(f"Warning: Failed to load assemblies: {e}")
    
    def _save_library(self):
        """Save all polyforms and assemblies to disk."""
        # Save polyforms
        polyforms_file = os.path.join(self.library_dir, 'polyforms.json')
        try:
            with open(polyforms_file, 'w') as f:
                json.dump(self._polyforms, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save polyforms: {e}")
        
        # Save assemblies
        assemblies_file = os.path.join(self.library_dir, 'assemblies.json')
        try:
            with open(assemblies_file, 'w') as f:
                json.dump(self._assemblies, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save assemblies: {e}")
    
    def add_polyform(self, polyform: Dict[str, Any], polyform_id: str = None) -> str:
        """
        Add a polyform to the library.
        
        Args:
            polyform: Polyform data dictionary
            polyform_id: Optional ID (generated if None)
            
        Returns:
            The polyform ID
        """
        # Normalize input (use adapter when available)
        norm_pf = _normalize_polyform_local(polyform)

        if polyform_id is None:
            polyform_id = norm_pf.get('id') or str(uuid.uuid4())

        # Ensure ID is set and consistent with normalized data
        norm_pf['id'] = polyform_id

        # Store in memory (use normalized copy)
        self._polyforms[polyform_id] = norm_pf.copy()
        
        # Save to disk
        self._save_library()
        
        return polyform_id
    
    def get_polyform(self, polyform_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a polyform by ID.
        
        Args:
            polyform_id: The polyform ID
            
        Returns:
            Polyform data or None if not found
        """
        return self._polyforms.get(polyform_id)
    
    def get_all_polyforms(self) -> Dict[str, Dict[str, Any]]:
        """Get all polyforms in the library."""
        return self._polyforms.copy()
    
    def remove_polyform(self, polyform_id: str) -> bool:
        """
        Remove a polyform from the library.
        
        Args:
            polyform_id: The polyform ID
            
        Returns:
            True if removed, False if not found
        """
        if polyform_id in self._polyforms:
            del self._polyforms[polyform_id]
            self._save_library()
            return True
        return False
    
    def add_assembly(self, assembly_data: Dict[str, Any], assembly_id: str = None) -> str:
        """
        Add a complete assembly to the library.
        
        Args:
            assembly_data: Assembly data with polyforms list
            assembly_id: Optional ID (generated if None)
            
        Returns:
            The assembly ID
        """
        if assembly_id is None:
            assembly_id = assembly_data.get('id') or str(uuid.uuid4())

        # Ensure ID is set
        assembly_data['id'] = assembly_id

        # Normalize any polyforms embedded in assembly_data
        try:
            if 'polyforms' in assembly_data and isinstance(assembly_data['polyforms'], list):
                new_pf_list = []
                for pf in assembly_data['polyforms']:
                    try:
                        new_pf_list.append(_normalize_polyform_local(pf))
                    except Exception:
                        new_pf_list.append(pf)
                assembly_data['polyforms'] = new_pf_list
        except Exception:
            pass

        # Store in memory
        self._assemblies[assembly_id] = assembly_data.copy()
        
        # Save to disk
        self._save_library()
        
        return assembly_id
    
    def get_assembly(self, assembly_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an assembly by ID.
        
        Args:
            assembly_id: The assembly ID
            
        Returns:
            Assembly data or None if not found
        """
        return self._assemblies.get(assembly_id)
    
    def get_all_assemblies(self) -> Dict[str, Dict[str, Any]]:
        """Get all assemblies in the library."""
        return self._assemblies.copy()
    
    def remove_assembly(self, assembly_id: str) -> bool:
        """
        Remove an assembly from the library.
        
        Args:
            assembly_id: The assembly ID
            
        Returns:
            True if removed, False if not found
        """
        if assembly_id in self._assemblies:
            del self._assemblies[assembly_id]
            self._save_library()
            return True
        return False
    
    def search_polyforms(self, **criteria) -> List[Dict[str, Any]]:
        """
        Search polyforms by criteria.
        
        Args:
            **criteria: Search criteria (e.g., sides=4, type='polygon')
            
        Returns:
            List of matching polyforms
        """
        results = []
        
        for polyform in self._polyforms.values():
            match = True
            for key, value in criteria.items():
                if polyform.get(key) != value:
                    match = False
                    break
            
            if match:
                results.append(polyform.copy())
        
        return results
    
    def clear(self):
        """Clear all library data."""
        self._polyforms.clear()
        self._assemblies.clear()
        self._save_library()


# Global library instance
_global_library = None

def get_library(library_dir: str = "polyform_library") -> PolyformLibraryManager:
    """Get or create global library instance."""
    global _global_library
    
    if _global_library is None:
        _global_library = PolyformLibraryManager(library_dir)
    
    return _global_library
