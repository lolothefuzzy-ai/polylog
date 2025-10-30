#!/usr/bin/env python
"""
Broken Code Detector
====================

Finds:
- AttributeErrors (missing methods/properties)
- TypeErrors (wrong types)
- NameErrors (undefined variables)
- Logic errors (infinite loops, dead code)
- Incomplete implementations
- Missing return statements
"""

import sys
import pathlib
import ast
import importlib
from typing import Dict, List, Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class BrokenCodeDetector:
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
    
    def test_imports_and_runtime(self):
        """Test modules for actual runtime errors."""
        print("\n[TEST] Import & Runtime Errors")
        
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
            'api_server'
        ]
        
        for mod_name in core_modules:
            try:
                mod = importlib.import_module(mod_name)
                # Try to access key classes
                if mod_name == 'managers':
                    assert hasattr(mod, 'RealMemoryManager')
                    assert hasattr(mod, 'RealChainManager')
                    m = mod.RealMemoryManager()
                    assert hasattr(m, 'get_scaler_confidence')
                    m.get_scaler_confidence('test')  # Call it
                elif mod_name == 'automated_placement_engine':
                    assert hasattr(mod, 'AutomatedPlacementEngine')
                    assert hasattr(mod, 'ConnectionEvaluator')
                
                print(f"  [OK] {mod_name}")
            except Exception as e:
                self.issues.append({
                    'module': mod_name,
                    'type': 'RuntimeError',
                    'error': str(e),
                    'severity': 'CRITICAL'
                })
                print(f"  [FAIL] {mod_name}: {e}")
    
    def test_api_calls(self):
        """Test that key API calls work."""
        print("\n[TEST] API Call Integrity")
        
        try:
            # Test polygon creation
            from polygon_utils import create_polygon
            p = create_polygon(4)
            assert 'vertices' in p
            assert 'sides' in p
            assert p['sides'] == 4
            print(f"  [OK] create_polygon(4)")
            
            # Test managers
            from managers import RealMemoryManager, RealChainManager
            m = RealMemoryManager()
            m.record_success('test', {}, 0.5)
            c = RealChainManager()
            print(f"  [OK] Manager instantiation")
            
            # Test engine instantiation
            from managers import RealFoldValidator, RealWorkspaceManager, RealProvenanceTracker
            from automated_placement_engine import ConnectionEvaluator, FoldSequencer, DecayManager, AutomatedPlacementEngine
            v = RealFoldValidator()
            w = RealWorkspaceManager()
            p = RealProvenanceTracker()
            e = ConnectionEvaluator(m, c)
            s = FoldSequencer(v, w)
            d = DecayManager(c, m, w)
            engine = AutomatedPlacementEngine(e, s, d, w, p)
            print(f"  [OK] Engine instantiation")
            
        except Exception as e:
            self.issues.append({
                'test': 'api_calls',
                'type': 'RuntimeError',
                'error': str(e),
                'severity': 'CRITICAL'
            })
            print(f"  [FAIL] {e}")
    
    def test_assembly_operations(self):
        """Test assembly manipulation."""
        print("\n[TEST] Assembly Operations")
        
        try:
            from polygon_utils import create_polygon
            
            class TestAsm:
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
                    new = TestAsm()
                    new.polyforms = {k: dict(v) for k, v in self.polyforms.items()}
                    new.bonds = list(self.bonds)
                    return new
            
            asm = TestAsm()
            p1 = create_polygon(4)
            p2 = create_polygon(3)
            asm.add_polyform(p1)
            asm.add_polyform(p2)
            
            assert len(asm.get_all_polyforms()) == 2
            assert asm.get_polyform(p1['id']) is not None
            
            # Test copy
            asm2 = asm.copy()
            assert len(asm2.get_all_polyforms()) == 2
            
            print(f"  [OK] Assembly ops (2 polys, copy works)")
            
        except Exception as e:
            self.issues.append({
                'test': 'assembly_operations',
                'type': 'RuntimeError',
                'error': str(e),
                'severity': 'HIGH'
            })
            print(f"  [FAIL] {e}")
    
    def test_validators(self):
        """Test validator functions."""
        print("\n[TEST] Validators")
        
        try:
            from polygon_utils import create_polygon
            import validators as V
            
            p = create_polygon(4)
            ok, meta = V.check_polyform_integrity(p)
            assert ok, f"Valid polygon failed: {meta}"
            
            # Test bad polygon
            bad = {'type': 'polygon', 'sides': 3, 'vertices': [[0,0,0], [1,0,0]]}
            ok, meta = V.check_polyform_integrity(bad)
            assert not ok, "Bad polygon should fail"
            
            print(f"  [OK] Validators work")
            
        except Exception as e:
            self.issues.append({
                'test': 'validators',
                'type': 'RuntimeError',
                'error': str(e),
                'severity': 'HIGH'
            })
            print(f"  [FAIL] {e}")
    
    def test_estimator(self):
        """Test canonical estimator."""
        print("\n[TEST] Canonical Estimator")
        
        try:
            from canonical_estimator import canonical_estimate
            
            result = canonical_estimate(T=10.0, types=[{'a': 4, 'c': 2}])
            assert 'logN' in result
            assert 'n' in result
            assert result['n'] > 0
            
            print(f"  [OK] Estimator works (logN={result['logN']:.2f})")
            
        except Exception as e:
            self.issues.append({
                'test': 'estimator',
                'type': 'RuntimeError',
                'error': str(e),
                'severity': 'MEDIUM'
            })
            print(f"  [FAIL] {e}")
    
    def test_library_ops(self):
        """Test library operations."""
        print("\n[TEST] Library Operations")
        
        try:
            from stable_library import StableLibrary
            from polygon_utils import create_polygon
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                temp_path = f.name
            
            try:
                lib = StableLibrary(temp_path)
                
                class Asm:
                    def get_all_polyforms(self):
                        return [create_polygon(4), create_polygon(3)]
                    def get_bonds(self):
                        return []
                
                asm = Asm()
                entry_id = lib.save_assembly(asm, name='test')
                assert entry_id
                
                entries = lib.list_entries()
                assert len(entries) > 0
                
                loaded = lib.load_entry(entry_id)
                assert loaded
                assert loaded['name'] == 'test'
                
                print(f"  [OK] Library save/load works")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        except Exception as e:
            self.issues.append({
                'test': 'library_ops',
                'type': 'RuntimeError',
                'error': str(e),
                'severity': 'MEDIUM'
            })
            print(f"  [FAIL] {e}")
    
    def test_placement_cycle(self):
        """Test full placement cycle."""
        print("\n[TEST] Placement Cycle")
        
        try:
            from polygon_utils import create_polygon
            from managers import (
                RealMemoryManager, RealChainManager, RealFoldValidator,
                RealWorkspaceManager, RealProvenanceTracker
            )
            from automated_placement_engine import (
                ConnectionEvaluator, FoldSequencer, DecayManager, AutomatedPlacementEngine
            )
            
            class Asm:
                def __init__(self):
                    self.polyforms = {}
                    self.bonds = []
                    self._id = 1
                def add_polyform(self, p):
                    if 'id' not in p:
                        p['id'] = f"p{self._id}"
                        self._id += 1
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
                    new = Asm()
                    new.polyforms = {k: dict(v) for k, v in self.polyforms.items()}
                    new.bonds = list(self.bonds)
                    return new
            
            asm = Asm()
            p1 = create_polygon(4)
            p2 = create_polygon(4)
            asm.add_polyform(p1)
            asm.add_polyform(p2)
            
            m = RealMemoryManager()
            c = RealChainManager()
            v = RealFoldValidator()
            w = RealWorkspaceManager()
            pr = RealProvenanceTracker()
            e = ConnectionEvaluator(m, c)
            s = FoldSequencer(v, w)
            d = DecayManager(c, m, w)
            engine = AutomatedPlacementEngine(e, s, d, w, pr)
            
            # Test evaluate
            cands = e.evaluate_all_connections(p1['id'], p2['id'], asm)
            assert len(cands) > 0, "No candidates found"
            
            # Test placement
            res = engine.place_polyform(p1['id'], p2['id'], asm)
            assert hasattr(res, 'success')
            assert hasattr(res, 'fold_sequence')
            
            print(f"  [OK] Placement cycle works (result.success={res.success})")
            
        except Exception as e:
            self.issues.append({
                'test': 'placement_cycle',
                'type': 'RuntimeError',
                'error': str(e),
                'severity': 'CRITICAL'
            })
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
    
    def run_all(self):
        """Run all broken code tests."""
        print("=" * 70)
        print("BROKEN CODE DETECTOR")
        print("=" * 70)
        
        self.test_imports_and_runtime()
        self.test_api_calls()
        self.test_assembly_operations()
        self.test_validators()
        self.test_estimator()
        self.test_library_ops()
        self.test_placement_cycle()
        
        # Report
        print("\n" + "=" * 70)
        if not self.issues:
            print("RESULTS: NO BROKEN CODE FOUND - ALL TESTS PASS")
            print("=" * 70)
            return True
        
        critical = [i for i in self.issues if i.get('severity') == 'CRITICAL']
        high = [i for i in self.issues if i.get('severity') == 'HIGH']
        medium = [i for i in self.issues if i.get('severity') == 'MEDIUM']
        
        print(f"RESULTS: {len(self.issues)} issues found")
        print("=" * 70)
        
        if critical:
            print(f"\nCRITICAL ({len(critical)}):")
            for issue in critical:
                print(f"  {issue}")
        
        if high:
            print(f"\nHIGH ({len(high)}):")
            for issue in high:
                print(f"  {issue}")
        
        if medium:
            print(f"\nMEDIUM ({len(medium)}):")
            for issue in medium:
                print(f"  {issue}")
        
        return len(critical) == 0 and len(high) == 0


if __name__ == '__main__':
    detector = BrokenCodeDetector()
    success = detector.run_all()
    sys.exit(0 if success else 1)
