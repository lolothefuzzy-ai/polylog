#!/usr/bin/env python3
"""
Example: Canonical N Tracking Integration

Shows how to use the integrated canonical N tracking
in the ContinuousExplorationEngine.

Two examples:
1. Simple tracking: Track convergence of single exploration run
2. Strategy comparison: Compare different exploration strategies

Run: python example_tracking_integration.py
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from continuous_exploration_engine import (
    ContinuousExplorationEngine,
    ExplorationConfig,
    ExplorationStrategy,
    SuggestionEngine
)
import time


# Mock classes for testing (same as in engine)
class MockAssembly:
    """Mock assembly for demonstration"""
    def __init__(self):
        self.polyforms = []
        self.bonds = []
    
    def add_polyform(self, p):
        self.polyforms.append(p)
    
    def get_all_polyforms(self):
        return self.polyforms
    
    def get_bonds(self):
        return self.bonds


class MockPlacementEngine:
    """Mock placement engine - always succeeds"""
    def place_polyform(self, target_id, new_id, assembly):
        return {'success': True, 'method': 'mock'}


class MockMemoryManager:
    """Mock memory manager"""
    def query_successful_patterns(self, context):
        return []


class MockChainManager:
    """Mock chain manager"""
    pass


class MockWorkspaceManager:
    """Mock workspace manager"""
    pass


class MockProvenanceTracker:
    """Mock provenance tracker"""
    pass


# ═══════════════════════════════════════════════════════════════
# EXAMPLE 1: Simple Tracking
# ═══════════════════════════════════════════════════════════════

def example_1_simple_tracking():
    """
    Example 1: Track a single exploration run.
    
    This shows the simplest usage - just enable tracking
    and the engine automatically records assembly states.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Canonical N Tracking")
    print("="*80)
    
    # Create components
    memory = MockMemoryManager()
    chains = MockChainManager()
    placement = MockPlacementEngine()
    workspace = MockWorkspaceManager()
    provenance = MockProvenanceTracker()
    
    suggestions = SuggestionEngine(memory, chains)
    
    # Configure with tracking enabled (NEW)
    config = ExplorationConfig(
        strategy=ExplorationStrategy.BALANCED,
        max_order=5,
        max_iterations=20,
        animation_speed=5.0,  # Fast for testing
        enable_canonical_tracking=True,  # Enable tracking
        track_strategy_comparison=False   # Simple single tracker
    )
    
    # Create engine with tracking
    exploration = ContinuousExplorationEngine(
        placement,
        suggestions,
        workspace,
        provenance,
        config
    )
    
    # Create and run exploration
    print("\nStarting exploration with canonical N tracking...\n")
    assembly = MockAssembly()
    
    exploration.start_exploration(
        assembly,
        seed_polyform={'id': '1', 'sides': 4, 'vertices': []}
    )
    
    # Wait for completion
    time.sleep(3)
    exploration.stop_exploration()
    
    # The tracking report is automatically printed when exploration finishes
    print("\n✓ Example 1 complete")


# ═══════════════════════════════════════════════════════════════
# EXAMPLE 2: Strategy Comparison
# ═══════════════════════════════════════════════════════════════

def example_2_strategy_comparison():
    """
    Example 2: Compare different exploration strategies.
    
    This shows how to track and compare convergence
    across different strategies (greedy, random, balanced).
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Strategy Comparison with Tracking")
    print("="*80)
    
    # Create components
    memory = MockMemoryManager()
    chains = MockChainManager()
    placement = MockPlacementEngine()
    workspace = MockWorkspaceManager()
    provenance = MockProvenanceTracker()
    
    suggestions = SuggestionEngine(memory, chains)
    
    # Configure with strategy comparison tracking (NEW)
    config = ExplorationConfig(
        strategy=ExplorationStrategy.GREEDY,  # Will be changed per run
        max_order=5,
        max_iterations=15,
        animation_speed=5.0,  # Fast for testing
        enable_canonical_tracking=True,
        track_strategy_comparison=True  # Enable strategy comparison
    )
    
    # Create engine
    exploration = ContinuousExplorationEngine(
        placement,
        suggestions,
        workspace,
        provenance,
        config
    )
    
    print("\nRunning explorations with different strategies...\n")
    
    # Run with different strategies
    strategies = [
        ExplorationStrategy.GREEDY,
        ExplorationStrategy.BALANCED,
        ExplorationStrategy.RANDOM
    ]
    
    for strategy in strategies:
        print(f"\n--- Testing {strategy.value} strategy ---")
        
        # Update strategy
        exploration.config.strategy = strategy
        
        # Run exploration
        assembly = MockAssembly()
        exploration.start_exploration(
            assembly,
            seed_polyform={'id': '1', 'sides': 4, 'vertices': []}
        )
        
        # Wait for completion
        time.sleep(2)
        exploration.stop_exploration()
    
    # The comparison report is automatically printed at the end
    print("\n✓ Example 2 complete")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════╗")
    print("║  CANONICAL N TRACKING - INTEGRATION EXAMPLES          ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    print("\nThese examples show how to use canonical N tracking")
    print("integrated into the ContinuousExplorationEngine.\n")
    
    print("Key features:")
    print("  • Automatic assembly state tracking")
    print("  • Convergence detection")
    print("  • Strategy comparison")
    print("  • ASCII visualization")
    print("  • Zero code changes to existing engine\n")
    
    # Run examples
    example_1_simple_tracking()
    example_2_strategy_comparison()
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)
    print("\nTo use in your code:")
    print("  1. Set enable_canonical_tracking=True in ExplorationConfig")
    print("  2. (Optional) Set track_strategy_comparison=True for comparisons")
    print("  3. Tracking starts automatically")
    print("  4. Reports printed when exploration finishes\n")
