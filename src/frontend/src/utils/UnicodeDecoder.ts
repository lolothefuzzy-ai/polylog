// Geometry definitions ported from Python geometry_catalog.json
interface Primitive {
  sides: number;
  symbol: string;
  vertices: number[][];
  edges: number[][];
  bounding_box: {
    min: number[];
    max: number[];
  };
  s_value: number;
}

interface GeometryLibrary {
  type: string;
  version: string;
  primitives: Record<string, Primitive>;
  polyhedra?: Record<string, any>;
}

// Primitive definitions (simplified subset for MVP)
const PRIMITIVES: Record<string, Primitive> = {
  triangle: {
    sides: 3,
    symbol: "A",
    vertices: [
      [1.0, 0.0, 0.0],
      [-0.5, 0.866025, 0.0],
      [-0.5, -0.866025, 0.0]
    ],
    edges: [[0, 1], [1, 2], [2, 0]],
    bounding_box: {
      min: [-0.5, -0.866025, 0.0],
      max: [1.0, 0.866025, 0.0]
    },
    s_value: 3
  },
  square: {
    sides: 4,
    symbol: "B",
    vertices: [
      [1.0, 0.0, 0.0],
      [0.0, 1.0, 0.0],
      [-1.0, 0.0, 0.0],
      [0.0, -1.0, 0.0]
    ],
    edges: [[0, 1], [1, 2], [2, 3], [3, 0]],
    bounding_box: {
      min: [-1.0, -1.0, 0.0],
      max: [1.0, 1.0, 0.0]
    },
    s_value: 4
  },
  pentagon: {
    sides: 5,
    symbol: "C",
    vertices: [
      [1.0, 0.0, 0.0],
      [0.309017, 0.951057, 0.0],
      [-0.809017, 0.587785, 0.0],
      [-0.809017, -0.587785, 0.0],
      [0.309017, -0.951057, 0.0]
    ],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
    bounding_box: {
      min: [-0.809017, -0.951057, 0.0],
      max: [1.0, 0.951057, 0.0]
    },
    s_value: 5
  },
  hexagon: {
    sides: 6,
    symbol: "D",
    vertices: [
      [1.0, 0.0, 0.0],
      [0.5, 0.866025, 0.0],
      [-0.5, 0.866025, 0.0],
      [-1.0, 0.0, 0.0],
      [-0.5, -0.866025, 0.0],
      [0.5, -0.866025, 0.0]
    ],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]],
    bounding_box: {
      min: [-1.0, -0.866025, 0.0],
      max: [1.0, 0.866025, 0.0]
    },
    s_value: 6
  }
};

export interface DecodedGeometry {
  vertices: Float32Array;
  indices: Uint32Array;
  normals: Float32Array;
  boundingBox: {
    min: number[];
    max: number[];
  };
}

export class UnicodeDecoder {
  private primitives: Record<string, Primitive>;
  private backendUrl: string;

  constructor() {
    this.primitives = PRIMITIVES;
    this.backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  /**
   * Decode a Unicode symbol or simple encoding to geometry
   * For MVP, handles single primitive symbols (A, B, C, D)
   */
  async decode(encoding: string): Promise<DecodedGeometry> {
    try {
      // Try to get geometry from backend API
      const response = await fetch(`${this.backendUrl}/api/polyform/decode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ encoding }),
      });

      if (response.ok) {
        const data = await response.json();
        return this.convertBackendGeometry(data);
      }
    } catch (error) {
      console.warn('Backend API unavailable, using fallback:', error);
    }

    // Fallback to local decoding
    return this.decodeLocal(encoding);
  }

  private decodeLocal(encoding: string): DecodedGeometry {
    // Handle single symbol (primitive)
    if (encoding.length === 1) {
      const symbol = encoding.toUpperCase();
      for (const primitive of Object.values(this.primitives)) {
        if (primitive.symbol === symbol) {
          return this.convertPrimitive(primitive);
        }
      }
    }

    // TODO: Handle more complex encodings like "Ω₁", "A11", etc.
    // For now, fallback to triangle
    console.warn(`Unknown encoding: ${encoding}, falling back to triangle`);
    return this.convertPrimitive(this.primitives.triangle);
  }

  private convertBackendGeometry(data: any): DecodedGeometry {
    const geometry = data.lod.full;
    
    // Convert vertices to Float32Array
    const vertices = new Float32Array(geometry.vertices.length * 3);
    geometry.vertices.forEach((vertex: number[], i: number) => {
      vertices[i * 3] = vertex[0];
      vertices[i * 3 + 1] = vertex[1];
      vertices[i * 3 + 2] = vertex[2];
    });

    // Convert indices (backend might return empty indices, so triangulate)
    let indices: Uint32Array;
    if (geometry.indices && geometry.indices.length > 0) {
      indices = new Uint32Array(geometry.indices);
    } else {
      // Triangulate the polygon
      indices = this.triangulatePolygon(geometry.vertices, []);
    }

    // Convert normals to Float32Array
    const normals = new Float32Array(geometry.normals.length * 3);
    geometry.normals.forEach((normal: number[], i: number) => {
      normals[i * 3] = normal[0];
      normals[i * 3 + 1] = normal[1];
      normals[i * 3 + 2] = normal[2];
    });

    return {
      vertices,
      indices,
      normals,
      boundingBox: data.lod.bbox
    };
  }

  private convertPrimitive(primitive: Primitive): DecodedGeometry {
    // Convert vertices to Float32Array
    const vertices = new Float32Array(primitive.vertices.length * 3);
    primitive.vertices.forEach((vertex, i) => {
      vertices[i * 3] = vertex[0];
      vertices[i * 3 + 1] = vertex[1];
      vertices[i * 3 + 2] = vertex[2];
    });

    // Convert edges to triangle indices (triangulate the polygon)
    const indices = this.triangulatePolygon(primitive.vertices, primitive.edges);

    // Calculate normals (flat shading for now)
    const normals = new Float32Array(vertices.length);
    for (let i = 0; i < normals.length; i += 3) {
      normals[i] = 0;
      normals[i + 1] = 0;
      normals[i + 2] = 1; // Face upward
    }

    return {
      vertices,
      indices,
      normals,
      boundingBox: primitive.bounding_box
    };
  }

  private triangulatePolygon(vertices: number[][], edges: number[][]): Uint32Array {
    // Simple fan triangulation from first vertex
    const indices: number[] = [];
    const n = vertices.length;
    
    if (n < 3) {
      throw new Error("Polygon must have at least 3 vertices");
    }

    // Triangulate as a fan from vertex 0
    for (let i = 1; i < n - 1; i++) {
      indices.push(0, i, i + 1);
    }

    return new Uint32Array(indices);
  }

  /**
   * Get available primitive symbols
   */
  getAvailableSymbols(): string[] {
    return Object.values(this.primitives).map(p => p.symbol);
  }

  /**
   * Get primitive info for a symbol
   */
  getPrimitiveInfo(symbol: string): Primitive | null {
    const upperSymbol = symbol.toUpperCase();
    for (const primitive of Object.values(this.primitives)) {
      if (primitive.symbol === upperSymbol) {
        return primitive;
      }
    }
    return null;
  }
}
