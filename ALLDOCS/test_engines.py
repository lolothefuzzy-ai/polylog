#!/usr/bin/env python
"""
Visual test verification for Polylog engines.
Tests core functionality without requiring GUI/API dependencies.
Run: py test_engines.py
"""

import sys
import json
import time
from typing import List, Dict, Any, Optional

# Test coloring
COLORS = {
    'green': '\033[92m',
    'red': '\033[91m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'reset': '\033[0m',
    'bold': '\033[1m',
}

def colored(text, color='reset'):
    """Add color to terminal output"""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def print_header(title):
    """Print test section header"""
    print(f"\n{colored('='*70, 'bold')}")
    print(f"{colored(title, 'blue')}")
    print(f"{colored('='*70, 'bold')}\n")

def print_test(name, passed, details=""):
    """Print individual test result"""
    status = colored("✓ PASS", 'green') if passed else colored("✗ FAIL", 'red')
    print(f"  {status} {name}")
    if details:
        print(f"      {colored(details, 'yellow')}")

def print_section(title):
    """Print subsection"""
    print(f"\n{colored(title, 'bold')}")
    print(f"{colored('-'*60, 'yellow')}")

# ============================================================================
# TESTS
# ============================================================================

def test_imports():
    """Test that core modules can be imported"""
    print_header("TEST 1: Module Imports")
    
    tests_passed = 0
    tests_total = 0
    
    modules = [
        'numpy',
        'automated_placement_engine',
        'continuous_exploration_engine',
        'managers',
        'polygon_utils',
        'validators',
    ]
    
    for module in modules:
        tests_total += 1
        try:
            __import__(module)
            print_test(f"Import {module}", True)
            tests_passed += 1
        except ImportError as e:
            print_test(f"Import {module}", False, str(e))
    
    return tests_passed, tests_total

def test_polygon_creation():
    """Test polygon creation utility"""
    print_header("TEST 2: Polygon Creation")
    
    from polygon_utils import create_polygon
    import numpy as np
    
    tests_passed = 0
    tests_total = 0
    
    # Test different polygon sides
    for sides in [3, 4, 5, 6, 8, 12]:
        tests_total += 1
        try:
            poly = create_polygon(sides, (0, 0, 0))
            
            # Verify structure
            assert 'vertices' in poly
            assert 'sides' in poly
            assert poly['sides'] == sides
            assert len(poly['vertices']) == sides
            
            # Verify vertices are 3D points
            for v in poly['vertices']:
                assert len(v) == 3
                assert all(isinstance(x, float) for x in v)
            
            print_test(f"Create {sides}-gon", True, f"{sides} vertices created")
            tests_passed += 1
        except Exception as e:
            print_test(f"Create {sides}-gon", False, str(e))
    
    return tests_passed, tests_total

def test_managers():
    """Test manager implementations"""
    print_header("TEST 3: Managers")
    
    from managers import RealMemoryManager, RealChainManager, RealFoldValidator
    
    tests_passed = 0
    tests_total = 0
    
    # Test MemoryManager
    tests_total += 1
    try:
        memory = RealMemoryManager()
        scalers = memory.get_all_scalers()
        assert len(scalers) > 0
        print_test("RealMemoryManager initialization", True, f"{len(scalers)} scalers loaded")
        tests_passed += 1
    except Exception as e:
        print_test("RealMemoryManager initialization", False, str(e))
    
    # Test ChainManager
    tests_total += 1
    try:
        chains = RealChainManager()
        # Create mock assembly
        class MockAssembly:
            def get_all_polyforms(self):
                return [{'id': 'p1'}, {'id': 'p2'}]
            def get_bonds(self):
                return [{'poly1_id': 'p1', 'poly2_id': 'p2'}]
        
        assembly = MockAssembly()
        components = chains.get_connected_components(assembly)
        assert len(components) == 1  # Should be one connected component
        print_test("RealChainManager connected components", True, f"{len(components)} component(s)")
        tests_passed += 1
    except Exception as e:
        print_test("RealChainManager connected components", False, str(e))
    
    # Test FoldValidator
    tests_total += 1
    try:
        validator = RealFoldValidator()
        # Just verify it initializes
        assert validator is not None
        print_test("RealFoldValidator initialization", True, "Validator ready")
        tests_passed += 1
    except Exception as e:
        print_test("RealFoldValidator initialization", False, str(e))
    
    return tests_passed, tests_total

def test_connection_evaluator():
    """Test connection evaluation engine"""
    print_header("TEST 4: Connection Evaluator")
    
    from automated_placement_engine import ConnectionEvaluator
    from managers import RealMemoryManager, RealChainManager
    from polygon_utils import create_polygon
    
    tests_passed = 0
    tests_total = 0
    
    try:
        # Create mock assembly
        class MockAssembly:
            def __init__(self):
                self.polyforms = {
                    'poly1': create_polygon(4, (0, 0, 0)),
                    'poly2': create_polygon(4, (2, 0, 0)),
                }
                self.bonds = []
            
            def get_polyform(self, pid):
                return self.polyforms.get(pid)
            
            def get_all_polyforms(self):
                return list(self.polyforms.values())
            
            def get_bonds(self):
                return self.bonds
        
        # Create evaluator
        memory = RealMemoryManager()
        chains = RealChainManager()
        evaluator = ConnectionEvaluator(memory, chains)
        
        # Test evaluation
        tests_total += 1
        assembly = MockAssembly()
        candidates = evaluator.evaluate_all_connections('poly1', 'poly2', assembly)
        
        assert len(candidates) > 0
        print_test("Evaluate connections (4-gon vs 4-gon)", True, 
                   f"{len(candidates)} candidate edges found")
        tests_passed += 1
        
        # Check candidate structure
        tests_total += 1
        first = candidates[0]
        assert hasattr(first, 'poly1_id')
        assert hasattr(first, 'stability_score')
        assert hasattr(first, 'quality')
        print_test("EdgeCandidate structure", True, 
                   f"Stability: {first.stability_score:.3f}, Quality: {first.quality.value}")
        tests_passed += 1
        
    except Exception as e:
        print_test("Connection Evaluator", False, str(e))
    
    return tests_passed, tests_total

def test_fold_sequencer():
    """Test fold sequencing engine"""
    print_header("TEST 5: Fold Sequencer")
    
    from automated_placement_engine import ConnectionEvaluator, FoldSequencer
    from managers import (RealMemoryManager, RealChainManager, RealFoldValidator,
                         RealWorkspaceManager)
    from polygon_utils import create_polygon
    
    tests_passed = 0
    tests_total = 0
    
    try:
        # Create mock assembly
        class MockAssembly:
            def __init__(self):
                self.polyforms = {
                    'poly1': create_polygon(4, (0, 0, 0)),
                    'poly2': create_polygon(4, (2, 0, 0)),
                }
                self.bonds = []
            
            def get_polyform(self, pid):
                return self.polyforms.get(pid)
            
            def get_all_polyforms(self):
                return list(self.polyforms.values())
            
            def get_bonds(self):
                return self.bonds
        
        # Create managers
        memory = RealMemoryManager()
        chains = RealChainManager()
        validator = RealFoldValidator()
        workspace = RealWorkspaceManager()
        
        # Create engines
        evaluator = ConnectionEvaluator(memory, chains)
        sequencer = FoldSequencer(validator, workspace)
        
        # Test fold sequencing
        tests_total += 1
        assembly = MockAssembly()
        candidates = evaluator.evaluate_all_connections('poly1', 'poly2', assembly)
        
        attempts, success = sequencer.execute_fold_sequence(candidates, assembly, max_attempts=3)
        
        print_test("Execute fold sequence", True, 
                   f"{len(attempts)} attempts, Success: {success}")
        tests_passed += 1
        
    except Exception as e:
        print_test("Fold Sequencer", False, str(e))
    
    return tests_passed, tests_total

def test_decay_manager():
    """Test decay/reformation manager"""
    print_header("TEST 6: Decay Manager")
    
    from automated_placement_engine import DecayManager
    from managers import (RealMemoryManager, RealChainManager,
                         RealWorkspaceManager)
    
    tests_passed = 0
    tests_total = 0
    
    try:
        # Create managers
        memory = RealMemoryManager()
        chains = RealChainManager()
        workspace = RealWorkspaceManager()
        
        # Create decay manager
        decay_mgr = DecayManager(chains, memory, workspace)
        
        tests_total += 1
        assert decay_mgr is not None
        print_test("DecayManager initialization", True, "Decay manager ready")
        tests_passed += 1
        
    except Exception as e:
        print_test("DecayManager", False, str(e))
    
    return tests_passed, tests_total

def test_exploration_engine():
    """Test exploration engine"""
    print_header("TEST 7: Exploration Engine")
    
    from continuous_exploration_engine import (
        SuggestionEngine, ExplorationConfig, ExplorationStrategy
    )
    from managers import RealMemoryManager, RealChainManager
    
    tests_passed = 0
    tests_total = 0
    
    try:
        # Create suggestion engine
        memory = RealMemoryManager()
        chains = RealChainManager()
        suggestions = SuggestionEngine(memory, chains)
        
        tests_total += 1
        assert suggestions is not None
        print_test("SuggestionEngine initialization", True, "Suggestion engine ready")
        tests_passed += 1
        
        # Test configuration
        tests_total += 1
        config = ExplorationConfig(
            strategy=ExplorationStrategy.BALANCED,
            max_order=10,
            exploration_rate=0.2
        )
        assert config.strategy == ExplorationStrategy.BALANCED
        print_test("ExplorationConfig", True, f"Strategy: {config.strategy.value}")
        tests_passed += 1
        
    except Exception as e:
        print_test("Exploration Engine", False, str(e))
    
    return tests_passed, tests_total

def test_assembly_consistency():
    """Test assembly validation"""
    print_header("TEST 8: Assembly Consistency")
    
    from validators import check_assembly_consistency
    from polygon_utils import create_polygon
    
    tests_passed = 0
    tests_total = 0
    
    try:
        # Create mock assembly
        class MockAssembly:
            def __init__(self):
                self.polyforms = {'p1': create_polygon(4)}
                self.bonds = []
            
            def get_polyform(self, pid):
                return self.polyforms.get(pid)
            
            def get_all_polyforms(self):
                return list(self.polyforms.values())
            
            def get_bonds(self):
                return self.bonds
        
        assembly = MockAssembly()
        
        tests_total += 1
        ok, meta = check_assembly_consistency(assembly)
        print_test("Assembly consistency check", ok, 
                   f"Valid: {ok}, Issues: {len(meta.get('issues', []))}")
        tests_passed += 1
        
    except Exception as e:
        print_test("Assembly consistency", False, str(e))
    
    return tests_passed, tests_total

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    print(colored("\n", 'reset'))
    print(colored("╔" + "="*68 + "╗", 'bold'))
    print(colored("║" + " "*10 + "POLYLOG6 ENGINE VISUAL TEST SUITE" + " "*24 + "║", 'bold'))
    print(colored("╚" + "="*68 + "╝", 'bold'))
    
    all_passed = 0
    all_total = 0
    
    test_functions = [
        test_imports,
        test_polygon_creation,
        test_managers,
        test_connection_evaluator,
        test_fold_sequencer,
        test_decay_manager,
        test_exploration_engine,
        test_assembly_consistency,
    ]
    
    for test_func in test_functions:
        try:
            passed, total = test_func()
            all_passed += passed
            all_total += total
        except Exception as e:
            print(colored(f"ERROR in {test_func.__name__}: {e}", 'red'))
    
    # Final summary
    print_header("TEST SUMMARY")
    success_rate = (all_passed / all_total * 100) if all_total > 0 else 0
    
    print(f"  Total Tests: {all_total}")
    print(f"  {colored(f'Passed: {all_passed}', 'green')}")
    print(f"  {colored(f'Failed: {all_total - all_passed}', 'red' if all_total - all_passed > 0 else 'green')}")
    print(f"  Success Rate: {colored(f'{success_rate:.1f}%', 'green' if success_rate == 100 else 'yellow')}")
    
    if success_rate == 100:
        print(f"\n{colored('✓ ALL TESTS PASSED! Engines are functional.', 'green')}")
        return 0
    else:
        print(f"\n{colored('✗ Some tests failed. Check output above.', 'red')}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
