/**
 * Auto-Snapping System for Polylog6
 * 
 * Automatically rotates and snaps polygons to valid attachment points
 */

import * as THREE from 'three';
import { OpenEdge } from './liaisonGraph';
import { canAttach, getStabilityScore, getBestFoldAngle, getStabilityColor } from './attachmentMatrix';

export interface SnapCandidate {
  openEdge: OpenEdge;
  targetPosition: THREE.Vector3;
  targetRotation: THREE.Euler;
  foldAngle: number;
  stability: number;
  stabilityColor: string;
  distance: number;
}

/**
 * Find the best snap candidate for a polygon
 */
export function findBestSnapCandidate(
  polygonSides: number,
  currentPosition: THREE.Vector3,
  openEdges: OpenEdge[],
  snapDistance: number = 2.0
): SnapCandidate | null {
  const candidates: SnapCandidate[] = [];
  
  for (const openEdge of openEdges) {
    // Check if polygons can attach
    const targetPolygonSides = getSidesFromPolygonId(openEdge.polygon_id);
    if (!canAttach(polygonSides, targetPolygonSides)) {
      continue;
    }
    
    // Calculate distance to edge midpoint
    const distance = currentPosition.distanceTo(openEdge.midpoint);
    if (distance > snapDistance) {
      continue;
    }
    
    // Calculate snap position and rotation
    const snapResult = calculateSnapTransform(
      polygonSides,
      openEdge,
      currentPosition
    );
    
    if (!snapResult) continue;
    
    const stability = getStabilityScore(polygonSides, targetPolygonSides);
    const stabilityColor = getStabilityColor(polygonSides, targetPolygonSides);
    const foldAngle = getBestFoldAngle(polygonSides, targetPolygonSides) ?? 180;
    
    candidates.push({
      openEdge,
      targetPosition: snapResult.position,
      targetRotation: snapResult.rotation,
      foldAngle,
      stability,
      stabilityColor,
      distance
    });
  }
  
  if (candidates.length === 0) return null;
  
  // Sort by stability (descending) then distance (ascending)
  candidates.sort((a, b) => {
    if (Math.abs(a.stability - b.stability) > 0.1) {
      return b.stability - a.stability;
    }
    return a.distance - b.distance;
  });
  
  return candidates[0];
}

/**
 * Calculate snap transform (position and rotation) for a polygon to attach to an open edge
 */
function calculateSnapTransform(
  polygonSides: number,
  openEdge: OpenEdge,
  currentPosition: THREE.Vector3
): { position: THREE.Vector3; rotation: THREE.Euler } | null {
  // Calculate polygon circumradius for unit edge length
  const radius = 1 / (2 * Math.sin(Math.PI / polygonSides));
  
  // Position: place polygon so its first edge aligns with the open edge
  // The polygon should be on the opposite side of the edge normal
  const offset = openEdge.normal.clone().multiplyScalar(radius);
  const position = openEdge.midpoint.clone().sub(offset);
  
  // Rotation: align polygon's first edge with the open edge (anti-parallel)
  const edgeVector = new THREE.Vector3().subVectors(openEdge.end_vertex, openEdge.start_vertex);
  const edgeAngle = Math.atan2(edgeVector.y, edgeVector.x);
  
  // Polygon's first edge should be anti-parallel (180° rotated)
  const targetAngle = edgeAngle + Math.PI;
  
  // Calculate rotation needed
  // For now, assume rotation around Z-axis only (2D mode)
  const rotation = new THREE.Euler(0, 0, targetAngle);
  
  return { position, rotation };
}

/**
 * Extract polygon sides from polygon ID
 * Assumes ID format: "polygon-{timestamp}" or similar
 * This is a placeholder - should be replaced with actual polygon data lookup
 */
function getSidesFromPolygonId(polygonId: string): number {
  // TODO: Replace with actual lookup from liaison graph
  // For now, return a default value
  return 3;
}

/**
 * Calculate snap zones for visualization
 * Returns circles/spheres around open edges
 */
export function calculateSnapZones(
  openEdges: OpenEdge[],
  snapDistance: number = 2.0
): Array<{ position: THREE.Vector3; radius: number; color: string }> {
  return openEdges.map(edge => ({
    position: edge.midpoint.clone(),
    radius: snapDistance,
    color: '#4CAF50'  // Green
  }));
}

/**
 * Interpolate between current and target transform for smooth snapping
 */
export function interpolateTransform(
  currentPosition: THREE.Vector3,
  currentRotation: THREE.Euler,
  targetPosition: THREE.Vector3,
  targetRotation: THREE.Euler,
  alpha: number
): { position: THREE.Vector3; rotation: THREE.Euler } {
  const position = new THREE.Vector3().lerpVectors(currentPosition, targetPosition, alpha);
  
  // Convert Euler to Quaternion for smooth rotation interpolation
  const currentQuat = new THREE.Quaternion().setFromEuler(currentRotation);
  const targetQuat = new THREE.Quaternion().setFromEuler(targetRotation);
  const interpolatedQuat = new THREE.Quaternion().slerpQuaternions(currentQuat, targetQuat, alpha);
  
  const rotation = new THREE.Euler().setFromQuaternion(interpolatedQuat);
  
  return { position, rotation };
}

/**
 * Check if a snap is valid (no collisions, geometric constraints satisfied)
 */
export function isSnapValid(
  polygonSides: number,
  targetPosition: THREE.Vector3,
  existingPolygons: Array<{ position: THREE.Vector3; sides: number }>,
  minDistance: number = 0.5
): boolean {
  // Check for collisions with existing polygons
  for (const existing of existingPolygons) {
    const distance = targetPosition.distanceTo(existing.position);
    if (distance < minDistance) {
      return false;
    }
  }
  
  return true;
}

/**
 * Calculate edge alignment score (0.0 to 1.0)
 * Higher score means better alignment
 */
export function calculateAlignmentScore(
  edge1Start: THREE.Vector3,
  edge1End: THREE.Vector3,
  edge2Start: THREE.Vector3,
  edge2End: THREE.Vector3
): number {
  // Check if edges are anti-parallel
  const edge1Vector = new THREE.Vector3().subVectors(edge1End, edge1Start).normalize();
  const edge2Vector = new THREE.Vector3().subVectors(edge2End, edge2Start).normalize();
  
  // Dot product should be close to -1 for anti-parallel edges
  const dotProduct = edge1Vector.dot(edge2Vector);
  const parallelScore = (1 - Math.abs(dotProduct + 1)) / 2;  // 0 when dot = -1 (perfect)
  
  // Check if edge lengths match
  const length1 = edge1Start.distanceTo(edge1End);
  const length2 = edge2Start.distanceTo(edge2End);
  const lengthDiff = Math.abs(length1 - length2);
  const lengthScore = Math.max(0, 1 - lengthDiff);
  
  // Check if edges are close in space
  const midpoint1 = new THREE.Vector3().addVectors(edge1Start, edge1End).multiplyScalar(0.5);
  const midpoint2 = new THREE.Vector3().addVectors(edge2Start, edge2End).multiplyScalar(0.5);
  const distance = midpoint1.distanceTo(midpoint2);
  const distanceScore = Math.max(0, 1 - distance / 2);
  
  // Combined score (weighted average)
  return parallelScore * 0.4 + lengthScore * 0.3 + distanceScore * 0.3;
}

/**
 * Generate snap feedback message for UI
 */
export function generateSnapFeedback(candidate: SnapCandidate | null): string {
  if (!candidate) {
    return 'No valid attachment points nearby';
  }
  
  return `Snap to edge (stability: ${(candidate.stability * 100).toFixed(0)}%, fold: ${candidate.foldAngle.toFixed(1)}°)`;
}

/**
 * Calculate snap indicator position for visualization
 */
export function calculateSnapIndicator(
  candidate: SnapCandidate
): { position: THREE.Vector3; rotation: THREE.Euler; color: string } {
  return {
    position: candidate.targetPosition.clone(),
    rotation: candidate.targetRotation.clone(),
    color: candidate.stabilityColor
  };
}
