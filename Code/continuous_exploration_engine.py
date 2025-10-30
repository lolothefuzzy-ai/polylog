"""
CONTINUOUS EXPLORATION ENGINE
==============================

Enables autonomous, background exploration of polyform space by:
1. Suggesting next-likely polyforms based on workspace state
2. Running automated placement attempts
3. Learning from successes and failures
4. Advancing assemblies toward higher orders
5. Discovering new stable configurations

This transforms the visualizer into a self-directed research tool.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import time
import threading
from queue import Queue, Empty

# Canonical N Tracking Integration
try:
    from integration_hooks import GAIntegration, MultiPopulationIntegration
    CANONICAL_TRACKING_AVAILABLE = True
except ImportError:
    CANONICAL_TRACKING_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# EXPLORATION STRATEGIES
# ═══════════════════════════════════════════════════════════════

class ExplorationStrategy(Enum):
    """Different strategies for autonomous exploration"""
    GREEDY = "greedy"              # Always pick highest-confidence option
    RANDOM = "random"              # Random selection for diversity
    BALANCED = "balanced"          # Balance exploitation vs exploration
    SYSTEMATIC = "systematic"      # Exhaustive search of possibility space
    LEARNED = "learned"            # Use ML-guided heuristics


@dataclass
class ExplorationConfig:
    """Configuration for continuous exploration"""
    strategy: ExplorationStrategy = ExplorationStrategy.BALANCED
    max_order: int = 10
    time_limit_seconds: Optional[float] = None
    max_iterations: Optional[int] = None
    confidence_threshold: float = 0.3
    exploration_rate: float = 0.2  # % of time to try random options
    animation_speed: float = 1.0   # Multiplier for animation delays
    auto_save_interval: int = 10   # Save every N successful placements
    enable_canonical_tracking: bool = True  # Track canonical N metrics
    track_strategy_comparison: bool = False  # Compare strategies via tracking


@dataclass
class ExplorationState:
    """Tracks the current state of exploration"""
    current_order: int = 0
    iterations: int = 0
    successful_placements: int = 0
    failed_attempts: int = 0
    decay_events: int = 0
    unique_polyforms_discovered: int = 0
    elapsed_time: float = 0.0
    is_running: bool = False


# ═══════════════════════════════════════════════════════════════
# SUGGESTION ENGINE
# ═══════════════════════════════════════════════════════════════

class SuggestionEngine:
    """
    Analyzes workspace state and suggests next-likely polyforms to add.
    Uses pattern recognition, learned heuristics, and strategic exploration.
    """
    
    def __init__(self, memory_manager, chain_manager):
        self.memory = memory_manager
        self.chains = chain_manager
        self.suggestion_history = []
        
    def suggest_next_polyforms(
        self,
        assembly,
        strategy: ExplorationStrategy,
        n_suggestions: int = 5
    ) -> List[Dict]:
        """
        Generate top N suggestions for next polyforms to add.
        
        Returns list of dicts with:
        - polyform_spec: Dict describing the polyform
        - confidence: float (0-1)
        - reasoning: str explaining suggestion
        """
        
        if strategy == ExplorationStrategy.GREEDY:
            return self._greedy_suggestions(assembly, n_suggestions)
        elif strategy == ExplorationStrategy.RANDOM:
            return self._random_suggestions(assembly, n_suggestions)
        elif strategy == ExplorationStrategy.BALANCED:
            return self._balanced_suggestions(assembly, n_suggestions)
        elif strategy == ExplorationStrategy.SYSTEMATIC:
            return self._systematic_suggestions(assembly, n_suggestions)
        elif strategy == ExplorationStrategy.LEARNED:
            return self._learned_suggestions(assembly, n_suggestions)
        
        return []
    
    def _greedy_suggestions(self, assembly, n: int) -> List[Dict]:
        """Always suggest highest-confidence options"""
        suggestions = []
        
        # Analyze current assembly
        context = self._analyze_assembly_context(assembly)
        
        # Get all possible polyforms
        candidates = self._get_all_candidate_polyforms()
        
        # Score each candidate
        scored = []
        for candidate in candidates:
            score = self._score_candidate(candidate, context, assembly)
            scored.append({
                'polyform_spec': candidate,
                'confidence': score,
                'reasoning': f"High compatibility with {context['dominant_type']}"
            })
        
        # Sort by confidence and return top N
        scored.sort(key=lambda x: x['confidence'], reverse=True)
        
        return scored[:n]
    
    def _random_suggestions(self, assembly, n: int) -> List[Dict]:
        """Random selection for maximum diversity"""
        candidates = self._get_all_candidate_polyforms()
        
        # Random sample
        selected = np.random.choice(candidates, size=min(n, len(candidates)), replace=False)
        
        suggestions = []
        for candidate in selected:
            suggestions.append({
                'polyform_spec': candidate,
                'confidence': 0.5,  # Neutral confidence
                'reasoning': "Random exploration for diversity"
            })
        
        return suggestions
    
    def _balanced_suggestions(self, assembly, n: int) -> List[Dict]:
        """Balance between exploitation (high confidence) and exploration (diversity)"""
        # Get greedy suggestions
        greedy = self._greedy_suggestions(assembly, n)
        
        # Get random suggestions
        random = self._random_suggestions(assembly, n)
        
        # Mix: 70% greedy, 30% random
        n_greedy = int(n * 0.7)
        n_random = n - n_greedy
        
        mixed = greedy[:n_greedy] + random[:n_random]
        
        return mixed
    
    def _systematic_suggestions(self, assembly, n: int) -> List[Dict]:
        """Exhaustive search following systematic order"""
        context = self._analyze_assembly_context(assembly)
        
        # Generate systematic sequence: all n-gons in order
        suggestions = []
        
        for sides in range(3, 13):  # 3-12 sided polygons
            if len(suggestions) >= n:
                break
            
            suggestions.append({
                'polyform_spec': {'type': 'polygon', 'sides': sides},
                'confidence': 0.6,
                'reasoning': f"Systematic exploration: {sides}-gon"
            })
        
        return suggestions
    
    def _learned_suggestions(self, assembly, n: int) -> List[Dict]:
        """Use ML-guided heuristics from memory"""
        context = self._analyze_assembly_context(assembly)
        
        # Query memory for successful patterns
        learned_patterns = self.memory.query_successful_patterns(context)
        
        suggestions = []
        for pattern in learned_patterns[:n]:
            suggestions.append({
                'polyform_spec': pattern['next_polyform'],
                'confidence': pattern['success_rate'],
                'reasoning': f"Learned pattern: {pattern['name']}"
            })
        
        # Fill remaining with greedy if needed
        if len(suggestions) < n:
            greedy = self._greedy_suggestions(assembly, n - len(suggestions))
            suggestions.extend(greedy)
        
        return suggestions
    
    def _analyze_assembly_context(self, assembly) -> Dict:
        """Analyze current assembly to understand context"""
        polyforms = assembly.get_all_polyforms()
        
        if not polyforms:
            return {
                'dominant_type': 'empty',
                'avg_sides': 0,
                'total_polygons': 0,
                'bond_density': 0.0,
                'has_triangles': False,
                'has_squares': False,
                'has_pentagons': False,
                'has_hexagons': False,
            }
        
        # Calculate statistics
        sides_list = [p.get('sides', 0) for p in polyforms]
        total_edges = sum(sides_list)
        total_bonds = len(assembly.get_bonds())
        
        context = {
            'dominant_type': self._get_dominant_type(sides_list),
            'avg_sides': np.mean(sides_list) if sides_list else 0,
            'total_polygons': len(polyforms),
            'bond_density': total_bonds / (total_edges / 2) if total_edges > 0 else 0.0,
            'has_triangles': 3 in sides_list,
            'has_squares': 4 in sides_list,
            'has_pentagons': 5 in sides_list,
            'has_hexagons': 6 in sides_list
        }
        
        return context
    
    def _get_dominant_type(self, sides_list: List[int]) -> str:
        """Get most common polygon type"""
        if not sides_list:
            return 'none'
        
        from collections import Counter
        counts = Counter(sides_list)
        most_common = counts.most_common(1)[0][0]
        
        names = {3: 'triangle', 4: 'square', 5: 'pentagon', 6: 'hexagon'}
        return names.get(most_common, f'{most_common}-gon')
    
    def _get_all_candidate_polyforms(self) -> List[Dict]:
        """Get all possible candidate polyforms"""
        candidates = []
        
        # Regular polygons (3-12 sides)
        for sides in range(3, 13):
            candidates.append({
                'type': 'polygon',
                'sides': sides
            })
        
        # Add compound polyforms from stable library if available
        try:
            from stable_library import StableLibrary
            stable_lib = StableLibrary()
            # Query stable patterns that could be suggested
            stable_patterns = stable_lib.query(max_results=10)
            for pattern in stable_patterns:
                candidates.append({
                    'type': 'compound',
                    'pattern_id': pattern.get('id'),
                    'description': pattern.get('description', 'Stable compound')
                })
        except Exception:
            # Stable library not available or query failed - continue without compounds
            pass
        
        return candidates
    
    def _score_candidate(self, candidate: Dict, context: Dict, assembly) -> float:
        """Score how well a candidate fits the current assembly"""
        score = 0.5  # Base score
        
        sides = candidate.get('sides', 4)
        
        # Bonus for similarity to existing polygons
        if abs(sides - context['avg_sides']) < 2:
            score += 0.2
        
        # Bonus for completing patterns
        if sides == 3 and context['has_squares']:
            score += 0.15  # Triangle-square combinations common
        
        if sides == 4 and context['has_triangles']:
            score += 0.15
        
        # Penalty for very different sizes
        if abs(sides - context['avg_sides']) > 4:
            score -= 0.1
        
        return np.clip(score, 0.0, 1.0)


# ═══════════════════════════════════════════════════════════════
# CONTINUOUS EXPLORATION ENGINE
# ═══════════════════════════════════════════════════════════════

class ContinuousExplorationEngine:
    """
    Main engine for autonomous exploration.
    Runs in background, continuously attempting placements.
    """
    
    def __init__(
        self,
        placement_engine,
        suggestion_engine,
        workspace_manager,
        provenance_tracker,
        config: Optional[ExplorationConfig] = None
    ):
        self.placement = placement_engine
        self.suggestions = suggestion_engine
        self.workspace = workspace_manager
        self.provenance = provenance_tracker
        
        self.config = config or ExplorationConfig()
        self.state = ExplorationState()
        
        # Threading support
        self.worker_thread = None
        self.command_queue = Queue()
        self.result_queue = Queue()
        
        # Callbacks
        self.on_placement_success: Optional[Callable] = None
        self.on_placement_failure: Optional[Callable] = None
        self.on_decay: Optional[Callable] = None
        self.on_progress: Optional[Callable] = None
        
        # Canonical N Tracking (NEW)
        self.canonical_trackers = None
        self.canonical_main_tracker = None
        if CANONICAL_TRACKING_AVAILABLE and self.config.enable_canonical_tracking:
            if self.config.track_strategy_comparison:
                # Multi-strategy comparison
                self.canonical_trackers = MultiPopulationIntegration()
                for strategy in ExplorationStrategy:
                    self.canonical_trackers.register_population(
                        self.config.max_order,
                        f"Strategy: {strategy.value}"
                    )
            else:
                # Simple single tracker
                self.canonical_main_tracker = GAIntegration(
                    self.config.max_order,
                    "Continuous Exploration"
                )
        
    def start_exploration(self, assembly, seed_polyform: Optional[Dict] = None):
        """Start autonomous exploration in background thread"""
        if self.state.is_running:
            print("⚠️  Exploration already running")
            return
        
        self.state = ExplorationState(is_running=True)
        
        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._exploration_loop,
            args=(assembly, seed_polyform),
            daemon=True
        )
        self.worker_thread.start()
        
        print("🚀 Continuous exploration started")
    
    def stop_exploration(self):
        """Stop autonomous exploration"""
        if not self.state.is_running:
            return
        
        self.command_queue.put({'command': 'stop'})
        self.state.is_running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        
        print("🛑 Exploration stopped")
    
    def pause_exploration(self):
        """Pause exploration (can be resumed)"""
        self.command_queue.put({'command': 'pause'})
        print("⏸️  Exploration paused")
    
    def resume_exploration(self):
        """Resume paused exploration"""
        self.command_queue.put({'command': 'resume'})
        print("▶️  Exploration resumed")
    
    def _exploration_loop(self, assembly, seed_polyform: Optional[Dict]):
        """Main exploration loop (runs in background thread)"""
        start_time = time.time()
        paused = False
        
        # Initialize with seed if provided
        if seed_polyform:
            assembly.add_polyform(seed_polyform)
            self.state.current_order = 1
        
        while self.state.is_running:
            # Check for commands
            try:
                cmd = self.command_queue.get_nowait()
                if cmd['command'] == 'stop':
                    break
                elif cmd['command'] == 'pause':
                    paused = True
                    continue
                elif cmd['command'] == 'resume':
                    paused = False
                    continue
            except Empty:
                pass
            
            if paused:
                time.sleep(0.1)
                continue
            
            # Check stopping conditions
            if self._should_stop(assembly):
                break
            
            # ═══════════════════════════════════════════════════════
            # EXPLORATION ITERATION
            # ═══════════════════════════════════════════════════════
            
            # 1. Get suggestions for next polyform
            suggestions = self.suggestions.suggest_next_polyforms(
                assembly,
                self.config.strategy,
                n_suggestions=5
            )
            
            if not suggestions:
                print("⚠️  No suggestions available")
                break
            
            # 2. Select suggestion based on strategy
            selected = self._select_suggestion(suggestions)
            
            # 3. Create polyform from spec
            new_polyform = self._create_polyform(selected['polyform_spec'])
            
            # 4. Attempt automated placement
            result = self._attempt_placement(assembly, new_polyform)
            
            # 5. Handle result
            self._handle_placement_result(result, assembly)
            
            # 6. Update state
            self.state.iterations += 1
            self.state.elapsed_time = time.time() - start_time
            
            # 7. Track canonical N metrics (NEW)
            if result.get('success'):
                self._track_assembly_state(assembly)
            
            # 8. Report progress
            if self.on_progress:
                self.on_progress(self.state)
            
            # 9. Animation delay
            if self.config.animation_speed > 0:
                time.sleep(0.5 / self.config.animation_speed)
        
        # Exploration finished
        self.state.is_running = False
        print(f"✓ Exploration complete: {self.state.successful_placements} successful placements")
        
        # Finalize and print canonical N tracking report (NEW)
        self._finalize_tracking()
    
    def _should_stop(self, assembly) -> bool:
        """Check if exploration should stop"""
        # Check order limit
        if self.state.current_order >= self.config.max_order:
            return True
        
        # Check time limit
        if self.config.time_limit_seconds:
            if self.state.elapsed_time >= self.config.time_limit_seconds:
                return True
        
        # Check iteration limit
        if self.config.max_iterations:
            if self.state.iterations >= self.config.max_iterations:
                return True
        
        # Check if assembly is closed (polyhedron formed)
        if self._is_assembly_closed(assembly):
            print("✓ Polyhedron closed!")
            return True
        
        return False
    
    def _is_assembly_closed(self, assembly) -> bool:
        """Check if assembly forms a closed polyhedron"""
        polyforms = assembly.get_all_polyforms()
        bonds = assembly.get_bonds()
        
        if not polyforms or not bonds:
            return False
        
        # Check if all edges are bonded
        total_edges = sum(p.get('sides', 0) for p in polyforms)
        bonded_edges = len(bonds) * 2  # Each bond connects 2 edges
        
        return bonded_edges >= total_edges
    
    def _select_suggestion(self, suggestions: List[Dict]) -> Dict:
        """Select which suggestion to try"""
        strategy = self.config.strategy
        
        if strategy == ExplorationStrategy.GREEDY:
            # Always pick highest confidence
            return max(suggestions, key=lambda s: s['confidence'])
        
        elif strategy == ExplorationStrategy.RANDOM:
            # Random selection
            import random
            return random.choice(suggestions)
        
        elif strategy == ExplorationStrategy.BALANCED:
            # Weighted random by confidence, with exploration bonus
            if np.random.random() < self.config.exploration_rate:
                # Explore: pick random
                import random
                return random.choice(suggestions)
            else:
                # Exploit: pick high confidence
                return max(suggestions, key=lambda s: s['confidence'])
        
        else:
            # Default to greedy
            return max(suggestions, key=lambda s: s['confidence'])
    
    def _create_polyform(self, spec: Dict) -> Dict:
        """Create a polyform from specification"""
        if spec['type'] == 'polygon':
            return {
                'id': str(np.random.randint(1000000)),
                'type': 'polygon',
                'sides': spec['sides'],
                'vertices': self._generate_vertices(spec['sides']),
                'bonds': []
            }
        
        elif spec['type'] == 'compound':
            # Load compound polyform from stable library
            try:
                from stable_library import StableLibrary
                stable_lib = StableLibrary()
                pattern_id = spec.get('pattern_id')
                if pattern_id:
                    loaded = stable_lib.load(pattern_id)
                    if loaded:
                        # Generate new ID for this instance
                        loaded['id'] = str(np.random.randint(1000000))
                        return loaded
            except Exception:
                pass
            
            # Fallback to regular polygon if compound loading fails
            return {
                'id': str(np.random.randint(1000000)),
                'type': 'polygon',
                'sides': 4,  # Default to square
                'vertices': self._generate_vertices(4),
                'bonds': []
            }
        
        return spec
    
    def _generate_vertices(self, sides: int) -> List[List[float]]:
        """Generate vertices for regular polygon"""
        vertices = []
        edge_length = 1.0
        radius = edge_length / (2 * np.sin(np.pi / sides))
        
        for i in range(sides):
            angle = 2 * np.pi * i / sides
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 0.0
            vertices.append([x, y, z])
        
        return vertices
    
    def _attempt_placement(self, assembly, new_polyform: Dict):
        """Attempt to place new polyform in assembly"""
        # Find target polyform (pick randomly from existing)
        existing = assembly.get_all_polyforms()
        
        if not existing:
            # First polyform - just add it
            assembly.add_polyform(new_polyform)
            return {
                'success': True,
                'method': 'initial',
                'polyform_id': new_polyform['id']
            }
        
        # Pick random target - must add polyform to assembly first
        assembly.add_polyform(new_polyform)
        
        import random
        target = random.choice(existing)
        
        # Use automated placement engine
        result = self.placement.place_polyform(
            target['id'],
            new_polyform['id'],
            assembly
        )
        
        return result
    
    def _handle_placement_result(self, result, assembly):
        """Handle result of placement attempt"""
        # Handle both dict and PlacementResult dataclass
        success = result.get('success') if isinstance(result, dict) else getattr(result, 'success', False)
        
        if success:
            # Success!
            self.state.successful_placements += 1
            self.state.current_order += 1
            
            if self.on_placement_success:
                self.on_placement_success(result)
            
            print(f"✓ Placement {self.state.successful_placements}: Order {self.state.current_order}")
        
        else:
            # Failure
            self.state.failed_attempts += 1
            
            if hasattr(result, 'decay_triggered') and result.decay_triggered:
                self.state.decay_events += 1
                
                if self.on_decay:
                    self.on_decay(result)
                
                print(f"⚡ Decay event {self.state.decay_events}")
            
            if self.on_placement_failure:
                self.on_placement_failure(result)
    
    def get_exploration_stats(self) -> Dict:
        """Get current exploration statistics"""
        success_rate = (self.state.successful_placements / 
                       max(self.state.iterations, 1))
        
        return {
            'is_running': self.state.is_running,
            'current_order': self.state.current_order,
            'iterations': self.state.iterations,
            'successful_placements': self.state.successful_placements,
            'failed_attempts': self.state.failed_attempts,
            'success_rate': success_rate,
            'decay_events': self.state.decay_events,
            'elapsed_time': self.state.elapsed_time,
            'placements_per_minute': (
                self.state.successful_placements / (self.state.elapsed_time / 60)
                if self.state.elapsed_time > 0 else 0
            )
        }
    
    def _track_assembly_state(self, assembly):
        """Track assembly state for canonical N metrics (NEW)"""
        if not CANONICAL_TRACKING_AVAILABLE:
            return
        
        try:
            polyforms = assembly.get_all_polyforms() if hasattr(assembly, 'get_all_polyforms') else []
            bonds = assembly.get_bonds() if hasattr(assembly, 'get_bonds') else []
            
            # Track in appropriate tracker
            if self.config.track_strategy_comparison and self.canonical_trackers:
                # Get tracker for current strategy
                strategy_idx = list(ExplorationStrategy).index(self.config.strategy)
                tracker = list(self.canonical_trackers.ga_integrations.values())[strategy_idx]
                tracker.track_generation(assembly)
            elif self.canonical_main_tracker:
                # Track in main tracker
                self.canonical_main_tracker.track_generation(assembly)
        except Exception as e:
            # Silently fail - tracking should not break exploration
            print(f"⚠️  Tracking error (non-critical): {e}")
    
    def _finalize_tracking(self):
        """Finalize and print tracking report (NEW)"""
        if not CANONICAL_TRACKING_AVAILABLE or not self.config.enable_canonical_tracking:
            return
        
        print("\n" + "="*80)
        print("CANONICAL N TRACKING REPORT")
        print("="*80)
        
        try:
            if self.config.track_strategy_comparison and self.canonical_trackers:
                print(self.canonical_trackers.get_convergence_report())
                self.canonical_trackers.print_comparison()
            elif self.canonical_main_tracker:
                print(self.canonical_main_tracker.finalize())
        except Exception as e:
            print(f"Error generating tracking report: {e}")


# ═══════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from managers import (
        RealMemoryManager,
        RealChainManager,
        RealWorkspaceManager,
        RealProvenanceTracker
    )
    from automated_placement_engine import AutomatedPlacementEngine
    
    print("╔════════════════════════════════════════════════════════╗")
    print("║  CONTINUOUS EXPLORATION ENGINE - TEST MODE            ║")
    print("╚════════════════════════════════════════════════════════╝\n")
    
    # Mock Assembly for testing (simplified)
    class MockAssembly:
        def __init__(self):
            self.polyforms = []
            self.bonds = []
        
        def add_polyform(self, p):
            self.polyforms.append(p)
        
        def get_all_polyforms(self):
            return self.polyforms
        
        def get_bonds(self):
            return self.bonds
    
    # Mock PlacementEngine for testing
    class MockPlacementEngine:
        def place_polyform(self, target_id, new_id, assembly):
            return {'success': True, 'method': 'mock'}
    
    # Create real managers
    memory = RealMemoryManager()
    chains = RealChainManager()
    placement = MockPlacementEngine()
    workspace = RealWorkspaceManager()
    provenance = RealProvenanceTracker()
    
    suggestions = SuggestionEngine(memory, chains)
    
    # Configure exploration
    config = ExplorationConfig(
        strategy=ExplorationStrategy.BALANCED,
        max_order=5,
        max_iterations=10,
        animation_speed=2.0
    )
    
    exploration = ContinuousExplorationEngine(
        placement,
        suggestions,
        workspace,
        provenance,
        config
    )
    
    # Set up callbacks
    def on_success(result):
        print(f"  ✓ Success: {result}")
    
    def on_failure(result):
        print(f"  ✗ Failure")
    
    exploration.on_placement_success = on_success
    exploration.on_placement_failure = on_failure
    
    # Create test assembly
    assembly = MockAssembly()
    
    # Start exploration
    print("Starting exploration...")
    exploration.start_exploration(assembly, seed_polyform={'id': '1', 'sides': 4})
    
    # Let it run for a bit
    time.sleep(3)
    
    # Get stats
    stats = exploration.get_exploration_stats()
    print(f"\n📊 Exploration Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Stop
    exploration.stop_exploration()
    
    print("\n✓ Test complete")
