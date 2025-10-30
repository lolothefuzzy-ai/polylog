import sys, time, argparse, json, random, tracemalloc, pathlib
import numpy as np

# Ensure project root in path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from polygon_utils import create_polygon_3d

# Optional GUI imports
try:
    from PySide6 import QtWidgets
    import pyqtgraph.opengl as gl
    from desktop_app import GLRenderer
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False


class Assembly:
    def __init__(self):
        self.polyforms = {}
        self.bonds = []
        self._next_id = 1
    def add_polyform(self, p):
        if 'id' not in p:
            p['id'] = f"poly_{self._next_id}"
            self._next_id += 1
        self.polyforms[p['id']] = p
    def get_polyform(self, pid):
        return self.polyforms.get(pid)
    def get_all_polyforms(self):
        return list(self.polyforms.values())
    def get_bonds(self):
        return self.bonds


def build_assembly(n: int, sides_min=3, sides_max=8, spread=0.5) -> (Assembly, float):
    asm = Assembly()
    t0 = time.time()
    for i in range(n):
        sides = random.randint(sides_min, sides_max)
        # Spread positions to avoid total overlap
        x = (i % 100) * spread
        y = ((i // 100) % 100) * spread
        z = ((i // 10000) % 10) * 0.1
        p = create_polygon_3d(sides, position=(x, y, z), thickness=0.08)
        asm.add_polyform(p)
    return asm, time.time() - t0


def render_assembly_gui(asm: Assembly, frames: int = 30) -> dict:
    if not GUI_AVAILABLE:
        return {'render_supported': False}
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    view = gl.GLViewWidget(); view.resize(640, 480)
    renderer = GLRenderer(view, use_3d_meshes=True)
    renderer.set_assembly_reference(asm)
    t0 = time.time()
    renderer.render_assembly(asm)
    view.show()
    # Pump a few frames
    t_start = time.time(); frames_done = 0
    while frames_done < frames:
        app.processEvents()
        frames_done += 1
    elapsed = time.time() - t_start
    fps = frames_done / elapsed if elapsed > 0 else 0.0
    view.close()
    return {
        'render_supported': True,
        'frames': frames_done,
        'fps': fps,
        'initial_render_ms': (time.time() - t0) * 1000.0,
    }


def main():
    parser = argparse.ArgumentParser(description='Large-scale 3D stress test')
    parser.add_argument('--count', type=int, default=1000, help='Number of polyforms')
    parser.add_argument('--frames', type=int, default=30, help='Frames to measure FPS (GUI only)')
    parser.add_argument('--no-gui', action='store_true', help='Skip GUI render even if available')
    args = parser.parse_args()

    tracemalloc.start()
    t_build0 = time.time()
    asm, build_time = build_assembly(args.count)
    snapshot1 = tracemalloc.take_snapshot()
    mem_stats = snapshot1.statistics('filename')
    total_bytes = sum(s.size for s in mem_stats)

    result = {
        'count': args.count,
        'build_time_s': round(build_time, 4),
        'peak_mem_mb': round(total_bytes / (1024*1024), 2),
        'gui': False,
        'fps': None,
        'initial_render_ms': None,
    }

    if GUI_AVAILABLE and not args.no_gui:
        r = render_assembly_gui(asm, frames=args.frames)
        result['gui'] = r.get('render_supported', False)
        result['fps'] = r.get('fps')
        result['initial_render_ms'] = r.get('initial_render_ms')

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
