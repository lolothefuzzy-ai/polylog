# Immediate Tasks (< 2 Hours)

## TASK-IMM-001: Fix pytest path resolution

- **File:** `pytest.ini`

- **Code:**

  ```ini
  [pytest]
  pythonpath = src
  testpaths = tests
  python_files = test_*.py
  ```

- **Validation:** `pytest tests/test_segmentation_regression.py -v`

- **Resources:** Standard pytest configuration

## TASK-IMM-002: Complete calibration run

- **File:** `scripts/calibrate_segmentation.py`

- **Command:** `python scripts/calibrate_segmentation.py`

- **Expected Output:**

  - `tests/fixtures/segmentation_snapshots/` (3 subdirectories with PNGs)

  - `tests/fixtures/expected_segmentations.json` (3 complete entries)

- **Validation:** JSON includes `expected_regions` and `felzenszwalb_params` for every fixture

- **Resources:** Existing script
