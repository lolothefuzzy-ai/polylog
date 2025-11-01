import pathlib
import sys

from PySide6 import QtWidgets

# Ensure project root on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import desktop_app as d

app = QtWidgets.QApplication(sys.argv)
win = d.MainWindow()

# Add a second polygon via the UI slot to ensure evaluator paths
win.on_add_polygon()  # uses current slider (default 4)

# Select different target/candidate if needed
ids = [win.combo_target.itemText(i) for i in range(win.combo_target.count())]
if len(ids) >= 2:
    win.combo_target.setCurrentIndex(0)
    win.combo_candidate.setCurrentIndex(1)

# Evaluate connections
win.on_evaluate()
print('EVAL_OUT:', win.txt_out.toPlainText())

# Attempt placement (this will exercise fold sequencer fast-path)
try:
    win.on_place()
    print('PLACE_OUT:', win.txt_out.toPlainText())
except Exception as e:
    print('PLACE_ERR:', repr(e))
    raise

# Close immediately
win.close()
app.quit()
