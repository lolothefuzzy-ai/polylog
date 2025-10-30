"""
Collection of built-in polyform templates.

Each template defines:
- Polyforms (sides, positions)
- Bonds (which edges connect)
- Default fold angles
- Symmetry properties
"""
from typing import Dict, List, Optional
import numpy as np


class TemplateLibrary:
    """
    Collection of built-in polyform templates.
    
    Each template defines:
    - Polyforms (sides, positions)
    - Bonds (which edges connect)
    - Default fold angles
    - Symmetry properties
    """
    
    TEMPLATES = {
        'cube_net': {
            'name': 'Cube Net (Cross)',
            'description': '6 squares in cross pattern',
            'preview_icon': 'icons/cube_net.png',
            'polyforms': [
                {'sides': 4, 'position': (0, 0, 0)},      # Center
                {'sides': 4, 'position': (2, 0, 0)},      # Right
                {'sides': 4, 'position': (-2, 0, 0)},     # Left
                {'sides': 4, 'position': (0, 2, 0)},      # Top
                {'sides': 4, 'position': (0, -2, 0)},     # Bottom
                {'sides': 4, 'position': (0, 0, 2)},      # Front
            ],
            'bonds': [
                {'poly_indices': (0, 1), 'edges': (0, 2)},  # Center-Right
                {'poly_indices': (0, 2), 'edges': (2, 0)},  # Center-Left
                {'poly_indices': (0, 3), 'edges': (1, 3)},  # Center-Top
                {'poly_indices': (0, 4), 'edges': (3, 1)},  # Center-Bottom
            ],
            'symmetry': {
                'type': 'rotational',
                'order': 4,  # 4-fold rotational symmetry
                'axis': 'z'
            }
        },
        
        'triangular_prism_net': {
            'name': 'Triangular Prism Net',
            'description': '2 triangles + 3 rectangles',
            'preview_icon': 'icons/tri_prism.png',
            'polyforms': [
                {'sides': 3, 'position': (0, 0, 0)},      # Triangle 1
                {'sides': 3, 'position': (0, 3, 0)},      # Triangle 2
                {'sides': 4, 'position': (1, 1, 0)},      # Rect 1
                {'sides': 4, 'position': (2, 1, 0)},      # Rect 2
                {'sides': 4, 'position': (3, 1, 0)},      # Rect 3
            ],
            'bonds': [
                {'poly_indices': (0, 2), 'edges': (0, 0)},
                {'poly_indices': (2, 3), 'edges': (1, 3)},
                {'poly_indices': (3, 4), 'edges': (1, 3)},
                {'poly_indices': (1, 2), 'edges': (0, 2)},
            ],
            'symmetry': {
                'type': 'reflection',
                'axis': 'x'
            }
        },
        
        'tetrahedron_net': {
            'name': 'Tetrahedron Net',
            'description': '4 triangles',
            'preview_icon': 'icons/tetrahedron.png',
            'polyforms': [
                {'sides': 3, 'position': (0, 0, 0)},
                {'sides': 3, 'position': (2, 0, 0)},
                {'sides': 3, 'position': (1, 1.732, 0)},
                {'sides': 3, 'position': (1, -1.732, 0)},
            ],
            'bonds': [
                {'poly_indices': (0, 1), 'edges': (0, 0)},
                {'poly_indices': (0, 2), 'edges': (1, 2)},
                {'poly_indices': (0, 3), 'edges': (2, 1)},
            ],
            'symmetry': {
                'type': 'rotational',
                'order': 3,
                'axis': 'z'
            }
        },
        
        'hexagon_flower': {
            'name': 'Hexagon Flower',
            'description': '1 center hexagon + 6 surrounding',
            'preview_icon': 'icons/hexagon_flower.png',
            'polyforms': [
                {'sides': 6, 'position': (0, 0, 0)},  # Center
                {'sides': 6, 'position': (2 * np.cos(0), 2 * np.sin(0), 0)},
                {'sides': 6, 'position': (2 * np.cos(np.pi / 3), 2 * np.sin(np.pi / 3), 0)},
                {'sides': 6, 'position': (2 * np.cos(2 * np.pi / 3), 2 * np.sin(2 * np.pi / 3), 0)},
                {'sides': 6, 'position': (2 * np.cos(np.pi), 2 * np.sin(np.pi), 0)},
                {'sides': 6, 'position': (2 * np.cos(4 * np.pi / 3), 2 * np.sin(4 * np.pi / 3), 0)},
                {'sides': 6, 'position': (2 * np.cos(5 * np.pi / 3), 2 * np.sin(5 * np.pi / 3), 0)},
            ],
            'bonds': [
                {'poly_indices': (0, 1), 'edges': (0, 3)},
                {'poly_indices': (0, 2), 'edges': (1, 4)},
                {'poly_indices': (0, 3), 'edges': (2, 5)},
                {'poly_indices': (0, 4), 'edges': (3, 0)},
                {'poly_indices': (0, 5), 'edges': (4, 1)},
                {'poly_indices': (0, 6), 'edges': (5, 2)},
            ],
            'symmetry': {
                'type': 'rotational',
                'order': 6,
                'axis': 'z'
            }
        },
        
        'octahedron_net': {
            'name': 'Octahedron Net',
            'description': '8 triangles in strip pattern',
            'preview_icon': 'icons/octahedron.png',
            'polyforms': [
                {'sides': 3, 'position': (0, 0, 0)},
                {'sides': 3, 'position': (2, 0, 0)},
                {'sides': 3, 'position': (4, 0, 0)},
                {'sides': 3, 'position': (6, 0, 0)},
                {'sides': 3, 'position': (1, 1.732, 0)},
                {'sides': 3, 'position': (3, 1.732, 0)},
                {'sides': 3, 'position': (5, 1.732, 0)},
                {'sides': 3, 'position': (7, 1.732, 0)},
            ],
            'bonds': [
                {'poly_indices': (0, 1), 'edges': (0, 0)},
                {'poly_indices': (1, 2), 'edges': (0, 0)},
                {'poly_indices': (2, 3), 'edges': (0, 0)},
                {'poly_indices': (0, 4), 'edges': (1, 2)},
                {'poly_indices': (1, 5), 'edges': (1, 2)},
                {'poly_indices': (2, 6), 'edges': (1, 2)},
                {'poly_indices': (3, 7), 'edges': (1, 2)},
            ],
            'symmetry': {
                'type': 'reflection',
                'axis': 'x'
            }
        }
    }
    
    @staticmethod
    def get(template_name: str) -> Optional[Dict]:
        """Retrieve template by name."""
        return TemplateLibrary.TEMPLATES.get(template_name)
    
    @staticmethod
    def list_all() -> List[Dict]:
        """Get all available templates."""
        return [
            {
                'id': key,
                'name': val['name'],
                'description': val['description'],
                'preview': val.get('preview_icon')
            }
            for key, val in TemplateLibrary.TEMPLATES.items()
        ]
    
    @staticmethod
    def get_template_names() -> List[str]:
        """Get list of all template names."""
        return list(TemplateLibrary.TEMPLATES.keys())
