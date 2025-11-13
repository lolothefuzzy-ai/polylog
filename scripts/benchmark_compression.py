"""Benchmark Unicode compression performance."""
import time
import tracemalloc
from polylog6.storage.polyform_storage import PolyformStorage
from polylog6.storage.encoder import TieredUnicodeEncoder


def generate_data(n: int) -> list[tuple[str, dict]]:
    """Generate test data."""
    return [
        (f"polyform-{i}", {"vertices": [[i, i, i]], "faces": [[0, 1, 2]]})
        for i in range(n)
    ]


def benchmark(n: int) -> dict:
    """Run benchmark for N polyforms."""
    data = generate_data(n)
    storage = PolyformStorage()
    
    # Time encoding
    start_time = time.perf_counter()
    for polyform_id, poly_data in data:
        storage.add(polyform_id, poly_data, frequency=1000)
    encode_time = time.perf_counter() - start_time
    
    # Memory usage
    tracemalloc.start()
    for polyform_id, poly_data in data:
        storage.add(polyform_id, poly_data, frequency=1000)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "n": n,
        "encode_time": encode_time,
        "memory_peak": peak / 1024,  # KB
    }


def main():
    """Run benchmarks across multiple scales."""
    results = []
    for n in [100, 10000, 100000]:
        print(f"Benchmarking n={n}...")
        results.append(benchmark(n))
    
    # Generate report
    report = "# Compression Benchmark Report\n\n"
    report += "| Scale | Encode Time (s) | Peak Memory (KB) |\n"
    report += "|-------|-----------------|------------------|\n"
    for res in results:
        report += f"| {res['n']} | {res['encode_time']:.4f} | {res['memory_peak']:.2f} |\n"
    
    with open("reports/compression_benchmark.md", "w") as f:
        f.write(report)
    print("Report saved to reports/compression_benchmark.md")


if __name__ == "__main__":
    main()
