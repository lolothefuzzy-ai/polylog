import math
import time
from typing import Dict, List, Tuple, Any, Optional

# Canonical, agent-implementable combinatorial estimator for N
# Follows the spec provided by user exactly, computing in log-space and returning
# the full canonical feature set. Results are cached by (S_id, lnT, ln_symmetry).

CacheKey = Tuple[str, float, float]
_cache: Dict[CacheKey, Dict[str, Any]] = {}


def _canonicalize_types(types: List[Any]) -> List[Tuple[int, int]]:
    """Normalize input types into sorted list of (a_j, c_j) tuples."""
    norm: List[Tuple[int, int]] = []
    for t in types:
        if isinstance(t, dict):
            a = int(t.get("a") or t.get("sides") or t.get("a_j"))
            c = int(t.get("c") or t.get("count") or t.get("c_j"))
        else:
            a, c = int(t[0]), int(t[1])
        if a < 3 or c < 1:
            raise ValueError("a_j must be >=3 and c_j must be >=1")
        norm.append((a, c))
    # sort ascending by a_j
    norm.sort(key=lambda x: x[0])
    return norm


def _build_sid(types_sorted: List[Tuple[int, int]]) -> str:
    parts = [f"{a}x{c}" for a, c in types_sorted]
    return "S:" + "_".join(parts)


def _ln_factorial(n: int) -> float:
    # ln(n!) = lnGamma(n+1)
    if n < 0:
        raise ValueError("n must be >= 0")
    return math.lgamma(n + 1.0)


def _safe_int_factorial(n: int) -> int:
    # exact factorial using Python big-int
    return math.factorial(n)


def canonical_estimate(
    T: float,
    types: List[Any],
    symmetry_factor: float = 1.0,
    symmetry_notes: str = "",
    agent_id: str = "auto",
    timestamp: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute canonical estimator for N with full feature set and caching.
    Inputs:
      - T: positive real
      - types: list of pairs or dicts mapping to (a_j, c_j)
      - symmetry_factor: (0,1]
      - symmetry_notes: provenance string for symmetry
    Returns dict with fields specified in the spec.
    """
    if T <= 0:
        raise ValueError("T must be positive")
    if not (0 < symmetry_factor <= 1.0):
        raise ValueError("symmetry_factor must be in (0,1]")

    types_sorted = _canonicalize_types(types)
    S_id = _build_sid(types_sorted)

    # Derived values
    n = sum(c for _, c in types_sorted)
    if n == 0:
        raise ValueError("n must be >= 1")

    # log components
    lnT = math.log(T)
    ln_symmetry = 0.0 if symmetry_factor == 1.0 else math.log(symmetry_factor)

    # sum_cj_ln_aj and s_product (big-int) in parallel
    sum_cj_ln_aj = 0.0
    s_product_int = 1
    sum_a_c = 0
    for a, c in types_sorted:
        sum_cj_ln_aj += c * math.log(a)
        s_product_int *= pow(a, c)
        sum_a_c += a * c

    s_eff_geo = math.exp(sum_cj_ln_aj / n)
    s_eff_arith = sum_a_c / n

    # factorial logs
    ln_n_factorial = _ln_factorial(n)
    sum_ln_cj_fact = sum(_ln_factorial(c) for _, c in types_sorted)

    # logN
    logN = lnT + ln_n_factorial - sum_ln_cj_fact + sum_cj_ln_aj + ln_symmetry

    # permutation factor exact if feasible
    permutation_factor: Optional[int] = None
    try:
        num = _safe_int_factorial(n)
        denom = 1
        for _, c in types_sorted:
            denom *= _safe_int_factorial(c)
        permutation_factor = num // denom
    except Exception:
        permutation_factor = None  # too large or failed; rely on logs

    # Optional diversity index (Shannon entropy)
    diversity_index = 0.0
    for _, c in types_sorted:
        p = c / n
        diversity_index -= p * math.log(p)

    # Optional N (may overflow); compute only if small log
    N_value: Optional[float] = None
    if logN < 709.0:  # exp(709) ~ 8.2e307 near double max
        N_value = math.exp(logN)

    ts = timestamp if timestamp is not None else time.time()

    result: Dict[str, Any] = {
        "S_id": S_id,
        "n": n,
        "types": [{"a_j": a, "c_j": c} for a, c in types_sorted],
        "s_product": s_product_int,  # big-int exact
        "s_eff_geo": s_eff_geo,
        "s_eff_arith": s_eff_arith,
        "permutation_factor": permutation_factor,
        "log_components": {
            "lnT": lnT,
            "ln_n_factorial": ln_n_factorial,
            "sum_ln_cj_fact": sum_ln_cj_fact,
            "sum_cj_ln_aj": sum_cj_ln_aj,
            "ln_symmetry": ln_symmetry,
        },
        "logN": logN,
        "N": N_value,
        "diversity_index": diversity_index,
        "provenance": {
            "agent_id": agent_id,
            "timestamp": ts,
            "symmetry_notes": symmetry_notes,
            "validation_status": "canonical-estimate",
        },
    }

    key: CacheKey = (S_id, lnT, ln_symmetry)
    _cache[key] = result

    return result


def get_cached(S_id: str, lnT: float, ln_symmetry: float) -> Optional[Dict[str, Any]]:
    return _cache.get((S_id, lnT, ln_symmetry))
