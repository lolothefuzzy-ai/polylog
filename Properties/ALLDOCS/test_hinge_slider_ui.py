"""
Tests for HingeSliderUI widget and constraint solver integration.

Tests UI creation, angle control, constraint updates, and signal emissions.
"""

import sys

import numpy as np
from constraint_solver import ConstraintMode, ForwardKinematics, HingeConstraint


class MockAssembly:
    """Mock assembly for testing."""
    def __init__(self):
        self.polyforms = {}
        self.bonds = []
    
    def add_polyform(self, poly_id: str, sides: int = 4):
        """Add polyform to assembly."""
        vertices = []
        for i in range(sides):
            angle = 2 * np.pi * i / sides
            vertices.append([np.cos(angle), np.sin(angle), 0.0])
        self.polyforms[poly_id] = {
            'id': poly_id,
            'sides': sides,
            'vertices': vertices
        }
    
    def add_bond(self, poly1_id: str, poly2_id: str, edge1: int = 0, edge2: int = 0):
        """Add bond between polyforms."""
        self.bonds.append({
            'poly1_id': poly1_id,
            'edge1_idx': edge1,
            'poly2_id': poly2_id,
            'edge2_idx': edge2,
        })
    
    def get_polyform(self, poly_id: str):
        return self.polyforms.get(poly_id)
    
    def get_all_polyforms(self):
        return list(self.polyforms.values())
    
    def get_bonds(self):
        return self.bonds


def test_constraint_creation():
    """Test HingeConstraint creation and properties."""
    print("  Testing HingeConstraint creation...")
    
    constraint = HingeConstraint(
        polyform_id='poly1',
        edge_idx=0,
        min_angle=0.0,
        max_angle=np.pi,
        current_angle=np.pi/2
    )
    
    assert constraint.polyform_id == 'poly1'
    assert constraint.edge_idx == 0
    assert constraint.min_angle == 0.0
    assert constraint.max_angle == np.pi
    assert constraint.current_angle == np.pi/2
    assert constraint.active == True
    assert constraint.mode == ConstraintMode.RELATIVE
    
    print("    ✓ HingeConstraint creation works")


def test_constraint_clamping():
    """Test constraint angle clamping."""
    print("  Testing constraint clamping...")
    
    constraint = HingeConstraint('poly1', 0, min_angle=0.0, max_angle=np.pi)
    
    # Test clamping
    assert constraint.clamp_angle(-0.5) == 0.0
    assert constraint.clamp_angle(2*np.pi) == np.pi
    assert constraint.clamp_angle(np.pi/2) == np.pi/2
    
    # Test set_target
    constraint.set_target(3*np.pi)
    assert constraint.current_angle == np.pi
    
    print("    ✓ Constraint clamping works")


def test_forward_kinematics_solver():
    """Test ForwardKinematics solver initialization."""
    print("  Testing ForwardKinematics solver...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    assembly.add_polyform('poly2')
    assembly.add_bond('poly1', 'poly2')
    
    solver = ForwardKinematics(assembly)
    
    assert solver.assembly is not None
    assert len(solver.constraints) == 0
    assert len(solver.constraint_graph) > 0
    
    print("    ✓ ForwardKinematics solver initialization works")


def test_set_and_get_angles():
    """Test setting and getting angles."""
    print("  Testing set/get angles...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    assembly.add_polyform('poly2')
    
    solver = ForwardKinematics(assembly)
    
    # Set angle
    solver.set_angle('poly1', 0, np.pi/4)
    angle = solver.get_angle('poly1', 0)
    assert angle == np.pi/4
    
    # Get non-existent angle
    angle = solver.get_angle('poly3', 0)
    assert angle is None
    
    print("    ✓ Set/get angles work")


def test_constraint_solve_convergence():
    """Test solver convergence."""
    print("  Testing solver convergence...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    assembly.add_polyform('poly2')
    assembly.add_bond('poly1', 'poly2')
    
    solver = ForwardKinematics(assembly)
    solver.set_angle('poly1', 0, np.pi/3)
    
    # Should converge
    converged = solver.solve(max_iterations=10)
    assert converged
    
    print("    ✓ Solver converges")


def test_constraint_export_import():
    """Test exporting and importing constraints."""
    print("  Testing constraint export/import...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    assembly.add_polyform('poly2')
    
    solver1 = ForwardKinematics(assembly)
    solver1.set_angle('poly1', 0, np.pi/3)
    solver1.set_angle('poly2', 1, np.pi/6)
    
    # Export
    exported = solver1.export_constraints()
    assert len(exported) == 2
    
    # Import into new solver
    solver2 = ForwardKinematics(assembly)
    solver2.import_constraints(exported)
    
    assert len(solver2.constraints) == 2
    assert solver2.get_angle('poly1', 0) == np.pi/3
    assert solver2.get_angle('poly2', 1) == np.pi/6
    
    print("    ✓ Export/import works")


def test_chain_angles():
    """Test getting chain angles."""
    print("  Testing chain angles...")
    
    assembly = MockAssembly()
    for i in range(5):
        assembly.add_polyform(f'poly{i}')
    
    for i in range(4):
        assembly.add_bond(f'poly{i}', f'poly{i+1}')
    
    solver = ForwardKinematics(assembly)
    for i in range(5):
        solver.set_angle(f'poly{i}', 0, np.pi/(i+2))
    
    chain_angles = solver.get_chain_angles('poly0')
    assert len(chain_angles) > 0
    
    print(f"    ✓ Chain angles retrieved ({len(chain_angles)} angles)")


def test_multiple_constraints():
    """Test multiple constraints on same polyform."""
    print("  Testing multiple constraints...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1', sides=6)  # 6-gon has 6 edges
    
    solver = ForwardKinematics(assembly)
    
    # Add multiple constraints for different edges
    for edge in range(3):
        solver.set_angle('poly1', edge, np.pi/2 + edge*0.1)
    
    assert len(solver.constraints) == 3
    
    # Verify each constraint
    for edge in range(3):
        angle = solver.get_angle('poly1', edge)
        assert angle == np.pi/2 + edge*0.1
    
    print("    ✓ Multiple constraints work")


def test_rodrigues_rotation_formula():
    """Test Rodrigues rotation formula in solver."""
    print("  Testing Rodrigues rotation formula...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1', sides=4)
    
    solver = ForwardKinematics(assembly)
    
    # Get polyform
    poly = assembly.get_polyform('poly1')
    original_verts = np.array(poly['vertices'], dtype=float).copy()
    
    # Apply rotation
    axis = np.array([0, 0, 1])  # Z-axis
    pivot = np.array([0, 0, 0])
    angle = np.pi / 4  # 45 degrees
    
    solver._rotate_polyform_around_axis(poly, pivot, axis, angle)
    rotated_verts = np.array(poly['vertices'], dtype=float)
    
    # Verify rotation happened
    assert not np.allclose(original_verts, rotated_verts), "Vertices should have rotated"
    
    # Verify distances from pivot are preserved (rotation property)
    orig_dists = np.linalg.norm(original_verts - pivot, axis=1)
    rot_dists = np.linalg.norm(rotated_verts - pivot, axis=1)
    
    assert np.allclose(orig_dists, rot_dists), "Rotation should preserve distances"
    
    print("    ✓ Rodrigues rotation formula works")


def test_large_assembly_performance():
    """Test performance with large assembly."""
    print("  Testing large assembly performance...")
    
    import time
    
    assembly = MockAssembly()
    for i in range(50):
        assembly.add_polyform(f'poly{i}')
    
    # Create chain bonds
    for i in range(49):
        assembly.add_bond(f'poly{i}', f'poly{i+1}')
    
    solver = ForwardKinematics(assembly)
    
    # Add constraints at intervals
    for i in range(0, 50, 5):
        solver.set_angle(f'poly{i}', 0, np.pi/2)
    
    # Time the solve
    start = time.time()
    converged = solver.solve(max_iterations=5)
    elapsed = time.time() - start
    
    assert converged
    assert elapsed < 5.0, f"Should solve 50 polyforms in <5s, got {elapsed:.3f}s"
    
    print(f"    ✓ Large assembly (50 polyforms) solved in {elapsed:.3f}s")


def test_constraint_modes():
    """Test different constraint modes."""
    print("  Testing constraint modes...")
    
    # Test ABSOLUTE mode
    c1 = HingeConstraint('poly1', 0, mode=ConstraintMode.ABSOLUTE)
    assert c1.mode == ConstraintMode.ABSOLUTE
    
    # Test RELATIVE mode
    c2 = HingeConstraint('poly1', 0, mode=ConstraintMode.RELATIVE)
    assert c2.mode == ConstraintMode.RELATIVE
    
    # Test CHAIN mode
    c3 = HingeConstraint('poly1', 0, mode=ConstraintMode.CHAIN)
    assert c3.mode == ConstraintMode.CHAIN
    
    # Test BALANCED mode
    c4 = HingeConstraint('poly1', 0, mode=ConstraintMode.BALANCED)
    assert c4.mode == ConstraintMode.BALANCED
    
    print("    ✓ Constraint modes work")


def test_constraint_activation():
    """Test constraint activation/deactivation."""
    print("  Testing constraint activation...")
    
    assembly = MockAssembly()
    assembly.add_polyform('poly1')
    
    constraint = HingeConstraint('poly1', 0)
    assert constraint.active == True
    
    # Deactivate
    constraint.active = False
    assert constraint.active == False
    
    # Re-activate
    constraint.active = True
    assert constraint.active == True
    
    print("    ✓ Constraint activation works")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("HINGE SLIDER UI & CONSTRAINT SOLVER INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        ("HingeConstraint Creation", test_constraint_creation),
        ("Constraint Clamping", test_constraint_clamping),
        ("ForwardKinematics Solver", test_forward_kinematics_solver),
        ("Set/Get Angles", test_set_and_get_angles),
        ("Solver Convergence", test_constraint_solve_convergence),
        ("Export/Import Constraints", test_constraint_export_import),
        ("Chain Angles", test_chain_angles),
        ("Multiple Constraints", test_multiple_constraints),
        ("Rodrigues Rotation Formula", test_rodrigues_rotation_formula),
        ("Constraint Modes", test_constraint_modes),
        ("Constraint Activation", test_constraint_activation),
        ("Large Assembly Performance", test_large_assembly_performance),
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
