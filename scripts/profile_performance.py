#!/usr/bin/env python3
"""Performance profiling for critical paths."""

import cProfile
import pstats
from Properties.Code.main import main as run_application

def main():
    profiler = cProfile.Profile()
    profiler.enable()
    run_application()  # Call your actual main function
    profiler.disable()
    
    # Save stats
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.dump_stats("performance.prof")
    stats.print_stats()

if __name__ == "__main__":
    main()
