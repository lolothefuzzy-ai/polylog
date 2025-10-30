"""
Analyze polyform data structures by generating a small sample and printing a schema-like summary.
"""
import json
from typing import Any, Dict

# Import the minimal generator used in tests (load by path to avoid package import issues)
import importlib.util
from pathlib import Path

tests_path = Path(__file__).resolve().parents[1] / "tests" / "minimal_generator.py"
spec = importlib.util.spec_from_file_location("minimal_generator", str(tests_path))
mg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mg)

RandomPolyformGenerator = mg.RandomPolyformGenerator
GenerationParams = mg.GenerationParams


def summarize(poly: Dict[str, Any]) -> Dict[str, Any]:
    summary = {}
    for k, v in poly.items():
        t = type(v).__name__
        if isinstance(v, (list, tuple)) and len(v) > 0:
            elem_types = {type(x).__name__ for x in v}
            summary[k] = {
                'type': t,
                'len': len(v),
                'elem_types': list(elem_types)[:5]
            }
        else:
            summary[k] = {'type': t, 'value_sample': repr(v)[:200]}
    return summary


def main():
    params = GenerationParams(n=5)
    gen = RandomPolyformGenerator(params=params)
    polyforms = gen.generate_batch()

    print(f"Generated {len(polyforms)} polyforms\n")

    # Print schema-like summary for first polyform
    if polyforms:
        p = polyforms[0]
        schema = summarize(p)
        print(json.dumps(schema, indent=2))

    # Additionally, inspect vertices shape across samples
    verts_info = []
    for p in polyforms:
        v = p.get('vertices', [])
        verts_info.append({'id': p.get('id'), 'sides': p.get('sides', len(v)), 'vertex_len': len(v)})
    print('\nVertex summary for samples:')
    print(json.dumps(verts_info, indent=2))

if __name__ == '__main__':
    main()
