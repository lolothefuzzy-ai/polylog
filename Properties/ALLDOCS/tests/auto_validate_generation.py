import pathlib
import sys
import time

# Ensure project root in path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from automated_placement_engine import (
    AutomatedPlacementEngine,
    ConnectionEvaluator,
    DecayManager,
    FoldSequencer,
)
from continuous_exploration_engine import (
    ContinuousExplorationEngine,
    ExplorationConfig,
    ExplorationStrategy,
    SuggestionEngine,
)
from managers import (
    RealChainManager,
    RealFoldValidator,
    RealMemoryManager,
    RealProvenanceTracker,
    RealWorkspaceManager,
)


class Assembly:
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
    def get_bonds(self):
        return self.bonds


def main():
    # Managers
    memory = RealMemoryManager()
    chains = RealChainManager()
    validator = RealFoldValidator()
    workspace = RealWorkspaceManager()
    provenance = RealProvenanceTracker()

    # Engine stack
    evaluator = ConnectionEvaluator(memory, chains)
    sequencer = FoldSequencer(validator, workspace, memory_manager=memory)
    decay = DecayManager(chains, memory, workspace)
    engine = AutomatedPlacementEngine(evaluator, sequencer, decay, workspace, provenance)
    # Enable visual validation (headless)
    engine.enable_visual_validation(require_3d_mesh=False, check_collisions=False)

    suggestions = SuggestionEngine(memory, chains)
    config = ExplorationConfig(
        strategy=ExplorationStrategy.BALANCED,
        max_order=6,
        max_iterations=12,
        animation_speed=100.0,
    )
    exploration = ContinuousExplorationEngine(engine, suggestions, workspace, provenance, config)

    asm = Assembly()

    # Run brief autonomous generation
    exploration.start_exploration(asm)
    time.sleep(2.0)
    exploration.stop_exploration()

    # Print basic summary
    stats = exploration.get_exploration_stats()
    print({k: stats[k] for k in ['current_order','iterations','successful_placements','failed_attempts']})


if __name__ == '__main__':
    main()
