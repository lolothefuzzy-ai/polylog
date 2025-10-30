"""
Top-level entry point for the Polylog6 project.
Delegates to the implementation found in `Code/main.py` so users can run:

    python main.py [mode]

This keeps the canonical entry point at repository root while preserving the
existing implementation under `Code/` for compatibility.
"""

import sys
from Code import main as code_main

if __name__ == '__main__':
    # Delegate to Code.main.main(), preserving exit code semantics
    sys.exit(code_main.main())
