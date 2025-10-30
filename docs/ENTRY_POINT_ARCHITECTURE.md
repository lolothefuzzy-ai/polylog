# Entry Point Architecture - Polylog Simulator

**Status:** Analysis & Clarity Document  
**Primary Goal:** Clarify the main entry point and eliminate confusion

---

## 🎯 Current State - THE PROBLEM

You have **multiple entry points** which creates confusion about what the primary entry is:

```
Entry Points Currently:
├── main.py (unified launcher)
├── pyproject.toml script: polylog = "main:main"
├── _archive_legacy_code/run_polylog.py (CLI - archived)
├── _archive_legacy_code/polylog_main.py (API - archived)
├── demo_library_integration.py (demo)
└── desktop_app.py (GUI - referenced but not standalone)

Problem: Users don't know what to run!
```

---

## 📊 Current Entry Point Analysis

### 1. `main.py` (Current "Unified" Entry Point)
**Status:** ❌ Confusing  
**What it does:** Acts as dispatcher/launcher
```python
python main.py              # Tries to launch GUI (broken fallback)
python main.py cli          # Tries to launch CLI (broken fallback)
python main.py api          # Launches API server
python main.py demo         # Launches demo
```

**Issues:**
- GUI mode falls back to demo (not clear)
- CLI mode references archived code
- Misleading help text
- No clear "this is Polylog Simulator"

### 2. `_archive_legacy_code/polylog_main.py` (API Server)
**Status:** ✅ Works  
**What it does:** FastAPI server implementation
```python
from polylog_main import start_api
```

**Issues:**
- Buried in archive folder
- Real implementation is hidden
- `main.py` references it indirectly

### 3. `_archive_legacy_code/run_polylog.py` (CLI)
**Status:** ⚠️ Archived but functional
**What it does:** Interactive CLI
```python
from run_polylog import main as cli_main
```

**Issues:**
- Archived but still referenced
- Not accessible to users

### 4. `demo_library_integration.py`
**Status:** ✅ Works  
**What it does:** Demonstration of system functionality

### 5. `desktop_app.py` (GUI)
**Status:** ⚠️ Not fully integrated
**What it does:** Desktop GUI with 3D visualization
**Issues:**
- Referenced in old `main.py` code
- Not actually working as standalone entry

---

## 🎯 RECOMMENDED SOLUTION: Clear Entry Point Architecture

### PRIMARY ENTRY POINT: `main.py` → "Polylog Simulator"

```
POLYLOG SIMULATOR (main.py)
├─ Unified Entry Point
├─ Single point of clarity
├─ Primary use case: `python main.py`
└─ Smart defaults (API + demo by default)
```

### THREE OPERATIONAL MODES

```
1. API SERVER MODE (Production/Integration)
   Command: python main.py api
   Port: 8000 (default)
   Use case: Integrate Polylog with other systems
   
2. INTERACTIVE DEMO MODE (User Exploration)
   Command: python main.py demo
   Port: N/A
   Use case: See Polylog Simulator in action
   
3. COMBINED MODE (Recommended Default)
   Command: python main.py (or python main.py combined)
   Port: 8000
   Use case: API running + demo in background
```

### CLEAR FILE ORGANIZATION

```
Polylog6/
├── main.py                           # PRIMARY ENTRY POINT ★
│   ├── Imports specific mode handlers
│   ├── Clear Polylog Simulator branding
│   └── Simple 3-mode selection
│
├── modes/                            # Mode implementations
│   ├── api_mode.py                  # API server
│   ├── demo_mode.py                 # Interactive demo
│   └── combined_mode.py             # Both together
│
├── _archive_legacy_code/            # For reference only
│   ├── run_polylog.py              # Old CLI (archived)
│   └── polylog_main.py             # Old main (now split)
│
└── demo_library_integration.py       # Imported by demo_mode
```

---

## ✅ PROPOSED MAIN.PY (Clear & Simple)

```python
#!/usr/bin/env python
"""
╔═══════════════════════════════════════════════════════════╗
║                  POLYLOG SIMULATOR v0.1.0                 ║
║          Interactive Polyform Design & Exploration        ║
╚═══════════════════════════════════════════════════════════╝

Entry point for all Polylog Simulator modes.

Usage:
  python main.py                  # Launch API + Demo (default)
  python main.py api              # API server only
  python main.py demo             # Interactive demo only
  python main.py -h               # Show help

This is the PRIMARY entry point for Polylog Simulator.
All other entry points are deprecated/archived.
"""

import sys
import argparse
from modes import api_mode, demo_mode, combined_mode


def main():
    parser = argparse.ArgumentParser(
        description="╔══════════════════════════════════════╗\n"
                    "║   POLYLOG SIMULATOR - Main Entry     ║\n"
                    "║   Interactive Polyform Explorer      ║\n"
                    "╚══════════════════════════════════════╝",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # Launch combined mode (API + Demo)
  python main.py api          # API server on port 8000
  python main.py demo         # Interactive demo only
  python main.py api --port 9000  # API on custom port

Modes:
  (default)  - Combined: API server + interactive demo
  api        - FastAPI server only
  demo       - Interactive demonstration only
        """
    )

    parser.add_argument(
        'mode',
        nargs='?',
        choices=['api', 'demo', 'combined'],
        default='combined',
        help='Operation mode (default: combined)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API server port (default: 8000)'
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='API server host (default: 127.0.0.1)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    try:
        # Print banner for clarity
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║           POLYLOG SIMULATOR - Launching                  ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")

        if args.mode == 'api':
            api_mode.launch(args.host, args.port, args.verbose)
        elif args.mode == 'demo':
            demo_mode.launch(args.verbose)
        elif args.mode == 'combined':
            combined_mode.launch(args.host, args.port, args.verbose)

        return 0

    except KeyboardInterrupt:
        print("\n\nPolylog Simulator - Shutdown by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Clarify Current State (IMMEDIATE)
- [ ] Create entry point documentation
- [ ] Update main.py with clear branding
- [ ] Add "POLYLOG SIMULATOR" banner on startup
- [ ] Document which mode to use for what

### Phase 2: Organize Code (OPTIONAL)
- [ ] Create `modes/` folder
- [ ] Split main.py functionality into separate mode files
- [ ] Update imports
- [ ] Keep legacy code clearly archived

### Phase 3: Update Documentation
- [ ] Update README with primary entry point
- [ ] Add quick start guide
- [ ] Remove references to internal entry points
- [ ] Document API vs Demo vs Combined

---

## 🎯 DECISION MATRIX

| Question | Answer | Why |
|----------|--------|-----|
| What is PRIMARY entry point? | `main.py` | Standard Python convention |
| What is default mode? | Combined (API + Demo) | Most useful for users |
| Should users use archived files? | No | Use main.py instead |
| How many entry points should users know about? | 1 (`main.py`) | Simplicity |
| Is there a "Polylog Simulator" brand? | YES | Clearly identify the project |

---

## 🚀 QUICK WINS (Do These Now)

### 1. Update main.py Docstring
```python
"""
Polylog Simulator - Primary Entry Point
========================================

Single unified entry point for all Polylog modes.
This is THE main entry point - use this to launch Polylog.
"""
```

### 2. Add Startup Banner
```python
print("""
╔═══════════════════════════════════════════════════════════╗
║        POLYLOG SIMULATOR v0.1.0 - Starting...            ║
║          Interactive Polyform Design System              ║
╚═══════════════════════════════════════════════════════════╝
""")
```

### 3. Update pyproject.toml Script
```toml
[project.scripts]
polylog = "main:main"  # Primary: Polylog Simulator
polylog-api = "modes.api:main"  # Secondary: API only
polylog-demo = "modes.demo:main"  # Secondary: Demo only
```

### 4. Create Simple README for Entry Points
```markdown
# Starting Polylog Simulator

The PRIMARY entry point is `main.py`:

```bash
# Start Polylog Simulator (recommended)
python main.py

# Start API server only
python main.py api

# Start demo only  
python main.py demo
```

That's it! Use `main.py` for everything.
```

---

## 📊 Entry Point Summary

### BEFORE (Current - Confusing)
```
User asks: "How do I run Polylog?"
Answer: "Uh... main.py? Or maybe polylog_main.py? 
         Or run_polylog.py? Or main.py with demo flag?"
Result: ❌ Confusion
```

### AFTER (Proposed - Clear)
```
User asks: "How do I run Polylog Simulator?"
Answer: "Just: python main.py"
        "Or: python main.py api"
        "Or: python main.py demo"
Result: ✅ Clear
```

---

## ✅ SUCCESS CRITERIA

Phase 1 is done when:
- [ ] Users can run `python main.py` and get Polylog Simulator
- [ ] Clear banner shows "POLYLOG SIMULATOR" on startup
- [ ] Documentation says use `main.py` (not other entry points)
- [ ] No references to polylog_main.py or run_polylog.py in main documentation
- [ ] Three modes clearly explained: api, demo, combined

---

## 📚 Related Documentation

- **README_UNIFIED.md** - Master documentation index
- **PHASE1_COMPLETE_SUMMARY.md** - Recent pruning work
- **pyproject.toml** - Package configuration with entry point

---

**Recommendation:** Implement quick wins immediately, then plan Phase 2 reorganization.

This clarifies the project identity: **Polylog Simulator** with a single, clear entry point.
