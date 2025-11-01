import math
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class ConvergenceTracker:
    """
    Tracks T estimation convergence with statistical bounds and confidence intervals.
    
    Uses the expanded canonical estimator form:
        logN = lnT + ln(n!) - Σln(c_j!) + Σ(c_j * ln(a_j)) + ln(symmetry)
    
    Tracks:
    - T value history and derived bounds
    - logN convergence with variance
    - Confidence intervals (95%)
    - Convergence quality metrics
    """
    
    def __init__(self, window_size: int = 50, confidence_level: float = 0.95):
        """
        Args:
            window_size: Number of recent samples for rolling statistics
            confidence_level: Confidence level for intervals (default 95%)
        """
        self.window_size = window_size
        self.confidence_level = confidence_level
        
        # History
        self.T_history: List[float] = []
        self.logN_history: List[float] = []
        self.n_history: List[int] = []
        self.S_id_history: List[str] = []
        self.timestamp_history: List[float] = []
        
        # Rolling window for recent statistics
        self.recent_T = deque(maxlen=window_size)
        self.recent_logN = deque(maxlen=window_size)
        
        # Convergence state
        self.is_converged = False
        self.convergence_threshold = 0.05  # 5% relative change
        
    def add_sample(self, estimate: Dict[str, Any], T_value: float):
        """
        Add a new estimation sample.
        
        Args:
            estimate: Result from canonical_estimate()
            T_value: The T value used for estimation
        """
        logN = float(estimate['logN'])
        n = int(estimate['n'])
        S_id = str(estimate['S_id'])
        timestamp = float(estimate['provenance']['timestamp'])
        
        # Add to full history
        self.T_history.append(T_value)
        self.logN_history.append(logN)
        self.n_history.append(n)
        self.S_id_history.append(S_id)
        self.timestamp_history.append(timestamp)
        
        # Update rolling window
        self.recent_T.append(T_value)
        self.recent_logN.append(logN)
        
        # Check convergence
        self._update_convergence_state()
    
    def _update_convergence_state(self):
        """Update convergence status based on recent variance."""
        if len(self.recent_logN) < 10:
            self.is_converged = False
            return
        
        # Check relative change in recent window
        recent = list(self.recent_logN)
        mean_val = np.mean(recent)
        std_val = np.std(recent)
        
        if mean_val != 0:
            relative_std = abs(std_val / mean_val)
            self.is_converged = relative_std < self.convergence_threshold
        else:
            self.is_converged = False
    
    def get_current_statistics(self) -> Dict[str, Any]:
        """
        Get current statistical summary.
        
        Returns dict with:
            - mean_T, std_T, T_bounds (lower, upper)
            - mean_logN, std_logN, logN_bounds
            - confidence intervals
            - convergence metrics
        """
        if not self.T_history:
            return {
                'sample_count': 0,
                'converged': False,
            }
        
        # Use recent window for statistics
        recent_T_arr = np.array(list(self.recent_T))
        recent_logN_arr = np.array(list(self.recent_logN))
        
        # Compute statistics
        mean_T = float(np.mean(recent_T_arr))
        std_T = float(np.std(recent_T_arr))
        mean_logN = float(np.mean(recent_logN_arr))
        std_logN = float(np.std(recent_logN_arr))
        
        # Confidence intervals (t-distribution for small samples)
        n_samples = len(recent_T_arr)
        if n_samples > 1:
            # Use 1.96 for 95% CI (approximate for large n)
            z_score = 1.96
            if n_samples < 30:
                # More conservative for small samples
                z_score = 2.0 + (30 - n_samples) * 0.05
            
            T_ci_width = z_score * std_T / math.sqrt(n_samples)
            logN_ci_width = z_score * std_logN / math.sqrt(n_samples)
            
            T_bounds = (mean_T - T_ci_width, mean_T + T_ci_width)
            logN_bounds = (mean_logN - logN_ci_width, mean_logN + logN_ci_width)
        else:
            T_bounds = (mean_T, mean_T)
            logN_bounds = (mean_logN, mean_logN)
        
        # Convergence quality score (0-1, based on relative variance)
        if mean_logN != 0:
            relative_var = (std_logN / abs(mean_logN)) ** 2
            convergence_score = max(0.0, 1.0 - relative_var / 0.01)  # 1% variance = 0 score
        else:
            convergence_score = 0.0
        
        return {
            'sample_count': len(self.T_history),
            'window_size': len(self.recent_T),
            
            # T statistics
            'mean_T': mean_T,
            'std_T': std_T,
            'T_bounds': T_bounds,
            'T_range': (float(np.min(recent_T_arr)), float(np.max(recent_T_arr))),
            
            # logN statistics
            'mean_logN': mean_logN,
            'std_logN': std_logN,
            'logN_bounds': logN_bounds,
            'logN_range': (float(np.min(recent_logN_arr)), float(np.max(recent_logN_arr))),
            
            # Convergence metrics
            'converged': self.is_converged,
            'convergence_score': convergence_score,
            'relative_std': std_logN / abs(mean_logN) if mean_logN != 0 else float('inf'),
        }
    
    def get_smoothed_history(self, smoothing_window: int = 5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get smoothed logN history with confidence bands.
        
        Args:
            smoothing_window: Window size for moving average
            
        Returns:
            (indices, smoothed_values, confidence_bands)
            where confidence_bands is shape (2, n) for upper/lower bounds
        """
        if len(self.logN_history) < 2:
            empty = np.array([])
            return empty, empty, np.array([[], []])
        
        indices = np.arange(len(self.logN_history))
        values = np.array(self.logN_history)
        
        # Moving average
        if smoothing_window > 1 and len(values) >= smoothing_window:
            kernel = np.ones(smoothing_window) / smoothing_window
            smoothed = np.convolve(values, kernel, mode='same')
            
            # Moving std for confidence bands
            moving_std = np.array([
                np.std(values[max(0, i-smoothing_window//2):min(len(values), i+smoothing_window//2+1)])
                for i in range(len(values))
            ])
            
            # 95% confidence bands
            z_score = 1.96
            upper = smoothed + z_score * moving_std
            lower = smoothed - z_score * moving_std
        else:
            smoothed = values
            # Simple global std
            std_val = np.std(values)
            upper = smoothed + std_val
            lower = smoothed - std_val
        
        confidence_bands = np.array([lower, upper])
        
        return indices, smoothed, confidence_bands
    
    def estimate_N_bounds(self, current_estimate: Dict[str, Any], T_lower: Optional[float] = None, 
                         T_upper: Optional[float] = None) -> Dict[str, float]:
        """
        Estimate N value bounds given T confidence interval.
        
        Uses: N = exp(logN) where logN = lnT + ln(n!) - Σln(c_j!) + Σ(c_j*ln(a_j)) + ln(sym)
        
        Args:
            current_estimate: Latest canonical estimate
            T_lower, T_upper: T confidence bounds (if None, use current statistics)
            
        Returns:
            Dict with N_lower, N_mean, N_upper (if computable)
        """
        if T_lower is None or T_upper is None:
            stats = self.get_current_statistics()
            if stats['sample_count'] == 0:
                return {}
            T_lower, T_upper = stats['T_bounds']
        
        # Extract log components from estimate
        log_comp = current_estimate['log_components']
        lnT_current = log_comp['lnT']
        logN_current = float(current_estimate['logN'])
        
        # Compute logN bounds by substituting T bounds
        # logN = lnT + constant_terms
        constant_terms = logN_current - lnT_current
        
        logN_lower = math.log(T_lower) + constant_terms
        logN_upper = math.log(T_upper) + constant_terms
        
        result = {
            'logN_lower': logN_lower,
            'logN_mean': logN_current,
            'logN_upper': logN_upper,
        }
        
        # Try to compute N if values aren't too large
        max_safe_logN = 709.0  # exp(709) near double max
        
        if logN_lower < max_safe_logN:
            result['N_lower'] = math.exp(logN_lower)
        if logN_current < max_safe_logN:
            result['N_mean'] = math.exp(logN_current)
        if logN_upper < max_safe_logN:
            result['N_upper'] = math.exp(logN_upper)
        
        return result
    
    def get_convergence_report(self) -> str:
        """Generate human-readable convergence report."""
        stats = self.get_current_statistics()
        
        if stats['sample_count'] == 0:
            return "No samples recorded"
        
        lines = [
            f"Convergence Analysis ({stats['sample_count']} samples, window={stats['window_size']})",
            f"",
            f"T estimation:",
            f"  Mean: {stats['mean_T']:.4f}",
            f"  Std:  {stats['std_T']:.4f}",
            f"  95% CI: [{stats['T_bounds'][0]:.4f}, {stats['T_bounds'][1]:.4f}]",
            f"  Range: [{stats['T_range'][0]:.4f}, {stats['T_range'][1]:.4f}]",
            f"",
            f"logN estimation:",
            f"  Mean: {stats['mean_logN']:.4f}",
            f"  Std:  {stats['std_logN']:.4f}",
            f"  95% CI: [{stats['logN_bounds'][0]:.4f}, {stats['logN_bounds'][1]:.4f}]",
            f"  Range: [{stats['logN_range'][0]:.4f}, {stats['logN_range'][1]:.4f}]",
            f"",
            f"Convergence:",
            f"  Status: {'✓ CONVERGED' if stats['converged'] else '⋯ converging'}",
            f"  Score: {stats['convergence_score']:.2%}",
            f"  Relative std: {stats['relative_std']:.4f}",
        ]
        
        return "\n".join(lines)
    
    def reset(self):
        """Clear all history."""
        self.T_history.clear()
        self.logN_history.clear()
        self.n_history.clear()
        self.S_id_history.clear()
        self.timestamp_history.clear()
        self.recent_T.clear()
        self.recent_logN.clear()
        self.is_converged = False
