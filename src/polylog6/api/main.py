"""
FastAPI entry point for Tauri sidecar
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

from polylog6.api.tier1_polyhedra import router as tier1_router
from polylog6.api.storage import router as storage_router

app = FastAPI(title="Polyform Backend")

# CORS for Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(tier1_router)
app.include_router(storage_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mapping from numeric polygon IDs to letter symbols
POLYGON_ID_TO_SYMBOL = {
    11: "A",  # triangle
    13: "B",  # square
    3: "C",   # pentagon
    15: "D",  # hexagon
    5: "E",   # heptagon
    17: "F",  # octagon
    7: "G",   # nonagon
    19: "H",  # decagon
    9: "I",   # hendecagon
    20: "J",  # dodecagon
    4: "K",   # 13-gon
    6: "L",   # 14-gon
    8: "M",   # 15-gon
    10: "N",  # 16-gon
    12: "O",  # 17-gon
    14: "P",  # 18-gon
    16: "Q",  # 19-gon
    18: "R",  # 20-gon
}

@app.post("/api/polyform/decode")
async def decode_polyform(request: dict):
    """
    Decode Unicode encoding to geometry data
    """
    encoding = request.get("encoding")
    
    # Load geometry catalog
    catalog_path = Path(__file__).parent.parent.parent.parent.parent / "lib" / "catalogs" / "geometry_catalog.json"
    try:
        with open(catalog_path, "r") as f:
            geometry_catalog = json.load(f)
    except FileNotFoundError:
        # Fallback to basic triangle if catalog not found
        return {
            "lod": {
                "full": {
                    "vertices": [[1.0, 0.0, 0.0], [-0.5, 0.866025, 0.0], [-0.5, -0.866025, 0.0]],
                    "indices": [0, 1, 2],
                    "normals": [[0, 0, 1], [0, 0, 1], [0, 0, 1]]
                },
                "medium": {"vertices": [], "indices": []},
                "bbox": {"min": [-0.5, -0.866025, 0.0], "max": [1.0, 0.866025, 0.0]}
            },
            "folds": [],
            "metadata": {
                "polygon_count": 1,
                "edge_count": 3,
                "compression_ratio": 1.0
            }
        }
    
    # For single character symbols (A, B, C, D...), return the corresponding primitive
    if encoding and len(encoding) == 1 and encoding.isalpha():
        symbol = encoding.upper()
        for primitive_name, primitive_data in geometry_catalog["primitives"].items():
            if primitive_data["symbol"] == symbol:
                return {
                    "lod": {
                        "full": {
                            "vertices": primitive_data["vertices"],
                            "indices": [],  # Will be triangulated on frontend
                            "normals": [[0, 0, 1] for _ in primitive_data["vertices"]]
                        },
                        "medium": {"vertices": [], "indices": []},
                        "bbox": primitive_data["bounding_box"]
                    },
                    "folds": [],
                    "metadata": {
                        "polygon_count": 1,
                        "edge_count": primitive_data["sides"],
                        "compression_ratio": 1.0,
                        "primitive_name": primitive_name,
                        "symbol": symbol
                    }
                }
    
    # For numeric IDs (from tier structure), convert to symbol then return primitive
    if encoding and encoding.isdigit():
        polygon_id = int(encoding)
        if polygon_id in POLYGON_ID_TO_SYMBOL:
            symbol = POLYGON_ID_TO_SYMBOL[polygon_id]
            for primitive_name, primitive_data in geometry_catalog["primitives"].items():
                if primitive_data["symbol"] == symbol:
                    return {
                        "lod": {
                            "full": {
                                "vertices": primitive_data["vertices"],
                                "indices": [],  # Will be triangulated on frontend
                                "normals": [[0, 0, 1] for _ in primitive_data["vertices"]]
                            },
                            "medium": {"vertices": [], "indices": []},
                            "bbox": primitive_data["bounding_box"]
                        },
                        "folds": [],
                        "metadata": {
                            "polygon_count": 1,
                            "edge_count": primitive_data["sides"],
                            "compression_ratio": 1.0,
                            "primitive_name": primitive_name,
                            "symbol": symbol,
                            "polygon_id": polygon_id
                        }
                    }
    
    # Fallback to triangle
    triangle_data = geometry_catalog["primitives"]["triangle"]
    return {
        "lod": {
            "full": {
                "vertices": triangle_data["vertices"],
                "indices": [],  # Will be triangulated on frontend
                "normals": [[0, 0, 1] for _ in triangle_data["vertices"]]
            },
            "medium": {"vertices": [], "indices": []},
            "bbox": triangle_data["bounding_box"]
        },
        "folds": [],
        "metadata": {
            "polygon_count": 1,
            "edge_count": 3,
            "compression_ratio": 1.0,
            "primitive_name": "triangle",
            "symbol": "A"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8008)
