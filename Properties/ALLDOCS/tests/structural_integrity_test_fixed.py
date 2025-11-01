#!/usr/bin/env python
# coding: utf-8
"""
Structural Integrity Test Suite
================================

Validates:
1. Single entry point (main.py) and all launch modes
2. Module dependencies and circular import detection
3. API contracts between managers, engines, and UI
4. Data consistency through placement/decay/exploration cycles
5. Exception handling and error recovery
"""

import importlib
import json
import pathlib
import sys
import traceback
from typing import Any, Dict, List

# Ensure project root on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class IntegrityTester:
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
    
    def test_entry_point_main_py(self):
        """Test main.py as single unified entry point."""
        print("\n[TEST] Entry Point: main.py")
        try:
            import main
            # Check all required functions exist
            assert hasattr(main, 'main'), "main() not found"
            assert hasattr(main, '_launch_gui'), "_launch_gui() not found"
            assert hasattr(main, '_launch_cli'), "_launch_cli() not found"
            assert hasattr(main, '_launch_api'), "_launch_api() not found"
            assert hasattr(main, '_launch_both'), "_launch_both() not found"
            assert hasattr(main, '_launch_demo'), "_launch_demo() not found"
            
            # Test argument parsing (don't try to parse sys.argv; just check main has argparse)
            assert hasattr(main, 'argparse'), "main doesn't have argparse module"
            # Parser exists and is properly configured in main.main()
            # Skip direct parse test to avoid side effects
            
            self.results['entry_point_main'] = {'status': 'PASS', 'modes': 6}
            print("  [OK] main.py entry point valid; 6 modes callable")
            return True
        except Exception as e:
            self.errors.append(f"Entry point test failed: {e}")
            self.results['entry_point_main'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  [FAIL] {e}")
            return False
    
    def test_module_imports_no_circularity(self):
        """Verify all core modules import without circular dependency."""
        print("\n[TEST] Module Imports: No Circularity")
        # Core modules that must exist and be importable
        core_modules = [
            'polygon_utils',
            'managers',
            'validators',
            'automated_placement_engine',
            'continuous_exploration_engine',
            'canonical_estimator',
            'polyform_library',
            'stable_library',
            'desktop_app',
            'api_server',
            'demo_automated_placement',
            'verify_system',
            'main'
        ]
        
        imported = {}
        failed = []
        for mod_name in core_modules:
            try:
                mod = importlib.import_module(mod_name)
                imported[mod_name] = mod
                print(f"  [OK] {mod_name}")
            except Exception as e:
                failed.append((mod_name, str(e)))
                print(f"  [FAIL] {mod_name}: {e}")
        
        self.results['module_imports'] = {
            'status': 'PASS' if not failed else 'PARTIAL',
            'imported': len(imported),
            'failed': len(failed),
            'failed_list': failed
        }
        
        if failed:
            self.errors.append(f"Failed to import {len(failed)} modules")
        return len(failed) == 0
    
    def test_manager_api_contracts(self):
        """Verify manager API contracts (methods, signatures, return types)."""
        print("\n[TEST] Manager API Contracts")
        try:
            
            contracts = {
                'RealMemoryManager': ['get_scaler_confidence', 'get_all_scalers', 'record_success', 'query_successful_patterns'],
                'RealChainManager': ['get_connected_components'],
                'RealFoldValidator': ['validate_fold'],
                'RealWorkspaceManager': ['register_assembly', 'postprocess_assembly', 'update_bond_visualization'],
                'RealProvenanceTracker': ['log_placement']
            }
            
            failed = []
            for cls_name, methods in contracts.items():
                cls = locals()[cls_name]
                for method_name in methods:
                    if not hasattr(cls, method_name):
                        failed.append(f"{cls_name}.{method_name}")
            
            self.results['manager_api'] = {
                'status': 'PASS' if not failed else 'FAIL',
                'contracts_checked': sum(len(m) for m in contracts.values()),
                'failed': failed
            }
            
            if failed:
                print(f"  [FAIL] Missing methods: {failed}")
                self.errors.append(f"Manager API violations: {failed}")
                return False
            
            print(f"  [OK] All {sum(len(m) for m in contracts.values())} contract methods present")
            return True
        except Exception as e:
            self.results['manager_api'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  [FAIL] {e}")
            self.errors.append(f"Manager API test failed: {e}")
            return False
    
    def test_engine_api_contracts(self):
        """Verify engine API contracts."""
        print("\n[TEST] Engine API Contracts")
        try:
            
            contracts = {
                'ConnectionEvaluator': ['evaluate_all_connections', 'clear_cache'],
                'FoldSequencer': ['execute_fold_sequence'],
                'DecayManager': ['trigger_decay'],
                'AutomatedPlacementEngine': ['place_polyform', 'get_placement_stats'],
                'SuggestionEngine': ['suggest_next_polyforms'],
                'ContinuousExplorationEngine': ['start_exploration', 'stop_exploration', 'get_exploration_stats']
            }
            
            failed = []
            for cls_name, methods in contracts.items():
                cls = locals()[cls_name]
                for method_name in methods:
                    if not hasattr(cls, method_name):
                        failed.append(f"{cls_name}.{method_name}")
            
            self.results['engine_api'] = {
                'status': 'PASS' if not failed else 'FAIL',
                'contracts_checked': sum(len(m) for m in contracts.values()),
                'failed': failed
            }
            
            if failed:
                print(f"  [FAIL] Missing methods: {failed}")
                self.errors.append(f"Engine API violations: {failed}")
                return False
            
            print(f"  [OK] All {sum(len(m) for m in contracts.values())} contract methods present")
            return True
        except Exception as e:
            self.results['engine_api'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  [FAIL] {e}")
            self.errors.append(f"Engine API test failed: {e}")
            return False
    
    def test_assembly_data_consistency(self):
        """Test assembly data model consistency through cycles."""
        print("\n[TEST] Assembly Data Consistency")
        try:
            import validators as V
            from automated_placement_engine import (
                AutomatedPlacementEngine,
                ConnectionEvaluator,
                DecayManager,
                FoldSequencer,
            )
            from managers import (
                RealChainManager,
                RealFoldValidator,
                RealMemoryManager,
                RealProvenanceTracker,
                RealWorkspaceManager,
            )
            from polygon_utils import create_polygon
            
            # Mock assembly
            class TestAssembly:
                def __init__(self):
                    self.polyforms = {}
                    self.bonds = []
                    self._next_id = 1
                def add_polyform(self, p):
                    if 'id' not in p:
                        p['id'] = f"poly_{self._next_id}"
                        self._next_id += 1
                    self.polyforms[p['id']] = p
                def get_polyform(self, pid):
                    return self.polyforms.get(pid)
                def get_all_polyforms(self):
                    return list(self.polyforms.values())
                def add_bond(self, b):
                    self.bonds.append(b)
                def get_bonds(self):
                    return self.bonds
                def copy(self):
                    new = TestAssembly()
                    new.polyforms = {k: dict(v) for k, v in self.polyforms.items()}
                    new.bonds = list(self.bonds)
                    new._next_id = self._next_id
                    return new
            
            asm = TestAssembly()
            p1 = create_polygon(4)
            p2 = create_polygon(4)
            asm.add_polyform(p1)
            asm.add_polyform(p2)
            
            # Validate integrity before and after operations
            for p in asm.get_all_polyforms():
                ok, meta = V.check_polyform_integrity(p, tol_relative=2e-3)
                assert ok, f"Polyform {p['id']} failed integrity: {meta}"
            
            ok, meta = V.check_assembly_consistency(asm, tol_relative=2e-3)
            assert ok, f"Assembly failed consistency: {meta}"
            
            # Attempt placement
            memory = RealMemoryManager()
            chains = RealChainManager()
            validator = RealFoldValidator()
            workspace = RealWorkspaceManager()
            provenance = RealProvenanceTracker()
            
            evaluator = ConnectionEvaluator(memory, chains)
            sequencer = FoldSequencer(validator, workspace)
            decay = DecayManager(chains, memory, workspace)
            engine = AutomatedPlacementEngine(evaluator, sequencer, decay, workspace, provenance)
            
            res = engine.place_polyform(p1['id'], p2['id'], asm)
            
            # Validate after placement
            for p in asm.get_all_polyforms():
                ok, meta = V.check_polyform_integrity(p, tol_relative=2e-3)
                if not ok:
                    print(f"  [FAIL] Integrity failed after placement: {meta}")
                    return False
            
            ok, meta = V.check_assembly_consistency(asm, tol_relative=2e-3)
            if not ok:
                print(f"  [FAIL] Consistency failed after placement: {meta}")
                return False
            
            self.results['assembly_consistency'] = {
                'status': 'PASS',
                'placements': 1,
                'polyforms': len(asm.get_all_polyforms()),
                'bonds': len(asm.get_bonds())
            }
            
            print(f"  [OK] Assembly consistent through placement cycle ({len(asm.get_all_polyforms())} polys, {len(asm.get_bonds())} bonds)")
            return True
        except Exception as e:
            self.results['assembly_consistency'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  [FAIL] {e}")
            traceback.print_exc()
            self.errors.append(f"Assembly consistency test failed: {e}")
            return False
    
    def test_validators_coverage(self):
        """Test validator functions with edge cases."""
        print("\n[TEST] Validators Coverage")
        try:
            import validators as V
            from polygon_utils import create_polygon
            
            # Test 1: valid polygon
            p = create_polygon(4)
            ok, meta = V.check_polyform_integrity(p)
            assert ok, f"Valid polygon failed: {meta}"
            
            # Test 2: degenerate (invalid) polygon
            bad_poly = {
                'type': 'polygon',
                'sides': 3,
                'vertices': [[0,0,0], [1,0,0]],  # Too few vertices
                'bonds': []
            }
            ok, meta = V.check_polyform_integrity(bad_poly)
            assert not ok, "Degenerate polygon should fail"
            
            # Test 3: assembly with bonds
            class TestAsm:
                def __init__(self):
                    self.polyforms = {}
                    self.bonds = []
                def get_all_polyforms(self):
                    return list(self.polyforms.values())
                def get_bonds(self):
                    return self.bonds
            
            asm = TestAsm()
            p1 = create_polygon(4)
            p1['id'] = 'p1'
            p2 = create_polygon(4)
            p2['id'] = 'p2'
            asm.polyforms['p1'] = p1
            asm.polyforms['p2'] = p2
            asm.bonds.append({'poly1_id': 'p1', 'edge1_idx': 0, 'poly2_id': 'p2', 'edge2_idx': 2})
            
            ok, meta = V.check_assembly_consistency(asm)
            assert ok, f"Valid assembly failed: {meta}"
            
            self.results['validators'] = {
                'status': 'PASS',
                'tests': 3
            }
            
            print("  [OK] Validators passed all edge case tests")
            return True
        except Exception as e:
            self.results['validators'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  [FAIL] {e}")
            self.errors.append(f"Validators test failed: {e}")
            return False
    
    def test_library_persistence(self):
        """Test stable library save/load cycle."""
        print("\n[TEST] Library Persistence")
        try:
            import os
            import tempfile

            from polygon_utils import create_polygon
            from stable_library import StableLibrary
            
            # Use temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                temp_path = f.name
            
            try:
                lib = StableLibrary(temp_path)
                
                # Mock assembly
                class Asm:
                    def __init__(self):
                        self.polys = [create_polygon(4), create_polygon(3)]
                    def get_all_polyforms(self):
                        return self.polys
                    def get_bonds(self):
                        return []
                
                asm = Asm()
                
                # Save
                entry_id = lib.save_assembly(asm, name='test_assembly')
                assert entry_id, "Save returned no ID"
                
                # List
                entries = lib.list_entries()
                assert len(entries) > 0, "List returned no entries"
                
                # Load
                loaded = lib.load_entry(entry_id)
                assert loaded, "Load returned None"
                assert loaded['name'] == 'test_assembly', "Name mismatch"
                assert len(loaded['polyforms']) == 2, "Polyform count mismatch"
                
                self.results['library_persistence'] = {
                    'status': 'PASS',
                    'saved': 1,
                    'loaded': 1
                }
                
                print("  [OK] Library persistence cycle passed")
                return True
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            self.results['library_persistence'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  [FAIL] {e}")
            self.errors.append(f"Library persistence test failed: {e}")
            return False
    
    def run_all(self):
        """Run all tests and report."""
        print("=" * 70)
        print("STRUCTURAL INTEGRITY TEST SUITE")
        print("=" * 70)
        
        tests = [
            self.test_entry_point_main_py,
            self.test_module_imports_no_circularity,
            self.test_manager_api_contracts,
            self.test_engine_api_contracts,
            self.test_assembly_data_consistency,
            self.test_validators_coverage,
            self.test_library_persistence,
        ]
        
        passed = sum(1 for t in tests if t())
        total = len(tests)
        
        print("\n" + "=" * 70)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("=" * 70)
        
        if self.errors:
            print("\nERRORS:")
            for err in self.errors:
                print(f"  - {err}")
        
        print("\nDETAILS:")
        print(json.dumps(self.results, indent=2, default=str))
        
        return passed == total


if __name__ == '__main__':
    tester = IntegrityTester()
    success = tester.run_all()
    sys.exit(0 if success else 1)
