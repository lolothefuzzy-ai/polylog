import pathlib
import sys

from PySide6 import QtWidgets

# Ensure project root in path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import desktop_app as d
import validators as V

app = QtWidgets.QApplication(sys.argv)
win = d.MainWindow()

# Validate integrity for polygons 3..12 via UI interactions
results = []
# Ensure at least one seed exists (MainWindow._seed already adds one)
for n in range(3, 13):
    win.sides_slider.setValue(n)
    win.on_add_polygon()  # adds new polygon
    asm = win.assembly
    # Integrity check for all current polyforms
    ok_all = True
    for p in asm.get_all_polyforms():
        ok, meta = V.check_polyform_integrity(p, tol_relative=2e-3)
        if not ok:
            ok_all = False
            print('INTEGRITY_FAIL:', p.get('id'), meta)
            break
    # Try an evaluation/placement if there are at least 2 polys
    if len(asm.get_all_polyforms()) >= 2:
        win.combo_target.setCurrentIndex(0)
        win.combo_candidate.setCurrentIndex(len(asm.get_all_polyforms()) - 1)
        try:
            win.on_evaluate()
            win.on_place()
        except Exception as e:
            print('PLACE_EXCEPTION:', repr(e))
            ok_all = False
    # Assembly-level consistency
    ok_cons, meta_cons = V.check_assembly_consistency(asm, tol_relative=2e-3)
    if not ok_cons:
        print('CONSISTENCY_WARN:', meta_cons)
    results.append((n, ok_all and ok_cons))

# Simple report
fails = [n for (n, ok) in results if not ok]
print('RANGE_RESULTS:', {'fails': fails, 'count': len(results)})

# Visual preview smoke (should produce a non-null pixmap)
pix = win._render_preview(win.assembly.get_all_polyforms(), size=64)
print('PIXMAP_NULL:', pix.isNull())

win.close()
app.quit()
