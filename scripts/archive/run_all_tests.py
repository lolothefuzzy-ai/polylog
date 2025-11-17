#!/usr/bin/env python3
"""
Run All Tests - Automated Test Suite
Fully automated testing with backend-frontend integration
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Import automated test suite
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from automated_test_suite import main

if __name__ == "__main__":
    sys.exit(main())

