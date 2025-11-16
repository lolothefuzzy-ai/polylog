/**
 * Attachment Resolver for Polylog Visualizer
 * 
 * Implements edge-to-edge attachment validation based on Polylog6 architecture:
 * - Unit edge length enforcement
 * - Edge compatibility checking
 * - Snap-to-edge functionality
 * - Stability scoring
 */

import * as THREE from 'three';
import { Polygon3D, Edge3D, UNIT_EDGE_LENGTH, canAttachEdges, calculateAttachmentTransform } from './polygon3D';

export interface AttachmentCandidate {
  sourcePolygon: Polygon3D;
  targetPolygon: Polygon3D;
  sourceEdgeIndex: number;
  targetEdgeIndex: number;
  transform: {
    position: THREE.Vector3;
    rotation: THREE.Quaternion;
  };
  stabilityScore: number;
  distance: number;
}

export interface SnapGuide {
  sourceEdge: Edge3D;
  targetEdge: Edge3D;
  snapPosition: THREE.Vector3;
  snapRotation: THREE.Quaternion;
  isValid: boolean;
}

const SNAP_THRESHOLD = 0.5; // Distance threshold for snap-to-edge
const EDGE_LENGTH_TOLERANCE = 0.01; // Tolerance for unit edge length matching

/**
 * Find all valid attachment candidates for a polygon in the workspace
 */
export function findAttachments(
  polygon: Polygon3D,
  workspace: Polygon3D[],
  snapThreshold: number = SNAP_THRESHOLD
): AttachmentCandidate[] {
  const candidates: AttachmentCandidate[] = [];
  
  // Check each polygon in workspace
  for (const targetPolygon of workspace) {
    if (targetPolygon.id === polygon.id) continue;
    
    // Check each edge of the source polygon
    for (let sourceEdgeIdx = 0; sourceEdgeIdx < polygon.edges.length; sourceEdgeIdx++) {
      const sourceEdge = polygon.edges[sourceEdgeIdx];
      
      // Only consider open edges
      if (!sourceEdge.isOpen) continue;
      
      // Check each edge of the target polygon
      for (let targetEdgeIdx = 0; targetEdgeIdx < targetPolygon.edges.length; targetEdgeIdx++) {
        const targetEdge = targetPolygon.edges[targetEdgeIdx];
        
        // Only consider open edges
        if (!targetEdge.isOpen) continue;
        
        // Check if edges can attach
        if (!canAttachEdges(sourceEdge, targetEdge, EDGE_LENGTH_TOLERANCE)) continue;
        
        // Calculate distance between edge midpoints
        const distance = sourceEdge.midpoint.distanceTo(targetEdge.midpoint);
        
        // Only consider edges within snap threshold
        if (distance > snapThreshold) continue;
        
        // Calculate attachment transform
        const transform = calculateAttachmentTransform(sourceEdge, targetEdge);
        
        // Calculate stability score
        const stabilityScore = calculateStabilityScore(
          polygon,
          targetPolygon,
          sourceEdgeIdx,
          targetEdgeIdx,
          distance
        );
        
        candidates.push({
          sourcePolygon: polygon,
          targetPolygon,
          sourceEdgeIndex: sourceEdgeIdx,
          targetEdgeIndex: targetEdgeIdx,
          transform,
          stabilityScore,
          distance,
        });
      }
    }
  }
  
  // Sort by stability score (highest first)
  return candidates.sort((a, b) => b.stabilityScore - a.stabilityScore);
}

/**
 * Calculate stability score for an attachment
 * 
 * Score = (1 / distance) × edge_alignment × closure_benefit
 */
function calculateStabilityScore(
  sourcePolygon: Polygon3D,
  targetPolygon: Polygon3D,
  sourceEdgeIdx: number,
  targetEdgeIdx: number,
  distance: number
): number {
  const sourceEdge = sourcePolygon.edges[sourceEdgeIdx];
  const targetEdge = targetPolygon.edges[targetEdgeIdx];
  
  // Distance factor (closer = better)
  const distanceFactor = 1 / (distance + 0.1);
  
  // Edge alignment factor (parallel edges = better)
  const sourceDir = new THREE.Vector3().subVectors(sourceEdge.end, sourceEdge.start).normalize();
  const targetDir = new THREE.Vector3().subVectors(targetEdge.start, targetEdge.end).normalize(); // Reverse for opposite orientation
  const alignment = Math.abs(sourceDir.dot(targetDir)); // 1 = perfectly aligned, 0 = perpendicular
  
  // Closure benefit (reducing open edges)
  const currentOpenEdges = sourcePolygon.openEdges.size + targetPolygon.openEdges.size;
  const afterOpenEdges = currentOpenEdges - 2; // Closing one edge on each polygon
  const closureBenefit = currentOpenEdges / Math.max(afterOpenEdges, 1);
  
  return distanceFactor * alignment * closureBenefit;
}

/**
 * Find the best snap guide for a polygon being moved
 */
export function findSnapGuide(
  polygon: Polygon3D,
  workspace: Polygon3D[],
  snapThreshold: number = SNAP_THRESHOLD
): SnapGuide | null {
  const candidates = findAttachments(polygon, workspace, snapThreshold);
  
  if (candidates.length === 0) return null;
  
  // Return the best candidate as a snap guide
  const best = candidates[0];
  
  return {
    sourceEdge: best.sourcePolygon.edges[best.sourceEdgeIndex],
    targetEdge: best.targetPolygon.edges[best.targetEdgeIndex],
    snapPosition: best.transform.position,
    snapRotation: best.transform.rotation,
    isValid: best.stabilityScore > 0.5, // Threshold for valid snap
  };
}

/**
 * Apply an attachment to connect two polygons
 */
export function applyAttachment(
  candidate: AttachmentCandidate
): { sourcePolygon: Polygon3D; targetPolygon: Polygon3D } {
  const { sourcePolygon, targetPolygon, sourceEdgeIndex, targetEdgeIndex, transform } = candidate;
  
  // Update source polygon position and rotation
  sourcePolygon.mesh.position.copy(transform.position);
  sourcePolygon.mesh.quaternion.copy(transform.rotation);
  sourcePolygon.mesh.updateMatrixWorld();
  
  // Mark edges as closed
  sourcePolygon.edges[sourceEdgeIndex].isOpen = false;
  sourcePolygon.edges[sourceEdgeIndex].attachedTo = {
    polygonId: targetPolygon.id,
    edgeIndex: targetEdgeIndex,
  };
  
  targetPolygon.edges[targetEdgeIndex].isOpen = false;
  targetPolygon.edges[targetEdgeIndex].attachedTo = {
    polygonId: sourcePolygon.id,
    edgeIndex: sourceEdgeIndex,
  };
  
  // Update open edge sets
  sourcePolygon.openEdges.delete(sourceEdgeIndex);
  targetPolygon.openEdges.delete(targetEdgeIndex);
  
  return { sourcePolygon, targetPolygon };
}

/**
 * Check if two polygons would collide
 */
export function checkCollision(polygon1: Polygon3D, polygon2: Polygon3D): boolean {
  // Simple bounding sphere collision check
  const center1 = new THREE.Vector3();
  const center2 = new THREE.Vector3();
  
  polygon1.mesh.geometry.computeBoundingSphere();
  polygon2.mesh.geometry.computeBoundingSphere();
  
  const sphere1 = polygon1.mesh.geometry.boundingSphere!;
  const sphere2 = polygon2.mesh.geometry.boundingSphere!;
  
  center1.copy(sphere1.center).applyMatrix4(polygon1.mesh.matrixWorld);
  center2.copy(sphere2.center).applyMatrix4(polygon2.mesh.matrixWorld);
  
  const distance = center1.distanceTo(center2);
  const minDistance = sphere1.radius + sphere2.radius;
  
  return distance < minDistance * 0.9; // 90% threshold to account for edge attachment
}

/**
 * Validate edge attachment constraints
 */
export function validateAttachment(
  sourceEdge: Edge3D,
  targetEdge: Edge3D
): { valid: boolean; reason?: string } {
  // Check unit edge length
  if (Math.abs(sourceEdge.length - UNIT_EDGE_LENGTH) > EDGE_LENGTH_TOLERANCE) {
    return { valid: false, reason: 'Source edge is not unit length' };
  }
  
  if (Math.abs(targetEdge.length - UNIT_EDGE_LENGTH) > EDGE_LENGTH_TOLERANCE) {
    return { valid: false, reason: 'Target edge is not unit length' };
  }
  
  // Check edge lengths match
  if (Math.abs(sourceEdge.length - targetEdge.length) > EDGE_LENGTH_TOLERANCE) {
    return { valid: false, reason: 'Edge lengths do not match' };
  }
  
  // Check edges are open
  if (!sourceEdge.isOpen) {
    return { valid: false, reason: 'Source edge is already attached' };
  }
  
  if (!targetEdge.isOpen) {
    return { valid: false, reason: 'Target edge is already attached' };
  }
  
  return { valid: true };
}

/**
 * Calculate closure progress for the entire workspace
 */
export function calculateClosureProgress(polygons: Polygon3D[]): {
  totalEdges: number;
  openEdges: number;
  closedEdges: number;
  closurePercentage: number;
} {
  const totalEdges = polygons.reduce((sum, p) => sum + p.sides, 0);
  const openEdges = polygons.reduce((sum, p) => sum + p.openEdges.size, 0);
  const closedEdges = totalEdges - openEdges;
  const closurePercentage = totalEdges > 0 ? (closedEdges / totalEdges) * 100 : 100;
  
  return {
    totalEdges,
    openEdges,
    closedEdges,
    closurePercentage,
  };
}
