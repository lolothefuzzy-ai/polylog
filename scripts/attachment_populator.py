#!/usr/bin/env python3
"""
Attachment Matrix Populator

Extracts dihedral angles from polyhedra and builds the 18×18 polygon pair
attachment matrix with fold angles and stability scores.

Outputs:
- catalogs/attachments/attachment_matrix.json (18×18 polygon pair matrix)
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import logging
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class AttachmentOption:
    """Represents a valid attachment between two polygon types."""
    fold_angle: float  # radians
    stability: float   # 0.0-1.0
    context: str       # "2d_planar", "3d_tetrahedral", etc.
    source_polyhedra: List[str]  # Which polyhedra use this attachment


class AttachmentMatrixBuilder:
    """Builds the 18×18 polygon pair attachment matrix."""

    # Tier 0 polygon symbols (3-20 sides)
    TIER0_SYMBOLS = [
        "a3", "b2", "a5", "b3", "a7", "b4", "a9", "b5", "a1", "b6",
        "a2", "b7", "a4", "b8", "a6", "b9", "a8", "b1"
    ]

    # Edge count to symbol mapping
    EDGES_TO_SYMBOL = {
        3: "a3", 4: "b2", 5: "a5", 6: "b3", 7: "a7", 8: "b4",
        9: "a9", 10: "b5", 11: "a1", 12: "b6", 13: "a2", 14: "b7",
        15: "a4", 16: "b8", 17: "a6", 18: "b9", 19: "a8", 20: "b1"
    }

    # Known dihedral angles from Platonic solids
    KNOWN_ANGLES = {
        # Platonic solids
        (3, 3): [2.4119, 1.9106],  # Icosahedron, Octahedron
        (4, 4): [1.5708],           # Cube (90°)
        (5, 5): [2.0344],           # Dodecahedron
        # Mixed pairs (approximations)
        (3, 4): [1.7321, 1.9106],   # Triangle-Square
        (3, 5): [1.9106, 2.0344],   # Triangle-Pentagon
        (4, 5): [1.5708, 2.0344],   # Square-Pentagon
    }

    def __init__(self, polyhedra_file: Path = Path("catalogs/tier1/polyhedra.jsonl")):
        """Initialize builder."""
        self.polyhedra_file = polyhedra_file
        self.polyhedra: Dict[str, Dict[str, Any]] = {}
        self.attachment_matrix: Dict[str, Dict[str, List[AttachmentOption]]] = {}
        self._initialize_matrix()

    def _initialize_matrix(self) -> None:
        """Initialize empty attachment matrix for all 18×18 pairs."""
        for symbol_a in self.TIER0_SYMBOLS:
            self.attachment_matrix[symbol_a] = {}
            for symbol_b in self.TIER0_SYMBOLS:
                self.attachment_matrix[symbol_a][symbol_b] = []

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

    def populate_from_polyhedra(self) -> None:
        """Extract attachment angles from polyhedra and populate matrix."""
        logger.info("Extracting attachment angles from polyhedra...")

        for symbol, poly in self.polyhedra.items():
            if not poly.get('faces') or not poly.get('dihedral_angles'):
                continue

            # Get face types in this polyhedron
            face_types = {}
            for face in poly['faces']:
                edges = face.get('edges', 0)
                face_types[edges] = face_types.get(edges, 0) + 1

            # Extract angles
            angles = poly.get('dihedral_angles', [])
            if not angles:
                continue

            angle = angles[0]  # Primary dihedral angle
            stability = self._calculate_stability(angle)

            # Add attachment options for each pair of face types
            face_edge_counts = list(face_types.keys())
            for edges_a in face_edge_counts:
                for edges_b in face_edge_counts:
                    symbol_a = self.EDGES_TO_SYMBOL.get(edges_a)
                    symbol_b = self.EDGES_TO_SYMBOL.get(edges_b)

                    if symbol_a and symbol_b:
                        # Normalize pair order
                        if symbol_a > symbol_b:
                            symbol_a, symbol_b = symbol_b, symbol_a

                        # Check if this angle already exists
                        existing = self.attachment_matrix[symbol_a][symbol_b]
                        angle_exists = any(
                            abs(opt.fold_angle - angle) < 0.01
                            for opt in existing
                        )

                        if not angle_exists:
                            option = AttachmentOption(
                                fold_angle=angle,
                                stability=stability,
                                context=self._get_context(symbol_a, symbol_b, angle),
                                source_polyhedra=[symbol]
                            )
                            self.attachment_matrix[symbol_a][symbol_b].append(option)
                        else:
                            # Update source polyhedra list
                            for opt in existing:
                                if abs(opt.fold_angle - angle) < 0.01:
                                    if symbol not in opt.source_polyhedra:
                                        opt.source_polyhedra.append(symbol)

        logger.info("Extraction complete")

    def populate_known_angles(self) -> None:
        """Populate matrix with known angles from Platonic solids."""
        logger.info("Populating known angles from Platonic solids...")

        for (edges_a, edges_b), angles in self.KNOWN_ANGLES.items():
            symbol_a = self.EDGES_TO_SYMBOL.get(edges_a)
            symbol_b = self.EDGES_TO_SYMBOL.get(edges_b)

            if not symbol_a or not symbol_b:
                continue

            # Normalize pair order
            if symbol_a > symbol_b:
                symbol_a, symbol_b = symbol_b, symbol_a

            for angle in angles:
                stability = self._calculate_stability(angle)
                option = AttachmentOption(
                    fold_angle=angle,
                    stability=stability,
                    context=self._get_context(symbol_a, symbol_b, angle),
                    source_polyhedra=[]
                )

                # Check if already exists
                existing = self.attachment_matrix[symbol_a][symbol_b]
                angle_exists = any(
                    abs(opt.fold_angle - angle) < 0.01
                    for opt in existing
                )

                if not angle_exists:
                    self.attachment_matrix[symbol_a][symbol_b].append(option)

    def _calculate_stability(self, angle: float) -> float:
        """Calculate stability score from dihedral angle."""
        # Stability = 1.0 - |angle - ideal_angle| / π
        # Ideal angles: 0 (planar), π/2 (orthogonal), π/3 (tetrahedral), etc.

        ideal_angles = [0, math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2,
                       2 * math.pi / 3, 3 * math.pi / 4, 5 * math.pi / 6, math.pi]

        min_distance = min(abs(angle - ideal) for ideal in ideal_angles)
        stability = max(0.0, 1.0 - (min_distance / math.pi))

        # Clamp to valid range
        return max(0.0, min(1.0, stability))

    def _get_context(self, symbol_a: str, symbol_b: str, angle: float) -> str:
        """Determine attachment context from symbols and angle."""
        edges_a = self._symbol_to_edges(symbol_a)
        edges_b = self._symbol_to_edges(symbol_b)

        # Planar attachment (0 radians)
        if angle < 0.1:
            return "2d_planar"

        # Orthogonal (π/2 ≈ 1.5708)
        if 1.4 < angle < 1.7:
            return "3d_cubic"

        # Tetrahedral (≈ 1.9106)
        if 1.8 < angle < 2.0:
            return "3d_tetrahedral"

        # Pentagonal/Icosahedral (≈ 2.4119)
        if 2.3 < angle < 2.5:
            return "3d_icosahedral"

        # Dodecahedral (≈ 2.0344)
        if 2.0 < angle < 2.1:
            return "3d_dodecahedral"

        # Mixed edge lengths
        if edges_a != edges_b:
            return "mixed_edge_lengths"

        return "3d_general"

    def _symbol_to_edges(self, symbol: str) -> int:
        """Convert symbol to edge count."""
        for edges, sym in self.EDGES_TO_SYMBOL.items():
            if sym == symbol:
                return edges
        return 0

    def fill_gaps_with_defaults(self) -> None:
        """Fill any gaps in the matrix with default attachment options."""
        logger.info("Filling gaps with default attachments...")

        for symbol_a in self.TIER0_SYMBOLS:
            for symbol_b in self.TIER0_SYMBOLS:
                if not self.attachment_matrix[symbol_a][symbol_b]:
                    # Add a default planar attachment
                    option = AttachmentOption(
                        fold_angle=0.0,
                        stability=0.5,
                        context="2d_planar",
                        source_polyhedra=[]
                    )
                    self.attachment_matrix[symbol_a][symbol_b].append(option)

    def save_matrix(self, output_file: Path = Path("catalogs/attachments/attachment_matrix.json")) -> Path:
        """Save attachment matrix to JSON file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format
        matrix_dict = {}
        for symbol_a in self.TIER0_SYMBOLS:
            matrix_dict[symbol_a] = {}
            for symbol_b in self.TIER0_SYMBOLS:
                options = self.attachment_matrix[symbol_a][symbol_b]
                matrix_dict[symbol_a][symbol_b] = [
                    {
                        "fold_angle": opt.fold_angle,
                        "stability": round(opt.stability, 3),
                        "context": opt.context,
                        "source_polyhedra": opt.source_polyhedra
                    }
                    for opt in options
                ]

        with open(output_file, 'w') as f:
            json.dump(matrix_dict, f, indent=2)

        logger.info(f"Saved attachment matrix to {output_file}")
        return output_file

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the populated matrix."""
        total_pairs = len(self.TIER0_SYMBOLS) ** 2
        populated_pairs = 0
        total_options = 0
        stable_options = 0

        for symbol_a in self.TIER0_SYMBOLS:
            for symbol_b in self.TIER0_SYMBOLS:
                options = self.attachment_matrix[symbol_a][symbol_b]
                if options:
                    populated_pairs += 1
                    total_options += len(options)
                    stable_options += sum(1 for opt in options if opt.stability >= 0.7)

        return {
            "total_pairs": total_pairs,
            "populated_pairs": populated_pairs,
            "coverage": f"{100 * populated_pairs / total_pairs:.1f}%",
            "total_options": total_options,
            "stable_options": stable_options,
            "average_options_per_pair": round(total_options / populated_pairs, 2) if populated_pairs > 0 else 0
        }


def main():
    """Main entry point."""
    builder = AttachmentMatrixBuilder()

    # Load polyhedra
    if not builder.load_polyhedra():
        logger.error("Failed to load polyhedra")
        return 1

    # Populate from polyhedra
    builder.populate_from_polyhedra()

    # Add known angles
    builder.populate_known_angles()

    # Fill gaps
    builder.fill_gaps_with_defaults()

    # Save matrix
    builder.save_matrix()

    # Print statistics
    stats = builder.get_statistics()
    logger.info(f"Matrix statistics: {stats}")

    logger.info("✓ Attachment matrix population complete")
    return 0


if __name__ == "__main__":
    exit(main())
