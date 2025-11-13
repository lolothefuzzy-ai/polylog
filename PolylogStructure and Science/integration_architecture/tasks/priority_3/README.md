# Priority 3 — Detection Phases 3–5 (INT-014)

## TASK-DET-001: Pattern Analysis Threshold Tuning

- **File:** `scripts/tune_pattern_thresholds.py`
- **Dependencies:** `opencv-python`, `numpy`
- **Code Stub:**

  ```python
  import cv2
  import numpy as np
  from pathlib import Path

  from polylog6.detection.patterns import PatternAnalyzer
  from polylog6.detection.segmentation import ImageSegmenter


  def analyze_symmetry_distribution(fixtures_dir: Path) -> dict[str, float]:
      segmenter = ImageSegmenter()
      analyzer = PatternAnalyzer()

      symmetries: list[float] = []
      fft_magnitudes: list[float] = []

      for img_path in fixtures_dir.glob("*.png"):
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        regions = segmenter.segment(img)

        for region in regions:
            stats = analyzer.analyze_region(region["mask"], region["bbox"])
            symmetries.append(stats["symmetry"])
            fft_magnitudes.extend(peak["magnitude"] for peak in stats.get("fft_peaks", []))

      symmetry_threshold = float(np.percentile(symmetries, 75))
      fft_threshold = float(np.percentile(fft_magnitudes, 75))

      print("Recommended thresholds:")
      print(f"  symmetry_threshold: {symmetry_threshold:.2f}")
      print(f"  fft_magnitude_threshold: {fft_threshold:.2f}")

      return {"symmetry": symmetry_threshold, "fft": fft_threshold}


  if __name__ == "__main__":
      analyze_symmetry_distribution(Path("tests/fixtures/images"))
  ```

- **Validation:** CLI prints numeric thresholds without errors; optional JSON export for later consumption
- **Resources:** NumPy percentile reference <https://numpy.org/doc/stable/reference/generated/numpy.percentile.html>

## TASK-DET-002: Pattern Analysis Regression Tests

- **File:** `tests/test_pattern_analysis_real.py`
- **Dependencies:** `pytest`, `opencv-python`
- **Test Skeleton:**

  ```python
  import cv2
  import pytest
  from pathlib import Path

  from polylog6.detection.patterns import PatternAnalyzer
  from polylog6.detection.segmentation import ImageSegmenter


  @pytest.fixture
  def fixture_images():
      fixtures_dir = Path("tests/fixtures/images")
      if not fixtures_dir.exists():
          pytest.skip("Fixtures not available")

      images = {}
      for img_path in fixtures_dir.glob("*.png"):
          image = cv2.imread(str(img_path))
          if image is not None:
              images[img_path.name] = image
      return images


  def test_symmetry_in_range(fixture_images):
      segmenter = ImageSegmenter()
      analyzer = PatternAnalyzer()

      for image in fixture_images.values():
          regions = segmenter.segment(image)
          for region in regions:
              stats = analyzer.analyze_region(region["mask"], region["bbox"])
              assert 0.0 <= stats["symmetry"] <= 1.0


  def test_fft_peak_limits(fixture_images):
      segmenter = ImageSegmenter()
      analyzer = PatternAnalyzer()

      for image in fixture_images.values():
          regions = segmenter.segment(image)
          for region in regions:
              stats = analyzer.analyze_region(region["mask"], region["bbox"])
              assert len(stats["fft_peaks"]) <= 10
  ```

- **Validation:** `pytest tests/test_pattern_analysis_real.py -v` passes against updated fixtures
- **Resources:** Pytest fixtures guide <https://docs.pytest.org/en/stable/how-to/fixtures.html>
