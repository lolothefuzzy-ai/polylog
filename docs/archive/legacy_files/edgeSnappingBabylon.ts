/**
 * Edge Snapping Utility for Babylon.js
 * Implements 3D edge-to-edge snapping for polyform assembly
 */

import * as BABYLON from '@babylonjs/core';

export interface PolygonEdge {
  start: BABYLON.Vector3;
  end: BABYLON.Vector3;
  midpoint: BABYLON.Vector3;
  length: number;
  normal: BABYLON.Vector3;  // Face normal at this edge
}

export interface SnapCandidate {
  targetMesh: BABYLON.Mesh;
  targetEdgeIndex: number;
  targetEdge: PolygonEdge;
  movingEdgeIndex: number;  // Which edge of the moving polygon
  movingEdge: PolygonEdge;  // The edge from moving polygon
  distance: number;
  alignmentScore: number;  // 0-1, higher = better alignment
}

const SNAP_THRESHOLD = 2.0;  // Units (scaled edge length ~3.0)
const EDGE_LENGTH_TOLERANCE = 0.1;  // 10% tolerance for edge matching

/**
 * Extract edges from a polygon mesh
 */
export function extractEdges(mesh: BABYLON.Mesh): PolygonEdge[] {
  const geometryData = mesh.metadata?.geometryData;
  if (!geometryData) return [];

  const edges: PolygonEdge[] = [];
  const worldMatrix = mesh.getWorldMatrix();
  
  // Transform vertices to world space
  const worldVertices = geometryData.vertices.map((v: BABYLON.Vector3) => {
    return BABYLON.Vector3.TransformCoordinates(v, worldMatrix);
  });

  // Calculate face normal (assuming flat polygon on XZ plane initially)
  const normal = BABYLON.Vector3.Up();  // Will be transformed by rotation

  // Create edges
  for (let i = 0; i < worldVertices.length; i++) {
    const start = worldVertices[i];
    const end = worldVertices[(i + 1) % worldVertices.length];
    const midpoint = BABYLON.Vector3.Center(start, end);
    const length = BABYLON.Vector3.Distance(start, end);

    edges.push({
      start,
      end,
      midpoint,
      length,
      normal
    });
  }

  return edges;
}

/**
 * Find the closest edge from existing meshes to a point
 */
export function findClosestEdge(
  point: BABYLON.Vector3,
  existingMeshes: BABYLON.Mesh[],
  excludeMesh?: BABYLON.Mesh
): SnapCandidate | null {
  let bestCandidate: SnapCandidate | null = null;
  let minDistance = SNAP_THRESHOLD;

  for (const mesh of existingMeshes) {
    if (mesh === excludeMesh) continue;
    
    const edges = extractEdges(mesh);
    
    edges.forEach((edge, edgeIndex) => {
      const distance = BABYLON.Vector3.Distance(point, edge.midpoint);
      
      if (distance < minDistance) {
        // Calculate alignment score (1.0 = perfect, 0.0 = perpendicular)
        const alignmentScore = 1.0;  // Simplified for now
        
        // Create a stub moving edge (this function doesn't have moving mesh context)
        const stubMovingEdge: PolygonEdge = {
          start: point,
          end: point,
          midpoint: point,
          length: 0,
          normal: BABYLON.Vector3.Up()
        };
        
        bestCandidate = {
          targetMesh: mesh,
          targetEdgeIndex: edgeIndex,
          targetEdge: edge,
          movingEdgeIndex: 0,  // Stub value
          movingEdge: stubMovingEdge,
          distance,
          alignmentScore
        };
        minDistance = distance;
      }
    });
  }

  return bestCandidate;
}

/**
 * Find snap candidates for a moving polygon
 */
export function findSnapCandidates(
  movingMesh: BABYLON.Mesh,
  existingMeshes: BABYLON.Mesh[]
): SnapCandidate[] {
  const candidates: SnapCandidate[] = [];
  const movingEdges = extractEdges(movingMesh);

  for (const mesh of existingMeshes) {
    if (mesh === movingMesh) continue;
    
    const targetEdges = extractEdges(mesh);
    
    // Check each edge of moving polygon against each edge of target
    movingEdges.forEach((movingEdge, movingEdgeIndex) => {
      targetEdges.forEach((targetEdge, targetEdgeIndex) => {
        // Check if edge lengths are compatible
        const lengthDiff = Math.abs(movingEdge.length - targetEdge.length);
        if (lengthDiff > EDGE_LENGTH_TOLERANCE * movingEdge.length) {
          return;  // Edges incompatible
        }

        // Calculate distance between edge midpoints
        const distance = BABYLON.Vector3.Distance(
          movingEdge.midpoint,
          targetEdge.midpoint
        );

        if (distance < SNAP_THRESHOLD) {
          // Calculate alignment score
          const edgeDir1 = movingEdge.end.subtract(movingEdge.start).normalize();
          const edgeDir2 = targetEdge.end.subtract(targetEdge.start).normalize();
          const dotProduct = Math.abs(BABYLON.Vector3.Dot(edgeDir1, edgeDir2));
          const alignmentScore = dotProduct;  // 1.0 = parallel, 0.0 = perpendicular

          candidates.push({
            targetMesh: mesh,
            targetEdgeIndex,
            targetEdge,
            movingEdgeIndex,
            movingEdge,
            distance,
            alignmentScore
          });
        }
      });
    });
  }

  // Sort by distance (closest first)
  candidates.sort((a, b) => a.distance - b.distance);

  return candidates;
}

/**
 * Calculate snap position and rotation for edge-to-edge attachment
 * Returns the rotation needed to align movingEdge with targetEdge (flipped 180°)
 */
export function calculateSnapTransform(
  movingEdge: PolygonEdge,
  targetEdge: PolygonEdge,
  currentRotation?: BABYLON.Quaternion
): { position: BABYLON.Vector3; rotation: BABYLON.Quaternion } {
  // Position: align edge midpoints
  const position = targetEdge.midpoint.clone();

  // Calculate edge directions
  const targetDir = targetEdge.end.subtract(targetEdge.start).normalize();
  const movingDir = movingEdge.end.subtract(movingEdge.start).normalize();
  
  // We want to flip the moving edge 180° to attach on opposite side
  const desiredDir = targetDir.scale(-1);
  
  // Calculate rotation axis (perpendicular to both directions)
  let axis = BABYLON.Vector3.Cross(movingDir, desiredDir);
  
  // Handle parallel/anti-parallel edges (axis would be zero)
  if (axis.lengthSquared() < 0.0001) {
    // Edges are already aligned or opposite - use up vector as axis
    axis = BABYLON.Vector3.Up();
  } else {
    axis.normalize();
  }
  
  // Calculate rotation angle
  const dotProduct = BABYLON.Vector3.Dot(movingDir, desiredDir);
  const angle = Math.acos(Math.max(-1, Math.min(1, dotProduct)));
  
  // Create rotation quaternion
  const rotation = BABYLON.Quaternion.RotationAxis(axis, angle);

  return { position, rotation };
}

/**
 * Highlight an edge for visual feedback
 */
export function highlightEdge(
  edge: PolygonEdge,
  scene: BABYLON.Scene,
  color: BABYLON.Color3 = new BABYLON.Color3(0, 1, 0)  // Green
): BABYLON.LinesMesh {
  const points = [edge.start, edge.end];
  const line = BABYLON.MeshBuilder.CreateLines(
    'edgeHighlight',
    { points },
    scene
  );
  line.color = color;
  line.isPickable = false;
  
  return line;
}

/**
 * Remove edge highlight
 */
export function removeHighlight(highlight: BABYLON.LinesMesh | null) {
  if (highlight) {
    highlight.dispose();
  }
}
