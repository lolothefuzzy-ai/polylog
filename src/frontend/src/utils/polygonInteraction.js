/**
 * Polygon interaction system for drag, drop, and 3D manipulation
 */

import * as BABYLON from '@babylonjs/core';
import { EdgeSnapper } from './edgeSnapping.js';

export class PolygonInteractionManager {
  constructor(scene, camera, onAttachment) {
    this.scene = scene;
    this.camera = camera;
    this.onAttachment = onAttachment;
    this.meshes = new Map(); // polygonId -> mesh
    this.dragging = null;
    this.snapGuide = null;
    this.openEdges = new Map(); // polygonId -> Set<edgeIndex>
  }

  /**
   * Add polygon to workspace
   */
  addPolygon(polygonId, mesh, metadata) {
    mesh.metadata = metadata;
    this.meshes.set(polygonId, mesh);
    
    // Initialize open edges (all edges start open)
    const vertexCount = mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind).length / 3;
    this.openEdges.set(polygonId, new Set(Array.from({ length: vertexCount }, (_, i) => i)));
    
    // Enable picking
    mesh.enablePointerMoveEvents = true;
    mesh.actionManager = new BABYLON.ActionManager(this.scene);
    
    // Set up drag handlers
    this.setupDragHandlers(mesh, polygonId);
    
    // If this is the second polygon, attempt auto-attachment
    if (this.meshes.size === 2) {
      this.attemptAutoAttachment();
    }
  }

  /**
   * Attempt automatic attachment when second polygon is added
   */
  async attemptAutoAttachment() {
    const polygonIds = Array.from(this.meshes.keys());
    if (polygonIds.length < 2) return;

    const polyAId = polygonIds[0];
    const polyBId = polygonIds[1];
    const meshA = this.meshes.get(polyAId);
    const meshB = this.meshes.get(polyBId);

    // Find best attachment option
    const candidates = EdgeSnapper.findSnapCandidates(meshB, [meshA]);
    if (candidates.length === 0) return;

    const bestCandidate = candidates[0];
    
    // Get attachment sequence from API
    try {
      const symbolA = meshA.metadata?.symbol || 'A';
      const symbolB = meshB.metadata?.symbol || 'B';
      
      const response = await fetch('http://localhost:8000/api/attachment/sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          polygonA: symbolA,
          polygonB: symbolB,
          scaler: 1.0
        })
      });
      
      const data = await response.json();
      if (data.success && data.stability >= 0.7) {
        // Apply attachment with fold angle from sequence
        const foldAngle = (data.fold_angle || 0) * (Math.PI / 180); // Convert to radians
        this.applyAttachment(meshA, meshB, bestCandidate, foldAngle);
      }
    } catch (error) {
      console.error('Auto-attachment failed:', error);
    }
  }

  /**
   * Apply attachment between two meshes
   */
  applyAttachment(meshA, meshB, candidate, foldAngle) {
    // Calculate snap transform
    const movingEdge = {
      start: meshB.position,
      end: meshB.position.clone().add(BABYLON.Vector3.Right()),
      midpoint: meshB.position
    };
    
    const transform = EdgeSnapper.calculateSnapTransform(
      movingEdge,
      candidate.targetEdge,
      foldAngle
    );
    
    // Apply transform
    meshB.position.addInPlace(transform.position);
    meshB.rotationQuaternion = transform.rotation;
    
    // Mark edges as attached
    const polyAId = Array.from(this.meshes.entries()).find(([_, m]) => m === meshA)?.[0];
    const polyBId = Array.from(this.meshes.entries()).find(([_, m]) => m === meshB)?.[0];
    
    if (polyAId && polyBId) {
      // Remove attached edges from open edges
      const openA = this.openEdges.get(polyAId);
      const openB = this.openEdges.get(polyBId);
      if (openA) openA.delete(candidate.targetEdge.index);
      if (openB) openB.delete(0); // Simplified - would need actual edge index
    }
    
    // Notify callback
    if (this.onAttachment) {
      this.onAttachment({
        polygonA: polyAId,
        polygonB: polyBId,
        foldAngle: foldAngle,
        transform: transform
      });
    }
  }

  /**
   * Set up drag handlers for a mesh
   */
  setupDragHandlers(mesh, polygonId) {
    let isDragging = false;
    let dragStart = null;

    mesh.actionManager.registerAction(
      new BABYLON.ExecuteCodeAction(BABYLON.ActionManager.OnPickDownTrigger, (evt) => {
        isDragging = true;
        dragStart = evt.pickedPoint;
        this.dragging = { mesh, polygonId, start: dragStart };
      })
    );

    this.scene.onPointerObservable.add((pointerInfo) => {
      if (pointerInfo.type === BABYLON.PointerEventTypes.POINTERMOVE && isDragging && this.dragging) {
        const ray = this.scene.createPickingRay(
          pointerInfo.event.offsetX,
          pointerInfo.event.offsetY,
          BABYLON.Matrix.Identity(),
          this.camera
        );
        
        const hit = this.scene.pickWithRay(ray);
        if (hit && hit.pickedPoint) {
          // Update mesh position
          this.dragging.mesh.position = hit.pickedPoint;
          
          // Check for snap candidates
          const otherMeshes = Array.from(this.meshes.values()).filter(m => m !== this.dragging.mesh);
          const candidates = EdgeSnapper.findSnapCandidates(this.dragging.mesh, otherMeshes);
          
          if (candidates.length > 0) {
            this.snapGuide = candidates[0];
            // Visual feedback could be added here
          } else {
            this.snapGuide = null;
          }
        }
      }
      
      if (pointerInfo.type === BABYLON.PointerEventTypes.POINTERUP && isDragging) {
        isDragging = false;
        if (this.snapGuide && this.dragging) {
          // Apply snap
          this.applyAttachment(
            this.snapGuide.targetMesh,
            this.dragging.mesh,
            this.snapGuide,
            0 // Would get from API
          );
        }
        this.dragging = null;
        this.snapGuide = null;
      }
    });
  }
}

