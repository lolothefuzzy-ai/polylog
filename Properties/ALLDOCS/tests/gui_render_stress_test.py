import pathlib
import sys

from PySide6 import QtCore, QtWidgets

# Ensure project root on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import desktop_app as d

app = QtWidgets.QApplication(sys.argv)
win = d.MainWindow()
win.show()  # create GL context

# Enable auto-orbit to exercise GL updates
win.auto_orbit_chk.setChecked(True)

# Add a mix of polygons and perform actions
for n in range(3, 9):
    win.sides_slider.setValue(n)
    win.on_add_polygon()

# Evaluate/place repeatedly on first two items if available
if win.combo_target.count() >= 2:
    win.combo_target.setCurrentIndex(0)
    win.combo_candidate.setCurrentIndex(1)
    win.on_evaluate()
    win.on_place()

# Quit after a short run to let timers and GL refresh execute
QtCore.QTimer.singleShot(2000, app.quit)

rc = app.exec()
print('RENDER_STRESS_EXIT', rc)
