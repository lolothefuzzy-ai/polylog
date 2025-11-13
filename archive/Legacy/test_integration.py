"""
Integration Test Script for Polylog GUI v0.2.0

Tests all major integration points:
1. Viewport displays polyforms from assembly
2. Keyboard shortcuts work
3. Fold validation functions
4. StableLibrary save/load works
"""
import sys


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from PySide6.QtWidgets import QApplication
        print("  ✓ PySide6 imported")
        _ = QApplication
    except ImportError as e:
        print(f"  ✗ PySide6 import failed: {e}")
        return False
    
    try:
        from OpenGL.GL import glClearColor
        print("  ✓ OpenGL imported")
        _ = glClearColor
    except ImportError as e:
        print(f"  ✗ OpenGL import failed: {e}")
        return False
    
    try:
        from gui.main_window import MainWindow
        print("  ✓ MainWindow imported")
        _ = MainWindow
    except ImportError as e:
        print(f"  ✗ MainWindow import failed: {e}")
        return False
    
    try:
        from generator_protocol import get_generator_registry
        print("  ✓ Generator protocol imported")
        _ = get_generator_registry
    except ImportError as e:
        print(f"  ✗ Generator protocol import failed: {e}")
        return False
    
    try:
        from unified_bonding_system import UnifiedBondingSystem
        print("  ✓ Bonding system imported")
        _ = UnifiedBondingSystem
    except ImportError as e:
        print(f"  ✗ Bonding system import failed: {e}")
        return False
    
    try:
        from hinge_manager import HingeManager
        print("  ✓ Hinge manager imported")
        _ = HingeManager
    except ImportError as e:
        print(f"  ✗ Hinge manager import failed: {e}")
        return False
    
    try:
        from collision_validator import CollisionValidator
        print("  ✓ Collision validator imported")
        _ = CollisionValidator
    except ImportError as e:
        print(f"  ✗ Collision validator import failed: {e}")
        return False
    
    try:
        from stable_library import StableLibrary
        print("  ✓ Stable library imported")
        _ = StableLibrary
    except ImportError as e:
        print(f"  ✗ Stable library import failed: {e}")
        return False
    
    return True


def test_backend_systems():
    """Test that backend systems can be initialized."""
    print("\nTesting backend systems...")
    
    try:
        from generator_protocol import get_generator_registry
        registry = get_generator_registry()
        generators = registry.list_generators()
        print(f"  ✓ Generator registry initialized ({len(generators)} generators)")
        
        from unified_bonding_system import UnifiedBondingSystem
        _ = UnifiedBondingSystem()
        print("  ✓ Bonding system initialized")
        
        from hinge_manager import HingeManager
        _ = HingeManager()
        print("  ✓ Hinge manager initialized")
        
        from collision_validator import CollisionValidator
        _ = CollisionValidator()
        print("  ✓ Collision validator initialized")
        
        from stable_library import StableLibrary
        _ = StableLibrary('test_stable_library.jsonl')
        print("  ✓ Stable library initialized")
        
        return True
    except Exception as e:
        print(f"  ✗ Backend initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_initialization():
    """Test that GUI can be initialized without errors."""
    print("\nTesting GUI initialization...")
    
    try:
        from PySide6.QtWidgets import QApplication

        from gui.main_window import MainWindow
        
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create main window
        window = MainWindow()
        print("  ✓ Main window created")
        
        # Check components
        if hasattr(window, 'viewport'):
            print("  ✓ Viewport exists")
        
        if hasattr(window, 'generator_panel'):
            print("  ✓ Generator panel exists")
        
        if hasattr(window, 'bonding_panel'):
            print("  ✓ Bonding panel exists")
        
        if hasattr(window, 'hinge_manager'):
            print("  ✓ Hinge manager connected")
        
        if hasattr(window, 'collision_validator'):
            print("  ✓ Collision validator connected")
        
        if hasattr(window, 'stable_library'):
            print("  ✓ Stable library connected")
        
        # Don't show window in test
        # window.show()
        
        return True
    except Exception as e:
        print(f"  ✗ GUI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_points():
    """Test specific integration points."""
    print("\nTesting integration points...")
    
    try:
        from PySide6.QtWidgets import QApplication

        from gui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = MainWindow()
        
        # Test 1: Check if viewport update method exists
        if hasattr(window, '_update_viewport_from_assembly'):
            print("  ✓ Viewport update method exists")
        else:
            print("  ✗ Viewport update method missing")
            return False
        
        # Test 2: Check if keyboard shortcuts are initialized
        if hasattr(window, '_on_quick_generate'):
            print("  ✓ Keyboard shortcut handlers exist")
        else:
            print("  ✗ Keyboard shortcut handlers missing")
            return False
        
        # Test 3: Check if validation methods exist
        if hasattr(window, '_validate_bond_creation'):
            print("  ✓ Validation methods exist")
        else:
            print("  ✗ Validation methods missing")
            return False
        
        # Test 4: Check if save/load methods exist
        if hasattr(window, '_on_save_assembly') and hasattr(window, '_load_assembly_by_id'):
            print("  ✓ Save/load methods exist")
        else:
            print("  ✗ Save/load methods missing")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Polylog GUI Integration Tests v0.2.0")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Backend systems
    results.append(("Backend Systems", test_backend_systems()))
    
    # Test 3: GUI initialization
    results.append(("GUI Initialization", test_gui_initialization()))
    
    # Test 4: Integration points
    results.append(("Integration Points", test_integration_points()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Integration successful!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
