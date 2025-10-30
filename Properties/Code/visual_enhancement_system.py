"""
Enhanced Visual Representation System

Upgrades rendering with:
- Material properties (metallic, glossy, matte, transparent)
- Advanced lighting (directional, point, ambient)
- Shadows and depth effects
- Edge highlighting and beveling
- Texture support
- Color gradients and patterns
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MaterialType(Enum):
    """Material presets for different visual styles."""
    MATTE = "matte"
    GLOSSY = "glossy"
    METALLIC = "metallic"
    GLASS = "glass"
    PLASTIC = "plastic"
    PAPER = "paper"
    WOOD = "wood"


@dataclass
class Material:
    """Material properties for rendering."""
    name: str
    base_color: Tuple[float, float, float]  # RGB
    metallic: float = 0.0  # 0=dielectric, 1=metal
    roughness: float = 0.5  # 0=smooth, 1=rough
    opacity: float = 1.0  # 0=transparent, 1=opaque
    emissive: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    
    # Additional properties
    specular_intensity: float = 0.5
    specular_power: float = 32.0
    ambient_strength: float = 0.2
    
    @staticmethod
    def from_preset(preset: MaterialType, base_color: Tuple[float, float, float]) -> 'Material':
        """Create material from preset type."""
        presets = {
            MaterialType.MATTE: Material(
                name="Matte",
                base_color=base_color,
                metallic=0.0,
                roughness=0.9,
                specular_intensity=0.1,
                specular_power=8.0
            ),
            MaterialType.GLOSSY: Material(
                name="Glossy",
                base_color=base_color,
                metallic=0.0,
                roughness=0.2,
                specular_intensity=0.8,
                specular_power=64.0
            ),
            MaterialType.METALLIC: Material(
                name="Metallic",
                base_color=base_color,
                metallic=1.0,
                roughness=0.3,
                specular_intensity=1.0,
                specular_power=128.0
            ),
            MaterialType.GLASS: Material(
                name="Glass",
                base_color=base_color,
                metallic=0.0,
                roughness=0.0,
                opacity=0.3,
                specular_intensity=1.0,
                specular_power=256.0
            ),
            MaterialType.PLASTIC: Material(
                name="Plastic",
                base_color=base_color,
                metallic=0.0,
                roughness=0.4,
                specular_intensity=0.6,
                specular_power=48.0
            ),
            MaterialType.PAPER: Material(
                name="Paper",
                base_color=base_color,
                metallic=0.0,
                roughness=0.95,
                specular_intensity=0.05,
                specular_power=4.0
            ),
        }
        return presets.get(preset, Material(name="Default", base_color=base_color))


@dataclass
class Light:
    """Light source for scene illumination."""
    position: np.ndarray  # 3D position
    color: Tuple[float, float, float]  # RGB
    intensity: float = 1.0
    type: str = "point"  # point, directional, spot
    direction: Optional[np.ndarray] = None  # For directional/spot
    
    # Shadow properties
    cast_shadows: bool = True
    shadow_softness: float = 0.5


class VisualEnhancementRenderer:
    """
    Enhanced renderer with advanced visual features.
    
    Integrates with existing GLRenderer to add:
    - Material-based shading
    - Multi-light support
    - Edge effects
    - Post-processing
    """
    
    def __init__(self):
        self.materials: Dict[str, Material] = {}
        self.lights: List[Light] = []
        
        # Default materials
        self._setup_default_materials()
        
        # Default lighting
        self._setup_default_lights()
        
        # Rendering settings
        self.enable_shadows = True
        self.enable_ambient_occlusion = True
        self.enable_edge_highlighting = True
        self.edge_width = 2.0
        self.edge_color = (0.1, 0.1, 0.1, 1.0)
        
        # Visual effects
        self.enable_bloom = False
        self.enable_depth_of_field = False
        self.background_gradient = True
    
    def _setup_default_materials(self):
        """Create default material presets."""
        colors = {
            'cyan': (0.2, 0.7, 1.0),
            'green': (0.2, 1.0, 0.4),
            'orange': (1.0, 0.6, 0.2),
            'purple': (0.7, 0.3, 1.0),
            'yellow': (1.0, 0.9, 0.2),
            'red': (1.0, 0.3, 0.3),
        }
        
        # Create materials for each preset type
        for color_name, rgb in colors.items():
            for mat_type in MaterialType:
                name = f"{color_name}_{mat_type.value}"
                self.materials[name] = Material.from_preset(mat_type, rgb)
    
    def _setup_default_lights(self):
        """Setup default three-point lighting."""
        # Key light (main)
        self.lights.append(Light(
            position=np.array([5.0, 5.0, 10.0]),
            color=(1.0, 1.0, 0.95),
            intensity=1.0,
            type="point"
        ))
        
        # Fill light (softer, opposite side)
        self.lights.append(Light(
            position=np.array([-3.0, 3.0, 8.0]),
            color=(0.8, 0.85, 1.0),
            intensity=0.5,
            type="point"
        ))
        
        # Rim light (behind)
        self.lights.append(Light(
            position=np.array([0.0, -5.0, 5.0]),
            color=(0.9, 0.9, 1.0),
            intensity=0.3,
            type="point"
        ))
    
    def compute_lighting(self, vertex_pos: np.ndarray, vertex_normal: np.ndarray,
                        material: Material, camera_pos: np.ndarray) -> Tuple[float, float, float]:
        """
        Compute Blinn-Phong lighting for a vertex.
        
        Args:
            vertex_pos: 3D position
            vertex_normal: Surface normal (normalized)
            material: Material properties
            camera_pos: Camera position
            
        Returns:
            Final RGB color
        """
        # Start with ambient
        ambient = np.array(material.base_color) * material.ambient_strength
        
        # Accumulate lighting from all sources
        diffuse = np.zeros(3)
        specular = np.zeros(3)
        
        for light in self.lights:
            # Light direction
            if light.type == "directional":
                light_dir = -light.direction / np.linalg.norm(light.direction)
            else:  # point
                to_light = light.position - vertex_pos
                light_dir = to_light / np.linalg.norm(to_light)
            
            # Diffuse component
            diff_intensity = max(0.0, np.dot(vertex_normal, light_dir))
            diffuse += np.array(light.color) * diff_intensity * light.intensity
            
            # Specular component (Blinn-Phong)
            if material.specular_intensity > 0:
                view_dir = camera_pos - vertex_pos
                view_dir = view_dir / np.linalg.norm(view_dir)
                half_dir = light_dir + view_dir
                half_dir = half_dir / np.linalg.norm(half_dir)
                
                spec_intensity = max(0.0, np.dot(vertex_normal, half_dir))
                spec_intensity = pow(spec_intensity, material.specular_power)
                specular += np.array(light.color) * spec_intensity * material.specular_intensity * light.intensity
        
        # Combine components
        diffuse_color = np.array(material.base_color) * diffuse
        
        # Metallic workflow: metals have colored specular
        if material.metallic > 0.5:
            specular = specular * np.array(material.base_color)
        
        final_color = ambient + diffuse_color + specular
        
        # Emissive
        if material.emissive != (0.0, 0.0, 0.0):
            final_color += np.array(material.emissive)
        
        # Clamp to valid range
        final_color = np.clip(final_color, 0.0, 1.0)
        
        return tuple(final_color)
    
    def get_polyform_material(self, poly: Dict[str, Any]) -> Material:
        """
        Determine material for a polyform based on properties.
        
        Priority:
        1. Explicit material assignment
        2. Type-based (triangles vs squares)
        3. Stability-based coloring
        4. Default
        """
        # Check for explicit material
        if 'material' in poly:
            mat_name = poly['material']
            if mat_name in self.materials:
                return self.materials[mat_name]
        
        # Type-based
        sides = poly.get('sides', 4)
        stability = poly.get('stability_score', 0.5)
        
        # Choose color based on sides
        if sides == 3:
            base_name = 'cyan'
        elif sides == 4:
            base_name = 'green'
        elif sides == 5:
            base_name = 'orange'
        elif sides == 6:
            base_name = 'purple'
        else:
            base_name = 'yellow'
        
        # Choose material type based on stability
        if stability > 0.8:
            mat_type = MaterialType.GLOSSY
        elif stability > 0.5:
            mat_type = MaterialType.PLASTIC
        else:
            mat_type = MaterialType.MATTE
        
        mat_name = f"{base_name}_{mat_type.value}"
        
        return self.materials.get(mat_name, self.materials['cyan_matte'])
    
    def apply_edge_highlighting(self, poly: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate edge highlight geometry.
        
        Returns list of edge segments with enhanced properties.
        """
        vertices = np.array(poly.get('vertices', []))
        if len(vertices) < 2:
            return []
        
        edges = []
        n = len(vertices)
        
        for i in range(n):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % n]
            
            # Check if this edge is bonded
            is_bonded = False
            bond_quality = None
            
            if 'bonds' in poly:
                for bond in poly['bonds']:
                    if bond.get('edge_idx') == i:
                        is_bonded = True
                        bond_quality = bond.get('quality', 'good')
                        break
            
            # Color based on status
            if is_bonded:
                if bond_quality == 'perfect':
                    color = (0.0, 1.0, 0.0, 1.0)
                elif bond_quality == 'good':
                    color = (0.5, 1.0, 0.5, 1.0)
                else:
                    color = (1.0, 1.0, 0.0, 1.0)
                width = self.edge_width * 1.5
            else:
                color = self.edge_color
                width = self.edge_width
            
            edges.append({
                'start': v1,
                'end': v2,
                'color': color,
                'width': width,
                'is_bonded': is_bonded,
            })
        
        return edges
    
    def generate_vertex_colors(self, poly: Dict[str, Any], material: Material,
                              camera_pos: np.ndarray) -> np.ndarray:
        """
        Generate per-vertex colors with lighting.
        
        Returns: (N, 4) array of RGBA colors
        """
        vertices = np.array(poly.get('vertices', []))
        n = len(vertices)
        
        if n < 3:
            return np.ones((n, 4))
        
        # Compute face normal (assuming planar polygon)
        v0, v1, v2 = vertices[0], vertices[1], vertices[2]
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        normal = normal / (np.linalg.norm(normal) + 1e-8)
        
        # Compute lighting for each vertex
        colors = np.zeros((n, 4))
        
        for i, vert in enumerate(vertices):
            rgb = self.compute_lighting(vert, normal, material, camera_pos)
            colors[i] = (*rgb, material.opacity)
        
        return colors


class VisualPresetManager:
    """Manage and apply visual presets."""
    
    def __init__(self, renderer: VisualEnhancementRenderer):
        self.renderer = renderer
        self.presets = self._create_presets()
    
    def _create_presets(self) -> Dict[str, Dict[str, Any]]:
        """Define visual style presets."""
        return {
            'default': {
                'name': 'Default',
                'description': 'Balanced visualization',
                'material_type': MaterialType.PLASTIC,
                'edge_highlighting': True,
                'shadows': True,
            },
            'blueprint': {
                'name': 'Blueprint',
                'description': 'Technical drawing style',
                'material_type': MaterialType.MATTE,
                'edge_highlighting': True,
                'edge_width': 3.0,
                'shadows': False,
                'background': (0.1, 0.15, 0.2),
            },
            'render': {
                'name': 'Photo Render',
                'description': 'Realistic materials',
                'material_type': MaterialType.GLOSSY,
                'edge_highlighting': False,
                'shadows': True,
                'ambient_occlusion': True,
            },
            'glass': {
                'name': 'Glass',
                'description': 'Transparent materials',
                'material_type': MaterialType.GLASS,
                'edge_highlighting': True,
                'shadows': True,
            },
            'metal': {
                'name': 'Metallic',
                'description': 'Shiny metal surfaces',
                'material_type': MaterialType.METALLIC,
                'edge_highlighting': False,
                'shadows': True,
            },
            'paper': {
                'name': 'Paper Craft',
                'description': 'Origami-style',
                'material_type': MaterialType.PAPER,
                'edge_highlighting': True,
                'edge_width': 1.5,
                'shadows': True,
            },
        }
    
    def apply_preset(self, preset_name: str):
        """Apply a visual preset."""
        if preset_name not in self.presets:
            return
        
        preset = self.presets[preset_name]
        
        # Apply settings
        if 'edge_highlighting' in preset:
            self.renderer.enable_edge_highlighting = preset['edge_highlighting']
        
        if 'edge_width' in preset:
            self.renderer.edge_width = preset['edge_width']
        
        if 'shadows' in preset:
            self.renderer.enable_shadows = preset['shadows']
        
        # Update materials based on preset type
        mat_type = preset.get('material_type', MaterialType.PLASTIC)
        for name, material in self.renderer.materials.items():
            base_color = material.base_color
            updated = Material.from_preset(mat_type, base_color)
            self.renderer.materials[name] = updated


# Integration helper
def integrate_visual_enhancements(gl_renderer):
    """
    Integrate enhanced visuals into existing GLRenderer.
    
    Usage:
        renderer = GLRenderer(view)
        visual_system = integrate_visual_enhancements(renderer)
    """
    visual_renderer = VisualEnhancementRenderer()
    preset_manager = VisualPresetManager(visual_renderer)
    
    # Attach to existing renderer
    gl_renderer.visual_system = visual_renderer
    gl_renderer.preset_manager = preset_manager
    
    return visual_renderer
