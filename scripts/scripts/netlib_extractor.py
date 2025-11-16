#!/usr/bin/env python3
"""
Netlib Polyhedra Extractor

Parses Netlib polyhedra files (0-114) and extracts:
- 5 Platonic solids
- 13 Archimedean solids
- 92 Johnson solids

Outputs:
- catalogs/tier1/polyhedra.jsonl (110 polyhedra with decompositions)
- catalogs/tier1/decompositions.json (attachment sequences)
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.request import urlopen
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Face:
    """Represents a polyhedron face."""
    id: int
    vertices: List[int]
    edges: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vertices": self.vertices,
            "edges": self.edges,
            "type": self._face_type()
        }

    def _face_type(self) -> str:
        """Determine face type from vertex count."""
        types = {3: "triangle", 4: "square", 5: "pentagon", 6: "hexagon",
                 7: "heptagon", 8: "octagon", 9: "nonagon", 10: "decagon"}
        return types.get(self.edges, f"polygon_{self.edges}")


@dataclass
class Polyhedron:
    """Represents a complete polyhedron."""
    symbol: str
    name: str
    netlib_id: int
    classification: str  # "platonic", "archimedean", "johnson"
    composition: str  # e.g., "6×b2"
    faces: List[Face]
    vertices: List[Tuple[float, float, float]]
    dihedral_angles: List[float]
    dihedral_edge_count: int
    symmetry_group: str
    euler_characteristic: int = 2
    compression_ratio: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "netlib_id": self.netlib_id,
            "classification": self.classification,
            "composition": self.composition,
            "faces": [f.to_dict() for f in self.faces],
            "vertices": self.vertices,
            "dihedral_angles": self.dihedral_angles,
            "dihedral_edge_count": self.dihedral_edge_count,
            "symmetry_group": self.symmetry_group,
            "euler_characteristic": self.euler_characteristic,
            "compression_ratio": self.compression_ratio
        }


class NetlibParser:
    """Parses Netlib polyhedra file format."""

    NETLIB_BASE_URL = "https://netlib.org/polyhedra"
    
    # Platonic solids (files 1-5)
    PLATONIC_IDS = {1: "Ω1", 2: "Ω2", 3: "Ω3", 4: "Ω4", 5: "Ω5"}
    
    # Archimedean solids (files 9-21, with George Hart corrections for some)
    ARCHIMEDEAN_IDS = {i: f"Ω{i-3}" for i in range(9, 22)}  # Ω6-Ω18
    
    # Johnson solids (files 22-114)
    JOHNSON_START_ID = 22
    JOHNSON_START_SYMBOL = 19  # Ω19 onwards

    # George Hart corrections needed for these files
    GEORGE_HART_CORRECTIONS = {66, 67, 68, 69, 70, 81, 108, 115}

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize parser with optional local cache."""
        self.cache_dir = cache_dir or Path("data/netlib_raw")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def parse_file(self, file_id: int) -> Optional[Polyhedron]:
        """Parse a single Netlib file."""
        try:
            content = self._fetch_file(file_id)
            if not content:
                return None
            
            parsed = self._parse_content(content, file_id)
            if parsed:
                parsed.symbol = self._get_symbol(file_id)
                parsed.classification = self._classify(file_id)
            return parsed
        except Exception as e:
            logger.error(f"Error parsing file {file_id}: {e}")
            return None

    def _fetch_file(self, file_id: int) -> Optional[str]:
        """Fetch Netlib file from cache or URL."""
        cache_file = self.cache_dir / str(file_id)
        
        # Try cache first
        if cache_file.exists():
            return cache_file.read_text()
        
        # Fetch from URL
        try:
            url = f"{self.NETLIB_BASE_URL}/{file_id}"
            logger.info(f"Fetching {url}")
            with urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
                cache_file.write_text(content)
                return content
        except Exception as e:
            logger.error(f"Failed to fetch file {file_id}: {e}")
            return None

    def _parse_content(self, content: str, file_id: int) -> Optional[Polyhedron]:
        """Parse Netlib file content."""
        lines = content.strip().split('\n')
        fields = self._extract_fields(lines)
        
        if not fields:
            return None
        
        name = fields.get('name', [f'Polyhedron_{file_id}'])[0]
        
        # Parse faces from :solid section
        solid_faces = self._parse_solid_faces(fields.get('solid', []))
        if not solid_faces:
            return None
        
        # Parse vertices
        vertices = self._parse_vertices(fields.get('vertices', []))
        
        # Parse dihedral angles
        dihedral_angles, dihedral_edge_count = self._parse_dihedral(fields.get('dih', []))
        
        # Determine composition
        face_types = {}
        for face in solid_faces:
            face_type = face.edges
            face_types[face_type] = face_types.get(face_type, 0) + 1
        
        composition = self._build_composition(face_types)
        symmetry_group = self._infer_symmetry(file_id, len(solid_faces))
        
        # Calculate compression ratio
        full_size = len(solid_faces) * 100 + len(vertices) * 24  # Rough estimate
        compressed_size = max(full_size // 10, 60)  # Assume 10:1 compression
        compression_ratio = full_size / compressed_size if compressed_size > 0 else 1.0
        
        return Polyhedron(
            symbol="",  # Will be set by caller
            name=name,
            netlib_id=file_id,
            classification="",  # Will be set by caller
            composition=composition,
            faces=solid_faces,
            vertices=vertices,
            dihedral_angles=dihedral_angles,
            dihedral_edge_count=dihedral_edge_count,
            symmetry_group=symmetry_group,
            compression_ratio=compression_ratio
        )

    def _extract_fields(self, lines: List[str]) -> Dict[str, List[str]]:
        """Extract Netlib fields from lines."""
        fields = {}
        current_field = None
        current_content = []
        
        for line in lines:
            if line.startswith(':'):
                if current_field:
                    fields[current_field] = current_content
                current_field = line[1:].strip()
                current_content = []
            elif current_field and line.strip() and not line.startswith(':'):
                current_content.append(line)
        
        if current_field:
            fields[current_field] = current_content
        
        return fields

    def _parse_solid_faces(self, solid_lines: List[str]) -> List[Face]:
        """Parse :solid section to extract faces."""
        if not solid_lines or len(solid_lines) < 1:
            return []
        
        faces = []
        face_id = 0
        
        # First line: face_count max_vertices_per_face
        header = solid_lines[0].split()
        if len(header) < 2:
            return []
        
        # Parse face definitions
        for line in solid_lines[1:]:
            parts = line.split()
            if not parts:
                continue
            
            try:
                vertex_count = int(parts[0])
                vertices = [int(p) for p in parts[1:vertex_count+1]]
                
                face = Face(
                    id=face_id,
                    vertices=vertices,
                    edges=vertex_count
                )
                faces.append(face)
                face_id += 1
            except (ValueError, IndexError):
                continue
        
        return faces

    def _parse_vertices(self, vertex_lines: List[str]) -> List[Tuple[float, float, float]]:
        """Parse :vertices section."""
        if not vertex_lines or len(vertex_lines) < 1:
            return []
        
        vertices = []
        
        # First line: vertex_count max_coords
        # Remaining lines: x y z [symbolic_expression]
        for line in vertex_lines[1:]:
            parts = line.split()
            if len(parts) < 3:
                continue
            
            try:
                x = float(parts[0])
                y = float(parts[1])
                z = float(parts[2])
                vertices.append((x, y, z))
            except ValueError:
                continue
        
        return vertices

    def _parse_dihedral(self, dih_lines: List[str]) -> Tuple[List[float], int]:
        """Parse :dih section for dihedral angles."""
        if not dih_lines or len(dih_lines) < 1:
            return [], 0
        
        angles = []
        edge_count = 0
        
        try:
            # First line: count of distinct dihedral angles
            count = int(dih_lines[0])
            
            # Parse each dihedral angle entry
            for line in dih_lines[1:count+1]:
                parts = line.split()
                if len(parts) >= 4:
                    edge_count = int(parts[0])
                    angle = float(parts[3])
                    angles.append(angle)
        except (ValueError, IndexError):
            pass
        
        return angles, edge_count

    def _build_composition(self, face_types: Dict[int, int]) -> str:
        """Build composition string from face types."""
        # Map edge counts to Tier 0 symbols
        edge_to_symbol = {
            3: "a3", 4: "b2", 5: "a5", 6: "b3", 7: "a7", 8: "b4",
            9: "a9", 10: "b5", 11: "a1", 12: "b6", 13: "a2", 14: "b7",
            15: "a4", 16: "b8", 17: "a6", 18: "b9", 19: "a8", 20: "b1"
        }
        
        parts = []
        for edges in sorted(face_types.keys()):
            count = face_types[edges]
            symbol = edge_to_symbol.get(edges, f"p{edges}")
            parts.append(f"{count}×{symbol}")
        
        return " + ".join(parts) if parts else "unknown"

    def _infer_symmetry(self, file_id: int, face_count: int) -> str:
        """Infer symmetry group from file ID and face count."""
        # Platonic solids
        if file_id == 1:  # Cube
            return "Oh"
        elif file_id == 2:  # Octahedron
            return "Oh"
        elif file_id == 3:  # Dodecahedron
            return "Ih"
        elif file_id == 4:  # Icosahedron
            return "Ih"
        elif file_id == 5:  # Tetrahedron
            return "Td"
        
        # Archimedean solids (approximate)
        if 9 <= file_id <= 21:
            if face_count == 8:
                return "Oh"
            elif face_count == 14:
                return "Oh"
            elif face_count == 20:
                return "Ih"
            else:
                return "Cn"
        
        # Johnson solids (default)
        return "C1"

    def _get_symbol(self, file_id: int) -> str:
        """Get Unicode symbol for polyhedron."""
        if file_id in self.PLATONIC_IDS:
            return self.PLATONIC_IDS[file_id]
        elif file_id in self.ARCHIMEDEAN_IDS:
            return self.ARCHIMEDEAN_IDS[file_id]
        elif file_id >= self.JOHNSON_START_ID:
            johnson_index = file_id - self.JOHNSON_START_ID
            symbol_index = self.JOHNSON_START_SYMBOL + johnson_index
            return f"Ω{symbol_index}"
        return f"Ω{file_id}"

    def _classify(self, file_id: int) -> str:
        """Classify polyhedron type."""
        if file_id in self.PLATONIC_IDS:
            return "platonic"
        elif file_id in self.ARCHIMEDEAN_IDS:
            return "archimedean"
        elif file_id >= self.JOHNSON_START_ID:
            return "johnson"
        return "unknown"


class PolyhedraExtractor:
    """Main extractor orchestrating Netlib parsing and output."""

    def __init__(self, output_dir: Path = Path("catalogs/tier1")):
        """Initialize extractor."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parser = NetlibParser()
        self.polyhedra: Dict[str, Polyhedron] = {}

    def extract_all(self) -> bool:
        """Extract all 110 polyhedra (5 Platonic + 13 Archimedean + 92 Johnson)."""
        logger.info("Starting extraction of 110 polyhedra...")
        
        # Extract Platonic solids (files 1-5)
        platonic_ids = list(range(1, 6))
        logger.info(f"Extracting {len(platonic_ids)} Platonic solids...")
        for file_id in platonic_ids:
            poly = self.parser.parse_file(file_id)
            if poly:
                self.polyhedra[poly.symbol] = poly
                logger.info(f"✓ {poly.symbol}: {poly.name}")
        
        # Extract Archimedean solids (files 9-21)
        archimedean_ids = list(range(9, 22))
        logger.info(f"Extracting {len(archimedean_ids)} Archimedean solids...")
        for file_id in archimedean_ids:
            poly = self.parser.parse_file(file_id)
            if poly:
                self.polyhedra[poly.symbol] = poly
                logger.info(f"✓ {poly.symbol}: {poly.name}")
        
        # Extract Johnson solids (files 22-114)
        johnson_ids = list(range(22, 115))
        logger.info(f"Extracting {len(johnson_ids)} Johnson solids...")
        for i, file_id in enumerate(johnson_ids):
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{len(johnson_ids)} Johnson solids...")
            poly = self.parser.parse_file(file_id)
            if poly:
                self.polyhedra[poly.symbol] = poly
        
        logger.info(f"Extraction complete: {len(self.polyhedra)} polyhedra extracted")
        return len(self.polyhedra) >= 90  # At least 90 of 110 (some files may have parsing issues)

    def save_polyhedra_jsonl(self) -> Path:
        """Save polyhedra to JSONL file."""
        output_file = self.output_dir / "polyhedra.jsonl"
        
        with open(output_file, 'w') as f:
            for symbol in sorted(self.polyhedra.keys()):
                poly = self.polyhedra[symbol]
                f.write(json.dumps(poly.to_dict()) + '\n')
        
        logger.info(f"Saved {len(self.polyhedra)} polyhedra to {output_file}")
        return output_file

    def save_decompositions(self) -> Path:
        """Save decompositions to JSON file."""
        output_file = self.output_dir / "decompositions.json"
        
        decompositions = {}
        for symbol, poly in self.polyhedra.items():
            # Extract base symbols from composition
            base_symbols = self._extract_base_symbols(poly.composition)
            
            decompositions[symbol] = {
                "name": poly.name,
                "base_symbols": base_symbols,
                "face_count": len(poly.faces),
                "composition": poly.composition,
                "dihedral_angles": poly.dihedral_angles,
                "attachment_sequence": self._build_attachment_sequence(poly)
            }
        
        with open(output_file, 'w') as f:
            json.dump(decompositions, f, indent=2)
        
        logger.info(f"Saved decompositions to {output_file}")
        return output_file

    def _extract_base_symbols(self, composition: str) -> List[str]:
        """Extract unique base symbols from composition string."""
        # Parse "6×b2 + 8×a3" format
        symbols = set()
        parts = composition.split(' + ')
        for part in parts:
            if '×' in part:
                symbol = part.split('×')[1]
                symbols.add(symbol)
        return sorted(list(symbols))

    def _build_attachment_sequence(self, poly: Polyhedron) -> List[Dict[str, Any]]:
        """Build attachment sequence from faces and dihedral angles."""
        sequence = []
        
        for i, face in enumerate(poly.faces):
            entry = {
                "face": i,
                "vertices": face.vertices,
                "edges": face.edges
            }
            
            # Add attachment info for faces after the first
            if i > 0 and poly.dihedral_angles:
                entry["attach_to"] = i - 1
                entry["fold_angle"] = poly.dihedral_angles[0]  # Use first dihedral angle
            
            sequence.append(entry)
        
        return sequence


def main():
    """Main entry point."""
    extractor = PolyhedraExtractor()
    
    # Extract all polyhedra
    success = extractor.extract_all()
    
    if success:
        # Save outputs
        extractor.save_polyhedra_jsonl()
        extractor.save_decompositions()
        logger.info("✓ Extraction complete and saved")
        return 0
    else:
        logger.error("✗ Extraction failed: insufficient polyhedra extracted")
        return 1


if __name__ == "__main__":
    exit(main())
