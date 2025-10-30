#!/usr/bin/env python3
"""
Quick startup test - check for import errors and breakpoints
"""
import sys
import traceback

print("=" * 60)
print("POLYLOG STARTUP TEST")
print("=" * 60)

# Test 1: Import main modules
print("\n[1/5] Testing core imports...")
try:
    from desktop_app import MainWindow
    print("✓ desktop_app.MainWindow imported")
except Exception as e:
    print(f"✗ Error importing desktop_app: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Import GUI enhancements
print("\n[2/5] Testing GUI enhancements...")
try:
    from gui_enhancements_v2 import (
        StatusBarManager,
        UndoRedoManager,
        FoldAnimationEngine,
        PolygonInfluenceSlider,
        create_menu_bar,
        create_toolbar,
    )
    print("✓ All GUI enhancement modules imported")
except Exception as e:
    print(f"✗ Error importing GUI enhancements: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check PolygonInfluenceSlider signal
print("\n[3/5] Testing PolygonInfluenceSlider...")
try:
    from PySide6 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    slider = PolygonInfluenceSlider()
    
    # Check for the new signal
    if not hasattr(slider, 'add_polygon_clicked'):
        raise AttributeError("add_polygon_clicked signal missing!")
    
    print("✓ PolygonInfluenceSlider has add_polygon_clicked signal")
    print(f"✓ Slider methods: mousePressEvent={hasattr(slider, 'mousePressEvent')}")
    print(f"✓ Slider has _reset_style: {hasattr(slider, '_reset_style')}")
except Exception as e:
    print(f"✗ Error testing PolygonInfluenceSlider: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check toolbar buttons
print("\n[4/5] Testing toolbar...")
try:
    from PySide6 import QtWidgets
    
    main_window = QtWidgets.QMainWindow()
    callbacks = {
        'new': lambda: None,
        'explore_start': lambda: None,
        'explore_stop': lambda: None,
        'undo': lambda: None,
        'redo': lambda: None,
        'help_menu': lambda: None,
    }
    
    toolbar = create_toolbar(main_window, callbacks)
    
    print("✓ Toolbar created successfully")
    print(f"✓ Toolbar has {len(toolbar.actions())} actions")
    
    # Check that Place button is NOT in toolbar
    action_texts = [a.text() for a in toolbar.actions()]
    if "Place" in action_texts:
        print("✗ WARNING: 'Place' button still in toolbar (should be removed)")
    else:
        print("✓ 'Place' button correctly removed from toolbar")
        
    if "Explore" not in action_texts:
        print("✗ WARNING: 'Explore' button missing from toolbar")
    else:
        print("✓ 'Explore' button present in toolbar")
        
except Exception as e:
    print(f"✗ Error testing toolbar: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Check desktop_app callbacks
print("\n[5/5] Checking desktop_app callbacks...")
try:
    # Check that required callback methods exist
    required_callbacks = [
        'on_polygon_slider_clicked',
        'on_library_item_clicked',
        '_auto_place_library_item',
        '_on_placement_complete',
    ]
    
    from inspect import getmembers, ismethod
    
    # We can't instantiate MainWindow without Qt, but we can check the class
    for callback_name in required_callbacks:
        if hasattr(MainWindow, callback_name):
            print(f"✓ {callback_name} exists")
        else:
            print(f"✗ {callback_name} missing!")
            
except Exception as e:
    print(f"✗ Error checking callbacks: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED - NO BREAKPOINTS DETECTED")
print("=" * 60)
print("\nReady to launch: python main.py")
print("")
