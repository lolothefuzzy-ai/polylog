"""
Library Integration Demo

Demonstrates the complete workflow:
1. Generate random assemblies
2. Render thumbnails
3. Save to library
4. Simulate drag-drop operations

Run: python demo_library_integration.py
"""
import os
import sys
from typing import Any, Dict

# Ensure imports work
sys.path.insert(0, os.path.dirname(__file__))

from library_drag_drop import LibraryDragDropHandler
from library_thumbnail_renderer import LibraryThumbnailRenderer, ThumbnailConfig
from managers import RealWorkspaceManager
from polyform_library import get_library
from random_assembly_generator import RandomAssemblyGenerator


class MockAssembly:
    """Mock assembly for demo purposes."""
    
    def __init__(self):
        self.polyforms = []
        self.bonds = []
    
    def add_polyform(self, polyform: Dict[str, Any]) -> bool:
        """Add polyform to assembly."""
        # Normalize incoming polyform to canonical shape when possible
        try:
            from gui.polyform_adapter import normalize_polyform
            norm = normalize_polyform(polyform)
        except Exception:
            norm = dict(polyform)
            if 'id' not in norm:
                import uuid
                norm['id'] = str(uuid.uuid4())
            verts = []
            for v in norm.get('vertices', []):
                if isinstance(v, (list, tuple)):
                    if len(v) == 2:
                        verts.append((float(v[0]), float(v[1]), 0.0))
                    else:
                        verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
            if verts:
                norm['vertices'] = verts

        self.polyforms.append(norm)
        return True
    
    def get_all_polyforms(self):
        """Get all polyforms."""
        return self.polyforms
    
    def get_bonds(self):
        """Get bonds."""
        return self.bonds
    
    def add_bond(self, bond: Dict[str, Any]):
        """Add bond."""
        self.bonds.append(bond)


class MockWorkspace:
    """Mock workspace for demo."""
    
    def __init__(self):
        self.manager = RealWorkspaceManager()
        self.assembly = MockAssembly()
    
    def add_polyform(self, polyform: Dict[str, Any]) -> bool:
        """Add polyform to workspace."""
        return self.assembly.add_polyform(polyform)
    
    def screen_to_world(self, screen_x: float, screen_y: float):
        """Convert screen to world coordinates."""
        return self.manager.screen_to_world(screen_x, screen_y)
    
    def contains_point(self, screen_x: float, screen_y: float) -> bool:
        """Check if point is in workspace."""
        return self.manager.contains_point(screen_x, screen_y)


def demo_random_generation():
    """Demo 1: Generate random assemblies."""
    print("=" * 60)
    print("DEMO 1: Random Assembly Generation")
    print("=" * 60)
    
    generator = RandomAssemblyGenerator()
    
    # Generate different patterns
    patterns = ['circular', 'grid', 'spiral', 'random_cluster', 'linear', 'organic']
    
    for pattern in patterns:
        print(f"\nGenerating {pattern} assembly...")
        
        polyforms = generator.generate_random_assembly(
            num_polyforms=8,
            pattern=pattern,
            use_3d=True
        )
        
        print(f"  Generated {len(polyforms)} polyforms")
        
        # Show types
        type_counts = {}
        for p in polyforms:
            sides = p.get('sides', 0)
            type_counts[sides] = type_counts.get(sides, 0) + 1
        
        print(f"  Types: {type_counts}")
    
    # Show statistics
    stats = generator.get_statistics()
    print(f"\nGenerator statistics:")
    print(f"  Total generated: {stats['generated_count']}")
    print(f"  Type usage: {stats['type_usage']}")
    print(f"  Pattern success: {stats['pattern_success']}")
    
    print("\n✓ Random generation demo complete!\n")
    return generator


def demo_thumbnail_rendering(generator):
    """Demo 2: Render thumbnails."""
    print("=" * 60)
    print("DEMO 2: Thumbnail Rendering")
    print("=" * 60)
    
    # Create thumbnail renderer
    config = ThumbnailConfig(
        size=(256, 256),
        show_label=True,
        auto_color=True
    )
    
    renderer = LibraryThumbnailRenderer(config)
    
    # Generate a sample assembly
    print("\nGenerating sample assembly for thumbnails...")
    polyforms = generator.generate_random_assembly(
        num_polyforms=5,
        pattern='circular',
        use_3d=True
    )
    
    # Render individual polyforms
    print(f"\nRendering {len(polyforms)} individual polyform thumbnails...")
    
    thumbnail_dir = "demo_thumbnails"
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    for i, polyform in enumerate(polyforms):
        img = renderer.render_polyform(polyform, polyform_id=f"poly_{i}")
        
        output_path = os.path.join(thumbnail_dir, f"polyform_{i}.png")
        img.save(output_path)
        
        sides = polyform.get('sides', '?')
        print(f"  Saved {sides}-gon thumbnail: {output_path}")
    
    # Render complete assembly
    print("\nRendering assembly thumbnail...")
    
    assembly_data = {'polyforms': polyforms}
    assembly_img = renderer.render_assembly(assembly_data, assembly_id="demo_assembly")
    
    assembly_path = os.path.join(thumbnail_dir, "assembly_complete.png")
    assembly_img.save(assembly_path)
    print(f"  Saved assembly thumbnail: {assembly_path}")
    
    print(f"\n✓ Thumbnail rendering demo complete! Check {thumbnail_dir}/ directory\n")
    
    return polyforms


def demo_library_storage(polyforms):
    """Demo 3: Save to library."""
    print("=" * 60)
    print("DEMO 3: Library Storage")
    print("=" * 60)
    
    # Create library manager
    library = get_library("demo_library")
    
    # Clear previous data
    library.clear()
    print("\nCleared previous library data")
    
    # Add polyforms to library
    print(f"\nAdding {len(polyforms)} polyforms to library...")
    
    polyform_ids = []
    for i, polyform in enumerate(polyforms):
        polyform_id = library.add_polyform(polyform)
        polyform_ids.append(polyform_id)
        
        sides = polyform.get('sides', '?')
        print(f"  Added {sides}-gon with ID: {polyform_id[:8]}...")
    
    # Add complete assembly
    assembly_data = {
        'name': 'Demo Assembly',
        'polyforms': polyforms,
        'description': 'Sample assembly from demo'
    }
    
    assembly_id = library.add_assembly(assembly_data)
    print(f"\nAdded assembly with ID: {assembly_id[:8]}...")
    
    # Search library
    print("\nSearching library for squares...")
    squares = library.search_polyforms(sides=4)
    print(f"  Found {len(squares)} squares")
    
    print("\nSearching library for triangles...")
    triangles = library.search_polyforms(sides=3)
    print(f"  Found {len(triangles)} triangles")
    
    # List all
    all_polyforms = library.get_all_polyforms()
    all_assemblies = library.get_all_assemblies()
    
    print(f"\nLibrary contents:")
    print(f"  Total polyforms: {len(all_polyforms)}")
    print(f"  Total assemblies: {len(all_assemblies)}")
    
    print("\n✓ Library storage demo complete!\n")
    
    return library, polyform_ids


def demo_drag_drop_simulation(library, polyform_ids):
    """Demo 4: Simulate drag-drop operations."""
    print("=" * 60)
    print("DEMO 4: Drag-Drop Simulation")
    print("=" * 60)
    
    # Create workspace and drag-drop handler
    workspace = MockWorkspace()
    drag_handler = LibraryDragDropHandler(workspace, library)
    
    # Enable snap-to-grid
    drag_handler.set_snap_to_grid(True, grid_size=1.0)
    print("\nSnap-to-grid enabled (grid size: 1.0)")
    
    # Simulate dragging polyforms from library to workspace
    print(f"\nSimulating drag-drop of {len(polyform_ids)} polyforms...")
    
    for i, polyform_id in enumerate(polyform_ids):
        # Start drag
        start_x, start_y = 100.0, 100.0
        
        success = drag_handler.start_drag(polyform_id, start_x, start_y)
        
        if success:
            print(f"\n  [{i+1}] Started drag for polyform {polyform_id[:8]}...")
            
            # Simulate mouse movement
            drag_handler.update_drag(start_x + 50, start_y + 50)
            print(f"      Dragging to ({start_x + 50}, {start_y + 50})...")
            
            # Drop at final position
            drop_x = i * 50.0
            drop_y = i * 30.0
            
            dropped = drag_handler.complete_drag(drop_x, drop_y)
            
            if dropped:
                print(f"      ✓ Dropped at ({drop_x}, {drop_y})")
            else:
                print(f"      ✗ Drop failed")
        else:
            print(f"\n  [{i+1}] ✗ Failed to start drag for {polyform_id[:8]}")
    
    # Check workspace
    workspace_polyforms = workspace.assembly.get_all_polyforms()
    print(f"\nWorkspace now contains {len(workspace_polyforms)} polyforms")
    
    # Show types in workspace
    type_counts = {}
    for p in workspace_polyforms:
        sides = p.get('sides', 0)
        type_counts[sides] = type_counts.get(sides, 0) + 1
    
    print(f"Workspace types: {type_counts}")
    
    print("\n✓ Drag-drop simulation demo complete!\n")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " " * 10 + "POLYLOG LIBRARY INTEGRATION DEMO" + " " * 16 + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    try:
        # Demo 1: Random generation
        generator = demo_random_generation()
        
        # Demo 2: Thumbnail rendering
        polyforms = demo_thumbnail_rendering(generator)
        
        # Demo 3: Library storage
        library, polyform_ids = demo_library_storage(polyforms)
        
        # Demo 4: Drag-drop simulation
        demo_drag_drop_simulation(library, polyform_ids)
        
        print("=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nGenerated files:")
        print("  - demo_thumbnails/       (thumbnail images)")
        print("  - demo_library/          (library database)")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
