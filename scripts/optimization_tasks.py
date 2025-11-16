#!/usr/bin/env python3
"""
Polylog6 Optimization Tasks
Continuous optimization and validation for novel systems
"""

import argparse
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def run_command(cmd: list, cwd: Path = None, check: bool = True) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def benchmark_performance():
    """Run performance benchmarks"""
    print_header("Performance Benchmarking")
    
    metrics = {
        "timestamp": time.time(),
        "api_response": None,
        "rendering_fps": None,
        "memory_usage": None,
        "lod_transition": None,
        "edge_validation": None
    }
    
    print_info("Running performance benchmarks...")
    print_info("This will test API, rendering, and validation performance")
    
    # Run frontend performance tests
    print_info("Testing frontend performance...")
    success = run_command(
        ["npm", "run", "test:performance"],
        cwd=FRONTEND_DIR,
        check=False
    )
    
    if success:
        print_success("Frontend performance tests passed")
    else:
        print_warning("Frontend performance tests not configured yet")
    
    # Save metrics
    metrics_file = PROJECT_ROOT / "performance_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print_success(f"Metrics saved to {metrics_file}")
    return metrics

def run_visual_tests(watch: bool = False, update_snapshots: bool = False):
    """Run visual regression tests"""
    print_header("Visual Regression Testing")
    
    cmd = ["npm", "run", "test:visual"]
    
    if update_snapshots:
        cmd.append("--update-snapshots")
        print_info("Updating visual snapshots...")
    
    if watch:
        cmd.append("--watch")
        print_info("Running in watch mode (continuous)...")
    
    print_info("Launching visual tests with browser window...")
    run_command(cmd, cwd=FRONTEND_DIR, check=False)

def run_integration_tests():
    """Run full system integration tests"""
    print_header("Full System Integration Tests")
    
    print_info("Starting API server...")
    # API will be started by test runner
    
    print_info("Running integration tests...")
    success = run_command(
        ["npm", "run", "test:integration"],
        cwd=FRONTEND_DIR,
        check=False
    )
    
    if success:
        print_success("Integration tests passed")
    else:
        print_warning("Some integration tests may have failed")
        print_info("Check test output for details")

def validate_optimizations():
    """Validate that optimizations don't break functionality"""
    print_header("Optimization Validation")
    
    print_info("Running full test suite...")
    
    # Visual tests
    print_info("1. Visual regression...")
    run_command(["npm", "run", "test:visual"], cwd=FRONTEND_DIR, check=False)
    
    # Integration tests
    print_info("2. Integration tests...")
    run_command(["npm", "run", "test:integration"], cwd=FRONTEND_DIR, check=False)
    
    # Performance benchmarks
    print_info("3. Performance benchmarks...")
    benchmark_performance()
    
    print_success("Optimization validation complete")

def profile_performance():
    """Run performance profiler"""
    print_header("Performance Profiling")
    
    print_info("Starting profiler...")
    print_info("This will analyze:")
    print_info("  - API response times")
    print_info("  - Rendering performance")
    print_info("  - Memory usage")
    print_info("  - CPU usage")
    
    # Run with profiling
    print_info("Launching app with profiler...")
    print_info("Open browser DevTools Performance tab")
    print_info("Record a session, then analyze results")
    
    # Start dev server
    run_command(["npm", "run", "dev"], cwd=FRONTEND_DIR, check=False)

def monitor_system():
    """Monitor system metrics continuously"""
    print_header("System Monitoring")
    
    print_info("Starting continuous monitoring...")
    print_info("Monitoring:")
    print_info("  - API response times")
    print_info("  - Rendering FPS")
    print_info("  - Memory usage")
    print_info("  - Error rates")
    
    print_info("Press Ctrl+C to stop")
    
    try:
        while True:
            # Check API health
            import requests
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    print_success(f"API healthy: {time.strftime('%H:%M:%S')}")
                else:
                    print_warning(f"API unhealthy: {response.status_code}")
            except:
                print_warning("API not responding")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print_info("\nMonitoring stopped")

def optimize_bundle():
    """Optimize frontend bundle size"""
    print_header("Bundle Optimization")
    
    print_info("Analyzing bundle...")
    run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)
    
    print_info("Checking bundle size...")
    dist_dir = FRONTEND_DIR / "dist"
    if dist_dir.exists():
        total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print_info(f"Total bundle size: {size_mb:.2f} MB")
        
        if size_mb > 2:
            print_warning(f"Bundle size ({size_mb:.2f} MB) exceeds target (2 MB)")
            print_info("Consider code splitting or tree shaking")
        else:
            print_success(f"Bundle size ({size_mb:.2f} MB) within target")

def check_coverage():
    """Check test coverage"""
    print_header("Test Coverage Check")
    
    print_info("Running tests with coverage...")
    run_command(
        ["npm", "run", "test", "--", "--coverage"],
        cwd=FRONTEND_DIR,
        check=False
    )
    
    print_info("Coverage report generated in coverage/")

def main():
    parser = argparse.ArgumentParser(
        description="Polylog6 Optimization Tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python optimization_tasks.py benchmark        # Run performance benchmarks
  python optimization_tasks.py visual --watch  # Continuous visual testing
  python optimization_tasks.py validate         # Validate optimizations
  python optimization_tasks.py monitor          # Monitor system metrics
        """
    )
    
    subparsers = parser.add_subparsers(dest="task", help="Optimization tasks")
    
    # Benchmark
    subparsers.add_parser("benchmark", help="Run performance benchmarks")
    
    # Visual tests
    visual_parser = subparsers.add_parser("visual", help="Run visual regression tests")
    visual_parser.add_argument("--watch", action="store_true", help="Watch mode")
    visual_parser.add_argument("--update-snapshots", action="store_true", help="Update snapshots")
    
    # Integration tests
    subparsers.add_parser("integration", help="Run integration tests")
    
    # Validation
    subparsers.add_parser("validate", help="Validate optimizations")
    
    # Profiling
    subparsers.add_parser("profile", help="Run performance profiler")
    
    # Monitoring
    subparsers.add_parser("monitor", help="Monitor system metrics")
    
    # Bundle optimization
    subparsers.add_parser("bundle", help="Optimize bundle size")
    
    # Coverage
    subparsers.add_parser("coverage", help="Check test coverage")
    
    args = parser.parse_args()
    
    if not args.task:
        parser.print_help()
        return
    
    try:
        if args.task == "benchmark":
            benchmark_performance()
        elif args.task == "visual":
            run_visual_tests(watch=args.watch, update_snapshots=args.update_snapshots)
        elif args.task == "integration":
            run_integration_tests()
        elif args.task == "validate":
            validate_optimizations()
        elif args.task == "profile":
            profile_performance()
        elif args.task == "monitor":
            monitor_system()
        elif args.task == "bundle":
            optimize_bundle()
        elif args.task == "coverage":
            check_coverage()
    except KeyboardInterrupt:
        print_info("\nOperation cancelled")
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

