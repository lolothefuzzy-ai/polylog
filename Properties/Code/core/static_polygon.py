import numpy as np

class StaticPolygon:
    """
    Static foldable polygon with fixed internal angles and side lengths.
    Only polyform state properties (fold angle, centroid, orientation) can change.
    """
    def __init__(self, sides: int, side_length: float = 1.0):
        """
        Initialize a static equilateral polygon.

        Args:
            sides: Number of sides (3+ for valid polygon)
            side_length: Length of each side (constant)
        """
        self.sides = sides
        self.side_length = side_length

        # IMMUTABLE PROPERTIES - Never change
        self.internal_angles = (sides - 2) * 180 / sides  # Fixed internal angle
        self.vertices = self._calculate_base_vertices()   # Base vertex positions

    def _calculate_base_vertices(self):
        """
        Generate equilateral polygon vertices.
        Internal angles NEVER change during folding.
        """
        if self.sides < 3:
            raise ValueError("Polygon must have at least 3 sides")

        angles = np.linspace(0, 2*np.pi, self.sides, endpoint=False)
        vertices = []
        for angle in angles:
            x = np.cos(angle) * self.side_length
            y = np.sin(angle) * self.side_length
            vertices.append((x, y))

        return vertices

    @property
    def is_equilateral(self):
        """All sides are equal length - always True for static polygons"""
        return True

    @property
    def is_equilateral(self):
        """All internal angles are equal - always True for regular polygons"""
        return True

    def get_vertex_count(self):
        """Number of vertices"""
        return self.sides

    def get_side_count(self):
        """Number of sides"""
        return self.sides
