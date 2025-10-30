"""
GRPC SERVER FOR POLYLOG
=======================

High-performance gRPC server providing:
- Fast binary serialization (protobuf)
- Real-time streaming (exploration updates)
- Bidirectional communication (interactive placement)
- HTTP/2 multiplexing (10x more efficient than REST)

Run with:
  python grpc_server.py --port 50051

Or use from main.py:
  python main.py grpc --port 50051
"""

import grpc
from concurrent import futures
import logging
import time
from typing import Iterator, Optional

# Import generated protobuf code (after running protoc)
try:
    import polylog_pb2
    import polylog_pb2_grpc
except ImportError:
    print("ERROR: Protobuf files not found!")
    print("Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. polylog.proto")
    exit(1)

# Import Polylog modules
from automated_placement_engine import ConnectionEvaluator, FoldSequencer, DecayManager, AutomatedPlacementEngine
from managers import RealMemoryManager, RealChainManager, RealFoldValidator, RealWorkspaceManager, RealProvenanceTracker
from continuous_exploration_engine import ContinuousExplorationEngine, SuggestionEngine, ExplorationConfig, ExplorationStrategy
from stable_library import StableLibrary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Simple in-memory assembly (same as api_server.py)
class Assembly:
    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self.polyforms = {}
        self.bonds = []
        self._next_id = 1

    def add_polyform(self, polyform):
        with self._lock:
            try:
                from gui.polyform_adapter import normalize_polyform
                normalized = normalize_polyform(polyform)
            except Exception:
                normalized = dict(polyform)
                if 'id' not in normalized:
                    normalized['id'] = f"poly_{self._next_id}"
                    self._next_id += 1

            # Advance internal id counter if needed
            if isinstance(normalized.get('id'), str) and normalized['id'].startswith('poly_'):
                try:
                    n = int(normalized['id'].split('_', 1)[1])
                    if n >= self._next_id:
                        self._next_id = n + 1
                except Exception:
                    pass

            self.polyforms[normalized['id']] = normalized

    def get_polyform(self, polyform_id: str):
        with self._lock:
            return self.polyforms.get(polyform_id)

    def get_all_polyforms(self):
        with self._lock:
            return list(self.polyforms.values())

    def add_bond(self, bond):
        with self._lock:
            self.bonds.append(bond)

    def get_bonds(self):
        with self._lock:
            return list(self.bonds)


class PolylogPlacementServicer(polylog_pb2_grpc.PolylogPlacementServicer):
    """
    gRPC service implementation for Polylog.
    
    Provides high-performance placement and exploration services.
    """
    
    def __init__(self, placement_engine, evaluator, exploration_engine):
        self.placement_engine = placement_engine
        self.evaluator = evaluator
        self.exploration_engine = exploration_engine
        logger.info("PolylogPlacementServicer initialized")
    
    def Health(self, request, context):
        """Health check endpoint"""
        logger.info("Health check requested")
        return polylog_pb2.HealthCheckResponse(
            ok=True,
            timestamp=int(time.time() * 1000),
            version="1.0.0"
        )
    
    def EvaluateConnections(self, request, context):
        """
        Evaluate all possible edge connections between two polyforms.
        Returns sorted candidates by stability score.
        """
        logger.info(f"Evaluating connections: {request.target_id} <- {request.candidate_id}")
        
        try:
            # Get assembly from exploration engine
            candidates = self.evaluator.evaluate_all_connections(
                request.target_id,
                request.candidate_id,
                self.exploration_engine.assembly
            )
            
            # Convert to protobuf
            response = polylog_pb2.EvaluateResponse()
            for c in candidates:
                edge = response.candidates.add()
                edge.poly1_id = c.poly1_id
                edge.edge1_idx = c.edge1_idx
                edge.poly2_id = c.poly2_id
                edge.edge2_idx = c.edge2_idx
                edge.stability_score = c.stability_score
                edge.confidence = c.confidence
                edge.quality = c.quality.value if hasattr(c.quality, 'value') else str(c.quality)
            
            logger.info(f"Found {len(candidates)} candidates")
            return response
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return polylog_pb2.EvaluateResponse()
    
    def PlacePolyform(self, request, context):
        """
        Perform automated placement with optimal fold sequence.
        """
        logger.info(f"Placing: {request.candidate_id} on {request.target_id}")
        
        try:
            result = self.placement_engine.place_polyform(
                request.target_id,
                request.candidate_id,
                self.exploration_engine.assembly
            )
            
            return polylog_pb2.PlacementResult(
                success=result.success,
                final_polyform_id=result.final_polyform_id or "",
                total_time=result.total_time,
                confidence_score=result.confidence_score,
                fold_count=len(result.fold_sequence),
                failure_reason=result.fold_sequence[-1].failure_reason if result.fold_sequence and not result.success else ""
            )
            
        except Exception as e:
            logger.error(f"Placement failed: {e}")
            return polylog_pb2.PlacementResult(
                success=False,
                failure_reason=str(e)
            )
    
    def GetExplorationStats(self, request, context):
        """Get current exploration statistics"""
        try:
            stats = self.exploration_engine.get_exploration_stats()
            
            return polylog_pb2.ExplorationStats(
                current_iteration=stats.get('current_iteration', 0),
                successful_placements=stats.get('successful_placements', 0),
                failed_attempts=stats.get('failed_attempts', 0),
                decay_events=stats.get('decay_events', 0),
                elapsed_time=stats.get('elapsed_time', 0.0),
                is_running=stats.get('is_running', False)
            )
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            return polylog_pb2.ExplorationStats()
    
    def StreamExplorationUpdates(self, request, context) -> Iterator[polylog_pb2.ExplorationEvent]:
        """
        NEW: Server-side streaming for real-time exploration updates.
        Replaces long-polling pattern used in REST API.
        
        Yields exploration events as they occur.
        """
        logger.info(f"Streaming exploration updates (strategy: {request.strategy})")
        
        # Configure exploration
        strategy_map = {
            "greedy": ExplorationStrategy.GREEDY,
            "random": ExplorationStrategy.RANDOM,
            "balanced": ExplorationStrategy.BALANCED,
            "systematic": ExplorationStrategy.SYSTEMATIC,
            "learned": ExplorationStrategy.LEARNED,
        }
        strategy = strategy_map.get(request.strategy.lower(), ExplorationStrategy.BALANCED)
        
        config = ExplorationConfig(
            strategy=strategy,
            max_order=request.max_order or 10,
            max_iterations=request.max_iterations or 100,
            exploration_rate=request.exploration_rate or 0.2,
            animation_speed=request.animation_speed or 1.0
        )
        
        try:
            # Start exploration
            seed = None
            if request.seed_sides:
                seed = {
                    "type": "polygon",
                    "sides": request.seed_sides,
                    "vertices": [],
                    "bonds": []
                }
            
            self.exploration_engine.config = config
            self.exploration_engine.start_exploration(
                self.exploration_engine.assembly,
                seed_polyform=seed
            )
            
            # Stream updates
            iteration = 0
            while (self.exploration_engine.is_running() and 
                   iteration < (request.max_iterations or 10000)):
                
                stats = self.exploration_engine.get_exploration_stats()
                
                # Yield progress event
                yield polylog_pb2.ExplorationEvent(
                    type="progress",
                    current_iteration=iteration,
                    success_rate=stats.get('success_rate', 0.0),
                    successful_placements=stats.get('successful_placements', 0),
                    failed_attempts=stats.get('failed_attempts', 0),
                    message=f"Iteration {iteration}: {stats.get('successful_placements', 0)} placements"
                )
                
                iteration += 1
                time.sleep(0.1)  # Yield control
            
            # Final event
            yield polylog_pb2.ExplorationEvent(
                type="done",
                current_iteration=iteration,
                message="Exploration complete"
            )
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield polylog_pb2.ExplorationEvent(
                type="error",
                message=f"Error: {str(e)}"
            )
    
    def InteractivePlacement(self, request_iterator, context) -> Iterator[polylog_pb2.PlacementResult]:
        """
        NEW: Bidirectional streaming for interactive placement.
        Client sends placement requests, server streams results.
        
        Enables batch operations and real-time feedback.
        """
        logger.info("Interactive placement stream started")
        
        try:
            for request in request_iterator:
                logger.debug(f"Interactive placement: {request.candidate_id} on {request.target_id}")
                
                result = self.placement_engine.place_polyform(
                    request.target_id,
                    request.candidate_id,
                    self.exploration_engine.assembly
                )
                
                yield polylog_pb2.PlacementResult(
                    success=result.success,
                    final_polyform_id=result.final_polyform_id or "",
                    total_time=result.total_time,
                    confidence_score=result.confidence_score,
                    fold_count=len(result.fold_sequence)
                )
                
        except Exception as e:
            logger.error(f"Interactive placement failed: {e}")


def start_grpc_server(host: str = "0.0.0.0", port: int = 50051, max_workers: int = 10):
    """
    Start the gRPC server.
    
    Args:
        host: Server host (0.0.0.0 for public)
        port: Server port
        max_workers: Thread pool size
    """
    
    # Initialize managers
    memory = RealMemoryManager()
    chains = RealChainManager()
    validator = RealFoldValidator()
    workspace = RealWorkspaceManager()
    provenance = RealProvenanceTracker()
    
    # Initialize assembly
    assembly = Assembly()
    
    # Initialize engines
    stable_lib = StableLibrary()
    evaluator = ConnectionEvaluator(memory, chains)
    sequencer = FoldSequencer(validator, workspace)
    decay = DecayManager(chains, memory, workspace)
    placement_engine = AutomatedPlacementEngine(evaluator, sequencer, decay, workspace, provenance, stable_lib)
    
    suggestions = SuggestionEngine(memory, chains)
    exploration = ContinuousExplorationEngine(
        placement_engine,
        suggestions,
        workspace,
        provenance,
        ExplorationConfig(strategy=ExplorationStrategy.BALANCED)
    )
    exploration.assembly = assembly  # Share assembly
    
    # Create servicer
    servicer = PolylogPlacementServicer(placement_engine, evaluator, exploration)
    
    # Create server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
        ]
    )
    
    # Register servicer
    polylog_pb2_grpc.add_PolylogPlacementServicer_to_server(servicer, server)
    
    # Bind to port
    server.add_insecure_port(f'{host}:{port}')
    
    # Start
    print(f"\n{'='*60}")
    print(f"gRPC Server starting...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Workers: {max_workers}")
    print(f"{'='*60}\n")
    
    logger.info(f"gRPC server listening on {host}:{port}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.stop(grace=5)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Polylog gRPC Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=50051, help='Server port')
    parser.add_argument('--workers', type=int, default=10, help='Thread pool size')
    
    args = parser.parse_args()
    
    start_grpc_server(host=args.host, port=args.port, max_workers=args.workers)
