"""Benchmark simulation performance."""
import time
from polylog6.simulation.runtime import SimulationRuntime


def main():
    runtime = SimulationRuntime()
    
    # Warmup
    for _ in range(100):
        runtime.step()
    
    # Benchmark
    start_time = time.perf_counter()
    for _ in range(1000):
        runtime.step()
    duration = time.perf_counter() - start_time
    
    print(f"Simulation benchmark: 1000 steps in {duration:.3f}s ({duration/1000*1000:.3f}ms/step)")


if __name__ == "__main__":
    main()
