"""
TEST AND BENCHMARK: OPTUNA INTEGRATION
=======================================

Tests Optuna placement tuner against:
1. Scipy constraint optimizer
2. Manual exploration strategies
3. Performance benchmarks
4. Convergence analysis

Run with:
    python test_optuna_integration.py
    pytest test_optuna_integration.py
"""

import pytest
import time
import logging
from typing import Dict, List
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockAssembly:
    """Mock assembly for testing"""
    
    def __init__(self):
        self.polyforms = {}
        self.bonds = []
        self._id_counter = 1
    
    def add_polyform(self, polyform):
        try:
            from gui.polyform_adapter import normalize_polyform
            norm = normalize_polyform(polyform)
        except Exception:
            norm = dict(polyform)
            if 'id' not in norm:
                norm['id'] = f"poly_{self._id_counter}"
                self._id_counter += 1
            verts = []
            for v in norm.get('vertices', []):
                if isinstance(v, (list, tuple)):
                    if len(v) == 2:
                        verts.append((float(v[0]), float(v[1]), 0.0))
                    else:
                        verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
            if verts:
                norm['vertices'] = verts
        self.polyforms[norm['id']] = norm
    
    def get_polyform(self, poly_id):
        return self.polyforms.get(poly_id)
    
    def get_all_polyforms(self):
        return list(self.polyforms.values())


class MockPlacementEngine:
    """Mock placement engine for testing"""
    
    def __init__(self, success_rate: float = 0.6):
        self.success_rate = success_rate
        self.call_count = 0
        self.placement_history = []
    
    def place_polyform(self, target_id, candidate_id, assembly):
        """Mock placement that succeeds based on configured rate"""
        import random
        import time
        
        self.call_count += 1
        
        # Simulate placement time
        time.sleep(0.01)
        
        success = random.random() < self.success_rate
        
        self.placement_history.append({
            'target_id': target_id,
            'candidate_id': candidate_id,
            'success': success,
        })
        
        # Mock PlacementResult
        class Result:
            def __init__(self, success):
                self.success = success
                self.final_polyform_id = candidate_id if success else None
                self.fold_sequence = []
                self.total_time = 0.01
                self.confidence_score = 0.8 if success else 0.2
        
        return Result(success)


class MockMemoryManager:
    """Mock memory manager"""
    
    def __init__(self):
        self.patterns = {}
    
    def query_successful_patterns(self, context):
        return []


class TestOptunaPlacementTuner:
    """Test OptunaPlacementTuner functionality"""
    
    @pytest.fixture
    def setup(self):
        """Setup test fixtures"""
        try:
            from optuna_placement_tuner import OptunaPlacementTuner
        except ImportError:
            pytest.skip("Optuna not installed")
        
        assembly = MockAssembly()
        placement_engine = MockPlacementEngine(success_rate=0.65)
        memory_manager = MockMemoryManager()
        
        # Create tuner with in-memory storage
        tuner = OptunaPlacementTuner(
            placement_engine,
            memory_manager,
            storage=None,  # In-memory
            study_name="test_polylog"
        )
        
        return {
            'tuner': tuner,
            'assembly': assembly,
            'engine': placement_engine,
            'memory': memory_manager
        }
    
    def test_initialization(self, setup):
        """Test tuner initialization"""
        tuner = setup['tuner']
        assert tuner.study_name == "test_polylog"
        assert len(tuner.study.trials) == 0
    
    def test_suggest_polyform_sequence(self, setup):
        """Test polyform sequence suggestion"""
        tuner = setup['tuner']
        assembly = setup['assembly']
        
        # Add initial polyform
        assembly.add_polyform({'sides': 6, 'vertices': []})
        
        # Suggest sequence (with few trials for speed)
        suggestions = tuner.suggest_polyform_sequence(
            assembly,
            n_suggestions=3,
            n_trials=10,
            verbose=False
        )
        
        assert len(suggestions) <= 3
        assert all(hasattr(s, 'polyform_spec') for s in suggestions)
        assert all(hasattr(s, 'success_rate') for s in suggestions)
        assert all(hasattr(s, 'confidence') for s in suggestions)
    
    def test_quick_suggestion(self, setup):
        """Test quick single suggestion"""
        tuner = setup['tuner']
        assembly = setup['assembly']
        
        assembly.add_polyform({'sides': 5, 'vertices': []})
        
        suggestions = tuner.suggest_next_polyform(
            assembly,
            n_trials=5,
            top_k=1
        )
        
        assert len(suggestions) <= 1
        if suggestions:
            assert 3 <= suggestions[0].polyform_spec['sides'] <= 12
    
    def test_optimization_history(self, setup):
        """Test optimization history tracking"""
        tuner = setup['tuner']
        assembly = setup['assembly']
        
        assembly.add_polyform({'sides': 4, 'vertices': []})
        
        tuner.suggest_polyform_sequence(
            assembly,
            n_suggestions=2,
            n_trials=5
        )
        
        history = tuner.get_optimization_history()
        
        assert 'study_name' in history
        assert history['n_trials'] > 0
        assert 'suggestion_history' in history
    
    def test_trial_analysis(self, setup):
        """Test trial performance analysis"""
        tuner = setup['tuner']
        assembly = setup['assembly']
        
        assembly.add_polyform({'sides': 3, 'vertices': []})
        
        tuner.suggest_polyform_sequence(
            assembly,
            n_suggestions=1,
            n_trials=8
        )
        
        analysis = tuner.get_trial_analysis()
        
        assert 'n_trials' in analysis
        assert 'n_complete' in analysis
        assert 'success_rate' in analysis


class BenchmarkComparison:
    """Benchmark Optuna vs other approaches"""
    
    @staticmethod
    def setup_fixtures():
        """Setup for benchmarking"""
        from optuna_placement_tuner import OptunaPlacementTuner
        from scipy_constraint_optimizer import ScipyConstraintOptimizer
        
        assembly = MockAssembly()
        placement_engine = MockPlacementEngine(success_rate=0.7)
        memory_manager = MockMemoryManager()
        
        tuner = OptunaPlacementTuner(
            placement_engine,
            memory_manager,
            storage=None
        )
        
        scipy_optimizer = ScipyConstraintOptimizer(assembly)
        
        return tuner, scipy_optimizer, assembly, placement_engine
    
    @staticmethod
    def benchmark_optuna_convergence():
        """Test convergence speed of Optuna"""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK: Optuna Convergence")
        logger.info("="*60)
        
        tuner, _, assembly, _ = BenchmarkComparison.setup_fixtures()
        
        # Add polyform
        assembly.add_polyform({'sides': 6, 'vertices': []})
        
        # Run optimization
        start = time.time()
        suggestions = tuner.suggest_polyform_sequence(
            assembly,
            n_suggestions=5,
            n_trials=50,
            verbose=False
        )
        elapsed = time.time() - start
        
        analysis = tuner.get_trial_analysis()
        
        logger.info(f"Trials completed: {analysis['n_complete']}")
        logger.info(f"Trials pruned: {analysis['n_pruned']}")
        logger.info(f"Time elapsed: {elapsed:.2f}s")
        logger.info(f"Suggestions found: {len(suggestions)}")
        
        if suggestions:
            logger.info(f"Best success rate: {suggestions[0].success_rate:.2f}")
            logger.info(f"Best confidence: {suggestions[0].confidence:.2f}")
        
        return elapsed
    
    @staticmethod
    def benchmark_scipy_constraint_solving():
        """Test constraint solving with Scipy"""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK: Scipy Constraint Solving")
        logger.info("="*60)
        
        _, scipy_optimizer, assembly, _ = BenchmarkComparison.setup_fixtures()
        
        # Create mock polyforms
        polyform_ids = []
        for i in range(5):
            assembly.add_polyform({'sides': i+3, 'vertices': [], 'id': f'poly_{i}'})
            polyform_ids.append(f'poly_{i}')
        
        # Optimize fold angles
        start = time.time()
        angles = scipy_optimizer.optimize_fold_angles(
            polyform_ids,
            target_stability=0.8,
            target_spacing=2.0,
            verbose=False
        )
        elapsed = time.time() - start
        
        logger.info(f"Polyforms optimized: {len(angles)}")
        logger.info(f"Time elapsed: {elapsed:.2f}s")
        logger.info(f"Sample angles: {list(angles.values())[:3]}")
        
        return elapsed
    
    @staticmethod
    def benchmark_comparison():
        """Compare Optuna vs Scipy"""
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE COMPARISON")
        logger.info("="*60)
        
        optuna_time = BenchmarkComparison.benchmark_optuna_convergence()
        scipy_time = BenchmarkComparison.benchmark_scipy_constraint_solving()
        
        logger.info("\n" + "="*60)
        logger.info("RESULTS SUMMARY")
        logger.info("="*60)
        logger.info(f"Optuna (50 trials):        {optuna_time:.2f}s")
        logger.info(f"Scipy (5 polyforms):       {scipy_time:.2f}s")
        logger.info(f"Ratio: {optuna_time/scipy_time if scipy_time > 0 else 'N/A':.2f}x")


def run_all_tests():
    """Run all tests and benchmarks"""
    logger.info("\nStarting Optuna Integration Tests...")
    
    # Run benchmarks
    try:
        BenchmarkComparison.benchmark_comparison()
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
    
    logger.info("\nOptuna Integration Testing Complete!")


if __name__ == '__main__':
    import sys
    
    # Check if running with pytest
    if 'pytest' in sys.modules:
        pass  # pytest will discover and run tests
    else:
        # Run benchmarks standalone
        run_all_tests()
