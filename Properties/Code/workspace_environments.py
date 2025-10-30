"""
Workspace Environment Customization

Allows users to change the entire visual environment including:
- Background styles (solid, gradient, skybox, grid)
- Workspace themes (dark, light, colorful, minimal)
- 3D scene environments (studio, outdoor, space, blueprint)
- Camera presets (isometric, perspective, orthographic)
- Lighting schemes (natural, dramatic, soft, neon)
"""
import numpy as np
from typing import Dict, Any, Tuple, List
from enum import Enum
from dataclasses import dataclass


class EnvironmentTheme(Enum):
    """Predefined environment themes."""
    DARK_STUDIO = "dark_studio"
    LIGHT_STUDIO = "light_studio"
    BLUEPRINT = "blueprint"
    SPACE = "space"
    OUTDOOR = "outdoor"
    CYBERPUNK = "cyberpunk"
    ORIGAMI = "origami"
    MINIMAL = "minimal"


@dataclass
class EnvironmentConfig:
    """Complete environment configuration."""
    name: str
    description: str
    
    # Background
    background_type: str  # solid, gradient, image, procedural
    background_color_top: Tuple[float, float, float]
    background_color_bottom: Tuple[float, float, float]
    
    # Grid
    grid_visible: bool
    grid_color: Tuple[float, float, float, float]
    grid_size: int
    grid_spacing: float
    
    # Lighting
    ambient_color: Tuple[float, float, float]
    ambient_intensity: float
    light_positions: List[Tuple[float, float, float]]
    light_colors: List[Tuple[float, float, float]]
    light_intensities: List[float]
    
    # Fog/Atmosphere
    fog_enabled: bool
    fog_color: Tuple[float, float, float]
    fog_density: float
    
    # Camera
    default_distance: float
    default_elevation: float
    default_azimuth: float
    
    # UI Colors
    ui_primary_color: str
    ui_background_color: str
    ui_text_color: str


class WorkspaceEnvironmentManager:
    """
    Manages workspace visual environments.
    
    Users can:
    - Switch between preset themes
    - Customize individual elements
    - Save custom environments
    - Share environment configs
    """
    
    def __init__(self):
        self.current_environment: EnvironmentConfig = None
        self.environments = self._create_preset_environments()
        self.custom_environments: Dict[str, EnvironmentConfig] = {}
        
        # Set default
        self.apply_environment('dark_studio')
    
    def _create_preset_environments(self) -> Dict[str, EnvironmentConfig]:
        """Create preset environment configurations."""
        
        environments = {}
        
        # 1. DARK STUDIO (Default)
        environments['dark_studio'] = EnvironmentConfig(
            name="Dark Studio",
            description="Professional dark theme with subtle lighting",
            background_type="gradient",
            background_color_top=(0.04, 0.06, 0.08),
            background_color_bottom=(0.02, 0.03, 0.04),
            grid_visible=True,
            grid_color=(0.2, 0.2, 0.2, 0.3),
            grid_size=20,
            grid_spacing=1.0,
            ambient_color=(0.3, 0.3, 0.35),
            ambient_intensity=0.3,
            light_positions=[
                (5.0, 5.0, 10.0),
                (-3.0, 3.0, 8.0),
                (0.0, -5.0, 5.0)
            ],
            light_colors=[
                (1.0, 1.0, 0.95),
                (0.8, 0.85, 1.0),
                (0.9, 0.9, 1.0)
            ],
            light_intensities=[1.0, 0.5, 0.3],
            fog_enabled=False,
            fog_color=(0.1, 0.1, 0.15),
            fog_density=0.0,
            default_distance=20.0,
            default_elevation=20.0,
            default_azimuth=45.0,
            ui_primary_color="#00ffaa",
            ui_background_color="#0b0f14",
            ui_text_color="#ffffff"
        )
        
        # 2. LIGHT STUDIO
        environments['light_studio'] = EnvironmentConfig(
            name="Light Studio",
            description="Bright, clean workspace with high visibility",
            background_type="gradient",
            background_color_top=(0.95, 0.95, 0.98),
            background_color_bottom=(0.85, 0.87, 0.90),
            grid_visible=True,
            grid_color=(0.6, 0.6, 0.6, 0.5),
            grid_size=20,
            grid_spacing=1.0,
            ambient_color=(0.9, 0.9, 0.95),
            ambient_intensity=0.8,
            light_positions=[
                (5.0, 5.0, 10.0),
                (-3.0, 3.0, 8.0)
            ],
            light_colors=[
                (1.0, 0.98, 0.95),
                (0.95, 0.97, 1.0)
            ],
            light_intensities=[1.2, 0.6],
            fog_enabled=False,
            fog_color=(0.9, 0.9, 0.95),
            fog_density=0.0,
            default_distance=20.0,
            default_elevation=25.0,
            default_azimuth=45.0,
            ui_primary_color="#0066cc",
            ui_background_color="#f5f5f5",
            ui_text_color="#222222"
        )
        
        # 3. BLUEPRINT
        environments['blueprint'] = EnvironmentConfig(
            name="Blueprint",
            description="Technical drawing aesthetic with grid",
            background_type="solid",
            background_color_top=(0.1, 0.15, 0.25),
            background_color_bottom=(0.1, 0.15, 0.25),
            grid_visible=True,
            grid_color=(0.3, 0.5, 0.7, 0.8),
            grid_size=30,
            grid_spacing=0.5,
            ambient_color=(0.2, 0.3, 0.4),
            ambient_intensity=0.9,
            light_positions=[(0.0, 0.0, 20.0)],
            light_colors=[(1.0, 1.0, 1.0)],
            light_intensities=[1.0],
            fog_enabled=False,
            fog_color=(0.1, 0.15, 0.25),
            fog_density=0.0,
            default_distance=25.0,
            default_elevation=30.0,
            default_azimuth=0.0,
            ui_primary_color="#4da6ff",
            ui_background_color="#0d1929",
            ui_text_color="#e0e8f0"
        )
        
        # 4. SPACE
        environments['space'] = EnvironmentConfig(
            name="Space",
            description="Dark void with stars and dramatic lighting",
            background_type="procedural",
            background_color_top=(0.0, 0.0, 0.05),
            background_color_bottom=(0.0, 0.0, 0.0),
            grid_visible=False,
            grid_color=(0.1, 0.1, 0.2, 0.2),
            grid_size=20,
            grid_spacing=1.0,
            ambient_color=(0.05, 0.05, 0.1),
            ambient_intensity=0.1,
            light_positions=[
                (10.0, 0.0, 10.0),
                (-5.0, 8.0, 5.0)
            ],
            light_colors=[
                (1.0, 0.9, 0.8),
                (0.5, 0.6, 1.0)
            ],
            light_intensities=[1.5, 0.8],
            fog_enabled=True,
            fog_color=(0.0, 0.0, 0.05),
            fog_density=0.02,
            default_distance=30.0,
            default_elevation=15.0,
            default_azimuth=60.0,
            ui_primary_color="#ff00ff",
            ui_background_color="#000000",
            ui_text_color="#ffffff"
        )
        
        # 5. OUTDOOR
        environments['outdoor'] = EnvironmentConfig(
            name="Outdoor",
            description="Natural daylight with sky gradient",
            background_type="gradient",
            background_color_top=(0.4, 0.6, 1.0),
            background_color_bottom=(0.8, 0.9, 1.0),
            grid_visible=True,
            grid_color=(0.3, 0.5, 0.3, 0.4),
            grid_size=20,
            grid_spacing=1.0,
            ambient_color=(0.6, 0.7, 0.9),
            ambient_intensity=0.6,
            light_positions=[
                (10.0, 10.0, 15.0),
                (-5.0, 5.0, 10.0)
            ],
            light_colors=[
                (1.0, 0.95, 0.85),
                (0.7, 0.8, 1.0)
            ],
            light_intensities=[1.3, 0.4],
            fog_enabled=True,
            fog_color=(0.7, 0.8, 0.95),
            fog_density=0.01,
            default_distance=25.0,
            default_elevation=30.0,
            default_azimuth=45.0,
            ui_primary_color="#4caf50",
            ui_background_color="#e8f5e9",
            ui_text_color="#1b5e20"
        )
        
        # 6. CYBERPUNK
        environments['cyberpunk'] = EnvironmentConfig(
            name="Cyberpunk",
            description="Neon-lit futuristic environment",
            background_type="gradient",
            background_color_top=(0.05, 0.0, 0.1),
            background_color_bottom=(0.1, 0.0, 0.2),
            grid_visible=True,
            grid_color=(1.0, 0.0, 1.0, 0.6),
            grid_size=25,
            grid_spacing=0.8,
            ambient_color=(0.2, 0.0, 0.3),
            ambient_intensity=0.4,
            light_positions=[
                (5.0, 5.0, 10.0),
                (-5.0, 3.0, 8.0),
                (0.0, -5.0, 5.0)
            ],
            light_colors=[
                (1.0, 0.0, 1.0),
                (0.0, 1.0, 1.0),
                (1.0, 0.2, 0.5)
            ],
            light_intensities=[1.2, 1.0, 0.8],
            fog_enabled=True,
            fog_color=(0.3, 0.0, 0.5),
            fog_density=0.015,
            default_distance=22.0,
            default_elevation=18.0,
            default_azimuth=30.0,
            ui_primary_color="#ff00ff",
            ui_background_color="#1a0033",
            ui_text_color="#00ffff"
        )
        
        # 7. ORIGAMI
        environments['origami'] = EnvironmentConfig(
            name="Origami",
            description="Paper-craft aesthetic with soft shadows",
            background_type="gradient",
            background_color_top=(0.98, 0.95, 0.90),
            background_color_bottom=(0.95, 0.92, 0.85),
            grid_visible=False,
            grid_color=(0.8, 0.8, 0.8, 0.3),
            grid_size=20,
            grid_spacing=1.0,
            ambient_color=(0.95, 0.93, 0.88),
            ambient_intensity=0.7,
            light_positions=[
                (5.0, 8.0, 12.0),
                (-3.0, 5.0, 8.0)
            ],
            light_colors=[
                (1.0, 0.95, 0.85),
                (0.9, 0.95, 1.0)
            ],
            light_intensities=[1.0, 0.5],
            fog_enabled=False,
            fog_color=(0.95, 0.93, 0.88),
            fog_density=0.0,
            default_distance=18.0,
            default_elevation=25.0,
            default_azimuth=40.0,
            ui_primary_color="#ff9800",
            ui_background_color="#fff8e1",
            ui_text_color="#3e2723"
        )
        
        # 8. MINIMAL
        environments['minimal'] = EnvironmentConfig(
            name="Minimal",
            description="Clean, distraction-free workspace",
            background_type="solid",
            background_color_top=(0.15, 0.15, 0.15),
            background_color_bottom=(0.15, 0.15, 0.15),
            grid_visible=False,
            grid_color=(0.2, 0.2, 0.2, 0.2),
            grid_size=20,
            grid_spacing=1.0,
            ambient_color=(0.4, 0.4, 0.4),
            ambient_intensity=0.8,
            light_positions=[(0.0, 5.0, 15.0)],
            light_colors=[(1.0, 1.0, 1.0)],
            light_intensities=[1.0],
            fog_enabled=False,
            fog_color=(0.15, 0.15, 0.15),
            fog_density=0.0,
            default_distance=20.0,
            default_elevation=20.0,
            default_azimuth=45.0,
            ui_primary_color="#ffffff",
            ui_background_color="#262626",
            ui_text_color="#eeeeee"
        )
        
        return environments
    
    def apply_environment(self, env_name: str) -> bool:
        """
        Apply an environment by name.
        
        Returns True if successful, False if environment not found.
        """
        if env_name in self.environments:
            self.current_environment = self.environments[env_name]
            return True
        elif env_name in self.custom_environments:
            self.current_environment = self.custom_environments[env_name]
            return True
        return False
    
    def get_environment_names(self) -> List[str]:
        """Get list of available environment names."""
        return list(self.environments.keys()) + list(self.custom_environments.keys())
    
    def get_current_environment(self) -> EnvironmentConfig:
        """Get current environment configuration."""
        return self.current_environment
    
    def create_custom_environment(self, name: str, base_env: str = 'dark_studio') -> EnvironmentConfig:
        """
        Create a new custom environment based on an existing one.
        
        Args:
            name: Name for the custom environment
            base_env: Name of environment to use as template
            
        Returns:
            New environment config
        """
        if base_env not in self.environments:
            base_env = 'dark_studio'
        
        # Copy base environment
        base = self.environments[base_env]
        custom = EnvironmentConfig(
            name=name,
            description=f"Custom environment based on {base.name}",
            background_type=base.background_type,
            background_color_top=base.background_color_top,
            background_color_bottom=base.background_color_bottom,
            grid_visible=base.grid_visible,
            grid_color=base.grid_color,
            grid_size=base.grid_size,
            grid_spacing=base.grid_spacing,
            ambient_color=base.ambient_color,
            ambient_intensity=base.ambient_intensity,
            light_positions=base.light_positions.copy(),
            light_colors=base.light_colors.copy(),
            light_intensities=base.light_intensities.copy(),
            fog_enabled=base.fog_enabled,
            fog_color=base.fog_color,
            fog_density=base.fog_density,
            default_distance=base.default_distance,
            default_elevation=base.default_elevation,
            default_azimuth=base.default_azimuth,
            ui_primary_color=base.ui_primary_color,
            ui_background_color=base.ui_background_color,
            ui_text_color=base.ui_text_color
        )
        
        self.custom_environments[name] = custom
        return custom
    
    def get_preview_description(self, env_name: str) -> Dict[str, Any]:
        """
        Get a description suitable for preview display.
        
        Returns dict with:
        - name, description
        - visual characteristics
        - best for (use cases)
        """
        env = self.environments.get(env_name)
        if not env:
            return {}
        
        previews = {
            'dark_studio': {
                'icon': '🎬',
                'characteristics': ['Dark background', 'Subtle lighting', 'Professional'],
                'best_for': 'General use, long sessions',
                'mood': 'Focused and calm'
            },
            'light_studio': {
                'icon': '☀️',
                'characteristics': ['Bright background', 'High visibility', 'Clean'],
                'best_for': 'Presentations, printing',
                'mood': 'Energetic and clear'
            },
            'blueprint': {
                'icon': '📐',
                'characteristics': ['Technical grid', 'Precise alignment', 'Orthogonal'],
                'best_for': 'Technical work, measurements',
                'mood': 'Precise and structured'
            },
            'space': {
                'icon': '🌌',
                'characteristics': ['Dark void', 'Dramatic lighting', 'No distractions'],
                'best_for': 'Creative exploration, demos',
                'mood': 'Dramatic and immersive'
            },
            'outdoor': {
                'icon': '🌤️',
                'characteristics': ['Sky gradient', 'Natural light', 'Soft shadows'],
                'best_for': 'Organic designs, relaxed work',
                'mood': 'Natural and relaxed'
            },
            'cyberpunk': {
                'icon': '🌃',
                'characteristics': ['Neon colors', 'High contrast', 'Futuristic'],
                'best_for': 'Creative projects, inspiration',
                'mood': 'Bold and energetic'
            },
            'origami': {
                'icon': '📄',
                'characteristics': ['Paper colors', 'Soft light', 'Warm tones'],
                'best_for': 'Paper crafts, origami design',
                'mood': 'Warm and inviting'
            },
            'minimal': {
                'icon': '⬜',
                'characteristics': ['No grid', 'Flat background', 'Focused'],
                'best_for': 'Screenshots, minimal UI',
                'mood': 'Clean and distraction-free'
            }
        }
        
        info = previews.get(env_name, {})
        info['name'] = env.name
        info['description'] = env.description
        
        return info


def apply_environment_to_scene(gl_view, env_config: EnvironmentConfig):
    """
    Apply environment configuration to OpenGL view.
    
    Args:
        gl_view: GLViewWidget instance
        env_config: Environment configuration to apply
    """
    # Background color
    if env_config.background_type == "solid":
        color = env_config.background_color_top
        gl_view.setBackgroundColor(
            (int(color[0]*255), int(color[1]*255), int(color[2]*255))
        )
    elif env_config.background_type == "gradient":
        # Use bottom color for now (gradient requires shader)
        color = env_config.background_color_bottom
        gl_view.setBackgroundColor(
            (int(color[0]*255), int(color[1]*255), int(color[2]*255))
        )
    
    # Camera position
    gl_view.setCameraPosition(distance=env_config.default_distance)
    gl_view.orbit(env_config.default_azimuth, env_config.default_elevation)


def get_ui_stylesheet(env_config: EnvironmentConfig) -> str:
    """
    Generate Qt stylesheet based on environment configuration.
    
    Returns CSS-like stylesheet string for Qt widgets.
    """
    bg_color = env_config.ui_background_color
    text_color = env_config.ui_text_color
    primary_color = env_config.ui_primary_color
    
    # Lighten/darken for hover effects
    hover_bg = _adjust_color(bg_color, 1.2)
    
    stylesheet = f"""
    QMainWindow {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    QPushButton {{
        background-color: {primary_color};
        color: {text_color};
        border: none;
        padding: 6px 12px;
        border-radius: 3px;
    }}
    
    QPushButton:hover {{
        background-color: {hover_bg};
    }}
    
    QGroupBox {{
        border: 1px solid {primary_color};
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
        color: {text_color};
    }}
    
    QLabel {{
        color: {text_color};
    }}
    
    QComboBox {{
        background-color: {hover_bg};
        color: {text_color};
        border: 1px solid {primary_color};
        padding: 4px;
    }}
    """
    
    return stylesheet


def _adjust_color(hex_color: str, factor: float) -> str:
    """Adjust color brightness by factor."""
    # Simple implementation
    return hex_color  # Would need full implementation
