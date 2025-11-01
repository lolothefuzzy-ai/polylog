"""
Assembly Manager - Handles saving and loading polygon assemblies.

Provides persistence for polygon designs to disk.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class AssemblyManager:
    """Manages assembly persistence (save/load)."""
    
    def __init__(self, storage_dir: str = "assemblies"):
        """Initialize assembly manager."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.current_assembly = None
        self.current_filename = None
    
    def new_assembly(self) -> Dict[str, Any]:
        """Create new assembly."""
        self.current_assembly = {
            'name': 'Untitled Assembly',
            'version': '1.0',
            'polygons': [],
            'metadata': {
                'created': str(Path.ctime.__doc__),
                'modified': str(Path.ctime.__doc__),
            }
        }
        self.current_filename = None
        return self.current_assembly
    
    def save_assembly(self, filename: Optional[str] = None) -> bool:
        """Save current assembly to disk."""
        if not self.current_assembly:
            return False
        
        if filename:
            self.current_filename = filename
        elif not self.current_filename:
            self.current_filename = "assembly.json"
        
        try:
            filepath = self.storage_dir / self.current_filename
            
            # Ensure .json extension
            if not filepath.suffix == '.json':
                filepath = filepath.with_suffix('.json')
            
            with open(filepath, 'w') as f:
                json.dump(self.current_assembly, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving assembly: {e}")
            return False
    
    def load_assembly(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load assembly from disk."""
        try:
            filepath = self.storage_dir / filename
            
            # Ensure .json extension
            if not filepath.suffix == '.json':
                filepath = filepath.with_suffix('.json')
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                self.current_assembly = json.load(f)
            
            self.current_filename = filename
            return self.current_assembly
        except Exception as e:
            print(f"Error loading assembly: {e}")
            return None
    
    def add_polygon_to_assembly(self, polygon: Dict[str, Any]) -> bool:
        """Add polygon to current assembly."""
        if not self.current_assembly:
            return False
        
        if 'polygons' not in self.current_assembly:
            self.current_assembly['polygons'] = []
        
        # Normalize the polygon into canonical form when possible
        try:
            from gui.polyform_adapter import normalize_polyform
            norm = normalize_polyform(polygon)
            poly_data = norm
        except Exception:
            # Minimal fallback: keep essential fields and ensure 3D vertices
            poly_data = {
                'sides': polygon.get('sides'),
                'vertices': [],
                'position': polygon.get('position', [0, 0, 0]),
                'rotation': polygon.get('rotation', 0),
            }
            verts = []
            for v in polygon.get('vertices', []):
                if isinstance(v, (list, tuple)):
                    if len(v) == 2:
                        verts.append((float(v[0]), float(v[1]), 0.0))
                    else:
                        verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
            if verts:
                poly_data['vertices'] = verts

        self.current_assembly['polygons'].append(poly_data)
        return True
    
    def get_polygons(self) -> List[Dict[str, Any]]:
        """Get all polygons from current assembly."""
        if not self.current_assembly:
            return []
        
        return self.current_assembly.get('polygons', [])
    
    def clear_assembly(self) -> bool:
        """Clear current assembly."""
        if self.current_assembly:
            self.current_assembly['polygons'] = []
            return True
        return False
    
    def list_assemblies(self) -> List[str]:
        """List all saved assemblies."""
        try:
            assemblies = []
            for file in self.storage_dir.glob("*.json"):
                assemblies.append(file.name)
            return sorted(assemblies)
        except Exception:
            return []
    
    def delete_assembly(self, filename: str) -> bool:
        """Delete assembly from disk."""
        try:
            filepath = self.storage_dir / filename
            if filepath.exists():
                filepath.unlink()
                return True
            return False
        except Exception:
            return False
    
    def export_assembly(self, filename: str, format: str = 'json') -> bool:
        """Export assembly to file."""
        if not self.current_assembly:
            return False
        
        try:
            filepath = Path(filename)
            
            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(self.current_assembly, f, indent=2)
            elif format == 'csv':
                return self._export_csv(filepath)
            else:
                return False
            
            return True
        except Exception as e:
            print(f"Error exporting assembly: {e}")
            return False
    
    def _export_csv(self, filepath: Path) -> bool:
        """Export assembly as CSV."""
        try:
            with open(filepath, 'w') as f:
                # Write header
                f.write("polygon_id,sides,x,y,z,rotation\n")
                
                # Write polygon data
                for i, poly in enumerate(self.current_assembly.get('polygons', [])):
                    sides = poly.get('sides', 0)
                    pos = poly.get('position', [0, 0, 0])
                    rotation = poly.get('rotation', 0)
                    
                    f.write(f"{i},{sides},{pos[0]},{pos[1]},{pos[2]},{rotation}\n")
            
            return True
        except Exception:
            return False
    
    def set_assembly_name(self, name: str) -> None:
        """Set assembly name."""
        if self.current_assembly:
            self.current_assembly['name'] = name
    
    def get_assembly_name(self) -> Optional[str]:
        """Get current assembly name."""
        if self.current_assembly:
            return self.current_assembly.get('name', 'Untitled')
        return None
