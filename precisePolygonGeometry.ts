import * as BABYLON from '@babylonjs/core';
import earcut from 'earcut';

export interface PolygonEdge {
  start: BABYLON.Vector3;
  end: BABYLON.Vector3;
  midpoint: BABYLON.Vector3;
  normal: BABYLON.Vector3;  // Outward-facing normal
  length: number;
}

export interface PolygonGeometryData {
  vertices: BABYLON.Vector3[];
  edges: PolygonEdge[];
  center: BABYLON.Vector3;
  area: number;
}

/**
 * Create a regular polygon with EXACT unit edge length (1.0)
 * All polygons lie flat on XZ plane (y=0) for 2D base
 */
export function createPrecisePolygon(sides: number): PolygonGeometryData {
  // Calculate circumradius for unit edge length
  // For regular polygon: edge_length = 2 * R * sin(π/n)
  // Therefore: R = edge_length / (2 * sin(π/n))
  const edgeLength = 1.0;  // Unit edge length
  const circumradius = edgeLength / (2 * Math.sin(Math.PI / sides));
  
  // Generate vertices on XZ plane (y=0)
  const vertices: BABYLON.Vector3[] = [];
  for (let i = 0; i < sides; i++) {
    const angle = (i * 2 * Math.PI) / sides;
    const x = circumradius * Math.cos(angle);
    const z = circumradius * Math.sin(angle);
    vertices.push(new BABYLON.Vector3(x, 0, z));  // y=0 for 2D base plane
  }
  
  // Calculate edges with midpoints and normals
  const edges: PolygonEdge[] = [];
  for (let i = 0; i < sides; i++) {
    const start = vertices[i];
    const end = vertices[(i + 1) % sides];
    const midpoint = BABYLON.Vector3.Center(start, end);
    
    // Calculate outward-facing normal (perpendicular to edge, pointing away from center)
    const edgeVector = end.subtract(start);
    const normal = new BABYLON.Vector3(-edgeVector.z, 0, edgeVector.x).normalize();
    
    // Verify edge length is exactly 1.0
    const length = BABYLON.Vector3.Distance(start, end);
    
    edges.push({
      start,
      end,
      midpoint,
      normal,
      length
    });
  }
  
  // Calculate center and area
  const center = BABYLON.Vector3.Zero();
  vertices.forEach(v => center.addInPlace(v));
  center.scaleInPlace(1 / sides);
  
  // Area of regular polygon: (n * s²) / (4 * tan(π/n))
  const area = (sides * edgeLength * edgeLength) / (4 * Math.tan(Math.PI / sides));
  
  return {
    vertices,
    edges,
    center,
    area
  };
}

/**
 * Create Babylon.js mesh from polygon geometry data
 */
export function createPolygonMesh(
  sides: number,
  scene: BABYLON.Scene,
  name?: string
): BABYLON.Mesh {
  const geometryData = createPrecisePolygon(sides);
  
  // Flatten vertices for earcut (2D coordinates only, XZ plane)
  const flatVertices: number[] = [];
  geometryData.vertices.forEach(v => {
    flatVertices.push(v.x, v.z);  // Only X and Z (2D)
  });
  
  // Triangulate using earcut
  const indices = earcut(flatVertices);
  
  // Create 3D vertex positions (add Y coordinate back)
  const positions: number[] = [];
  geometryData.vertices.forEach(v => {
    positions.push(v.x, v.y, v.z);
  });
  
  // Create custom mesh
  const mesh = new BABYLON.Mesh(name || `polygon-${sides}`, scene);
  const vertexData = new BABYLON.VertexData();
  
  vertexData.positions = positions;
  vertexData.indices = indices;
  
  // Initialize normals array
  const normals: number[] = [];
  
  // Calculate normals (all pointing up since polygon is flat on XZ plane)
  BABYLON.VertexData.ComputeNormals(positions, indices, normals);
  vertexData.normals = normals;
  
  vertexData.applyToMesh(mesh);
  
  // Create material with backface culling disabled for visibility
  const material = new BABYLON.StandardMaterial(`polygon-mat-${sides}`, scene);
  material.diffuseColor = new BABYLON.Color3(0.3, 0.6, 1.0);  // Blue
  material.specularColor = new BABYLON.Color3(0.2, 0.2, 0.2);
  material.backFaceCulling = false;  // Show both sides
  material.twoSidedLighting = true;  // Light both sides
  mesh.material = material;
  
  // Store geometry data as metadata for snap detection
  mesh.metadata = {
    geometryData,
    polygonSides: sides,
    edgeLength: 1.0
  };
  
  return mesh;
}

/**
 * Get edge data from a polygon mesh
 */
export function getPolygonEdges(mesh: BABYLON.Mesh): PolygonEdge[] | null {
  if (!mesh.metadata || !mesh.metadata.geometryData) {
    return null;
  }
  return mesh.metadata.geometryData.edges;
}

/**
 * Find the nearest edge to a given point (for snap detection)
 */
export function findNearestEdge(
  point: BABYLON.Vector3,
  edges: PolygonEdge[],
  maxDistance: number = 0.5
): { edge: PolygonEdge; distance: number } | null {
  let nearestEdge: PolygonEdge | null = null;
  let minDistance = maxDistance;
  
  for (const edge of edges) {
    const distance = BABYLON.Vector3.Distance(point, edge.midpoint);
    if (distance < minDistance) {
      minDistance = distance;
      nearestEdge = edge;
    }
  }
  
  if (nearestEdge) {
    return { edge: nearestEdge, distance: minDistance };
  }
  
  return null;
}
