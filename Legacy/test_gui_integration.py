#!/usr/bin/env python3
"""
Test script to verify GUI Enhancements v2 integration.
Run: python test_gui_integration.py
"""

import sys

print("=" * 60)
print("POLYLOG GUI ENHANCEMENTS v2 - INTEGRATION TEST")
print("=" * 60)

# Test 1: Import gui_enhancements_v2
print("\n[1/4] Testing gui_enhancements_v2 module...")
try:
    from gui_enhancements_v2 import (
        FoldAnimationEngine,
        PolygonInfluenceSlider,
        StatusBarManager,
        UndoRedoManager,
        create_help_dropdown_menu,
        create_menu_bar,
        create_toolbar,
    )
    print("✓ Successfully imported all GUI enhancement components")
    _ = (
        FoldAnimationEngine,
        PolygonInfluenceSlider,
        StatusBarManager,
        UndoRedoManager,
        create_help_dropdown_menu,
        create_menu_bar,
        create_toolbar,
    )
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Import theme_manager
print("\n[2/4] Testing theme_manager module...")
try:
    from theme_manager import load_theme, set_button_color, set_label_color
    print("✓ Successfully imported theme manager")
    _ = (load_theme, set_button_color, set_label_color)
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 3: Import desktop_app (without creating QApplication)
print("\n[3/4] Testing desktop_app imports...")
try:
    # We can't fully test desktop_app without QApplication,
    # but we can verify the module can be parsed
    import ast
    with open('desktop_app.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    print("✓ desktop_app.py syntax is valid")
except SyntaxError as e:
    print(f"✗ Syntax error in desktop_app.py: {e}")
    sys.exit(1)

# Test 4: Check theme.qss exists
print("\n[4/4] Checking theme file...")
try:
    from pathlib import Path
    theme_path = Path("theme.qss")
    if theme_path.exists():
        size = theme_path.stat().st_size
        print(f"✓ theme.qss found ({size} bytes)")
    else:
        print("✗ theme.qss not found")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking theme file: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✓ ALL INTEGRATION TESTS PASSED")
print("=" * 60)
print("\nTo run the GUI application:")
print("  python main.py")
print("  or")
print("  python desktop_app.py")
print("\nFeatures:")
print("  • Dark theme with bold colors")
print("  • Library-focused layout")
print("  • Polygon influence slider")
print("  • Fold animations")
print("  • Undo/Redo system")
print("  • Menu bar & toolbar")
print("=" * 60)
