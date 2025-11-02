"""
Library Thumbnail Renderer

Generates visual thumbnails for polyforms in the library.

Features:
- Rasterized polygon rendering
- Color-coded by type or properties
- Automatic scaling and centering
- Caching for performance
- Multiple thumbnail sizes
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail rendering."""
    size: Tuple[int, int] = (128, 128)
    background_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    edge_color: Tuple[int, int, int] = (0, 0, 0)
    edge_width: int = 2
    fill_alpha: int = 200
    padding: int = 10
    show_label: bool = True
    label_font_size: int = 12
    auto_color: bool = True


class LibraryThumbnailRenderer:
    """
    Renders thumbnails for polyforms in the library.
    
    Creates visual representations that can be displayed in GUI.
    """
    
    def __init__(self, config: Optional[ThumbnailConfig] = None):
        """
        Initialize thumbnail renderer.
        
        Args:
            config: Thumbnail configuration (uses default if None)
        """
        self.config = config or ThumbnailConfig()
        
        # Cache rendered thumbnails
        self.cache: Dict[str, Image.Image] = {}
        self.cache_max_size = 100
        
        # Color mapping for polygon types
        self.type_colors = {
            3: (255, 100, 100),   # Triangles - Red
            4: (100, 150, 255),   # Squares - Blue
            5: (100, 255, 150),   # Pentagons - Green
            6: (255, 200, 100),   # Hexagons - Orange
            7: (200, 100, 255),   # Heptagons - Purple
            8: (255, 150, 200),   # Octagons - Pink
            9: (150, 255, 255),   # Nonagons - Cyan
            10: (255, 255, 100),  # Decagons - Yellow
            11: (150, 150, 255),  # Hendecagons - Light Purple
            12: (255, 150, 100),  # Dodecagons - Salmon
        }
    
    def render_polyform(
        self,
        polyform_data: Dict[str, Any],
        polyform_id: str = None
    ) -> Image.Image:
        """
        Render a polyform as a thumbnail image.
        
        Args:
            polyform_data: Polyform data dictionary
            polyform_id: Optional ID for caching
            
        Returns:
            PIL Image thumbnail
        """
        # Check cache
        cache_key = self._get_cache_key(polyform_data, polyform_id)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Create image
        img = Image.new('RGBA', self.config.size, self.config.background_color)
        draw = ImageDraw.Draw(img)
        
        # Get vertices
        vertices = polyform_data.get('vertices', [])
        
        if not vertices:
            # Draw placeholder
            self._draw_placeholder(draw)
        else:
            # Transform vertices to thumbnail space
            thumb_vertices = self._transform_to_thumbnail_space(vertices)
            
            # Determine fill color
            fill_color = self._get_fill_color(polyform_data)
            
            # Draw polygon
            if len(thumb_vertices) >= 3:
                draw.polygon(
                    thumb_vertices,
                    fill=fill_color + (self.config.fill_alpha,),
                    outline=self.config.edge_color,
                    width=self.config.edge_width
                )
        
        # Draw label if enabled
        if self.config.show_label:
            label = self._get_label(polyform_data)
            self._draw_label(draw, label)
        
        # Cache and return
        self._add_to_cache(cache_key, img)
        
        return img
    
    def render_assembly(
        self,
        assembly_data: Dict[str, Any],
        assembly_id: str = None
    ) -> Image.Image:
        """
        Render an entire assembly as a thumbnail.
        
        Shows all polyforms in the assembly.
        
        Args:
            assembly_data: Assembly data with polyforms
            assembly_id: Optional ID for caching
            
        Returns:
            PIL Image thumbnail
        """
        # Check cache
        cache_key = self._get_cache_key(assembly_data, assembly_id)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Create image
        img = Image.new('RGBA', self.config.size, self.config.background_color)
        draw = ImageDraw.Draw(img)
        
        # Get all polyforms
        polyforms = assembly_data.get('polyforms', [])
        
        if not polyforms:
            self._draw_placeholder(draw)
        else:
            # Collect all vertices
            all_vertices = []
            for poly in polyforms:
                verts = poly.get('vertices', [])
                if verts:
                    all_vertices.extend(verts)
            
            if all_vertices:
                # Transform to thumbnail space (unified)
                thumb_space = self._get_thumbnail_transform(all_vertices)
                
                # Draw each polyform
                for poly in polyforms:
                    verts = poly.get('vertices', [])
                    if len(verts) >= 3:
                        thumb_verts = self._apply_transform(verts, thumb_space)
                        
                        fill_color = self._get_fill_color(poly)
                        
                        draw.polygon(
                            thumb_verts,
                            fill=fill_color + (self.config.fill_alpha,),
                            outline=self.config.edge_color,
                            width=max(1, self.config.edge_width // 2)
                        )
        
        # Draw label
        if self.config.show_label:
            label = f"{len(polyforms)} polyforms"
            self._draw_label(draw, label)
        
        # Cache and return
        self._add_to_cache(cache_key, img)
        
        return img
    
    def render_batch(
        self,
        polyforms: List[Tuple[str, Dict[str, Any]]]
    ) -> Dict[str, Image.Image]:
        """
        Render multiple polyforms at once.
        
        Args:
            polyforms: List of (id, polyform_data) tuples
            
        Returns:
            Dictionary mapping IDs to thumbnail images
        """
        results = {}
        
        for poly_id, poly_data in polyforms:
            results[poly_id] = self.render_polyform(poly_data, poly_id)
        
        return results
    
    def clear_cache(self):
        """Clear thumbnail cache."""
        self.cache.clear()
    
    def _get_cache_key(self, data: Dict[str, Any], data_id: str = None) -> str:
        """Generate cache key for data."""
        if data_id:
            return data_id
        
        # Hash the data
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _add_to_cache(self, key: str, img: Image.Image):
        """Add image to cache, managing size."""
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        
        self.cache[key] = img
    
    def _transform_to_thumbnail_space(self, vertices: List) -> List[Tuple[int, int]]:
        """Transform 3D vertices to 2D thumbnail coordinates."""
        verts_array = np.array(vertices)
        
        # Project to 2D (use X, Y)
        verts_2d = verts_array[:, :2]
        
        # Get bounds
        min_vals = verts_2d.min(axis=0)
        max_vals = verts_2d.max(axis=0)
        
        # Compute scale to fit in thumbnail with padding
        width = self.config.size[0] - 2 * self.config.padding
        height = self.config.size[1] - 2 * self.config.padding
        
        data_width = max_vals[0] - min_vals[0]
        data_height = max_vals[1] - min_vals[1]
        
        if data_width == 0 or data_height == 0:
            scale = 1.0
        else:
            scale = min(width / data_width, height / data_height)
        
        # Center in thumbnail
        center_x = self.config.size[0] / 2
        center_y = self.config.size[1] / 2
        
        data_center = (min_vals + max_vals) / 2
        
        # Transform vertices
        thumb_verts = []
        for v in verts_2d:
            # Translate to origin, scale, translate to center
            x = (v[0] - data_center[0]) * scale + center_x
            y = (v[1] - data_center[1]) * scale + center_y
            
            thumb_verts.append((int(x), int(y)))
        
        return thumb_verts
    
    def _get_thumbnail_transform(self, all_vertices: List) -> Dict[str, Any]:
        """Compute transform parameters for multiple polyforms."""
        verts_array = np.array(all_vertices)
        
        # Project to 2D
        verts_2d = verts_array[:, :2]
        
        # Get bounds
        min_vals = verts_2d.min(axis=0)
        max_vals = verts_2d.max(axis=0)
        
        # Compute scale
        width = self.config.size[0] - 2 * self.config.padding
        height = self.config.size[1] - 2 * self.config.padding
        
        data_width = max_vals[0] - min_vals[0]
        data_height = max_vals[1] - min_vals[1]
        
        if data_width == 0 or data_height == 0:
            scale = 1.0
        else:
            scale = min(width / data_width, height / data_height)
        
        # Center
        center_x = self.config.size[0] / 2
        center_y = self.config.size[1] / 2
        data_center = (min_vals + max_vals) / 2
        
        return {
            'scale': scale,
            'center_x': center_x,
            'center_y': center_y,
            'data_center': data_center
        }
    
    def _apply_transform(self, vertices: List, transform: Dict[str, Any]) -> List[Tuple[int, int]]:
        """Apply transform to vertices."""
        verts_array = np.array(vertices)
        verts_2d = verts_array[:, :2]
        
        scale = transform['scale']
        center_x = transform['center_x']
        center_y = transform['center_y']
        data_center = transform['data_center']
        
        thumb_verts = []
        for v in verts_2d:
            x = (v[0] - data_center[0]) * scale + center_x
            y = (v[1] - data_center[1]) * scale + center_y
            thumb_verts.append((int(x), int(y)))
        
        return thumb_verts
    
    def _get_fill_color(self, polyform_data: Dict[str, Any]) -> Tuple[int, int, int]:
        """Get fill color for polyform."""
        if not self.config.auto_color:
            # Use specified color if available
            color = polyform_data.get('color', (150, 150, 150))
            return tuple(color[:3])
        
        # Auto-color based on polygon type
        sides = polyform_data.get('sides', 4)
        
        return self.type_colors.get(sides, (150, 150, 150))
    
    def _get_label(self, polyform_data: Dict[str, Any]) -> str:
        """Get label text for polyform."""
        sides = polyform_data.get('sides', '?')
        
        # Type names
        type_names = {
            3: "Tri",
            4: "Quad",
            5: "Pent",
            6: "Hex",
            7: "Hept",
            8: "Oct",
            9: "Non",
            10: "Dec",
            11: "Hend",
            12: "Dodec"
        }
        
        return type_names.get(sides, f"{sides}-gon")
    
    def _draw_label(self, draw: ImageDraw.ImageDraw, text: str):
        """Draw label text on thumbnail."""
        # Try to load font
        try:
            font = ImageFont.truetype("arial.ttf", self.config.label_font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text size (using textbbox for newer Pillow)
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(text) * 6
            text_height = 10
        
        # Position at bottom
        x = (self.config.size[0] - text_width) // 2
        y = self.config.size[1] - text_height - 5
        
        # Draw background
        draw.rectangle(
            [x - 2, y - 2, x + text_width + 2, y + text_height + 2],
            fill=(255, 255, 255, 200)
        )
        
        # Draw text
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
    
    def _draw_placeholder(self, draw: ImageDraw.ImageDraw):
        """Draw placeholder for empty/invalid polyform."""
        # Draw X
        padding = 20
        draw.line(
            [padding, padding, self.config.size[0] - padding, self.config.size[1] - padding],
            fill=(200, 200, 200),
            width=2
        )
        draw.line(
            [self.config.size[0] - padding, padding, padding, self.config.size[1] - padding],
            fill=(200, 200, 200),
            width=2
        )
        
        # Text
        self._draw_label(draw, "Empty")


class ThumbnailCache:
    """
    Persistent thumbnail cache.
    
    Saves rendered thumbnails to disk for faster loading.
    """
    
    def __init__(self, cache_dir: str):
        """
        Initialize thumbnail cache.
        
        Args:
            cache_dir: Directory to store cached thumbnails
        """
        self.cache_dir = cache_dir
        
        # Ensure directory exists
        import os
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Optional[Image.Image]:
        """Get cached thumbnail."""
        import os
        
        cache_path = os.path.join(self.cache_dir, f"{key}.png")
        
        if os.path.exists(cache_path):
            try:
                return Image.open(cache_path)
            except:
                return None
        
        return None
    
    def put(self, key: str, img: Image.Image):
        """Save thumbnail to cache."""
        import os
        
        cache_path = os.path.join(self.cache_dir, f"{key}.png")
        
        try:
            img.save(cache_path, "PNG")
        except Exception as e:
            print(f"Failed to cache thumbnail: {e}")
    
    def clear(self):
        """Clear all cached thumbnails."""
        import os
        import shutil
        
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)


# Quick access functions
_global_renderer = None

def render_thumbnail(
    polyform_data: Dict[str, Any],
    size: Tuple[int, int] = (128, 128)
) -> Image.Image:
    """
    Quick function to render a thumbnail.
    
    Usage:
        img = render_thumbnail(polyform_data)
        img.save("thumbnail.png")
        # or display in GUI
    """
    global _global_renderer
    
    if _global_renderer is None:
        config = ThumbnailConfig(size=size)
        _global_renderer = LibraryThumbnailRenderer(config)
    
    return _global_renderer.render_polyform(polyform_data)


def get_renderer(config: Optional[ThumbnailConfig] = None) -> LibraryThumbnailRenderer:
    """Get global renderer instance."""
    global _global_renderer
    
    if _global_renderer is None or config is not None:
        _global_renderer = LibraryThumbnailRenderer(config)
    
    return _global_renderer
