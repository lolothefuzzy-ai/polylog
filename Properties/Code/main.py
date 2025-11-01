#!/usr/bin/env python
"""
╔═══════════════════════════════════════════════════════════╗
║              POLYLOG SIMULATOR v0.1.0                    ║
║         Interactive Polyform Design & Exploration         ║
╚═══════════════════════════════════════════════════════════╝

PRIMARY ENTRY POINT for Polylog Simulator.

This is the main entry point for all Polylog operations.
Use this script to launch Polylog in any mode.

Usage:
  python main.py                # Run GUI (default)
  python main.py gui            # Desktop GUI
  python main.py api            # API server only
  python main.py demo           # Interactive demo only
  python main.py combined       # API server + demo
  python main.py -h             # Show help

Modes:
  (default) - GUI: Desktop graphical interface
  gui       - Desktop GUI (same as default)
  api       - FastAPI server on port 8000
  demo      - Interactive demonstration
  combined  - API server + interactive demo

API Options:
  --host HOST  - Server host (default: 127.0.0.1)
  --port PORT  - Server port (default: 8000)
  -v, --verbose - Verbose output
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="POLYLOG SIMULATOR - Main Entry Point",
        epilog="Examples:\n"
               "  python main.py                      # Launch GUI (default)\n"
               "  python main.py gui                  # Launch desktop GUI\n"
               "  python main.py api                  # Launch API server\n"
               "  python main.py demo                 # Launch interactive demo\n"
               "  python main.py combined             # Launch API + Demo\n"
               "  python main.py api --port 9000      # API on port 9000\n"
               "  python main.py -h                   # Show this help",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Positional mode argument
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['gui', 'api', 'demo', 'combined'],
        default='gui',
        help='Operation mode (default: gui - Desktop GUI)'
    )

    # API options
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='API server host (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API server port (default: 8000)'
    )

    # Verbosity
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    try:
        # Print startup banner
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║           POLYLOG SIMULATOR - Starting                  ║")
        print("║         Interactive Polyform Design System              ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")
        
        if args.mode == 'gui':
            _launch_gui(args.verbose)
        elif args.mode == 'api':
            _launch_api(args.host, args.port, args.verbose)
        elif args.mode == 'demo':
            _launch_demo(args.verbose)
        elif args.mode == 'combined':
            _launch_combined(args.host, args.port, args.verbose)
    except KeyboardInterrupt:
        print("\n\nShutdown by user")
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        # Always show traceback for debugging
        import traceback
        traceback.print_exc()
        return 1

    return 0


def _launch_gui(verbose: bool = False):
    """Launch desktop GUI"""
    if verbose:
        print("Launching Polylog Simulator - Desktop GUI Mode...")
    
    print("\nMode: DESKTOP GUI")
    print("Loading graphical interface...\n")
    
    try:
        # Try PyQt5 first as it's proven to work with Python 3.13
        print("Attempting to load PyQt5...")
        from code.gui.qt5.app_qt5 import main as qt5_main

        import PyQt5
        import PyQt5.QtCore
        import PyQt5.QtWidgets
        from PyQt5.QtOpenGL import QGLFormat
        _ = (PyQt5.QtCore, PyQt5.QtWidgets, QGLFormat)
        
        # Verify OpenGL support
        fmt = QGLFormat()
        if not fmt.hasOpenGL():
            raise ImportError("PyQt5 OpenGL support not available")
            
        print("✓ Using PyQt5 backend")
        return qt5_main()
        
    except ImportError as e1:
        print(f"PyQt5 import failed: {e1}")
        try:
            # Fallback to PySide6
            print("\nAttempting to load PySide6...")
            import PySide6
            import PySide6.QtCore
            import PySide6.QtWidgets
            from PySide6.QtOpenGL import QOpenGLWidget
            _ = (PySide6.QtCore, PySide6.QtWidgets, QOpenGLWidget)

            from gui.app import run_gui
            
            print("✓ Using PySide6 backend")
            return run_gui()
            
        except ImportError as e2:
            print("\n❌ Error: Could not import GUI modules")
            print("\nTo use PyQt5 (recommended for Python 3.13):")
            print("   pip install PySide6 PySide6-Qt6 PySide6-Essentials")
            print("   # Uses the PySide6 backend")
            print("pip install PySide6")
            print("\nDetails:\nPyQt5 error: {}\nPySide6 error: {}".format(e1, e2))
            return 1
    except Exception as e:
        print("\n❌ Error running GUI: {}".format(e))
        import traceback
        traceback.print_exc()
        return 1


def _launch_combined(host: str, port: int, verbose: bool = False):
    """Launch both API server and interactive demo"""
    if verbose:
        print(f"Launching Polylog Simulator (Combined: API + Demo)...")
    
    print(f"\nMode: COMBINED (API + Demo)")
    print(f"API Server: {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs\n")
    
    # For now, just launch demo (API integration pending)
    print("[Note: API server integration in progress]")
    print("Launching demo...\n")
    _launch_demo(verbose)


def _launch_api(host: str, port: int, verbose: bool = False):
    """Launch API server only"""
    if verbose:
        print(f"Launching Polylog Simulator - API Server Mode...")
    
    print(f"\nMode: API SERVER")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Swagger UI: http://{host}:{port}/docs")
    print(f"ReDoc: http://{host}:{port}/redoc\n")
    
    try:
        from polylog_main import start_api
        start_api(host, port)
    except ImportError:
        print("Error: Could not import polylog_main")
        print("API mode requires polylog_main.py in root directory")
        return 1


def _launch_demo(verbose: bool = False):
    """Run interactive demonstration"""
    if verbose:
        print("Launching Polylog Simulator - Interactive Demo Mode...")
    
    print("\nMode: INTERACTIVE DEMO")
    print("Running Polylog Simulator library integration demo...\n")
    
    try:
        from demo_library_integration import main as demo_main
        demo_main()
    except ImportError as e:
        print(f"\n❌ Error: Could not import demo: {e}")
        print("Make sure demo_library_integration.py exists.")
        print("\nRequired dependencies: numpy, PIL (Pillow)")
        return 1
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
