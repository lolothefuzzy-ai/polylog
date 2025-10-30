from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time

from automated_placement_engine import (
    ConnectionEvaluator,
    FoldSequencer,
    DecayManager,
    AutomatedPlacementEngine,
)
from managers import (
    RealMemoryManager,
    RealChainManager,
    RealFoldValidator,
    RealWorkspaceManager,
    RealProvenanceTracker,
)
from continuous_exploration_engine import (
    SuggestionEngine,
    ContinuousExplorationEngine,
    ExplorationConfig,
    ExplorationStrategy,
)
from canonical_estimator import canonical_estimate, get_cached
from scipy_constraint_optimizer import ScipyConstraintOptimizer
from optuna_placement_tuner import OptunaPlacementTuner


# ---- Simple in-memory Assembly (thread-safe) ----
class Assembly:
    def __init__(self):
        self._lock = threading.Lock()
        self.polyforms: Dict[str, Dict[str, Any]] = {}
        self.bonds: List[Dict[str, Any]] = []
        self._next_id = 1

    def add_polyform(self, polyform: Dict[str, Any]):
        with self._lock:
            if 'id' not in polyform:
                polyform['id'] = f"poly_{self._next_id}"
                self._next_id += 1
            self.polyforms[polyform['id']] = polyform

    def get_polyform(self, polyform_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.polyforms.get(polyform_id)

    def get_all_polyforms(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.polyforms.values())

    def add_bond(self, bond: Dict[str, Any]):
        with self._lock:
            self.bonds.append(bond)

    def get_bonds(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.bonds)

    def copy(self):
        new_a = Assembly()
        with self._lock:
            new_a.polyforms = self.polyforms.copy()
            new_a.bonds = self.bonds.copy()
            new_a._next_id = self._next_id
        return new_a


# ---- API models ----
class PolyformIn(BaseModel):
    type: str = "polygon"
    sides: int
    position: Optional[List[float]] = None  # [x,y,z]
    vertices: Optional[List[List[float]]] = None

class AddPolyformResponse(BaseModel):
    id: str

class EvaluateRequest(BaseModel):
    target_id: str
    candidate_id: str

class PlaceRequest(BaseModel):
    target_id: str
    candidate_id: str

class ExplorationStartRequest(BaseModel):
    strategy: Optional[str] = "balanced"
    max_order: Optional[int] = 10
    max_iterations: Optional[int] = None
    exploration_rate: Optional[float] = 0.2
    animation_speed: Optional[float] = 1.0
    seed_sides: Optional[int] = None

# Estimator models
class TypeSpec(BaseModel):
    a: int
    c: int

class EstimatorRequest(BaseModel):
    T: float
    types: List[TypeSpec]
    symmetry_factor: Optional[float] = 1.0
    symmetry_notes: Optional[str] = ""


# Constraint optimizer models
class OptimizeConstraintsRequest(BaseModel):
    polyform_ids: List[str]
    target_stability: Optional[float] = 0.85
    target_spacing: Optional[float] = 2.0
    objectives: Optional[Dict[str, float]] = None
    constraints: Optional[Dict[str, float]] = None
    verbose: Optional[bool] = False


class OptimizeConstraintsResponse(BaseModel):
    optimal_angles: Dict[str, float]
    method: str
    elapsed_time: float
    success: bool


# ---- App setup ----
app = FastAPI(title="Polylog Automated Placement API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (real managers)
memory = RealMemoryManager()
chains = RealChainManager()
validator = RealFoldValidator()
workspace = RealWorkspaceManager()
provenance = RealProvenanceTracker()

assembly = Assembly()

# Engines
from stable_library import StableLibrary
stable_lib = StableLibrary()
_evaluator = ConnectionEvaluator(memory, chains)
_sequencer = FoldSequencer(validator, workspace)
_decay = DecayManager(chains, memory, workspace)
placement_engine = AutomatedPlacementEngine(_evaluator, _sequencer, _decay, workspace, provenance, stable_lib)

suggestions = SuggestionEngine(memory, chains)
exploration = ContinuousExplorationEngine(
    placement_engine,
    suggestions,
    workspace,
    provenance,
    ExplorationConfig(strategy=ExplorationStrategy.BALANCED)
)

# Scipy constraint optimizer
scippy_optimizer = ScipyConstraintOptimizer(assembly)

# Optuna placement tuner
optuna_tuner = OptunaPlacementTuner(placement_engine, memory)


# ---- Helpers ----
def _quality_str(q) -> str:
    try:
        return q.value
    except Exception:
        return str(q)


def candidate_to_dict(c) -> Dict[str, Any]:
    return {
        "poly1_id": c.poly1_id,
        "edge1_idx": c.edge1_idx,
        "poly2_id": c.poly2_id,
        "edge2_idx": c.edge2_idx,
        "stability_score": c.stability_score,
        "confidence": c.confidence,
        "quality": _quality_str(c.quality),
        "scaler_match": c.scaler_match,
    }


def attempt_to_dict(a) -> Dict[str, Any]:
    return {
        "candidate": candidate_to_dict(a.candidate),
        "success": a.success,
        "fold_angle": a.fold_angle,
        "validation_time": a.validation_time,
        "failure_reason": a.failure_reason,
        "timestamp": a.timestamp,
    }


def result_to_dict(r) -> Dict[str, Any]:
    # r may be dict (from exploration mock path) or PlacementResult
    if isinstance(r, dict):
        return r
    return {
        "success": r.success,
        "fold_sequence": [attempt_to_dict(a) for a in r.fold_sequence],
        "final_polyform_id": r.final_polyform_id,
        "decay_triggered": r.decay_triggered,
        "reformed_polyforms": r.reformed_polyforms,
        "total_time": r.total_time,
        "confidence_score": r.confidence_score,
    }


# ---- Endpoints ----
@app.get("/health")
def health():
    return {"ok": True, "ts": time.time()}


@app.get("/assembly/polyforms")
def list_polyforms():
    return assembly.get_all_polyforms()


@app.get("/assembly/bonds")
def list_bonds():
    return assembly.get_bonds()


@app.post("/assembly/polyforms", response_model=AddPolyformResponse)
def add_polyform(p: PolyformIn):
    poly: Dict[str, Any] = {
        "type": p.type,
        "sides": p.sides,
        "vertices": p.vertices or [],
        "bonds": [],
        "position": p.position or [0, 0, 0],
    }
    assembly.add_polyform(poly)
    return {"id": poly["id"]}


@app.post("/placement/evaluate")
def evaluate(req: EvaluateRequest):
    cands = _evaluator.evaluate_all_connections(req.target_id, req.candidate_id, assembly)
    return [candidate_to_dict(c) for c in cands]


@app.post("/placement/place")
def place(req: PlaceRequest):
    res = placement_engine.place_polyform(req.target_id, req.candidate_id, assembly)
    return result_to_dict(res)


@app.get("/placement/stats")
def placement_stats():
    return placement_engine.get_placement_stats()


@app.get("/workspace/events")
def workspace_events():
    # Drain workspace event queue for frontend to consume
    return workspace.drain_events()


@app.post("/exploration/start")
def exploration_start(cfg: ExplorationStartRequest):
    strategy = {
        "greedy": ExplorationStrategy.GREEDY,
        "random": ExplorationStrategy.RANDOM,
        "balanced": ExplorationStrategy.BALANCED,
        "systematic": ExplorationStrategy.SYSTEMATIC,
        "learned": ExplorationStrategy.LEARNED,
    }.get((cfg.strategy or "balanced").lower(), ExplorationStrategy.BALANCED)

    exploration.config.strategy = strategy
    if cfg.max_order is not None:
        exploration.config.max_order = cfg.max_order
    if cfg.max_iterations is not None:
        exploration.config.max_iterations = cfg.max_iterations
    if cfg.exploration_rate is not None:
        exploration.config.exploration_rate = cfg.exploration_rate
    if cfg.animation_speed is not None:
        exploration.config.animation_speed = cfg.animation_speed

    seed = None
    if cfg.seed_sides:
        seed = {"type": "polygon", "sides": cfg.seed_sides, "vertices": [], "bonds": []}

    exploration.start_exploration(assembly, seed_polyform=seed)
    return {"started": True}


@app.post("/exploration/stop")
def exploration_stop():
    exploration.stop_exploration()
    return {"stopped": True}


@app.get("/exploration/stats")
def exploration_stats():
    return exploration.get_exploration_stats()


# ---- Canonical estimator endpoints ----
@app.post("/estimator/estimate")
def estimator_estimate(req: EstimatorRequest):
    types_list = [{"a": t.a, "c": t.c} for t in req.types]
    res = canonical_estimate(
        T=req.T,
        types=types_list,
        symmetry_factor=req.symmetry_factor or 1.0,
        symmetry_notes=req.symmetry_notes or "",
        agent_id="api"
    )
    return res


@app.get("/estimator/cache")
def estimator_cache(S_id: str, lnT: float, ln_symmetry: float):
    cached = get_cached(S_id, lnT, ln_symmetry)
    return cached or {"cached": False}


# ---- Scipy Constraint Optimizer endpoints ----
@app.post("/constraints/optimize", response_model=OptimizeConstraintsResponse)
def optimize_constraints(req: OptimizeConstraintsRequest):
    """
    NEW ENDPOINT: Use scipy to find optimal fold angles.
    Supports both single-objective (stability/spacing) and multi-objective optimization.
    """
    import time
    start_time = time.time()
    
    try:
        if req.objectives:
            # Multi-objective optimization
            angles = scippy_optimizer.optimize_multi_objective(
                req.polyform_ids,
                req.objectives,
                constraints=req.constraints,
                verbose=req.verbose or False
            )
            method = "scipy-trust-constr"
        else:
            # Single-objective optimization
            angles = scippy_optimizer.optimize_fold_angles(
                req.polyform_ids,
                target_stability=req.target_stability or 0.85,
                target_spacing=req.target_spacing or 2.0,
                verbose=req.verbose or False
            )
            method = "scipy-SLSQP"
        
        elapsed = time.time() - start_time
        
        return OptimizeConstraintsResponse(
            optimal_angles=angles,
            method=method,
            elapsed_time=elapsed,
            success=True
        )
    except Exception as e:
        import logging
        logging.error(f"Constraint optimization failed: {e}")
        return OptimizeConstraintsResponse(
            optimal_angles={},
            method="error",
            elapsed_time=time.time() - start_time,
            success=False
        )


@app.get("/constraints/history")
def constraints_history():
    """View scipy optimization history"""
    return {
        "history": scippy_optimizer.get_optimization_history(),
        "total_optimizations": len(scippy_optimizer.get_optimization_history())
    }


@app.post("/constraints/clear-history")
def constraints_clear_history():
    """Clear optimization history"""
    scippy_optimizer.clear_history()
    return {"cleared": True}


# ---- Optuna Exploration Optimization endpoints ----
class OptunaOptimizeRequest(BaseModel):
    n_suggestions: Optional[int] = 5
    n_trials: Optional[int] = 100
    verbose: Optional[bool] = False


class OptunaStrategyRequest(BaseModel):
    strategies: Optional[List[str]] = None
    n_trials_per_strategy: Optional[int] = 20


class OptunaSuggestionResponse(BaseModel):
    polyform_spec: Dict[str, Any]
    success_rate: float
    speed_score: float
    confidence: float
    trial_number: int
    reasoning: str


@app.post("/exploration/optuna-optimize")
def optuna_optimize(req: OptunaOptimizeRequest):
    """
    NEW ENDPOINT: Use Optuna Bayesian optimization to find best polyform sequence.
    Replaces hard-coded exploration strategies with principled hyperparameter tuning.
    """
    import time
    start_time = time.time()
    
    try:
        suggestions = optuna_tuner.suggest_polyform_sequence(
            assembly,
            n_suggestions=req.n_suggestions or 5,
            n_trials=req.n_trials or 100,
            verbose=req.verbose or False
        )
        
        elapsed = time.time() - start_time
        
        return {
            "suggestions": [
                {
                    "polyform_spec": s.polyform_spec,
                    "success_rate": s.success_rate,
                    "speed_score": s.speed_score,
                    "confidence": s.confidence,
                    "trial_number": s.trial_number,
                    "reasoning": s.reasoning,
                }
                for s in suggestions
            ],
            "elapsed_time": elapsed,
            "method": "optuna-tpe"
        }
    except Exception as e:
        import logging
        logging.error(f"Optuna optimization failed: {e}")
        return {
            "error": str(e),
            "method": "optuna-tpe"
        }


@app.post("/exploration/optuna-compare-strategies")
def optuna_compare_strategies(req: OptunaStrategyRequest):
    """
    NEW ENDPOINT: Compare exploration strategies using Optuna.
    Returns confidence scores for each strategy.
    """
    try:
        scores = optuna_tuner.optimize_exploration_strategy(
            assembly,
            strategies=req.strategies,
            n_trials_per_strategy=req.n_trials_per_strategy or 20
        )
        
        return {
            "strategy_scores": scores,
            "best_strategy": max(scores.items(), key=lambda x: x[1])[0] if scores else None,
            "method": "optuna-strategy-comparison"
        }
    except Exception as e:
        import logging
        logging.error(f"Strategy comparison failed: {e}")
        return {
            "error": str(e),
            "method": "optuna-strategy-comparison"
        }


@app.get("/exploration/optuna-history")
def optuna_history():
    """View Optuna optimization history"""
    return optuna_tuner.get_optimization_history()


@app.get("/exploration/optuna-analysis")
def optuna_analysis():
    """Analyze Optuna trial performance"""
    return optuna_tuner.get_trial_analysis()


@app.post("/exploration/optuna-export")
def optuna_export(filepath: Optional[str] = "optuna_study.json"):
    """Export Optuna study to JSON"""
    optuna_tuner.export_study(filepath or "optuna_study.json")
    return {"exported": filepath or "optuna_study.json"}


@app.get("/exploration/optuna-suggestion")
def optuna_quick_suggestion(n_trials: Optional[int] = 20):
    """
    Quick single suggestion using fewer trials.
    Fast alternative to full optimization.
    """
    suggestions = optuna_tuner.suggest_next_polyform(
        assembly,
        n_trials=n_trials or 20,
        top_k=1
    )
    
    if suggestions:
        s = suggestions[0]
        return {
            "polyform_spec": s.polyform_spec,
            "success_rate": s.success_rate,
            "speed_score": s.speed_score,
            "confidence": s.confidence,
            "reasoning": s.reasoning,
        }
    else:
        return {"error": "No suggestions found"}
