/**
 * Unified Geometry Utilities
 * Single source of truth for all geometry calculations
 * Ensures consistency across workspace, GPU, and interaction systems
 */

import * as BABYLON from '@babylonjs/core';

/**
 * Unit edge length constant
 */
export const UNIT_EDGE_LENGTH = 1.0;

/**
 * Calculate circumradius for regular polygon with unit edge length
 * Formula: R = edge_length / (2 * sin(π/n))
 * 
 * @param {number} sides - Number of sides (3-20)
 * @returns {number} Circumradius
 */
export function calculateCircumradius(sides) {
  if (sides < 3 || sides > 20) {
    throw new Error(`Invalid number of sides: ${sides}. Must be 3-20.`);
  }
  return UNIT_EDGE_LENGTH / (2 * Math.sin(Math.PI / sides));
}

/**
 * Calculate internal angle for regular polygon
 * Formula: internal_angle = (n-2) * π / n
 * 
 * @param {number} sides - Number of sides
 * @returns {number} Internal angle in radians
 */
export function calculateInternalAngle(sides) {
  if (sides < 3) {
    throw new Error(`Invalid number of sides: ${sides}. Must be >= 3.`);
  }
  return ((sides - 2) * Math.PI) / sides;
}

/**
 * Calculate external angle for regular polygon
 * Formula: external_angle = 2π / n
 * 
 * @param {number} sides - Number of sides
 * @returns {number} External angle in radians
 */
export function calculateExternalAngle(sides) {
  if (sides < 3) {
    throw new Error(`Invalid number of sides: ${sides}. Must be >= 3.`);
  }
  return (2 * Math.PI) / sides;
}

/**
 * Generate vertices for regular polygon with unit edge length
 * All vertices lie on XZ plane (y=0) initially
 * Tries to use backend geometry first, falls back to local calculation
 * 
 * @param {number} sides - Number of sides (3-20)
 * @param {BABYLON.Vector3} center - Center position (default: origin)
 * @param {number} rotation - Rotation angle around Y axis (default: 0)
 * @param {boolean} useBackend - Whether to try backend first (default: true)
 * @returns {Promise<BABYLON.Vector3[]>} Array of vertex positions
 */
export async function generatePolygonVertices(sides, center = BABYLON.Vector3.Zero(), rotation = 0, useBackend = true) {
  // Try backend first if requested
  if (useBackend) {
    try {
      const backendGeometry = await getPrimitiveGeometryFromBackend(sides);
      if (backendGeometry && backendGeometry.vertices && backendGeometry.vertices.length > 0) {
        // Convert backend vertices to Babylon vectors
        const vertices = backendGeometry.vertices.map(v => {
          const vec = new BABYLON.Vector3(v[0], v[1] || 0, v[2] || 0);
          if (rotation !== 0) {
            const rotationMatrix = BABYLON.Matrix.RotationY(rotation);
            BABYLON.Vector3.TransformCoordinatesToRef(vec, rotationMatrix, vec);
          }
          return vec.add(center);
        });
        return vertices;
      }
    } catch (error) {
      console.warn(`[geometryUtils] Backend geometry fetch failed, using local calculation: ${error.message}`);
    }
  }
  
  // Fallback to local calculation
  const circumradius = calculateCircumradius(sides);
  const vertices = [];
  
  for (let i = 0; i < sides; i++) {
    const angle = (i * 2 * Math.PI) / sides + rotation;
    const x = circumradius * Math.cos(angle);
    const z = circumradius * Math.sin(angle);
    vertices.push(new BABYLON.Vector3(x, 0, z).add(center));
  }
  
  return vertices;
}

/**
 * Calculate edge information for polygon
 * 
 * @param {BABYLON.Vector3[]} vertices - Polygon vertices
 * @param {number} sides - Number of sides
 * @returns {Array} Array of edge objects
 */
export function calculateEdges(vertices, sides) {
  const edges = [];
  const internalAngle = calculateInternalAngle(sides);
  
  for (let i = 0; i < sides; i++) {
    const start = vertices[i];
    const end = vertices[(i + 1) % sides];
    const midpoint = BABYLON.Vector3.Center(start, end);
    const length = BABYLON.Vector3.Distance(start, end);
    
    // Verify unit edge length (with tolerance)
    const tolerance = 0.001;
    if (Math.abs(length - UNIT_EDGE_LENGTH) > tolerance) {
      console.warn(`Edge ${i} length ${length.toFixed(4)} != unit length ${UNIT_EDGE_LENGTH}`);
    }
    
    // Calculate edge normal (perpendicular to edge, pointing outward)
    const edgeVector = end.subtract(start).normalize();
    const normal = new BABYLON.Vector3(-edgeVector.z, 0, edgeVector.x).normalize();
    
    edges.push({
      index: i,
      start: start.clone(),
      end: end.clone(),
      midpoint: midpoint.clone(),
      length,
      internalAngle,
      normal,
      isOpen: true
    });
  }
  
  return edges;
}

/**
 * Calculate fold angle between two polygons
 * Uses simplified dihedral angle formula
 * 
 * @param {number} sidesA - Number of sides for polygon A
 * @param {number} sidesB - Number of sides for polygon B
 * @returns {number} Fold angle in radians
 */
export function calculateFoldAngle(sidesA, sidesB) {
  const angleA = calculateInternalAngle(sidesA);
  const angleB = calculateInternalAngle(sidesB);
  
  // Simplified dihedral angle: π - (angleA + angleB) / 2
  // In practice, should use backend attachment matrix for accuracy
  return Math.PI - (angleA + angleB) / 2;
}

/**
 * Get fold angle from backend attachment matrix
 * This is the preferred method for accuracy - uses Netlib precomputed data
 * 
 * @param {number} sidesA - Number of sides for polygon A
 * @param {number} sidesB - Number of sides for polygon B
 * @returns {Promise<number|null>} Fold angle in radians, or null if not found
 */
export async function getFoldAngleFromBackend(sidesA, sidesB) {
  try {
    const response = await fetch(`/api/geometry/fold-angle/${sidesA}/${sidesB}`);
    if (!response.ok) {
      console.warn(`[geometryUtils] Fold angle not found for ${sidesA}-${sidesB}, using fallback`);
      return calculateFoldAngle(sidesA, sidesB);
    }
    const data = await response.json();
    return data.fold_angle;
  } catch (error) {
    console.warn(`[geometryUtils] Error fetching fold angle: ${error.message}, using fallback`);
    return calculateFoldAngle(sidesA, sidesB);
  }
}

/**
 * Get primitive geometry from backend
 * Uses Netlib precomputed data for accuracy
 * 
 * @param {number} sides - Number of sides (3-20)
 * @returns {Promise<Object|null>} Geometry data or null if not found
 */
export async function getPrimitiveGeometryFromBackend(sides) {
  try {
    const response = await fetch(`/api/geometry/primitive/${sides}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.warn(`[geometryUtils] Error fetching primitive geometry: ${error.message}`);
    return null;
  }
}

/**
 * Get polyhedron geometry from backend
 * Uses Netlib precomputed data
 * 
 * @param {string} symbol - Polyhedron symbol (e.g., "Ω1")
 * @returns {Promise<Object|null>} Geometry data or null if not found
 */
export async function getPolyhedronGeometryFromBackend(symbol) {
  try {
    const response = await fetch(`/api/geometry/polyhedron/${encodeURIComponent(symbol)}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.warn(`[geometryUtils] Error fetching polyhedron geometry: ${error.message}`);
    return null;
  }
}

/**
 * Get attachment geometry from backend
 * Uses Netlib attachment matrix
 * 
 * @param {number} sidesA - Number of sides for polygon A
 * @param {number} sidesB - Number of sides for polygon B
 * @returns {Promise<Object|null>} Attachment geometry or null if not found
 */
export async function getAttachmentGeometryFromBackend(sidesA, sidesB) {
  try {
    const response = await fetch(`/api/geometry/attachment/${sidesA}/${sidesB}`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.warn(`[geometryUtils] Error fetching attachment geometry: ${error.message}`);
    return null;
  }
}

/**
 * Calculate snap transform to align two edges
 * 
 * @param {Object} movingEdge - Edge being moved {start, end, midpoint, normal}
 * @param {Object} targetEdge - Target edge {start, end, midpoint, normal}
 * @param {number} foldAngle - Fold angle to apply (radians)
 * @returns {Object} Transform {position, rotation}
 */
export function calculateSnapTransform(movingEdge, targetEdge, foldAngle = 0) {
  // Calculate rotation to align edges
  const movingDir = movingEdge.end.subtract(movingEdge.start).normalize();
  const targetDir = targetEdge.end.subtract(targetEdge.start).normalize();
  
  // Calculate rotation angle to align directions
  const alignAngle = Math.atan2(
    BABYLON.Vector3.Cross(movingDir, targetDir).y,
    BABYLON.Vector3.Dot(movingDir, targetDir)
  );
  
  // Apply fold angle rotation around edge axis
  const foldRotation = BABYLON.Matrix.RotationAxis(targetEdge.normal, foldAngle);
  const alignRotation = BABYLON.Matrix.RotationY(alignAngle);
  const combinedRotation = alignRotation.multiply(foldRotation);
  
  // Calculate position offset to align midpoints
  const positionOffset = targetEdge.midpoint.subtract(movingEdge.midpoint);
  
  return {
    position: positionOffset,
    rotation: BABYLON.Quaternion.FromRotationMatrix(combinedRotation)
  };
}

/**
 * Verify unit edge length in geometry
 * 
 * @param {BABYLON.Vector3[]} vertices - Polygon vertices
 * @param {number} tolerance - Tolerance for verification (default: 0.001)
 * @returns {boolean} True if all edges are unit length
 */
export function verifyUnitEdges(vertices, tolerance = 0.001) {
  for (let i = 0; i < vertices.length; i++) {
    const start = vertices[i];
    const end = vertices[(i + 1) % vertices.length];
    const length = BABYLON.Vector3.Distance(start, end);
    
    if (Math.abs(length - UNIT_EDGE_LENGTH) > tolerance) {
      console.warn(`Edge ${i} length ${length.toFixed(4)} != unit length ${UNIT_EDGE_LENGTH}`);
      return false;
    }
  }
  return true;
}

/**
 * Create Babylon.js mesh from polygon geometry
 * 
 * @param {number} sides - Number of sides
 * @param {BABYLON.Scene} scene - Babylon.js scene
 * @param {BABYLON.Vector3} position - Position (default: origin)
 * @param {string} name - Mesh name (default: "polygon_{sides}")
 * @returns {BABYLON.Mesh} Babylon.js mesh
 */
export function createPolygonMesh(sides, scene, position = BABYLON.Vector3.Zero(), name = null) {
  const meshName = name || `polygon_${sides}`;
  const vertices = generatePolygonVertices(sides, position);
  
  // Create vertex data
  const vertexData = new BABYLON.VertexData();
  const positions = [];
  const indices = [];
  
  // Add vertices
  vertices.forEach(v => {
    positions.push(v.x, v.y, v.z);
  });
  
  // Create fan triangulation (center to perimeter)
  const centerIndex = positions.length / 3;
  for (let i = 0; i < sides; i++) {
    indices.push(centerIndex, i, (i + 1) % sides);
  }
  
  vertexData.positions = new Float32Array(positions);
  vertexData.indices = new Uint32Array(indices);
  vertexData.normals = [];
  BABYLON.VertexData.ComputeNormals(positions, indices, vertexData.normals);
  
  // Create mesh
  const mesh = new BABYLON.Mesh(meshName, scene);
  vertexData.applyToMesh(mesh);
  
  return mesh;
}

