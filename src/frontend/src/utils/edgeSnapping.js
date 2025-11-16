/**
 * Edge snapping utilities for 3D polyform assembly
 * Implements edge-to-edge snapping with fold angle calculation
 */

import * as BABYLON from '@babylonjs/core';

const SNAP_THRESHOLD = 0.5; // Distance threshold for snapping

export class EdgeSnapper {
  /**
   * Find closest edge from a polygon mesh
   */
  static findClosestEdge(mesh, targetPoint) {
    const positions = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind);
    if (!positions || positions.length < 9) return null;

    let closestDist = Infinity;
    let closestEdge = null;
    const vertexCount = positions.length / 3;

    for (let i = 0; i < vertexCount; i++) {
      const v1 = new BABYLON.Vector3(
        positions[i * 3],
        positions[i * 3 + 1],
        positions[i * 3 + 2]
      );
      const v2 = new BABYLON.Vector3(
        positions[((i + 1) % vertexCount) * 3],
        positions[((i + 1) % vertexCount) * 3 + 1],
        positions[((i + 1) % vertexCount) * 3 + 2]
      );

      // Project targetPoint onto edge
      const edgeVec = v2.subtract(v1);
      const pointVec = targetPoint.subtract(v1);
      const t = BABYLON.Vector3.Dot(pointVec, edgeVec) / edgeVec.lengthSquared();

      if (t >= 0 && t <= 1) {
        const projection = v1.add(edgeVec.scale(t));
        const dist = BABYLON.Vector3.Distance(targetPoint, projection);

        if (dist < closestDist && dist < SNAP_THRESHOLD) {
          closestDist = dist;
          closestEdge = {
            index: i,
            start: v1,
            end: v2,
            midpoint: projection,
            distance: dist
          };
        }
      }
    }

    return closestEdge;
  }

  /**
   * Find snap candidates between moving mesh and existing meshes
   */
  static findSnapCandidates(movingMesh, existingMeshes) {
    const candidates = [];
    const movingCenter = movingMesh.getBoundingInfo().boundingBox.centerWorld;

    existingMeshes.forEach(existingMesh => {
      if (existingMesh === movingMesh) return;

      const edge = this.findClosestEdge(existingMesh, movingCenter);
      if (edge) {
        candidates.push({
          targetMesh: existingMesh,
          targetEdge: edge,
          distance: edge.distance
        });
      }
    });

    return candidates.sort((a, b) => a.distance - b.distance);
  }

  /**
   * Calculate snap transform to align edges
   */
  static calculateSnapTransform(movingEdge, targetEdge, foldAngle = 0) {
    // Calculate rotation to align edges
    const targetDir = targetEdge.end.subtract(targetEdge.start).normalize();
    const movingDir = movingEdge.end.subtract(movingEdge.start).normalize();
    
    // Rotate moving edge to align with target (flipped for attachment)
    const alignmentAngle = Math.acos(BABYLON.Vector3.Dot(targetDir, movingDir));
    const cross = BABYLON.Vector3.Cross(targetDir, movingDir);
    
    // Apply fold angle rotation around the edge
    const foldAxis = targetDir; // Rotation axis is along the edge
    const foldQuaternion = BABYLON.Quaternion.RotationAxis(foldAxis, foldAngle);
    
    // Calculate position offset
    const offset = targetEdge.midpoint.subtract(movingEdge.midpoint);
    
    return {
      position: offset,
      rotation: foldQuaternion,
      foldAngle: foldAngle
    };
  }
}

