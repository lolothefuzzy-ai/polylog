/**
 * Visual feedback for edge snapping
 */

import * as BABYLON from '@babylonjs/core';

export class SnapVisualFeedback {
  constructor(scene) {
    this.scene = scene;
    this.snapGuides = [];
    this.highlightMeshes = [];
  }

  /**
   * Show snap guide for a candidate edge
   */
  showSnapGuide(targetMesh, edgeIndex, edge) {
    this.clearGuides();

    // Create highlight line for the edge
    const points = [
      edge.start,
      edge.end
    ];

    const line = BABYLON.MeshBuilder.CreateLines(
      `snap_guide_${targetMesh.name}`,
      { points: points },
      this.scene
    );
    line.color = new BABYLON.Color3(0, 1, 0); // Green
    line.alpha = 0.8;

    this.snapGuides.push(line);

    // Create highlight sphere at midpoint
    const sphere = BABYLON.MeshBuilder.CreateSphere(
      `snap_point_${targetMesh.name}`,
      { diameter: 0.2 },
      this.scene
    );
    sphere.position = edge.midpoint;
    sphere.material = new BABYLON.StandardMaterial(`snap_mat_${targetMesh.name}`, this.scene);
    sphere.material.emissiveColor = new BABYLON.Color3(0, 1, 0);
    sphere.material.alpha = 0.6;

    this.highlightMeshes.push(sphere);
  }

  /**
   * Highlight valid snap zones
   */
  highlightSnapZones(meshes, snapCandidates) {
    this.clearGuides();

    snapCandidates.forEach((candidate, index) => {
      const edge = candidate.targetEdge;
      
      // Create visual guide
      const points = [edge.start, edge.end];
      const line = BABYLON.MeshBuilder.CreateLines(
        `snap_zone_${index}`,
        { points: points },
        this.scene
      );
      
      // Color by distance (closer = brighter green)
      const intensity = 1.0 - (candidate.distance / 0.5);
      line.color = new BABYLON.Color3(0, intensity, 0);
      line.alpha = 0.5 + intensity * 0.3;

      this.snapGuides.push(line);
    });
  }

  /**
   * Clear all visual guides
   */
  clearGuides() {
    this.snapGuides.forEach(guide => guide.dispose());
    this.highlightMeshes.forEach(mesh => mesh.dispose());
    this.snapGuides = [];
    this.highlightMeshes = [];
  }

  /**
   * Show rotation feedback
   */
  showRotationFeedback(mesh, angle) {
    // Could add rotation indicator here
    // For now, just update mesh rotation
    if (mesh.rotationQuaternion) {
      const rotation = BABYLON.Quaternion.RotationAxis(
        BABYLON.Vector3.Up(),
        angle
      );
      mesh.rotationQuaternion.multiplyInPlace(rotation);
    }
  }
}

