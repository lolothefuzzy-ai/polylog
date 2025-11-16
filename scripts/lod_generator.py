#!/usr/bin/env python3
"""
LOD Metadata Generator

Generates Level of Detail (LOD) metadata for all polyhedra based on
face count, vertex count, and geometric complexity.

Outputs:
- catalogs/tier1/lod_metadata.json (LOD breakpoints for all 110 polyhedra)
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import logging
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class LODLevel:
    """Represents a single LOD level."""
    name: str
    face_ratio: float  # 0.0-1.0, fraction of full faces
    vertex_ratio: float  # 0.0-1.0, fraction of full vertices
    render_distance: str  # "close", "normal", "far", "thumbnail"


class LODGenerator:
    """Generates LOD metadata for polyhedra."""

    # LOD level definitions
    LOD_LEVELS = [
        LODLevel(name="full", face_ratio=1.0, vertex_ratio=1.0, render_distance="close"),
        LODLevel(name="medium", face_ratio=0.6, vertex_ratio=0.7, render_distance="normal"),
        LODLevel(name="low", face_ratio=0.2, vertex_ratio=0.3, render_distance="far"),
        LODLevel(name="thumbnail", face_ratio=0.05, vertex_ratio=0.1, render_distance="thumbnail"),
    ]

    def __init__(self, polyhedra_file: Path = Path("catalogs/tier1/polyhedra.jsonl")):
        """Initialize generator."""
        self.polyhedra_file = polyhedra_file
        self.polyhedra: Dict[str, Dict[str, Any]] = {}
        self.lod_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def load_polyhedra(self) -> bool:
        """Load polyhedra from JSONL file."""
        if not self.polyhedra_file.exists():
            logger.error(f"Polyhedra file not found: {self.polyhedra_file}")
            return False

        try:
            with open(self.polyhedra_file, 'r') as f:
                for line in f:
                    if line.strip():
                        poly = json.loads(line)
                        self.polyhedra[poly['symbol']] = poly
            logger.info(f"Loaded {len(self.polyhedra)} polyhedra")
            return True
        except Exception as e:
            logger.error(f"Error loading polyhedra: {e}")
            return False

    def generate_lod_metadata(self) -> None:
        """Generate LOD metadata for all polyhedra."""
        logger.info("Generating LOD metadata...")

        for symbol, poly in self.polyhedra.items():
            full_faces = len(poly.get('faces', []))
            full_vertices = len(poly.get('vertices', []))

            if full_faces == 0 or full_vertices == 0:
                logger.warning(f"Skipping {symbol}: no faces or vertices")
                continue

            lod_data = {}

            for lod_level in self.LOD_LEVELS:
                # Calculate reduced counts
                lod_faces = max(1, int(full_faces * lod_level.face_ratio))
                lod_vertices = max(1, int(full_vertices * lod_level.vertex_ratio))

                # Estimate file sizes (rough approximation)
                # Full: ~100 bytes per face + 24 bytes per vertex
                full_size = full_faces * 100 + full_vertices * 24
                lod_size = lod_faces * 100 + lod_vertices * 24

                # Calculate compression ratio
                compression_ratio = full_size / lod_size if lod_size > 0 else 1.0

                lod_data[lod_level.name] = {
                    "faces": lod_faces,
                    "vertices": lod_vertices,
                    "edges": self._estimate_edges(lod_faces),
                    "size_bytes": lod_size,
                    "compression_ratio": round(compression_ratio, 2),
                    "render_distance": lod_level.render_distance,
                    "load_time_ms": self._estimate_load_time(lod_size),
                    "render_time_ms": self._estimate_render_time(lod_faces, lod_vertices)
                }

            self.lod_metadata[symbol] = lod_data

        logger.info(f"Generated LOD metadata for {len(self.lod_metadata)} polyhedra")

    def _estimate_edges(self, face_count: int) -> int:
        """Estimate edge count from face count using Euler's formula."""
        # V - E + F = 2
        # For polyhedra: E ≈ 1.5 * F (rough approximation)
        return max(1, int(face_count * 1.5))

    def _estimate_load_time(self, size_bytes: int) -> float:
        """Estimate load time in milliseconds."""
        # Assume 1 MB/s load speed
        return round((size_bytes / 1_000_000) * 1000, 1)

    def _estimate_render_time(self, face_count: int, vertex_count: int) -> float:
        """Estimate render time in milliseconds."""
        # Rough approximation: 0.1ms per face + 0.05ms per vertex
        return round(face_count * 0.1 + vertex_count * 0.05, 1)

    def add_transition_hints(self) -> None:
        """Add transition hints for LOD switching."""
        logger.info("Adding LOD transition hints...")

        for symbol in self.lod_metadata:
            lod_data = self.lod_metadata[symbol]

            # Add transition thresholds (camera distance in units)
            lod_data["transition_distances"] = {
                "full_to_medium": 5.0,
                "medium_to_low": 15.0,
                "low_to_thumbnail": 50.0
            }

            # Add quality hints
            lod_data["quality_hints"] = {
                "full": "High quality, use for close inspection",
                "medium": "Balanced quality and performance, default view",
                "low": "Low quality, use for distance viewing",
                "thumbnail": "Minimal quality, use for thumbnails only"
            }

    def save_metadata(self, output_file: Path = Path("catalogs/tier1/lod_metadata.json")) -> Path:
        """Save LOD metadata to JSON file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(self.lod_metadata, f, indent=2)

        logger.info(f"Saved LOD metadata to {output_file}")
        return output_file

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about LOD metadata."""
        total_polyhedra = len(self.lod_metadata)
        total_lod_entries = total_polyhedra * len(self.LOD_LEVELS)

        avg_full_faces = 0
        avg_full_vertices = 0
        avg_compression = 0

        for symbol, lod_data in self.lod_metadata.items():
            if 'full' in lod_data:
                full = lod_data['full']
                avg_full_faces += full.get('faces', 0)
                avg_full_vertices += full.get('vertices', 0)
                avg_compression += full.get('compression_ratio', 1.0)

        if total_polyhedra > 0:
            avg_full_faces //= total_polyhedra
            avg_full_vertices //= total_polyhedra
            avg_compression /= total_polyhedra

        return {
            "total_polyhedra": total_polyhedra,
            "total_lod_entries": total_lod_entries,
            "lod_levels": len(self.LOD_LEVELS),
            "average_full_faces": avg_full_faces,
            "average_full_vertices": avg_full_vertices,
            "average_compression_ratio": round(avg_compression, 2)
        }


def main():
    """Main entry point."""
    generator = LODGenerator()

    # Load polyhedra
    if not generator.load_polyhedra():
        logger.error("Failed to load polyhedra")
        return 1

    # Generate LOD metadata
    generator.generate_lod_metadata()

    # Add transition hints
    generator.add_transition_hints()

    # Save metadata
    generator.save_metadata()

    # Print statistics
    stats = generator.get_statistics()
    logger.info(f"LOD statistics: {stats}")

    logger.info("✓ LOD metadata generation complete")
    return 0


if __name__ == "__main__":
    exit(main())
