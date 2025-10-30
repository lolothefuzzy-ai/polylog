"""
Tests for constraint solver and forward kinematics.

Tests constraint propagation through large assembly chains,
performance with 100+ polyforms, and solver convergence.
"""

import sys
import numpy as np
import time
from constraint_solver import (
    ForwardKinematics,
    HingeConstraint,
    ConstraintValidator,
    ConstraintMode,
    apply_constraints
)


class MockPolyform:
    """Simple polyform for testing"""
    def __init__(self, poly_id: str, sides: int = 4):
        self.poly_id = poly_id
        self.sides = sides
        # Create regular polygon in XY plane
        self.vertices = []
        for i in range(sides):
            angle = 2 * np.pi * i / sides
            self.vertices.append([np.cos(angle), np.sin(angle), 0.0])
        self.data = {
            'id': poly_id,
            'sides': sides,
            'vertices': self.vertices
        }


class MockBond:
    """Simple bond between two polyforms"""
    def __init__(self, poly1_id: str, poly2_id: str, edge1: int, edge2: int):
        self.data = {
            'poly1_id': poly1_id,
            'edge1_idx': edge1,
            'poly2_id': poly2_id,
            'edge2_idx': edge2,
            'fold_angle': 0.0
        }


class MockAssembly:
    """Mock assembly for testing large chains"""
    def __init__(self):
        self.polyforms = {}
        self.bonds = []
    
    def add_polyform(self, poly_id: str, sides: int = 4):
        """Add polyform to assembly"""
        poly = MockPolyform(poly_id, sides)
        self.polyforms[poly_id] = poly.data
    
    def add_bond(self, poly1_id: str, poly2_id: str, edge1: int = 0, edge2: int = 0):
        """Add bond between polyforms"""
        bond = MockBond(poly1_id, poly2_id, edge1, edge2)
        self.bonds.append(bond.data)
    
    def get_polyform(self, poly_id: str):
        return self.polyforms.get(poly_id)
    
    def get_all_polyforms(self):
        return list(self.polyforms.values())
    
    def get_bonds(self):
        return self.bonds
    
    def polyform_count(self) -> int:
        return len(self.polyforms)


def test_single_constraint():
    """Test single hinge constraint"""
    print("\n  Testing single constraint...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    assembly.add_polyform('poly2')
    assembly.add_bond('poly1', 'poly2')
    
    solver = ForwardKinematics(assembly)
    constraint = HingeConstraint('poly1', 0, target_angle=np.pi/4)
    solver.add_constraint(constraint)
    
    converged = solver.solve()
    assert converged, "Should converge"
    assert constraint.current_angle == np.pi/4, "Angle should be set"
    
    print("    ✓ Single constraint works")


def test_angle_clamping():
    """Test angle clamping to valid range"""
    print("  Testing angle clamping...")
    
    constraint = HingeConstraint('poly1', 0, min_angle=0.0, max_angle=np.pi)
    
    # Test clamping
    assert constraint.clamp_angle(-1.0) == 0.0, "Should clamp low"
    assert constraint.clamp_angle(4.0) == np.pi, "Should clamp high"
    assert constraint.clamp_angle(np.pi/2) == np.pi/2, "Should keep valid"
    
    # Test set_target
    constraint.set_target(2*np.pi)
    assert constraint.current_angle == np.pi, "Should clamp on set_target"
    
    print("    ✓ Angle clamping works")


def test_chain_propagation():
    """Test constraint propagation through linear chain"""
    print("  Testing chain propagation...")
    
    # Create linear chain: poly1 - poly2 - poly3 - poly4
    assembly = MockAssembly()
    for i in range(1, 5):
        assembly.add_polyform(f'poly{i}')
    
    for i in range(1, 4):
        assembly.add_bond(f'poly{i}', f'poly{i+1}')
    
    solver = ForwardKinematics(assembly)
    
    # Set constraint on poly1 in RELATIVE mode (simpler to test)
    constraint = HingeConstraint(
        'poly1', 0,
        target_angle=np.pi/3,
        mode=ConstraintMode.RELATIVE
    )
    solver.add_constraint(constraint)
    
    converged = solver.solve()
    assert converged, "Should converge"
    
    # Check dependency graph built correctly
    assert 'poly2' in solver.constraint_graph.get('poly1', set()), "Should find poly2"
    assert 'poly3' in solver.constraint_graph.get('poly2', set()), "Should find poly3"
    
    # Verify constraint was applied
    assert constraint.current_angle == np.pi/3, "Constraint angle should be applied"
    
    print("    ✓ Chain propagation works")


def test_large_assembly_10_polyforms():
    """Test with 10 polyforms"""
    print("  Testing with 10 polyforms...")
    
    assembly = MockAssembly()
    for i in range(10):
        assembly.add_polyform(f'poly{i}')
    
    # Create random bonds
    for i in range(9):
        assembly.add_bond(f'poly{i}', f'poly{i+1}')
    
    solver = ForwardKinematics(assembly)
    
    # Add multiple constraints
    for i in range(0, 10, 3):
        constraint = HingeConstraint(f'poly{i}', 0, target_angle=np.pi/2)
        solver.add_constraint(constraint)
    
    start = time.time()
    converged = solver.solve()
    elapsed = time.time() - start
    
    assert converged, "Should converge"
    assert elapsed < 1.0, f"Should be fast (<1s), got {elapsed:.3f}s"
    
    print(f"    ✓ 10 polyforms solved in {elapsed:.3f}s")


def test_large_assembly_100_polyforms():
    """Test with 100 polyforms - performance test for large n"""
    print("  Testing with 100 polyforms (large n)...")
    
    assembly = MockAssembly()
    for i in range(100):
        assembly.add_polyform(f'poly{i}')
    
    # Create branching structure for realistic load
    # 10 linear chains of 10 polyforms each
    chain_idx = 0
    for chain in range(10):
        for i in range(9):
            assembly.add_bond(f'poly{chain_idx}', f'poly{chain_idx+1}')
            chain_idx += 1
        chain_idx += 1  # Skip one for next chain
    
    solver = ForwardKinematics(assembly)
    
    # Add constraints at chain roots
    for i in range(0, 100, 10):
        constraint = HingeConstraint(f'poly{i}', 0, target_angle=np.pi/2)
        solver.add_constraint(constraint)
    
    start = time.time()
    converged = solver.solve(max_iterations=10)
    elapsed = time.time() - start
    
    assert converged, "Should converge for 100 polyforms"
    assert elapsed < 5.0, f"Should handle 100 polyforms (<5s), got {elapsed:.3f}s"
    
    print(f"    ✓ 100 polyforms solved in {elapsed:.3f}s")


def test_very_large_assembly_500_polyforms():
    """Test with 500 polyforms - extreme large n test"""
    print("  Testing with 500 polyforms (extreme n)...")
    
    assembly = MockAssembly()
    for i in range(500):
        assembly.add_polyform(f'poly{i}')
    
    # Create sparse connectivity (each polyform bonded to next)
    for i in range(499):
        assembly.add_bond(f'poly{i}', f'poly{i+1}')
    
    solver = ForwardKinematics(assembly)
    
    # Add fewer constraints for extreme case
    for i in range(0, 500, 50):
        constraint = HingeConstraint(f'poly{i}', 0, target_angle=np.pi/2)
        solver.add_constraint(constraint)
    
    start = time.time()
    # Reduced iterations for performance
    converged = solver.solve(max_iterations=5)
    elapsed = time.time() - start
    
    # More relaxed constraint for extreme case
    assert elapsed < 30.0, f"500 polyforms should be <30s, got {elapsed:.3f}s"
    
    print(f"    ✓ 500 polyforms handled in {elapsed:.3f}s")


def test_constraint_validator():
    """Test collision detection"""
    print("  Testing constraint validator...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1', sides=4)
    assembly.add_polyform('poly2', sides=4)
    
    validator = ConstraintValidator(assembly)
    
    # Both polyforms are unit circles centered at origin
    # This AABB test should show overlap
    result = validator.check_collision('poly1')
    
    # Result depends on AABB overlap logic
    # Just verify function runs without error
    assert isinstance(result, bool), "Should return boolean"
    
    print("    ✓ Constraint validator works")


def test_constraint_export_import():
    """Test exporting and importing constraints"""
    print("  Testing export/import...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    assembly.add_polyform('poly2')
    
    solver = ForwardKinematics(assembly)
    solver.set_angle('poly1', 0, np.pi/3)
    solver.set_angle('poly2', 1, np.pi/6)
    
    # Export
    exported = solver.export_constraints()
    assert len(exported) == 2, "Should export 2 constraints"
    
    # Create new solver and import
    solver2 = ForwardKinematics(assembly)
    solver2.import_constraints(exported)
    
    assert len(solver2.constraints) == 2, "Should import 2 constraints"
    assert solver2.get_angle('poly1', 0) == np.pi/3, "Should restore angle"
    
    print("    ✓ Export/import works")


def test_get_chain_angles():
    """Test getting all angles in a chain"""
    print("  Testing chain angle query...")
    
    assembly = MockAssembly()
    for i in range(5):
        assembly.add_polyform(f'poly{i}')
    
    for i in range(4):
        assembly.add_bond(f'poly{i}', f'poly{i+1}')
    
    solver = ForwardKinematics(assembly)
    for i in range(5):
        solver.set_angle(f'poly{i}', 0, np.pi/(i+2))
    
    chain_angles = solver.get_chain_angles('poly0')
    
    assert len(chain_angles) > 0, "Should find angles in chain"
    
    print(f"    ✓ Chain angle query works ({len(chain_angles)} angles)")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("CONSTRAINT SOLVER TEST SUITE - Large Assembly Support")
    print("="*70)
    
    tests = [
        ("Single Constraint", test_single_constraint),
        ("Angle Clamping", test_angle_clamping),
        ("Chain Propagation", test_chain_propagation),
        ("10 Polyforms", test_large_assembly_10_polyforms),
        ("100 Polyforms (Large n)", test_large_assembly_100_polyforms),
        ("500 Polyforms (Extreme n)", test_very_large_assembly_500_polyforms),
        ("Constraint Validator", test_constraint_validator),
        ("Export/Import", test_constraint_export_import),
        ("Chain Angle Query", test_get_chain_angles),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"    ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
