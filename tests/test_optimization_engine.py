from unittest.mock import MagicMock

from src.engines.optimization_engine import OptimizationEngine


def test_optimization_engine_basic():
    """Test optimization engine with mock assembly."""
    # Create mock assembly
    assembly = MagicMock()
    assembly.get_fold_angles.return_value = [45, 90]
    assembly.calculate_stability.return_value = 0.8
    
    # Initialize engine
    engine = OptimizationEngine(config={})
    
    # Run optimization
    result = engine.optimize_fold(assembly)
    
    # Verify
    assert result == assembly
    assembly.set_fold_angles.assert_called_once()
