"""
AUTOMATED POLYGON/POLYFORM PLACEMENT & FOLDING ENGINE
======================================================

Implements intelligent, automated placement logic that:
1. Evaluates all possible edge connections for stability
2. Automatically attempts folding sequences
3. Handles failures through decay and reformation
4. Enables continuous exploration and growth

Key Components:
- ConnectionEvaluator: Scores all possible edge pairs for stability
- FoldSequencer: Iteratively attempts folds in order of confidence
- DecayManager: Handles failure → reformation into stable polyforms
- ExplorationEngine: Background autonomous assembly growth
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════
# CORE DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

class ConnectionQuality(Enum):
    """Quality levels for edge connections"""
    PERFECT = "perfect"      # 0.9+ stability
    EXCELLENT = "excellent"  # 0.75-0.9
    GOOD = "good"           # 0.6-0.75
    FAIR = "fair"           # 0.4-0.6
    POOR = "poor"           # 0.2-0.4
    FAILED = "failed"       # <0.2


@dataclass
class EdgeCandidate:
    """Represents a potential edge-to-edge connection"""
    poly1_id: str
    edge1_idx: int
    poly2_id: str
    edge2_idx: int
    stability_score: float
    confidence: float
    scaler_match: Optional[str] = None
    quality: ConnectionQuality = ConnectionQuality.FAILED
    
    def __post_init__(self):
        """Auto-assign quality based on stability score"""
        if self.stability_score >= 0.9:
            self.quality = ConnectionQuality.PERFECT
        elif self.stability_score >= 0.75:
            self.quality = ConnectionQuality.EXCELLENT
        elif self.stability_score >= 0.6:
            self.quality = ConnectionQuality.GOOD
        elif self.stability_score >= 0.4:
            self.quality = ConnectionQuality.FAIR
        elif self.stability_score >= 0.2:
            self.quality = ConnectionQuality.POOR
        else:
            self.quality = ConnectionQuality.FAILED


@dataclass
class FoldAttempt:
    """Records a single fold attempt"""
    candidate: EdgeCandidate
    success: bool
    fold_angle: Optional[float] = None
    validation_time: float = 0.0
    failure_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class PlacementResult:
    """Result of automated placement attempt"""
    success: bool
    fold_sequence: List[FoldAttempt]
    final_polyform_id: Optional[str] = None
    decay_triggered: bool = False
    reformed_polyforms: List[str] = field(default_factory=list)
    total_time: float = 0.0
    confidence_score: float = 0.0


# ═══════════════════════════════════════════════════════════════
# CONNECTION EVALUATOR
# ═══════════════════════════════════════════════════════════════

class ConnectionEvaluator:
    """
    Evaluates all possible edge connections and scores them for stability.
    Uses learned scalers and geometric analysis.
    """
    
    def __init__(self, memory_manager, chain_manager, use_multilevel_cache: bool = True):
        from collections import OrderedDict
        self.memory = memory_manager
        self.chains = chain_manager
        self.enable_broad_phase = True
        self.proximity_cutoff = 3.5  # only consider polygons within this centroid distance
        
        # PHASE 2: Use multilevel cache by default
        self.use_multilevel_cache = use_multilevel_cache
        if use_multilevel_cache:
            try:
                from multilevel_cache import MultiLevelCacheAdapter
                self._lru_cache = MultiLevelCacheAdapter(max_cache_size=50000)
                self._cache_interface = 'multilevel'
            except Exception as e:
                import logging
                logging.warning(f"Could not load multilevel cache: {e}, falling back to OrderedDict")
                self._lru_cache = OrderedDict()
                self._cache_interface = 'simple'
        else:
            self._lru_cache = OrderedDict()
            self._cache_interface = 'simple'
        
        self._cache_max = 50000
        # Optional disk cache
        try:
            from evaluator_cache import EvaluatorCache
            self.disk_cache = EvaluatorCache()
        except Exception:
            self.disk_cache = None
        
        # PHASE 2: Spatial indexing support
        try:
            from spatial_index import SpatialIndexedCollisionValidator
            self.spatial_index = SpatialIndexedCollisionValidator()
        except Exception:
            self.spatial_index = None
        
        # PHASE 1 STABILIZATION: Early termination threshold for high-n stability
        # Limits evaluation of edge pairs to maintain performance at n > 1000
        self.TOP_K_LIMIT = 100  # Return top-100 candidates max (prevents O(n²) explosion)
        
    def clear_cache(self):
        """Clear all cache levels."""
        if self.disk_cache:
            try:
                self.disk_cache.clear()
            except Exception:
                pass
        try:
            if self._cache_interface == 'multilevel':
                self._lru_cache.clear()
            else:
                self._lru_cache.clear()
        except Exception:
            pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self._cache_interface == 'multilevel':
            try:
                return self._lru_cache.cache.get_stats()
            except Exception:
                return {}
        return {}
        
    def evaluate_all_connections(
        self,
        target_polyform_id: str,
        candidate_polyform_id: str,
        assembly
    ) -> List[EdgeCandidate]:
        """
        Evaluate ALL possible edge pairs between target and candidate.
        Returns sorted list by descending stability score.
        """
        candidates = []
        
        target_poly = assembly.get_polyform(target_polyform_id)
        candidate_poly = assembly.get_polyform(candidate_polyform_id)
        
        if not target_poly or not candidate_poly:
            return []
        
        # Get all edges from both polyforms
        target_edges = self._get_all_edges(target_poly)
        candidate_edges = self._get_all_edges(candidate_poly)
        
        # Broad-phase culling by centroid distance (no external deps)
        if self.enable_broad_phase:
            def _centroid(verts):
                arr = np.array(verts, dtype=float)
                if arr.size == 0:
                    return np.zeros(3, dtype=float)
                if arr.shape[1] < 3:
                    # pad to 3D
                    pad = np.zeros((arr.shape[0], 3 - arr.shape[1]))
                    arr = np.hstack([arr, pad])
                return arr.mean(axis=0)
            c1 = _centroid(target_poly.get('vertices', []))
            c2 = _centroid(candidate_poly.get('vertices', []))
            if np.linalg.norm(c1 - c2) > self.proximity_cutoff:
                return []
        
        # Evaluate each possible edge pair
        # PHASE 1 STABILIZATION: Early termination for high-n performance
        for t_edge_idx, t_edge in enumerate(target_edges):
            for c_edge_idx, c_edge in enumerate(candidate_edges):
                
                # Skip if edge already bonded
                if self._is_edge_bonded(target_poly, t_edge_idx):
                    continue
                if self._is_edge_bonded(candidate_poly, c_edge_idx):
                    continue
                
                # Calculate stability score (PHASE 2: with multilevel cache)
                cache_key = (target_polyform_id, t_edge_idx, candidate_polyform_id, c_edge_idx)
                score = None
                
                # Try cache get
                if self._cache_interface == 'multilevel':
                    score = self._lru_cache.get(cache_key)
                else:
                    # Simple OrderedDict interface
                    if cache_key in self._lru_cache:
                        score = self._lru_cache[cache_key]
                        if hasattr(self._lru_cache, 'move_to_end'):
                            self._lru_cache.move_to_end(cache_key)
                
                if score is None:
                    # Optional disk cache
                    if self.disk_cache:
                        try:
                            score = self.disk_cache.get(str(cache_key))
                        except Exception:
                            score = None
                    
                    if score is None:
                        score = self._calculate_stability(
                            target_poly, t_edge_idx,
                            candidate_poly, c_edge_idx,
                            assembly
                        )
                        if self.disk_cache:
                            try:
                                self.disk_cache.set(str(cache_key), float(score))
                            except Exception:
                                pass
                    
                    # Put into cache
                    if self._cache_interface == 'multilevel':
                        self._lru_cache.put(cache_key, score)
                    else:
                        self._lru_cache[cache_key] = score
                        if len(self._lru_cache) > self._cache_max:
                            self._lru_cache.popitem(last=False)
                
                # Check for scaler match (boosts confidence)
                scaler_match = self._check_scaler_match(
                    target_poly, candidate_poly, assembly
                )
                
                confidence = self._calculate_confidence(
                    score, scaler_match, assembly
                )
                
                candidate = EdgeCandidate(
                    poly1_id=target_polyform_id,
                    edge1_idx=t_edge_idx,
                    poly2_id=candidate_polyform_id,
                    edge2_idx=c_edge_idx,
                    stability_score=score,
                    confidence=confidence,
                    scaler_match=scaler_match
                )
                
                candidates.append(candidate)
                
                # PHASE 1 STABILIZATION: Early termination check
                # Once we have enough good candidates, stop evaluating more pairs
                if len(candidates) >= self.TOP_K_LIMIT * 2:
                    # Sort intermediate results to keep only top candidates
                    candidates.sort(
                        key=lambda c: (c.stability_score, c.confidence),
                        reverse=True
                    )
                    candidates = candidates[:self.TOP_K_LIMIT]
                    # If we still have TOP_K_LIMIT candidates, we can skip further evaluation
                    if len(candidates) >= self.TOP_K_LIMIT:
                        break  # Early termination from inner loop
            
            # Check if we should break from outer loop as well
            if len(candidates) >= self.TOP_K_LIMIT:
                break
        
        # Sort by stability (descending), then by confidence
        candidates.sort(
            key=lambda c: (c.stability_score, c.confidence),
            reverse=True
        )
        
        # PHASE 1 STABILIZATION: Return only top-k candidates
        return candidates[:self.TOP_K_LIMIT]
    
    def _calculate_stability(
        self,
        poly1, edge1_idx,
        poly2, edge2_idx,
        assembly
    ) -> float:
        """
        Calculate stability score for an edge pair connection.
        
        Factors:
        - Edge length compatibility (must be ~1.0)
        - Vertex proximity
        - Angle compatibility
        - Existing bond structure stability
        - Scaler pattern recognition
        """
        score = 0.0
        
        # Factor 1: Edge length match (critical)
        edge1_len = self._get_edge_length(poly1, edge1_idx)
        edge2_len = self._get_edge_length(poly2, edge2_idx)
        length_match = 1.0 - abs(edge1_len - edge2_len)
        score += length_match * 0.4  # 40% weight
        
        # Factor 2: Vertex proximity (for alignment)
        proximity = self._calculate_vertex_proximity(
            poly1, edge1_idx, poly2, edge2_idx
        )
        score += proximity * 0.2  # 20% weight
        
        # Factor 3: Angle compatibility
        angle_compat = self._calculate_angle_compatibility(
            poly1, edge1_idx, poly2, edge2_idx
        )
        score += angle_compat * 0.2  # 20% weight
        
        # Factor 4: Bond structure stability
        structure_score = self._evaluate_bond_structure(poly1, poly2, assembly)
        score += structure_score * 0.15  # 15% weight
        
        # Factor 5: Scaler boost
        scaler_boost = self._get_scaler_boost(poly1, poly2, assembly)
        score += scaler_boost * 0.05  # 5% weight
        
        return np.clip(score, 0.0, 1.0)
    
    def _calculate_confidence(
        self,
        stability_score: float,
        scaler_match: Optional[str],
        assembly
    ) -> float:
        """
        Calculate confidence in this connection succeeding.
        
        Higher confidence = more likely to succeed in fold validation.
        """
        confidence = stability_score
        
        # Boost confidence if scaler matched
        if scaler_match:
            scaler_confidence = self.memory.get_scaler_confidence(scaler_match)
            confidence = confidence * 0.5 + scaler_confidence * 0.5
        
        # Boost if similar patterns succeeded before
        pattern_history = self._get_pattern_history(assembly)
        if pattern_history:
            confidence = confidence * 0.7 + pattern_history * 0.3
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _get_all_edges(self, polyform) -> List[Tuple]:
        """Extract all edges from a polyform"""
        edges = []
        vertices = polyform.get('vertices', [])
        n = len(vertices)
        for i in range(n):
            edges.append((vertices[i], vertices[(i+1) % n]))
        return edges
    
    def _is_edge_bonded(self, polyform, edge_idx: int) -> bool:
        """Check if an edge already has a bond"""
        bonds = polyform.get('bonds', [])
        for bond in bonds:
            if bond.get('edge1_idx') == edge_idx or bond.get('edge2_idx') == edge_idx:
                return True
        return False
    
    def _get_edge_length(self, polyform, edge_idx: int) -> float:
        """Get length of an edge (should always be ~1.0)"""
        edges = self._get_all_edges(polyform)
        if edge_idx >= len(edges):
            return 0.0
        v1, v2 = edges[edge_idx]
        return np.linalg.norm(np.array(v2) - np.array(v1))
    
    def _calculate_vertex_proximity(self, poly1, edge1_idx, poly2, edge2_idx) -> float:
        """Calculate how close edge vertices are (for alignment scoring)"""
        edges1 = self._get_all_edges(poly1)
        edges2 = self._get_all_edges(poly2)
        
        if edge1_idx >= len(edges1) or edge2_idx >= len(edges2):
            return 0.0
        
        v1a, v1b = edges1[edge1_idx]
        v2a, v2b = edges2[edge2_idx]
        
        # Calculate minimum distance between edge endpoints
        dist1 = np.linalg.norm(np.array(v1a) - np.array(v2a))
        dist2 = np.linalg.norm(np.array(v1b) - np.array(v2b))
        min_dist = min(dist1, dist2)
        
        # Convert distance to proximity score (closer = higher)
        proximity = np.exp(-min_dist)  # Exponential decay
        return proximity
    
    def _calculate_angle_compatibility(self, poly1, edge1_idx, poly2, edge2_idx) -> float:
        """Calculate angle compatibility between edges"""
        # Simplified: check if edges are roughly parallel/anti-parallel
        edges1 = self._get_all_edges(poly1)
        edges2 = self._get_all_edges(poly2)
        
        if edge1_idx >= len(edges1) or edge2_idx >= len(edges2):
            return 0.0
        
        v1a, v1b = edges1[edge1_idx]
        v2a, v2b = edges2[edge2_idx]
        
        vec1 = np.array(v1b) - np.array(v1a)
        vec2 = np.array(v2b) - np.array(v2a)
        
        # Normalize
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
        
        # Dot product gives cosine of angle
        dot = np.abs(np.dot(vec1_norm, vec2_norm))
        
        return dot  # 1.0 = parallel, 0.0 = perpendicular
    
    def _evaluate_bond_structure(self, poly1, poly2, assembly) -> float:
        """Evaluate if adding this bond creates a stable structure"""
        # Simplified: check if existing bonds form a consistent pattern
        existing_bonds = assembly.get_bonds()
        if len(existing_bonds) == 0:
            return 0.5  # Neutral for first bond
        
        # More bonds = need higher stability
        return 1.0 / (1.0 + len(existing_bonds) * 0.1)
    
    def _get_scaler_boost(self, poly1, poly2, assembly) -> float:
        """Get boost if this connection matches a known scaler pattern"""
        scaler_match = self._check_scaler_match(poly1, poly2, assembly)
        if scaler_match:
            return self.memory.get_scaler_confidence(scaler_match)
        return 0.0
    
    def _check_scaler_match(self, poly1, poly2, assembly) -> Optional[str]:
        """Check if this connection matches a known scaler pattern"""
        # Generate pattern signature
        signature = self._generate_signature(poly1, poly2, assembly)
        
        # Check against known scalers
        for scaler_name, scaler in self.memory.get_all_scalers().items():
            if scaler.matches(signature):
                return scaler_name
        
        return None
    
    def _generate_signature(self, poly1, poly2, assembly) -> str:
        """Generate pattern signature for scaler matching"""
        sides1 = poly1.get('sides', 0)
        sides2 = poly2.get('sides', 0)
        return f"{sides1}-{sides2}"
    
    def _get_pattern_history(self, assembly) -> float:
        """Get historical success rate for similar patterns"""
        # Query memory manager for successful patterns with similar context
        context = {
            'total_polyforms': len(assembly.get_all_polyforms()),
            'total_bonds': len(assembly.get_bonds()),
            'avg_sides': sum(p.get('sides', 0) for p in assembly.get_all_polyforms()) / max(1, len(assembly.get_all_polyforms()))
        }
        
        patterns = self.memory.query_successful_patterns(context)
        if patterns:
            avg_success = sum(p.get('success_rate', 0.5) for p in patterns) / len(patterns)
            return avg_success
        
        return 0.5  # Default neutral if no history


# ═══════════════════════════════════════════════════════════════
# FOLD SEQUENCER
# ═══════════════════════════════════════════════════════════════

from concurrent.futures import ThreadPoolExecutor, as_completed

class FoldSequencer:
    """
    Manages the iterative folding sequence, attempting folds in order
    of stability until local maximum is reached.
    """
    
    def __init__(self, fold_validator, workspace_manager, memory_manager=None):
        self.validator = fold_validator
        self.workspace = workspace_manager
        self.memory = memory_manager  # Optional, will be injected by engine if not provided
        self.attempt_history = []
        self.parallel_validations = True
        self.max_workers = 4
        
    def execute_fold_sequence(
        self,
        candidates: List[EdgeCandidate],
        assembly,
        max_attempts: int = 10
    ) -> Tuple[List[FoldAttempt], bool]:
        """
        Attempt folds in order of stability score until one succeeds
        or max attempts reached.
        
        Returns: (fold_attempts, success)
        """
        attempts = []
        
        # Try fast-path scaler matches first (sequential)
        scaler_first = [c for c in candidates[:max_attempts] if c.scaler_match]
        normal = [c for c in candidates[:max_attempts] if not c.scaler_match]

        for candidate in scaler_first:
            attempt = self._attempt_fold(candidate, assembly)
            attempts.append(attempt)
            if attempt.success:
                self._apply_successful_fold(candidate, assembly)
                return attempts, True

        # Parallel validate remaining
        if self.parallel_validations and normal:
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futures = {ex.submit(self._validated_fold, cand, assembly): cand for cand in normal}
                for fut in as_completed(futures):
                    cand = futures[fut]
                    result = fut.result()
                    attempt = FoldAttempt(
                        candidate=cand,
                        success=result['success'],
                        fold_angle=result.get('fold_angle'),
                        validation_time=0.0,
                        failure_reason=result.get('failure_reason')
                    )
                    attempts.append(attempt)
                    if attempt.success:
                        self._apply_successful_fold(cand, assembly)
                        return attempts, True
        else:
            for candidate in normal:
                attempt = self._attempt_fold(candidate, assembly)
                attempts.append(attempt)
                if attempt.success:
                    self._apply_successful_fold(candidate, assembly)
                    return attempts, True

        # All attempts failed
        return attempts, False
    
    def _attempt_fold(
        self,
        candidate: EdgeCandidate,
        assembly
    ) -> FoldAttempt:
        """
        Attempt a single fold operation with validation.
        """
        start_time = time.time()
        
        # Check if scaler provides fast-path
        if candidate.scaler_match:
            result = self._fast_path_fold(candidate, assembly)
        else:
            result = self._validated_fold(candidate, assembly)
        
        validation_time = time.time() - start_time
        
        return FoldAttempt(
            candidate=candidate,
            success=result['success'],
            fold_angle=result.get('fold_angle'),
            validation_time=validation_time,
            failure_reason=result.get('failure_reason')
        )
    
    def _fast_path_fold(self, candidate: EdgeCandidate, assembly) -> Dict:
        """Execute fold using scaler rules (bypasses validation)"""
        mm = getattr(self, 'memory', None)
        if mm is None and hasattr(self, 'validator') and hasattr(self.validator, 'memory'):
            mm = self.validator.memory
        if mm is None:
            return {'success': False, 'failure_reason': 'No memory manager available'}
        scaler = mm.get_scaler(candidate.scaler_match)
        
        if not scaler:
            return {'success': False, 'failure_reason': 'Scaler not found'}
        
        # Get fold angle from scaler
        fold_angle = scaler.get_fold_angle(
            candidate.poly1_id, candidate.edge1_idx,
            candidate.poly2_id, candidate.edge2_idx
        )
        
        # Apply fold directly (trust scaler)
        return {
            'success': True,
            'fold_angle': fold_angle,
            'method': 'scaler_fast_path'
        }
    
    def _validated_fold(self, candidate: EdgeCandidate, assembly) -> Dict:
        """Execute fold with full geometric validation"""
        # Create temporary assembly to test fold
        test_assembly = assembly.copy()
        
        # Apply fold transformation
        fold_angle = self._estimate_fold_angle(candidate, assembly)
        self._apply_fold_transform(
            test_assembly,
            candidate.poly2_id,
            candidate.edge2_idx,
            fold_angle
        )
        
        # Validate for intersections
        validation_result = self.validator.validate_fold(test_assembly)
        
        if validation_result['is_valid']:
            return {
                'success': True,
                'fold_angle': fold_angle,
                'method': 'validated'
            }
        else:
            return {
                'success': False,
                'failure_reason': validation_result.get('reason'),
                'method': 'validated'
            }
    
    def _estimate_fold_angle(self, candidate: EdgeCandidate, assembly) -> float:
        """Estimate appropriate fold angle based on geometry"""
        # Simplified: use default angles based on polygon types
        poly1 = assembly.get_polyform(candidate.poly1_id)
        poly2 = assembly.get_polyform(candidate.poly2_id)
        
        if not poly1 or not poly2:
            return np.pi / 2  # Default 90 degree fold
        
        sides1 = poly1.get('sides', 4)
        sides2 = poly2.get('sides', 4)
        
        # Heuristic: more sides = smaller interior angles = larger fold angles
        angle = np.pi * (1.0 - 2.0 / (sides1 + sides2))
        
        return angle
    
    def _apply_fold_transform(
        self,
        assembly,
        poly_id: str,
        edge_idx: int,
        angle: float
    ):
        """Apply fold transformation to polygon"""
        poly = assembly.get_polyform(poly_id)
        
        if not poly:
            return  # Polyform not found, cannot transform
        
        # Get edge vertices
        edges = self._get_edges(poly)
        if edge_idx >= len(edges):
            return
        
        v1, v2 = edges[edge_idx]
        
        # Compute rotation axis (edge direction)
        axis = np.array(v2) - np.array(v1)
        axis = axis / (np.linalg.norm(axis) + 1e-8)
        
        # Apply Rodrigues rotation formula to all vertices
        vertices = poly.get('vertices', [])
        rotated_vertices = []
        
        for v in vertices:
            v_rot = self._rodrigues_rotation(v, v1, axis, angle)
            rotated_vertices.append(v_rot)
        
        poly['vertices'] = rotated_vertices
    
    def _rodrigues_rotation(self, point, pivot, axis, angle):
        """Rotate point around axis through pivot by angle (Rodrigues formula)"""
        p = np.array(point) - np.array(pivot)
        k = np.array(axis)
        
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        p_rot = (p * cos_a + 
                 np.cross(k, p) * sin_a + 
                 k * np.dot(k, p) * (1 - cos_a))
        
        return (p_rot + np.array(pivot)).tolist()
    
    def _get_edges(self, polyform):
        """Get all edges from polyform"""
        vertices = polyform.get('vertices', [])
        n = len(vertices)
        edges = [(vertices[i], vertices[(i+1) % n]) for i in range(n)]
        return edges
    
    def _apply_successful_fold(self, candidate: EdgeCandidate, assembly):
        """Update assembly after successful fold"""
        # Create bond
        bond = {
            'poly1_id': candidate.poly1_id,
            'edge1_idx': candidate.edge1_idx,
            'poly2_id': candidate.poly2_id,
            'edge2_idx': candidate.edge2_idx,
            'fold_angle': candidate.quality.value
        }
        
        assembly.add_bond(bond)
        
        # Update workspace visualization
        self.workspace.update_bond_visualization(bond)
        
        # Spatial post-processing (snap + auto-bond)
        if hasattr(self.workspace, 'register_assembly'):
            try:
                self.workspace.register_assembly(assembly)
                self.workspace.postprocess_assembly(assembly)
            except Exception:
                pass
        # Invalidate evaluator cache after topology change if available
        if hasattr(self, 'validator') and hasattr(self, 'workspace'):
            try:
                # evaluator sits on engine, not here; cache cleared in engine
                pass
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# DECAY MANAGER
# ═══════════════════════════════════════════════════════════════

class DecayManager:
    """
    Handles failure cases by triggering decay and reformation into
    more stable polyform configurations.
    """
    
    def __init__(self, chain_manager, memory_manager, workspace_manager):
        self.chains = chain_manager
        self.memory = memory_manager
        self.workspace = workspace_manager
        self.decay_history = []
        
    def trigger_decay(
        self,
        failed_attempts: List[FoldAttempt],
        assembly
    ) -> List[str]:
        """
        Analyze failures and decompose into more stable sub-polyforms.
        
        Returns: List of new stable polyform IDs
        """
        # Analyze failure patterns
        failure_analysis = self._analyze_failures(failed_attempts)
        
        # Find alternative stable configurations
        stable_alternatives = self._find_stable_alternatives(
            failure_analysis,
            assembly
        )
        
        if not stable_alternatives:
            return []
        
        # Select highest confidence alternative
        best_alternative = max(
            stable_alternatives,
            key=lambda a: a['confidence']
        )
        
        # Execute decay and reformation
        new_polyforms = self._execute_reformation(
            best_alternative,
            assembly
        )
        
        # Visualize decay animation
        self._animate_decay(assembly, new_polyforms)
        
        # Log decay event
        self._log_decay_event(failed_attempts, new_polyforms)
        
        return new_polyforms
    
    def _analyze_failures(self, failed_attempts: List[FoldAttempt]) -> Dict:
        """Analyze what went wrong in failed attempts"""
        analysis = {
            'failure_types': defaultdict(int),
            'problematic_edges': set(),
            'confidence_average': 0.0
        }
        
        for attempt in failed_attempts:
            # Count failure types
            reason = attempt.failure_reason or 'unknown'
            analysis['failure_types'][reason] += 1
            
            # Mark problematic edges
            analysis['problematic_edges'].add(
                (attempt.candidate.poly1_id, attempt.candidate.edge1_idx)
            )
            analysis['problematic_edges'].add(
                (attempt.candidate.poly2_id, attempt.candidate.edge2_idx)
            )
        
        # Calculate average confidence of failures
        if failed_attempts:
            avg_conf = sum(a.candidate.confidence for a in failed_attempts) / len(failed_attempts)
            analysis['confidence_average'] = avg_conf
        
        return analysis
    
    def _find_stable_alternatives(
        self,
        failure_analysis: Dict,
        assembly
    ) -> List[Dict]:
        """
        Find alternative stable polyforms by:
        1. Removing problematic edges
        2. Rearranging into known stable configurations
        3. Using memory of previously successful patterns
        """
        alternatives = []
        
        # Strategy 1: Decompose into smaller stable units
        decomposed = self._decompose_to_stable_units(assembly)
        alternatives.extend(decomposed)
        
        # Strategy 2: Try known stable patterns
        known_stables = self._try_known_patterns(assembly)
        alternatives.extend(known_stables)
        
        # Strategy 3: Simplify to base polyforms
        simplified = self._simplify_to_base(assembly)
        alternatives.extend(simplified)
        
        return alternatives
    
    def _decompose_to_stable_units(self, assembly) -> List[Dict]:
        """Break assembly into smaller stable sub-polyforms"""
        alternatives = []
        
        # Get all connected components
        components = self.chains.get_connected_components(assembly)
        
        for component in components:
            # Check if component is stable
            stability = self._evaluate_component_stability(component)
            
            if stability > 0.6:
                alternatives.append({
                    'type': 'decomposed',
                    'polyforms': component,
                    'confidence': stability
                })
        
        return alternatives
    
    def _try_known_patterns(self, assembly) -> List[Dict]:
        """Try to reform into known stable patterns from memory"""
        alternatives = []
        
        # Get polygon composition
        composition = self._get_composition(assembly)
        
        # Check memory for stable patterns with similar composition
        known_patterns = self.memory.query_stable_patterns(composition)
        
        for pattern in known_patterns:
            alternatives.append({
                'type': 'known_pattern',
                'pattern': pattern,
                'confidence': pattern.get('confidence', 0.5)
            })
        
        return alternatives
    
    def _simplify_to_base(self, assembly) -> List[Dict]:
        """Simplify to individual polygons (always stable)"""
        polygons = assembly.get_all_polyforms()
        
        return [{
            'type': 'base_polygons',
            'polyforms': [p['id'] for p in polygons],
            'confidence': 1.0  # Individual polygons always stable
        }]
    
    def _evaluate_component_stability(self, component) -> float:
        """Evaluate stability of a connected component"""
        # Simplified: count ratio of closed edges
        total_edges = sum(p.get('sides', 0) for p in component)
        bonded_edges = sum(len(p.get('bonds', [])) for p in component)
        
        if total_edges == 0:
            return 0.0
        
        return bonded_edges / total_edges
    
    def _get_composition(self, assembly) -> str:
        """Get polygon composition signature"""
        polyforms = assembly.get_all_polyforms()
        sides_list = sorted([p.get('sides', 0) for p in polyforms])
        return '-'.join(map(str, sides_list))
    
    def _execute_reformation(self, alternative: Dict, assembly) -> List[str]:
        """Execute the reformation into stable configuration"""
        alt_type = alternative['type']
        
        if alt_type == 'decomposed':
            return self._apply_decomposition(alternative, assembly)
        elif alt_type == 'known_pattern':
            return self._apply_known_pattern(alternative, assembly)
        elif alt_type == 'base_polygons':
            return self._apply_simplification(alternative, assembly)
        
        return []
    
    def _apply_decomposition(self, alternative: Dict, assembly) -> List[str]:
        """Apply decomposition into stable sub-polyforms"""
        new_ids = []
        
        for component in alternative['polyforms']:
            # Create new polyform from component
            new_id = str(uuid.uuid4())
            new_polyform = {
                'id': new_id,
                'type': 'stable_subform',
                'polygons': component,
                'confidence': alternative['confidence']
            }
            
            assembly.add_polyform(new_polyform)
            new_ids.append(new_id)
        
        return new_ids
    
    def _apply_known_pattern(self, alternative: Dict, assembly) -> List[str]:
        """Apply known stable pattern from memory/library"""
        pattern = alternative['pattern']
        new_ids = []
        
        # Get pattern specification
        next_polyform = pattern.get('next_polyform', {})
        if next_polyform:
            # Create polyform based on pattern
            new_id = str(uuid.uuid4())
            new_polyform_spec = {
                'id': new_id,
                'type': next_polyform.get('type', 'polygon'),
                'sides': next_polyform.get('sides', 4),
                'confidence': pattern.get('success_rate', 0.5)
            }
            
            # Generate vertices if needed
            from polygon_utils import create_polygon
            if 'vertices' not in new_polyform_spec and 'sides' in new_polyform_spec:
                poly = create_polygon(new_polyform_spec['sides'])
                new_polyform_spec['vertices'] = poly.get('vertices', [])
            
            assembly.add_polyform(new_polyform_spec)
            new_ids.append(new_id)
        
        return new_ids
    
    def _apply_simplification(self, alternative: Dict, assembly) -> List[str]:
        """Simplify to individual polygons"""
        return alternative['polyforms']
    
    def _animate_decay(self, assembly, new_polyforms: List[str]):
        """Visualize decay animation and postprocess"""
        # Trigger workspace decay animation event
        self.workspace.trigger_decay_animation(assembly, new_polyforms)
        
        # After decay/reformation, register assembly and perform spatial postprocessing
        # This includes vertex snapping and auto-bonding of aligned edges
        if hasattr(self.workspace, 'register_assembly'):
            try:
                self.workspace.register_assembly(assembly)
                self.workspace.postprocess_assembly(assembly)
            except Exception as e:
                # Gracefully handle postprocessing errors
                import warnings
                warnings.warn(f"Postprocessing failed: {e}")
    
    def _log_decay_event(self, failed_attempts: List[FoldAttempt], new_polyforms: List[str]):
        """Log decay event for provenance"""
        event = {
            'timestamp': time.time(),
            'failed_attempts': len(failed_attempts),
            'new_polyforms': new_polyforms,
            'avg_confidence': sum(a.candidate.confidence for a in failed_attempts) / len(failed_attempts) if failed_attempts else 0.0
        }
        
        self.decay_history.append(event)


# ═══════════════════════════════════════════════════════════════
# AUTOMATED PLACEMENT ENGINE (Main Controller)
# ═══════════════════════════════════════════════════════════════

class AutomatedPlacementEngine:
    """
    Main controller orchestrating the entire automated placement workflow.
    
    Supports both 2D and 3D placement modes:
    - 2D mode: Traditional flat folding
    - 3D mode: Full 3D hinge tracking and out-of-plane folding
    """
    
    def __init__(
        self,
        connection_evaluator,
        fold_sequencer,
        decay_manager,
        workspace_manager,
        provenance_tracker,
        stable_library=None,
        hinge_manager=None
    ):
        self.evaluator = connection_evaluator
        self.sequencer = fold_sequencer
        self.decay = decay_manager
        self.workspace = workspace_manager
        self.provenance = provenance_tracker
        self.stable_library = stable_library
        
        # 3D mode support with hinge tracking
        self.hinge_manager = hinge_manager
        self._enable_3d_mode = False
        
        # Ensure sequencer has access to memory manager for fast-path
        try:
            if getattr(self.sequencer, 'memory', None) is None and hasattr(self.evaluator, 'memory'):
                self.sequencer.memory = self.evaluator.memory
        except Exception:
            pass
        
        self.placement_history = []
    
    def enable_3d_mode(self, enable: bool = True):
        """
        Enable or disable 3D-aware placement mode.
        
        When enabled, successful fold operations will create hinges
        in the HingeManager for 3D tracking and manipulation.
        
        Args:
            enable: True to enable 3D mode, False for traditional 2D mode
        """
        if enable and self.hinge_manager is None:
            raise ValueError("Cannot enable 3D mode: HingeManager not provided")
        self._enable_3d_mode = enable
    
    def is_3d_mode_enabled(self) -> bool:
        """Check if 3D mode is currently enabled."""
        return self._enable_3d_mode

    def enable_visual_validation(self, require_3d_mesh: bool = False, check_collisions: bool = False):
        """Enable post-placement visual assembly validation (non-blocking).
        Records validation reports to provenance; does not alter placement result.
        """
        self._visual_validation_opts = {
            'require_3d_mesh': bool(require_3d_mesh),
            'check_collisions': bool(check_collisions)
        }
    
    def get_hinge_manager(self):
        """Get the HingeManager instance (may be None)."""
        return self.hinge_manager
        
    def place_polyform(
        self,
        target_polyform_id: str,
        new_polyform_id: str,
        assembly
    ) -> PlacementResult:
        """
        Execute automated placement workflow:
        1. Evaluate all edge connections
        2. Attempt folding sequence
        3. Handle failures via decay
        4. Update workspace
        """
        start_time = time.time()
        
        # ═════════════════════════════════════════════════════════
        # STEP 1: Connection Evaluation
        # ═════════════════════════════════════════════════════════
        candidates = self.evaluator.evaluate_all_connections(
            target_polyform_id,
            new_polyform_id,
            assembly
        )
        
        if not candidates:
            return PlacementResult(
                success=False,
                fold_sequence=[],
                total_time=time.time() - start_time
            )
        
        # ═════════════════════════════════════════════════════════
        # STEP 2: Automated Folding Sequence
        # ═════════════════════════════════════════════════════════
        attempts, success = self.sequencer.execute_fold_sequence(
            candidates,
            assembly,
            max_attempts=10
        )
        
        if success:
            # Success! Update and return
            total_time = time.time() - start_time
            
            # ═══════════════════════════════════════════════════
            # 3D MODE: Create hinges from successful bonds
            # ═══════════════════════════════════════════════════
            if self._enable_3d_mode and self.hinge_manager is not None:
                self._create_hinges_from_placement(attempts, assembly)
            
            result = PlacementResult(
                success=True,
                fold_sequence=attempts,
                final_polyform_id=target_polyform_id,
                total_time=total_time,
                confidence_score=self._calculate_final_confidence(attempts)
            )
            
            # Optional visual validation (non-blocking)
            try:
                if hasattr(self, '_visual_validation_opts'):
                    from validators import validate_visual_assembly
                    report = validate_visual_assembly(
                        assembly,
                        require_3d_mesh=self._visual_validation_opts.get('require_3d_mesh', False),
                        check_collisions=self._visual_validation_opts.get('check_collisions', False)
                    )
                    if hasattr(self.provenance, 'log_validation'):
                        self.provenance.log_validation(report)
            except Exception:
                pass
        
        # Log successful placement
        self.provenance.log_placement(result)
        self.placement_history.append(result)
        # Invalidate evaluator cache (geometry changed)
        if hasattr(self.evaluator, 'clear_cache'):
            self.evaluator.clear_cache()
        
            # Consider autosaving stable configuration if closed or dense
            try:
                self._save_stable_if_applicable(assembly)
            except Exception:
                pass
            return result
        
        # ═════════════════════════════════════════════════════════
        # STEP 3: Decay & Reformation (Failure Handling)
        # ═════════════════════════════════════════════════════════
        reformed_ids = self.decay.trigger_decay(attempts, assembly)
        
        total_time = time.time() - start_time
        
        result = PlacementResult(
            success=False,
            fold_sequence=attempts,
            decay_triggered=True,
            reformed_polyforms=reformed_ids,
            total_time=total_time,
            confidence_score=0.0
        )
        
        # Log decay event
        self.provenance.log_placement(result)
        self.placement_history.append(result)
        # Invalidate evaluator cache after decay
        if hasattr(self.evaluator, 'clear_cache'):
            self.evaluator.clear_cache()
        # Consider autosaving (decay may yield stable components)
        try:
            self._save_stable_if_applicable(assembly)
        except Exception:
            pass
        
        return result
    
    def _create_hinges_from_placement(self, attempts: List[FoldAttempt], assembly):
        """
        Create hinges in HingeManager from successful fold attempts.
        
        This tracks 3D fold relationships for interactive manipulation.
        
        Args:
            attempts: List of fold attempts (successful ones will be converted to hinges)
            assembly: Assembly object containing the polyforms and bonds
        """
        if not self.hinge_manager:
            return
        
        for attempt in attempts:
            if not attempt.success:
                continue
            
            # Extract bond information from successful attempt
            candidate = attempt.candidate
            bond = {
                'poly1_id': candidate.poly1_id,
                'edge1_idx': candidate.edge1_idx,
                'poly2_id': candidate.poly2_id,
                'edge2_idx': candidate.edge2_idx,
                'fold_angle': attempt.fold_angle if attempt.fold_angle else 0.0
            }
            
            # Add bond as hinge to the HingeManager
            try:
                hinge_idx = self.hinge_manager.add_bond_as_hinge(bond, assembly)
                if hinge_idx is not None and attempt.fold_angle:
                    # Update hinge with fold angle from placement
                    hinge = self.hinge_manager.graph.get_hinge(hinge_idx)
                    if hinge:
                        hinge.fold_angle = attempt.fold_angle
            except Exception as e:
                # Gracefully handle hinge creation failures
                import warnings
                warnings.warn(f"Failed to create hinge: {e}")
    
    def _calculate_final_confidence(self, attempts: List[FoldAttempt]) -> float:
        """Calculate overall confidence of successful placement"""
        if not attempts:
            return 0.0
        
        successful = [a for a in attempts if a.success]
        
        if not successful:
            return 0.0
        
        avg_confidence = sum(a.candidate.confidence for a in successful) / len(successful)
        
        return avg_confidence
    
    def get_placement_stats(self) -> Dict:
        """Get statistics on placement history"""
        total = len(self.placement_history)
        
        if total == 0:
            return {
                'total_placements': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0,
                'decay_rate': 0.0
            }
        
        successful = sum(1 for p in self.placement_history if p.success)
        decayed = sum(1 for p in self.placement_history if p.decay_triggered)
        
        avg_conf = sum(p.confidence_score for p in self.placement_history) / total
        
        return {
            'total_placements': total,
            'success_rate': successful / total,
            'avg_confidence': avg_conf,
            'decay_rate': decayed / total,
            'avg_time': sum(p.total_time for p in self.placement_history) / total
        }

    # -------------------- Stable save helpers --------------------
    def _is_closed(self, assembly) -> bool:
        polys = assembly.get_all_polyforms()
        bonds = assembly.get_bonds()
        if not polys or not bonds:
            return False
        total_edges = sum(p.get('sides', 0) for p in polys)
        bonded_edges = len(bonds) * 2
        return bonded_edges >= total_edges

    def _component_density(self, component: List[Dict[str, Any]], assembly) -> float:
        ids = {p['id'] for p in component}
        total_edges = sum(p.get('sides', 0) for p in component)
        bonded = 0
        for b in assembly.get_bonds():
            if b.get('poly1_id') in ids and b.get('poly2_id') in ids:
                bonded += 2
        return bonded / max(1, total_edges)

    def _signature_from_polys(self, polys: List[Dict[str, Any]]) -> str:
        counts: Dict[int, int] = {}
        for p in polys:
            s = int(p.get('sides', 0))
            if s >= 3:
                counts[s] = counts.get(s, 0) + 1
        parts = [f"{a}x{c}" for a, c in sorted(counts.items())]
        return "S:" + "_".join(parts)

    def _save_stable_if_applicable(self, assembly):
        if not self.stable_library:
            return
        # Compute signature meta
        try:
            meta = {'S_id': self._signature_from_polys(assembly.get_all_polyforms())}
        except Exception:
            meta = {}
        # Save whole assembly if closed
        if self._is_closed(assembly):
            self.stable_library.save_assembly(assembly, name='closed_assembly', meta=meta)
            return
        # Otherwise, save dense components
        try:
            components = self.evaluator.chains.get_connected_components(assembly)
        except Exception:
            components = []
        for comp in components:
            d = self._component_density(comp, assembly)
            if d >= 0.85 and len(comp) >= 3:
                ids = {p['id'] for p in comp}
                polys = comp
                bonds = [b for b in assembly.get_bonds() if b.get('poly1_id') in ids and b.get('poly2_id') in ids]
                try:
                    meta_c = {'S_id': self._signature_from_polys(polys)}
                except Exception:
                    meta_c = {}
                self.stable_library.save_component(polys, bonds, name=f'dense_{len(polys)}', meta=meta_c)




if __name__ == "__main__":
    from managers import (
        RealMemoryManager,
        RealChainManager,
        RealFoldValidator,
        RealWorkspaceManager,
        RealProvenanceTracker
    )
    
    print("╔════════════════════════════════════════════════════════╗")
    print("║   AUTOMATED PLACEMENT ENGINE - TEST MODE              ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    # Create real managers
    memory = RealMemoryManager()
    chains = RealChainManager()
    validator = RealFoldValidator()
    workspace = RealWorkspaceManager()
    provenance = RealProvenanceTracker()
    
    # Create engine components
    evaluator = ConnectionEvaluator(memory, chains)
    sequencer = FoldSequencer(validator, workspace)
    decay_manager = DecayManager(chains, memory, workspace)
    
    # Create main engine
    engine = AutomatedPlacementEngine(
        evaluator,
        sequencer,
        decay_manager,
        workspace,
        provenance
    )
    
    print("\n✓ Automated Placement Engine initialized")
    print("✓ Ready for integration with visualizer")
    print("\nKey capabilities:")
    print("  • Intelligent edge matching and stability scoring")
    print("  • Automated folding sequence execution")
    print("  • Decay and reformation on failures")
    print("  • Provenance tracking and logging")
    print("  • Continuous exploration support")
